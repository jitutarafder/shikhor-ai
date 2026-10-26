import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  Stethoscope,
  AlertTriangle,
  CheckCircle2,
  Filter,
  ArrowLeft,
  X,
  Clock,
  RefreshCw,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { CropCase } from '../features/crop-assistant/types';
import { getPendingExpertCasesApi, submitExpertCaseReviewApi } from '../features/expert/api';
import { ExpertCaseReviewCreateInput } from '../features/expert/types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { CropLeafImage } from '../components/crop-assistant/CropLeafImage';

export const ExpertPortal: React.FC = () => {
  const { user, token, isAuthenticated } = useAuth();

  const [pendingCases, setPendingCases] = useState<CropCase[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [selectedCrop, setSelectedCrop] = useState<string>('all');

  // Review Modal State
  const [activeCase, setActiveCase] = useState<CropCase | null>(null);
  const [diagnosis, setDiagnosis] = useState('');
  const [treatment, setTreatment] = useState('');
  const [severity, setSeverity] = useState<'mild' | 'moderate' | 'severe'>('moderate');
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const isAuthorized =
    isAuthenticated && (user?.role === 'expert' || user?.role === 'admin');

  useEffect(() => {
    if (isAuthorized && token) {
      loadPendingCases();
    }
  }, [isAuthorized, token, selectedCrop]);

  const loadPendingCases = async () => {
    if (!token) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const cropFilter = selectedCrop === 'all' ? undefined : selectedCrop;
      const data = await getPendingExpertCasesApi(token, cropFilter);
      setPendingCases(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'পেন্ডিং কেস তালিকা লোড করা যায়নি।');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenReview = (c: CropCase) => {
    setActiveCase(c);
    setDiagnosis(c.possibleCondition?.replace(' (কৃষিবিদ দ্বারা যাচাইকৃত)', '') || '');
    setTreatment('');
    setSeverity('moderate');
    setNotes('');
    setFormError(null);
  };

  const handleCloseReview = () => {
    setActiveCase(null);
    setFormError(null);
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !activeCase) return;

    if (!diagnosis.trim()) {
      setFormError('অনুগ্রহ করে সঠিক রোগ বা সমস্যার নাম লিখুন।');
      return;
    }
    if (!treatment.trim() || treatment.trim().length < 10) {
      setFormError('অনুমোদিত চিকিৎসা বা প্রেসক্রিপশন ন্যূনতম ১০ অক্ষরের হতে হবে।');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    const payload: ExpertCaseReviewCreateInput = {
      reviewedDiagnosis: diagnosis.trim(),
      prescribedTreatment: treatment.trim(),
      severityLevel: severity,
      expertNotes: notes.trim() ? notes.trim() : undefined,
    };

    try {
      await submitExpertCaseReviewApi(activeCase.id, payload, token);
      setSuccessMsg(
        `কেস #${activeCase.id.slice(0, 8)} সফলভাবে যাচাই ও প্রেসক্রিপশন প্রদান করা হয়েছে!`
      );
      // Remove reviewed case from the pending queue
      setPendingCases((prev) => prev.filter((item) => item.id !== activeCase.id));
      setActiveCase(null);
      // Clear success notification after 5s
      setTimeout(() => setSuccessMsg(null), 5000);
    } catch (err: any) {
      setFormError(err.message || 'বিশেষজ্ঞ রিভিউ জমা দিতে সমস্যা হয়েছে।');
    } finally {
      setIsSubmitting(false);
    }
  };

  // If not logged in
  if (!isAuthenticated) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <Card className="max-w-md w-full p-8 text-center space-y-4">
          <Stethoscope className="w-12 h-12 text-forest-700 mx-auto" />
          <h1 className="text-xl font-bold text-forest-900">লগ ইন আবশ্যক</h1>
          <p className="text-sm text-ink-600">
            কৃষি বিশেষজ্ঞ পোর্টালে প্রবেশ করতে অনুমোদিত কৃষিবিদ বা অ্যাডমিন হিসেবে লগ ইন করুন।
          </p>
          <Link to="/login">
            <Button variant="primary" fullWidth size="md">
              লগ ইন পৃষ্ঠায় যান
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  // If role is unauthorized
  if (!isAuthorized) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <Card className="max-w-md w-full p-8 text-center space-y-4">
          <AlertTriangle className="w-12 h-12 text-paddy-400 mx-auto" />
          <h1 className="text-xl font-bold text-forest-900">অননুমোদিত প্রবেশাধিকার (403)</h1>
          <p className="text-sm text-ink-600">
            এই পোর্টালটি শুধুমাত্র অনুমোদিত কৃষি কর্মকর্তা/বিশেষজ্ঞ (expert) এবং প্রশাসকদের (admin) জন্য সংরক্ষিত।
          </p>
          <Link to="/app">
            <Button variant="secondary" fullWidth size="md">
              ড্যাশবোর্ডে ফিরে যান
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-line-200 pb-5">
        <div>
          <Link
            to="/app"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-forest-700 hover:underline mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>ড্যাশবোর্ডে ফিরে যান</span>
          </Link>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-leaf-100 text-forest-700 flex items-center justify-center shrink-0">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-forest-900 flex items-center gap-2">
                <span>কৃষি বিশেষজ্ঞ কেস-রিভিউ পোর্টাল</span>
                <Badge variant="success">Expert Only</Badge>
              </h1>
              <p className="text-sm text-ink-600 mt-0.5">
                এআই মডেলের অনিশ্চিত বা বিশেষজ্ঞের পর্যালোচনা প্রত্যাশী জটিল ফসলের রোগ বিশ্লেষণ ও প্রেসক্রিপশন
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 bg-surface px-3 py-1.5 rounded-btn border border-line-200">
            <Filter className="w-4 h-4 text-ink-600" />
            <select
              value={selectedCrop}
              onChange={(e) => setSelectedCrop(e.target.value)}
              className="bg-transparent text-xs font-semibold text-forest-900 focus:outline-hidden"
              aria-label="ফসল ফিল্টার"
            >
              <option value="all">সকল ফসল</option>
              <option value="ধান">ধান (Rice)</option>
              <option value="আলু">আলু (Potato)</option>
              <option value="টমেটো">টমেটো (Tomato)</option>
              <option value="গম">গম (Wheat)</option>
              <option value="ভুট্টা">ভুট্টা (Maize)</option>
            </select>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={loadPendingCases}
            isLoading={isLoading}
            className="text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            <span>রিফ্রেশ</span>
          </Button>
        </div>
      </div>

      {/* Global Alerts */}
      {successMsg && (
        <div className="p-4 bg-leaf-100 border border-leaf-500/30 text-forest-900 rounded-btn text-sm flex items-center gap-2.5 animate-in fade-in">
          <CheckCircle2 className="w-5 h-5 text-forest-700 shrink-0" />
          <span className="font-medium">{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-4 bg-danger-600/10 border border-danger-600/20 text-danger-600 rounded-btn text-sm flex items-center gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Stats Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="p-5 border-line-200 bg-surface flex items-center gap-4">
          <div className="w-12 h-12 rounded-btn bg-paddy-400/20 text-soil-700 flex items-center justify-center shrink-0">
            <Clock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-forest-900">{pendingCases.length}</div>
            <div className="text-xs text-ink-600">অপেক্ষমাণ কেস (Pending Review)</div>
          </div>
        </Card>

        <Card className="p-5 border-line-200 bg-surface flex items-center gap-4">
          <div className="w-12 h-12 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center shrink-0">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-forest-900">{user?.fullName}</div>
            <div className="text-xs text-ink-600">অনুমোদিত বিশেষজ্ঞ অ্যাকাউন্ট</div>
          </div>
        </Card>

        <Card className="p-5 border-line-200 bg-surface flex items-center gap-4">
          <div className="w-12 h-12 rounded-btn bg-forest-700/10 text-forest-700 flex items-center justify-center shrink-0">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-forest-900">মান নিয়ন্ত্রণ</div>
            <div className="text-xs text-ink-600">নিয়ম ১৯: মানব পর্যালোচনা বাধ্যবাধকতা</div>
          </div>
        </Card>
      </div>

      {/* Pending Cases Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-forest-900 flex items-center gap-2">
            <span>পর্যালোচনার জন্য অপেক্ষমাণ কেসসমূহ</span>
            <span className="text-xs bg-leaf-100 text-forest-900 px-2 py-0.5 rounded-full font-semibold">
              {pendingCases.length}
            </span>
          </h2>
          <span className="text-xs text-ink-600">
            সর্বশেষ আপলোডকৃত অনির্দিষ্ট বা উচ্চ ঝুঁকির কেসগুলো অগ্রাধিকার ভিত্তিতে প্রদর্শিত হচ্ছে
          </span>
        </div>

        {isLoading ? (
          <div className="text-center py-16 text-ink-600 text-sm">
            অপেক্ষমাণ কেস লোড হচ্ছে…
          </div>
        ) : pendingCases.length === 0 ? (
          <Card className="p-12 text-center border-line-200 space-y-3 bg-surface/50">
            <CheckCircle2 className="w-12 h-12 text-forest-700 mx-auto" />
            <h3 className="text-base font-bold text-forest-900">
              বর্তমানে পর্যালোচনার জন্য কোনো কেস অপেক্ষমাণ নেই!
            </h3>
            <p className="text-xs text-ink-600 max-w-md mx-auto">
              সব এআই রোগ কেস স্বাভাবিক আস্থা সীমার মধ্যে রয়েছে অথবা বিশেষজ্ঞ পর্যালোচনা সম্পন্ন হয়েছে।
            </p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pendingCases.map((c) => (
              <Card
                key={c.id}
                className="p-5 border-line-200 bg-canvas space-y-4 shadow-xs flex flex-col justify-between"
              >
                <div className="space-y-3">
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-2 border-b border-line-200 pb-3">
                    <div>
                      <span className="text-xs font-semibold text-forest-700 uppercase tracking-wider block">
                        ফসল: {c.cropType}
                      </span>
                      <h3 className="font-bold text-base text-forest-900 mt-0.5 line-clamp-1">
                        {c.possibleCondition || 'অনির্ধারিত রোগ বা সংক্রমণ'}
                      </h3>
                    </div>
                    <Badge variant={c.escalationRecommended ? 'danger' : 'warning'}>
                      {c.escalationRecommended ? 'জরুরি পরামর্শ' : 'অনিশ্চিত এআই'}
                    </Badge>
                  </div>

                  {/* Crop Leaf Photo */}
                  <div className="space-y-1">
                    <CropLeafImage
                      caseId={c.id}
                      imageFilename={c.imageFilename}
                      cropType={c.cropType}
                      token={token}
                      className="w-full h-44 object-cover rounded-btn"
                    />
                  </div>

                  {/* AI Diagnosis Details */}
                  <div className="space-y-1.5 text-xs text-ink-600">
                    <div className="flex items-center justify-between">
                      <span>এআই কনফিডেন্স:</span>
                      <span className="font-semibold text-ink-900">
                        {Math.round(c.confidence * 100)}% ({c.confidenceBand})
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>কেস আইডি:</span>
                      <span className="font-mono text-[11px] text-ink-900">#{c.id.slice(0, 8)}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>তারিখ:</span>
                      <span>{new Date(c.createdAt).toLocaleDateString('bn-BD')}</span>
                    </div>
                  </div>

                  {/* Reported Symptoms */}
                  {c.symptomsDescription && (
                    <div className="bg-surface p-3 rounded-btn border border-line-200 text-xs">
                      <span className="font-semibold text-forest-900 block mb-0.5">
                        কৃষকের বর্ণিত লক্ষণ:
                      </span>
                      <p className="text-ink-700 italic line-clamp-2">
                        "{c.symptomsDescription}"
                      </p>
                    </div>
                  )}

                  {/* AI Reason Summary */}
                  {c.reasonSummary && c.reasonSummary.length > 0 && (
                    <div className="text-xs text-ink-600 space-y-1">
                      <span className="font-semibold text-forest-900">এআই পর্যবেক্ষণ:</span>
                      <ul className="list-disc pl-4 space-y-0.5 text-[11px]">
                        {c.reasonSummary.slice(0, 2).map((r, idx) => (
                          <li key={idx} className="line-clamp-1">
                            {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Review Action Button */}
                <div className="pt-3 border-t border-line-200">
                  <Button
                    variant="primary"
                    size="sm"
                    fullWidth
                    onClick={() => handleOpenReview(c)}
                    className="text-xs"
                  >
                    <Stethoscope className="w-3.5 h-3.5 mr-1" />
                    <span>পর্যালোচনা ও প্রেসক্রিপশন লিখুন</span>
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Review Modal Dialog */}
      {activeCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/60 backdrop-blur-xs animate-in fade-in">
          <Card className="max-w-2xl w-full p-6 bg-canvas border-line-200 shadow-xl max-h-[90vh] overflow-y-auto space-y-5">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-line-200 pb-3">
              <div className="flex items-center gap-2">
                <Stethoscope className="w-5 h-5 text-forest-700" />
                <h3 className="text-lg font-bold text-forest-900">
                  কৃষিবিদ প্রেসক্রিপশন ও রোগ নিশ্চিতকরণ
                </h3>
              </div>
              <button
                onClick={handleCloseReview}
                className="text-ink-600 hover:text-ink-900 p-1 rounded-btn hover:bg-surface"
                aria-label="বন্ধ করুন"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Case Snapshot with Leaf Photo */}
            <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 bg-surface p-4 rounded-card border border-line-200">
              <div className="sm:col-span-5">
                <CropLeafImage
                  caseId={activeCase.id}
                  imageFilename={activeCase.imageFilename}
                  cropType={activeCase.cropType}
                  token={token}
                  className="w-full h-44 object-cover rounded-btn"
                />
              </div>
              <div className="sm:col-span-7 space-y-2 text-xs flex flex-col justify-between">
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-ink-900 font-semibold border-b border-line-200 pb-1">
                    <span className="text-sm font-bold text-forest-900">ফসল: {activeCase.cropType}</span>
                    <span className="font-mono text-ink-600 text-[11px]">#{activeCase.id.slice(0, 8)}</span>
                  </div>
                  {activeCase.symptomsDescription && (
                    <p className="text-ink-700">
                      <span className="font-semibold text-forest-900">কৃষকের সমস্যা বর্ণনা:</span>{' '}
                      {activeCase.symptomsDescription}
                    </p>
                  )}
                  {activeCase.possibleCondition && (
                    <p className="text-ink-700">
                      <span className="font-semibold text-forest-900">প্রাথমিক এআই ধারণা:</span>{' '}
                      {activeCase.possibleCondition}
                    </p>
                  )}
                </div>
                <div className="text-[11px] text-forest-700 bg-leaf-100/70 p-2 rounded-btn font-medium">
                  🔍 ছবিতে ক্লিক করে ফুল-স্ক্রিন জুম করে পাতার দাগ ও মার্জিন নিখুঁতভাবে পর্যবেক্ষণ করুন।
                </div>
              </div>
            </div>

            {/* Error Message inside Modal */}
            {formError && (
              <div className="p-3 bg-danger-600/10 border border-danger-600/20 text-danger-600 rounded-btn text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmitReview} className="space-y-4">
              {/* Confirmed Diagnosis Input */}
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  যাচাইকৃত রোগ / সমস্যার নাম <span className="text-danger-600">*</span>
                </label>
                <input
                  type="text"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="যেমন: ধানের ব্লাস্ট রোগ (Leaf Blast), আলুর নাবী ধসা..."
                  className="w-full px-3.5 min-h-[44px] rounded-btn border border-line-200 bg-canvas text-sm focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                  required
                />
              </div>

              {/* Severity Level */}
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  আক্রমণের তীব্রতা মাত্রা <span className="text-danger-600">*</span>
                </label>
                <select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value as any)}
                  className="w-full px-3.5 min-h-[44px] rounded-btn border border-line-200 bg-canvas text-sm focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                >
                  <option value="mild">মৃদু (Mild Severity)</option>
                  <option value="moderate">মাঝারি (Moderate Severity)</option>
                  <option value="severe">মারাত্মক / তীব্র (Severe / Urgent)</option>
                </select>
              </div>

              {/* Treatment / Prescription */}
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  অনুমোদিত প্রেসক্রিপশন ও দমন ব্যবস্থাপনা <span className="text-danger-600">*</span>
                </label>
                <p className="text-xs text-ink-600 mb-1.5">
                  কৃষকের সুরক্ষার স্বার্থে নির্ভরযোগ্য বালাইনাশকের জেনেরিক নাম, অনুমোদিত মাত্রা এবং প্রয়োগবিধি লিখুন:
                </p>
                <textarea
                  rows={4}
                  value={treatment}
                  onChange={(e) => setTreatment(e.target.value)}
                  placeholder="যেমন: প্রতি লিটার পানিতে ০.৭৫ গ্রাম ট্রাইসাইক্লাজল ৭৫ ডব্লিউপি মিশিয়ে শেষ বিকেলে স্প্রে করুন। অতিরিক্ত ইউরিয়া সার বন্ধ রেখে কাঠকয়লার ছাই বা পটাশ সার প্রয়োগ করুন।"
                  className="w-full p-3 rounded-btn border border-line-200 bg-canvas text-sm focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                  required
                />
              </div>

              {/* Expert Notes */}
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  অভ্যন্তরীণ নোট বা ফলোআপ নির্দেশনা (ঐচ্ছিক)
                </label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="যেমন: ৭ দিন পর পুনরায় ফিল্ড ভিজিট বা ছবি যাচাই প্রয়োজন..."
                  className="w-full px-3.5 min-h-[44px] rounded-btn border border-line-200 bg-canvas text-sm focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                />
              </div>

              {/* Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-line-200">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={handleCloseReview}
                  disabled={isSubmitting}
                >
                  বাতিল
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSubmitting}
                >
                  <CheckCircle2 className="w-4 h-4 mr-1.5" />
                  <span>অফিসিয়াল প্রেসক্রিপশন জমা দিন</span>
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};
