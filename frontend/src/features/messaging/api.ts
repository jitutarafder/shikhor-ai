import {
  ConversationCreateInput,
  ConversationItem,
  MessageItem,
  ModerationReportInput,
  ModerationReportItem,
} from './types';

export async function getMyConversationsApi(token: string): Promise<ConversationItem[]> {
  const res = await fetch('/api/v1/conversations', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'কথোপকথন তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function createConversationApi(
  token: string,
  input: ConversationCreateInput
): Promise<ConversationItem> {
  const res = await fetch('/api/v1/conversations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'বার্তা শুরু করা সম্ভব হয়নি।');
  }
  return data;
}

export async function getConversationMessagesApi(
  token: string,
  conversationId: string
): Promise<MessageItem[]> {
  const res = await fetch(`/api/v1/conversations/${conversationId}/messages`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'বার্তাগুলো লোড করা সম্ভব হয়নি।');
  }
  return data;
}

export async function sendMessageApi(
  token: string,
  conversationId: string,
  content: string
): Promise<MessageItem> {
  const res = await fetch(`/api/v1/conversations/${conversationId}/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'বার্তা পাঠানো সম্ভব হয়নি।');
  }
  return data;
}

export async function sendMessageWithAttachmentApi(
  token: string,
  conversationId: string,
  file: File,
  content?: string
): Promise<MessageItem> {
  const formData = new FormData();
  formData.append('image', file);
  if (content && content.trim()) {
    formData.append('content', content.trim());
  }
  const res = await fetch(`/api/v1/conversations/${conversationId}/messages/attachment`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ছবিসহ বার্তা পাঠানো সম্ভব হয়নি।');
  }
  return data;
}

export async function blockUserApi(token: string, targetUserId: string): Promise<void> {
  const res = await fetch('/api/v1/users/block', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ targetUserId }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ব্যবহারকারীকে ব্লক করা সম্ভব হয়নি।');
  }
}

export async function reportUserApi(
  token: string,
  input: ModerationReportInput
): Promise<ModerationReportItem> {
  const res = await fetch('/api/v1/reports', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'অভিযোগ দাখিল করা সম্ভব হয়নি।');
  }
  return data;
}
