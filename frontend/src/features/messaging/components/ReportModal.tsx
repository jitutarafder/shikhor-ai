import React, { useState } from 'react';
import { X, ShieldAlert, CheckCircle } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { ModerationReportInput } from '../types';
import { getErrorMessage } from '../../../lib/errors';

interface ReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (report: ModerationReportInput) => Promise<void>;
  targetUserId: string;
  targetUserName: string;
  contentType?: 'user' | 'crop_listing' | 'equipment' | 'message';
  contentId?: string;
}

const REPORT_REASONS = [
  'স্প্যাম বা বারবার অপ্রাসঙ্গিক বার্তা প্রেরণ',
  'অশালীন, অপমানজনক বা হুমকিমূলক ভাষা ব্যবহার',
  'ভুয়া বা বিভ্রান্তিকর ফসলের তথ্য ও দাম',
  'প্রতারণা বা অননুমোদিত লেনদেনের চেষ্টা',
  'অন্যান্য আপত্তিজনক আচরণ',
];

export const ReportModal: React.FC<ReportModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  targetUserId,
  targetUserName,
  contentType = 'user',
  contentId,
}) => {
  const [selectedReason, setSelectedReason] = useState(REPORT_REASONS[0]);
  const [details, setDetails] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      await onSubmit({
        reportedUserId: targetUserId,
        contentType,
        contentId: contentId || targetUserId,
        reason: selectedReason,
        details: details.trim() || undefined,
      });
      setSubmitted(true);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'অভিযোগ জমা দেওয়া যায়নি। আবার চেষ্টা করুন।'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-100 p-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-600" />
            <h3 className="text-lg font-bold text-slate-900">অভিযোগ দাখিল করুন</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {submitted ? (
          <div className="py-6 text-center space-y-3">
            <CheckCircle className="w-12 h-12 text-emerald-600 mx-auto" />
            <h4 className="text-base font-bold text-slate-900">আপনার অভিযোগ জমা হয়েছে</h4>
            <p className="text-xs text-slate-600">
              আমাদের মডারেশন টিম দ্রুত বিষয়টি পর্যালোচনা করে প্রয়োজনীয় ব্যবস্থা গ্রহণ করবে।
            </p>
            <div className="pt-3">
              <Button
                variant="primary"
                onClick={() => {
                  setSubmitted(false);
                  onClose();
                }}
              >
                ঠিক আছে
              </Button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 text-sm">
            <p className="text-xs text-slate-600">
              ব্যবহারকারী <strong className="text-slate-900">{targetUserName}</strong> এর বিরুদ্ধে
              যথাযথ কারণ নির্বাচন করুন:
            </p>

            {error && (
              <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs">
                {error}
              </div>
            )}

            <div className="space-y-2">
              {REPORT_REASONS.map((reason) => (
                <label
                  key={reason}
                  className={`flex items-center gap-2.5 p-2.5 rounded-xl border cursor-pointer text-xs transition-colors ${
                    selectedReason === reason
                      ? 'border-emerald-600 bg-emerald-50/50 text-emerald-900 font-medium'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <input
                    type="radio"
                    name="reportReason"
                    value={reason}
                    checked={selectedReason === reason}
                    onChange={(e) => setSelectedReason(e.target.value)}
                    className="text-emerald-600 focus:ring-emerald-500"
                  />
                  <span>{reason}</span>
                </label>
              ))}
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1 text-xs">
                অতিরিক্ত বিবরণ (ঐচ্ছিক)
              </label>
              <textarea
                rows={3}
                placeholder="ঘটনাক্রম বা সুনির্দিষ্ট তথ্য লিখুন..."
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-end gap-2">
              <Button variant="outline" type="button" onClick={onClose} disabled={loading}>
                বাতিল
              </Button>
              <Button
                variant="primary"
                type="submit"
                className="bg-rose-600 hover:bg-rose-700 text-white"
                disabled={loading}
              >
                {loading ? 'জমা হচ্ছে...' : 'অভিযোগ পাঠান'}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
