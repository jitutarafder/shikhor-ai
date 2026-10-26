import React, { useState } from 'react';
import {
  Clock,
  ShieldAlert,
  AlertCircle,
  CheckCircle2,
  Lock,
  RefreshCw,
  LogOut,
  Sparkles,
  Tractor,
  CloudSun,
  ShoppingBag,
  MessageSquare,
  Upload,
  FileCheck,
  FileUp,
  UserCheck,
  Sprout,
  Truck,
  Briefcase,
  GraduationCap,
} from 'lucide-react';
import { User, useAuth } from '../AuthContext';
import { Button } from '../../../components/ui/Button';
import { Card } from '../../../components/ui/Card';
import { BD_DISTRICTS } from '../../../lib/geoData';
import { getErrorMessage } from '../../../lib/errors';

interface AccountApprovalLockProps {
  user: User;
}

export const AccountApprovalLock: React.FC<AccountApprovalLockProps> = ({ user }) => {
  const { refreshCurrentUser, logout, resubmitNid, uploadNidImage } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState<string | null>(null);

  // Form states for Completing Profile & NID
  const isUnsubmitted = !user.nid || user.nidVerificationStatus === 'unsubmitted';
  const isRejected = user.nidVerificationStatus === 'rejected';
  const isPending = user.nidVerificationStatus === 'pending';

  const [fullName, setFullName] = useState(user.fullName || '');
  const [phone, setPhone] = useState(
    user.phone && !user.phone.startsWith('019') ? user.phone : ''
  );
  const [selectedRole, setSelectedRole] = useState<'farmer' | 'owner' | 'buyer' | 'expert'>(
    user.role === 'admin' || user.role === 'moderator' ? 'farmer' : user.role
  );
  const [districtKey, setDistrictKey] = useState('bogura');
  const [upazila, setUpazila] = useState(BD_DISTRICTS['bogura']?.upazilasBn[0] || '');

  const [nidNumber, setNidNumber] = useState(user.nid || '');
  const [dob, setDob] = useState(user.dob || '');

  const [nidFrontPreview, setNidFrontPreview] = useState<string | null>(user.nidFrontImage || null);
  const [nidFrontUrl, setNidFrontUrl] = useState<string | null>(user.nidFrontImage || null);
  const [isUploadingFront, setIsUploadingFront] = useState(false);

  const [nidBackPreview, setNidBackPreview] = useState<string | null>(user.nidBackImage || null);
  const [nidBackUrl, setNidBackUrl] = useState<string | null>(user.nidBackImage || null);
  const [isUploadingBack, setIsUploadingBack] = useState(false);

  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Toggle form visibility for pending users who want to update their submission
  const [showEditForm, setShowEditForm] = useState(isUnsubmitted || isRejected);

  // Live 10/13/17 digit validator
  const cleanNid = nidNumber.trim().replace(/\D/g, '');
  const isNidValid = /^(?:\d{10}|\d{13}|\d{17})$/.test(cleanNid);

  // Phone validator
  const cleanPhone = phone.trim().replace(/\D/g, '');
  const isPhoneValid = /^01[3-9]\d{8}$/.test(cleanPhone);

  const handleDistrictChange = (key: string) => {
    setDistrictKey(key);
    const upazilas = BD_DISTRICTS[key]?.upazilasBn || [];
    setUpazila(upazilas[0] || '');
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setRefreshMsg(null);
    try {
      await refreshCurrentUser();
      setRefreshMsg('স্ট্যাটাস আপডেট চেক করা হয়েছে।');
    } catch (err: unknown) {
      setRefreshMsg(getErrorMessage(err, 'স্ট্যাটাস রিফ্রেশ করতে সমস্যা হয়েছে।'));
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleFrontImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      setFormError('ছবির সাইজ সর্বোচ্চ ১০ মেগাবাইট (10MB) হতে পারবে।');
      return;
    }
    setFormError(null);
    setNidFrontPreview(URL.createObjectURL(file));
    setIsUploadingFront(true);
    try {
      const uploadedUrl = await uploadNidImage(file);
      setNidFrontUrl(uploadedUrl);
    } catch (err: unknown) {
      setFormError(getErrorMessage(err, 'NID কার্ডের সামনের ছবি আপলোড করতে সমস্যা হয়েছে।'));
    } finally {
      setIsUploadingFront(false);
    }
  };

  const handleBackImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      setFormError('ছবির সাইজ সর্বোচ্চ ১০ মেগাবাইট (10MB) হতে পারবে।');
      return;
    }
    setFormError(null);
    setNidBackPreview(URL.createObjectURL(file));
    setIsUploadingBack(true);
    try {
      const uploadedUrl = await uploadNidImage(file);
      setNidBackUrl(uploadedUrl);
    } catch (err: unknown) {
      setFormError(getErrorMessage(err, 'NID কার্ডের পেছনের ছবি আপলোড করতে সমস্যা হয়েছে।'));
    } finally {
      setIsUploadingBack(false);
    }
  };

  const handleSubmitProfileAndNid = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);

    if (!fullName.trim()) {
      setFormError('অনুগ্রহ করে আপনার পূর্ণ নাম প্রদান করুন।');
      return;
    }

    if (!isPhoneValid) {
      setFormError('সঠিক ১১ ডিজিটের বাংলাদেশি মোবাইল নম্বর প্রদান করুন (যেমন: 017XXXXXXXX)।');
      return;
    }

    if (!cleanNid || !isNidValid) {
      setFormError('জাতীয় পরিচয়পত্র (NID) নম্বর অবশ্যই ১০, ১৩ অথবা ১৭ সংখ্যার হতে হবে।');
      return;
    }

    if (!nidFrontUrl) {
      setFormError('অনুগ্রহ করে আপনার NID কার্ডের সামনের অংশের পরিষ্কার ছবি আপলোড করুন।');
      return;
    }

    if (!nidBackUrl) {
      setFormError('অনুগ্রহ করে আপনার NID কার্ডের পেছনের অংশের পরিষ্কার ছবি আপলোড করুন।');
      return;
    }

    setIsSubmitting(true);
    try {
      const districtName = BD_DISTRICTS[districtKey]?.nameBn || 'বগুড়া';
      await resubmitNid({
        fullName: fullName.trim(),
        phone: cleanPhone,
        role: selectedRole,
        district: districtName,
        upazila: upazila || 'সদর',
        nid: cleanNid,
        dob: dob || undefined,
        nidFrontImage: nidFrontUrl,
        nidBackImage: nidBackUrl,
      });

      setFormSuccess('আপনার তথ্য ও NID কার্ড সফলভাবে জমা দেওয়া হয়েছে! সর্বোচ্চ ২৪ ঘণ্টার মধ্যে অ্যাডমিন যাচাই সম্পন্ন হবে এবং ইমেইলে জানিয়ে দেওয়া হবে।');
      setShowEditForm(false);
      await refreshCurrentUser();
    } catch (err: unknown) {
      setFormError(getErrorMessage(err, 'তথ্য জমা দিতে সমস্যা হয়েছে। পুনরায় চেষ্টা করুন।'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const lockedFeatures = [
    {
      title: 'এআই ফসল রোগ নির্ণয়',
      desc: 'ফসলের পাতার ছবি তুলে কৃত্রিম বুদ্ধিমত্তার মাধ্যমে দ্রুত রোগ সনাক্তকরণ ও সঠিক চিকিৎসা',
      icon: Sparkles,
    },
    {
      title: 'কৃষি যন্ত্রপাতি ভাড়া',
      desc: 'নিকটস্থ যাচাইকৃত মালিকদের কাছ থেকে ট্রাক্টর, পাওয়ার টিলার ও হারভেস্টার ভাড়া',
      icon: Tractor,
    },
    {
      title: 'আবহাওয়া ও স্প্রে পরিকল্পনা',
      desc: 'উপজেলা ভিত্তিক লাইভ আবহাওয়া পূর্বাভাস ও নিরাপদ স্প্রে করার আদর্শ সময়সূচী',
      icon: CloudSun,
    },
    {
      title: 'ফসল কেনাবেচা বাজার',
      desc: 'মধ্যস্বত্বভোগী ছাড়া সরাসরি পাইকারি ক্রেতাদের কাছে ন্যায্যমূল্যে ফসল বিক্রয়',
      icon: ShoppingBag,
    },
    {
      title: 'কৃষি বিশেষজ্ঞ পরামর্শ ও বার্তা',
      desc: 'জেলা কৃষি কর্মকর্তা ও প্রযুক্তিবিদদের সাথে সরাসরি বার্তা বিনিময়ের নিরাপদ মাধ্যম',
      icon: MessageSquare,
    },
  ];

  const rolesList = [
    { id: 'farmer', title: 'কৃষক', desc: 'ফসল চাষ ও রোগ পরামর্শ', icon: Sprout },
    { id: 'owner', title: 'যন্ত্রের মালিক', desc: 'কৃষি যন্ত্রপাতি ভাড়া সেবা', icon: Truck },
    { id: 'buyer', title: 'পাইকার / ক্রেতা', desc: 'সরাসরি ফসল ক্রয়', icon: Briefcase },
    { id: 'expert', title: 'কৃষি কর্মকর্তা / বিশেষজ্ঞ', desc: 'কৃষি পরামর্শ ও পর্যালোচনা', icon: GraduationCap },
  ];

  return (
    <div className="min-h-[85vh] bg-slate-50/50 py-10 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn">
        
        {/* Top Header Card */}
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
            <div className="flex items-center gap-3.5">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                <UserCheck className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-xl sm:text-2xl font-black text-slate-900">
                  {user.fullName ? `স্বাগতম, ${user.fullName}` : 'স্বাগতম!'}
                </h1>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  নিবন্ধিত ইমেইল: <span className="font-semibold text-slate-700">{user.email || 'Google Account'}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="text-xs flex items-center gap-1.5 py-2"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
                {isRefreshing ? 'যাচাই হচ্ছে...' : 'স্ট্যাটাস রিফ্রেশ'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={logout}
                className="text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 border-rose-200 flex items-center gap-1.5 py-2"
              >
                <LogOut className="w-3.5 h-3.5" />
                লগআউট
              </Button>
            </div>
          </div>

          {refreshMsg && (
            <div className="mt-4 p-3 bg-sky-50 border border-sky-200 rounded-xl text-sky-800 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-sky-600 shrink-0" />
              <span>{refreshMsg}</span>
            </div>
          )}

          {/* Current Verification Status Banner */}
          <div className="mt-6">
            {isPending && (
              <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <Clock className="w-6 h-6 text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-sm font-bold text-amber-900">অ্যাকাউন্ট ভেরিফিকেশন প্রক্রিয়াধীন রয়েছে</h2>
                      <span className="px-2 py-0.5 bg-amber-200/80 text-amber-900 text-[11px] font-bold rounded-full">
                        Pending Admin Review
                      </span>
                    </div>
                    <p className="text-xs text-amber-800 mt-1 max-w-xl leading-relaxed">
                      আপনার NID ও প্রোফাইল তথ্য সফলভাবে জমা হয়েছে। <strong>সর্বোচ্চ ২৪ ঘণ্টার মধ্যে</strong> অ্যাডমিন প্যানেল থেকে আপনার অ্যাকাউন্ট পর্যালোচনা ও অনুমোদন করা হবে। অনুমোদন সম্পন্ন হলে আপনাকে <strong>ইমেইলের মাধ্যমে নিশ্চিতকরণ নোটিশ</strong> পাঠিয়ে দেওয়া হবে এবং প্ল্যাটফর্মের সকল ফিচার স্বয়ংক্রিয়ভাবে উন্মুক্ত হয়ে যাবে।
                    </p>
                  </div>
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowEditForm(!showEditForm)}
                  className="text-xs shrink-0 border-amber-300 text-amber-900 hover:bg-amber-100"
                >
                  {showEditForm ? 'তথ্য ফর্ম লুকান' : 'প্রদত্ত তথ্য পরিবর্তন করুন'}
                </Button>
              </div>
            )}

            {isRejected && (
              <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="w-6 h-6 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-sm font-bold text-rose-900">NID যাচাইকরণ বাতিল করা হয়েছে</h2>
                      <span className="px-2 py-0.5 bg-rose-200 text-rose-900 text-[11px] font-bold rounded-full">
                        Action Required
                      </span>
                    </div>
                    <p className="text-xs text-rose-800 mt-1">
                      কারণ: <span className="font-semibold">{user.nidRejectionReason || 'NID কার্ডের ছবি অস্পষ্ট বা ভুল তথ্য প্রদান করা হয়েছিল।'}</span>
                    </p>
                    <p className="text-xs text-rose-700 mt-0.5">
                      অনুগ্রহ করে নিচের ফর্মে আপনার NID কার্ডের পরিষ্কার ছবি ও সঠিক তথ্য দিয়ে পুনরায় জমা দিন।
                    </p>
                  </div>
                </div>

                <Button
                  size="sm"
                  onClick={() => setShowEditForm(true)}
                  className="text-xs bg-rose-600 hover:bg-rose-700 text-white shrink-0"
                >
                  পুনরায় তথ্য জমা দিন
                </Button>
              </div>
            )}

            {isUnsubmitted && (
              <div className="p-4 bg-emerald-50/80 border border-emerald-200 rounded-2xl flex items-start gap-3">
                <ShieldAlert className="w-6 h-6 text-emerald-700 shrink-0 mt-0.5" />
                <div>
                  <h2 className="text-sm font-bold text-emerald-950">
                    গুগল সাইন-ইন সম্পন্ন হয়েছে — অ্যাকাউন্ট সক্রিয় করতে প্রোফাইল ও NID তথ্য দিন
                  </h2>
                  <p className="text-xs text-emerald-800 mt-1 leading-relaxed">
                    কৃষি সেবা গ্রহণ, লেনদেন ও বিশ্বস্ততার স্বার্থে শিখড় এআই-তে সকল ব্যবহারকারীর পরিচয়পত্র যাচাই আবশ্যক। তথ্য জমা দেওয়ার পর <strong>সর্বোচ্চ ২৪ ঘণ্টার মধ্যে</strong> অ্যাডমিন প্যানেল থেকে তা যাচাই করে <strong>ইমেইলের মাধ্যমে অনুমোদন নিশ্চিত করা হবে</strong>।
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Profile Completion & NID Submission Form */}
        {showEditForm && (
          <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 sm:p-8 space-y-6">
            <div className="border-b border-slate-100 pb-4">
              <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <FileCheck className="w-5 h-5 text-emerald-700" />
                প্রোফাইল তথ্য ও জাতীয় পরিচয়পত্র (NID) পূরণ ফর্ম
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                অনুগ্রহ করে নির্ভুল তথ্য প্রদান করুন। অ্যাডমিন অনুমোদনের পর তথ্য পরিবর্তন করতে পুনরায় যাচাইকরণ লাগবে।
              </p>
            </div>

            {formError && (
              <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-2xl text-rose-800 text-xs flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                <span>{formError}</span>
              </div>
            )}

            {formSuccess && (
              <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs flex items-start gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>{formSuccess}</span>
              </div>
            )}

            <form onSubmit={handleSubmitProfileAndNid} className="space-y-6">
              
              {/* Role Selection */}
              <div className="space-y-2">
                <label className="block text-xs font-bold text-slate-700">
                  আপনার ভূমিকা / অ্যাকাউন্টের ধরন <span className="text-rose-500">*</span>
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                  {rolesList.map((r) => {
                    const Icon = r.icon;
                    const isSelected = selectedRole === r.id;
                    return (
                      <button
                        type="button"
                        key={r.id}
                        onClick={() => setSelectedRole(r.id as any)}
                        className={`p-3.5 rounded-2xl border text-left transition-all flex flex-col justify-between ${
                          isSelected
                            ? 'border-emerald-600 bg-emerald-50/50 shadow-sm ring-2 ring-emerald-500/20'
                            : 'border-slate-200 hover:border-slate-300 bg-white'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${isSelected ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
                            <Icon className="w-4 h-4" />
                          </div>
                          {isSelected && <span className="text-emerald-700 text-xs font-bold">✓ নির্বাচিত</span>}
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-slate-900">{r.title}</h4>
                          <p className="text-[11px] text-slate-500 mt-0.5">{r.desc}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Name & Phone */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    আপনার পূর্ণ নাম <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="যেমন: মো: রফিকুল ইসলাম"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    সক্রিয় মোবাইল নম্বর <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="017XXXXXXXX"
                    maxLength={11}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    {phone.length > 0 && !isPhoneValid ? 'সঠিক ১১ সংখ্যার মোবাইল নম্বর লিখুন' : 'কৃষি সেবা ও যোগাযোগের জন্য ব্যবহৃত হবে'}
                  </span>
                </div>
              </div>

              {/* District & Upazila */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    জেলা <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={districtKey}
                    onChange={(e) => handleDistrictChange(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  >
                    {Object.entries(BD_DISTRICTS).map(([key, item]) => (
                      <option key={key} value={key}>
                        {item.nameBn} ({item.nameEn})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    উপজেলা <span className="text-rose-500">*</span>
                  </label>
                  <select
                    value={upazila}
                    onChange={(e) => setUpazila(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  >
                    {(BD_DISTRICTS[districtKey]?.upazilasBn || []).map((u) => (
                      <option key={u} value={u}>
                        {u}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* NID Number & Date of Birth */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    জাতীয় পরিচয়পত্র (NID) নম্বর <span className="text-rose-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={nidNumber}
                    onChange={(e) => setNidNumber(e.target.value)}
                    placeholder="১০, ১৩ বা ১৭ ডিজিট NID নম্বর"
                    maxLength={17}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                  <div className="flex justify-between items-center mt-1 text-[11px]">
                    <span className={isNidValid ? 'text-emerald-700 font-bold' : 'text-slate-500'}>
                      {cleanNid.length === 10 && '১০ ডিজিট (স্মার্ট কার্ড) ✓'}
                      {cleanNid.length === 13 && '১৩ ডিজিট (পুরাতন ফরম্যাট) ✓'}
                      {cleanNid.length === 17 && '১৭ ডিজিট (১৭ সংখ্যার ফরম্যাট) ✓'}
                      {cleanNid.length > 0 && !isNidValid && `${cleanNid.length} ডিজিট (১০, ১৩ বা ১৭ ডিজিট আবশ্যক)`}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1.5">
                    জন্ম তারিখ (NID অনুযায়ী)
                  </label>
                  <input
                    type="date"
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* NID Photos Upload */}
              <div className="space-y-3 pt-2">
                <label className="block text-xs font-bold text-slate-800">
                  জাতীয় পরিচয়পত্রের উভয় পাশের ছবি <span className="text-rose-500">*</span>
                </label>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Front Photo */}
                  <div className="border-2 border-dashed border-slate-200 rounded-2xl p-4 text-center hover:border-emerald-500 transition-colors bg-slate-50/50">
                    {nidFrontPreview ? (
                      <div className="space-y-2">
                        <img
                          src={nidFrontPreview}
                          alt="NID Front Preview"
                          className="h-32 mx-auto object-cover rounded-xl border border-slate-200"
                        />
                        <div className="flex justify-center items-center gap-2">
                          <span className="text-xs text-emerald-700 font-bold flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            সামনের ছবি যুক্ত হয়েছে
                          </span>
                          <label className="text-xs text-slate-500 hover:text-slate-800 underline cursor-pointer">
                            পরিবর্তন
                            <input
                              type="file"
                              accept="image/jpeg,image/png,image/webp"
                              onChange={handleFrontImageUpload}
                              className="hidden"
                            />
                          </label>
                        </div>
                      </div>
                    ) : (
                      <label className="cursor-pointer block py-4">
                        <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                        <span className="text-xs font-bold text-slate-700 block">
                          NID কার্ডের সামনের ছবি আপলোড করুন
                        </span>
                        <span className="text-[11px] text-slate-400 block mt-0.5">
                          (JPG, PNG বা WebP • সর্বোচ্চ ১০ মেগাবাইট)
                        </span>
                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          onChange={handleFrontImageUpload}
                          className="hidden"
                        />
                      </label>
                    )}
                    {isUploadingFront && (
                      <p className="text-xs text-emerald-700 font-semibold animate-pulse mt-2">
                        ছবি আপলোড ও এনকোড হচ্ছে...
                      </p>
                    )}
                  </div>

                  {/* Back Photo */}
                  <div className="border-2 border-dashed border-slate-200 rounded-2xl p-4 text-center hover:border-emerald-500 transition-colors bg-slate-50/50">
                    {nidBackPreview ? (
                      <div className="space-y-2">
                        <img
                          src={nidBackPreview}
                          alt="NID Back Preview"
                          className="h-32 mx-auto object-cover rounded-xl border border-slate-200"
                        />
                        <div className="flex justify-center items-center gap-2">
                          <span className="text-xs text-emerald-700 font-bold flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            পেছনের ছবি যুক্ত হয়েছে
                          </span>
                          <label className="text-xs text-slate-500 hover:text-slate-800 underline cursor-pointer">
                            পরিবর্তন
                            <input
                              type="file"
                              accept="image/jpeg,image/png,image/webp"
                              onChange={handleBackImageUpload}
                              className="hidden"
                            />
                          </label>
                        </div>
                      </div>
                    ) : (
                      <label className="cursor-pointer block py-4">
                        <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                        <span className="text-xs font-bold text-slate-700 block">
                          NID কার্ডের পেছনের ছবি আপলোড করুন
                        </span>
                        <span className="text-[11px] text-slate-400 block mt-0.5">
                          (JPG, PNG বা WebP • সর্বোচ্চ ১০ মেগাবাইট)
                        </span>
                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          onChange={handleBackImageUpload}
                          className="hidden"
                        />
                      </label>
                    )}
                    {isUploadingBack && (
                      <p className="text-xs text-emerald-700 font-semibold animate-pulse mt-2">
                        ছবি আপলোড ও এনকোড হচ্ছে...
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Submit Action */}
              <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
                {isPending && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setShowEditForm(false)}
                    className="text-xs"
                  >
                    বাতিল করুন
                  </Button>
                )}
                <Button
                  type="submit"
                  disabled={isSubmitting || isUploadingFront || isUploadingBack}
                  className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs sm:text-sm px-6 py-2.5 rounded-xl flex items-center gap-2 shadow-sm font-bold"
                >
                  <FileUp className="w-4 h-4" />
                  {isSubmitting ? 'তথ্য জমা দেওয়া হচ্ছে...' : 'অ্যাডমিন পর্যালোচনার জন্য জমা দিন'}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Locked Features Preview Grid */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 px-1">
            <Lock className="w-4 h-4 text-slate-400" />
            <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider">
              ভেরিফিকেশনের পর আনলক হবে যে সকল ফিচার:
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {lockedFeatures.map((feat, idx) => {
              const Icon = feat.icon;
              return (
                <Card
                  key={idx}
                  className="p-5 border-slate-200/80 bg-white/70 backdrop-blur-sm relative overflow-hidden rounded-2xl group opacity-85"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center shrink-0">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0 pr-6">
                      <h4 className="text-sm font-bold text-slate-800">{feat.title}</h4>
                      <p className="text-xs text-slate-500 mt-1 leading-relaxed">{feat.desc}</p>
                    </div>
                    <div className="absolute top-4 right-4 text-slate-400">
                      <Lock className="w-4 h-4" />
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
};
