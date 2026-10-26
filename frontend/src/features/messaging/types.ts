/**
 * Messaging, 1-to-1 Farmer-Buyer Chat, and Moderation types.
 * Strictly complies with:
 * - AGENTS.md Rule 12: Object-level authorization policy (only conversation participants).
 * - AGENTS.md Rule 26: Redact sensitive coordinates and private messages in audit.
 * - AGENTS.md Rule 27: Rate limiting, blocking, and abuse reporting.
 */

export interface ConversationItem {
  id: string;
  participant1Id: string;
  participant1Name: string;
  participant2Id: string;
  participant2Name: string;
  contextType?: string | null;
  contextId?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface MessageItem {
  id: string;
  conversationId: string;
  senderId: string;
  senderName: string;
  content?: string;
  attachmentFilename?: string | null;
  attachmentUrl?: string | null;
  isRead: boolean;
  createdAt: string;
}

export interface ConversationCreateInput {
  recipientId: string;
  contextType?: string;
  contextId?: string;
  initialMessage?: string;
}

export interface ModerationReportInput {
  reportedUserId: string;
  contentType: 'user' | 'crop_listing' | 'equipment' | 'message';
  contentId: string;
  reason: string;
  details?: string;
}

export interface ModerationReportItem {
  id: string;
  reporterId: string;
  reportedUserId: string;
  contentType: string;
  contentId: string;
  reason: string;
  details?: string | null;
  status: string;
  createdAt: string;
}
