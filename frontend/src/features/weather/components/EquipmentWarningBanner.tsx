import React from 'react';
import { AlertTriangle, ShieldAlert } from 'lucide-react';
import { MachineryWeatherWarning } from '../types';

interface EquipmentWarningBannerProps {
  warnings: MachineryWeatherWarning[];
}

export const EquipmentWarningBanner: React.FC<EquipmentWarningBannerProps> = ({ warnings }) => {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="space-y-3">
      {warnings.map((warn, idx) => (
        <div
          key={idx}
          className={`p-4 rounded-card border flex items-start gap-3.5 shadow-sm ${
            warn.warningLevel === 'alert'
              ? 'bg-danger-600/10 border-danger-600/30 text-danger-600'
              : 'bg-paddy-400/20 border-paddy-400/30 text-soil-700'
          }`}
        >
          {warn.warningLevel === 'alert' ? (
            <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
          )}

          <div className="space-y-1 text-xs">
            <h4 className="font-bold text-sm">{warn.titleBn}</h4>
            <p className="leading-relaxed">{warn.messageBn}</p>
            {warn.affectedEquipment.length > 0 && (
              <span className="inline-block mt-1 font-semibold text-[11px] opacity-90">
                প্রভাবিত কৃষিযন্ত্র: {warn.affectedEquipment.join(', ')}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};
