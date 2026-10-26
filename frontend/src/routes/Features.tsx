import React from 'react';
import { Link } from 'react-router-dom';
import {
  ScanLine,
  Tractor,
  CloudSun,
  WifiOff,
  ArrowRight,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const Features: React.FC = () => {
  return (
    <div className="space-y-20 sm:space-y-24 py-8">
      {/* 1. Header */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
        <Badge variant="info">প্ল্যাটফর্ম সুবিধাসমূহ</Badge>
        <h1 className="text-3xl sm:text-5xl font-bold text-forest-900 tracking-tight">
          মাঠের প্রয়োজনে আধুনিক প্রযুক্তির সঠিক মেলবন্ধন
        </h1>
        <p className="text-lg text-ink-600 max-w-2xl mx-auto">
          কৃষকের সময় ও খরচ বাঁচাতে ছয়টি জরুরি সেবা এখন একটি সহজ মোবাইল প্ল্যাটফর্মে।
        </p>
      </section>

      {/* 2. Feature Sections */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Feature 1: Crop Assistant */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-6 space-y-4">
            <div className="w-12 h-12 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center">
              <ScanLine className="w-6 h-6" />
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-forest-900">
              এআই ফসল সমস্যা সহচর
            </h2>
            <p className="text-ink-600 leading-relaxed">
              ফসলের রোগাক্রান্ত পাতার পরিষ্কার ছবি তুলুন অথবা বাংলায় লক্ষণ লিখে জানান। এআই মডেল লক্ষণ বিশ্লেষণ করে সম্ভাব্য রোগ ও বিশেষজ্ঞদের অনুমোদিত প্রাথমিক সমাধান প্রদর্শন করে।
            </p>
            <ul className="space-y-2 text-sm text-ink-900 font-medium">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-leaf-500" />
                <span>স্বচ্ছ কনফিডেন্স স্কোর (উচ্চ / মাঝারি / অনিশ্চিত)</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-leaf-500" />
                <span>অনিশ্চিত ফলাফলে সরাসরি উপজেলা কৃষি কর্মকর্তার পরামর্শ নেওয়ার নির্দেশ</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-leaf-500" />
                <span>কোনো কাল্পনিক ক্ষতিকর কীটনাশকের অযৌক্তিক ব্যবহার নেই</span>
              </li>
            </ul>
          </div>
          <div className="lg:col-span-6">
            <Card className="p-6 bg-surface border-line-200">
              <div className="flex items-center justify-between pb-4 border-b border-line-200">
                <span className="text-xs font-semibold text-soil-700">ফলাফল প্রিভিউ</span>
                <Badge variant="success">৮৪% সামঞ্জস্যপূর্ণ</Badge>
              </div>
              <div className="py-4 space-y-2">
                <div className="text-base font-bold text-forest-900">ধানের পাতা পোড়া রোগ (Bacterial Blight)</div>
                <p className="text-xs text-ink-600 leading-relaxed">
                  কারণ: ব্যাকটেরিয়াজনিত আক্রমণ। ইউরিয়া সারের অতিরিক্ত ব্যবহার রোধ করুন এবং জমি শুকিয়ে কয়েক দিন রোদ লাগান।
                </p>
              </div>
              <div className="p-3 bg-canvas rounded-btn border border-line-200 text-xs text-ink-600">
                ⚠️ প্রাথমিক নির্দেশিকা। নিশ্চিত হতে নিকটস্থ কৃষি সম্প্রসারণ অফিসে যোগাযোগ করুন।
              </div>
            </Card>
          </div>
        </div>

        {/* Feature 2: Equipment Rental */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-6 lg:order-2 space-y-4">
            <div className="w-12 h-12 rounded-btn bg-paddy-400/20 text-soil-700 flex items-center justify-center">
              <Tractor className="w-6 h-6" />
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-forest-900">
              কাছের কৃষিযন্ত্র আবিষ্কার ও স্বচ্ছ ভাড়া
            </h2>
            <p className="text-ink-600 leading-relaxed">
              জমি চাষ বা ফসল কাটার মৌসুমে নিকটস্থ পাওয়ার টিলার, হার্ভেস্টার বা সেচ পাম্প খুঁজুন। দূরত্বের কারণে অযথা অতিরিক্ত ভাড়া না দিয়ে স্বচ্ছ মূল্যায়নের মাধ্যমে সঠিক যন্ত্র নির্বাচন করুন।
            </p>
            <div className="p-4 bg-leaf-100 rounded-btn text-xs text-forest-900 font-medium">
              💡 স্বচ্ছ র‍্যাংকিং সূত্র: <strong>৬৫% ভাড়ার সাশ্রয় + ৩৫% নিকটবর্তী দূরত্ব</strong>। কোনো গোপন পেইড প্রোমোশন ফলাফলকে প্রভাবিত করে না।
            </div>
          </div>
          <div className="lg:col-span-6 lg:order-1">
            <Card className="p-6 bg-surface border-line-200 space-y-3">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-forest-900">কম্বাইন হার্ভেস্টার (কুবোতা)</h3>
                  <p className="text-xs text-ink-600">মালিক: মো. রফিকুল ইসলাম • ধামরাই, ঢাকা</p>
                </div>
                <span className="text-sm font-bold text-forest-900">৳ ১,২০০/ঘণ্টা</span>
              </div>
              <div className="text-xs text-ink-600 flex gap-4 pt-2">
                <span>দূরত্ব: ৩.১ কিমি</span>
                <span className="text-leaf-500 font-semibold">উপলব্ধ</span>
              </div>
            </Card>
          </div>
        </div>

        {/* Feature 3: 3-Day Weather */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-6 space-y-4">
            <div className="w-12 h-12 rounded-btn bg-sky-600/10 text-sky-600 flex items-center justify-center">
              <CloudSun className="w-6 h-6" />
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-forest-900">
              কৃষিবান্ধব ৩ দিনের আবহাওয়া পরিকল্পনা
            </h2>
            <p className="text-ink-600 leading-relaxed">
              শুধুমাত্র তাপমাত্রার সংখ্যা নয়, বরং কৃষিকাজের উপযোগী সুনির্দিষ্ট পরামর্শ। বালাইনাশক স্প্রে করা, সার প্রয়োগ বা ফসল কাটার অনুকূল সময় কখন তা সহজে জানুন।
            </p>
          </div>
          <div className="lg:col-span-6">
            <div className="grid grid-cols-3 gap-2 sm:gap-3">
              <Card className="p-3 text-center border-line-200 bg-canvas">
                <span className="text-[11px] text-ink-600 font-semibold">আজ</span>
                <div className="font-bold text-sm text-forest-900 my-1">৩২° / ২৬°</div>
                <span className="text-[10px] text-leaf-500 font-semibold block">স্প্রে করার ভালো সময়</span>
              </Card>
              <Card className="p-3 text-center border-line-200 bg-canvas">
                <span className="text-[11px] text-ink-600 font-semibold">কাল</span>
                <div className="font-bold text-sm text-forest-900 my-1">২৯° / ২৫°</div>
                <span className="text-[10px] text-paddy-400 font-semibold block">বৃষ্টির ঝুঁকি (৬০%)</span>
              </Card>
              <Card className="p-3 text-center border-line-200 bg-canvas">
                <span className="text-[11px] text-ink-600 font-semibold">পরশু</span>
                <div className="font-bold text-sm text-forest-900 my-1">৩১° / ২৪°</div>
                <span className="text-[10px] text-sky-600 font-semibold block">মাঠে কাজের উপযোগী</span>
              </Card>
            </div>
          </div>
        </div>

        {/* Feature 4: Offline First */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-6 lg:order-2 space-y-4">
            <div className="w-12 h-12 rounded-btn bg-soil-100 text-soil-700 flex items-center justify-center">
              <WifiOff className="w-6 h-6" />
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-forest-900">
              অফলাইনে তথ্য পড়া ও সিঙ্ক সুবিধা
            </h2>
            <p className="text-ink-600 leading-relaxed">
              গ্রামীণ এলাকায় দুর্বল বা বিচ্ছিন্ন ইন্টারনেট সংযোগের কথা মাথায় রেখে তৈরি। পূর্বে সংরক্ষিত রোগ ও ফসলের নির্দেশিকা নেট ছাড়াও পড়তে পারবেন এবং অফলাইনে অনুরোধ সংরক্ষণ করতে পারবেন।
            </p>
          </div>
          <div className="lg:col-span-6 lg:order-1">
            <Card className="p-6 bg-surface border-line-200 space-y-3">
              <div className="flex items-center gap-2">
                <Badge variant="offline">অফলাইন সংরক্ষিত</Badge>
                <span className="text-xs text-ink-600">১টি অনুরোধ কিউতে আছে</span>
              </div>
              <p className="text-xs text-ink-600">
                ইন্টারনেট ফিরে আসলে স্বয়ংক্রিয়ভাবে সার্ভারের সঙ্গে সিঙ্ক সম্পন্ন হবে। কোনো ডুপ্লিকেট তথ্য তৈরি হবে না।
              </p>
            </Card>
          </div>
        </div>
      </section>

      {/* 3. FAQ Section */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
        <h2 className="text-2xl sm:text-3xl font-bold text-forest-900 text-center">
          সাধারণ জিজ্ঞাসা (FAQ)
        </h2>
        <div className="space-y-4">
          <Card className="p-5">
            <h3 className="font-bold text-forest-900 text-base flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-leaf-500" />
              শিকড় এআই কি সম্পূর্ণ বিনামূল্যে ব্যবহার করা যায়?
            </h3>
            <p className="text-sm text-ink-600 mt-2 pl-7">
              হ্যাঁ, কৃষকদের জন্য প্রাথমিক ফসল রোগ অনুসন্ধান, আবহাওয়া তথ্য ও কৃষিযন্ত্র অনুসন্ধানের সেবা বিনামূল্যে উন্মুক্ত।
            </p>
          </Card>

          <Card className="p-5">
            <h3 className="font-bold text-forest-900 text-base flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-leaf-500" />
              ইন্টারনেট না থাকলে কি অ্যাপ কাজ করবে?
            </h3>
            <p className="text-sm text-ink-600 mt-2 pl-7">
              পূর্বে ডাউনলোডকৃত কৃষি নির্দেশিকা অফলাইনে পড়া যাবে এবং যন্ত্র ভাড়ার অনুরোধ অফলাইনে সেভ করে রাখা যাবে, যা নেট পেলেই সিঙ্ক হবে।
            </p>
          </Card>
        </div>
      </section>

      {/* 4. CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center pt-8">
        <Link to="/signup">
          <Button variant="primary" size="lg">
            <span>আজই বিনামূল্যে শুরু করুন</span>
            <ArrowRight className="w-5 h-5 ml-1" />
          </Button>
        </Link>
      </section>
    </div>
  );
};
