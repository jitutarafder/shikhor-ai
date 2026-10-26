import React, { useState, useEffect } from 'react';
import { KnowledgeArticleItem } from '../features/offline/types';
import {
  getLocalKnowledgeArticles,
  syncKnowledgeToLocalDb,
} from '../features/offline/knowledgeApi';
import { Button } from '../components/ui/Button';
import {
  BookOpen,
  Download,
  Calendar,
  Layers,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  AlertCircle,
  WifiOff,
} from 'lucide-react';

export const OfflineKnowledge: React.FC = () => {
  const [articles, setArticles] = useState<KnowledgeArticleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [cropFilter, setCropFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const loadArticles = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getLocalKnowledgeArticles({
        cropType: cropFilter !== 'all' ? cropFilter : undefined,
        category: categoryFilter !== 'all' ? categoryFilter : undefined,
      });
      setArticles(data);
    } catch (err: any) {
      setError(err?.message || 'তথ্য লোড করা সম্ভব হয়নি।');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadArticles();
  }, [cropFilter, categoryFilter]);

  const handleManualSync = async () => {
    try {
      setSyncing(true);
      setSyncMsg(null);
      setError(null);
      const res = await syncKnowledgeToLocalDb();
      setSyncMsg(
        `সফলভাবে ${res.downloadedCount}টি নতুন বা হালনাগাদ তথ্য সংরক্ষিত হয়েছে। মোট সংরক্ষিত: ${res.totalLocalCount}টি।`
      );
      await loadArticles();
    } catch (err: any) {
      setError(
        navigator.onLine
          ? 'সার্ভার থেকে তথ্য হালনাগাদ করা যায়নি।'
          : 'আপনি অফলাইনে আছেন। ইন্টারনেট সংযোগ ছাড়া নতুন তথ্য ডাউনলোড করা সম্ভব নয়।'
      );
    } finally {
      setSyncing(false);
    }
  };

  const cropLabels: Record<string, string> = {
    all: 'সকল ফসল',
    paddy: 'ধান',
    potato: 'আলু',
    wheat: 'গম',
  };

  const categoryLabels: Record<string, string> = {
    all: 'সকল বিষয়',
    disease: 'রোগবালাই দমন',
    irrigation: 'পরিমিত সেচ ব্যবস্থা',
    fertilizer: 'সুষম সার প্রয়োগ',
    pest: 'পোকামাকড় নিয়ন্ত্রণ',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-emerald-950 via-forest-900 to-forest-800 rounded-3xl p-8 mb-8 text-white relative shadow-lg">
        <div className="max-w-2xl">
          <div className="flex items-center gap-2 mb-3">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-700/60 text-emerald-200 border border-emerald-500/30 inline-flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5" />
              অফলাইন কৃষি তথ্যভাণ্ডার
            </span>
            {!navigator.onLine && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500 text-slate-900 inline-flex items-center gap-1">
                <WifiOff className="w-3 h-3" />
                অফলাইন মোড
              </span>
            )}
          </div>
          <h1 className="text-3xl font-extrabold sm:text-4xl tracking-tight">
            যাচাইকৃত কৃষি প্রযুক্তি ও সমাধান
          </h1>
          <p className="mt-3 text-emerald-100 text-sm leading-relaxed">
            ইন্টারনেট সংযোগ ছাড়াই মাঠের মধ্যে বসে বিভিন্ন ফসলের রোগবালাই, সার ব্যবস্থাপনা এবং সেচ নির্দেশিকা পড়ুন। একবার ডাউনলোড হলে তা সবসময় আপনার ডিভাইসে সংরক্ষিত থাকবে।
          </p>

          <div className="mt-6 flex items-center gap-3">
            <Button
              variant="outline"
              onClick={handleManualSync}
              disabled={syncing}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs sm:text-sm flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              {syncing ? 'ডাউনলোড হচ্ছে...' : 'অফলাইন ডাটাবেস আপডেট করুন'}
            </Button>
          </div>
        </div>
      </div>

      {syncMsg && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-900 text-xs sm:text-sm flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{syncMsg}</span>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-xs sm:text-sm flex items-center gap-2">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-4 mb-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">ফসল নির্বাচন</label>
            <select
              value={cropFilter}
              onChange={(e) => setCropFilter(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
            >
              {Object.entries(cropLabels).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1">বিষয়ভিত্তিক বিভাগ</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="px-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
            >
              {Object.entries(categoryLabels).map(([k, v]) => (
                <option key={k} value={k}>
                  {v}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="text-xs text-slate-500 font-medium">
          মোট সংরক্ষিত নির্দেশিকা: <strong className="text-slate-800">{articles.length}টি</strong>
        </div>
      </div>

      {/* Articles Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 text-sm">তথ্য লোড হচ্ছে...</div>
      ) : articles.length === 0 ? (
        <div className="py-20 text-center bg-white rounded-3xl border border-slate-200/80 p-8 shadow-xs">
          <BookOpen className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800">কোনো নির্দেশিকা পাওয়া যায়নি</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            আপনার নির্বাচিত ফিল্টারে কোনো তথ্য নেই। ফিল্টার পরিবর্তন করুন অথবা অনলাইন থাকা অবস্থায় তথ্যভাণ্ডার সিঙ্ক করুন।
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {articles.map((item) => {
            const isExpanded = expandedId === item.id;
            const downloadedDateStr = item.downloadedAt
              ? new Date(item.downloadedAt).toLocaleDateString([], {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })
              : 'প্রাথমিক ডাটাবেস';

            return (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow p-6 flex flex-col justify-between"
              >
                <div>
                  {/* Badges & Meta (Exit Criterion 5: version and date) */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200/60">
                        {cropLabels[item.cropType] || item.cropType}
                      </span>
                      <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-slate-100 text-slate-700">
                        {categoryLabels[item.category] || item.category}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-slate-400 shrink-0">
                      <span className="flex items-center gap-1 font-mono">
                        <Layers className="w-3 h-3 text-emerald-600" />
                        v{item.version}
                      </span>
                    </div>
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-bold text-slate-900 leading-snug mb-2">
                    {item.titleBn}
                  </h3>

                  {/* Summary */}
                  <p className="text-xs text-slate-600 leading-relaxed mb-4">
                    {item.summaryBn}
                  </p>

                  {/* Expanded Body */}
                  {isExpanded && (
                    <div className="pt-4 border-t border-slate-100 space-y-4 animate-fade-in text-xs leading-relaxed text-slate-700">
                      <div>
                        <h4 className="font-bold text-slate-900 mb-1 text-sm">বিস্তারিত বিবরণ:</h4>
                        <p className="whitespace-pre-line">{item.contentBn}</p>
                      </div>

                      {item.recommendedPracticesBn && (
                        <div className="bg-emerald-50/70 p-3 rounded-xl border border-emerald-200/60">
                          <h4 className="font-bold text-emerald-900 mb-1 text-xs">
                            কৃষি বিজ্ঞানীদের সুপারিশকৃত করণীয়:
                          </h4>
                          <p className="whitespace-pre-line text-emerald-950 font-medium">
                            {item.recommendedPracticesBn}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer with Sync Date & Toggle */}
                <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-[11px] text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    সংরক্ষণ: {downloadedDateStr}
                  </span>

                  <button
                    onClick={() => setExpandedId(isExpanded ? null : item.id)}
                    className="font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1 transition-colors"
                  >
                    <span>{isExpanded ? 'সংক্ষিপ্ত করুন' : 'বিস্তারিত পড়ুন'}</span>
                    {isExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
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
