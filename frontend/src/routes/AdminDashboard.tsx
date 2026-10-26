import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../features/auth/AuthContext';
import {
  AdminMetrics,
  AdminUser,
  AuditLogItem,
  BackgroundJob,
  JobStats,
  KnowledgeArticleCreateInput,
  ModerationReportDetail,
} from '../features/admin/types';
import {
  cancelJobApi,
  enqueueJobApi,
  getAdminMetricsApi,
  getAdminReportsApi,
  getAdminUsersApi,
  getAuditLogsApi,
  getJobsListApi,
  getJobStatsApi,
  getNidVerificationsApi,
  publishKnowledgeArticleApi,
  resolveAdminReportApi,
  retryJobApi,
  reviewNidVerificationApi,
  toggleUserStatusApi,
  toggleUserVerificationApi,
  triggerWorkerTickApi,
} from '../features/admin/api';
import {
  PilotTelemetryMetrics,
  PilotFeedback,
} from '../features/pilot/types';
import {
  getPilotMetricsApi,
  getPilotFeedbackListApi,
} from '../features/pilot/api';
import { Button } from '../components/ui/Button';
import {
  ShieldAlert,
  Users,
  Activity,
  CheckCircle2,
  AlertTriangle,
  History,
  BookOpen,
  ArrowLeft,
  X,
  RefreshCw,
  Compass,
  Gauge,
  Smartphone,
  Wifi,
  Star,
  MessageSquare,
  BadgeCheck,
  Cpu,
  Play,
  RotateCcw,
  Ban,
  Layers,
  CreditCard,
  Eye,
  Check,
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, token: authToken } = useAuth();
  const token = authToken || sessionStorage.getItem('shikhor_access_token') || localStorage.getItem('shikhor_token');

  const [activeTab, setActiveTab] = useState<'metrics' | 'reports' | 'users' | 'nid' | 'audit' | 'publish' | 'pilot' | 'jobs'>('metrics');
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [reports, setReports] = useState<ModerationReportDetail[]>([]);
  const [usersList, setUsersList] = useState<AdminUser[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [pilotMetrics, setPilotMetrics] = useState<PilotTelemetryMetrics | null>(null);
  const [pilotFeedbacks, setPilotFeedbacks] = useState<PilotFeedback[]>([]);
  const [jobStats, setJobStats] = useState<JobStats | null>(null);
  const [jobsList, setJobsList] = useState<BackgroundJob[]>([]);
  const [jobStatusFilter, setJobStatusFilter] = useState<string>('all');
  const [triggeringTick, setTriggeringTick] = useState<boolean>(false);
  const [enqueuingJob, setEnqueuingJob] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // NID Verifications State
  const [nidUsers, setNidUsers] = useState<AdminUser[]>([]);
  const [nidStatusFilter, setNidStatusFilter] = useState<string>('pending');
  const [loadingNid, setLoadingNid] = useState<boolean>(false);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [rejectingUser, setRejectingUser] = useState<AdminUser | null>(null);
  const [rejectReason, setRejectReason] = useState<string>('');
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Report Resolution Modal state
  const [selectedReport, setSelectedReport] = useState<ModerationReportDetail | null>(null);
  const [resolveAction, setResolveAction] = useState<'dismiss' | 'warn' | 'hide_content' | 'suspend_user'>('warn');
  const [resolveNotes, setResolveNotes] = useState('');
  const [resolving, setResolving] = useState(false);

  // Knowledge Publish Form state
  const [publishForm, setPublishForm] = useState<KnowledgeArticleCreateInput>({
    cropType: 'paddy',
    category: 'disease',
    titleBn: '',
    summaryBn: '',
    contentBn: '',
    recommendedPracticesBn: '',
  });
  const [publishing, setPublishing] = useState(false);
  const [publishSuccess, setPublishSuccess] = useState<string | null>(null);

  const isPrivileged = user?.role === 'admin' || user?.role === 'moderator';

  const loadData = async () => {
    if (!token || !isPrivileged) return;
    try {
      setLoading(true);
      setError(null);
      const [m, r, u, a, pm, pf, js, jl, nv] = await Promise.all([
        getAdminMetricsApi(token).catch(() => null),
        getAdminReportsApi(token).catch(() => []),
        getAdminUsersApi(token).catch(() => []),
        getAuditLogsApi(token).catch(() => []),
        getPilotMetricsApi(token).catch(() => null),
        getPilotFeedbackListApi(token).catch(() => []),
        getJobStatsApi(token).catch(() => null),
        getJobsListApi(token).catch(() => []),
        getNidVerificationsApi(token).catch(() => []),
      ]);
      setMetrics(m);
      setReports(r);
      setUsersList(u);
      setAuditLogs(a);
      setPilotMetrics(pm);
      setPilotFeedbacks(pf);
      setJobStats(js);
      setJobsList(jl);
      setNidUsers(nv);
    } catch (err: any) {
      setError(err?.message || 'তথ্য লোড করা সম্ভব হয়নি।');
    } finally {
      setLoading(false);
    }
  };

  const handleNidStatusFilterChange = async (status: string) => {
    setNidStatusFilter(status);
    if (!token) return;
    setLoadingNid(true);
    try {
      const data = await getNidVerificationsApi(token, status);
      setNidUsers(data);
    } catch (err) {
      // ignore
    } finally {
      setLoadingNid(false);
    }
  };

  const handleApproveNid = async (targetUser: AdminUser) => {
    if (!token) {
      setActionFeedback({ type: 'error', message: 'অনুমোদন সেশন টোকেন পাওয়া যায়নি।' });
      return;
    }
    setActionLoadingId(targetUser.id);
    setActionFeedback(null);
    try {
      await reviewNidVerificationApi(token, targetUser.id, 'approve');
      setActionFeedback({
        type: 'success',
        message: `${targetUser.fullName}-এর আবেদন সফলভাবে অনুমোদিত হয়েছে এবং ব্যবহারকারীকে ইমেইল পাঠানো হয়েছে!`,
      });
      await loadData();
    } catch (err: any) {
      setActionFeedback({
        type: 'error',
        message: err?.message || 'অনুমোদন সম্পন্ন করা যায়নি।',
      });
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleOpenRejectModal = (targetUser: AdminUser) => {
    setRejectingUser(targetUser);
    setRejectReason('NID কার্ডের ছবি অস্পষ্ট বা তথ্য যাচাইযোগ্য নয়');
    setActionFeedback(null);
  };

  const handleConfirmRejectNid = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !rejectingUser) return;
    const finalReason = rejectReason.trim() || 'এনআইডি তথ্য বা ছবি সুস্পষ্ট নয়';
    setActionLoadingId(rejectingUser.id);
    setActionFeedback(null);
    try {
      await reviewNidVerificationApi(token, rejectingUser.id, 'reject', finalReason);
      setActionFeedback({
        type: 'success',
        message: `${rejectingUser.fullName}-এর আবেদন বাতিল করা হয়েছে এবং কারণসহ নোটিফিকেশন ইমেইল পাঠানো হয়েছে!`,
      });
      setRejectingUser(null);
      setRejectReason('');
      await loadData();
    } catch (err: any) {
      setActionFeedback({
        type: 'error',
        message: err?.message || 'বাতিলকরণ সম্পন্ন করা যায়নি।',
      });
    } finally {
      setActionLoadingId(null);
    }
  };

  useEffect(() => {
    if (isPrivileged) {
      loadData();
    }
  }, [token, isPrivileged]);

  if (!isPrivileged) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center">
        <div className="bg-white rounded-3xl border border-rose-200 p-8 shadow-sm space-y-4">
          <AlertTriangle className="w-12 h-12 text-rose-600 mx-auto" />
          <h2 className="text-xl font-bold text-slate-900">অননুমোদিত প্রবেশাধিকার</h2>
          <p className="text-sm text-slate-600">
            এই ড্যাশবোর্ডটি শুধুমাত্র অনুমোদিত অ্যাডমিন ও মডারেটরদের জন্য সংরক্ষিত (Rule 12)।
          </p>
          <Button variant="primary" onClick={() => navigate('/app')}>
            ড্যাশবোর্ডে ফিরে যান
          </Button>
        </div>
      </div>
    );
  }

  const handleResolveReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !selectedReport || !resolveNotes.trim()) return;
    try {
      setResolving(true);
      await resolveAdminReportApi(token, selectedReport.id, resolveAction, resolveNotes.trim());
      setSelectedReport(null);
      setResolveNotes('');
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'অভিযোগ নিষ্পত্তি ব্যর্থ হয়েছে।');
    } finally {
      setResolving(false);
    }
  };

  const handleToggleUser = async (targetUser: AdminUser) => {
    const nextStatus = !targetUser.isActive;
    const reason = window.prompt(
      `${targetUser.fullName}-কে ${nextStatus ? 'সক্রিয়' : 'স্থগিত'} করার কারণ লিখুন:`
    );
    if (!reason || !token) return;

    try {
      await toggleUserStatusApi(token, targetUser.id, nextStatus, reason);
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'ব্যবহারকারীর অবস্থা পরিবর্তন করা যায়নি।');
    }
  };

  const handleToggleVerification = async (targetUser: AdminUser) => {
    const nextStatus = !targetUser.isVerified;
    const actionBn = nextStatus ? 'যাচাইকৃত (Verified) ব্যাজ প্রদান' : 'যাচাইকৃত ব্যাজ প্রত্যাহার';
    const notes = window.prompt(
      `${targetUser.fullName}-কে ${actionBn} করার কারণ বা নোট লিখুন (ঐচ্ছিক):`,
      nextStatus ? 'কাগজপত্র ও পরিচয় যাচাই সম্পন্ন।' : 'ভেরিফিকেশন মানদণ্ড অসম্পূর্ণ।'
    );
    if (notes === null) return;
    if (!token) return;

    try {
      await toggleUserVerificationApi(token, targetUser.id, nextStatus, notes);
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'ব্যবহারকারীর ভেরিফিকেশন অবস্থা পরিবর্তন করা যায়নি।');
    }
  };

  const handlePublishKnowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !publishForm.titleBn || !publishForm.contentBn) return;
    try {
      setPublishing(true);
      setPublishSuccess(null);
      await publishKnowledgeArticleApi(token, publishForm);
      setPublishSuccess('কৃষি নির্দেশিকা সফলভাবে প্রকাশিত এবং নতুন সংস্করণ তৈরি হয়েছে!');
      setPublishForm({
        cropType: 'paddy',
        category: 'disease',
        titleBn: '',
        summaryBn: '',
        contentBn: '',
        recommendedPracticesBn: '',
      });
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'প্রকাশনা ব্যর্থ হয়েছে।');
    } finally {
      setPublishing(false);
    }
  };

  const handleTriggerWorkerTick = async () => {
    if (!token) return;
    try {
      setTriggeringTick(true);
      const executedJob = await triggerWorkerTickApi(token);
      if (executedJob) {
        alert(`ওয়ার্কার সফলভাবে কাজ সম্পন্ন করেছে: ${executedJob.jobType} (${executedJob.id.slice(0, 8)})`);
      } else {
        alert('বর্তমানে প্রক্রিয়াকরণের জন্য কোনো পেন্ডিং জব নেই।');
      }
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'ওয়ার্কার পরিচালনায় ত্রুটি হয়েছে।');
    } finally {
      setTriggeringTick(false);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    if (!token) return;
    try {
      await retryJobApi(token, jobId);
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'জব রিট্রাই ব্যর্থ হয়েছে।');
    }
  };

  const handleCancelJob = async (jobId: string) => {
    if (!token || !window.confirm('আপনি কি নিশ্চিতভাবে এই জবটি বাতিল করতে চান?')) return;
    try {
      await cancelJobApi(token, jobId);
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'জব বাতিল ব্যর্থ হয়েছে।');
    }
  };

  const handleQuickEnqueue = async (jobType: string) => {
    if (!token) return;
    try {
      setEnqueuingJob(true);
      let payload: Record<string, unknown> = {};
      if (jobType === 'weather_cache_warmup') {
        payload = { district: 'বগুড়া' };
      } else if (jobType === 'test_echo_job') {
        payload = { message: 'ম্যানুয়াল টেস্ট রিকোয়েস্ট ' + new Date().toLocaleTimeString('bn-BD') };
      } else if (jobType === 'telemetry_aggregation') {
        payload = {};
      }
      await enqueueJobApi(token, jobType, payload, 5);
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'জব যোগ করতে ত্রুটি হয়েছে।');
    } finally {
      setEnqueuingJob(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <button
            onClick={() => navigate('/app')}
            className="text-xs text-slate-500 hover:text-emerald-700 flex items-center gap-1.5 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            মূল ড্যাশবোর্ডে ফিরে যান
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 flex items-center gap-2.5">
            <ShieldAlert className="w-7 h-7 text-emerald-700" />
            অ্যাডমিন ও মডারেশন কন্ট্রোল প্যানেল
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            প্ল্যাটফর্মের স্বচ্ছতা, অভিযোগ নিষ্পত্তি এবং নিরাপত্তা অডিট নিয়ন্ত্রণ কেন্দ্র
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={loadData}
          disabled={loading}
          className="text-xs flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          রিফ্রেশ
        </Button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-xs">
          {error}
        </div>
      )}

      {/* Real Platform Metrics Cards (Rule 31) */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-500 block">মোট ব্যবহারকারী</span>
            <span className="text-2xl font-extrabold text-slate-900">{metrics.totalUsers}</span>
            <span className="text-[10px] text-slate-400 block mt-0.5">
              কৃষক {metrics.farmersCount} • পাইকার {metrics.buyersCount}
            </span>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-500 block">সক্রিয় ফসল তালিকা</span>
            <span className="text-2xl font-extrabold text-emerald-700">
              {metrics.activeCropListings}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">উন্মুক্ত বিক্রয়</span>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-500 block">ভাড়ার অনুরোধ</span>
            <span className="text-2xl font-extrabold text-forest-800">
              {metrics.totalRentalRequests}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">কৃষিযন্ত্র বুকিং</span>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-500 block">অমীমাংসিত অভিযোগ</span>
            <span
              className={`text-2xl font-extrabold ${
                metrics.pendingModerationReports > 0 ? 'text-rose-600' : 'text-slate-800'
              }`}
            >
              {metrics.pendingModerationReports}
            </span>
            <span className="text-[10px] text-slate-400 block mt-0.5">মডারেশন প্রয়োজন</span>
          </div>

          <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
            <span className="text-[11px] font-semibold text-slate-500 block">নিরাপত্তা অডিট লগ</span>
            <span className="text-2xl font-extrabold text-slate-800">
              {metrics.totalAuditEvents}
            </span>
            <span className="text-[10px] text-emerald-600 font-medium block mt-0.5 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" />
              সিস্টেম সচল
            </span>
          </div>
        </div>
      )}

      {/* Navigation Tabs - Modern Responsive Grid / Pill System */}
      <div className="bg-slate-100/90 p-1.5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-1.5">
          <button
            onClick={() => setActiveTab('metrics')}
            className={`px-2.5 py-2 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'metrics'
                ? 'bg-white text-forest-900 shadow-xs font-black border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-forest-700 shrink-0" />
            <span className="truncate">সিস্টেম পরিচিতি</span>
          </button>

          <button
            onClick={() => setActiveTab('reports')}
            className={`px-2.5 py-2 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'reports'
                ? 'bg-white text-forest-900 shadow-xs font-black border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-rose-600 shrink-0" />
            <span className="truncate">মডারেশন</span>
            {reports.filter((r) => r.status === 'pending').length > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-rose-100 text-rose-800 font-extrabold leading-none">
                {reports.filter((r) => r.status === 'pending').length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('users')}
            className={`px-2.5 py-2 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'users'
                ? 'bg-white text-forest-900 shadow-xs font-black border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <Users className="w-3.5 h-3.5 text-forest-700 shrink-0" />
            <span className="truncate">ব্যবহারকারী</span>
            <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-slate-200/80 text-slate-700 font-bold leading-none">
              {usersList.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('nid')}
            className={`px-2.5 py-2 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'nid'
                ? 'bg-white text-forest-900 shadow-xs font-black border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <CreditCard className="w-3.5 h-3.5 text-sky-700 shrink-0" />
            <span className="truncate">এনআইডি যাচাই</span>
            {nidUsers.filter((u) => u.nidVerificationStatus === 'pending').length > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-amber-100 text-amber-900 font-extrabold leading-none">
                {nidUsers.filter((u) => u.nidVerificationStatus === 'pending').length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('audit')}
            className={`px-2.5 py-2 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'audit'
                ? 'bg-white text-forest-900 shadow-xs font-black border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <History className="w-3.5 h-3.5 text-indigo-600 shrink-0" />
            <span className="truncate">অডিট ট্রেইল</span>
            <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-slate-200/80 text-slate-700 font-bold leading-none">
              {auditLogs.length}
            </span>
          </button>

          <button
            onClick={() => setActiveTab('publish')}
            className={`px-2.5 py-2 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'publish'
                ? 'bg-white text-forest-900 shadow-xs font-black border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5 text-forest-700 shrink-0" />
            <span className="truncate">জ্ঞান প্রকাশনা</span>
          </button>

          <button
            onClick={() => setActiveTab('pilot')}
            className={`px-2.5 py-2 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'pilot'
                ? 'bg-white text-forest-900 shadow-xs font-black border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <Compass className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
            <span className="truncate">মাঠ পাইলট</span>
          </button>

          <button
            onClick={() => setActiveTab('jobs')}
            className={`px-2.5 py-2 text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'jobs'
                ? 'bg-white text-forest-900 shadow-xs font-black border border-slate-200/60'
                : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-amber-700 shrink-0" />
            <span className="truncate">জব কিউ</span>
            {jobStats && jobStats.total > 0 && (
              <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-slate-200/80 text-slate-700 font-bold leading-none">
                {jobStats.total}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Tab 1: System Overview */}
      {activeTab === 'metrics' && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-6">
          <h3 className="text-base font-bold text-slate-900">অপারেশনাল প্রস্তুতি ও সুরক্ষা নির্দেশিকা</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs leading-relaxed">
            <div className="p-4 bg-emerald-50 rounded-2xl border border-emerald-200/60 space-y-2">
              <span className="font-bold text-emerald-900 text-sm block">ভূমিকাভিত্তিক ক্ষমতা (RBAC)</span>
              <p className="text-emerald-800">
                প্রত্যেকটি সুরক্ষিত কার্যক্রমে অনুমোদনের বাধ্যবাধকতা রয়েছে। সাধারণ ব্যবহারকারী বা অঅনুমোদিত কেউ প্রশাসনিক কোনো ফাইল বা রেকর্ডে প্রবেশ করতে পারে না।
              </p>
            </div>
            <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-2">
              <span className="font-bold text-slate-900 text-sm block">অপরিবর্তনীয় অডিট ট্রেইল</span>
              <p className="text-slate-600">
                প্রশাসনিক সিদ্ধান্ত, রিপোর্ট নিষ্পত্তি, অথবা ব্যবহারকারী স্থগিতকরণের ঘটনাগুলো ডাটাবেস অডিট ট্রেইলে স্বয়ংক্রিয়ভাবে সংরক্ষিত থাকে।
              </p>
            </div>
            <div className="p-4 bg-amber-50 rounded-2xl border border-amber-200/60 space-y-2">
              <span className="font-bold text-amber-900 text-sm block">কৃষি তথ্যের সততা রক্ষা</span>
              <p className="text-amber-900">
                তথ্যভাণ্ডারে যেকোনো নতুন প্রযুক্তি বা বালাইনাশক নির্দেশিকা প্রকাশের পূর্বে অনুমোদিত বিশেষজ্ঞ দ্বারা পর্যালোচনার পর ভার্সন বৃদ্ধির মাধ্যমে প্রকাশিত হয়।
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Moderation Reports */}
      {activeTab === 'reports' && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">অভিযোগ ও মডারেশন কিউ</h3>
            <span className="text-xs text-slate-500">মোট রিপোর্ট: {reports.length}টি</span>
          </div>

          {reports.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-xs">কোনো অভিযোগ জমা নেই।</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 font-semibold">
                    <th className="py-3 px-2">তারিখ</th>
                    <th className="py-3 px-2">অভিযোগকারী</th>
                    <th className="py-3 px-2">অভিযুক্ত</th>
                    <th className="py-3 px-2">কারণ</th>
                    <th className="py-3 px-2">অবস্থা</th>
                    <th className="py-3 px-2 text-right">কার্যক্রম</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {reports.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-2 text-slate-500 shrink-0">
                        {new Date(r.createdAt).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </td>
                      <td className="py-3 px-2 font-medium text-slate-900">{r.reporterName}</td>
                      <td className="py-3 px-2 font-medium text-rose-700">{r.reportedUserName}</td>
                      <td className="py-3 px-2 text-slate-700 max-w-xs truncate">{r.reason}</td>
                      <td className="py-3 px-2">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            r.status === 'pending'
                              ? 'bg-amber-100 text-amber-800'
                              : r.status === 'resolved'
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {r.status === 'pending'
                            ? 'পর্যালোচনাধীন'
                            : r.status === 'resolved'
                            ? 'নিষ্পত্তি হয়েছে'
                            : 'বাতিলকৃত'}
                        </span>
                      </td>
                      <td className="py-3 px-2 text-right">
                        {r.status === 'pending' ? (
                          <Button
                            variant="primary"
                            size="sm"
                            className="text-[11px] py-1 px-2.5"
                            onClick={() => setSelectedReport(r)}
                          >
                            ব্যবস্থা নিন
                          </Button>
                        ) : (
                          <span className="text-[11px] text-slate-400">নিষ্পন্ন</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: User Management */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">ব্যবহারকারী ও হিসাব নিয়ন্ত্রণ</h3>
            <span className="text-xs text-slate-500">মোট হিসাব: {usersList.length}টি</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-semibold">
                  <th className="py-3 px-2">নাম</th>
                  <th className="py-3 px-2">ফোন নম্বর</th>
                  <th className="py-3 px-2">ভূমিকা (Role)</th>
                  <th className="py-3 px-2">অবস্থা</th>
                  <th className="py-3 px-2">ভেরিফিকেশন</th>
                  <th className="py-3 px-2 text-right">কার্যক্রম</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {usersList.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-2 font-bold text-slate-900">{u.fullName}</td>
                    <td className="py-3 px-2 text-slate-600 font-mono">{u.phone}</td>
                    <td className="py-3 px-2">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 uppercase">
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          u.isActive
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {u.isActive ? 'সক্রিয়' : 'স্থগিত (Suspended)'}
                      </span>
                    </td>
                    <td className="py-3 px-2">
                      {u.isVerified ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          <BadgeCheck className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                          যাচাইকৃত
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 text-slate-500">
                          অযাচাইকৃত
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-2 text-right space-x-2">
                      <button
                        onClick={() => handleToggleVerification(u)}
                        className={`text-xs font-bold underline transition-colors ${
                          u.isVerified
                            ? 'text-amber-600 hover:text-amber-800'
                            : 'text-emerald-700 hover:text-emerald-900'
                        }`}
                        title={u.isVerified ? 'ভেরিফিকেশন ব্যাজ প্রত্যাহার করুন' : 'যাচাইকৃত ব্যাজ প্রদান করুন'}
                      >
                        {u.isVerified ? 'ব্যাজ প্রত্যাহার' : 'ব্যাজ প্রদান'}
                      </button>
                      {user?.id !== u.id && user?.role === 'admin' && (
                        <button
                          onClick={() => handleToggleUser(u)}
                          className={`text-xs font-bold underline transition-colors ${
                            u.isActive
                              ? 'text-rose-600 hover:text-rose-800'
                              : 'text-emerald-600 hover:text-emerald-800'
                          }`}
                        >
                          {u.isActive ? 'স্থগিত' : 'সক্রিয়'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab: NID Verifications */}
      {activeTab === 'nid' && (
        <div className="space-y-6">
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <CreditCard className="w-5 h-5 text-emerald-700" />
                  জাতীয় পরিচয়পত্র (NID) যাচাই ও অনুমোদন
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  রেজিস্ট্রেশনকৃত কৃষকদের NID নম্বর, জন্মতারিখ এবং কার্ডের ছবি ম্যানুয়ালি যাচাই করে ভেরিফিকেশন স্ট্যাটাস আপডেট করুন।
                </p>
              </div>

              {/* Status Filter Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                {[
                  { id: 'pending', label: 'পেন্ডিং (অপেক্ষমান)' },
                  { id: 'approved', label: 'অনুমোদিত' },
                  { id: 'rejected', label: 'বাতিলকৃত' },
                  { id: 'all', label: 'সকল আবেদন' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => handleNidStatusFilterChange(tab.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                      nidStatusFilter === tab.id
                        ? 'bg-emerald-800 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Action Feedback Banner */}
          {actionFeedback && (
            <div
              className={`p-4 rounded-2xl text-xs flex items-center justify-between gap-2 transition-all ${
                actionFeedback.type === 'success'
                  ? 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                  : 'bg-rose-50 text-rose-900 border border-rose-200'
              }`}
            >
              <div className="flex items-center gap-2">
                {actionFeedback.type === 'success' ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
                )}
                <span className="font-medium">{actionFeedback.message}</span>
              </div>
              <button
                onClick={() => setActionFeedback(null)}
                className="p-1 rounded-lg hover:bg-black/5 text-slate-500"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {/* List of NID Verifications */}
          {loadingNid ? (
            <div className="py-16 text-center text-slate-500 text-sm">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-600 mb-2" />
              এনআইডি যাচাই তালিকা লোড হচ্ছে...
            </div>
          ) : nidUsers.length === 0 ? (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-12 text-center text-slate-400 text-sm">
              কোনো আবেদন পাওয়া যায়নি।
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {nidUsers.map((u) => (
                <div
                  key={u.id}
                  className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-xs hover:border-slate-300 transition-all space-y-4"
                >
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-sm">{u.fullName}</span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 capitalize">
                          {u.role === 'farmer' ? 'কৃষক' : u.role === 'buyer' ? 'পাইকার' : u.role}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        মোবাইল: {u.phone} {u.email ? `• ${u.email}` : ''} {u.district ? `• ${u.district}` : ''} {u.upazila ? `(${u.upazila})` : ''}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        নিবন্ধন: {new Date(u.createdAt).toLocaleDateString('bn-BD')}
                      </div>
                    </div>

                    {/* Status Badge */}
                    <div>
                      {u.nidVerificationStatus === 'approved' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          অনুমোদিত
                        </span>
                      ) : u.nidVerificationStatus === 'rejected' ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                          <Ban className="w-3.5 h-3.5 text-rose-600" />
                          বাতিলকৃত
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200 animate-pulse">
                          যাচাই অপেক্ষমান
                        </span>
                      )}
                    </div>
                  </div>

                  {/* NID Details */}
                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-2xl border border-slate-100">
                    <div>
                      <span className="text-slate-400 text-[11px] block">এনআইডি নম্বর</span>
                      <span className="font-mono font-bold text-slate-800">
                        {u.nid || 'প্রদান করা হয়নি'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 text-[11px] block">জন্মতারিখ</span>
                      <span className="font-medium text-slate-800">
                        {u.dob || 'প্রদান করা হয়নি'}
                      </span>
                    </div>
                    {u.nidRejectionReason && (
                      <div className="col-span-2 text-rose-700 bg-rose-50 p-2 rounded-xl text-[11px] border border-rose-100">
                        <strong>বাতিলের কারণ:</strong> {u.nidRejectionReason}
                      </div>
                    )}
                  </div>

                  {/* Photos Section */}
                  <div className="space-y-1.5">
                    <span className="text-xs font-semibold text-slate-700 block">
                      এনআইডি কার্ডের ছবিসমূহ (বড় করে দেখতে ক্লিক করুন)
                    </span>
                    <div className="grid grid-cols-2 gap-3">
                      {/* Front Photo */}
                      <div className="space-y-1">
                        <span className="text-[11px] text-slate-500 font-medium">সামনের অংশ</span>
                        {u.nidFrontImage ? (
                          <div
                            onClick={() => setPreviewImage(u.nidFrontImage!)}
                            className="relative group h-32 rounded-xl overflow-hidden border border-slate-200 bg-slate-100 cursor-pointer shadow-xs hover:border-emerald-500 transition-all"
                          >
                            <img
                              src={u.nidFrontImage}
                              alt="NID Front"
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                            />
                            <div className="absolute inset-0 bg-slate-900/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-semibold gap-1">
                              <Eye className="w-4 h-4" />
                              বড় করুন
                            </div>
                          </div>
                        ) : (
                          <div className="h-32 rounded-xl border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center text-slate-400 text-xs">
                            ছবি দেওয়া হয়নি
                          </div>
                        )}
                      </div>

                      {/* Back Photo */}
                      <div className="space-y-1">
                        <span className="text-[11px] text-slate-500 font-medium">পেছনের অংশ</span>
                        {u.nidBackImage ? (
                          <div
                            onClick={() => setPreviewImage(u.nidBackImage!)}
                            className="relative group h-32 rounded-xl overflow-hidden border border-slate-200 bg-slate-100 cursor-pointer shadow-xs hover:border-emerald-500 transition-all"
                          >
                            <img
                              src={u.nidBackImage}
                              alt="NID Back"
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                            />
                            <div className="absolute inset-0 bg-slate-900/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-semibold gap-1">
                              <Eye className="w-4 h-4" />
                              বড় করুন
                            </div>
                          </div>
                        ) : (
                          <div className="h-32 rounded-xl border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center text-slate-400 text-xs">
                            ছবি দেওয়া হয়নি
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                    {u.nidVerificationStatus !== 'approved' && (
                      <Button
                        variant="primary"
                        size="sm"
                        disabled={actionLoadingId === u.id}
                        onClick={() => handleApproveNid(u)}
                        className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold flex items-center gap-1.5"
                      >
                        {actionLoadingId === u.id ? (
                          <RefreshCw className="w-4 h-4 animate-spin" />
                        ) : (
                          <Check className="w-4 h-4" />
                        )}
                        অনুমোদন করুন (Approve)
                      </Button>
                    )}

                    {u.nidVerificationStatus !== 'rejected' && (
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={actionLoadingId === u.id}
                        onClick={() => handleOpenRejectModal(u)}
                        className="border-rose-300 text-rose-700 hover:bg-rose-50 font-bold flex items-center gap-1.5"
                      >
                        <X className="w-4 h-4" />
                        বাতিল করুন (Reject)
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Audit Logs */}
      {activeTab === 'audit' && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-900">নিরাপত্তা ও অপারেশনাল অডিট ট্রেইল</h3>
            <span className="text-xs text-slate-500">মোট রেকর্ড: {auditLogs.length}টি</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-semibold">
                  <th className="py-3 px-2">সময়</th>
                  <th className="py-3 px-2">প্রশাসনিক ব্যক্তি</th>
                  <th className="py-3 px-2">কার্যক্রম (Action)</th>
                  <th className="py-3 px-2">রিসোর্স</th>
                  <th className="py-3 px-2">বিবরণ</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/50">
                    <td className="py-3 px-2 text-slate-400 shrink-0">
                      {new Date(log.createdAt).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3 px-2 text-slate-800 font-bold">{log.actorPhone}</td>
                    <td className="py-3 px-2">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-800">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-slate-500 uppercase">{log.resourceType}</td>
                    <td className="py-3 px-2 text-slate-600 max-w-sm truncate">{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 5: Publish Knowledge */}
      {activeTab === 'publish' && (
        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 max-w-2xl">
          <h3 className="text-base font-bold text-slate-900 mb-1">নতুন কৃষি নির্দেশিকা প্রকাশ</h3>
          <p className="text-xs text-slate-500 mb-5">
            প্রকাশিত তথ্য স্বয়ংক্রিয়ভাবে সংস্করণ বৃদ্ধির মাধ্যমে কৃষকদের অফলাইন তথ্যভাণ্ডারে পৌঁছে যাবে।
          </p>

          {publishSuccess && (
            <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{publishSuccess}</span>
            </div>
          )}

          <form onSubmit={handlePublishKnowledge} className="space-y-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">ফসলের ধরন</label>
                <select
                  value={publishForm.cropType}
                  onChange={(e) => setPublishForm({ ...publishForm, cropType: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
                >
                  <option value="paddy">ধান</option>
                  <option value="potato">আলু</option>
                  <option value="wheat">গম</option>
                  <option value="mustard">সরিষা</option>
                  <option value="maize">ভুট্টা</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">বিভাগ</label>
                <select
                  value={publishForm.category}
                  onChange={(e) => setPublishForm({ ...publishForm, category: e.target.value })}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
                >
                  <option value="disease">রোগবালাই দমন</option>
                  <option value="irrigation">সেচ ব্যবস্থাপনা</option>
                  <option value="fertilizer">সার প্রয়োগ</option>
                  <option value="pest">পোকামাকড় নিয়ন্ত্রণ</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                শিরোনাম (বাংলা) <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                value={publishForm.titleBn}
                onChange={(e) => setPublishForm({ ...publishForm, titleBn: e.target.value })}
                placeholder="যেমন: আলুর আর্লি ব্লাইট রোগের লক্ষণ ও প্রতিকার"
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                সারসংক্ষেপ <span className="text-rose-500">*</span>
              </label>
              <textarea
                rows={2}
                required
                value={publishForm.summaryBn}
                onChange={(e) => setPublishForm({ ...publishForm, summaryBn: e.target.value })}
                placeholder="কৃষকদের জন্য সংক্ষিপ্ত সারাংশ..."
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                বিস্তারিত বিষয়বস্তু <span className="text-rose-500">*</span>
              </label>
              <textarea
                rows={4}
                required
                value={publishForm.contentBn}
                onChange={(e) => setPublishForm({ ...publishForm, contentBn: e.target.value })}
                placeholder="রোগের লক্ষণ, আক্রমণের কারণ ও বিস্তারিত আলোচনা..."
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                সুপারিশকৃত করণীয় (পদ্ধতিগত নির্দেশিকা)
              </label>
              <textarea
                rows={3}
                value={publishForm.recommendedPracticesBn}
                onChange={(e) =>
                  setPublishForm({ ...publishForm, recommendedPracticesBn: e.target.value })
                }
                placeholder="১. মাত্রাতিরিক্ত ইউরিয়া পরিহার করুন। ২. অনুমোদিত ছত্রাকনাশক স্প্রে করুন..."
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>

            <div className="pt-2">
              <Button variant="primary" type="submit" disabled={publishing}>
                {publishing ? 'প্রকাশ হচ্ছে...' : 'অনুমোদিত প্রকাশনা সম্পন্ন করুন'}
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Tab 6: Controlled Pilot Telemetry & Go/No-Go Release Gate (Phase 9) */}
      {activeTab === 'pilot' && (
        <div className="space-y-6">
          {/* Go/No-Go Readiness Review Panel */}
          {pilotMetrics?.go_no_go_checklist && (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-2xl bg-emerald-50 text-emerald-800 border border-emerald-200/60">
                    <Compass className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      মাঠ পাইলট Go/No-Go মূল্যায়ন ও রিলিজ গেট (Phase 9 Exit Criteria)
                    </h3>
                    <p className="text-xs text-slate-500">
                      মাঠ পর্যায়ের তথ্য, ব্যবহারকারীর গ্রহণযোগ্যতা ও সিস্টেমের নির্ভরযোগ্যতার চূড়ান্ত মূল্যায়ন
                    </p>
                  </div>
                </div>
                <div>
                  {pilotMetrics.go_no_go_checklist.overall_status === 'READY_FOR_GO_NO_GO' ? (
                    <span className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                      GO FOR RELEASE (অনুমোদনের জন্য প্রস্তুত)
                    </span>
                  ) : (
                    <span className="px-3.5 py-1.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-amber-700" />
                      পাইলট পর্যবেক্ষণ চলমান (In Progress)
                    </span>
                  )}
                </div>
              </div>

              {/* 6 Criteria Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 text-xs">
                <div className="p-3.5 rounded-2xl border bg-slate-50/50 border-slate-200/80 space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-900">
                    <span>১. নিরাপত্তা ও গোপনীয়তা</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  </div>
                  <p className="text-slate-500 leading-relaxed">
                    কোনো উন্মুক্ত নিরাপত্তা ঝুঁকি নেই; Argon2id, ভূমিকা সুরক্ষা ও ডাটা মাস্কিং সক্রিয়।
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl border bg-slate-50/50 border-slate-200/80 space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-900">
                    <span>২. মূল যাত্রা ও কার্যসমাপ্তি</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  </div>
                  <p className="text-slate-500 leading-relaxed">
                    রোগ নির্ণয়, যন্ত্র বুকিং ও অফলাইন সিঙ্ক সফলভাবে সম্পন্ন হয়েছে।
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl border bg-slate-50/50 border-slate-200/80 space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-900">
                    <span>৩. মডারেশন ও সাপোর্ট সক্ষমতা</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  </div>
                  <p className="text-slate-500 leading-relaxed">
                    অমীমাংসিত অভিযোগের সংখ্যা সহনশীল সীমার ভেতরে রয়েছে।
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl border bg-slate-50/50 border-slate-200/80 space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-900">
                    <span>৪. এআই সীমাবদ্ধতার বোধগম্যতা</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  </div>
                  <p className="text-slate-500 leading-relaxed">
                    {pilotMetrics.comprehension_and_usability.ai_limitations_comprehension_pct}% কৃষক নিশ্চিত করেছেন যে তারা এআই সীমাবদ্ধতা বুঝতে পেরেছেন।
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl border bg-slate-50/50 border-slate-200/80 space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-900">
                    <span>৫. সিস্টেম লেটেন্সি ও আর্কিটেকচার</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  </div>
                  <p className="text-slate-500 leading-relaxed">
                    ডিভাইস ও 2G/3G নেটওয়ার্কের লেটেন্সি সঠিকভাবে পরিমাপকৃত (গড় {pilotMetrics.network_and_latency.avg_latency_ms} ms)।
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl border bg-slate-50/50 border-slate-200/80 space-y-1">
                  <div className="flex items-center justify-between font-bold text-slate-900">
                    <span>৬. চূড়ান্ত Go/No-Go পর্যালোচনা</span>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  </div>
                  <p className="text-slate-500 leading-relaxed">
                    কৃষি বিশেষজ্ঞ ও টেকনিক্যাল টিমের যৌথ পর্যালোচনা সম্পন্ন।
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 7 Telemetry Metrics Cards */}
          {pilotMetrics && (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs space-y-2">
                <span className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-emerald-700" />
                  কার্যক্রম ও সক্রিয়করণ
                </span>
                <div className="text-2xl font-extrabold text-slate-900">
                  {pilotMetrics.activation_and_tasks.completed_crop_cases} টি
                </div>
                <div className="text-[11px] text-slate-500 space-y-0.5">
                  <div>ফসল কেস: {pilotMetrics.activation_and_tasks.completed_crop_cases}</div>
                  <div>ভাড়ার অনুরোধ: {pilotMetrics.activation_and_tasks.created_rental_requests}</div>
                  <div>ফসল তালিকা: {pilotMetrics.activation_and_tasks.created_crop_listings}</div>
                  <div>অফলাইন সিঙ্ক: {pilotMetrics.activation_and_tasks.processed_sync_records}</div>
                </div>
              </div>

              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs space-y-2">
                <span className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  এআই অনিশ্চয়তা ও এসকেলেশন
                </span>
                <div className="text-2xl font-extrabold text-amber-600">
                  {pilotMetrics.ai_escalation.escalation_rate_pct}%
                </div>
                <div className="text-[11px] text-slate-500 space-y-0.5">
                  <div>মোট কেস: {pilotMetrics.ai_escalation.total_crop_cases}</div>
                  <div>অনিশ্চিত অবস্থা: {pilotMetrics.ai_escalation.uncertain_or_unsupported_cases}</div>
                  <div>বিশেষজ্ঞ এসকেলেশন: {pilotMetrics.ai_escalation.escalated_cases}</div>
                  <div>সংশোধন মতামত: {pilotMetrics.ai_escalation.corrective_feedback_count}</div>
                </div>
              </div>

              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs space-y-2">
                <span className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                  <Gauge className="w-4 h-4 text-forest-700" />
                  যন্ত্র ভাড়া কনভার্শন রেট
                </span>
                <div className="text-2xl font-extrabold text-forest-800">
                  {pilotMetrics.rental_conversion.conversion_rate_pct}%
                </div>
                <div className="text-[11px] text-slate-500 space-y-0.5">
                  <div>মোট অনুরোধ: {pilotMetrics.rental_conversion.total_rental_requests}</div>
                  <div>গৃহীত ভাড়া: {pilotMetrics.rental_conversion.accepted_rentals}</div>
                  <div>সফল নিষ্পত্তি: ১০০% স্বচ্ছ হিসাব</div>
                </div>
              </div>

              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs space-y-2">
                <span className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                  <Wifi className="w-4 h-4 text-emerald-700" />
                  অফলাইন সিঙ্ক নির্ভরযোগ্যতা
                </span>
                <div className="text-2xl font-extrabold text-emerald-700">
                  {pilotMetrics.offline_sync_reliability.sync_success_rate_pct}%
                </div>
                <div className="text-[11px] text-slate-500 space-y-0.5">
                  <div>মোট সিঙ্ক রেকর্ড: {pilotMetrics.offline_sync_reliability.total_sync_operations}</div>
                  <div>সফল সিঙ্ক: {pilotMetrics.offline_sync_reliability.successful_syncs}</div>
                  <div>ডুপ্লিকেট প্রতিরোধ: আইডিএমপোটেন্ট সক্রিয়</div>
                </div>
              </div>

              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs space-y-2">
                <span className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                  <Star className="w-4 h-4 text-amber-500" />
                  বাংলা বোধগম্যতা ও সহজতা
                </span>
                <div className="text-2xl font-extrabold text-slate-900">
                  {pilotMetrics.comprehension_and_usability.avg_bangla_comprehension} <span className="text-xs font-normal text-slate-400">/ ৫.০</span>
                </div>
                <div className="text-[11px] text-slate-500 space-y-0.5">
                  <div>সহজতা রেটিং: {pilotMetrics.comprehension_and_usability.avg_ease_of_use} / ৫.০</div>
                  <div>মোট মতামত: {pilotMetrics.comprehension_and_usability.total_feedback_submissions} টি</div>
                  <div>সীমাবদ্ধতা অবগত: {pilotMetrics.comprehension_and_usability.ai_limitations_comprehension_pct}%</div>
                </div>
              </div>

              <div className="bg-white p-5 rounded-3xl border border-slate-200/80 shadow-xs space-y-2">
                <span className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                  <Smartphone className="w-4 h-4 text-slate-700" />
                  নেটওয়ার্ক ও লেটেন্সি
                </span>
                <div className="text-2xl font-extrabold text-slate-900">
                  {pilotMetrics.network_and_latency.avg_latency_ms} <span className="text-xs font-normal text-slate-400">ms</span>
                </div>
                <div className="text-[11px] text-slate-500 space-y-0.5">
                  <div>নমুনা সংখ্যা: {pilotMetrics.network_and_latency.total_latency_samples}</div>
                  <div>নেটওয়ার্ক: 3G / 4G / 2G ফিল্ড টেস্ট</div>
                  <div>ডিভাইস: কমদামী অ্যান্ড্রয়েড অপ্টিমাইজড</div>
                </div>
              </div>
            </div>
          )}

          {/* Qualitative Feedback Stream */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-emerald-700" />
                মাঠ পাইলট অংশগ্রহণকারীদের মতামত প্রবাহ ({pilotFeedbacks.length})
              </h3>
            </div>

            {pilotFeedbacks.length === 0 ? (
              <div className="py-8 text-center text-slate-400 text-xs">
                এখনো কোনো নতুন মতামত জমা পড়েনি।
              </div>
            ) : (
              <div className="space-y-3">
                {pilotFeedbacks.map((fb) => (
                  <div
                    key={fb.id}
                    className="p-4 rounded-2xl border border-slate-100 bg-slate-50/50 space-y-2 text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 capitalize">
                          {fb.task_type.replace('_', ' ')}
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-semibold">
                          সহজতা: {fb.ease_of_use_rating}/৫
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 text-[10px] font-semibold">
                          বাংলা: {fb.bangla_comprehension_rating}/৫
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {new Date(fb.created_at).toLocaleDateString('bn-BD')}
                      </div>
                    </div>

                    {fb.comments && (
                      <p className="text-slate-700 italic bg-white p-3 rounded-xl border border-slate-100">
                        "{fb.comments}"
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-500 pt-1">
                      <span>ডিভাইস: {fb.device_category}</span>
                      <span>•</span>
                      <span>নেটওয়ার্ক: {fb.network_type}</span>
                      {fb.latency_ms !== null && (
                        <>
                          <span>•</span>
                          <span>লেটেন্সি: {fb.latency_ms} ms</span>
                        </>
                      )}
                      {fb.district && (
                        <>
                          <span>•</span>
                          <span>জেলা: {fb.district}</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 7: Durable Job Workers (Phase Later / Rule 25) */}
      {activeTab === 'jobs' && (
        <div className="space-y-6">
          {/* Header & Worker Metrics */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-emerald-700" />
                  স্থায়ী ও বিতরিত জব কিউ ব্যবস্থা (Durable Distributed Job Queue)
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  AGENTS.md Rule 25 অনুযায়ী দীর্ঘমেয়াদী ক্রিটিক্যাল কাজ (নোটিফিকেশন, ওয়েদার প্রি-ওয়ার্মিং, মেট্রিক্স ইত্যাদি) ডাটাবেজে স্থায়ীভাবে সংরক্ষিত ও ব্যাকগ্রাউন্ড কর্মী দ্বারা প্রসেস হয়।
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleTriggerWorkerTick}
                  disabled={triggeringTick}
                  className="text-xs flex items-center gap-1.5"
                >
                  <Play className={`w-3.5 h-3.5 ${triggeringTick ? 'animate-spin' : ''}`} />
                  {triggeringTick ? 'চলছে...' : 'ম্যানুয়াল কর্মী চালান (Run Worker Tick)'}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickEnqueue('test_echo_job')}
                  disabled={enqueuingJob}
                  className="text-xs"
                >
                  + টেস্ট ইকো জব
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleQuickEnqueue('weather_cache_warmup')}
                  disabled={enqueuingJob}
                  className="text-xs"
                >
                  + আবহাওয়া প্রি-ওয়ার্ম
                </Button>
              </div>
            </div>

            {/* Queue Metrics Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2 border-t border-slate-100">
              <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/70">
                <span className="text-[11px] font-semibold text-slate-500 block">মোট কিউ জব</span>
                <span className="text-xl font-extrabold text-slate-900">{jobStats?.total ?? 0}</span>
                <span className="text-[10px] text-slate-400 block mt-0.5">সবগুলো রেকর্ড</span>
              </div>

              <div className="p-3.5 bg-amber-50/70 rounded-2xl border border-amber-200/60">
                <span className="text-[11px] font-semibold text-amber-800 block">পেন্ডিং (Pending)</span>
                <span className="text-xl font-extrabold text-amber-700">{jobStats?.pending ?? 0}</span>
                <span className="text-[10px] text-amber-600 block mt-0.5">প্রক্রিয়াকরণের অপেক্ষায়</span>
              </div>

              <div className="p-3.5 bg-blue-50/70 rounded-2xl border border-blue-200/60">
                <span className="text-[11px] font-semibold text-blue-800 block">প্রসেসিং (Processing)</span>
                <span className="text-xl font-extrabold text-blue-700">{jobStats?.processing ?? 0}</span>
                <span className="text-[10px] text-blue-600 block mt-0.5">বর্তমানে কার্যরত</span>
              </div>

              <div className="p-3.5 bg-emerald-50/70 rounded-2xl border border-emerald-200/60">
                <span className="text-[11px] font-semibold text-emerald-800 block">সম্পন্ন (Completed)</span>
                <span className="text-xl font-extrabold text-emerald-700">{jobStats?.completed ?? 0}</span>
                <span className="text-[10px] text-emerald-600 block mt-0.5">সফলভাবে সমাপ্ত</span>
              </div>

              <div className="p-3.5 bg-rose-50/70 rounded-2xl border border-rose-200/60">
                <span className="text-[11px] font-semibold text-rose-800 block">ডেড লেটার (DLQ)</span>
                <span className="text-xl font-extrabold text-rose-700">{jobStats?.deadLetter ?? 0}</span>
                <span className="text-[10px] text-rose-600 block mt-0.5">সর্বোচ্চ ব্যর্থ জব</span>
              </div>

              <div className="p-3.5 bg-purple-50/70 rounded-2xl border border-purple-200/60">
                <span className="text-[11px] font-semibold text-purple-800 block">সক্রিয় কর্মী (Workers)</span>
                <span className="text-xl font-extrabold text-purple-700">{jobStats?.activeWorkers ?? 0}</span>
                <span className="text-[10px] text-purple-600 block mt-0.5">লক সক্রিয় কর্মী</span>
              </div>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pt-2">
              <span className="text-xs font-semibold text-slate-500 mr-1 flex items-center gap-1">
                <Layers className="w-3.5 h-3.5" /> ফিল্টার:
              </span>
              {[
                { id: 'all', label: 'সব' },
                { id: 'pending', label: 'পেন্ডিং' },
                { id: 'processing', label: 'প্রসেসিং' },
                { id: 'completed', label: 'সম্পন্ন' },
                { id: 'failed', label: 'ব্যর্থ / DLQ' },
              ].map((f) => (
                <button
                  key={f.id}
                  onClick={() => setJobStatusFilter(f.id)}
                  className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
                    jobStatusFilter === f.id
                      ? 'bg-emerald-700 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Job Queue Table / Cards */}
          <div className="bg-white rounded-3xl border border-slate-200/80 p-6 space-y-4">
            <h4 className="text-sm font-bold text-slate-800 flex items-center justify-between">
              <span>কিউতে থাকা জব তালিকা ({jobsList.length})</span>
              <span className="text-xs font-normal text-slate-400">সর্বশেষ স্বয়ংক্রিয় রিফ্রেশ সক্রিয়</span>
            </h4>

            {jobsList.length === 0 ? (
              <div className="text-center py-12 text-slate-400 text-xs">
                কোনো ব্যাকগ্রাউন্ড জব পাওয়া যায়নি।
              </div>
            ) : (
              <div className="space-y-3">
                {jobsList
                  .filter((job) => {
                    if (jobStatusFilter === 'all') return true;
                    if (jobStatusFilter === 'failed') return job.status === 'failed' || job.status === 'dead_letter';
                    return job.status === jobStatusFilter;
                  })
                  .map((job) => (
                    <div
                      key={job.id}
                      className="p-4 rounded-2xl border border-slate-200/80 hover:border-emerald-300 transition-all bg-white shadow-xs space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-xs text-slate-900 font-mono bg-slate-100 px-2 py-0.5 rounded-md">
                            {job.jobType}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                              job.status === 'completed'
                                ? 'bg-emerald-100 text-emerald-800'
                                : job.status === 'processing'
                                ? 'bg-blue-100 text-blue-800 animate-pulse'
                                : job.status === 'dead_letter' || job.status === 'failed'
                                ? 'bg-rose-100 text-rose-800'
                                : job.status === 'cancelled'
                                ? 'bg-slate-200 text-slate-700'
                                : 'bg-amber-100 text-amber-800'
                            }`}
                          >
                            {job.status === 'completed'
                              ? 'সম্পন্ন'
                              : job.status === 'processing'
                              ? 'প্রসেসিং'
                              : job.status === 'dead_letter'
                              ? 'ডেড লেটার'
                              : job.status === 'failed'
                              ? 'ব্যর্থ'
                              : job.status === 'cancelled'
                              ? 'বাতিল'
                              : 'পেন্ডিং'}
                          </span>
                          <span className="text-[10px] font-medium text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-md">
                            অগ্রাধিকার: {job.priority}
                          </span>
                          <span className="text-[10px] font-medium text-slate-500 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded-md">
                            চেষ্টা: {job.attempts}/{job.maxAttempts}
                          </span>
                        </div>

                        {/* Action buttons */}
                        <div className="flex items-center gap-2">
                          {(job.status === 'dead_letter' || job.status === 'failed') && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleRetryJob(job.id)}
                              className="text-xs flex items-center gap-1 text-emerald-700 border-emerald-300 hover:bg-emerald-50"
                            >
                              <RotateCcw className="w-3 h-3" />
                              পুনরায় চালান
                            </Button>
                          )}
                          {job.status === 'pending' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleCancelJob(job.id)}
                              className="text-xs flex items-center gap-1 text-rose-700 border-rose-300 hover:bg-rose-50"
                            >
                              <Ban className="w-3 h-3" />
                              বাতিল
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* Meta Information Grid */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] text-slate-600 bg-slate-50/80 p-2.5 rounded-xl border border-slate-100">
                        <div>
                          <strong className="text-slate-700">আইডি:</strong>{' '}
                          <span className="font-mono text-[10px]">{job.id.slice(0, 18)}...</span>
                        </div>
                        <div>
                          <strong className="text-slate-700">লক কর্মী:</strong>{' '}
                          <span className="font-mono text-[10px]">{job.lockedBy || 'মুক্ত (None)'}</span>
                        </div>
                        <div>
                          <strong className="text-slate-700">নির্ধারিত সময়:</strong>{' '}
                          <span>{new Date(job.scheduledAt).toLocaleTimeString('bn-BD')}</span>
                        </div>
                      </div>

                      {/* Error or Result Data Display */}
                      {job.lastError && (
                        <div className="p-2.5 bg-rose-50/80 border border-rose-200 rounded-xl text-rose-700 text-xs font-mono">
                          <strong>সর্বশেষ ত্রুটি:</strong> {job.lastError}
                        </div>
                      )}

                      {job.resultData && (
                        <div className="p-2.5 bg-emerald-50/80 border border-emerald-200 rounded-xl text-emerald-800 text-[11px] font-mono overflow-x-auto">
                          <strong>ফলাফল:</strong> {JSON.stringify(job.resultData)}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Resolution Modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl max-w-md w-full shadow-2xl border border-slate-100 p-6 text-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-base font-bold text-slate-900">অভিযোগ নিষ্পত্তি করুন</h3>
              <button
                onClick={() => setSelectedReport(null)}
                className="p-1 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 mb-4 space-y-1">
              <div>
                <strong>অভিযুক্ত ব্যক্তি:</strong> {selectedReport.reportedUserName}
              </div>
              <div>
                <strong>কারণ:</strong> {selectedReport.reason}
              </div>
              {selectedReport.details && (
                <div className="text-slate-500 mt-1">"{selectedReport.details}"</div>
              )}
            </div>

            <form onSubmit={handleResolveReport} className="space-y-4">
              <div>
                <label className="block text-slate-700 font-semibold mb-1">গৃহীত ব্যবস্থা</label>
                <select
                  value={resolveAction}
                  onChange={(e: any) => setResolveAction(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
                >
                  <option value="warn">সতর্কবার্তা দিন (Warning Issued)</option>
                  <option value="suspend_user">অ্যাকাউন্ট স্থগিত করুন (Suspend User)</option>
                  <option value="hide_content">কনটেন্ট অপসারণ করুন (Hide Content)</option>
                  <option value="dismiss">অভিযোগ খারিজ (Dismiss)</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  সিদ্ধান্ত ও পর্যালোচনার বিবরণ <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="গৃহীত ব্যবস্থার যৌক্তিক কারণ লিখুন (অডিট লগে অন্তর্ভুক্ত হবে)..."
                  value={resolveNotes}
                  onChange={(e) => setResolveNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  variant="outline"
                  type="button"
                  onClick={() => setSelectedReport(null)}
                  disabled={resolving}
                >
                  বাতিল
                </Button>
                <Button variant="primary" type="submit" disabled={resolving}>
                  {resolving ? 'সংরক্ষণ হচ্ছে...' : 'নিষ্পত্তি সম্পন্ন করুন'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* NID Rejection Modal */}
      {rejectingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs animate-fade-in">
          <div className="bg-white rounded-3xl max-w-lg w-full shadow-2xl border border-slate-100 p-6 text-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-rose-50 rounded-xl text-rose-600">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    এনআইডি আবেদন বাতিলের কারণ
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    আবেদনকারী: {rejectingUser.fullName} ({rejectingUser.phone})
                  </p>
                </div>
              </div>
              <button
                onClick={() => setRejectingUser(null)}
                className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleConfirmRejectNid} className="space-y-4">
              <div>
                <label className="block text-slate-700 font-semibold mb-1.5">
                  দ্রুত কারণ নির্বাচন করুন:
                </label>
                <div className="space-y-1.5">
                  {[
                    'NID কার্ডের ছবি অস্পষ্ট বা কাটা পড়েছে',
                    'এনআইডি নম্বর বা জন্মতারিখের তথ্যের সাথে ছবির অমিল',
                    'জাল বা অবৈধ পরিচয়পত্র প্রতীয়মান',
                    'সামনের বা পেছনের অংশের ছবি অনুপস্থিত',
                  ].map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setRejectReason(preset)}
                      className={`w-full text-left px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
                        rejectReason === preset
                          ? 'border-rose-300 bg-rose-50 text-rose-800'
                          : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      {preset}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  বাতিলের বিবরণ বা কাস্টম কারণ <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="কৃষকের ইমেইলে পাঠানোর জন্য বাতিলের সুনির্দিষ্ট কারণ লিখুন..."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-500"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  * এই কারণটি স্বয়ংক্রিয়ভাবে কৃষকের ইমেইলে নোটিফিকেশন হিসেবে পৌঁছে যাবে।
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  variant="outline"
                  type="button"
                  onClick={() => setRejectingUser(null)}
                  disabled={actionLoadingId === rejectingUser.id}
                >
                  বাতিল
                </Button>
                <Button
                  variant="primary"
                  type="submit"
                  disabled={actionLoadingId === rejectingUser.id}
                  className="bg-rose-600 hover:bg-rose-700 text-white font-bold"
                >
                  {actionLoadingId === rejectingUser.id ? (
                    <span className="flex items-center gap-1.5">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      বাতিল ও ইমেইল পাঠানো হচ্ছে...
                    </span>
                  ) : (
                    'নিশ্চিতভাবে বাতিল করুন'
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Full-screen Image Preview Modal */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in"
          onClick={() => setPreviewImage(null)}
        >
          <div
            className="bg-white rounded-3xl max-w-2xl w-full shadow-2xl border border-slate-100 p-5 text-xs overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-emerald-700" />
                জাতীয় পরিচয়পত্র (NID) প্রিভিউ
              </h3>
              <div className="flex items-center gap-2">
                <a
                  href={previewImage}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold"
                >
                  নতুন ট্যাবে খুলুন ↗
                </a>
                <button
                  onClick={() => setPreviewImage(null)}
                  className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="max-h-[75vh] flex items-center justify-center bg-slate-900/5 rounded-2xl overflow-hidden p-2">
              <img
                src={previewImage}
                alt="Full NID Preview"
                className="max-h-[70vh] w-auto max-w-full object-contain rounded-xl shadow-sm"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
