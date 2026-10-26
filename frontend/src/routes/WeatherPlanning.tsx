import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CloudSun,
  MapPin,
  Calendar,
  Loader2,
  AlertCircle,
  RefreshCw,
  Tractor,
  ArrowRight,
  Sparkles,
  Navigation,
} from 'lucide-react';
import { WeatherPlanResponse } from '../features/weather/types';
import { checkEmergencyWeatherAlertsApi, getWeatherPlanApi } from '../features/weather/api';
import { WeatherFactCard } from '../features/weather/components/WeatherFactCard';
import { ActivityWindowCard } from '../features/weather/components/ActivityWindowCard';
import { EquipmentWarningBanner } from '../features/weather/components/EquipmentWarningBanner';
import { Button } from '../components/ui/Button';
import { useAuth } from '../features/auth/AuthContext';

interface DistrictCoord {
  name: string;
  lat: number;
  lon: number;
}

const POPULAR_DISTRICTS: DistrictCoord[] = [
  { name: 'বগুড়া', lat: 24.85, lon: 89.37 },
  { name: 'রংপুর', lat: 25.74, lon: 89.27 },
  { name: 'দিনাজপুর', lat: 25.62, lon: 88.63 },
  { name: 'রাজশাহী', lat: 24.37, lon: 88.60 },
  { name: 'ময়মনসিংহ', lat: 24.75, lon: 90.40 },
  { name: 'যশোর', lat: 23.16, lon: 89.21 },
  { name: 'কুমিল্লা', lat: 23.46, lon: 91.18 },
  { name: 'বরিশাল', lat: 22.70, lon: 90.36 },
];

export const WeatherPlanning: React.FC = () => {
  const { token } = useAuth();
  const [selectedDistrict, setSelectedDistrict] = useState<DistrictCoord>(POPULAR_DISTRICTS[0]);
  const [weatherPlan, setWeatherPlan] = useState<WeatherPlanResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isGpsDetecting, setIsGpsDetecting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeDayTab, setActiveDayTab] = useState<number>(0); // 0 = Today, 1 = Day 1, 2 = Day 2, 3 = Day 3

  const fetchWeather = async (coords: DistrictCoord) => {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const [planData] = await Promise.all([
        getWeatherPlanApi({
          latitude: coords.lat,
          longitude: coords.lon,
          district: coords.name,
        }),
        checkEmergencyWeatherAlertsApi(
          {
            latitude: coords.lat,
            longitude: coords.lon,
            district: coords.name,
            sendNotification: true,
          },
          token
        ),
      ]);
      setWeatherPlan(planData);
    } catch (err: any) {
      setErrorMsg(err.message || 'আবহাওয়ার পূর্বাভাস লোড করা যায়নি।');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGpsDetect = (showAlert = false) => {
    if (!navigator.geolocation) {
      if (showAlert) {
        alert('আপনার ব্রাউজারে জিপিএস সমর্থিত নয়।');
      }
      return;
    }
    setIsGpsDetecting(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsGpsDetecting(false);
        const customCoord: DistrictCoord = {
          name: 'জিপিএস অবস্থান',
          lat: pos.coords.latitude,
          lon: pos.coords.longitude,
        };
        setSelectedDistrict(customCoord);
      },
      () => {
        setIsGpsDetecting(false);
        if (showAlert) {
          alert('জিপিএস লোকেশন পাওয়া যায়নি বা অনুমতি দেওয়া হয়নি। পূর্বের জেলা বহাল রাখা হচ্ছে।');
        }
      },
      { timeout: 10000, enableHighAccuracy: false }
    );
  };

  // Attempt auto-acquisition of GPS location on mount
  useEffect(() => {
    handleGpsDetect(false);
  }, []);

  useEffect(() => {
    fetchWeather(selectedDistrict);
  }, [selectedDistrict]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-line-200">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-btn bg-sky-600/10 text-sky-600 flex items-center justify-center">
              <CloudSun className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-forest-900">কৃষি আবহাওয়া ও ৩ দিনের কর্মপরিকল্পনা</h1>
              <p className="text-xs text-ink-600">
                বৃষ্টি, বাতাস ও রোদের তথ্য বিশ্লেষণ করে স্প্রে, সেচ ও ফসল কাটার বিজ্ঞানসম্মত পরামর্শ
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/app/equipment">
            <Button variant="outline" size="sm" className="text-xs">
              <Tractor className="w-3.5 h-3.5 mr-1 text-forest-700" />
              <span>যন্ত্র বুকিংয়ে ফিরুন</span>
            </Button>
          </Link>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchWeather(selectedDistrict)}
            disabled={isLoading}
            className="text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            <span>রিফ্রেশ</span>
          </Button>
        </div>
      </div>

      {/* Location Bar */}
      <div className="bg-canvas border border-line-200 rounded-card p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-soft">
        <div className="flex items-center gap-2 text-xs font-semibold text-ink-900">
          <MapPin className="w-4 h-4 text-forest-700" />
          <span>এলাকা নির্বাচন করুন:</span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* GPS Button placed first */}
          <button
            onClick={() => handleGpsDetect(true)}
            disabled={isGpsDetecting}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-btn text-xs font-medium transition-colors border min-h-[38px] ${
              selectedDistrict.name === 'জিপিএস অবস্থান'
                ? 'bg-forest-700 text-canvas border-forest-700 shadow-sm font-bold'
                : 'bg-surface text-ink-700 border-line-200 hover:border-forest-700'
            }`}
          >
            <Navigation
              className={`w-3.5 h-3.5 ${
                isGpsDetecting
                  ? 'animate-spin text-forest-500'
                  : selectedDistrict.name === 'জিপিএস অবস্থান'
                  ? 'text-canvas'
                  : 'text-forest-700'
              }`}
            />
            <span>{isGpsDetecting ? 'জিপিএস খোঁজা হচ্ছে...' : 'বর্তমান জিপিএস'}</span>
          </button>

          {/* Popular Districts */}
          {POPULAR_DISTRICTS.map((d) => (
            <button
              key={d.name}
              onClick={() => setSelectedDistrict(d)}
              className={`px-3 py-1.5 rounded-btn text-xs font-medium transition-colors border min-h-[38px] ${
                selectedDistrict.name === d.name
                  ? 'bg-forest-700 text-canvas border-forest-700 shadow-sm font-bold'
                  : 'bg-surface text-ink-700 border-line-200 hover:border-forest-700'
              }`}
            >
              {d.name}
            </button>
          ))}
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 bg-danger-600/10 border border-danger-600/20 rounded-card text-xs text-danger-600 flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {isLoading ? (
        <div className="py-20 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-forest-700 animate-spin mx-auto" />
          <p className="text-sm text-ink-600">আবহাওয়ার পূর্বাভাস ও কৃষি পরামর্শ তৈরি করা হচ্ছে...</p>
        </div>
      ) : weatherPlan ? (
        <div className="space-y-8">
          {/* Equipment Warning Banners if any */}
          <EquipmentWarningBanner warnings={weatherPlan.equipmentWarnings} />

          {/* 1. Real-time Weather Facts (Rule 20: Isolated Provider Facts) */}
          <WeatherFactCard
            facts={weatherPlan.facts}
            location={weatherPlan.location}
            providerName={weatherPlan.providerName}
            attribution={weatherPlan.attribution}
            providerTimestamp={weatherPlan.providerTimestamp}
            isStale={weatherPlan.isStale}
            staleReason={weatherPlan.staleReason}
          />

          {/* 2. Agricultural Activity Planning Window (Rule 20: Isolated Recommendations) */}
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-line-200">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-forest-700" />
                <div>
                  <h2 className="text-lg font-bold text-forest-900">
                    কৃষি কাজের অনুকূলতা ও দিকনির্দেশনা
                  </h2>
                  <p className="text-xs text-ink-600">
                    আবহাওয়ার পূর্বাভাসের ওপর ভিত্তি করে বিজ্ঞানসম্মত সুপারিশমালা
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Verdict Ribbon for Today */}
            {weatherPlan.activityWindows && weatherPlan.activityWindows.length > 0 && (
              <div className="bg-canvas border border-line-200/90 rounded-2xl p-4 shadow-soft">
                <span className="text-[11px] font-bold text-ink-600 uppercase tracking-wider block mb-2.5">
                  আজকের জরুরি সিদ্ধান্ত সংক্ষেপ:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  {weatherPlan.activityWindows.map((act, idx) => {
                    const isOk = act.suitability === 'suitable';
                    const isWarn = act.suitability === 'caution';
                    const shortName = act.titleBn
                      .replace('স্প্রে কার্যক্রমের অনুকূলতা', 'কীটনাশক স্প্রে')
                      .replace('ফসল কাটার অনুকূলতা', 'ফসল কাটা')
                      .replace('সেচ কার্যক্রমের অনুকূলতা', 'সেচ প্রদান')
                      .replace('ভারী কৃষিযন্ত্র চলাচলের উপযোগিতা', 'কৃষিযন্ত্র চালনা');
                    const badgeText = isOk ? 'অনুকূল' : isWarn ? 'সতর্কতা' : 'স্থগিত';
                    const colorClass = isOk
                      ? 'bg-emerald-50 text-emerald-900 border-emerald-200'
                      : isWarn
                      ? 'bg-amber-50 text-amber-900 border-amber-200'
                      : 'bg-rose-50 text-rose-900 border-rose-200';

                    return (
                      <div
                        key={idx}
                        className={`p-2.5 rounded-xl border flex items-center justify-between gap-2 text-xs font-semibold ${colorClass}`}
                      >
                        <span className="truncate">{shortName}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-white/80 border border-black/5 shrink-0">
                          {badgeText}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Day Switcher Tabs (Today vs 3-day projection) */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
              <button
                onClick={() => setActiveDayTab(0)}
                className={`px-4 py-2.5 rounded-xl text-xs font-bold whitespace-nowrap min-h-[44px] transition-all border ${
                  activeDayTab === 0
                    ? 'bg-forest-700 text-canvas border-forest-700 shadow-sm ring-2 ring-forest-700/20'
                    : 'bg-canvas text-ink-800 border-line-200 hover:border-forest-700'
                }`}
              >
                আজকের কার্যক্রম
              </button>

              {weatherPlan.threeDayForecast.map((day, idx) => (
                <button
                  key={day.date}
                  onClick={() => setActiveDayTab(idx + 1)}
                  className={`px-4 py-2 rounded-xl text-xs font-medium whitespace-nowrap min-h-[44px] transition-all border text-left ${
                    activeDayTab === idx + 1
                      ? 'bg-forest-700 text-canvas border-forest-700 shadow-sm ring-2 ring-forest-700/20 font-bold'
                      : 'bg-canvas text-ink-800 border-line-200 hover:border-forest-700'
                  }`}
                >
                  <span className="block">{day.date}</span>
                  <span className={`text-[10px] block ${activeDayTab === idx + 1 ? 'opacity-90' : 'text-ink-600'}`}>
                    {day.tempMaxC}° / {day.tempMinC}° • বৃষ্টি {day.precipitationProbabilityMax}%
                  </span>
                </button>
              ))}
            </div>

            {/* Render recommendations for the active tab */}
            {activeDayTab === 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {weatherPlan.activityWindows.map((rec, idx) => (
                  <ActivityWindowCard key={idx} recommendation={rec} />
                ))}
              </div>
            ) : (
              weatherPlan.threeDayForecast[activeDayTab - 1] && (
                <div className="space-y-4">
                  <div className="p-3.5 bg-field-wash rounded-xl border border-line-200 text-xs flex items-center justify-between">
                    <span className="font-semibold text-forest-900 flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-forest-700" />
                      <span>তারিখ: {weatherPlan.threeDayForecast[activeDayTab - 1].date}</span>
                    </span>
                    <span className="text-ink-700 font-medium">
                      পূর্বাভাস: {weatherPlan.threeDayForecast[activeDayTab - 1].weatherDescriptionBn}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {weatherPlan.threeDayForecast[activeDayTab - 1].activityRecommendations.map(
                      (rec, idx) => (
                        <ActivityWindowCard key={idx} recommendation={rec} />
                      )
                    )}
                  </div>
                </div>
              )
            )}
          </div>

          {/* Quick link to Machinery Search with weather-aware planning */}
          <div className="p-6 bg-gradient-to-r from-leaf-100/60 via-canvas to-field-wash rounded-2xl border border-line-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-soft">
            <div className="space-y-1">
              <h3 className="text-base font-bold text-forest-900 flex items-center gap-2">
                <Tractor className="w-5 h-5 text-forest-700" />
                <span>আবহাওয়া অনুকূল থাকলে কৃষিযন্ত্র ভাড়া করুন</span>
              </h3>
              <p className="text-xs text-ink-600">
                বৃষ্টি ও মাটির অবস্থা যাচাই করে আশেপাশের ট্রাক্টর, হার্ভেস্টার বা পাম্প মালিকের সাথে সরাসরি যোগাযোগ করুন।
              </p>
            </div>
            <Link to="/app/equipment" className="shrink-0">
              <Button variant="primary" size="md">
                <span>যন্ত্র আবিষ্কারে যান</span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
};
