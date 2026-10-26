/**
 * Firebase Client SDK setup for Phone & Google Authentication.
 * 
 * Strictly complies with:
 * - AGENTS.md Rule 4: No hardcoded secrets. Reads strictly from VITE_FIREBASE_* env variables.
 * - Handles phone normalization, reCAPTCHA verifier initialization, SMS OTP dispatch, and confirmation.
 */

import { initializeApp, getApps, getApp, FirebaseApp } from 'firebase/app';
import {
  getAuth,
  RecaptchaVerifier,
  signInWithPhoneNumber,
  ConfirmationResult,
  Auth,
  GoogleAuthProvider,
  signInWithPopup,
  UserCredential,
  User,
} from 'firebase/auth';
import { env } from './env';

declare global {
  interface Window {
    recaptchaVerifier?: RecaptchaVerifier | null;
  }
}

const firebaseConfig = {
  apiKey: env.VITE_FIREBASE_API_KEY || '',
  authDomain: env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: env.VITE_FIREBASE_PROJECT_ID || '',
  storageBucket: env.VITE_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: env.VITE_FIREBASE_APP_ID || '',
};

export function isFirebaseConfigured(): boolean {
  return Boolean(
    firebaseConfig.apiKey &&
    firebaseConfig.projectId &&
    firebaseConfig.apiKey.trim().length > 5
  );
}

let firebaseApp: FirebaseApp | null = null;
let firebaseAuth: Auth | null = null;

export function getFirebaseAuth(): Auth | null {
  if (!isFirebaseConfigured()) {
    return null;
  }
  if (!firebaseApp) {
    firebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);
    firebaseAuth = getAuth(firebaseApp);
    firebaseAuth.useDeviceLanguage();
  }
  return firebaseAuth;
}

/**
 * Formats a Bangladeshi mobile number to international E.164 (+8801XXXXXXXXX) format.
 */
export function formatToE164(phone: string): string {
  const cleaned = phone.replace(/[\s\-()]/g, '');
  if (cleaned.startsWith('+880')) {
    return cleaned;
  }
  if (cleaned.startsWith('880')) {
    return `+${cleaned}`;
  }
  if (cleaned.startsWith('01')) {
    return `+88${cleaned}`;
  }
  return `+880${cleaned}`;
}

/**
 * Cleans up existing RecaptchaVerifier instance and resets the DOM container.
 */
export function cleanupRecaptcha(containerId: string = 'recaptcha-container'): void {
  if (window.recaptchaVerifier) {
    try {
      window.recaptchaVerifier.clear();
    } catch {
      // ignore
    }
    window.recaptchaVerifier = null;
  }
  const container = document.getElementById(containerId);
  if (container) {
    container.innerHTML = '';
  }
}

/**
 * Prepares an invisible RecaptchaVerifier on the specified container DOM element.
 * Reuses existing instance if already created and element is clean, avoiding:
 * "Error: reCAPTCHA has already been rendered in this element".
 */
export function setupRecaptcha(containerId: string = 'recaptcha-container'): RecaptchaVerifier {
  const auth = getFirebaseAuth();
  if (!auth) {
    throw new Error('Firebase কনফিগারেশন অনুপস্থিত। অনুগ্রহ করে .env ফাইলে Firebase কী যুক্ত করুন।');
  }

  // If a valid verifier already exists on window and the container still exists, reuse it!
  const existing = window.recaptchaVerifier;
  const container = document.getElementById(containerId);

  if (existing && container && container.children.length > 0) {
    return existing;
  }

  // Otherwise, ensure clean DOM and clear state before creating a new verifier
  cleanupRecaptcha(containerId);

  const verifier = new RecaptchaVerifier(auth, containerId, {
    size: 'invisible',
    callback: () => {
      // reCAPTCHA solved
    },
    'expired-callback': () => {
      // reCAPTCHA expired, prompt user to retry
      cleanupRecaptcha(containerId);
    },
  });

  window.recaptchaVerifier = verifier;
  return verifier;
}

/**
 * Dispatches an SMS verification code to the target phone number via Firebase.
 */
export async function sendFirebasePhoneOtp(
  rawPhone: string,
  verifier: RecaptchaVerifier
): Promise<ConfirmationResult> {
  const auth = getFirebaseAuth();
  if (!auth) {
    throw new Error('Firebase কনফিগারেশন সেটআপ করা নেই।');
  }

  const formattedPhone = formatToE164(rawPhone);
  return await signInWithPhoneNumber(auth, formattedPhone, verifier);
}

/**
 * Confirms user OTP code and returns Google Firebase ID Token for backend authentication.
 */
export async function verifyFirebasePhoneOtp(
  confirmationResult: ConfirmationResult,
  otpCode: string
): Promise<string> {
  const userCredential = await confirmationResult.confirm(otpCode);
  const idToken = await userCredential.user.getIdToken();
  return idToken;
}

/**
 * Triggers Google Sign-in popup and returns Firebase ID Token, along with user details.
 */
export async function signInWithGoogle(): Promise<{ idToken: string; user: User }> {
  const auth = getFirebaseAuth();
  if (!auth) {
    throw new Error('Firebase কনফিগারেশন সেটআপ করা নেই। .env ফাইলে কী যুক্ত করুন।');
  }
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: 'select_account' });
  const result: UserCredential = await signInWithPopup(auth, provider);
  const idToken = await result.user.getIdToken();
  return { idToken, user: result.user };
}
