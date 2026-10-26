import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import {
  LifeBuoy,
  PhoneCall,
  HelpCircle,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface FaqItem {
  q: string;
  a: string;
}

const faqs: FaqItem[] = [
  {
    q: 'শিখড় এআই কি সম্পূর্ণ বিনামূল্যে ব্যবহার করা যায়?',
    a: 'হ্যাঁ, কৃষকদের জন্য ফসলের প্রাথমিক রোগ নির্ণয়, নিকটস্থ কৃষিযন্ত্রের সন্ধান এবং আবহাওয়া পূর্বাভাস সেবা সম্পূর্ণ বিনামূল্যে উন্মুক্ত।',
  },
  {
    q: 'ইন্টারনেট না থাকলে কি রোগ নির্ণয় করা যাবে?',
    a: 'ইন্টারনেট না থাকলেও পূর্বে সংরক্ষিত অফলাইন কৃষি তথ্যভাণ্ডার পড়ে পরামর্শ পাওয়া যাবে। ইন্টারনেট ফিরলে জমাকৃত অনুরোধগুলো স্বয়ংক্রিয়ভাবে সার্ভারে সিঙ্ক হয়ে যাবে।',
  },
  {
    q: 'রোগ নির্ণয়ের পরামর্শ কি শতভাগ নিশ্চিত?',
    a: 'না, এআই মডেলের ফলাফল হলো সিদ্ধান্ত সহায়তা। নিশ্চিত সিদ্ধান্ত ও মাত্রা অনুযায়ী কীটনাশক ব্যবহারের জন্য সবসময় নিকটস্থ উপসহকারী কৃষি কর্মকর্তা (SAAO)-এর সাথে পরামর্শ করুন।',
  },
  {
    q: 'কৃষিযন্ত্র কীভাবে ভাড়া করব?',
    a: 'যন্ত্রপাতি অংশে গিয়ে আপনার প্রয়োজনীয় যন্ত্র (যেমন: পাওয়ার টিলার বা হারভেস্টার) নির্বাচন করুন। দূরত্বের স্বচ্ছ হিসাব অনুযায়ী নিকটস্থ মালিকদের তালিকা থেকে অনুরোধ জমা দিন।',
  },
];

export const SupportCenter: React.FC = () => {
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const toggleFaq = (idx: number) => {
    setOpenFaq(openFaq === idx ? null : idx);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex p-3 rounded-2xl bg-emerald-50 text-forest-800 border border-emerald-200">
          <LifeBuoy className="w-8 h-8" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-forest-900">
          সহায়তা কেন্দ্র ও জরুরি যোগাযোগ
        </h1>
        <p className="text-sm text-ink-600 max-w-xl mx-auto">
          কৃষি সংক্রান্ত যেকোনো জিজ্ঞাসা বা প্ল্যাটফর্ম ব্যবহারে কোনো সমস্যায় আমরা আপনার পাশে আছি।
        </p>
      </div>

      {/* Emergency Callout Card */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-forest-900 text-white rounded-2xl p-6 space-y-3 shadow-md">
          <div className="flex items-center gap-2 text-paddy-300 font-bold text-sm">
            <PhoneCall className="w-5 h-5" />
            <span>সরকারি কৃষি কল সেন্টার</span>
          </div>
          <div className="text-3xl font-extrabold tracking-wide text-paddy-200">১৬১২৩</div>
          <p className="text-xs text-forest-100 leading-relaxed">
            কৃষি সম্প্রসারণ অধিদপ্তর (DAE)-এর বিশেষজ্ঞ কৃষি কর্মকর্তাদের সাথে সরাসরি কথা বলতে যেকোনো মোবাইল অপারেটর থেকে ১৬১২৩ নম্বরে কল করুন।
          </p>
        </div>

        <div className="bg-white border border-line-200 rounded-2xl p-6 space-y-3 shadow-xs">
          <div className="flex items-center gap-2 text-forest-900 font-bold text-sm">
            <ShieldAlert className="w-5 h-5 text-amber-600" />
            <span>শিখড় এআই সাপোর্ট ও অভিযোগ ডেস্ক</span>
          </div>
          <div className="text-lg font-bold text-ink-900">support@shikhor.ai</div>
          <p className="text-xs text-ink-600 leading-relaxed">
            প্ল্যাটফর্মে কোনো অসঙ্গতি, ভুয়া তালিকা বা অপব্যবহার দেখলে অ্যাপের ভেতর থেকে 'রিপোর্ট করুন' অথবা সরাসরি ইমেইল করুন।
          </p>
        </div>
      </div>

      {/* FAQs */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-forest-900 font-bold text-lg">
          <HelpCircle className="w-5 h-5 text-forest-700" />
          <h2>সাধারণ জিজ্ঞাসাসমূহ (FAQ)</h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <Card
                key={idx}
                className="overflow-hidden border-line-200 bg-canvas transition-all"
              >
                <button
                  onClick={() => toggleFaq(idx)}
                  className="w-full p-4.5 text-left flex items-center justify-between gap-4 font-semibold text-xs sm:text-sm text-forest-900 hover:bg-canvas-subtle transition-colors"
                >
                  <span>{faq.q}</span>
                  {isOpen ? (
                    <ChevronUp className="w-4 h-4 text-forest-700 shrink-0" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-ink-400 shrink-0" />
                  )}
                </button>
                {isOpen && (
                  <div className="p-4.5 pt-0 text-xs sm:text-sm text-ink-700 border-t border-line-100 bg-field-wash leading-relaxed">
                    {faq.a}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};
