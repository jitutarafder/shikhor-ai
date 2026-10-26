import React, { useState } from 'react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import {
  ShieldCheck,
  Lock,
  EyeOff,
  Download,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  FileText,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';

export const PrivacyPolicy: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const token = localStorage.getItem('shikhor_token');

  const [exporting, setExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteSuccess, setDeleteSuccess] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const handleExportData = async () => {
    if (!token) return;
    setExporting(true);
    setActionError(null);
    try {
      const res = await fetch('/api/v1/users/me/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) throw new Error('ডাটা এক্সপোর্ট সংগ্রহ করা যায়নি।');
      const data = await res.json();

      // Trigger client-side download
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `shikhor-ai-data-archive-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 4000);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'ত্রুটি ঘটেছে।');
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!token) return;
    const confirmed = window.confirm(
      'আপনি কি নিশ্চিত যে আপনি আপনার অ্যাকাউন্ট ও ব্যক্তিগত তথ্য স্থায়ীভাবে মুছে ফেলতে চান? এই সিদ্ধান্ত অপরিবর্তনীয়।'
    );
    if (!confirmed) return;

    setDeleting(true);
    setActionError(null);
    try {
      const res = await fetch('/api/v1/users/me', {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) throw new Error('অ্যাকাউন্ট মুছে ফেলা সম্ভব হয়নি।');
      setDeleteSuccess(true);
      setTimeout(() => {
        localStorage.removeItem('shikhor_token');
        localStorage.removeItem('shikhor_refresh');
        window.location.href = '/';
      }, 2500);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'ত্রুটি ঘটেছে।');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex p-3 rounded-2xl bg-emerald-50 text-forest-800 border border-emerald-200">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-forest-900">
          গোপনীয়তা ও ডাটা সুরক্ষা নীতি
        </h1>
        <p className="text-sm text-ink-600 max-w-xl mx-auto">
          শিখড় এআই কৃষকের তথ্য সুরক্ষা, নির্ভুলতা এবং গোপনীয়তাকে সর্বোচ্চ অগ্রাধিকার দেয়।
        </p>
      </div>

      {/* Action Notices */}
      {actionError && (
        <div className="p-4 rounded-xl bg-danger-50 border border-danger-200 text-danger-700 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}
      {exportSuccess && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>আপনার ব্যক্তিগত ডাটা আর্কাইভ সফলভাবে ডাউনলোড হয়েছে।</span>
        </div>
      )}
      {deleteSuccess && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>আপনার অ্যাকাউন্ট সফলভাবে মুছে ফেলা হয়েছে। হোমপেজে পুনঃনির্দেশ করা হচ্ছে...</span>
        </div>
      )}

      {/* Main Policy Cards */}
      <div className="space-y-6 text-sm text-ink-800 leading-relaxed">
        <Card className="p-6 space-y-4 border-line-200 bg-canvas">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <Lock className="w-5 h-5 text-forest-700" />
            <h2>১. আমরা কী তথ্য সংগ্রহ করি</h2>
          </div>
          <ul className="list-disc list-inside space-y-1.5 text-ink-700 text-xs sm:text-sm">
            <li><strong>প্রোফাইল তথ্য:</strong> মোবাইল নম্বর, পুরো নাম এবং সাধারণ ভূমিকা (কৃষক, যন্ত্রের মালিক, ফসল ক্রেতা)।</li>
            <li><strong>ভৌগোলিক অবস্থান:</strong> আনুমানিক জেলা ও উপজেলা নির্বাচন। আমরা কখনই কৃষকের বাড়ির সুনির্দিষ্ট অক্ষাংশ/দ্রাঘিমাংশ পাবলিক প্ল্যাটফর্মে প্রকাশ করি না (Rule 17)।</li>
            <li><strong>ফসলের ছবি ও লক্ষণ:</strong> এআই রোগ নির্ণয়ের জন্য আপলোড করা ফসলের পাতার ছবি ও লক্ষণ। আপলোডের সময় যেকোনো ক্যামেরার লুকানো EXIF/GPS তথ্য স্বয়ংক্রিয়ভাবে মুছে ফেলা হয় (Rule 18)।</li>
          </ul>
        </Card>

        <Card className="p-6 space-y-4 border-line-200 bg-canvas">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <EyeOff className="w-5 h-5 text-emerald-700" />
            <h2>২. ফসলের ছবি ও গোপনীয়তা সংরক্ষণ</h2>
          </div>
          <p className="text-xs sm:text-sm text-ink-700">
            আপলোডকৃত ছবিগুলো সুরক্ষিত ব্যক্তিগত স্টোরেজে সংরক্ষিত থাকে এবং জনসাধারণের জন্য সরাসরি উন্মুক্ত নয়। ফসল রোগ নির্ণয়ের মডেল কেবল পাতায় রোগের দৃশ্যমান প্যাটার্ন বিশ্লেষণ করে এবং কোনো ব্যক্তিগত ডাটা মডেলের বাহ্যিক প্রশিক্ষণে বিক্রি করা হয় না।
          </p>
        </Card>

        <Card className="p-6 space-y-4 border-line-200 bg-canvas">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h2>৩. এআই পরামর্শের দায়মুক্তি ও সীমাবদ্ধতা</h2>
          </div>
          <p className="text-xs sm:text-sm text-ink-700">
            শিখড় এআই একটি সিদ্ধান্ত সহায়তা প্রযুক্তি। এটি কোনো নিশ্চিত চিকিৎসা বা সরকারি কৃষি কর্মকর্তার প্রত্যক্ষ বিকল্প নয়। কোনো উচ্চমাত্রার রাসায়নিক কীটনাশক নিজের ইচ্ছামতো প্রয়োগ না করে স্থানীয় উপসহকারী কৃষি কর্মকর্তা (SAAO) এর পরামর্শ গ্রহণ আবশ্যক।
          </p>
        </Card>

        {/* User Data Rights Section (GDPR & Data Protection) */}
        <Card className="p-6 space-y-4 border-forest-200 bg-field-wash">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <FileText className="w-5 h-5 text-forest-800" />
            <h2>৪. আপনার ডাটা অধিকার (Data Subject Rights)</h2>
          </div>
          <p className="text-xs sm:text-sm text-ink-700">
            আইন ও সুরক্ষার আন্তর্জাতিক মানদণ্ড অনুযায়ী আপনি যেকোনো সময় আপনার পুরো ডাটা ডাউনলোড করতে পারেন অথবা আপনার অ্যাকাউন্ট সম্পূর্ণ মুছে ফেলতে পারেন।
          </p>

          {isAuthenticated ? (
            <div className="pt-2 flex flex-col sm:flex-row gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportData}
                disabled={exporting}
                className="text-xs border-forest-600 text-forest-900 hover:bg-emerald-50"
              >
                <Download className="w-4 h-4 mr-1.5 text-forest-700" />
                {exporting ? 'ডাউনলোড প্রস্তুত হচ্ছে...' : 'আমার সমস্ত ডাটা এক্সপোর্ট করুন (JSON)'}
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleDeleteAccount}
                disabled={deleting}
                className="text-xs"
              >
                <Trash2 className="w-4 h-4 mr-1.5" />
                {deleting ? 'মুছে ফেলা হচ্ছে...' : 'অ্যাকাউন্ট ও ডাটা মুছে ফেলুন'}
              </Button>
            </div>
          ) : (
            <p className="text-xs text-ink-500 italic">
              ডাটা এক্সপোর্ট বা অ্যাকাউন্ট মুছে ফেলার সুবিধা পেতে প্রথমে লগ ইন করুন।
            </p>
          )}
        </Card>
      </div>
    </div>
  );
};
