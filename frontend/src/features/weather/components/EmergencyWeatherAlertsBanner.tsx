import React from 'react';
import {
  AlertTriangle,
  CloudRain,
  Wind,
  Sun,
  Droplets,
  Zap,
  BellRing,
  Info,
} from 'lucide-react';
import { EmergencyWeatherAlertsResponse } from '../types';

interface EmergencyWeatherAlertsBannerProps {
  alertsData: EmergencyWeatherAlertsResponse | null;
  isLoading: boolean;
  onRefresh?: () => void;
  onGpsDetect?: () => void;
  locationName?: string;
}

export const EmergencyWeatherAlertsBanner: React.FC<EmergencyWeatherAlertsBannerProps> = ({
  alertsData,
  isLoading,
}) => {
  if (isLoading && !alertsData) {
    return null;
  }

  // Only render banner if there are active urgent alerts
  if (!alertsData || !alertsData.hasUrgentAlert || alertsData.alerts.length === 0) {
    return null;
  }

  const getAlertIcon = (iconType: string, severity: string) => {
    const className = `w-5 h-5 shrink-0 ${
      severity === 'danger'
        ? 'text-rose-600'
        : severity === 'warning'
        ? 'text-amber-600'
        : 'text-sky-600'
    }`;

    switch (iconType) {
      case 'wind':
        return <Wind className={className} />;
      case 'rain':
        return <CloudRain className={className} />;
      case 'sun':
        return <Sun className={className} />;
      case 'droplet':
        return <Droplets className={className} />;
      case 'zap':
        return <Zap className={className} />;
      default:
        return severity === 'danger' ? (
          <AlertTriangle className={className} />
        ) : (
          <Info className={className} />
        );
    }
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'danger':
        return 'bg-rose-50 border-rose-200 text-rose-950';
      case 'warning':
        return 'bg-amber-50 border-amber-200 text-amber-950';
      default:
        return 'bg-sky-50 border-sky-200 text-sky-950';
    }
  };

  const urgentAlerts = alertsData.alerts.filter((a) => a.severity === 'danger' || a.severity === 'warning');

  if (urgentAlerts.length === 0) return null;

  return (
    <div className="p-4 sm:p-5 rounded-2xl border border-rose-200 bg-gradient-to-r from-rose-50/90 via-amber-50/40 to-rose-50/60 shadow-soft space-y-3.5 animate-fadeIn">
      {/* Alert Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center shrink-0">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-extrabold text-sm sm:text-base text-rose-950">
              জরুরি স্প্রে ও সেচ সতর্কতা
            </h3>
            <p className="text-[11px] text-rose-800">
              বৃষ্টি বা বৈরী আবহাওয়ার কারণে কৃষিকাজে ক্ষতি এড়াতে নিচের পরামর্শ মেনে চলুন
            </p>
          </div>
        </div>

        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 border border-rose-200 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-600 animate-ping" />
          সতর্কতা সক্রিয়
        </span>
      </div>

      {alertsData.notificationDispatched && (
        <div className="px-3 py-1.5 bg-canvas/80 border border-rose-200 rounded-xl text-xs text-rose-800 font-medium flex items-center gap-2">
          <BellRing className="w-3.5 h-3.5 text-rose-600 shrink-0" />
          <span>আপনার অ্যাকাউন্টে স্বয়ংক্রিয় নোটিফিকেশন এলার্ট পাঠানো হয়েছে।</span>
        </div>
      )}

      {/* Alert Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {urgentAlerts.map((alert, idx) => (
          <div
            key={idx}
            className={`p-3.5 rounded-xl border ${getSeverityStyle(alert.severity)} space-y-2 text-xs`}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                {getAlertIcon(alert.iconType, alert.severity)}
                <h4 className="font-bold text-sm text-ink-900">{alert.titleBn}</h4>
              </div>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                  alert.severity === 'danger'
                    ? 'bg-rose-200 text-rose-900'
                    : 'bg-amber-200 text-amber-900'
                }`}
              >
                {alert.severity === 'danger' ? 'জরুরি স্থগিত' : 'সতর্কতা'}
              </span>
            </div>

            <p className="text-xs text-ink-800 leading-relaxed">{alert.messageBn}</p>

            <div className="pt-2 border-t border-slate-900/10 flex items-start gap-1 font-bold text-forest-900">
              <span className="shrink-0">👉 করণীয়:</span>
              <span>{alert.actionGuidanceBn}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
