import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  MapPin,
  Sprout,
  CheckSquare,
  AlertTriangle,
  ShieldCheck,
  Loader2,
  CheckCircle2,
} from 'lucide-react';
import { PilotDistrictCropConfig } from '../features/pilot/types';
import { getPilotConfigApi } from '../features/pilot/api';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';

export const UserGuide: React.FC = () => {
  const [config, setConfig] = useState<PilotDistrictCropConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [checkedSteps, setCheckedSteps] = useState<Record<number, boolean>>({});

  useEffect(() => {
    getPilotConfigApi()
      .then((data) => setConfig(data))
      .catch(() => { })
      .finally(() => setLoading(false));
  }, []);

  const toggleStep = (idx: number) => {
    setCheckedSteps((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Top Header & Breadcrumb */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-line-200">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-forest-900 text-emerald-300 flex items-center justify-center shadow-soft">
            <BookOpen className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl sm:text-3xl font-black text-forest-900">
              শিখড় এআই ব্যবহার সহায়িকা
            </h1>
            <p className="text-xs sm:text-sm text-ink-600 font-medium">
              সহজে ও নিরাপদে সকল সেবা গ্রহণের সম্পূর্ণ গাইড ও প্রস্তুতি তালিকা
            </p>
          </div>
        </div>


      </div>

      {loading ? (
        <div className="py-24 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-forest-700 animate-spin mx-auto" />
          <p className="text-sm text-ink-600 font-medium">সহায়িকা ও তথ্য লোড হচ্ছে...</p>
        </div>
      ) : config ? (
        <div className="space-y-8">
          {/* Important Advisory Banner */}
          <div className="bg-amber-50 border border-amber-200 rounded-3xl p-5 sm:p-6 shadow-soft flex items-start gap-4">
            <div className="w-10 h-10 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="font-extrabold text-base text-amber-950">
                গুরুত্বপূর্ণ সেবা দিকনির্দেশনা ও সতর্কতা
              </h3>
              <p className="text-xs sm:text-sm text-amber-900/90 leading-relaxed">
                {config.ai_limitations_notice}
              </p>
            </div>
          </div>

          {/* Supported Districts & Crops Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Districts Card */}
            <Card className="p-6 border-line-200 bg-canvas space-y-4 shadow-soft">
              <div className="flex items-center gap-2.5 pb-3 border-b border-line-200">
                <div className="w-9 h-9 rounded-xl bg-field-wash flex items-center justify-center text-forest-700">
                  <MapPin className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-forest-900">
                    বর্তমানে সেবা প্রাপ্তির জেলাসমূহ
                  </h3>
                  <p className="text-xs text-ink-600">যেসব এলাকায় প্রাথমিক মাঠ সেবা পুরোপুরি সক্রিয়</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 pt-1">
                {config.approved_districts.map((d) => (
                  <Badge
                    key={d.code}
                    variant="info"
                    className="text-xs font-bold py-1.5 px-3 rounded-xl border border-sky-200 bg-sky-50 text-sky-900"
                  >
                    📍 {d.name_bn}
                  </Badge>
                ))}
              </div>
            </Card>

            {/* Crops Card */}
            <Card className="p-6 border-line-200 bg-canvas space-y-4 shadow-soft">
              <div className="flex items-center gap-2.5 pb-3 border-b border-line-200">
                <div className="w-9 h-9 rounded-xl bg-field-wash flex items-center justify-center text-emerald-700">
                  <Sprout className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-forest-900">
                    সমর্থিত প্রধান ফসলসমূহ
                  </h3>
                  <p className="text-xs text-ink-600">যেসব ফসলের রোগ নির্ণয় ও তথ্য বিশেষায়িতভাবে প্রস্তুত</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 pt-1">
                {config.approved_crops.map((c) => {
                  const cleanName = c.name_bn.split('(')[0].trim();
                  return (
                    <Badge
                      key={c.code}
                      variant="success"
                      className="text-xs font-bold py-1.5 px-3 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-900"
                    >
                      🌾 {cleanName}
                    </Badge>
                  );
                })}
              </div>
            </Card>
          </div>

          {/* Getting Started Interactive Checklist */}
          <div className="bg-canvas border border-line-200 rounded-3xl p-6 sm:p-8 shadow-soft space-y-5">
            <div className="flex items-center justify-between gap-3 pb-3 border-b border-line-200">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-field-wash flex items-center justify-center text-forest-700">
                  <CheckSquare className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg sm:text-xl font-bold text-forest-900">
                    সেবা গ্রহণের প্রস্তুতি তালিকা (Step-by-step Checklist)
                  </h2>
                  <p className="text-xs text-ink-600">
                    প্রতিটি ধাপ সম্পন্ন করে সহজে সঠিক ফলাফল উপভোগ করুন
                  </p>
                </div>
              </div>

              <span className="text-xs font-bold px-3 py-1 bg-field-wash text-forest-800 rounded-full border border-line-200">
                {Object.values(checkedSteps).filter(Boolean).length} / {config.onboarding_checklist.length} সম্পন্ন
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {config.onboarding_checklist.map((item, idx) => {
                const isChecked = !!checkedSteps[idx];
                return (
                  <div
                    key={idx}
                    onClick={() => toggleStep(idx)}
                    className={`p-4 rounded-2xl border text-sm cursor-pointer transition-all flex items-start gap-3.5 ${isChecked
                      ? 'bg-emerald-50/80 border-emerald-300 text-forest-900 shadow-sm'
                      : 'bg-surface border-line-200 hover:border-forest-700/40 text-ink-900'
                      }`}
                  >
                    <div
                      className={`w-5 h-5 rounded-lg border flex items-center justify-center shrink-0 mt-0.5 transition-colors ${isChecked
                        ? 'bg-forest-700 border-forest-700 text-white'
                        : 'border-line-200 bg-white'
                        }`}
                    >
                      {isChecked && <CheckCircle2 className="w-4 h-4 text-white" />}
                    </div>

                    <div className="space-y-1">
                      <h4 className="font-bold text-sm text-forest-900">{item.step}</h4>
                      <p className="text-xs text-ink-600 leading-relaxed">{item.desc_bn}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : null}

      {/* Bottom Footer Note */}
      <div className="pt-4 border-t border-line-200 flex items-center justify-between text-xs text-ink-600">
        <span className="flex items-center gap-1.5 font-medium">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>শিখড় এআই — বাংলাদেশের কৃষকদের পাশে নির্ভরযোগ্য ডিজিটাল প্রযুক্তি</span>
        </span>

      </div>
    </div>
  );
};
