import React, { useEffect, useRef, useState } from 'react';
import { Bell, CheckCheck, ExternalLink, Loader2, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import {
  getNotificationsApi,
  getUnreadNotificationCountApi,
  markAllNotificationsReadApi,
  markNotificationReadApi,
} from '../api';
import { NotificationItem } from '../types';

export const NotificationBell: React.FC = () => {
  const { token, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);

  const dropdownRef = useRef<HTMLDivElement>(null);

  // Poll or fetch unread count on mount & every 30s
  useEffect(() => {
    if (!token || !isAuthenticated) {
      setUnreadCount(0);
      return;
    }

    let isMounted = true;
    const fetchCount = () => {
      getUnreadNotificationCountApi(token)
        .then((res) => {
          if (isMounted) setUnreadCount(res.unreadCount);
        })
        .catch(() => {});
    };

    fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [token, isAuthenticated]);

  // Fetch full notification list when dropdown opens
  useEffect(() => {
    if (isOpen && token) {
      setLoading(true);
      getNotificationsApi(token)
        .then((items) => {
          setNotifications(items);
          setLoading(false);
        })
        .catch(() => {
          setLoading(false);
        });
    }
  }, [isOpen, token]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleMarkAllRead = async () => {
    if (!token) return;
    try {
      await markAllNotificationsReadApi(token);
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
    } catch {
      // silently handle
    }
  };

  const handleNotificationClick = async (notif: NotificationItem) => {
    if (!notif.isRead && token) {
      try {
        await markNotificationReadApi(token, notif.id);
        setUnreadCount((c) => Math.max(0, c - 1));
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, isRead: true } : n))
        );
      } catch {
        // silently handle
      }
    }
    setIsOpen(false);
    if (notif.link) {
      navigate(notif.link);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="relative p-2 rounded-btn text-ink-700 hover:text-forest-900 hover:bg-surface/80 transition-colors focus:outline-none focus:ring-2 focus:ring-leaf-500/40 min-w-[40px] min-h-[40px] flex items-center justify-center"
        aria-label="বিজ্ঞপ্তি দেখুন"
        title="বিজ্ঞপ্তি"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 flex h-4 min-w-[16px] px-1 items-center justify-center rounded-full bg-danger-600 text-white text-[10px] font-bold ring-2 ring-canvas animate-pulse">
            {unreadCount > 9 ? '৯+' : unreadCount.toLocaleString('bn-BD')}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-card bg-canvas border border-line-200 shadow-float z-50 overflow-hidden animate-fadeIn text-left">
          {/* Header */}
          <div className="p-3.5 bg-surface border-b border-line-200 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-bold text-forest-900">বিজ্ঞপ্তিসমূহ</span>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-danger-50 text-danger-700 text-[11px] font-semibold border border-danger-200">
                  {unreadCount.toLocaleString('bn-BD')} টি নতুন
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllRead}
                className="text-xs text-forest-700 hover:text-forest-900 font-medium flex items-center gap-1 hover:underline"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>সব পঠিত</span>
              </button>
            )}
          </div>

          {/* Body */}
          <div className="max-h-80 overflow-y-auto divide-y divide-line-100">
            {loading ? (
              <div className="p-8 text-center text-xs text-ink-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-forest-700" />
                <span>বিজ্ঞপ্তি লোড হচ্ছে...</span>
              </div>
            ) : notifications.length === 0 ? (
              <div className="p-8 text-center text-xs text-ink-500 space-y-1">
                <Bell className="w-8 h-8 text-ink-300 mx-auto mb-2" />
                <p className="font-semibold text-ink-700">কোনো নতুন বিজ্ঞপ্তি নেই</p>
                <p>নতুন কোনো ফসলের সন্ধান বা আপডেট এলে এখানে দেখতে পাবেন।</p>
              </div>
            ) : (
              notifications.map((n) => (
                <button
                  key={n.id}
                  type="button"
                  onClick={() => handleNotificationClick(n)}
                  className={`w-full text-left p-3.5 transition-colors flex items-start gap-2.5 hover:bg-surface/70 ${
                    !n.isRead ? 'bg-leaf-50/40' : 'bg-canvas'
                  }`}
                >
                  <div className="mt-0.5 shrink-0">
                    {n.notificationType === 'weather_alert' ? (
                      <span className="w-7 h-7 rounded-full bg-amber-100 text-amber-900 border border-amber-300 flex items-center justify-center text-xs font-bold shadow-xs">
                        🌦️
                      </span>
                    ) : n.notificationType === 'crop_match' ? (
                      <span className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center text-xs font-bold">
                        🌾
                      </span>
                    ) : (
                      <span className="w-7 h-7 rounded-full bg-leaf-100 text-forest-800 flex items-center justify-center text-xs font-bold">
                        <Sparkles className="w-3.5 h-3.5" />
                      </span>
                    )}
                  </div>

                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center justify-between gap-1">
                      <h4
                        className={`text-xs font-bold line-clamp-1 ${
                          !n.isRead ? 'text-forest-900' : 'text-ink-700'
                        }`}
                      >
                        {n.title}
                      </h4>
                      {!n.isRead && (
                        <span className="w-2 h-2 rounded-full bg-leaf-500 shrink-0" />
                      )}
                    </div>

                    <p className="text-[12px] text-ink-600 line-clamp-2 leading-relaxed">
                      {n.message}
                    </p>

                    <div className="flex items-center justify-between pt-0.5 text-[10px] text-ink-500">
                      <span>
                        {new Date(n.createdAt).toLocaleDateString('bn-BD', {
                          day: 'numeric',
                          month: 'short',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                      {n.link && (
                        <span className="text-forest-700 font-semibold flex items-center gap-0.5">
                          <span>দেখুন</span>
                          <ExternalLink className="w-2.5 h-2.5" />
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
