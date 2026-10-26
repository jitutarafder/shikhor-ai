import React from 'react';
import {
  Droplets,
  CloudRain,
  Wind,
  Clock,
  Compass,
  Building2,
  AlertCircle,
} from 'lucide-react';
import { WeatherFact, WeatherLocation } from '../types';

interface WeatherFactCardProps {
  facts: WeatherFact;
  location: WeatherLocation;
  providerName: string;
  attribution: string;
  providerTimestamp: string;
  isStale: boolean;
  staleReason?: string | null;
}

export const WeatherFactCard: React.FC<WeatherFactCardProps> = ({
  facts,
  location,
  providerName,
  attribution,
  providerTimestamp,
  isStale,
  staleReason,
}) => {
  return (
    <div className="p-5 sm:p-6 rounded-3xl border border-line-200 bg-canvas space-y-5 shadow-soft">
      {/* Fact header with metadata & Rule 20 isolation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-line-200">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-extrabold uppercase tracking-wider text-forest-800 bg-leaf-100/90 px-2.5 py-0.5 rounded-full border border-leaf-200">
              আবহাওয়া পর্যবেক্ষণ তথ্য (Facts)
            </span>
            {isStale && (
              <span className="text-[11px] font-bold text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded-full border border-rose-200 flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                <span>সংরক্ষিত / অফলাইন তথ্য</span>
              </span>
            )}
          </div>
          <h2 className="text-xl sm:text-2xl font-black text-forest-900">
            {location.district ? `${location.district}${location.upazila ? `, ${location.upazila}` : ''}` : 'বর্তমান অবস্থান'}
          </h2>
        </div>

        <div className="text-xs text-ink-600 sm:text-right space-y-0.5">
          <div className="flex items-center sm:justify-end gap-1.5 font-medium">
            <Clock className="w-3.5 h-3.5 text-forest-700" />
            <span>
              আপডেট: {new Date(providerTimestamp).toLocaleTimeString('bn-BD', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
          <p className="text-[11px] text-ink-500">
            উৎস: <span className="font-semibold text-ink-700">{providerName}</span>
          </p>
        </div>
      </div>

      {isStale && staleReason && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-900 font-medium">
          <strong>সতর্কতা:</strong> {staleReason}
        </div>
      )}

      {/* Main Temperature and Weather Metrics Strip */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-center bg-field-wash p-5 sm:p-6 rounded-2xl border border-line-200/80">
        {/* Left: Temp & Condition */}
        <div className="lg:col-span-4 space-y-1">
          <div className="flex items-baseline gap-2">
            <span className="text-5xl sm:text-6xl font-black text-forest-900 font-mono tracking-tight">
              {Math.round(facts.temperatureC)}°
            </span>
            <span className="text-xs sm:text-sm font-semibold text-ink-600 bg-surface px-2.5 py-1 rounded-full border border-line-200">
              অনুভূত: <strong className="text-forest-900">{Math.round(facts.feelsLikeC)}°C</strong>
            </span>
          </div>
          <p className="text-lg font-bold text-forest-800">
            {facts.weatherDescriptionBn}
          </p>
        </div>

        {/* Right: 4 Metrics Grid */}
        <div className="lg:col-span-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="p-3.5 bg-canvas rounded-2xl border border-line-200 shadow-sm space-y-1">
            <span className="text-[11px] font-bold text-ink-600 flex items-center gap-1.5">
              <Droplets className="w-3.5 h-3.5 text-sky-600" />
              <span>আর্দ্রতা</span>
            </span>
            <span className="text-lg font-extrabold text-ink-900 block">
              {facts.relativeHumidity}%
            </span>
          </div>

          <div className="p-3.5 bg-canvas rounded-2xl border border-line-200 shadow-sm space-y-1">
            <span className="text-[11px] font-bold text-ink-600 flex items-center gap-1.5">
              <CloudRain className="w-3.5 h-3.5 text-sky-600" />
              <span>বৃষ্টির সম্ভাবনা</span>
            </span>
            <span className="text-lg font-extrabold text-ink-900 block">
              {facts.precipitationProbability}%
            </span>
          </div>

          <div className="p-3.5 bg-canvas rounded-2xl border border-line-200 shadow-sm space-y-1">
            <span className="text-[11px] font-bold text-ink-600 flex items-center gap-1.5">
              <Wind className="w-3.5 h-3.5 text-forest-700" />
              <span>বাতাস</span>
            </span>
            <span className="text-lg font-extrabold text-ink-900 block">
              {facts.windSpeedKmh} <span className="text-xs font-medium text-ink-600">কিমি/ঘ</span>
            </span>
          </div>

          <div className="p-3.5 bg-canvas rounded-2xl border border-line-200 shadow-sm space-y-1">
            <span className="text-[11px] font-bold text-ink-600 flex items-center gap-1.5">
              <Compass className="w-3.5 h-3.5 text-forest-700" />
              <span>দমকা হাওয়া</span>
            </span>
            <span className="text-lg font-extrabold text-ink-900 block">
              {facts.windGustKmh} <span className="text-xs font-medium text-ink-600">কিমি/ঘ</span>
            </span>
          </div>
        </div>
      </div>

      {/* Attribution footer (Rule 20) */}
      <div className="text-[11px] text-ink-500 flex items-center gap-1.5">
        <Building2 className="w-3.5 h-3.5 text-forest-700 shrink-0" />
        <span>{attribution}</span>
      </div>
    </div>
  );
};
