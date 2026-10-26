import React from 'react';
import {
  Sparkles,
  Scissors,
  Waves,
  Tractor,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from 'lucide-react';
import { ActivityRecommendation, ActivityType, SuitabilityLevel } from '../types';

interface ActivityWindowCardProps {
  recommendation: ActivityRecommendation;
}

export const ActivityWindowCard: React.FC<ActivityWindowCardProps> = ({ recommendation }) => {
  const iconMap: Record<ActivityType, React.ReactNode> = {
    spraying: <Sparkles className="w-5 h-5 text-forest-700" />,
    harvesting: <Scissors className="w-5 h-5 text-soil-700" />,
    irrigation: <Waves className="w-5 h-5 text-sky-600" />,
    machinery: <Tractor className="w-5 h-5 text-paddy-500" />,
  };

  const statusConfig: Record<
    SuitabilityLevel,
    {
      label: string;
      bgClass: string;
      borderClass: string;
      badgeClass: string;
      icon: React.ReactNode;
    }
  > = {
    suitable: {
      label: 'অনুকূল সময়',
      bgClass: 'bg-emerald-50/50',
      borderClass: 'border-emerald-200 hover:border-emerald-300',
      badgeClass: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
    },
    caution: {
      label: 'সতর্কতা অবলম্বন',
      bgClass: 'bg-amber-50/50',
      borderClass: 'border-amber-200 hover:border-amber-300',
      badgeClass: 'bg-amber-100 text-amber-900 border-amber-200',
      icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
    },
    unfavorable: {
      label: 'অনুপযুক্ত / স্থগিত',
      bgClass: 'bg-rose-50/50',
      borderClass: 'border-rose-200 hover:border-rose-300',
      badgeClass: 'bg-rose-100 text-rose-800 border-rose-200',
      icon: <XCircle className="w-4 h-4 text-rose-600" />,
    },
  };

  const config = statusConfig[recommendation.suitability] || statusConfig.suitable;

  return (
    <div
      className={`p-5 rounded-2xl border ${config.borderClass} ${config.bgClass} bg-canvas shadow-soft transition-all space-y-3.5 flex flex-col justify-between`}
    >
      <div className="space-y-3">
        {/* Header: Icon + Title + Status Badge */}
        <div className="flex items-center justify-between gap-3 pb-2.5 border-b border-line-200/80">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-surface flex items-center justify-center border border-line-200 shrink-0">
              {iconMap[recommendation.activityType]}
            </div>
            <h3 className="text-base font-bold text-forest-900">{recommendation.titleBn}</h3>
          </div>

          <span
            className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full border shrink-0 ${config.badgeClass}`}
          >
            {config.icon}
            <span>{config.label}</span>
          </span>
        </div>

        {/* Situation overview */}
        <p className="text-xs text-ink-700 leading-relaxed">
          {recommendation.reasonSummaryBn}
        </p>
      </div>

      {/* Actionable Guidance & Risk Warning */}
      <div className="space-y-2 pt-1">
        <div className="p-3 bg-canvas/90 rounded-xl border border-line-200/80 text-xs space-y-1">
          <span className="font-bold text-forest-800 flex items-center gap-1">
            <span>👉 করণীয় পরামর্শ:</span>
          </span>
          <p className="text-ink-800 leading-relaxed">{recommendation.guidanceBn}</p>
        </div>

        {recommendation.riskFactors.length > 0 && (
          <div className="px-3 py-2 bg-rose-50 border border-rose-200 rounded-xl text-[11px] text-rose-800 flex items-start gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600 shrink-0 mt-0.5" />
            <span className="leading-snug">
              <strong>ঝুঁকি:</strong> {recommendation.riskFactors.join('; ')}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

