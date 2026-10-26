import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  ConversationItem,
  MessageItem,
  ModerationReportInput,
} from '../features/messaging/types';
import {
  blockUserApi,
  getConversationMessagesApi,
  getMyConversationsApi,
  reportUserApi,
  sendMessageApi,
  sendMessageWithAttachmentApi,
} from '../features/messaging/api';
import { ConversationChat } from '../features/messaging/components/ConversationChat';
import { ReportModal } from '../features/messaging/components/ReportModal';
import { MessageSquare, ShieldCheck, ArrowLeft, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const MessagesInbox: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const token = localStorage.getItem('shikhor_token');

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(searchParams.get('convId'));
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string>('');
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Moderation Report Modal state
  const [reportTarget, setReportTarget] = useState<{ id: string; name: string } | null>(null);

  // Fetch current user ID from /auth/me
  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    fetch('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.id) setCurrentUserId(data.id);
      })
      .catch(() => {});
  }, [token]);

  const loadConversations = async () => {
    if (!token) return;
    try {
      setLoadingConvs(true);
      setError(null);
      const data = await getMyConversationsApi(token);
      setConversations(data);
      if (!activeConvId && data.length > 0) {
        setActiveConvId(data[0].id);
      }
    } catch (err: any) {
      setError(err?.message || 'কথোপকথন তালিকা লোড করা যায়নি।');
    } finally {
      setLoadingConvs(false);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [token]);

  // Load messages whenever activeConvId changes
  const loadMessages = async (convId: string) => {
    if (!token) return;
    try {
      setLoadingMsgs(true);
      const data = await getConversationMessagesApi(token, convId);
      setMessages(data);
    } catch (err: any) {
      console.error('Failed to load messages', err);
    } finally {
      setLoadingMsgs(false);
    }
  };

  useEffect(() => {
    if (activeConvId) {
      loadMessages(activeConvId);
      setSearchParams({ convId: activeConvId });
    }
  }, [activeConvId]);

  const handleSendMessage = async (content: string, attachment?: File) => {
    if (!token || !activeConvId) return;
    let newMsg: MessageItem;
    if (attachment) {
      newMsg = await sendMessageWithAttachmentApi(token, activeConvId, attachment, content);
    } else {
      newMsg = await sendMessageApi(token, activeConvId, content);
    }
    setMessages((prev) => [...prev, newMsg]);
    // Refresh conversation list to bump updated_at
    const updatedConvs = await getMyConversationsApi(token);
    setConversations(updatedConvs);
  };

  const handleBlockUser = async (targetUserId: string) => {
    if (!token) return;
    try {
      await blockUserApi(token, targetUserId);
      alert('ব্যবহারকারীকে সফলভাবে ব্লক করা হয়েছে।');
      loadConversations();
    } catch (err: any) {
      alert(err?.message || 'ব্লক করা ব্যর্থ হয়েছে।');
    }
  };

  const handleOpenReport = (targetUserId: string, targetUserName: string) => {
    setReportTarget({ id: targetUserId, name: targetUserName });
  };

  const handleSubmitReport = async (input: ModerationReportInput) => {
    if (!token) return;
    await reportUserApi(token, input);
  };

  const activeConversation = conversations.find((c) => c.id === activeConvId);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <button
            onClick={() => navigate('/app/crops')}
            className="text-xs text-slate-500 hover:text-emerald-700 flex items-center gap-1.5 mb-2 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            ফসল বাজারে ফিরে যান
          </button>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            বার্তা ও যোগাযোগ কেন্দ্র
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            ফসল ক্রয়-বিক্রয় ও সরঞ্জাম ভাড়ার বিষয়ে সুরক্ষিত ইন-প্ল্যাটফর্ম কথোপকথন
          </p>
        </div>

        <Button
          variant="outline"
          className="text-xs flex items-center gap-1.5 self-start sm:self-auto"
          onClick={() => {
            loadConversations();
            if (activeConvId) loadMessages(activeConvId);
          }}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          রিফ্রেশ করুন
        </Button>
      </div>

      {/* Main Grid: Sidebar + Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Sidebar: Conversations List */}
        <div
          className={`lg:col-span-4 bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden ${
            activeConvId ? 'hidden lg:block' : 'block'
          }`}
        >
          <div className="p-4 bg-slate-50 border-b border-slate-200/80 flex items-center justify-between">
            <span className="text-sm font-bold text-slate-800">কথোপকথন ({conversations.length})</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>

          <div className="divide-y divide-slate-100 h-[420px] sm:h-[440px] overflow-y-auto">
            {loadingConvs ? (
              <div className="p-8 text-center text-xs text-slate-400">তালিকা লোড হচ্ছে...</div>
            ) : error ? (
              <div className="p-4 text-center text-xs text-rose-600">{error}</div>
            ) : conversations.length === 0 ? (
              <div className="p-8 text-center text-slate-400">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                <p className="text-xs font-medium text-slate-600">কোনো বার্তা নেই</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  ফসল বাজার বা সরঞ্জাম তালিকা থেকে বার্তা শুরু করুন।
                </p>
              </div>
            ) : (
              conversations.map((c) => {
                const isUserP1 = currentUserId === c.participant1Id;
                const otherName = isUserP1 ? c.participant2Name : c.participant1Name;
                const isSelected = c.id === activeConvId;

                return (
                  <button
                    key={c.id}
                    onClick={() => setActiveConvId(c.id)}
                    className={`w-full text-left p-4 transition-colors flex items-center gap-3 ${
                      isSelected
                        ? 'bg-emerald-50/70 border-l-4 border-emerald-600'
                        : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm shrink-0">
                      {otherName.slice(0, 1)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-slate-900 truncate">
                          {otherName}
                        </span>
                        <span className="text-[10px] text-slate-400 shrink-0">
                          {new Date(c.updatedAt).toLocaleDateString([], {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 truncate mt-0.5">
                        {c.contextType === 'crop_listing' ? '🌾 ফসল সংক্রান্ত' : 'বার্তা'}
                      </p>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Pane: Active Chat Window */}
        <div
          className={`lg:col-span-8 ${
            activeConvId ? 'block' : 'hidden lg:block'
          }`}
        >
          {activeConvId && (
            <div className="lg:hidden mb-3">
              <Button
                variant="outline"
                className="text-xs flex items-center gap-1.5"
                onClick={() => setActiveConvId(null)}
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                সকল কথোপকথনে ফিরে যান
              </Button>
            </div>
          )}

          {activeConversation ? (
            <ConversationChat
              conversation={activeConversation}
              messages={messages}
              currentUserId={currentUserId}
              token={token}
              onSendMessage={handleSendMessage}
              onBlockUser={handleBlockUser}
              onOpenReport={handleOpenReport}
              loadingMessages={loadingMsgs}
            />
          ) : (
            <div className="bg-white rounded-3xl border border-slate-200/80 p-8 text-center shadow-xs flex flex-col items-center justify-center h-[480px] sm:h-[500px]">
              <MessageSquare className="w-12 h-12 text-slate-300 mb-3" />
              <h3 className="text-base font-bold text-slate-800">কোনো কথোপকথন নির্বাচন করা হয়নি</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-xs">
                বাম পাশের তালিকা থেকে যেকোনো একটি কথোপকথন নির্বাচন করুন অথবা ফসল বাজার থেকে কৃষকদের বার্তা পাঠান।
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Abuse Moderation Report Modal */}
      {reportTarget && (
        <ReportModal
          isOpen={true}
          onClose={() => setReportTarget(null)}
          onSubmit={handleSubmitReport}
          targetUserId={reportTarget.id}
          targetUserName={reportTarget.name}
        />
      )}
    </div>
  );
};
