/**
 * Offline Storage, Knowledge Library, and Synchronization types.
 * Strictly complies with:
 * - AGENTS.md Rule 21: Idempotent offline mutations with local UUID, key, operation name, payload.
 * - AGENTS.md Rule 22: Service-worker and cache safety; clean account data on logout.
 * - phases.md Phase 7 Exit Criteria:
 *   - Offline UI never reports server success prematurely.
 *   - Queued mutations synchronize without duplication.
 *   - Previously downloaded knowledge shows version/date.
 */

export interface KnowledgeArticleItem {
  id: string;
  cropType: string;
  category: string;
  titleBn: string;
  titleEn?: string | null;
  summaryBn: string;
  contentBn: string;
  recommendedPracticesBn?: string | null;
  version: number;
  publishedAt: string;
  updatedAt: string;
  downloadedAt?: string;
}

export type MutationStatus = 'queued' | 'syncing' | 'synced' | 'failed';

export interface OfflineMutation {
  localUuid: string;
  idempotencyKey: string;
  operationName: string;
  payload: Record<string, unknown>;
  accountId: string;
  createdAt: string;
  retryCount: number;
  status: MutationStatus;
  errorMessage?: string;
  errorCode?: string;
  responsePayload?: Record<string, unknown>;
}

export const OPERATION_LABELS: Record<string, string> = {
  CREATE_RENTAL_REQUEST: 'কৃষিযন্ত্র ভাড়ার অনুরোধ',
  CREATE_CROP_LISTING: 'নতুন ফসল বিক্রয় তালিকা',
  SEND_MESSAGE: 'কৃষক-পাইকার বার্তা প্রেরণ',
};

export const MUTATION_STATUS_LABELS: Record<MutationStatus, { label: string; color: string }> = {
  queued: { label: 'সিঙ্কের অপেক্ষায়', color: 'bg-amber-100 text-amber-800' },
  syncing: { label: 'সিঙ্ক হচ্ছে...', color: 'bg-sky-100 text-sky-800' },
  synced: { label: 'সিঙ্ক সম্পন্ন', color: 'bg-emerald-100 text-emerald-800' },
  failed: { label: 'সিঙ্ক ব্যর্থ', color: 'bg-rose-100 text-rose-800' },
};
