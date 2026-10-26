import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ScanLine,
  Tractor,
  CloudSun,
  Handshake,
  LogOut,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  FileText,
  ShoppingBag,
  MessageSquare,
  BookOpen,
  Layers,
  MessageSquarePlus,
  Stethoscope,
} from 'lucide-react';
import { useAuth } from '../features/auth/AuthContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { PilotFeedbackModal } from '../features/pilot/components/PilotFeedbackModal';
import { AccountApprovalLock } from '../features/auth/components/AccountApprovalLock';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, isAuthenticated } = useAuth();

  const [showPilotFeedback, setShowPilotFeedback] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <Card className="max-w-md w-full p-8 text-center space-y-4">
          <AlertTriangle className="w-12 h-12 text-paddy-400 mx-auto" />
          <h1 className="text-xl font-bold text-forest-900">অননুমোদিত প্রবেশ</h1>
          <p className="text-sm text-ink-600">ড্যাশবোর্ড দেখতে অনুগ্রহ করে লগ ইন করুন।</p>
          <Link to="/login">
            <Button variant="primary" fullWidth size="md">
              লগ ইন পৃষ্ঠায় যান
            </Button>
          </Link>
        </Card>
      </div>
    );
  }

  // If user is not yet approved by admin, show locked account screen
  const isPrivileged = user.role === 'admin' || user.role === 'moderator';
  if (!isPrivileged && user.nidVerificationStatus !== 'approved') {
    return <AccountApprovalLock user={user} />;
  }

  const roleLabels: Record<string, string> = {
    farmer: 'কৃষক',
    owner: 'যন্ত্রের মালিক',
    buyer: 'ফসল ক্রেতা',
    expert: 'কৃষি বিশেষজ্ঞ',
    admin: 'প্রশাসক',
    moderator: 'মডারেটর',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-field-wash border border-line-200 rounded-card p-6 sm:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 shadow-soft">
        <div className="space-y-2">
          <div className="flex items-center gap-2.5">
            <Badge variant="success">সক্রিয় অ্যাকাউন্ট</Badge>
            <span className="text-xs text-ink-600 font-semibold uppercase tracking-wider">
              {roleLabels[user.role] || user.role}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-forest-900">
            স্বাগতম, {user.fullName}!
          </h1>
          <p className="text-sm text-ink-600 flex items-center gap-2">
            <span>ফোন: {user.phone}</span>
            {user.hasProfile && (
              <span className="flex items-center gap-1 text-forest-700">
                <CheckCircle2 className="w-4 h-4" />
                <span>প্রোফাইল তথ্য সংযুক্ত</span>
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Link to="/app/messages">
            <Button variant="outline" size="sm" className="border-line-200 text-xs">
              <MessageSquare className="w-4 h-4 mr-1 text-emerald-700" />
              <span>বার্তা ও ইনবক্স</span>
            </Button>
          </Link>
          <Link to="/app/rental-requests">
            <Button variant="outline" size="sm" className="border-line-200 text-xs">
              <FileText className="w-4 h-4 mr-1 text-forest-700" />
              <span>ভাড়ার অনুরোধসমূহ</span>
            </Button>
          </Link>
          {user.role === 'owner' && (
            <Link to="/app/my-equipment">
              <Button variant="secondary" size="sm" className="text-xs">
                <Tractor className="w-4 h-4 mr-1 text-forest-700" />
                <span>আমার কৃষিযন্ত্র</span>
              </Button>
            </Link>
          )}
          <Link to="/app/my-crops">
            <Button variant="secondary" size="sm" className="text-xs">
              <ShoppingBag className="w-4 h-4 mr-1 text-emerald-700" />
              <span>আমার ফসল</span>
            </Button>
          </Link>
          <Link to="/app/knowledge">
            <Button variant="outline" size="sm" className="border-line-200 text-xs">
              <BookOpen className="w-4 h-4 mr-1 text-emerald-700" />
              <span>অফলাইন তথ্যভাণ্ডার</span>
            </Button>
          </Link>
          <Link to="/app/sync-queue">
            <Button variant="outline" size="sm" className="border-line-200 text-xs">
              <Layers className="w-4 h-4 mr-1 text-amber-700" />
              <span>সিঙ্ক কিউ</span>
            </Button>
          </Link>
          {(user.role?.toLowerCase() === 'expert' || user.role?.toLowerCase() === 'admin') && (
            <Link to="/app/expert-portal">
              <Button variant="secondary" size="sm" className="text-xs bg-leaf-100 text-forest-900 border-leaf-500/30">
                <Stethoscope className="w-4 h-4 mr-1 text-forest-700" />
                <span>বিশেষজ্ঞ পোর্টাল</span>
              </Button>
            </Link>
          )}
          <Link to="/app/guide">
            <Button
              variant="outline"
              size="sm"
              className="border-line-200 text-xs bg-emerald-50/70 text-forest-900 hover:bg-emerald-100/70 font-semibold"
            >
              <BookOpen className="w-4 h-4 mr-1 text-forest-700" />
              <span>ব্যবহার সহায়িকা</span>
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowPilotFeedback(true)}
            className="border-line-200 text-xs text-ink-700"
          >
            <MessageSquarePlus className="w-4 h-4 mr-1 text-emerald-700" />
            <span>মতামত দিন</span>
          </Button>
          <Button variant="outline" size="sm" onClick={handleLogout} className="border-line-200 text-xs">
            <LogOut className="w-4 h-4 mr-1.5 text-danger-600" />
            <span>লগ আউট</span>
          </Button>
        </div>
      </div>

      {/* Main Service Shortcuts */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-forest-900">আপনার প্রয়োজনীয় সেবাসমূহ</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link to="/app/crop-assistant" className="block">
            <Card hoverEffect className="p-6 space-y-3 border-line-200 bg-canvas h-full">
              <div className="w-12 h-12 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center">
                <ScanLine className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-forest-900">ফসল সমস্যা যাচাই</h3>
              <p className="text-xs text-ink-600 leading-relaxed">
                পাতার ছবি বা লক্ষণ বাংলায় লিখে তাৎক্ষণিক এআই রোগ শনাক্তকরণ ও নিরাপদ পরামর্শ।
              </p>
              <div className="pt-2">
                <span className="text-xs font-semibold text-forest-700 flex items-center gap-1">
                  <span>যাচাই শুরু করুন</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Card>
          </Link>

          <Link to="/app/equipment" className="block">
            <Card hoverEffect className="p-6 space-y-3 border-line-200 bg-canvas h-full">
              <div className="w-12 h-12 rounded-btn bg-paddy-400/20 text-soil-700 flex items-center justify-center">
                <Tractor className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-forest-900">কাছের কৃষিযন্ত্র</h3>
              <p className="text-xs text-ink-600 leading-relaxed">
                নিকটস্থ ট্রাক্টর, হার্ভেস্টার বা পাম্প খুঁজুন এবং মালিকের সঙ্গে সরাসরি যোগাযোগ করুন।
              </p>
              <div className="pt-2">
                <span className="text-xs font-semibold text-forest-700 flex items-center gap-1">
                  <span>যন্ত্র খুঁজুন</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Card>
          </Link>

          <Link to="/app/weather" className="block">
            <Card hoverEffect className="p-6 space-y-3 border-line-200 bg-canvas h-full">
              <div className="w-12 h-12 rounded-btn bg-sky-600/10 text-sky-600 flex items-center justify-center">
                <CloudSun className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-forest-900">৩ দিনের আবহাওয়া</h3>
              <p className="text-xs text-ink-600 leading-relaxed">
                বৃষ্টি ও তাপমাত্রার পূর্বাভাস দেখে জমিতে স্প্রে ও সেচ দেওয়ার অনুকূল সময় নির্ধারণ।
              </p>
              <div className="pt-2">
                <span className="text-xs font-semibold text-forest-700 flex items-center gap-1">
                  <span>পূর্বাভাস দেখুন</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Card>
          </Link>

          <Link to="/app/crops" className="block">
            <Card hoverEffect className="p-6 space-y-3 border-line-200 bg-canvas h-full">
              <div className="w-12 h-12 rounded-btn bg-emerald-100 text-emerald-800 flex items-center justify-center">
                <Handshake className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-forest-900">ফসল বাজার ও ক্রেতা সংযোগ</h3>
              <p className="text-xs text-ink-600 leading-relaxed">
                নিজের উৎপাদিত ফসলের তালিকা দিন অথবা পাইকার হিসেবে সরাসরি কৃষকের সাথে সুরক্ষিত চ্যাট করুন।
              </p>
              <div className="pt-2">
                <span className="text-xs font-semibold text-forest-700 flex items-center gap-1">
                  <span>ফসল বাজারে যান</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Card>
          </Link>

          <Link to="/app/knowledge" className="block">
            <Card hoverEffect className="p-6 space-y-3 border-line-200 bg-canvas h-full">
              <div className="w-12 h-12 rounded-btn bg-forest-100 text-forest-800 flex items-center justify-center">
                <BookOpen className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-forest-900">অফলাইন কৃষি তথ্যভাণ্ডার</h3>
              <p className="text-xs text-ink-600 leading-relaxed">
                ইন্টারনেট ছাড়াই বিভিন্ন ফসলের রোগবালাই, সার ও সেচ নির্দেশিকা পড়ুন।
              </p>
              <div className="pt-2">
                <span className="text-xs font-semibold text-forest-700 flex items-center gap-1">
                  <span>তথ্যভাণ্ডারে যান</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </Card>
          </Link>
        </div>
      </div>

      {/* Feedback Modal */}
      <PilotFeedbackModal
        isOpen={showPilotFeedback}
        onClose={() => setShowPilotFeedback(false)}
      />
    </div>
  );
};
