import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Sprout,
  Lock,
  Phone,
  Eye,
  EyeOff,
  AlertCircle,
  KeyRound,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  User as UserIcon,
  Mail,
  ArrowLeft,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import {
  isFirebaseConfigured,
  setupRecaptcha,
  cleanupRecaptcha,
  sendFirebasePhoneOtp,
  verifyFirebasePhoneOtp,
  signInWithGoogle,
} from '../lib/firebase';
import { ConfirmationResult } from 'firebase/auth';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    login,
    loginWithFirebase,
    loginWithGoogle,
    requestPasswordReset,
    verifyPasswordResetOtp,
    resetPassword,
  } = useAuth();

  const [authMode, setAuthMode] = useState<'otp' | 'password' | 'forgot-password'>('otp');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const state = location.state as { phone?: string; successMsg?: string } | null;
    if (state?.phone) {
      setPhone(state.phone);
      setAuthMode('password');
    }
    if (state?.successMsg) {
      setSuccessMsg(state.successMsg);
    }
  }, [location.state]);

  // Forgot Password with Email OTP states
  const [forgotStep, setForgotStep] = useState<1 | 2>(1);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotOtp, setForgotOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);

  // Firebase OTP Flow States
  const [confirmationResult, setConfirmationResult] = useState<ConfirmationResult | null>(null);
  const [otpCode, setOtpCode] = useState('');
  const [resendCountdown, setResendCountdown] = useState(0);

  // New user onboarding modal/step if phone not registered
  const [isNewUserStep, setIsNewUserStep] = useState(false);
  const [savedIdToken, setSavedIdToken] = useState<string | null>(null);
  const [newFullName, setNewFullName] = useState('');
  const [newRole, setNewRole] = useState<'farmer' | 'owner' | 'buyer' | 'expert'>('farmer');

  const firebaseReady = isFirebaseConfigured();

  // Timer countdown effect for OTP resend
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (resendCountdown > 0) {
      timer = setTimeout(() => setResendCountdown((prev) => prev - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [resendCountdown]);

  // Clean up reCAPTCHA on unmount
  useEffect(() => {
    return () => {
      cleanupRecaptcha('recaptcha-container');
    };
  }, []);

  // Traditional Password Login
  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!phone || !password) {
      setErrorMsg('মোবাইল নম্বর ও পাসওয়ার্ড প্রদান করুন।');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(phone, password);
      navigate('/app');
    } catch (err: any) {
      setErrorMsg(err.message || 'মোবাইল নম্বর বা পাসওয়ার্ড সঠিক নয়।');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleLogin = async () => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsSubmitting(true);
    try {
      const { idToken, user: gUser } = await signInWithGoogle();
      await loginWithGoogle({
        idToken,
        fullName: gUser?.displayName || undefined,
      });
      navigate('/app');
    } catch (err: any) {
      if (err?.code === 'auth/popup-closed-by-user') {
        return;
      }
      setErrorMsg(err?.message || 'Google দিয়ে লগ ইন সম্পন্ন করা সম্ভব হয়নি।');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRequestForgotOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    const emailTrim = forgotEmail.trim();
    if (!emailTrim || !emailTrim.includes('@')) {
      setErrorMsg('অনুগ্রহ করে একটি সঠিক নিবন্ধিত ইমেইল ঠিকানা দিন।');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await requestPasswordReset(emailTrim);
      setForgotStep(2);
      setSuccessMsg(res.message || 'আপনার ইমেইলে একটি ৬-সংখ্যার ওটিপি কোড পাঠানো হয়েছে।');
    } catch (err: any) {
      setErrorMsg(err?.message || 'ওটিপি পাঠাতে সমস্যা হয়েছে।');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    const emailTrim = forgotEmail.trim();
    const otpTrim = forgotOtp.trim();

    if (!otpTrim || otpTrim.length < 6) {
      setErrorMsg('ইমেইলে আসা ৬-সংখ্যার ওটিপি কোডটি লিখুন।');
      return;
    }
    if (newPassword.length < 10) {
      setErrorMsg('নিরাপত্তার স্বার্থে নতুন পাসওয়ার্ড কমপক্ষে ১০ অক্ষরের হতে হবে।');
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMsg('উভয় পাসওয়ার্ড একই হতে হবে।');
      return;
    }

    setIsSubmitting(true);
    try {
      const { resetToken } = await verifyPasswordResetOtp(emailTrim, otpTrim);
      await resetPassword({
        email: emailTrim,
        resetToken,
        newPassword,
      });
      setSuccessMsg('পাসওয়ার্ড সফলভাবে পরিবর্তন করা হয়েছে! নতুন পাসওয়ার্ড দিয়ে লগ ইন করুন।');
      setAuthMode('password');
      setForgotStep(1);
      setForgotOtp('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setErrorMsg(err?.message || 'পাসওয়ার্ড পরিবর্তন ব্যর্থ হয়েছে। ওটিপি কোড যাচাই করুন।');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatFirebaseError = (err: any): string => {
    const code = err?.code || '';
    const msg = err?.message || '';

    if (code === 'auth/billing-not-enabled' || msg.includes('billing-not-enabled')) {
      return 'আসল সিমে রিয়েল SMS পাঠাতে Firebase Blaze (Billing) প্ল্যান প্রয়োজন। বিনামূল্যে টেস্ট করতে Firebase Console-এ "Phone numbers for testing"-এ এই নম্বরটি যুক্ত করুন (যেমন আগের 01304595440 নম্বরটি করা ছিল)।';
    }
    if (code === 'auth/operation-not-allowed' || msg.includes('auth/operation-not-allowed') || msg.includes('region enabled')) {
      return 'Firebase-এ SMS Region Policy-র কারণে ব্লক হচ্ছে। দয়া করে Firebase Console -> Build -> Authentication -> Settings ট্যাবে গিয়ে "SMS region policy" সেকশনে Bangladesh (+880) এলাউ (Allow) করে Save করুন।';
    }
    if (code === 'auth/unauthorized-domain' || msg.includes('auth/unauthorized-domain')) {
      return 'এই ডোমেনটি Firebase-এ অনুমোদিত নয়। দয়া করে ব্রাউজারে http://localhost:5173 ব্যবহার করুন অথবা Firebase Console -> Authentication -> Settings -> Authorized domains-এ বর্তমান ডোমেন যুক্ত করুন।';
    }
    if (code === 'auth/invalid-phone-number' || msg.includes('auth/invalid-phone-number')) {
      return 'মোবাইল নম্বরের ফরম্যাট সঠিক নয়। যেমন: 017XXXXXXXX লিখুন।';
    }
    if (code === 'auth/too-many-requests' || msg.includes('auth/too-many-requests')) {
      return 'অতিরিক্ত অনুরোধের কারণে এই নম্বরে সাময়িকভাবে ব্লক করা হয়েছে। কিছুক্ষণ পর চেষ্টা করুন অথবা Firebase Console-এ টেস্টিং নম্বর ব্যবহার করুন।';
    }
    if (code === 'auth/quota-exceeded' || msg.includes('auth/quota-exceeded')) {
      return 'এসএমএস কোটা শেষ হয়ে গেছে। Firebase Console-এ "Phone numbers for testing" অংশে টেস্ট নম্বর যোগ করে পরীক্ষা করুন।';
    }
    if (
      code === 'auth/captcha-check-failed' ||
      msg.includes('captcha-check-failed') ||
      msg.includes('already been rendered')
    ) {
      return 'reCAPTCHA যাচাই পুনরায় প্রস্তুত করা হয়েছে। অনুগ্রহ করে আবার "ওটিপি (SMS) পাঠান" বাটনে ক্লিক করুন।';
    }
    if (code === 'auth/invalid-verification-code' || msg.includes('auth/invalid-verification-code')) {
      return 'প্রদত্ত ৬-সংখ্যার ওটিপি কোডটি সঠিক নয়। পুনরায় লিখুন।';
    }
    if (code === 'auth/code-expired' || msg.includes('auth/code-expired')) {
      return 'ওটিপি কোডের মেয়াদ শেষ হয়ে গেছে। পুনরায় ওটিপি পাঠান।';
    }
    return msg || 'ওটিপি পাঠাতে সমস্যা হয়েছে। অনুগ্রহ করে নম্বর পরীক্ষা করে পুনরায় চেষ্টা করুন।';
  };

  // Send Firebase Phone OTP
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!phone || phone.length < 10) {
      setErrorMsg('সঠিক ১১ ডিজিটের মোবাইল নম্বর দিন (যেমন: 017XXXXXXXX)।');
      return;
    }

    if (!firebaseReady) {
      setErrorMsg('Firebase কনফিগারেশন সেটআপ করা নেই। .env ফাইলে কী যুক্ত করুন অথবা পাসওয়ার্ড দিয়ে লগ ইন করুন।');
      return;
    }

    setIsSubmitting(true);
    try {
      const verifier = setupRecaptcha('recaptcha-container');

      const confirmation = await sendFirebasePhoneOtp(phone, verifier);
      setConfirmationResult(confirmation);
      setResendCountdown(60);
      setSuccessMsg('আপনার মোবাইলে ৬-সংখ্যার এসএমএস কোড পাঠানো হয়েছে!');
    } catch (err: any) {
      cleanupRecaptcha('recaptcha-container');
      setErrorMsg(formatFirebaseError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Verify Firebase Phone OTP
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!confirmationResult || !otpCode || otpCode.length < 6) {
      setErrorMsg('আপনার মোবাইলে আসা ৬-সংখ্যার ওটিপি কোডটি লিখুন।');
      return;
    }

    setIsSubmitting(true);
    try {
      const idToken = await verifyFirebasePhoneOtp(confirmationResult, otpCode);
      const res = await loginWithFirebase({ idToken });

      if (res.isNewUser) {
        // User phone verified but needs to set Full Name and Role
        setSavedIdToken(idToken);
        setIsNewUserStep(true);
        setSuccessMsg('ফোন নম্বর সফলভাবে যাচাই হয়েছে! এবার আপনার নাম ও ভূমিকা প্রদান করুন।');
      } else {
        navigate('/app');
      }
    } catch (err: any) {
      setErrorMsg(formatFirebaseError(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Complete Registration for verified new user
  const handleCompleteNewUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!savedIdToken || !newFullName.trim()) {
      setErrorMsg('অনুগ্রহ করে আপনার পুরো নাম লিখুন।');
      return;
    }

    setIsSubmitting(true);
    try {
      await loginWithFirebase({
        idToken: savedIdToken,
        fullName: newFullName.trim(),
        role: newRole,
      });
      navigate('/app');
    } catch (err: any) {
      setErrorMsg(err?.message || 'অ্যাকাউন্ট তৈরি সম্পন্ন করা যায়নি।');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-[75vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* Invisible reCAPTCHA container required by Firebase */}
      <div id="recaptcha-container"></div>

      <Card className="max-w-md w-full p-6 sm:p-8 border-line-200 shadow-soft space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center mx-auto">
            <Sprout className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold text-forest-900">
            {authMode === 'forgot-password' ? 'পাসওয়ার্ড রিসেট করুন' : 'লগ ইন করুন'}
          </h1>
          <p className="text-sm text-ink-600">
            {authMode === 'forgot-password'
              ? 'ইমেইল ওটিপি দিয়ে নিরাপদে পাসওয়ার্ড পরিবর্তন করুন'
              : authMode === 'otp'
              ? 'মোবাইল নম্বরে ওটিপি কোড দিয়ে তাৎক্ষণিক প্রবেশ করুন'
              : 'আপনার মোবাইল নম্বর ও পাসওয়ার্ড দিয়ে প্রবেশ করুন'}
          </p>
        </div>

        {/* Google Sign-In & Tab Selector */}
        {!isNewUserStep && authMode !== 'forgot-password' && (
          <div className="space-y-3">
            <button
              type="button"
              onClick={handleGoogleLogin}
              disabled={isSubmitting}
              className="w-full min-h-[48px] px-4 rounded-btn border border-line-200 bg-white hover:bg-slate-50 text-ink-900 font-semibold flex items-center justify-center gap-3 transition-colors shadow-xs"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              <span>Google দিয়ে সরাসরি লগ ইন</span>
            </button>

            <div className="relative py-1">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-line-200" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="bg-canvas px-3 text-ink-600 font-medium">অথবা অন্যান্য মাধ্যমে</span>
              </div>
            </div>

            <div className="flex rounded-xl bg-slate-100 p-1 border border-slate-200 text-xs font-semibold">
              <button
                type="button"
                onClick={() => {
                  setAuthMode('otp');
                  setErrorMsg(null);
                }}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                  authMode === 'otp'
                    ? 'bg-white text-forest-800 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <ShieldCheck className="w-4 h-4 text-forest-700" />
                মোবাইল ওটিপি (SMS)
              </button>
              <button
                type="button"
                onClick={() => {
                  setAuthMode('password');
                  cleanupRecaptcha('recaptcha-container');
                  setErrorMsg(null);
                }}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
                  authMode === 'password'
                    ? 'bg-white text-forest-800 shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <KeyRound className="w-4 h-4 text-forest-700" />
                পাসওয়ার্ড দিয়ে লগইন
              </button>
            </div>
          </div>
        )}

        {/* Status Alerts */}
        {errorMsg && (
          <div className="p-3.5 bg-danger-600/10 border border-danger-600/20 text-danger-600 rounded-btn text-sm flex items-center gap-2.5">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-btn text-sm flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Firebase Warning if Not Configured */}
        {authMode === 'otp' && !firebaseReady && !isNewUserStep && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs space-y-1">
            <p className="font-semibold flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              Firebase সক্রিয়করণ প্রয়োজন
            </p>
            <p className="text-[11px] text-amber-700 leading-relaxed">
              Firebase কনফিগারেশন কী <code>.env</code> ফাইলে যুক্ত করুন অথবা উপরের "পাসওয়ার্ড দিয়ে লগইন" ট্যাবটি বেছে নিন।
            </p>
          </div>
        )}

        {/* ----------------- MODE A: Firebase Phone OTP Flow ----------------- */}
        {authMode === 'otp' && !isNewUserStep && (
          <div>
            {!confirmationResult ? (
              // Step 1: Request SMS OTP
              <form onSubmit={handleSendOtp} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                    মোবাইল নম্বর <span className="text-danger-600">*</span>
                  </label>
                  <div className="relative">
                    <Phone className="w-5 h-5 text-ink-600 absolute left-3.5 top-3.5" />
                    <input
                      type="tel"
                      required
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="০১৭১১-XXXXXX"
                      className="w-full pl-11 pr-4 min-h-[48px] rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                    />
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Google Firebase-এর মাধ্যমে নিরাপদ SMS কোড পাঠানো হবে
                  </span>
                </div>

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  fullWidth
                  isLoading={isSubmitting}
                  disabled={!firebaseReady || isSubmitting}
                >
                  ওটিপি (SMS) পাঠান
                </Button>
              </form>
            ) : (
              // Step 2: Confirm 6-digit OTP
              <form onSubmit={handleVerifyOtp} className="space-y-4 animate-fade-in">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-sm font-semibold text-ink-900">
                      ৬-সংখ্যার এসএমএস ওটিপি কোড <span className="text-danger-600">*</span>
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        cleanupRecaptcha('recaptcha-container');
                        setConfirmationResult(null);
                        setOtpCode('');
                      }}
                      className="text-xs text-forest-700 hover:underline"
                    >
                      নম্বর পরিবর্তন
                    </button>
                  </div>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="123456"
                    className="w-full px-4 min-h-[48px] text-center text-2xl font-mono tracking-widest rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                  />
                  <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                    <span>এসএমএস না পেলে অপেক্ষা করুন</span>
                    {resendCountdown > 0 ? (
                      <span className="text-forest-700 font-semibold">{resendCountdown} সেকেন্ড</span>
                    ) : (
                      <button
                        type="button"
                        onClick={handleSendOtp}
                        className="text-forest-700 font-semibold hover:underline flex items-center gap-1"
                      >
                        <RefreshCw className="w-3 h-3" /> পুনরায় পাঠান
                      </button>
                    )}
                  </div>
                </div>

                <Button type="submit" variant="primary" size="lg" fullWidth isLoading={isSubmitting}>
                  ওটিপি যাচাই ও লগ ইন করুন
                </Button>
              </form>
            )}
          </div>
        )}

        {/* ----------------- New Verified User Profile Step ----------------- */}
        {isNewUserStep && (
          <form onSubmit={handleCompleteNewUser} className="space-y-4 animate-fade-in">
            <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-xs text-emerald-800">
              <strong className="block font-bold mb-0.5">নতুন অ্যাকাউন্ট তৈরি</strong>
              আপনার মোবাইল নম্বরটি গুগল দ্বারা যাচাইকৃত হয়েছে। অনুগ্রহ করে আপনার নাম ও পেশা নির্বাচন করে শুরু করুন।
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                আপনার পুরো নাম <span className="text-danger-600">*</span>
              </label>
              <div className="relative">
                <UserIcon className="w-5 h-5 text-ink-600 absolute left-3.5 top-3.5" />
                <input
                  type="text"
                  required
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  placeholder="যেমন: মোঃ রফিকুল ইসলাম"
                  className="w-full pl-11 pr-4 min-h-[48px] rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                আপনার ভূমিকা / পেশা <span className="text-danger-600">*</span>
              </label>
              <select
                value={newRole}
                onChange={(e: any) => setNewRole(e.target.value)}
                className="w-full px-3.5 min-h-[48px] rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-sm bg-white"
              >
                <option value="farmer">কৃষক (ফসল সমস্যা ও যন্ত্রপাতি ভাড়া নিতে)</option>
                <option value="owner">যন্ত্রপাতির মালিক (ভাড়া দিতে)</option>
                <option value="buyer">পাইকার / ক্রেতা (ফসল ক্রয় করতে)</option>
                <option value="expert">কৃষি বিশেষজ্ঞ / অফিসার</option>
              </select>
            </div>

            <Button type="submit" variant="primary" size="lg" fullWidth isLoading={isSubmitting}>
              নিবন্ধন সম্পন্ন করুন
            </Button>
          </form>
        )}

        {/* ----------------- MODE B: Traditional Password Login ----------------- */}
        {authMode === 'password' && (
          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                মোবাইল নম্বর <span className="text-danger-600">*</span>
              </label>
              <div className="relative">
                <Phone className="w-5 h-5 text-ink-600 absolute left-3.5 top-3.5" />
                <input
                  type="tel"
                  required
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="০১৭১১-XXXXXX"
                  className="w-full pl-11 pr-4 min-h-[48px] rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                পাসওয়ার্ড <span className="text-danger-600">*</span>
              </label>
              <div className="relative">
                <Lock className="w-5 h-5 text-ink-600 absolute left-3.5 top-3.5" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-11 pr-12 min-h-[48px] rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3.5 text-ink-600 hover:text-forest-700 p-0.5"
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => {
                  setAuthMode('forgot-password');
                  setForgotStep(1);
                  setErrorMsg(null);
                  setSuccessMsg(null);
                }}
                className="text-xs text-forest-700 font-semibold hover:underline"
              >
                পাসওয়ার্ড ভুলে গেছেন?
              </button>
            </div>

            <Button type="submit" variant="primary" size="lg" fullWidth isLoading={isSubmitting}>
              লগ ইন করুন
            </Button>
          </form>
        )}

        {/* ----------------- MODE C: Email OTP Forgot Password Flow ----------------- */}
        {authMode === 'forgot-password' && (
          <div className="space-y-4 animate-fade-in">
            <div className="flex items-center justify-between pb-2 border-b border-line-200">
              <div className="text-xs font-semibold text-ink-600 flex items-center gap-1.5">
                <span className="w-5 h-5 rounded-full bg-forest-100 text-forest-800 flex items-center justify-center font-bold text-[11px]">
                  {forgotStep === 1 ? '১' : '২'}
                </span>
                <span>{forgotStep === 1 ? 'ইমেইল যাচাইকরণ' : 'নতুন পাসওয়ার্ড প্রদান'}</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setAuthMode('password');
                  setErrorMsg(null);
                  setSuccessMsg(null);
                  setForgotStep(1);
                }}
                className="text-xs text-forest-700 font-semibold hover:underline flex items-center gap-1"
              >
                <ArrowLeft className="w-3.5 h-3.5" /> লগইনে ফিরে যান
              </button>
            </div>

            {forgotStep === 1 ? (
              // Step 1: Request 6-digit Email OTP
              <form onSubmit={handleRequestForgotOtp} className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                    আপনার নিবন্ধিত ইমেইল <span className="text-danger-600">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="w-5 h-5 text-ink-600 absolute left-3.5 top-3.5" />
                    <input
                      type="email"
                      required
                      value={forgotEmail}
                      onChange={(e) => setForgotEmail(e.target.value)}
                      placeholder="example@mail.com"
                      className="w-full pl-11 pr-4 min-h-[48px] rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                    />
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    পাসওয়ার্ড পরিবর্তনের জন্য এই ইমেইলে একটি ৬-সংখ্যার ওটিপি কোড পাঠানো হবে
                  </span>
                </div>

                <Button type="submit" variant="primary" size="lg" fullWidth isLoading={isSubmitting}>
                  ইমেইল ওটিপি পাঠান
                </Button>
              </form>
            ) : (
              // Step 2: Enter OTP & Set New Password
              <form onSubmit={handleResetPassword} className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-sm font-semibold text-ink-900">
                      ৬-সংখ্যার ইমেইল ওটিপি <span className="text-danger-600">*</span>
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setForgotStep(1);
                        setForgotOtp('');
                        setErrorMsg(null);
                      }}
                      className="text-xs text-forest-700 hover:underline"
                    >
                      ইমেইল পরিবর্তন
                    </button>
                  </div>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={forgotOtp}
                    onChange={(e) => setForgotOtp(e.target.value.replace(/\D/g, ''))}
                    placeholder="123456"
                    className="w-full px-4 min-h-[48px] text-center text-2xl font-mono tracking-widest rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700"
                  />
                  <div className="flex justify-end mt-1">
                    <button
                      type="button"
                      onClick={handleRequestForgotOtp}
                      disabled={isSubmitting}
                      className="text-xs text-forest-700 hover:underline flex items-center gap-1"
                    >
                      <RefreshCw className="w-3 h-3" /> পুনরায় ওটিপি পাঠান
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                    নতুন পাসওয়ার্ড <span className="text-danger-600">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="w-5 h-5 text-ink-600 absolute left-3.5 top-3.5" />
                    <input
                      type={showNewPassword ? 'text' : 'password'}
                      required
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="কমপক্ষে ১০ অক্ষরের পাসওয়ার্ড"
                      className="w-full pl-11 pr-12 min-h-[48px] rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3.5 top-3.5 text-ink-600 hover:text-forest-700 p-0.5"
                    >
                      {showNewPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    নিরাপত্তা নীতি অনুযায়ী কমপক্ষে ১০ অক্ষরের পাসওয়ার্ড আবশ্যক
                  </span>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-ink-900 mb-1.5">
                    নতুন পাসওয়ার্ড নিশ্চিত করুন <span className="text-danger-600">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="w-5 h-5 text-ink-600 absolute left-3.5 top-3.5" />
                    <input
                      type={showNewPassword ? 'text' : 'password'}
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="পুনরায় পাসওয়ার্ড লিখুন"
                      className="w-full pl-11 pr-4 min-h-[48px] rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                    />
                  </div>
                </div>

                <Button type="submit" variant="primary" size="lg" fullWidth isLoading={isSubmitting}>
                  পাসওয়ার্ড পরিবর্তন ও সংরক্ষণ
                </Button>
              </form>
            )}
          </div>
        )}

        <div className="text-center text-sm text-ink-600 pt-3 border-t border-line-200">
          নতুন অ্যাকাউন্ট খুলতে চান?{' '}
          <Link to="/signup" className="text-forest-700 font-semibold hover:underline">
            বিনামূল্যে সাইন আপ করুন
          </Link>
        </div>
      </Card>
    </div>
  );
};
