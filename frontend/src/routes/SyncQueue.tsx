import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MUTATION_STATUS_LABELS,
  OPERATION_LABELS,
  OfflineMutation,
} from '../features/offline/types';
import { offlineDb } from '../features/offline/db';
import {
  deleteQueuedMutation,
  flushSyncQueue,
  retryQueuedMutation,
  subscribeSyncState,
} from '../features/offline/syncEngine';
import { Button } from '../components/ui/Button';
import {
  Layers,
  RefreshCw,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Clock,
  ArrowLeft,
  WifiOff,
} from 'lucide-react';

export const SyncQueue: React.FC = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('shikhor_token');
  const [mutations, setMutations] = useState<OfflineMutation[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingAll, setSyncingAll] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [currentAccountId, setCurrentAccountId] = useState<string>('');

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }

    fetch('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((user) => {
        if (user?.id) {
          setCurrentAccountId(user.id);
          loadQueue(user.id);
        }
      })
      .catch(() => {});
  }, [token]);

  const loadQueue = async (accId?: string) => {
    try {
      setLoading(true);
      const targetId = accId || currentAccountId;
      let allMutations: OfflineMutation[] = [];
      if (targetId) {
        allMutations = await offlineDb.offline_mutation_queue
          .where('accountId')
          .equals(targetId)
          .sortBy('createdAt');
      } else {
        allMutations = await offlineDb.offline_mutation_queue.toArray();
      }
      setMutations(allMutations.reverse());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const unsub = subscribeSyncState(() => {
      if (currentAccountId) {
        loadQueue(currentAccountId);
      }
    });
    return unsub;
  }, [currentAccountId]);

  const handleSyncAll = async () => {
    if (!token || !currentAccountId) return;
    try {
      setSyncingAll(true);
      setSyncResult(null);
      const res = await flushSyncQueue(token, currentAccountId);
      setSyncResult(
        `সিঙ্ক সম্পন্ন: ${res.syncedCount}টি সফল, ${res.failedCount}টি অসফল/ব্যর্থ।`
      );
      await loadQueue(currentAccountId);
    } catch (err: any) {
      setSyncResult(err?.message || 'সার্ভারের সাথে সংযোগ স্থাপন করা যায়নি।');
    } finally {
      setSyncingAll(false);
    }
  };

  const handleRetry = async (localUuid: string) => {
    if (!token || !currentAccountId) return;
    await retryQueuedMutation(localUuid, token, currentAccountId);
    await loadQueue(currentAccountId);
  };

  const handleDelete = async (localUuid: string) => {
    if (window.confirm('আপনি কি এই অপেক্ষমাণ কার্যক্রমটি মুছে ফেলতে চান?')) {
      await deleteQueuedMutation(localUuid);
      await loadQueue(currentAccountId);
    }
  };

  const handleClearSynced = async () => {
    await offlineDb.offline_mutation_queue.where('status').equals('synced').delete();
    await loadQueue(currentAccountId);
  };

  const pendingCount = mutations.filter(
    (m) => m.status === 'queued' || m.status === 'failed'
  ).length;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <button
            onClick={() => navigate('/app')}
            className="text-xs text-slate-500 hover:text-emerald-700 flex items-center gap-1.5 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            ড্যাশবোর্ডে ফিরে যান
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 flex items-center gap-2.5">
            <Layers className="w-7 h-7 text-emerald-700" />
            অফলাইন সিঙ্ক কিউ (Sync Queue)
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            ইন্টারনেট না থাকা অবস্থায় করা ভাড়ার অনুরোধ, ফসল তালিকা বা বার্তা এখানে সংরক্ষিত থাকে
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <Button
            variant="outline"
            className="text-xs"
            onClick={handleClearSynced}
            disabled={!mutations.some((m) => m.status === 'synced')}
          >
            সম্পন্নগুলো মুছুন
          </Button>
          <Button
            variant="primary"
            onClick={handleSyncAll}
            disabled={syncingAll || pendingCount === 0 || !navigator.onLine}
            className="text-xs flex items-center gap-2"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncingAll ? 'animate-spin' : ''}`} />
            {syncingAll ? 'সিঙ্ক হচ্ছে...' : 'এখনই সব সিঙ্ক করুন'}
          </Button>
        </div>
      </div>

      {/* Network Warning Banner */}
      {!navigator.onLine && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-2xl text-amber-900 text-xs sm:text-sm flex items-center gap-2.5">
          <WifiOff className="w-5 h-5 text-amber-700 shrink-0" />
          <span>
            <strong>অফলাইন মোড সক্রিয়:</strong> বর্তমানে ইন্টারনেট সংযোগ নেই। নতুন অনুরোধগুলো ডিভাইসের সুরক্ষিত ডাটাবেসে জমা থাকবে এবং ইন্টারনেট সংযোগ সক্রিয় হলে সিঙ্ক হবে।
          </span>
        </div>
      )}

      {syncResult && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-900 text-xs sm:text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{syncResult}</span>
        </div>
      )}

      {/* Mutations Queue List (Exit Criterion 3: Inspect, retry, or delete) */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-sm">সিঙ্ক কিউ লোড হচ্ছে...</div>
      ) : mutations.length === 0 ? (
        <div className="py-20 text-center bg-white rounded-3xl border border-slate-200/80 p-8 shadow-xs">
          <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">কোনো অপেক্ষমাণ কার্যক্রম নেই</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            আপনার সকল অনুরোধ ও তথ্য সার্ভারে সফলভাবে সিঙ্ক ও হালনাগাদ রয়েছে।
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {mutations.map((mut) => {
            const statusInfo = MUTATION_STATUS_LABELS[mut.status];
            const opNameBn = OPERATION_LABELS[mut.operationName] || mut.operationName;
            const dateStr = new Date(mut.createdAt).toLocaleString([], {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <div
                key={mut.localUuid}
                className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-slate-900 text-sm">{opNameBn}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-semibold ${statusInfo.color}`}
                    >
                      {statusInfo.label}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      (চেষ্টা: {mut.retryCount})
                    </span>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <Clock className="w-3.5 h-3.5 text-slate-400" />
                    <span>সংরক্ষণ: {dateStr}</span>
                    <span className="text-slate-300">•</span>
                    <span className="font-mono text-[11px] text-slate-400 truncate">
                      কী: {mut.idempotencyKey.slice(0, 18)}...
                    </span>
                  </div>

                  {/* Failure Message */}
                  {mut.errorMessage && (
                    <div className="p-2 bg-rose-50 border border-rose-100 rounded-lg text-rose-700 text-xs flex items-center gap-1.5">
                      <AlertCircle className="w-4 h-4 shrink-0" />
                      <span>{mut.errorMessage}</span>
                    </div>
                  )}

                  {/* Payload Summary Preview */}
                  <div className="bg-slate-50 rounded-lg p-2 text-[11px] text-slate-600 font-mono overflow-x-auto">
                    {mut.operationName === 'CREATE_CROP_LISTING' && (
                      <span>
                        ফসল: {String(mut.payload.cropName || '')} • পরিমাণ: {String(mut.payload.quantity || '')}{' '}
                        {String(mut.payload.quantityUnit || '')} • মূল্য: ৳{String(mut.payload.pricePerUnit || '')}
                      </span>
                    )}
                    {mut.operationName === 'CREATE_RENTAL_REQUEST' && (
                      <span>
                        যন্ত্র আইডি: {String(mut.payload.equipmentId || '')} • তারিখ: {String(mut.payload.rentalDate || '')} •
                        মেয়াদ: {String(mut.payload.durationUnits || '')} একক
                      </span>
                    )}
                    {mut.operationName === 'SEND_MESSAGE' && (
                      <span>বার্তা: "{String(mut.payload.content || '')}"</span>
                    )}
                  </div>
                </div>

                {/* Action Buttons: Retry / Delete */}
                <div className="flex items-center gap-2 sm:self-center shrink-0">
                  {(mut.status === 'failed' || mut.status === 'queued') && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleRetry(mut.localUuid)}
                      disabled={!navigator.onLine}
                      className="text-xs flex items-center gap-1 py-1.5"
                    >
                      <RefreshCw className="w-3 h-3" />
                      পুনরায় চেষ্টা
                    </Button>
                  )}

                  <button
                    onClick={() => handleDelete(mut.localUuid)}
                    title="মুছে ফেলুন"
                    className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
