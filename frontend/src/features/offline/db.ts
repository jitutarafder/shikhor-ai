import Dexie, { type EntityTable } from 'dexie';
import { KnowledgeArticleItem, OfflineMutation } from './types';

export class ShikhorOfflineDatabase extends Dexie {
  knowledge_articles!: EntityTable<KnowledgeArticleItem, 'id'>;
  offline_mutation_queue!: EntityTable<OfflineMutation, 'localUuid'>;

  constructor() {
    super('ShikhorOfflineDatabase');
    this.version(1).stores({
      knowledge_articles: 'id, cropType, category, version, updatedAt',
      offline_mutation_queue: 'localUuid, idempotencyKey, operationName, accountId, status, createdAt',
    });
  }

  /**
   * Clears private account-specific queued work and offline cache on logout (Rule 21 & Exit Criterion 4).
   */
  async clearAccountData(accountId?: string): Promise<void> {
    if (accountId) {
      await this.offline_mutation_queue.where('accountId').equals(accountId).delete();
    } else {
      await this.offline_mutation_queue.clear();
    }
  }

  async getPendingMutations(accountId: string): Promise<OfflineMutation[]> {
    return this.offline_mutation_queue
      .where('accountId')
      .equals(accountId)
      .filter((m) => m.status === 'queued' || m.status === 'failed')
      .sortBy('createdAt');
  }

  async upsertArticles(articles: KnowledgeArticleItem[]): Promise<void> {
    const now = new Date().toISOString();
    const enriched = articles.map((a) => ({
      ...a,
      downloadedAt: now,
    }));
    await this.knowledge_articles.bulkPut(enriched);
  }
}

export const offlineDb = new ShikhorOfflineDatabase();
