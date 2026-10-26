import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ScanLine,
  UploadCloud,
  Camera,
  History,
  AlertCircle,
  HelpCircle,
  ArrowLeft,
  X,
  Sparkles,
  CheckCircle2,
  Cpu,
  BarChart2,
  ShieldAlert,
  Send,
  MessageSquare,
  ThumbsUp,
  AlertTriangle,
  AlertOctagon,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { CropCase, CropDiseasePredictionResult, FeedbackType } from '../features/crop-assistant/types';
import {
  getMyCropCasesApi,
  submitCropCaseApi,
  predictCropDiseaseApi,
  sendCaseToExpertApi,
  submitCropFeedbackApi,
} from '../features/crop-assistant/api';
import { CropCaseCard } from '../components/crop-assistant/CropCaseCard';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const CropAssistant: React.FC = () => {
  const { token, isAuthenticated } = useAuth();

  const [activeTab, setActiveTab] = useState<'scan' | 'history'>('scan');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [cropType, setCropType] = useState('ধান');
  const [symptoms, setSymptoms] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Vision Prediction & Crop Case Result
  const [visionResult, setVisionResult] = useState<CropDiseasePredictionResult | null>(null);
  const [currentResult, setCurrentResult] = useState<CropCase | null>(null);
  const [historyCases, setHistoryCases] = useState<CropCase[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Direct Send-to-Expert Modal State
  const [showDirectExpertModal, setShowDirectExpertModal] = useState(false);
  const [directFarmerNotes, setDirectFarmerNotes] = useState('');
  const [directAdditionalPhoto, setDirectAdditionalPhoto] = useState<File | null>(null);
  const [directPhotoPreview, setDirectPhotoPreview] = useState<string | null>(null);
  const [isSendingDirectExpert, setIsSendingDirectExpert] = useState(false);
  const [directExpertSuccess, setDirectExpertSuccess] = useState<string | null>(null);
  const [directExpertError, setDirectExpertError] = useState<string | null>(null);

  // Direct Farmer Feedback State
  const [directFeedbackSent, setDirectFeedbackSent] = useState<FeedbackType | null>(null);
  const [isSubmittingDirectFeedback, setIsSubmittingDirectFeedback] = useState(false);

  useEffect(() => {
    if (token && activeTab === 'history') {
      loadHistory();
    }
  }, [token, activeTab]);

  const loadHistory = async () => {
    if (!token) return;
    setIsLoadingHistory(true);
    try {
      const cases = await getMyCropCasesApi(token);
      setHistoryCases(cases);
    } catch (err: any) {
      setErrorMsg(err.message || 'পূর্ববর্তী তথ্য লোড করা যায়নি।');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setVisionResult(null);
      setCurrentResult(null);
      setErrorMsg(null);
    }
  };

  const handleClearImage = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setVisionResult(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    if (!cropType || !cropType.trim()) {
      setErrorMsg('অনুগ্রহ করে আগে ফসল নির্বাচন করুন।');
      return;
    }

    if (!selectedFile) {
      setErrorMsg('অনুগ্রহ করে ফসলের আক্রান্ত পাতার ছবি আপলোড করুন।');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      // 1. Run Crop-Aware Multimodal Disease Classification
      const visionData = await predictCropDiseaseApi(selectedFile, cropType, symptoms);
      setVisionResult(visionData);

      // 2. Automatically record in crop case history for the farmer if valid plant
      if (visionData.is_plant_leaf !== false && visionData.success !== false) {
        const effectiveCrop = visionData.crop_bn || cropType;
        const effectiveSymptoms = symptoms || `মডেল শনাক্তকরণ: ${visionData.disease_bn}`;
        try {
          const result = await submitCropCaseApi(token, selectedFile, effectiveCrop, effectiveSymptoms);
          setCurrentResult(result);
        } catch (historyErr) {
          console.warn('Background history sync notice:', historyErr);
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'ফসল সমস্যা বিশ্লেষণ সম্পন্ন করা যায়নি।');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDirectPhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setDirectAdditionalPhoto(file);
      const url = URL.createObjectURL(file);
      setDirectPhotoPreview(url);
    }
  };

  const handleClearDirectPhoto = () => {
    setDirectAdditionalPhoto(null);
    if (directPhotoPreview) {
      URL.revokeObjectURL(directPhotoPreview);
      setDirectPhotoPreview(null);
    }
  };

  const handleDirectSendToExpert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setIsSendingDirectExpert(true);
    setDirectExpertError(null);
    try {
      let targetCaseId = currentResult?.id;

      if (!targetCaseId && selectedFile) {
        const effectiveCrop = visionResult?.crop_bn || cropType;
        const effectiveSymptoms = directFarmerNotes || symptoms || `মডেল ফলাফল: ${visionResult?.disease_bn || 'ফসল রোগ যাচাই'}`;
        const newCase = await submitCropCaseApi(token, selectedFile, effectiveCrop, effectiveSymptoms);
        setCurrentResult(newCase);
        targetCaseId = newCase.id;
      }

      if (targetCaseId) {
        const updated = await sendCaseToExpertApi(token, targetCaseId, directFarmerNotes, directAdditionalPhoto || undefined);
        setCurrentResult(updated);
        setDirectExpertSuccess('আপনার রোগাক্রান্ত পাতার ছবি ও প্রশ্ন সরাসরি সরকারি কৃষি কর্মকর্তার তালিকায় পাঠানো হয়েছে! কর্মকর্তা শীঘ্রই প্রেসক্রিপশন প্রদান করবেন।');
        setShowDirectExpertModal(false);
        setDirectAdditionalPhoto(null);
        setDirectPhotoPreview(null);
        setDirectFarmerNotes('');
        setTimeout(() => setDirectExpertSuccess(null), 6000);
      } else {
        throw new Error('কেস আইডি পাওয়া যায়নি। অনুগ্রহ করে পুনরায় চেষ্টা করুন।');
      }
    } catch (err: any) {
      setDirectExpertError(err.message || 'বিশেষজ্ঞের কাছে পাঠাতে ব্যর্থ হয়েছে।');
    } finally {
      setIsSendingDirectExpert(false);
    }
  };

  const handleDirectFeedback = async (type: FeedbackType) => {
    if (directFeedbackSent || isSubmittingDirectFeedback || !token) return;
    setIsSubmittingDirectFeedback(true);
    try {
      if (currentResult?.id) {
        await submitCropFeedbackApi(token, currentResult.id, type);
      }
      setDirectFeedbackSent(type);
    } catch {
      setDirectFeedbackSent(type);
    } finally {
      setIsSubmittingDirectFeedback(false);
    }
  };

  if (!isAuthenticated || !token) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <Card className="max-w-md w-full p-8 text-center space-y-4">
          <ScanLine className="w-12 h-12 text-forest-700 mx-auto" />
          <h1 className="text-xl font-bold text-forest-900">লগ ইন আবশ্যক</h1>
          <p className="text-sm text-ink-600">ফসল সমস্যা সহচর ব্যবহার করতে আপনার অ্যাকাউন্টে লগ ইন করুন।</p>
          <Link to="/login">
            <Button variant="primary" fullWidth size="md">
              লগ ইন পৃষ্ঠায় যান
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-line-200 pb-5">
        <div>
          <Link to="/app" className="inline-flex items-center gap-1.5 text-xs font-semibold text-forest-700 hover:underline mb-2">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>ড্যাশবোর্ডে ফিরে যান</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-bold text-forest-900 flex items-center gap-2.5">
            <ScanLine className="w-7 h-7 text-leaf-500" />
            <span>এআই ফসল সমস্যা সহচর</span>
          </h1>
          <p className="text-sm text-ink-600 mt-1">
            আক্রান্ত পাতার ছবি তুলে বা লক্ষণ লিখে তাত্ক্ষণিক নির্ভরযোগ্য কৃষি পরামর্শ নিন
          </p>
        </div>

        {/* Tab switch */}
        <div className="flex items-center gap-2 bg-surface p-1 rounded-btn border border-line-200 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab('scan')}
            className={`px-3.5 py-1.5 rounded-btn text-xs font-semibold transition-colors flex items-center gap-1.5 ${activeTab === 'scan' ? 'bg-forest-700 text-canvas shadow-xs' : 'text-ink-600 hover:text-forest-900'
              }`}
          >
            <Camera className="w-4 h-4" />
            <span>নতুন রোগ যাচাই</span>
          </button>

          <button
            onClick={() => setActiveTab('history')}
            className={`px-3.5 py-1.5 rounded-btn text-xs font-semibold transition-colors flex items-center gap-1.5 ${activeTab === 'history' ? 'bg-forest-700 text-canvas shadow-xs' : 'text-ink-600 hover:text-forest-900'
              }`}
          >
            <History className="w-4 h-4" />
            <span>পূর্ববর্তী হিস্ট্রি</span>
          </button>
        </div>
      </div>

      {/* ERROR NOTICE */}
      {errorMsg && (
        <div className="p-4 bg-danger-600/10 border border-danger-600/20 text-danger-600 rounded-btn text-sm flex items-center gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* TAB 1: SCAN & ANALYZE */}
      {activeTab === 'scan' && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Left 7 cols: Upload form */}
            <form onSubmit={handleSubmit} className="lg:col-span-7 space-y-5">
              <Card className="p-6 border-line-200 space-y-5">
                {/* Crop selector */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label htmlFor="cropSelect" className="block text-sm font-semibold text-ink-900">
                      ফসল নির্বাচন করুন <span className="text-danger-600">*</span>
                    </label>
                    <span className="text-[11px] font-medium text-forest-700 bg-leaf-100/60 px-2 py-0.5 rounded-full">
                      ১৬টি ফসল সমর্থিত
                    </span>
                  </div>

                  <select
                    id="cropSelect"
                    value={cropType}
                    onChange={(e) => setCropType(e.target.value)}
                    className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 bg-canvas text-base font-medium focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                    required
                  >
                    <option value="">-- ফসল নির্বাচন করুন --</option>
                    <optgroup label="দানা শস্য (Cereals)">
                      <option value="ধান">ধান (Rice)</option>
                      <option value="গম">গম (Wheat)</option>
                      <option value="ভুট্টা">ভুট্টা (Corn)</option>
                    </optgroup>
                    <optgroup label="শাকসবজি ও কন্দাল ফসল (Vegetables & Tubers)">
                      <option value="আলু">আলু (Potato)</option>
                      <option value="টমেটো">টমেটো (Tomato)</option>
                      <option value="ক্যাপসিকাম">ক্যাপসিকাম (Bell Pepper)</option>
                      <option value="স্কোয়াশ">স্কোয়াশ (Squash)</option>
                    </optgroup>
                    <optgroup label="ফলমূল ও বেরি (Fruits & Berries)">
                      <option value="আপেল">আপেল (Apple)</option>
                      <option value="ব্লুবেরি">ব্লুবেরি (Blueberry)</option>
                      <option value="চেরি">চেরি (Cherry)</option>
                      <option value="আঙুর">আঙুর (Grape)</option>
                      <option value="কমলা">কমলা (Orange)</option>
                      <option value="পিচ">পিচ (Peach)</option>
                      <option value="রাস্পবেরি">রাস্পবেরি (Raspberry)</option>
                      <option value="স্ট্রবেরি">স্ট্রবেরি (Strawberry)</option>
                    </optgroup>
                    <optgroup label="তৈলবীজ ও ডালজাতীয় (Oilseeds & Legumes)">
                      <option value="সয়াবিন">সয়াবিন (Soybean)</option>
                    </optgroup>
                  </select>
                </div>

                {/* Image Upload Area */}
                <div>
                  <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                    ছবি আপলোড করুন <span className="text-danger-600">*</span>
                  </label>

                  {previewUrl ? (
                    <div className="relative rounded-card overflow-hidden border border-line-200 bg-surface">
                      <img src={previewUrl} alt="Crop Leaf Preview" className="w-full max-h-72 object-contain mx-auto" />
                      <button
                        type="button"
                        onClick={handleClearImage}
                        className="absolute top-3 right-3 p-1.5 bg-ink-900/80 hover:bg-ink-900 text-canvas rounded-full transition-colors"
                        title="ছবি পরিবর্তন করুন"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <label className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-line-200 hover:border-forest-700/60 rounded-card cursor-pointer bg-surface/50 hover:bg-surface transition-colors text-center">
                      <div className="w-14 h-14 rounded-full bg-leaf-100 text-forest-700 flex items-center justify-center mb-3">
                        <UploadCloud className="w-7 h-7" />
                      </div>
                      <span className="text-sm font-bold text-forest-900">
                        ক্যামেরা দিয়ে ছবি তুলুন বা ছবি নির্বাচন করুন
                      </span>
                      <span className="text-xs text-ink-600 mt-1">
                        JPEG, PNG, বা WebP (সর্বোচ্চ ১০ মেগাবাইট)
                      </span>
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                    </label>
                  )}
                </div>

                {/* Symptom Description (Optional) */}
                <div>
                  <label htmlFor="symptomsText" className="block text-sm font-semibold text-ink-900 mb-1.5">
                    লক্ষণ বা সমস্যার বিবরণ (ঐচ্ছিক - বাংলা বা বাংলিশে)
                  </label>
                  <textarea
                    id="symptomsText"
                    rows={3}
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    placeholder="যেমন: patay choto choto badami dag poreche, aga shukiye jacche…"
                    className="w-full p-3.5 rounded-btn border border-line-200 text-base focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                  />
                </div>

                <Button type="submit" variant="primary" size="lg" fullWidth isLoading={isSubmitting}>
                  <Sparkles className="w-4 h-4 mr-1.5 text-paddy-400" />
                  <span>রোগ শনাক্ত করুন</span>
                </Button>
              </Card>
            </form>

            {/* Right 5 cols: Photo guidelines */}
            <div className="lg:col-span-5 space-y-4">
              <Card className="p-6 bg-leaf-100/40 border-leaf-500/20 space-y-3">
                <h3 className="font-bold text-forest-900 text-sm flex items-center gap-1.5">
                  <HelpCircle className="w-4 h-4 text-forest-700" />
                  <span>সঠিক ছবির জন্য পরামর্শ:</span>
                </h3>
                <ul className="space-y-2 text-xs text-ink-600 leading-relaxed">
                  <li className="flex items-start gap-2">
                    <span className="text-forest-700 font-bold">১.</span>
                    <span>দিনের পরিষ্কার প্রাকৃতিক আলোতে ছবি তুলুন। অতিরিক্ত অন্ধকার বা ছায়া এড়িয়ে চলুন।</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-forest-700 font-bold">২.</span>
                    <span>পাতার যে অংশে রোগ বা দাগ রয়েছে, ক্যামেরা ঠিক সেই অংশের ওপর ফোকাস রাখুন।</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-forest-700 font-bold">৩.</span>
                    <span>অতিরিক্ত দূর থেকে তোলা পুরো জমির ছবি রোগ শনাক্তকরণে উপযুক্ত নয়।</span>
                  </li>
                </ul>
              </Card>

              <Card className="p-6 bg-surface border-line-200 space-y-2">
                <h4 className="font-bold text-forest-900 text-xs uppercase tracking-wider">
                  নিরাপত্তা ও গোপনীয়তা
                </h4>
                <p className="text-xs text-ink-600 leading-relaxed">
                  আপনার আপলোডকৃত ছবির জিপিএস ও ব্যক্তিগত মেটাডাটা স্বয়ংক্রিয়ভাবে মুছে ফেলা হয় এবং শুধুমাত্র রোগ নির্ণয়ের কাজেই ব্যবহৃত হয়।
                </p>
              </Card>
            </div>
          </div>

          {/* AI ANALYSIS RESULT DISPLAY (ONE FINAL DIAGNOSIS) */}
          {visionResult && (
            <div className="space-y-6 pt-4 border-t border-line-200 animate-in fade-in duration-300">
              {visionResult.is_plant_leaf === false ||
              visionResult.success === false ||
              visionResult.disease === 'গাছ বা পাতার ছবি নয়' ||
              visionResult.disease_bn === 'গাছ বা পাতার ছবি নয়' ||
              (visionResult.confidence === 0 && !visionResult.is_healthy) ? (
                <div className="bg-danger-600/10 border border-danger-600/30 p-5 rounded-card space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-danger-600 text-canvas flex items-center justify-center shrink-0">
                      <AlertCircle className="w-6 h-6" />
                    </div>
                    <div>
                      <h2 className="text-base sm:text-lg font-bold text-danger-600">
                        গাছ বা পাতার ছবি নয়
                      </h2>
                      <p className="text-xs text-ink-600 mt-0.5">
                        {visionResult.reason_summary && visionResult.reason_summary.length > 0
                          ? visionResult.reason_summary[0]
                          : 'আপলোডকৃত ছবিতে কোনো ফসল বা পাতার প্রাকৃতিক বৈশিষ্ট্য পাওয়া যায়নি (যেমন: প্রাণী, ফুল, ভূদৃশ্য বা অপ্রাসঙ্গিক ছবি)।'}
                      </p>
                    </div>
                  </div>

                  <div className="bg-canvas p-4 rounded-btn border border-line-200 text-xs text-ink-700 space-y-1.5">
                    <p className="font-bold text-forest-900">করণীয়:</p>
                    <ul className="list-disc list-inside space-y-1 text-ink-600">
                      <li>আক্রান্ত ফসলের পাতা বা ডালপালার কাছ থেকে পরিষ্কার ছবি তুলুন।</li>
                      <li>পর্যাপ্ত প্রাকৃতিক আলোতে পাতার দাগ স্পষ্ট রাখুন।</li>
                    </ul>
                  </div>
                </div>
              ) : visionResult.is_healthy || visionResult.disease === 'Healthy' ? (
                /* HEALTHY CLASS CLEAN DISPLAY */
                <div className="space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-leaf-100/60 p-5 rounded-card border border-leaf-500/30">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-full bg-forest-700 text-canvas flex items-center justify-center shrink-0 shadow-xs">
                        <CheckCircle2 className="w-6 h-6 text-paddy-400" />
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-forest-900 flex items-center gap-2">
                          <span>🌱 রোগ শনাক্ত হয়নি</span>
                        </h2>
                        <p className="text-xs text-ink-600 mt-0.5">
                          নির্বাচিত ফসল: <span className="font-semibold text-forest-800">{visionResult.crop_bn}</span> | সার্বিক অবস্থা: <span className="font-semibold text-forest-700">সুস্থ ও নিরোগ গাছ</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      <span className="text-xs bg-forest-700 text-canvas font-semibold px-3 py-1 rounded-full">
                        {visionResult.crop_bn} — সুস্থ
                      </span>
                    </div>
                  </div>

                  {/* Healthy plant maintenance guidance */}
                  <Card className="p-5 border-leaf-500/20 bg-canvas space-y-3">
                    <h3 className="text-sm font-bold text-forest-900 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-forest-700" />
                      <span>গাছের সুস্বাস্থ্য বজায় রাখতে করণীয়:</span>
                    </h3>
                    <ul className="space-y-2 text-xs sm:text-sm text-ink-800 font-medium">
                      {(visionResult.guidance && visionResult.guidance.length > 0 ? visionResult.guidance : [
                        'নিয়মিত গাছ পর্যবেক্ষণ করুন',
                        'সঠিক পানি ও সার ব্যবস্থাপনা করুন',
                        'আক্রান্ত/অস্বাভাবিক পাতা দেখলে পুনরায় পরীক্ষা করুন',
                        'পরিষ্কার কৃষি সরঞ্জাম ব্যবহার করুন',
                        'রোগ প্রতিরোধী জাত ব্যবহার করুন',
                      ]).map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2.5">
                          <span className="text-forest-700 font-bold">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                </div>
              ) : (
                /* DISEASE DETECTED DISPLAY */
                <div className="space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-forest-700/5 p-5 rounded-card border border-forest-700/20">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-full bg-forest-700 text-canvas flex items-center justify-center shrink-0 shadow-xs">
                        <Cpu className="w-6 h-6 text-paddy-400" />
                      </div>
                      <div>
                        <h2 className="text-lg sm:text-xl font-bold text-forest-900 flex items-center gap-2">
                          <span>শনাক্ত করা রোগ: {visionResult.disease_bn}</span>
                          {visionResult.uncertain && (
                            <Badge variant="warning">
                              নিশ্চয়তা কম
                            </Badge>
                          )}
                        </h2>
                        <p className="text-xs text-ink-600 mt-0.5">
                          নির্বাচিত ফসল: <span className="font-semibold text-forest-800">{visionResult.crop_bn}</span> | কনফিডেন্স স্কোর: <span className="font-bold text-forest-700">{(visionResult.confidence * 100).toFixed(1)}%</span>
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      <span className="text-xs bg-leaf-100 text-forest-900 font-semibold px-3 py-1 rounded-full border border-leaf-500/30">
                        {visionResult.crop_bn}
                      </span>
                    </div>
                  </div>

                  {/* Primary Solution */}
                  {visionResult.primary_solution && (
                    <div className="p-4 bg-forest-700/10 border border-forest-700/25 rounded-card space-y-1">
                      <h4 className="text-xs font-bold text-forest-900 uppercase tracking-wider">
                        প্রাথমিক সমাধান (Primary Solution):
                      </h4>
                      <p className="text-sm font-semibold text-forest-900 leading-relaxed">
                        {visionResult.primary_solution}
                      </p>
                    </div>
                  )}

                  {/* Action Items / করণীয় */}
                  {visionResult.guidance && visionResult.guidance.length > 0 && (
                    <Card className="p-5 border-line-200 space-y-3">
                      <h4 className="text-sm font-bold text-forest-900 flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4 text-forest-700" />
                        <span>করণীয় (Action Steps):</span>
                      </h4>
                      <ul className="space-y-2 text-xs sm:text-sm text-ink-800 font-medium">
                        {visionResult.guidance.map((guide, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-forest-700 font-bold">{idx + 1}.</span>
                            <span>{guide}</span>
                          </li>
                        ))}
                      </ul>
                    </Card>
                  )}

                  {/* Avoid / এড়িয়ে চলুন */}
                  {visionResult.avoid && (
                    <div className="p-4 bg-danger-600/10 border border-danger-600/25 rounded-card space-y-1 text-danger-600">
                      <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4" />
                        <span>এড়িয়ে চলুন:</span>
                      </h4>
                      <p className="text-xs sm:text-sm font-medium leading-relaxed">
                        {visionResult.avoid}
                      </p>
                    </div>
                  )}

                  {/* Prevention / প্রতিরোধ */}
                  {visionResult.prevention && (
                    <div className="p-4 bg-leaf-100/60 border border-leaf-500/30 rounded-card space-y-1 text-forest-900">
                      <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <ShieldAlert className="w-4 h-4 text-forest-700" />
                        <span>প্রতিরোধ ব্যবস্থা (Prevention):</span>
                      </h4>
                      <p className="text-xs sm:text-sm font-medium leading-relaxed">
                        {visionResult.prevention}
                      </p>
                    </div>
                  )}

                  {/* Special Warning / বিশেষ সতর্কতা */}
                  {visionResult.special_warning && (
                    <div className="p-4 bg-paddy-400/20 border border-paddy-400/40 rounded-card space-y-1 text-soil-700">
                      <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4 text-soil-700" />
                        <span>বিশেষ সতর্কতা:</span>
                      </h4>
                      <p className="text-xs sm:text-sm font-semibold leading-relaxed">
                        {visionResult.special_warning}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Top Predictions Breakdown Card */}
              {visionResult.top_predictions && visionResult.top_predictions.length > 0 && !visionResult.is_healthy && visionResult.disease !== 'Healthy' && (
                <Card className="p-5 border-line-200 space-y-4">
                  <div className="flex items-center justify-between border-b border-line-200 pb-3">
                    <h3 className="text-sm font-bold text-forest-900 flex items-center gap-2">
                      <BarChart2 className="w-4 h-4 text-leaf-500" />
                      <span>শীর্ষ সম্ভাব্য ফলাফলসমূহ:</span>
                    </h3>
                    <span className="text-[11px] text-ink-600">সম্ভাবনা স্কোর</span>
                  </div>

                  <div className="space-y-3">
                    {visionResult.top_predictions.map((pred, idx) => {
                      const pct = Math.round(pred.confidence * 1000) / 10;
                      const isTop = idx === 0;
                      return (
                        <div key={idx} className="space-y-1.5">
                          <div className="flex items-center justify-between text-xs">
                            <span className={`font-medium ${isTop ? 'text-forest-900 font-bold' : 'text-ink-700'}`}>
                              {idx + 1}. {pred.crop_bn} — {pred.disease_bn}
                            </span>
                            <span className={`font-mono ${isTop ? 'text-forest-700 font-bold' : 'text-ink-600'}`}>
                              {pct.toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-surface h-2 rounded-full overflow-hidden border border-line-200/60">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${isTop ? 'bg-forest-700' : 'bg-leaf-500/60'
                                }`}
                              style={{ width: `${Math.min(100, Math.max(3, pct))}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="text-[11px] text-ink-600 bg-surface p-2.5 rounded-btn border border-line-200 flex items-start gap-1.5">
                    <HelpCircle className="w-3.5 h-3.5 text-forest-700 shrink-0 mt-0.5" />
                    <span>
                      উল্লেখ্য: চূড়ান্ত সিদ্ধান্তের পূর্বে মাঠ পর্যায়ের লক্ষণ এবং অনুমোদিত কৃষি পদক্ষেপগুলো মিলিয়ে নিন।
                    </span>
                  </div>
                </Card>
              )}

              {/* Direct Expert Consultation Action Banner */}
              {visionResult && visionResult.is_plant_leaf !== false && (
                <div className="bg-field-wash border-2 border-forest-700/25 p-5 rounded-card flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-forest-900 flex items-center gap-1.5">
                        <Send className="w-4 h-4 text-forest-700" />
                        <span>ফলাফল নিয়ে কোনো সংশয়? সরাসরি কৃষি কর্মকর্তার মতামত নিন</span>
                      </span>
                    </div>
                    <p className="text-xs text-ink-600 leading-relaxed">
                      আক্রান্ত পাতার ছবি ও প্রশ্ন পাঠিয়ে উপজেলা কৃষি কর্মকর্তা বা উপ-সহকারী কৃষি কর্মকর্তার (SAAO) সরাসরি পরামর্শ ও প্রেসক্রিপশন গ্রহণ করুন।
                    </p>
                  </div>

                  <Button
                    type="button"
                    variant="primary"
                    size="md"
                    onClick={() => setShowDirectExpertModal(true)}
                    className="text-xs sm:text-sm shrink-0 bg-forest-700 hover:bg-forest-800 font-bold px-4 py-2.5 shadow-sm"
                  >
                    <Send className="w-4 h-4 mr-1.5 text-paddy-400" />
                    <span>বিশেষজ্ঞের কাছে সরাসরি পাঠান</span>
                  </Button>
                </div>
              )}

              {directExpertSuccess && (
                <div className="p-4 bg-leaf-100 border border-leaf-500/40 text-forest-900 rounded-btn text-sm font-semibold flex items-center gap-2.5 animate-in fade-in">
                  <CheckCircle2 className="w-5 h-5 text-forest-700 shrink-0" />
                  <span>{directExpertSuccess}</span>
                </div>
              )}

              {/* Mandatory Disclaimer & Model metadata */}
              <div className="text-xs text-ink-600 pt-3 border-t border-line-200 space-y-1">
                <p className="italic">{visionResult.disclaimer || 'এটি AI-ভিত্তিক প্রাথমিক বিশ্লেষণ ও কৃষিতাত্ত্বিক সিদ্ধান্ত সহায়তা। চূড়ান্ত পদক্ষেপ গ্রহণের পূর্বে স্থানীয় উপজেলা কৃষি কর্মকর্তা বা উপ-সহকারী কৃষি কর্মকর্তার (SAAO) পরামর্শ নিন।'}</p>
                <p className="text-[11px] text-ink-600/80">মডেল সংস্করণ: {visionResult.model_name || 'v2.0.0-multi-sector-reviewed'}</p>
              </div>

              {/* Farmer Feedback Section */}
              <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <span className="text-ink-700 font-medium flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4 text-forest-700" />
                  <span>এই ফলাফলটি কি আপনার জন্য সহায়ক হয়েছে?</span>
                </span>

                {directFeedbackSent ? (
                  <span className="text-forest-700 font-semibold flex items-center gap-1.5 bg-leaf-100/70 px-3 py-1.5 rounded-btn border border-leaf-500/30">
                    <CheckCircle2 className="w-4 h-4 text-forest-700" />
                    <span>মতামত প্রদানের জন্য ধন্যবাদ!</span>
                  </span>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleDirectFeedback('helpful')}
                      disabled={isSubmittingDirectFeedback}
                      className="px-3 py-1.5 rounded-btn bg-leaf-100 hover:bg-leaf-500/20 text-forest-900 font-medium flex items-center gap-1.5 border border-leaf-500/30 transition-colors cursor-pointer"
                    >
                      <ThumbsUp className="w-3.5 h-3.5 text-forest-700" />
                      <span>উপকারী</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDirectFeedback('incorrect')}
                      disabled={isSubmittingDirectFeedback}
                      className="px-3 py-1.5 rounded-btn bg-surface hover:bg-line-200 text-ink-700 font-medium flex items-center gap-1.5 border border-line-200 transition-colors cursor-pointer"
                    >
                      <AlertTriangle className="w-3.5 h-3.5 text-paddy-400" />
                      <span>ভুল মনে হচ্ছে</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDirectFeedback('unsafe')}
                      disabled={isSubmittingDirectFeedback}
                      className="px-3 py-1.5 rounded-btn bg-danger-600/10 hover:bg-danger-600/20 text-danger-600 font-medium flex items-center gap-1.5 border border-danger-600/25 transition-colors cursor-pointer"
                    >
                      <AlertOctagon className="w-3.5 h-3.5" />
                      <span>অনিরাপদ</span>
                    </button>
                  </div>
                )}
              </div>

              {/* Scan Tab Result End */}
            </div>
          )}

          {/* FALLBACK IF ONLY CURRENT RESULT EXISTS */}
          {!visionResult && currentResult && (
            <div className="space-y-4 pt-4 border-t border-line-200 animate-in fade-in duration-300">
              <h2 className="text-xl font-bold text-forest-900 flex items-center gap-2">
                <span>বিশ্লেষণ ফলাফল</span>
                <Badge variant="success">নতুন ফলাফল</Badge>
              </h2>
              <CropCaseCard cropCase={currentResult} token={token} />
            </div>
          )}
        </div>
      )}

      {/* TAB 2: DISEASE HISTORY */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-forest-900">আমার পূর্ববর্তী ফসল অনুসন্ধান</h2>
            <span className="text-xs text-ink-600 font-medium">
              মোট সংরক্ষিত রেকর্ড: {historyCases.length}
            </span>
          </div>

          {isLoadingHistory ? (
            <div className="text-center py-12 text-ink-600 text-sm">
              তথ্য লোড হচ্ছে…
            </div>
          ) : historyCases.length === 0 ? (
            <Card className="p-12 text-center border-line-200 space-y-3">
              <History className="w-10 h-10 text-ink-600 mx-auto" />
              <h3 className="font-bold text-base text-forest-900">কোনো হিস্ট্রি পাওয়া যায়নি</h3>
              <p className="text-xs text-ink-600 max-w-sm mx-auto">
                আপনি এখনও কোনো ফসলের রোগ যাচাই করেননি। উপরের বোতামে ক্লিক করে নতুন রোগ যাচাই করুন।
              </p>
            </Card>
          ) : (
            <div className="space-y-6">
              {historyCases.map((cropCase) => (
                <CropCaseCard key={cropCase.id} cropCase={cropCase} token={token} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Direct Send Photo to Expert Modal Dialog */}
      {showDirectExpertModal && (
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
                onClick={() => setShowDirectExpertModal(false)}
                className="text-ink-600 hover:text-ink-900 p-1 rounded-btn hover:bg-surface"
                aria-label="বন্ধ করুন"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {directExpertError && (
              <div className="p-3 bg-danger-600/10 border border-danger-600/20 text-danger-600 rounded-btn text-xs font-medium">
                {directExpertError}
              </div>
            )}

            <form onSubmit={handleDirectSendToExpert} className="space-y-4 text-xs">
              {/* Photo Upload Area */}
              <div>
                <label className="block text-xs font-semibold text-ink-900 mb-1.5">
                  আক্রান্ত পাতার ছবি (ক্যামেরা দিয়ে নতুন ছবি তুলুন বা গ্যালারি থেকে দিন):
                </label>

                {directPhotoPreview ? (
                  <div className="relative rounded-btn overflow-hidden border border-line-200 bg-surface">
                    <img src={directPhotoPreview} alt="নতুন ছবি প্রিভিউ" className="w-full h-44 object-cover" />
                    <button
                      type="button"
                      onClick={handleClearDirectPhoto}
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
                      না দিলে বর্তমান আপলোডকৃত ছবি দিয়েই বিশেষজ্ঞের কাছে পাঠানো হবে
                    </span>
                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={handleDirectPhotoChange}
                      className="hidden"
                    />
                  </label>
                )}
              </div>

              {/* Farmer's message / questions */}
              <div>
                <label htmlFor="directExpertNotesInput" className="block text-xs font-semibold text-ink-900 mb-1">
                  বিশেষজ্ঞ কর্মকর্তার জন্য আপনার প্রশ্ন বা সমস্যা বিবরণ:
                </label>
                <textarea
                  id="directExpertNotesInput"
                  rows={3}
                  value={directFarmerNotes}
                  onChange={(e) => setDirectFarmerNotes(e.target.value)}
                  placeholder="যেমন: কতদিন ধরে এই লক্ষণ দেখা যাচ্ছে, পাতায় কোনো ওষুধ দিয়েছেন কি না, জমিতে পানি কেমন আছে..."
                  className="w-full p-2.5 rounded-btn border border-line-200 text-xs focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-line-200">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowDirectExpertModal(false)}
                  disabled={isSendingDirectExpert}
                >
                  বাতিল
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSendingDirectExpert}
                >
                  <Send className="w-3.5 h-3.5 mr-1 text-paddy-400" />
                  <span>বিশেষজ্ঞের কাছে পাঠান</span>
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};
