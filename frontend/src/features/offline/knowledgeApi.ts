import { offlineDb } from './db';
import { KnowledgeArticleItem } from './types';

export interface KnowledgeFilterOptions {
  cropType?: string;
  category?: string;
}

export async function fetchRemoteKnowledgeCatalog(
  filters?: KnowledgeFilterOptions,
  sinceVersion?: number
): Promise<{ articles: KnowledgeArticleItem[]; latestVersion: number }> {
  const params = new URLSearchParams();
  if (filters?.cropType) params.append('crop_type', filters.cropType);
  if (filters?.category) params.append('category', filters.category);
  if (sinceVersion !== undefined) params.append('since_version', sinceVersion.toString());

  const url = `/api/v1/knowledge${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'কৃষি তথ্য ভাণ্ডার লোড করা যায়নি।');
  }
  return {
    articles: data.articles || [],
    latestVersion: data.latestVersion || 1,
  };
}

export async function syncKnowledgeToLocalDb(): Promise<{
  downloadedCount: number;
  totalLocalCount: number;
}> {
  // 1. Find highest version in local IndexedDB
  const localArticles = await offlineDb.knowledge_articles.toArray();
  const highestVersion = localArticles.reduce((max, a) => Math.max(max, a.version), 0);

  // 2. Fetch incrementally from backend
  const { articles } = await fetchRemoteKnowledgeCatalog(
    undefined,
    highestVersion > 0 ? highestVersion : undefined
  );

  // 3. Upsert into Dexie
  if (articles.length > 0) {
    await offlineDb.upsertArticles(articles);
  }

  const updatedTotal = await offlineDb.knowledge_articles.count();
  return {
    downloadedCount: articles.length,
    totalLocalCount: updatedTotal,
  };
}

export async function getLocalKnowledgeArticles(
  filters?: KnowledgeFilterOptions
): Promise<KnowledgeArticleItem[]> {
  let collection = offlineDb.knowledge_articles.toCollection();

  if (filters?.cropType && filters.cropType !== 'all') {
    collection = offlineDb.knowledge_articles.where('cropType').equals(filters.cropType);
  }

  let articles = await collection.toArray();

  if (filters?.category && filters.category !== 'all') {
    articles = articles.filter((a) => a.category === filters.category);
  }

  // If local DB is empty and browser is online, trigger initial sync
  if (articles.length === 0 && navigator.onLine) {
    try {
      await syncKnowledgeToLocalDb();
      articles = await offlineDb.knowledge_articles.toArray();
      if (filters?.cropType && filters.cropType !== 'all') {
        articles = articles.filter((a) => a.cropType === filters.cropType);
      }
      if (filters?.category && filters.category !== 'all') {
        articles = articles.filter((a) => a.category === filters.category);
      }
    } catch {
      // Fallback gracefully to empty array
    }
  }

  return articles;
}
