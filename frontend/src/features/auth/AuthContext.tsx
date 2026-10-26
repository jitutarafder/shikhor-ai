import React, { createContext, useContext, useState, useEffect } from 'react';
import { offlineDb } from '../offline/db';

export interface User {
  id: string;
  phone: string;
  email?: string | null;
  nid?: string | null;
  dob?: string | null;
  nidFrontImage?: string | null;
  nidBackImage?: string | null;
  isNidVerified: boolean;
  nidVerificationStatus: string;
  nidRejectionReason?: string | null;
  fullName: string;
  role: 'farmer' | 'owner' | 'buyer' | 'expert' | 'moderator' | 'admin';
  isActive: boolean;
  isVerified: boolean;
  isEmailVerified?: boolean;
  hasProfile: boolean;
}

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (phone: string, password: string) => Promise<void>;
  loginWithFirebase: (payload: {
    idToken: string;
    fullName?: string;
    role?: string;
    nid?: string;
  }) => Promise<{ isNewUser: boolean; phone?: string }>;
  loginWithGoogle: (payload: {
    idToken: string;
    fullName?: string;
    role?: string;
    phone?: string;
    nid?: string;
  }) => Promise<void>;
  register: (data: {
    phone: string;
    password: string;
    full_name: string;
    role: string;
    email: string;
    emailVerificationToken?: string;
    nid?: string;
    dob?: string;
    nidFrontImage?: string;
    nidBackImage?: string;
    district?: string;
    upazila?: string;
    primaryCrops?: string;
    serviceRadiusKm?: number;
    businessName?: string;
    designation?: string;
    organization?: string;
  }) => Promise<void>;
  resubmitNid: (data: {
    nid?: string;
    dob?: string;
    nidFrontImage: string;
    nidBackImage: string;
    fullName?: string;
    phone?: string;
    role?: string;
    district?: string;
    upazila?: string;
  }) => Promise<void>;
  uploadNidImage: (file: File) => Promise<string>;
  sendSignupEmailOtp: (email: string) => Promise<{ message: string; email: string; emailDispatched?: boolean; devOtp?: string }>;
  verifySignupEmailOtp: (email: string, otp: string) => Promise<{ verified: boolean; email: string; verificationToken: string }>;
  requestPasswordReset: (email: string) => Promise<{ message: string }>;
  verifyPasswordResetOtp: (email: string, otp: string) => Promise<{ resetToken: string }>;
  resetPassword: (payload: { email: string; resetToken: string; newPassword: string }) => Promise<void>;
  completeOnboarding: (data: {
    district: string;
    upazila?: string;
    primaryCrops?: string;
    serviceRadiusKm?: number;
    businessName?: string;
    designation?: string;
    organization?: string;
  }) => Promise<void>;
  refreshCurrentUser: () => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem('shikhor_access_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Fetch current user details when access token is present
  const fetchCurrentUser = async (accessToken: string) => {
    try {
      const res = await fetch('/api/v1/auth/me', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (res.ok) {
        const userData: User = await res.json();
        setUser(userData);
      } else {
        // Token invalid or expired, clear session
        sessionStorage.removeItem('shikhor_access_token');
        sessionStorage.removeItem('shikhor_refresh_token');
        setToken(null);
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshCurrentUser = async () => {
    const currentToken = token || sessionStorage.getItem('shikhor_access_token');
    if (currentToken) {
      await fetchCurrentUser(currentToken);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCurrentUser(token);
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const saveTokens = (tokens: AuthTokens) => {
    setToken(tokens.accessToken);
    sessionStorage.setItem('shikhor_access_token', tokens.accessToken);
    sessionStorage.setItem('shikhor_refresh_token', tokens.refreshToken);
    localStorage.setItem('shikhor_token', tokens.accessToken);
  };

  const login = async (phone: string, password: string) => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, password }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'লগইন ব্যর্থ হয়েছে।');
    }

    saveTokens(data);
    await fetchCurrentUser(data.accessToken);
  };

  const loginWithFirebase = async (payload: {
    idToken: string;
    fullName?: string;
    role?: string;
    nid?: string;
  }): Promise<{ isNewUser: boolean; phone?: string }> => {
    const res = await fetch('/api/v1/auth/firebase-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'Firebase ওটিপি যাচাইকরণ ব্যর্থ হয়েছে।');
    }

    if (data.tokens && data.tokens.accessToken) {
      saveTokens(data.tokens);
      await fetchCurrentUser(data.tokens.accessToken);
    }

    return {
      isNewUser: Boolean(data.isNewUser),
      phone: data.phone,
    };
  };

  const loginWithGoogle = async (payload: {
    idToken: string;
    fullName?: string;
    role?: string;
    phone?: string;
    nid?: string;
  }): Promise<void> => {
    const res = await fetch('/api/v1/auth/google-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'Google দিয়ে লগ ইন ব্যর্থ হয়েছে।');
    }

    saveTokens(data);
    await fetchCurrentUser(data.accessToken);
  };

  const register = async (payload: {
    phone: string;
    password: string;
    full_name: string;
    role: string;
    email: string;
    emailVerificationToken?: string;
    nid?: string;
    dob?: string;
    nidFrontImage?: string;
    nidBackImage?: string;
    district?: string;
    upazila?: string;
    primaryCrops?: string;
    serviceRadiusKm?: number;
    businessName?: string;
    designation?: string;
    organization?: string;
  }) => {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        email_verification_token: payload.emailVerificationToken,
        nid_front_image: payload.nidFrontImage,
        nid_back_image: payload.nidBackImage,
        primary_crops: payload.primaryCrops,
        service_radius_km: payload.serviceRadiusKm,
        business_name: payload.businessName,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'নিবন্ধন ব্যর্থ হয়েছে।');
    }

    // Do not establish active session upon registration — user must explicitly log in
    sessionStorage.removeItem('shikhor_access_token');
    localStorage.removeItem('shikhor_token');
    setUser(null);
    setToken(null);
  };

  const uploadNidImage = async (file: File): Promise<string> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/v1/auth/upload-nid-image', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'ছবি আপলোড ব্যর্থ হয়েছে।');
    }
    return data.fileUrl;
  };

  const resubmitNid = async (data: {
    nid?: string;
    dob?: string;
    nidFrontImage: string;
    nidBackImage: string;
    fullName?: string;
    phone?: string;
    role?: string;
    district?: string;
    upazila?: string;
  }): Promise<void> => {
    const currentToken = token || sessionStorage.getItem('shikhor_access_token');
    if (!currentToken) throw new Error('অনুগ্রহ করে পুনরায় লগইন করুন।');

    const res = await fetch('/api/v1/auth/resubmit-nid', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${currentToken}`,
      },
      body: JSON.stringify({
        nid: data.nid || undefined,
        dob: data.dob || undefined,
        nidFrontImage: data.nidFrontImage,
        nidBackImage: data.nidBackImage,
        fullName: data.fullName || undefined,
        phone: data.phone || undefined,
        role: data.role || undefined,
        district: data.district || undefined,
        upazila: data.upazila || undefined,
      }),
    });

    const resJson = await res.json();
    if (!res.ok) {
      throw new Error(resJson?.error?.message || 'এনআইডি পুনরায় জমা দেওয়া সম্ভব হয়নি।');
    }

    setUser(resJson);
  };

  const sendSignupEmailOtp = async (email: string): Promise<{ message: string; email: string }> => {
    const res = await fetch('/api/v1/auth/signup/send-email-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.trim() }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'ইমেইল ওটিপি পাঠানো সম্ভব হয়নি।');
    }
    return data;
  };

  const verifySignupEmailOtp = async (
    email: string,
    otp: string
  ): Promise<{ verified: boolean; email: string; verificationToken: string }> => {
    const res = await fetch('/api/v1/auth/signup/verify-email-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.trim(), otp: otp.trim() }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'ভুল বা মেয়াদোত্তীর্ণ ওটিপি কোড।');
    }
    return data;
  };

  const requestPasswordReset = async (email: string): Promise<{ message: string }> => {
    const res = await fetch('/api/v1/auth/forgot-password/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'পাসওয়ার্ড রিসেট ওটিপি পাঠাতে সমস্যা হয়েছে।');
    }
    return data;
  };

  const verifyPasswordResetOtp = async (email: string, otp: string): Promise<{ resetToken: string }> => {
    const res = await fetch('/api/v1/auth/forgot-password/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, otp }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'ওটিপি কোড সঠিক নয় অথবা মেয়াদোত্তীর্ণ।');
    }
    return data;
  };

  const resetPassword = async (payload: { email: string; resetToken: string; newPassword: string }): Promise<void> => {
    const res = await fetch('/api/v1/auth/forgot-password/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'পাসওয়ার্ড পরিবর্তন ব্যর্থ হয়েছে।');
    }
  };

  const completeOnboarding = async (payload: {
    district: string;
    upazila?: string;
    primaryCrops?: string;
    serviceRadiusKm?: number;
    businessName?: string;
    designation?: string;
    organization?: string;
  }) => {
    if (!token) throw new Error('Not authenticated');

    const res = await fetch('/api/v1/auth/onboarding', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data?.error?.message || 'প্রোফাইল সংরক্ষণ ব্যর্থ হয়েছে।');
    }

    setUser(data);
  };

  const logout = async () => {
    const refreshToken = sessionStorage.getItem('shikhor_refresh_token');
    if (refreshToken) {
      try {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refreshToken }),
        });
      } catch {
        // Continue clearing client storage regardless
      }
    }
    if (user?.id) {
      await offlineDb.clearAccountData(user.id);
    }
    sessionStorage.removeItem('shikhor_access_token');
    sessionStorage.removeItem('shikhor_refresh_token');
    localStorage.removeItem('shikhor_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        loginWithFirebase,
        loginWithGoogle,
        register,
        resubmitNid,
        uploadNidImage,
        sendSignupEmailOtp,
        verifySignupEmailOtp,
        requestPasswordReset,
        verifyPasswordResetOtp,
        resetPassword,
        completeOnboarding,
        refreshCurrentUser,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
