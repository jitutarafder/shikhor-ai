import React, { useState, useEffect } from 'react';
import { PilotDistrictCropConfig } from '../types';
import { getPilotConfigApi } from '../api';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import {
  BookOpen,
  CheckSquare,
  AlertTriangle,
  X,
  MapPin,
  Sprout,
  ShieldCheck,
} from 'lucide-react';

interface PilotOnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PilotOnboardingModal: React.FC<PilotOnboardingModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [config, setConfig] = useState<PilotDistrictCropConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkedSteps, setCheckedSteps] = useState<Record<number, boolean>>({});

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      if (!config) {
        setLoading(true);
        getPilotConfigApi()
          .then((data) => setConfig(data))
          .catch(() => {})
          .finally(() => setLoading(false));
      }
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, config]);

  if (!isOpen) return null;

  const toggleStep = (idx: number) => {
    setCheckedSteps((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-3 sm:p-6 animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="bg-canvas border border-line-200 rounded-3xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Fixed Header */}
        <div className="shrink-0 flex items-start justify-between gap-4 border-b border-line-200 p-5 sm:p-6 bg-canvas">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-forest-900 text-emerald-300">
              <BookOpen className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-black text-forest-900">
                শিখড় এআই ব্যবহার সহায়িকা
              </h2>
              <p className="text-xs text-ink-600 font-medium">
                সঠিক ও কার্যকর সেবা পেতে প্রাথমিক দিকনির্দেশনা ও প্রস্তুতি তালিকা
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-ink-500 hover:text-forest-900 p-2 rounded-xl hover:bg-canvas-subtle transition-colors shrink-0"
            title="বন্ধ করুন"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="overflow-y-auto flex-1 p-5 sm:p-6 space-y-6 scrollbar-thin">
          {loading ? (
            <div className="py-16 text-center text-ink-600 font-medium">সহায়িকা লোড হচ্ছে...</div>
          ) : config ? (
            <div className="space-y-6">
              {/* AI Warning Box */}
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3 text-amber-950 shadow-sm">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs sm:text-sm leading-relaxed">
                  <span className="font-bold text-amber-900">গুরুত্বপূর্ণ পরামর্শ: </span>
                  {config.ai_limitations_notice}
                </div>
              </div>

              {/* Approved Focus Districts & Crops */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-field-wash border border-line-200 rounded-2xl p-4 space-y-2.5">
                  <div className="flex items-center gap-2 text-forest-900 font-bold text-sm">
                    <MapPin className="w-4 h-4 text-forest-700" />
                    <span>বর্তমানে সেবা প্রাপ্তির জেলাসমূহ</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {config.approved_districts.map((d) => (
                      <Badge key={d.code} variant="info" className="text-xs py-1 px-2.5 rounded-lg">
                        {d.name_bn}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div className="bg-field-wash border border-line-200 rounded-2xl p-4 space-y-2.5">
                  <div className="flex items-center gap-2 text-forest-900 font-bold text-sm">
                    <Sprout className="w-4 h-4 text-emerald-700" />
                    <span>সমর্থিত প্রধান ফসলসমূহ</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {config.approved_crops.map((c) => {
                      const cleanName = c.name_bn.split('(')[0].trim();
                      return (
                        <Badge key={c.code} variant="success" className="text-xs py-1 px-2.5 rounded-lg">
                          {cleanName}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Checklist */}
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-forest-900 flex items-center gap-2">
                  <CheckSquare className="w-4 h-4 text-forest-700" />
                  <span>সেবা গ্রহণের সহজ প্রস্তুতি তালিকা (Checklist)</span>
                </h3>
                <div className="space-y-2.5">
                  {config.onboarding_checklist.map((item, idx) => {
                    const isChecked = !!checkedSteps[idx];
                    return (
                      <div
                        key={idx}
                        onClick={() => toggleStep(idx)}
                        className={`p-3.5 rounded-2xl border text-sm cursor-pointer transition-all flex items-start gap-3 ${
                          isChecked
                            ? 'bg-emerald-50/70 border-emerald-300 text-forest-900 shadow-sm'
                            : 'bg-canvas border-line-200 hover:border-forest-700/50 text-ink-900'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="mt-1 w-4 h-4 rounded text-forest-700 focus:ring-forest-700 cursor-pointer"
                        />
                        <div className="space-y-0.5">
                          <div className="font-bold text-xs sm:text-sm text-forest-900">{item.step}</div>
                          <div className="text-xs text-ink-600 leading-relaxed">{item.desc_bn}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : null}
        </div>

        {/* Fixed Footer */}
        <div className="shrink-0 p-4 sm:p-6 border-t border-line-200 bg-surface/50 flex flex-col sm:flex-row items-center justify-between gap-3">
          <span className="text-xs text-ink-600 flex items-center gap-1.5 font-medium">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>কৃষকদের সর্বোচ্চ সহায়তা প্রদানে আমরা দায়বদ্ধ</span>
          </span>
          <Button variant="primary" size="md" onClick={onClose} className="w-full sm:w-auto px-6 shadow-sm">
            ঠিক আছে, শুরু করুন
          </Button>
        </div>
      </div>
    </div>
  );
};
