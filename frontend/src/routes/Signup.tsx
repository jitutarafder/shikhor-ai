import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Sprout,
  User,
  Tractor,
  Store,
  Award,
  AlertCircle,
  MapPin,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Upload,
  X,
  FileCheck,
  Mail,
  KeyRound,
  RefreshCw,
  ShieldCheck,
  Lock,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { BD_DISTRICTS } from '../lib/geoData';
import { signInWithGoogle } from '../lib/firebase';
import { getErrorMessage } from '../lib/errors';

export const Signup: React.FC = () => {
  const navigate = useNavigate();
  const { register, loginWithGoogle, uploadNidImage, sendSignupEmailOtp, verifySignupEmailOtp } = useAuth();

  // 4 Steps as requested:
  // 1: Full name, phone, NID, DoB, password
  // 2: Role selection
  // 3: Gmail OTP verification
  // 4: NID photo upload, location, profile & final submission
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Step 1: Account & Credentials
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [nid, setNid] = useState('');
  const [dob, setDob] = useState('');
  const [password, setPassword] = useState('');

  // Step 2: Role
  const [role, setRole] = useState<'farmer' | 'owner' | 'buyer' | 'expert'>('farmer');

  // Step 3: Gmail OTP Verification state
  const [email, setEmail] = useState('');
  const [emailOtp, setEmailOtp] = useState('');
  const [emailVerificationToken, setEmailVerificationToken] = useState<string | null>(null);
  const [isEmailVerified, setIsEmailVerified] = useState(false);
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [otpCooldown, setOtpCooldown] = useState(0);
  const [otpSuccessMsg, setOtpSuccessMsg] = useState<string | null>(null);
  const [otpErrorMsg, setOtpErrorMsg] = useState<string | null>(null);
  const [devOtpHint, setDevOtpHint] = useState<string | null>(null);

  // Step 4: NID Photos, Location & Role Profile Details
  const [nidFrontPreview, setNidFrontPreview] = useState<string | null>(null);
  const [nidFrontUrl, setNidFrontUrl] = useState<string | null>(null);
  const [uploadingFront, setUploadingFront] = useState(false);

  const [nidBackPreview, setNidBackPreview] = useState<string | null>(null);
  const [nidBackUrl, setNidBackUrl] = useState<string | null>(null);
  const [uploadingBack, setUploadingBack] = useState(false);

  const [selectedDistrict, setSelectedDistrict] = useState<string>('bogura');
  const [selectedUpazila, setSelectedUpazila] = useState<string>('শেরপুর');
  const [primaryCrops, setPrimaryCrops] = useState('ধান, আলু, সরিষা');
  const [serviceRadiusKm, setServiceRadiusKm] = useState(15);
  const [businessName, setBusinessName] = useState('');
  const [designation, setDesignation] = useState('');

  const currentDistrictData = BD_DISTRICTS[selectedDistrict] || BD_DISTRICTS['bogura'];

  const handleDistrictChange = (districtKey: string) => {
    setSelectedDistrict(districtKey);
    const district = BD_DISTRICTS[districtKey];
    if (district && district.upazilasBn.length > 0) {
      setSelectedUpazila(district.upazilasBn[0]);
    }
  };

  const handleFrontImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg('ছবির সাইজ সর্বোচ্চ ৫ মেগাবাইট (5MB) হতে পারবে।');
      return;
    }
    setNidFrontPreview(URL.createObjectURL(file));
    setUploadingFront(true);
    try {
      const url = await uploadNidImage(file);
      setNidFrontUrl(url);
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, 'NID কার্ডের সামনের ছবি আপলোড করতে সমস্যা হয়েছে।'));
    } finally {
      setUploadingFront(false);
    }
  };

  const handleBackImageChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 5 * 1024 * 1024) {
      setErrorMsg('ছবির সাইজ সর্বোচ্চ ৫ মেগাবাইট (5MB) হতে পারবে।');
      return;
    }
    setNidBackPreview(URL.createObjectURL(file));
    setUploadingBack(true);
    try {
      const url = await uploadNidImage(file);
      setNidBackUrl(url);
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, 'NID কার্ডের পেছনের ছবি আপলোড করতে সমস্যা হয়েছে।'));
    } finally {
      setUploadingBack(false);
    }
  };

  useEffect(() => {
    if (otpCooldown > 0) {
      const timer = setTimeout(() => setOtpCooldown((prev) => prev - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [otpCooldown]);

  const handleSendEmailOtp = async () => {
    setOtpErrorMsg(null);
    setOtpSuccessMsg(null);
    setErrorMsg(null);

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setOtpErrorMsg('অনুগ্রহ করে একটি বৈধ ইমেইল ঠিকানা লিখুন।');
      return;
    }
    const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    if (!emailRegex.test(cleanEmail)) {
      setOtpErrorMsg('সঠিক ইমেইল ফরম্যাট দিন (যেমন: farmer@example.com)।');
      return;
    }

    setIsSendingOtp(true);
    try {
      const res = await sendSignupEmailOtp(cleanEmail);
      setOtpSent(true);
      setOtpCooldown(60);
      setOtpSuccessMsg(res.message || 'আপনার ইমেইলে ওটিপি কোড পাঠানো হয়েছে।');
      if (res.devOtp) {
        setDevOtpHint(res.devOtp);
        setEmailOtp(res.devOtp);
      } else {
        setDevOtpHint(null);
      }
    } catch (err: unknown) {
      setOtpErrorMsg(getErrorMessage(err, 'ওটিপি পাঠাতে সমস্যা হয়েছে। পুনরায় চেষ্টা করুন।'));
    } finally {
      setIsSendingOtp(false);
    }
  };

  const handleVerifyEmailOtp = async () => {
    setOtpErrorMsg(null);
    setOtpSuccessMsg(null);
    setErrorMsg(null);

    if (emailOtp.trim().length !== 6) {
      setOtpErrorMsg('অনুগ্রহ করে ৬-সংখ্যার ওটিপি কোডটি লিখুন।');
      return;
    }

    setIsVerifyingOtp(true);
    try {
      const res = await verifySignupEmailOtp(email.trim(), emailOtp.trim());
      setEmailVerificationToken(res.verificationToken);
      setIsEmailVerified(true);
      setOtpSuccessMsg('✓ ইমেইল সফলভাবে যাচাই হয়েছে!');
    } catch (err: unknown) {
      setOtpErrorMsg(getErrorMessage(err, 'ভুল বা মেয়াদোত্তীর্ণ ওটিপি কোড।'));
    } finally {
      setIsVerifyingOtp(false);
    }
  };

  const handleResetEmailVerification = () => {
    setIsEmailVerified(false);
    setEmailVerificationToken(null);
    setOtpSent(false);
    setEmailOtp('');
    setDevOtpHint(null);
    setOtpSuccessMsg(null);
    setOtpErrorMsg(null);
  };

  // Step 1 -> Step 2 validation
  const handleNextFromStep1 = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!fullName.trim() || !phone.trim() || !password || !nid.trim()) {
      setErrorMsg('অনুগ্রহ করে নাম, ফোন, এনআইডি (NID) ও পাসওয়ার্ড পূরণ করুন।');
      return;
    }

    const cleanPhone = phone.trim().replace(/\D/g, '');
    if (cleanPhone.length !== 11 || !cleanPhone.startsWith('01')) {
      setErrorMsg('সঠিক ১১ ডিজিটের বাংলাদেশি মোবাইল নম্বর দিন (যেমন: 01711XXXXXX)।');
      return;
    }

    const cleanNid = nid.trim();
    if (!/^(?:\d{10}|\d{13}|\d{17})$/.test(cleanNid)) {
      setErrorMsg('জাতীয় পরিচয়পত্র (NID) নম্বর অবশ্যই ১০ (স্মার্ট কার্ড), ১৩ অথবা ১৭ ডিজিটের হতে হবে।');
      return;
    }

    if (password.length < 10) {
      setErrorMsg('নিরাপত্তার স্বার্থে পাসওয়ার্ড কমপক্ষে ১০ অক্ষরের হতে হবে।');
      return;
    }

    setStep(2);
  };

  // Step 2 -> Step 3
  const handleNextFromStep2 = () => {
    setErrorMsg(null);
    setStep(3);
  };

  // Step 3 -> Step 4 validation (mandates email OTP verification)
  const handleNextFromStep3 = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!email.trim()) {
      setErrorMsg('অনুগ্রহ করে আপনার ইমেইল ঠিকানা প্রদান করুন।');
      return;
    }

    const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
    if (!emailRegex.test(email.trim())) {
      setErrorMsg('সঠিক ফরম্যাটের ইমেইল ঠিকানা দিন (যেমন: farmer@example.com)।');
      return;
    }

    if (!isEmailVerified || !emailVerificationToken) {
      setErrorMsg('অনুগ্রহ করে ওটিপি কোড দিয়ে আপনার জিমেইল যাচাই (Verify) সম্পন্ন করুন।');
      return;
    }

    setStep(4);
  };

  const handleGoogleSignup = async () => {
    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      const { idToken, user: gUser } = await signInWithGoogle();
      await loginWithGoogle({
        idToken,
        fullName: gUser?.displayName || undefined,
        role,
        nid: nid ? nid.trim() : undefined,
      });
      navigate('/app');
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, 'Google দিয়ে সাইন আপ সম্পন্ন করা সম্ভব হয়নি।'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Step 4: Final Submission
  const handleFinalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      // 1. Authoritative Backend Registration with profile data
      await register({
        phone: phone.trim(),
        password,
        full_name: fullName.trim(),
        role,
        email: email.trim(),
        emailVerificationToken: emailVerificationToken || undefined,
        nid: nid.trim(),
        dob: dob || undefined,
        nidFrontImage: nidFrontUrl || undefined,
        nidBackImage: nidBackUrl || undefined,
        district: currentDistrictData.nameBn,
        upazila: selectedUpazila,
        primaryCrops: role === 'farmer' ? primaryCrops : undefined,
        serviceRadiusKm: role === 'owner' ? Number(serviceRadiusKm) : undefined,
        businessName: role === 'buyer' ? businessName : undefined,
        designation: role === 'expert' ? designation : undefined,
      });

      // 2. Redirect to /login with pre-filled phone and clear success message
      navigate('/login', {
        replace: true,
        state: {
          phone: phone.trim(),
          successMsg: 'আপনার অ্যাকাউন্ট সফলভাবে তৈরি হয়েছে! সর্বোচ্চ ২৪ ঘণ্টার মধ্যে অ্যাডমিন ভেরিফিকেশন সম্পন্ন হবে এবং আপনাকে ইমেইলে জানানো হবে। অনুগ্রহ করে আপনার পাসওয়ার্ড দিয়ে লগইন করুন।',
        },
      });
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, 'নিবন্ধন সম্পন্ন করতে সমস্যা হয়েছে।'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <Card className="max-w-xl w-full p-6 sm:p-8 border-line-200 shadow-soft space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center mx-auto">
            <Sprout className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold text-forest-900">নতুন অ্যাকাউন্ট তৈরি করুন</h1>
          <p className="text-xs sm:text-sm text-ink-600">৪টি সহজ ধাপে শুরু করুন আপনার বিশ্বস্ত কৃষি সহচর যাত্রা</p>
        </div>

        {/* 4-Step Indicator */}
        <div className="flex items-center justify-between relative px-4 py-2">
          <div className="absolute left-6 right-6 top-1/2 -translate-y-1/2 h-0.5 bg-line-200 -z-0" />
          {[
            { num: 1, label: 'তথ্য' },
            { num: 2, label: 'ভূমিকা' },
            { num: 3, label: 'ইমেইল' },
            { num: 4, label: 'এনআইডি ও জমা' },
          ].map((s) => (
            <div key={s.num} className="flex flex-col items-center gap-1 z-10">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-xs ${
                  step >= s.num
                    ? 'bg-forest-700 text-canvas ring-4 ring-forest-50'
                    : 'bg-surface text-ink-600 border border-line-200'
                }`}
              >
                {step > s.num ? '✓' : s.num}
              </div>
              <span
                className={`text-[10px] font-semibold hidden sm:block ${
                  step >= s.num ? 'text-forest-900 font-bold' : 'text-slate-400'
                }`}
              >
                {s.label}
              </span>
            </div>
          ))}
        </div>

        {/* Error message */}
        {errorMsg && (
          <div className="p-3.5 bg-danger-600/10 border border-danger-600/20 text-danger-600 rounded-btn text-sm flex items-center gap-2.5">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* ============================================================ */}
        {/* PAGE 1: Full name, phone, NID, DoB, password                */}
        {/* ============================================================ */}
        {step === 1 && (
          <form onSubmit={handleNextFromStep1} className="space-y-4">
            <div className="border-b border-line-200 pb-2 flex items-center justify-between">
              <h2 className="text-sm font-bold text-forest-900">
                ধাপ ১: ব্যক্তিগত তথ্য ও পাসওয়ার্ড
              </h2>
              <span className="text-xs text-slate-500">ধাপ ১/৪</span>
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1">
                আপনার পূর্ণ নাম <span className="text-danger-600">*</span>
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="যেমন: মো. রহিম উদ্দিন"
                className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1">
                মোবাইল নম্বর <span className="text-danger-600">*</span>
              </label>
              <input
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="০১৭১১-XXXXXX"
                className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base font-mono"
              />
              <span className="text-xs text-ink-600 mt-1 block">
                সঠিক ১১ ডিজিটের বাংলাদেশি নম্বর ব্যবহার করুন
              </span>
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1">
                জাতীয় পরিচয়পত্র (NID) নম্বর <span className="text-danger-600">*</span>
              </label>
              <input
                type="text"
                required
                value={nid}
                onChange={(e) => setNid(e.target.value.replace(/\D/g, ''))}
                placeholder="১০, ১৩ বা ১৭ ডিজিটের NID নম্বর"
                className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base font-mono"
              />
              <span className="text-xs text-ink-600 mt-1 block">
                সরকারি পরিচয় নিশ্চিতকরণে ১০ (স্মার্ট কার্ড), ১৩ বা ১৭ ডিজিটের NID দিন
              </span>
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1">
                জন্ম তারিখ (NID অনুযায়ী)
              </label>
              <input
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1">
                পাসওয়ার্ড <span className="text-danger-600">*</span>
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="কমপক্ষে ১০ অক্ষরের শক্তিশালী পাসওয়ার্ড"
                className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base"
              />
              <span className="text-xs text-ink-600 mt-1 block">
                নিরাপত্তা নীতি অনুযায়ী কমপক্ষে ১০ অক্ষরের পাসওয়ার্ড আবশ্যক
              </span>
            </div>

            <Button type="submit" variant="primary" size="lg" fullWidth>
              <span>পরবর্তী ধাপ (ভূমিকা নির্বাচন)</span>
              <ArrowRight className="w-5 h-5 ml-1" />
            </Button>

            <div className="relative my-3">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-line-200" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-canvas px-3 text-ink-600">অথবা</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleGoogleSignup}
              disabled={isSubmitting}
              className="w-full min-h-[48px] px-4 rounded-btn border border-line-200 bg-white hover:bg-slate-50 text-ink-900 font-semibold flex items-center justify-center gap-3 transition-colors shadow-xs"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span>Google দিয়ে সাইন আপ করুন</span>
            </button>
          </form>
        )}

        {/* ============================================================ */}
        {/* PAGE 2: Role Selection (Same as before)                      */}
        {/* ============================================================ */}
        {step === 2 && (
          <div className="space-y-5">
            <div className="border-b border-line-200 pb-2 flex items-center justify-between">
              <h2 className="text-sm font-bold text-forest-900">
                ধাপ ২: প্ল্যাটফর্মে আপনার প্রাথমিক ভূমিকা নির্বাচন করুন
              </h2>
              <span className="text-xs text-slate-500">ধাপ ২/৪</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              <div
                onClick={() => setRole('farmer')}
                className={`p-4 rounded-card border cursor-pointer transition-all ${
                  role === 'farmer'
                    ? 'border-forest-700 bg-leaf-100/60 ring-2 ring-forest-700'
                    : 'border-line-200 hover:bg-surface'
                }`}
              >
                <div className="flex items-center gap-3">
                  <User className="w-6 h-6 text-forest-700" />
                  <div className="font-bold text-base text-forest-900">কৃষক</div>
                </div>
                <p className="text-xs text-ink-600 mt-2 leading-relaxed">
                  ফসলের রোগ যাচাই, যন্ত্র ভাড়া নেওয়া ও আবহাওয়া ভিত্তিক পরিকল্পনা সুবিধা।
                </p>
              </div>

              <div
                onClick={() => setRole('owner')}
                className={`p-4 rounded-card border cursor-pointer transition-all ${
                  role === 'owner'
                    ? 'border-forest-700 bg-leaf-100/60 ring-2 ring-forest-700'
                    : 'border-line-200 hover:bg-surface'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Tractor className="w-6 h-6 text-forest-700" />
                  <div className="font-bold text-base text-forest-900">যন্ত্রের মালিক</div>
                </div>
                <p className="text-xs text-ink-600 mt-2 leading-relaxed">
                  কৃষিযন্ত্রের তালিকাভুক্তকরণ, ভাড়ার অনুরোধ গ্রহণ ও আয় বৃদ্ধি।
                </p>
              </div>

              <div
                onClick={() => setRole('buyer')}
                className={`p-4 rounded-card border cursor-pointer transition-all ${
                  role === 'buyer'
                    ? 'border-forest-700 bg-leaf-100/60 ring-2 ring-forest-700'
                    : 'border-line-200 hover:bg-surface'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Store className="w-6 h-6 text-forest-700" />
                  <div className="font-bold text-base text-forest-900">ফসল পাইকার / ক্রেতা</div>
                </div>
                <p className="text-xs text-ink-600 mt-2 leading-relaxed">
                  সরাসরি মাঠ থেকে কৃষকের ফসল ক্রয় ও যোগাযোগের সুবিধা।
                </p>
              </div>

              <div
                onClick={() => setRole('expert')}
                className={`p-4 rounded-card border cursor-pointer transition-all ${
                  role === 'expert'
                    ? 'border-forest-700 bg-leaf-100/60 ring-2 ring-forest-700'
                    : 'border-line-200 hover:bg-surface'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Award className="w-6 h-6 text-forest-700" />
                  <div className="font-bold text-base text-forest-900">কৃষি বিশেষজ্ঞ / কর্মকর্তা</div>
                </div>
                <p className="text-xs text-ink-600 mt-2 leading-relaxed">
                  জটিল রোগ সমাধান, যাচাইকৃত কৃষি পরামর্শ ও মাঠ পর্যায়ের সহায়তা।
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <Button variant="outline" size="lg" onClick={() => setStep(1)} className="w-1/3">
                <ArrowLeft className="w-4 h-4 mr-1" />
                <span>পেছনে</span>
              </Button>
              <Button variant="primary" size="lg" onClick={handleNextFromStep2} className="w-2/3">
                <span>পরবর্তী ধাপ (ইমেইল যাচাই)</span>
                <ArrowRight className="w-5 h-5 ml-1" />
              </Button>
            </div>
          </div>
        )}

        {/* ============================================================ */}
        {/* PAGE 3: Gmail OTP Verification (Dedicated Step)             */}
        {/* ============================================================ */}
        {step === 3 && (
          <form onSubmit={handleNextFromStep3} className="space-y-5">
            <div className="border-b border-line-200 pb-2 flex items-center justify-between">
              <h2 className="text-sm font-bold text-forest-900">
                ধাপ ৩: জিমেইল ওটিপি (Gmail OTP) যাচাই
              </h2>
              <span className="text-xs text-slate-500">ধাপ ৩/৪</span>
            </div>

            <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-forest-900 font-bold text-sm">
                <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>অ্যাকাউন্টের নিরাপত্তা ও মালিকানা নিশ্চিতকরণ</span>
              </div>
              <p className="text-xs text-ink-600 leading-relaxed">
                পাসওয়ার্ড রিকভারি এবং নিরাপদ নোটিফিকেশনের জন্য ইমেইল যাচাই বাধ্যতামূলক। আপনার দেওয়া জিমেইলে একটি ৬-সংখ্যার ওটিপি (OTP) পাঠানো হবে।
              </p>
            </div>

            {/* Email Input & Send OTP Button */}
            <div className="space-y-3 p-4 bg-slate-50 border border-slate-200/90 rounded-2xl">
              <div className="flex items-center justify-between">
                <label className="block text-sm font-bold text-ink-900">
                  ইমেইল ঠিকানা <span className="text-danger-600">*</span>
                </label>
                {isEmailVerified ? (
                  <span className="text-xs font-bold text-emerald-700 bg-emerald-100/90 border border-emerald-300 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    যাচাইকৃত (Verified)
                  </span>
                ) : (
                  <span className="text-xs text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                    ওটিপি যাচাই আবশ্যক
                  </span>
                )}
              </div>

              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    disabled={isEmailVerified || isSendingOtp}
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      if (otpSent) {
                        setOtpSent(false);
                        setEmailOtp('');
                        setOtpErrorMsg(null);
                        setOtpSuccessMsg(null);
                      }
                    }}
                    placeholder="যেমন: yourname@gmail.com"
                    className={`w-full pl-10 pr-4 min-h-[46px] rounded-xl border text-sm ${
                      isEmailVerified
                        ? 'bg-slate-100 text-slate-600 border-slate-200 cursor-not-allowed'
                        : 'bg-white border-line-200 focus:border-forest-700'
                    }`}
                  />
                </div>

                {!isEmailVerified ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={isSendingOtp || otpCooldown > 0 || !email.trim()}
                    onClick={handleSendEmailOtp}
                    className="shrink-0 min-h-[46px] px-3.5 font-bold border-forest-700 text-forest-800 hover:bg-forest-50"
                  >
                    {isSendingOtp ? (
                      <span className="flex items-center gap-1">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        পাঠানো হচ্ছে...
                      </span>
                    ) : otpCooldown > 0 ? (
                      `পুনরায় (${otpCooldown}s)`
                    ) : otpSent ? (
                      'কোড আবার পাঠান'
                    ) : (
                      'ওটিপি পাঠান'
                    )}
                  </Button>
                ) : (
                  <button
                    type="button"
                    onClick={handleResetEmailVerification}
                    className="shrink-0 text-xs text-forest-800 font-bold hover:underline px-2.5"
                  >
                    পরিবর্তন
                  </button>
                )}
              </div>

              {/* Feedback messages */}
              {otpSuccessMsg && (
                <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                  <span>{otpSuccessMsg}</span>
                </div>
              )}
              {otpErrorMsg && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{otpErrorMsg}</span>
                </div>
              )}

              {/* OTP Entry Box */}
              {otpSent && !isEmailVerified && (
                <div className="mt-3 p-3.5 bg-white border border-forest-200 rounded-xl space-y-2.5 shadow-xs">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-700 flex items-center gap-1">
                      <KeyRound className="w-3.5 h-3.5 text-forest-700" />
                      জিমেইলে পাঠানো ৬-সংখ্যার কোডটি দিন
                    </span>
                    <span className="text-[11px] text-slate-400">মেয়াদ ১০ মিনিট</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      maxLength={6}
                      value={emailOtp}
                      onChange={(e) => setEmailOtp(e.target.value.replace(/\D/g, ''))}
                      placeholder="১২৩৪৫৬"
                      className="w-32 px-3 py-2 text-center font-mono font-bold tracking-widest text-lg rounded-xl border border-slate-300 bg-slate-50 focus:bg-white focus:border-forest-700 focus:outline-none"
                    />
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      onClick={handleVerifyEmailOtp}
                      disabled={isVerifyingOtp || emailOtp.length !== 6}
                      className="flex-1 min-h-[42px] font-bold"
                    >
                      {isVerifyingOtp ? 'যাচাই হচ্ছে...' : 'ওটিপি যাচাই সম্পন্ন করুন'}
                    </Button>
                  </div>

                  {devOtpHint && (
                    <div className="p-2.5 bg-amber-50 border border-amber-200/90 rounded-xl text-amber-900 text-xs flex flex-col gap-1">
                      <div className="flex items-center gap-1.5 font-bold">
                        <span>💡 টেস্ট ওটিপি কোড:</span>
                        <span className="font-mono bg-white px-2 py-0.5 rounded border border-amber-300 text-amber-800 text-sm tracking-wider">
                          {devOtpHint}
                        </span>
                      </div>
                      <span className="text-[11px] text-amber-700 leading-relaxed">
                        (লোকাল ডিভাইসে জিমেইল SMTP সেট না থাকলে কোডটি স্বয়ংক্রিয়ভাবে এখানে প্রদর্শিত হয়।)
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex items-center gap-3 pt-2">
              <Button variant="outline" size="lg" onClick={() => setStep(2)} className="w-1/3">
                <ArrowLeft className="w-4 h-4 mr-1" />
                <span>পেছনে</span>
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="lg"
                disabled={!isEmailVerified}
                className="w-2/3"
              >
                <span>পরবর্তী ধাপ (এনআইডি ছবি ও প্রোফাইল)</span>
                <ArrowRight className="w-5 h-5 ml-1" />
              </Button>
            </div>
          </form>
        )}

        {/* ============================================================ */}
        {/* PAGE 4: NID Photo Upload, Location, Profile & Submit         */}
        {/* ============================================================ */}
        {step === 4 && (
          <form onSubmit={handleFinalSubmit} className="space-y-4">
            <div className="border-b border-line-200 pb-2 flex items-center justify-between">
              <h2 className="text-sm font-bold text-forest-900">
                ধাপ ৪: এনআইডি কার্ডের ছবি ও প্রোফাইল জমা
              </h2>
              <span className="text-xs text-slate-500">ধাপ ৪/৪</span>
            </div>

            {/* NID Card Photo Upload Box */}
            <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
              <div>
                <label className="block text-sm font-bold text-forest-900 flex items-center gap-1.5">
                  <FileCheck className="w-4 h-4 text-forest-700" />
                  NID কার্ডের ছবি আপলোড (অ্যাডমিন অনুমোদনের জন্য)
                </label>
                <p className="text-xs text-ink-600 mt-0.5">
                  অ্যাডমিন আপনার NID-র ছবি দেখে অ্যাকাউন্ট অনুমোদন করবেন। ছবি স্পষ্ট ও পাঠযোগ্য হতে হবে।
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Front Image */}
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-slate-700 block">
                    সামনের অংশ (Front)
                  </span>
                  {nidFrontPreview ? (
                    <div className="relative rounded-lg border border-line-200 overflow-hidden bg-white aspect-video flex items-center justify-center">
                      <img src={nidFrontPreview} alt="NID Front" className="w-full h-full object-cover" />
                      <button
                        type="button"
                        onClick={() => {
                          setNidFrontPreview(null);
                          setNidFrontUrl(null);
                        }}
                        className="absolute top-1 right-1 bg-black/60 hover:bg-black text-white p-1 rounded-full"
                        title="ছবি মুছুন"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <label className="border-2 border-dashed border-line-200 hover:border-forest-700 rounded-lg p-3 text-center cursor-pointer flex flex-col items-center justify-center gap-1 bg-white hover:bg-slate-50 transition-colors aspect-video">
                      <Upload className="w-5 h-5 text-forest-700" />
                      <span className="text-xs text-slate-600 font-medium">সামনের ছবি বেছে নিন</span>
                      <span className="text-[10px] text-slate-400">JPG, PNG (সর্বোচ্চ 5MB)</span>
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        onChange={handleFrontImageChange}
                        className="hidden"
                      />
                    </label>
                  )}
                  {uploadingFront && <p className="text-[11px] text-forest-700 animate-pulse">আপলোড হচ্ছে...</p>}
                </div>

                {/* Back Image */}
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-slate-700 block">
                    পেছনের অংশ (Back)
                  </span>
                  {nidBackPreview ? (
                    <div className="relative rounded-lg border border-line-200 overflow-hidden bg-white aspect-video flex items-center justify-center">
                      <img src={nidBackPreview} alt="NID Back" className="w-full h-full object-cover" />
                      <button
                        type="button"
                        onClick={() => {
                          setNidBackPreview(null);
                          setNidBackUrl(null);
                        }}
                        className="absolute top-1 right-1 bg-black/60 hover:bg-black text-white p-1 rounded-full"
                        title="ছবি মুছুন"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <label className="border-2 border-dashed border-line-200 hover:border-forest-700 rounded-lg p-3 text-center cursor-pointer flex flex-col items-center justify-center gap-1 bg-white hover:bg-slate-50 transition-colors aspect-video">
                      <Upload className="w-5 h-5 text-forest-700" />
                      <span className="text-xs text-slate-600 font-medium">পেছনের ছবি বেছে নিন</span>
                      <span className="text-[10px] text-slate-400">JPG, PNG (সর্বোচ্চ 5MB)</span>
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp"
                        onChange={handleBackImageChange}
                        className="hidden"
                      />
                    </label>
                  )}
                  {uploadingBack && <p className="text-[11px] text-forest-700 animate-pulse">আপলোড হচ্ছে...</p>}
                </div>
              </div>
            </div>

            {/* Location (District & Upazila) */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  জেলা <span className="text-danger-600">*</span>
                </label>
                <select
                  value={selectedDistrict}
                  onChange={(e) => handleDistrictChange(e.target.value)}
                  className="w-full px-3 min-h-[48px] rounded-btn border border-line-200 bg-canvas text-base"
                >
                  {Object.entries(BD_DISTRICTS).map(([key, data]) => (
                    <option key={key} value={key}>
                      {data.nameBn}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  উপজেলা <span className="text-danger-600">*</span>
                </label>
                <select
                  value={selectedUpazila}
                  onChange={(e) => setSelectedUpazila(e.target.value)}
                  className="w-full px-3 min-h-[48px] rounded-btn border border-line-200 bg-canvas text-base"
                >
                  {currentDistrictData.upazilasBn.map((upazila) => (
                    <option key={upazila} value={upazila}>
                      {upazila}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* GPS helper */}
            <div className="p-3 bg-surface rounded-btn border border-line-200 flex items-center justify-between text-xs text-ink-600">
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-forest-700" />
                <span>জিপিএস ছাড়া ম্যানুয়াল নির্বাচন সমর্থিত</span>
              </span>
              <span className="text-forest-700 font-semibold">
                {currentDistrictData.nameBn} • {selectedUpazila}
              </span>
            </div>

            {/* Role specific input */}
            {role === 'farmer' && (
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  প্রধান প্রধান ফসল
                </label>
                <input
                  type="text"
                  value={primaryCrops}
                  onChange={(e) => setPrimaryCrops(e.target.value)}
                  placeholder="যেমন: ধান, আলু, ভুট্টা"
                  className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base"
                />
              </div>
            )}

            {role === 'owner' && (
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  সেবা প্রদানের আওতা (কিমি)
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={serviceRadiusKm}
                  onChange={(e) => setServiceRadiusKm(Number(e.target.value))}
                  className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base"
                />
              </div>
            )}

            {role === 'buyer' && (
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  ব্যবসা প্রতিষ্ঠানের নাম
                </label>
                <input
                  type="text"
                  value={businessName}
                  onChange={(e) => setBusinessName(e.target.value)}
                  placeholder="যেমন: ভাই ভাই বাণিজ্য ভাণ্ডার"
                  className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base"
                />
              </div>
            )}

            {role === 'expert' && (
              <div>
                <label className="block text-sm font-semibold text-ink-900 mb-1">
                  পদবী ও দপ্তর
                </label>
                <input
                  type="text"
                  value={designation}
                  onChange={(e) => setDesignation(e.target.value)}
                  placeholder="যেমন: উপজেলা কৃষি কর্মকর্তা, ডিএই"
                  className="w-full px-4 min-h-[48px] rounded-btn border border-line-200 text-base"
                />
              </div>
            )}

            {/* Admin Approval Notice Banner */}
            <div className="p-3.5 bg-amber-50/80 border border-amber-200 rounded-xl space-y-1.5 text-xs text-amber-900">
              <div className="flex items-center gap-1.5 font-bold text-amber-800">
                <Lock className="w-4 h-4 shrink-0 text-amber-700" />
                <span>অ্যাকাউন্ট অনুমোদন ও নিরাপত্তা নীতি</span>
              </div>
              <p className="leading-relaxed">
                নিবন্ধন সম্পন্ন হলে আপনি অ্যাকাউন্টে লগইন করতে পারবেন। কৃষকদের নিরাপত্তা নিশ্চিত করতে আপনার প্রদত্ত NID ও প্রোফাইল তথ্য <strong>সর্বোচ্চ ২৪ ঘণ্টার মধ্যে</strong> অ্যাডমিন কর্তৃক পর্যালোচনা ও অনুমোদন করা হবে। অনুমোদনের সাথে সাথে আপনাকে <strong>ইমেইলে নিশ্চিতকরণ বার্তা</strong> পাঠানো হবে এবং প্ল্যাটফর্মের সকল ফিচার স্বয়ংক্রিয়ভাবে সক্রিয় হয়ে যাবে।
              </p>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <Button variant="outline" size="lg" onClick={() => setStep(3)} className="w-1/3">
                <ArrowLeft className="w-4 h-4 mr-1" />
                <span>পেছনে</span>
              </Button>
              <Button type="submit" variant="primary" size="lg" isLoading={isSubmitting} className="w-2/3">
                <span>নিবন্ধন সম্পন্ন করুন</span>
                <CheckCircle2 className="w-5 h-5 ml-1" />
              </Button>
            </div>
          </form>
        )}

        <div className="text-center text-sm text-ink-600 pt-2 border-t border-line-200">
          ইতিমধ্যে অ্যাকাউন্ট আছে?{' '}
          <Link to="/login" className="text-forest-700 font-semibold hover:underline">
            লগ ইন করুন
          </Link>
        </div>
      </Card>
    </div>
  );
};
