import { offlineDb } from './db';
import { OfflineMutation } from './types';
import { getErrorMessage } from '../../lib/errors';

type SyncListener = (pendingCount: number, isOnline: boolean) => void;
const listeners: Set<SyncListener> = new Set();

export function subscribeSyncState(listener: SyncListener): () => void {
  listeners.add(listener);
  // Initial emit
  notifyListeners();
  return () => {
    listeners.delete(listener);
  };
}

async function notifyListeners() {
  const isOnline = typeof navigator !== 'undefined' ? navigator.onLine : true;
  const count = await offlineDb.offline_mutation_queue
    .filter((m) => m.status === 'queued' || m.status === 'failed')
    .count();
  listeners.forEach((l) => l(count, isOnline));
}

// Global network status change listeners
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    notifyListeners();
    // Auto-flush queue when connection is restored
    triggerAutoSync();
  });
  window.addEventListener('offline', () => {
    notifyListeners();
  });
}

export async function enqueueOfflineMutation(
  operationName: string,
  payload: Record<string, unknown>,
  accountId: string
): Promise<OfflineMutation> {
  const mutation: OfflineMutation = {
    localUuid: crypto.randomUUID(),
    idempotencyKey: `client-${Date.now()}-${crypto.randomUUID().slice(0, 8)}`,
    operationName,
    payload,
    accountId,
    createdAt: new Date().toISOString(),
    retryCount: 0,
    status: 'queued',
  };

  await offlineDb.offline_mutation_queue.add(mutation);
  await notifyListeners();

  // If online, attempt immediate sync
  if (navigator.onLine) {
    const token = localStorage.getItem('shikhor_token');
    if (token) {
      flushSyncQueue(token, accountId).catch(() => {});
    }
  }

  return mutation;
}

interface SyncServerResultItem {
  localUuid: string;
  status: 'success' | 'failed' | 'conflict';
  statusCode?: number;
  message?: string;
  code?: string;
  data?: Record<string, unknown>;
}

interface SyncServerBatchResponse {
  syncedCount: number;
  failedCount: number;
  results: SyncServerResultItem[];
}

export async function flushSyncQueue(
  token: string,
  accountId: string
): Promise<{ syncedCount: number; failedCount: number }> {
  const pending = await offlineDb.getPendingMutations(accountId);
  if (pending.length === 0) {
    return { syncedCount: 0, failedCount: 0 };
  }

  // Mark pending items as syncing
  for (const m of pending) {
    await offlineDb.offline_mutation_queue.update(m.localUuid, {
      status: 'syncing',
      retryCount: m.retryCount + 1,
    });
  }
  await notifyListeners();

  try {
    const batchPayload = {
      mutations: pending.map((m) => ({
        localUuid: m.localUuid,
        idempotencyKey: m.idempotencyKey,
        operationName: m.operationName,
        payload: m.payload,
        createdAt: m.createdAt,
      })),
    };

    const res = await fetch('/api/v1/sync/batch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(batchPayload),
    });

    if (!res.ok) {
      throw new Error(`Sync server responded with ${res.status}`);
    }

    const data = (await res.json()) as SyncServerBatchResponse;
    const results = data.results || [];

    for (const r of results) {
      if (r.status === 'success') {
        await offlineDb.offline_mutation_queue.update(r.localUuid, {
          status: 'synced',
          responsePayload: r.data,
          errorMessage: undefined,
          errorCode: undefined,
        });
      } else {
        await offlineDb.offline_mutation_queue.update(r.localUuid, {
          status: 'failed',
          errorMessage: r.message,
          errorCode: r.code,
        });
      }
    }

    await notifyListeners();
    return {
      syncedCount: data.syncedCount || 0,
      failedCount: data.failedCount || 0,
    };
  } catch (err: unknown) {
    // Network or server error -> Revert syncing status back to queued
    const errorMsg = getErrorMessage(err, 'সংযোগ ব্যর্থ হয়েছে। পরে চেষ্টা করা হবে।');
    for (const m of pending) {
      await offlineDb.offline_mutation_queue.update(m.localUuid, {
        status: 'queued',
        errorMessage: errorMsg,
      });
    }
    await notifyListeners();
    throw err;
  }
}

export async function deleteQueuedMutation(localUuid: string): Promise<void> {
  await offlineDb.offline_mutation_queue.delete(localUuid);
  await notifyListeners();
}

export async function retryQueuedMutation(
  localUuid: string,
  token: string,
  accountId: string
): Promise<void> {
  await offlineDb.offline_mutation_queue.update(localUuid, {
    status: 'queued',
    errorMessage: undefined,
    errorCode: undefined,
  });
  await flushSyncQueue(token, accountId);
}

function triggerAutoSync() {
  const token = localStorage.getItem('shikhor_token');
  if (token) {
    // Get distinct accounts with pending items
    offlineDb.offline_mutation_queue
      .filter((m) => m.status === 'queued')
      .toArray()
      .then((items) => {
        const accountIds = Array.from(new Set(items.map((i) => i.accountId)));
        for (const acc of accountIds) {
          flushSyncQueue(token, acc).catch(() => {});
        }
      });
  }
}
