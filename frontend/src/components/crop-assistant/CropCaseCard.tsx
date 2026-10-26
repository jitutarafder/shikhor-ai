import React, { useState } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ThumbsUp,
  AlertOctagon,
  MessageSquare,
  Send,
  X,
  Clock,
  Camera,
} from 'lucide-react';
import { CropCase, FeedbackType } from '../../features/crop-assistant/types';
import { submitCropFeedbackApi, sendCaseToExpertApi } from '../../features/crop-assistant/api';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { CropLeafImage } from './CropLeafImage';

interface CropCaseCardProps {
  cropCase: CropCase;
  token: string;
}

export const CropCaseCard: React.FC<CropCaseCardProps> = ({ cropCase: initialCase, token }) => {
  const [cropCase, setCropCase] = useState<CropCase>(initialCase);
  const [feedbackSent, setFeedbackSent] = useState<FeedbackType | null>(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);

  // Send Photo to Expert State
  const [showSendModal, setShowSendModal] = useState(false);
  const [additionalPhoto, setAdditionalPhoto] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [farmerNotes, setFarmerNotes] = useState('');
  const [isSendingToExpert, setIsSendingToExpert] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [sendSuccessMsg, setSendSuccessMsg] = useState<string | null>(null);

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAdditionalPhoto(file);
      const url = URL.createObjectURL(file);
      setPhotoPreview(url);
    }
  };

  const handleClearAdditionalPhoto = () => {
    setAdditionalPhoto(null);
    if (photoPreview) {
      URL.revokeObjectURL(photoPreview);
      setPhotoPreview(null);
    }
  };

  const handleSendToExpert = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSendingToExpert(true);
    setSendError(null);
    try {
      const updated = await sendCaseToExpertApi(token, cropCase.id, farmerNotes, additionalPhoto || undefined);
      setCropCase(updated);
      setSendSuccessMsg('আপনার রোগাক্রান্ত পাতার ছবি ও প্রশ্ন সফলভাবে কৃষি কর্মকর্তার তালিকায় পাঠানো হয়েছে!');
      setShowSendModal(false);
      setAdditionalPhoto(null);
      setPhotoPreview(null);
      setFarmerNotes('');
      setTimeout(() => setSendSuccessMsg(null), 5000);
    } catch (err: any) {
      setSendError(err.message || 'বিশেষজ্ঞের কাছে পাঠাতে ব্যর্থ হয়েছে।');
    } finally {
      setIsSendingToExpert(false);
    }
  };

  const handleFeedback = async (type: FeedbackType) => {
    if (feedbackSent || isSubmittingFeedback) return;
    setIsSubmittingFeedback(true);
    try {
      await submitCropFeedbackApi(token, cropCase.id, type);
      setFeedbackSent(type);
    } catch {
      // Ignore in UI
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const statusBadge = () => {
    switch (cropCase.status) {
      case 'possible_match':
        if (cropCase.isReviewedByExpert || cropCase.confidenceBand === 'expert_verified') {
          return (
            <Badge variant="success">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>কৃষি কর্মকর্তা দ্বারা পরীক্ষিত (১০০%)</span>
            </Badge>
          );
        }
        return (
          <Badge variant={cropCase.confidenceBand === 'high' ? 'success' : 'warning'}>
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>
              {Math.round(cropCase.confidence * 100)}% সামঞ্জস্যপূর্ণ ({cropCase.confidenceBand === 'high' ? 'উচ্চ' : 'মাঝারি'})
            </span>
          </Badge>
        );
      case 'uncertain':
        return (
          <Badge variant="warning">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>অনিশ্চিত ফলাফল ({Math.round(cropCase.confidence * 100)}%)</span>
          </Badge>
        );
      case 'unsupported':
        return (
          <Badge variant="offline">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>অসমর্থিত ফসল বা লক্ষণ</span>
          </Badge>
        );
      default:
        return (
          <Badge variant="neutral">
            <span>বিশ্লেষণ সম্পন্ন</span>
          </Badge>
        );
    }
  };

  return (
    <Card className="p-6 border-line-200 shadow-soft space-y-5 bg-canvas">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-line-200">
        <div>
          <span className="text-xs font-semibold text-forest-700 uppercase tracking-wider block mb-1">
            ফসল: {cropCase.cropType}
          </span>
          <h3 className="text-xl sm:text-2xl font-bold text-forest-900 leading-tight">
            {cropCase.possibleCondition || 'অনিশ্চিত বা অনির্ধারিত লক্ষণ'}
          </h3>
        </div>
        <div>{statusBadge()}</div>
      </div>

      {/* Image & Symptoms / Reasoning */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-start">
        <div className="md:col-span-4">
          <CropLeafImage
            caseId={cropCase.id}
            imageFilename={cropCase.imageFilename}
            cropType={cropCase.cropType}
            token={token}
            className="w-full h-44 object-cover rounded-btn"
          />
        </div>

        <div className="md:col-span-8 space-y-3">
          {/* Observed symptoms note if provided */}
          {cropCase.symptomsDescription && (
            <div className="text-xs text-ink-600 bg-surface p-3 rounded-btn border border-line-200">
              <span className="font-semibold text-forest-900">বর্ণিত লক্ষণ: </span>
              {cropCase.symptomsDescription}
            </div>
          )}

          {/* Reasoning Summary */}
          {cropCase.reasonSummary.length > 0 && (
            <div className="space-y-1.5">
              <h4 className="text-xs font-bold text-forest-900">পর্যবেক্ষণ ও কারণ:</h4>
              <ul className="space-y-1 text-xs text-ink-600">
                {cropCase.reasonSummary.map((reason, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <span className="text-leaf-500 font-bold">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Primary Solution */}
      {cropCase.primarySolution && (
        <div className="p-3.5 bg-forest-700/10 border border-forest-700/20 rounded-card space-y-1">
          <h4 className="text-xs font-bold text-forest-900 uppercase tracking-wider">
            প্রাথমিক সমাধান (Primary Solution):
          </h4>
          <p className="text-xs sm:text-sm font-semibold text-forest-900 leading-relaxed">
            {cropCase.primarySolution}
          </p>
        </div>
      )}

      {/* Actionable Reviewed Guidance */}
      {cropCase.guidance.length > 0 && (
        <div className="space-y-2.5 bg-leaf-100/50 p-4 rounded-card border border-leaf-500/20">
          <h4 className="text-sm font-bold text-forest-900 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-forest-700" />
            <span>{cropCase.isHealthy || cropCase.possibleCondition === 'Healthy' ? 'গাছের সুস্বাস্থ্য বজায় রাখতে করণীয়:' : 'অনুমোদিত করণীয়:'}</span>
          </h4>
          <ul className="space-y-2 text-xs sm:text-sm text-ink-900 font-medium">
            {cropCase.guidance.map((guide, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-forest-700 font-bold">{idx + 1}.</span>
                <span>{guide}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Avoid / এড়িয়ে চলুন */}
      {cropCase.avoid && (
        <div className="p-3.5 bg-danger-600/10 border border-danger-600/25 rounded-card space-y-1 text-danger-600">
          <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4" />
            <span>এড়িয়ে চলুন:</span>
          </h4>
          <p className="text-xs sm:text-sm font-medium leading-relaxed">
            {cropCase.avoid}
          </p>
        </div>
      )}

      {/* Prevention / প্রতিরোধ */}
      {cropCase.prevention && (
        <div className="p-3.5 bg-leaf-100/60 border border-leaf-500/30 rounded-card space-y-1 text-forest-900">
          <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-forest-700" />
            <span>প্রতিরোধ ব্যবস্থা:</span>
          </h4>
          <p className="text-xs sm:text-sm font-medium leading-relaxed">
            {cropCase.prevention}
          </p>
        </div>
      )}

      {/* Special Warning / বিশেষ সতর্কতা */}
      {cropCase.specialWarning && (
        <div className="p-3.5 bg-paddy-400/20 border border-paddy-400/40 rounded-card space-y-1 text-soil-700">
          <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-soil-700" />
            <span>বিশেষ সতর্কতা:</span>
          </h4>
          <p className="text-xs sm:text-sm font-semibold leading-relaxed">
            {cropCase.specialWarning}
          </p>
        </div>
      )}

      {/* Expert Verified Banner */}
      {cropCase.isReviewedByExpert && (
        <div className="bg-leaf-100/90 border border-leaf-500/40 p-4 rounded-card flex items-start gap-3 text-forest-900">
          <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5 text-forest-700" />
          <div className="space-y-1 text-xs sm:text-sm">
            <p className="font-bold text-forest-900">
              সার্টিফাইড কৃষি বিশেষজ্ঞ দ্বারা যাচাইকৃত ও প্রেসক্রাইবড:
            </p>
            <p className="leading-relaxed text-ink-900">
              এই রোগ কেসটি একজন অনুমোদিত কৃষি কর্মকর্তা পর্যালোচনা করেছেন এবং নির্ভরযোগ্য সমাধান ও বালাই ব্যবস্থাপনা নিশ্চিত করেছেন।
            </p>
          </div>
        </div>
      )}

      {/* Escalation Recommendation Notice */}
      {cropCase.escalationRecommended && (
        <div className="bg-paddy-400/20 border border-paddy-400/40 p-4 rounded-card flex items-start gap-3 text-soil-700">
          <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5 text-soil-700" />
          <div className="space-y-1 text-xs sm:text-sm">
            <p className="font-bold">বিশেষজ্ঞ পরামর্শ আবশ্যক (Escalation Recommended):</p>
            <p className="leading-relaxed">
              লক্ষণটি শতভাগ নিশ্চিত নয় অথবা জটিল সংক্রমণের ঝুঁকি রয়েছে। ক্ষতির বিস্তার ঠেকাতে নিকটস্থ উপজেলা কৃষি কর্মকর্তা বা উপ-সহকারী কৃষি কর্মকর্তার (SAAO) প্রত্যক্ষ পরামর্শ নিন।
            </p>
          </div>
        </div>
      )}

      {/* Send Photo to Expert Action Section */}
      {!cropCase.isReviewedByExpert && (
        <div className="bg-field-wash border border-forest-700/20 p-4 rounded-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-forest-900 flex items-center gap-1.5">
                <Send className="w-4 h-4 text-forest-700" />
                <span>কৃষি কর্মকর্তার সরাসরি পরামর্শ ও প্রেসক্রিপশন চান?</span>
              </span>
              {cropCase.escalationRecommended && (
                <span className="px-2 py-0.5 rounded-full bg-paddy-400/20 text-soil-700 text-[11px] font-semibold flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  <span>বিশেষজ্ঞ তালিকায় অপেক্ষমাণ</span>
                </span>
              )}
            </div>
            <p className="text-xs text-ink-600">
              আক্রান্ত পাতার স্পষ্ট ছবি পাঠিয়ে সরকারি সার্টিফাইড কৃষি কর্মকর্তার নির্ভরযোগ্য প্রেসক্রিপশন নিন।
            </p>
          </div>

          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={() => setShowSendModal(true)}
            className="text-xs shrink-0 bg-forest-700 hover:bg-forest-800"
          >
            <Camera className="w-3.5 h-3.5 mr-1.5 text-paddy-400" />
            <span>{cropCase.escalationRecommended ? 'আরেকটি ছবি / প্রশ্ন পাঠান' : 'বিশেষজ্ঞের কাছে ছবি পাঠান'}</span>
          </Button>
        </div>
      )}

      {sendSuccessMsg && (
        <div className="p-3 bg-leaf-100 border border-leaf-500/30 text-forest-900 rounded-btn text-xs font-medium flex items-center gap-2 animate-in fade-in">
          <CheckCircle2 className="w-4 h-4 text-forest-700 shrink-0" />
          <span>{sendSuccessMsg}</span>
        </div>
      )}

      {/* Mandatory Disclaimer & Model metadata */}
      <div className="text-[11px] text-ink-600 pt-2 border-t border-line-200 space-y-1">
        <p className="italic">{cropCase.disclaimer}</p>
        <p className="text-[10px] text-ink-600/80">মডেল সংস্করণ: {cropCase.modelVersion}</p>
      </div>

      {/* Farmer Feedback Section */}
      <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <span className="text-ink-600 font-medium flex items-center gap-1">
          <MessageSquare className="w-3.5 h-3.5" />
          এই ফলাফলটি কি আপনার জন্য সহায়ক হয়েছে?
        </span>

        {feedbackSent ? (
          <span className="text-forest-700 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            মতামত প্রদানের জন্য ধন্যবাদ!
          </span>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleFeedback('helpful')}
              disabled={isSubmittingFeedback}
              className="px-2.5 py-1.5 rounded-btn bg-leaf-100 hover:bg-leaf-500/20 text-forest-900 font-medium flex items-center gap-1 border border-leaf-500/20"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
              <span>উপকারী</span>
            </button>

            <button
              onClick={() => handleFeedback('incorrect')}
              disabled={isSubmittingFeedback}
              className="px-2.5 py-1.5 rounded-btn bg-surface hover:bg-line-200 text-ink-600 font-medium flex items-center gap-1 border border-line-200"
            >
              <AlertTriangle className="w-3.5 h-3.5 text-paddy-400" />
              <span>ভুল মনে হচ্ছে</span>
            </button>

            <button
              onClick={() => handleFeedback('unsafe')}
              disabled={isSubmittingFeedback}
              className="px-2.5 py-1.5 rounded-btn bg-danger-600/10 hover:bg-danger-600/20 text-danger-600 font-medium flex items-center gap-1 border border-danger-600/20"
            >
              <AlertOctagon className="w-3.5 h-3.5" />
              <span>অনিরাপদ</span>
            </button>
          </div>
        )}
      </div>

      {/* Send Photo to Expert Modal Dialog */}
      {showSendModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/60 backdrop-blur-xs animate-in fade-in">
          <Card className="max-w-lg w-full p-6 bg-canvas border-line-200 shadow-xl max-h-[90vh] overflow-y-auto space-y-4">
            <div className="flex items-center justify-between border-b border-line-200 pb-3">
              <div className="flex items-center gap-2">
                <Send className="w-5 h-5 text-forest-700" />
                <h3 className="text-base font-bold text-forest-900">
                  কৃষি কর্মকর্তার কাছে ছবি ও প্রশ্ন পাঠান
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowSendModal(false)}
                className="text-ink-600 hover:text-ink-900 p-1 rounded-btn hover:bg-surface"
                aria-label="বন্ধ করুন"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {sendError && (
              <div className="p-3 bg-danger-600/10 border border-danger-600/20 text-danger-600 rounded-btn text-xs">
                {sendError}
              </div>
            )}

            <form onSubmit={handleSendToExpert} className="space-y-4 text-xs">
              {/* Photo Upload Area */}
              <div>
                <label className="block text-xs font-semibold text-ink-900 mb-1.5">
                  আক্রান্ত পাতার ছবি (ক্যামেরা দিয়ে নতুন ছবি তুলুন বা গ্যালারি থেকে দিন):
                </label>

                {photoPreview ? (
                  <div className="relative rounded-btn overflow-hidden border border-line-200 bg-surface">
                    <img src={photoPreview} alt="নতুন ছবি প্রিভিউ" className="w-full h-44 object-cover" />
                    <button
                      type="button"
                      onClick={handleClearAdditionalPhoto}
                      className="absolute top-2 right-2 p-1.5 bg-ink-900/80 hover:bg-ink-900 text-canvas rounded-full transition-colors"
                      title="ছবি বাদ দিন"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <label className="flex flex-col items-center justify-center p-5 border-2 border-dashed border-line-200 hover:border-forest-700/60 rounded-btn cursor-pointer bg-surface/50 hover:bg-surface text-center transition-colors">
                    <div className="w-10 h-10 rounded-full bg-leaf-100 text-forest-700 flex items-center justify-center mb-1.5">
                      <Camera className="w-5 h-5" />
                    </div>
                    <span className="font-semibold text-forest-900">
                      নতুন বা স্পষ্ট আরেকটি ছবি যুক্ত করুন (ঐচ্ছিক)
                    </span>
                    <span className="text-[11px] text-ink-600 mt-0.5">
                      না দিলে বর্তমান ছবি দিয়েই বিশেষজ্ঞের কাছে পাঠানো হবে
                    </span>
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handlePhotoChange}
                      className="hidden"
                    />
                  </label>
                )}
              </div>

              {/* Farmer's message / questions */}
              <div>
                <label htmlFor="expertNotesInput" className="block text-xs font-semibold text-ink-900 mb-1">
                  বিশেষজ্ঞ কর্মকর্তার জন্য আপনার প্রশ্ন বা সমস্যা বিবরণ:
                </label>
                <textarea
                  id="expertNotesInput"
                  rows={3}
                  value={farmerNotes}
                  onChange={(e) => setFarmerNotes(e.target.value)}
                  placeholder="যেমন: কতদিন ধরে পাতার এই দাগ দেখা যাচ্ছে, কোনো সার বা কীটনাশক দিয়েছেন কি না, জমিতে পানি কেমন আছে..."
                  className="w-full p-2.5 rounded-btn border border-line-200 text-xs focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-line-200">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSendModal(false)}
                  disabled={isSendingToExpert}
                >
                  বাতিল
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSendingToExpert}
                >
                  <Send className="w-3.5 h-3.5 mr-1" />
                  <span>বিশেষজ্ঞের কাছে পাঠান</span>
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </Card>
  );
};
