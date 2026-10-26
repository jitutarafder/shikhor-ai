import React, { useState, useEffect } from 'react';
import { submitPilotFeedbackApi } from '../api';
import { Button } from '../../../components/ui/Button';
import {
  MessageSquarePlus,
  Star,
  CheckCircle2,
  AlertTriangle,
  X,
  Smartphone,
  Wifi,
} from 'lucide-react';

interface PilotFeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTaskType?: string;
}

export const PilotFeedbackModal: React.FC<PilotFeedbackModalProps> = ({
  isOpen,
  onClose,
  defaultTaskType = 'crop_diagnosis',
}) => {
  const token = localStorage.getItem('shikhor_token');

  const [taskType, setTaskType] = useState(defaultTaskType);
  const [easeRating, setEaseRating] = useState<number>(4);
  const [banglaRating, setBanglaRating] = useState<number>(5);
  const [aiUnderstood, setAiUnderstood] = useState(true);
  const [deviceCategory, setDeviceCategory] = useState('low_end_android');
  const [networkType, setNetworkType] = useState('3g');
  const [comments, setComments] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setError('মতামত প্রদানের জন্য লগ ইন থাকা আবশ্যক।');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await submitPilotFeedbackApi(
        {
          task_type: taskType,
          ease_of_use_rating: easeRating,
          bangla_comprehension_rating: banglaRating,
          ai_limitations_understood: aiUnderstood,
          device_category: deviceCategory,
          network_type: networkType,
          comments: comments.trim() ? comments.trim() : undefined,
        },
        token
      );
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 1800);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'মতামত পাঠাতে সমস্যা হয়েছে।');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      setTaskType(defaultTaskType);
      setError(null);
      setSuccess(false);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, defaultTaskType]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="bg-canvas border border-line-200 rounded-3xl shadow-2xl max-w-lg w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="shrink-0 flex items-start justify-between gap-4 border-b border-line-200 p-5 sm:p-6 bg-canvas">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-forest-900 text-paddy-300">
              <MessageSquarePlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg sm:text-xl font-bold text-forest-900">
                আপনার মতামত ও অভিজ্ঞতা
              </h2>
              <p className="text-xs text-ink-600">
                আপনার মতামতের ভিত্তিতে শিখড় এআই সেবা আরও উন্নত করা হচ্ছে
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-ink-500 hover:text-forest-900 p-1.5 rounded-xl hover:bg-canvas-subtle transition-colors shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="overflow-y-auto flex-1 p-5 sm:p-6 scrollbar-thin">
          {success ? (
            <div className="py-10 text-center space-y-3">
              <CheckCircle2 className="w-12 h-12 text-forest-700 mx-auto animate-bounce" />
              <h3 className="text-base font-bold text-forest-900">
                আপনার মতামত সফলভাবে গৃহীত হয়েছে!
              </h3>
              <p className="text-xs text-ink-600">
                শিখড় এআই প্ল্যাটফর্মের উন্নয়নে আপনার মূল্যবান মতামতের জন্য ধন্যবাদ।
              </p>
            </div>
          ) : (
            <form id="feedback-form" onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-danger-500/10 border border-danger-500/30 text-danger-700 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Task Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-ink-900">
                কোন সেবার বিষয়ে মতামত দিচ্ছেন?
              </label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                className="w-full px-3 py-2 border border-line-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-forest-700 text-ink-900"
              >
                <option value="crop_diagnosis">ফসলের রোগ নির্ণয় (Crop Diagnosis)</option>
                <option value="equipment_rental">কৃষিযন্ত্র ভাড়া (Equipment Rental)</option>
                <option value="weather_plan">আবহাওয়া ও স্প্রে পরিকল্পনা (Weather Plan)</option>
                <option value="crop_marketplace">ফসল কেনাবেচা (Crop Marketplace)</option>
                <option value="offline_sync">অফলাইন সিঙ্ক্রোনাইজেশন (Offline Sync)</option>
                <option value="general_onboarding">সাধারণ অনবোর্ডিং ও ভাষা (General)</option>
              </select>
            </div>

            {/* Ease of Use (1-5) */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-ink-900">ব্যবহার সহজতা:</span>
                <span className="text-forest-700 font-bold">{easeRating} / ৫</span>
              </div>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setEaseRating(star)}
                    className={`flex-1 py-1.5 rounded-lg border text-xs font-semibold flex items-center justify-center gap-1 transition-all ${
                      easeRating >= star
                        ? 'bg-emerald-50 border-forest-700 text-forest-900'
                        : 'bg-white border-line-200 text-ink-600 hover:bg-canvas-subtle'
                    }`}
                  >
                    <Star
                      className={`w-3.5 h-3.5 ${
                        easeRating >= star ? 'fill-forest-700 text-forest-700' : 'text-ink-300'
                      }`}
                    />
                    <span>{star}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Bangla Comprehension (1-5) */}
            <div className="space-y-1.5">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-ink-900">বাংলার ভাষা ও শব্দের স্পষ্টতা:</span>
                <span className="text-forest-700 font-bold">{banglaRating} / ৫</span>
              </div>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    onClick={() => setBanglaRating(star)}
                    className={`flex-1 py-1.5 rounded-lg border text-xs font-semibold flex items-center justify-center gap-1 transition-all ${
                      banglaRating >= star
                        ? 'bg-emerald-50 border-forest-700 text-forest-900'
                        : 'bg-white border-line-200 text-ink-600 hover:bg-canvas-subtle'
                    }`}
                  >
                    <Star
                      className={`w-3.5 h-3.5 ${
                        banglaRating >= star ? 'fill-forest-700 text-forest-700' : 'text-ink-300'
                      }`}
                    />
                    <span>{star}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Device and Network Row */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-ink-900 flex items-center gap-1">
                  <Smartphone className="w-3.5 h-3.5 text-forest-700" />
                  <span>ডিভাইসের ধরন:</span>
                </label>
                <select
                  value={deviceCategory}
                  onChange={(e) => setDeviceCategory(e.target.value)}
                  className="w-full px-2.5 py-1.5 border border-line-200 rounded-lg text-xs bg-white text-ink-900"
                >
                  <option value="low_end_android">কমদামী অ্যান্ড্রয়েড</option>
                  <option value="mid_android">সাধারণ স্মার্টফোন</option>
                  <option value="feature_browser">ফিচার ব্রাউজার</option>
                  <option value="desktop">কম্পিউটার / ল্যাপটপ</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-ink-900 flex items-center gap-1">
                  <Wifi className="w-3.5 h-3.5 text-emerald-700" />
                  <span>ইন্টারনেট গতি:</span>
                </label>
                <select
                  value={networkType}
                  onChange={(e) => setNetworkType(e.target.value)}
                  className="w-full px-2.5 py-1.5 border border-line-200 rounded-lg text-xs bg-white text-ink-900"
                >
                  <option value="3g">3G সাধারণ নেটওয়ার্ক</option>
                  <option value="4g_wifi">4G বা দ্রুত ওয়াইফাই</option>
                  <option value="2g_slow">2G ধীরগতির নেটওয়ার্ক</option>
                  <option value="offline_intermittent">ঘন ঘন বিচ্ছিন্ন হয়</option>
                </select>
              </div>
            </div>

            {/* AI Limitations Checkbox */}
            <div className="p-3 rounded-xl bg-field-wash border border-line-200 flex items-start gap-2.5">
              <input
                type="checkbox"
                id="ai-limits"
                checked={aiUnderstood}
                onChange={(e) => setAiUnderstood(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded text-forest-700 focus:ring-forest-700 cursor-pointer"
              />
              <label htmlFor="ai-limits" className="text-xs text-ink-800 leading-snug cursor-pointer">
                আমি বুঝতে পেরেছি যে শিখড় এআই-এর ফলাফল সিদ্ধান্ত সহায়তা মাত্র, সরাসরি কৃষি কর্মকর্তা বা নিশ্চিত প্রেসক্রিপশন নয়।
              </label>
            </div>

            {/* Comments */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-ink-900">
                অতিরিক্ত মন্তব্য বা পরামর্শ (ঐচ্ছিক):
              </label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="কোনো শব্দের অর্থ বা কোনো অংশ বুঝতে সমস্যা হলে লিখুন..."
                rows={2}
                maxLength={500}
                className="w-full px-3 py-2 border border-line-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-forest-700 text-ink-900 placeholder:text-ink-400"
              />
            </div>

          </form>
        )}
      </div>

      {/* Fixed Footer */}
      {!success && (
        <div className="shrink-0 p-4 sm:p-5 border-t border-line-200 bg-surface/50 flex justify-end gap-3">
          <Button type="button" variant="outline" size="sm" onClick={onClose} disabled={loading}>
            বাতিল
          </Button>
          <Button type="submit" form="feedback-form" variant="primary" size="sm" disabled={loading} className="px-5">
            {loading ? 'জমা দেওয়া হচ্ছে...' : 'মতামত জমা দিন'}
          </Button>
        </div>
      )}
    </div>
  </div>
);
};
