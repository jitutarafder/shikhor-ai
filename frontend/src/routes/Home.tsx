import React from 'react';
import { Link } from 'react-router-dom';
import {
  ScanLine,
  Tractor,
  CloudSun,
  Handshake,
  CheckCircle2,
  WifiOff,
  ArrowRight,
  ShieldCheck,
  ChevronRight,
  Sparkles,
} from 'lucide-react';
import { useLocale } from '../i18n/LocaleContext';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const Home: React.FC = () => {
  const { t } = useLocale();

  return (
    <div className="space-y-20 sm:space-y-28">
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden pt-8 pb-12 sm:pt-14 sm:pb-20 bg-field-wash border-b border-line-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left 7 cols: Copy & Actions */}
            <div className="lg:col-span-7 space-y-6 sm:space-y-8">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-leaf-100 border border-leaf-500/20 text-forest-900 text-xs sm:text-sm font-semibold tracking-wide">
                <Sparkles className="w-4 h-4 text-leaf-500" />
                <span>{t.hero.eyebrow}</span>
              </div>

              <h1 className="text-3xl sm:text-5xl lg:text-[54px] font-bold text-forest-900 leading-[1.15] tracking-tight">
                {t.hero.title}
              </h1>

              <p className="text-lg sm:text-xl text-ink-600 max-w-2xl leading-relaxed">
                {t.hero.description}
              </p>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-2">
                <Link to="/signup">
                  <Button variant="primary" size="lg" fullWidth className="sm:w-auto">
                    <span>{t.hero.primaryCta}</span>
                    <ArrowRight className="w-5 h-5 ml-1" />
                  </Button>
                </Link>

                <Link to="/features">
                  <Button variant="outline" size="lg" fullWidth className="sm:w-auto">
                    <span>{t.hero.secondaryCta}</span>
                  </Button>
                </Link>
              </div>

              {/* Trust & Offline note */}
              <div className="flex items-center gap-3 pt-2 text-sm text-soil-700 font-medium">
                <div className="w-2.5 h-2.5 rounded-full bg-paddy-400 animate-pulse" />
                <p>{t.hero.trustNote}</p>
              </div>
            </div>

            {/* Right 5 cols: Believable interactive preview cards */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md space-y-4">
                {/* Floating card 1: AI crop diagnosis preview */}
                <Card className="border-leaf-500/30 shadow-md bg-canvas relative overflow-hidden">
                  <div className="flex items-start justify-between gap-3 pb-3 border-b border-line-200">
                    <div>
                      <div className="text-xs text-ink-600 font-medium">ফসলের সমস্যা যাচাই</div>
                      <div className="font-bold text-base text-forest-900 mt-0.5">ধানের ব্লাইট রোগ (সম্ভাব্য)</div>
                    </div>
                    <Badge variant="warning">৭৮% সামঞ্জস্যপূর্ণ</Badge>
                  </div>
                  <p className="text-xs text-ink-600 pt-2.5 leading-relaxed">
                    প্রাথমিক লক্ষণ পাতায় হলদে দাগ। ক্ষতের বিস্তার রোধে অনুমোদিত ছত্রাকনাশক ও জমি নিষ্কাশন নিশ্চিত করুন।
                  </p>
                  <div className="mt-3 pt-2 flex items-center justify-between text-[11px] text-soil-700 bg-surface px-2.5 py-1.5 rounded-lg border border-line-200">
                    <span>নিশ্চিত না হলে কৃষি কর্মকর্তার সহায়তা নিন</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </div>
                </Card>

                {/* Floating card 2: Nearby equipment rental preview */}
                <Card className="border-forest-700/20 shadow-md bg-canvas">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-btn bg-leaf-100 flex items-center justify-center text-forest-700">
                        <Tractor className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="font-bold text-sm text-forest-900">পাওয়ার টিলার / ট্রাক্টর</div>
                        <div className="text-xs text-ink-600">দূরত্ব: ২.৫ কিমি • রেটিং: ৪.৮</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-forest-900 text-sm">৳ ৭৫০/ঘণ্টা</div>
                      <span className="text-[10px] text-leaf-500 font-semibold">উপলব্ধ</span>
                    </div>
                  </div>
                </Card>

                {/* Floating card 3: Weather & offline strip */}
                <div className="grid grid-cols-2 gap-3">
                  <Card className="p-3.5 bg-canvas flex items-center gap-2.5 border-line-200">
                    <CloudSun className="w-6 h-6 text-sky-600 shrink-0" />
                    <div>
                      <div className="text-[11px] text-ink-600">আগামীকাল আবহাওয়া</div>
                      <div className="text-xs font-bold text-forest-900">স্প্রে করার অনুকূল সময়</div>
                    </div>
                  </Card>

                  <Card className="p-3.5 bg-soil-100/60 border-soil-700/20 flex items-center gap-2">
                    <WifiOff className="w-5 h-5 text-soil-700 shrink-0" />
                    <div>
                      <div className="text-[11px] text-soil-700 font-medium">অফলাইন সুবিধা</div>
                      <div className="text-xs font-bold text-soil-700">অনুরোধ সংরক্ষিত হবে</div>
                    </div>
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. QUICK-ACTION STRIP */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Link to="/features" className="group">
            <Card hoverEffect className="h-full flex flex-col items-center justify-center text-center p-6 border-line-200 group-hover:border-forest-700/40">
              <div className="w-12 h-12 rounded-full bg-leaf-100 flex items-center justify-center text-forest-700 mb-3 group-hover:scale-110 transition-transform">
                <ScanLine className="w-6 h-6" />
              </div>
              <h2 className="text-base font-bold text-forest-900">{t.quickActions.cropScan}</h2>
              <span className="text-xs text-ink-600 mt-1">ছবি বা লক্ষণ লিখে</span>
            </Card>
          </Link>

          <Link to="/features" className="group">
            <Card hoverEffect className="h-full flex flex-col items-center justify-center text-center p-6 border-line-200 group-hover:border-forest-700/40">
              <div className="w-12 h-12 rounded-full bg-paddy-400/20 flex items-center justify-center text-soil-700 mb-3 group-hover:scale-110 transition-transform">
                <Tractor className="w-6 h-6" />
              </div>
              <h2 className="text-base font-bold text-forest-900">{t.quickActions.equipment}</h2>
              <span className="text-xs text-ink-600 mt-1">কাছের সেরা মূল্যে</span>
            </Card>
          </Link>

          <Link to="/features" className="group">
            <Card hoverEffect className="h-full flex flex-col items-center justify-center text-center p-6 border-line-200 group-hover:border-forest-700/40">
              <div className="w-12 h-12 rounded-full bg-sky-600/10 flex items-center justify-center text-sky-600 mb-3 group-hover:scale-110 transition-transform">
                <CloudSun className="w-6 h-6" />
              </div>
              <h2 className="text-base font-bold text-forest-900">{t.quickActions.weather}</h2>
              <span className="text-xs text-ink-600 mt-1">৩ দিনের কাজের হিসাব</span>
            </Card>
          </Link>

          <Link to="/features" className="group">
            <Card hoverEffect className="h-full flex flex-col items-center justify-center text-center p-6 border-line-200 group-hover:border-forest-700/40">
              <div className="w-12 h-12 rounded-full bg-soil-100 flex items-center justify-center text-soil-700 mb-3 group-hover:scale-110 transition-transform">
                <Handshake className="w-6 h-6" />
              </div>
              <h2 className="text-base font-bold text-forest-900">{t.quickActions.buyers}</h2>
              <span className="text-xs text-ink-600 mt-1">ন্যায্য মূল্যে বিক্রয়</span>
            </Card>
          </Link>
        </div>
      </section>

      {/* 3. PROBLEM-TO-SOLUTION FEATURE GRID */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-forest-900">
            {t.features.title}
          </h2>
          <p className="mt-3 text-lg text-ink-600">
            {t.features.subtitle}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center">
              <ScanLine className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-forest-900">{t.features.cropAssistant.title}</h3>
            <p className="text-sm text-ink-600 leading-relaxed">{t.features.cropAssistant.desc}</p>
          </Card>

          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center">
              <Tractor className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-forest-900">{t.features.equipmentRental.title}</h3>
            <p className="text-sm text-ink-600 leading-relaxed">{t.features.equipmentRental.desc}</p>
          </Card>

          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center">
              <CloudSun className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-forest-900">{t.features.weatherPlanning.title}</h3>
            <p className="text-sm text-ink-600 leading-relaxed">{t.features.weatherPlanning.desc}</p>
          </Card>

          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center">
              <Handshake className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-forest-900">{t.features.buyerNetwork.title}</h3>
            <p className="text-sm text-ink-600 leading-relaxed">{t.features.buyerNetwork.desc}</p>
          </Card>

          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-btn bg-soil-100 text-soil-700 flex items-center justify-center">
              <WifiOff className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-forest-900">{t.features.offlineSync.title}</h3>
            <p className="text-sm text-ink-600 leading-relaxed">{t.features.offlineSync.desc}</p>
          </Card>

          <Card hoverEffect className="space-y-3">
            <div className="w-10 h-10 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="text-xl font-bold text-forest-900">{t.features.verifiedKnowledge.title}</h3>
            <p className="text-sm text-ink-600 leading-relaxed">{t.features.verifiedKnowledge.desc}</p>
          </Card>
        </div>
      </section>

      {/* 4. RESPONSIBLE AI & ESCALATION COMMITMENT */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-forest-900 text-canvas rounded-card p-8 sm:p-12 relative overflow-hidden shadow-soft">
          <div className="max-w-2xl space-y-4">
            <Badge variant="warning" className="bg-paddy-400 text-forest-900 border-none">
              দায়িত্বশীল প্রযুক্তি
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold text-canvas leading-tight">
              কৃষকের আস্থা ও সঠিক নির্দেশনাই আমাদের অঙ্গীকার
            </h2>
            <p className="text-canvas/80 text-sm sm:text-base leading-relaxed">
              শিকড় এআই কখনও অনুমানের ওপর ভিত্তি করে ক্ষতিকর কীটনাশকের অযৌক্তিক মাত্রা সুপারিশ করে না। যে কোনো অনিশ্চিত ফলাফলে আমরা স্থানীয় উপজেলা কৃষি কর্মকর্তার সহায়তা নেওয়ার পরামর্শ প্রদান করি।
            </p>
            <div className="pt-2 flex flex-wrap gap-4 text-xs text-canvas/90">
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-paddy-400" />
                স্বচ্ছ কনফিডেন্স লেভেল
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-paddy-400" />
                কৃষি বিশেষজ্ঞ যাচাইকরণ
              </span>
              <span className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-paddy-400" />
                গোপনীয়তা সুরক্ষা
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* 5. FINAL CALL TO ACTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
        <h2 className="text-3xl sm:text-4xl font-bold text-forest-900">
          আজকের কৃষি সিদ্ধান্ত আরও সহজ ও লাভজনক করুন
        </h2>
        <p className="text-ink-600 max-w-xl mx-auto text-base sm:text-lg">
          বিনামূল্যে যোগ দিন এবং আপনার ফসল সুরক্ষায় ও কৃষিযন্ত্র সংযোগে ডিজিটাল সহচর হিসেবে সঙ্গে রাখুন শিকড় এআই।
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/signup">
            <Button variant="primary" size="lg">
              {t.nav.signup}
            </Button>
          </Link>
          <Link to="/contact">
            <Button variant="outline" size="lg">
              {t.nav.contact}
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
};
