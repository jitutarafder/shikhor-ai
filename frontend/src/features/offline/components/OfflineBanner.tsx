import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { WifiOff, RefreshCw, Layers } from 'lucide-react';
import { subscribeSyncState } from '../syncEngine';

export const OfflineBanner: React.FC = () => {
  const [isOnline, setIsOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true
  );
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    const unsubscribe = subscribeSyncState((count, online) => {
      setPendingCount(count);
      setIsOnline(online);
    });
    return unsubscribe;
  }, []);

  if (isOnline && pendingCount === 0) {
    return null;
  }

  return (
    <div
      className={`w-full py-2.5 px-4 text-xs font-medium flex items-center justify-between transition-colors z-30 ${
        !isOnline
          ? 'bg-amber-500 text-slate-950 shadow-xs'
          : 'bg-emerald-700 text-white'
      }`}
    >
      <div className="max-w-7xl mx-auto w-full flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {!isOnline ? (
            <WifiOff className="w-4 h-4 shrink-0 text-slate-950 animate-pulse" />
          ) : (
            <RefreshCw className="w-4 h-4 shrink-0 animate-spin" />
          )}
          <span>
            {!isOnline
              ? 'ইন্টারনেট সংযোগ বিচ্ছিন্ন (অফলাইন মোড)। আপনার তথ্য ডিভাইসে সংরক্ষিত আছে এবং সংযোগ ফিরলে স্বয়ংক্রিয়ভাবে সিঙ্ক হবে।'
              : 'ইন্টারনেট সংযোগ সচল। অপেক্ষমাণ অফলাইন কার্যক্রম সিঙ্ক করা হচ্ছে...'}
          </span>
        </div>

        {pendingCount > 0 && (
          <Link
            to="/app/sync-queue"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-black/10 hover:bg-black/20 font-bold transition-colors shrink-0"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>{pendingCount}টি অপেক্ষমাণ কার্যক্রম দেখুন</span>
          </Link>
        )}
      </div>
    </div>
  );
};
