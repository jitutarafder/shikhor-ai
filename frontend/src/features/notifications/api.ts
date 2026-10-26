/**
 * Notification API client functions.
 */

import { NotificationItem, UnreadCountResponse } from './types';

export async function getNotificationsApi(
  token: string,
  unreadOnly = false
): Promise<NotificationItem[]> {
  const query = unreadOnly ? '?unreadOnly=true' : '';
  const res = await fetch(`/api/v1/notifications${query}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'বিজ্ঞপ্তি লোড করা যায়নি।');
  }
  return data;
}

export async function getUnreadNotificationCountApi(
  token: string
): Promise<UnreadCountResponse> {
  const res = await fetch('/api/v1/notifications/unread-count', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'অপঠিত নোটিফিকেশন সংখ্যা পাওয়া যায়নি।');
  }
  return data;
}

export async function markNotificationReadApi(
  token: string,
  notificationId: string
): Promise<NotificationItem> {
  const res = await fetch(`/api/v1/notifications/${notificationId}/read`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'বিজ্ঞপ্তি পঠিত চিহ্নিত করা যায়নি।');
  }
  return data;
}

export async function markAllNotificationsReadApi(
  token: string
): Promise<{ markedCount: number }> {
  const res = await fetch('/api/v1/notifications/read-all', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'সব বিজ্ঞপ্তি পঠিত চিহ্নিত করা যায়নি।');
  }
  return data;
}
