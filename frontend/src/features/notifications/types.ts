/**
 * In-app Notification types.
 */

export interface NotificationItem {
  id: string;
  userId: string;
  title: string;
  message: string;
  notificationType: string;
  link?: string | null;
  isRead: boolean;
  createdAt: string;
}

export interface UnreadCountResponse {
  unreadCount: number;
}
