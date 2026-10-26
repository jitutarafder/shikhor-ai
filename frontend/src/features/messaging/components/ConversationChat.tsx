import React, { useState, useEffect, useRef } from 'react';
import { ConversationItem, MessageItem } from '../types';
import {
  Send,
  ShieldBan,
  ShieldAlert,
  Check,
  CheckCheck,
  AlertCircle,
  Image as ImageIcon,
  X,
  Maximize2,
} from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { getErrorMessage } from '../../../lib/errors';

interface ConversationChatProps {
  conversation: ConversationItem;
  messages: MessageItem[];
  currentUserId: string;
  token?: string | null;
  onSendMessage: (content: string, attachment?: File) => Promise<void>;
  onBlockUser: (targetUserId: string) => void;
  onOpenReport: (targetUserId: string, targetUserName: string) => void;
  loadingMessages?: boolean;
}

export const ConversationChat: React.FC<ConversationChatProps> = ({
  conversation,
  messages,
  currentUserId,
  token,
  onSendMessage,
  onBlockUser,
  onOpenReport,
  loadingMessages = false,
}) => {
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFilePreview, setSelectedFilePreview] = useState<string | null>(null);
  const [previewModalUrl, setPreviewModalUrl] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isUserP1 = currentUserId === conversation.participant1Id;
  const otherUserName = isUserP1 ? conversation.participant2Name : conversation.participant1Name;
  const otherUserId = isUserP1 ? conversation.participant2Id : conversation.participant1Id;

  const scrollToBottom = (smooth = false) => {
    if (messagesContainerRef.current) {
      if (smooth) {
        messagesContainerRef.current.scrollTo({
          top: messagesContainerRef.current.scrollHeight,
          behavior: 'smooth',
        });
      } else {
        messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
      }
    }
  };

  useEffect(() => {
    scrollToBottom(false);
  }, [messages]);

  // Clean up object preview URL on unmount or file change
  useEffect(() => {
    return () => {
      if (selectedFilePreview) {
        URL.revokeObjectURL(selectedFilePreview);
      }
    };
  }, [selectedFilePreview]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type (JPEG, PNG, WebP)
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
    if (!allowedTypes.includes(file.type.toLowerCase())) {
      setError('শুধুমাত্র জেপিইজি (JPEG), পিএনজি (PNG) বা ওয়েবপি (WebP) ফরম্যাটের ছবি গ্রহণযোগ্য।');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    // Validate size (max 10MB)
    const maxSizeBytes = 10 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      setError('ছবির আকার সর্বোচ্চ ১০ মেগাবাইট (10MB) হতে পারে।');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setSelectedFile(file);
    const previewUrl = URL.createObjectURL(file);
    setSelectedFilePreview(previewUrl);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (selectedFilePreview) {
      URL.revokeObjectURL(selectedFilePreview);
      setSelectedFilePreview(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const hasText = inputText.trim().length > 0;
    const hasFile = selectedFile !== null;
    if ((!hasText && !hasFile) || sending) return;

    try {
      setSending(true);
      setError(null);
      await onSendMessage(inputText.trim(), selectedFile || undefined);
      setInputText('');
      handleRemoveFile();
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'বার্তা বা ছবি পাঠানো সম্ভব হয়নি।'));
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-[480px] sm:h-[500px] bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
      {/* Chat Header */}
      <div className="px-6 py-3.5 bg-slate-50/80 border-b border-slate-200/80 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm border border-emerald-200">
            {otherUserName.slice(0, 1)}
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 leading-none">{otherUserName}</h3>
            <span className="text-xs text-slate-500 mt-1 inline-block">
              {conversation.contextType === 'crop_listing' ? 'কৃষি ফসল সংক্রান্ত বার্তা' : 'সাধারণ বার্তা'}
            </span>
          </div>
        </div>

        {/* Action Controls: Report & Block (Abuse Prevention Rule 27) */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => onOpenReport(otherUserId, otherUserName)}
            title="রিপোর্ট বা অভিযোগ করুন"
            className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors text-xs flex items-center gap-1.5 font-medium"
          >
            <ShieldAlert className="w-4 h-4" />
            <span className="hidden sm:inline">অভিযোগ</span>
          </button>
          <button
            onClick={() => {
              if (
                window.confirm(
                  `${otherUserName}-কে কি ব্লক করতে চান? এর পর থেকে তিনি আপনাকে আর বার্তা পাঠাতে পারবেন না।`
                )
              ) {
                onBlockUser(otherUserId);
              }
            }}
            title="ব্যবহারকারীকে ব্লক করুন"
            className="p-2 text-slate-500 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition-colors text-xs flex items-center gap-1.5 font-medium"
          >
            <ShieldBan className="w-4 h-4" />
            <span className="hidden sm:inline">ব্লক</span>
          </button>
        </div>
      </div>

      {/* Message Feed */}
      <div ref={messagesContainerRef} className="flex-1 p-5 overflow-y-auto space-y-3 bg-slate-50/30">
        {loadingMessages ? (
          <div className="flex justify-center items-center h-full text-slate-400 text-sm">
            বার্তা লোড হচ্ছে...
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6 text-slate-400">
            <p className="text-sm font-medium text-slate-600">কোনো বার্তা পাওয়া যায়নি</p>
            <p className="text-xs text-slate-400 mt-1">
              নিরাপদে ফসলের দাম ও নমুনা ছবি পাঠাতে নিচের ইনপুট ব্যবহার করুন।
            </p>
          </div>
        ) : (
          messages.map((msg) => {
            const isMe = msg.senderId === currentUserId;
            const timeStr = new Date(msg.createdAt).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            });

            // Compose authenticated attachment streaming URL
            const rawAttachmentUrl =
              msg.attachmentUrl ||
              (msg.attachmentFilename
                ? `/api/v1/conversations/${conversation.id}/messages/${msg.id}/attachment`
                : null);
            const authenticatedAttachmentUrl =
              rawAttachmentUrl && token
                ? `${rawAttachmentUrl}?token=${encodeURIComponent(token)}`
                : rawAttachmentUrl;

            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isMe ? 'items-end' : 'items-start'} max-w-[85%] sm:max-w-[75%] ${
                  isMe ? 'ml-auto' : 'mr-auto'
                }`}
              >
                {!isMe && (
                  <span className="text-[11px] text-slate-500 mb-1 px-1 font-medium">
                    {msg.senderName}
                  </span>
                )}
                <div
                  className={`p-3 rounded-2xl text-sm leading-relaxed overflow-hidden ${
                    isMe
                      ? 'bg-emerald-600 text-white rounded-br-xs shadow-xs'
                      : 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-xs shadow-xs'
                  }`}
                >
                  {/* Image Attachment Rendering */}
                  {authenticatedAttachmentUrl && (
                    <div className="mb-2 relative group overflow-hidden rounded-xl bg-slate-950/10">
                      <img
                        src={authenticatedAttachmentUrl}
                        alt="সংযুক্ত ছবি"
                        onClick={() => setPreviewModalUrl(authenticatedAttachmentUrl)}
                        className="max-h-56 sm:max-h-64 w-full object-cover rounded-xl cursor-pointer hover:opacity-95 transition-opacity"
                        loading="lazy"
                      />
                      <button
                        type="button"
                        onClick={() => setPreviewModalUrl(authenticatedAttachmentUrl)}
                        className="absolute bottom-2 right-2 px-2 py-1 bg-black/60 hover:bg-black/90 text-white text-[10px] rounded-md backdrop-blur-xs flex items-center gap-1 opacity-90 group-hover:opacity-100 transition-opacity"
                      >
                        <Maximize2 className="w-3 h-3" />
                        বড় করে দেখুন
                      </button>
                    </div>
                  )}

                  {/* Text Message Content */}
                  {msg.content ? (
                    <p className="whitespace-pre-wrap break-words">{msg.content}</p>
                  ) : !authenticatedAttachmentUrl ? (
                    <p className="italic text-xs opacity-75">ছবি লোড হচ্ছে বা অনুপলব্ধ...</p>
                  ) : null}
                </div>

                {/* Timestamp and Read Status */}
                <div className="flex items-center gap-1 mt-1 px-1 text-[10px] text-slate-400">
                  <span>{timeStr}</span>
                  {isMe && (
                    <span>
                      {msg.isRead ? (
                        <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <Check className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </span>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Selected Image Attachment Preview Chip */}
      {selectedFile && selectedFilePreview && (
        <div className="px-4 py-2.5 bg-emerald-50/80 border-t border-emerald-100/90 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <img
              src={selectedFilePreview}
              alt="Selected preview"
              className="w-11 h-11 object-cover rounded-xl border border-emerald-300 shadow-xs shrink-0"
            />
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-800 truncate">
                {selectedFile.name}
              </p>
              <p className="text-[10px] text-emerald-700 font-medium">
                {(selectedFile.size / 1024).toFixed(0)} KB • পাঠানোর জন্য প্রস্তুত
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleRemoveFile}
            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-xl transition-colors shrink-0"
            title="ছবি বাতিল করুন"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Anti-Spam or System Error Notification */}
      {error && (
        <div className="mx-4 my-2 p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Hidden File Input for Image Attachments */}
      <input
        type="file"
        ref={fileInputRef}
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Message Input Box with Attachment Trigger */}
      <form
        onSubmit={handleSend}
        className="p-3 bg-white border-t border-slate-200/80 flex items-center gap-2"
      >
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={sending}
          title="ছবি বা নমুনা সংযুক্ত করুন (JPEG, PNG, WebP)"
          className="p-2.5 text-slate-500 hover:text-emerald-700 hover:bg-emerald-50 rounded-xl transition-colors disabled:opacity-50 shrink-0"
        >
          <ImageIcon className="w-5 h-5" />
        </button>

        <input
          type="text"
          placeholder={selectedFile ? "ছবির সাথে ক্যাপশন লিখুন (ঐচ্ছিক)..." : "এখানে আপনার বার্তা লিখুন..."}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={sending}
          className="flex-1 px-4 py-2.5 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
        />

        <Button
          type="submit"
          variant="primary"
          disabled={(!inputText.trim() && !selectedFile) || sending}
          className="px-4 py-2.5 shrink-0 flex items-center gap-1.5"
        >
          <Send className="w-4 h-4" />
          <span className="hidden sm:inline">{sending ? 'পাঠানো হচ্ছে...' : 'পাঠান'}</span>
        </Button>
      </form>

      {/* Fullscreen Image Lightbox Preview Modal */}
      {previewModalUrl && (
        <div
          className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xs flex items-center justify-center p-4"
          onClick={() => setPreviewModalUrl(null)}
        >
          <div
            className="relative max-w-4xl max-h-[92vh] bg-slate-950 rounded-2xl overflow-hidden shadow-2xl flex flex-col items-center"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setPreviewModalUrl(null)}
              className="absolute top-3 right-3 p-2 bg-black/60 hover:bg-black/90 text-white rounded-full transition-colors z-10"
              title="বন্ধ করুন"
            >
              <X className="w-5 h-5" />
            </button>
            <img
              src={previewModalUrl}
              alt="বড় আকারের ছবি"
              className="max-h-[85vh] max-w-full object-contain p-2"
            />
          </div>
        </div>
      )}
    </div>
  );
};

