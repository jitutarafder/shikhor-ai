import React from 'react';
import { Card } from '../components/ui/Card';
import {
  FileCheck,
  Scale,
  AlertOctagon,
  ShieldCheck,
  Tractor,
  Handshake,
} from 'lucide-react';

export const TermsOfService: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex p-3 rounded-2xl bg-forest-100 text-forest-900 border border-forest-200">
          <Scale className="w-8 h-8" />
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-forest-900">
          ব্যবহারের সাধারণ শর্তাবলী (Terms of Service)
        </h1>
        <p className="text-sm text-ink-600 max-w-xl mx-auto">
          শিখড় এআই প্ল্যাটফর্ম ব্যবহার করার মাধ্যমে আপনি নিম্নলিখিত নিয়মাবলী মেনে নিতে সম্মত হচ্ছেন।
        </p>
      </div>

      <div className="space-y-6 text-sm text-ink-800 leading-relaxed">
        <Card className="p-6 space-y-3 border-line-200 bg-canvas">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <FileCheck className="w-5 h-5 text-forest-700" />
            <h2>১. প্ল্যাটফর্মের প্রকৃতি ও উদ্দেশ্য</h2>
          </div>
          <p className="text-xs sm:text-sm text-ink-700">
            শিখড় এআই হলো কৃষকদের জন্য একটি আধুনিক সিদ্ধান্ত সহায়তা প্ল্যাটফর্ম। এটি কৃষকদের ফসলের রোগের সম্ভাব্য লক্ষণ বুঝতে, নিকটস্থ কৃষিযন্ত্রের সন্ধান পেতে, আবহাওয়া উপযোগী কাজের পরিকল্পনা করতে এবং পাইকারি ক্রেতাদের সাথে সরাসরি যোগাযোগের সুবিধা প্রদান করে।
          </p>
        </Card>

        <Card className="p-6 space-y-3 border-line-200 bg-canvas">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <AlertOctagon className="w-5 h-5 text-danger-600" />
            <h2>২. সিদ্ধান্ত সহায়তা ও চিকিৎসা দায়মুক্তি</h2>
          </div>
          <p className="text-xs sm:text-sm text-ink-700">
            এআই মডেলের ফলাফল কেবল সম্ভাবনাময় ইঙ্গিত। এটি কোনোভাবেই কৃষি কর্মকর্তা বা ভেটেরিনারি চিকিৎসকের নিশ্চিত প্রেসক্রিপশনের সমতুল্য নয়। অননুমোদিত রাসায়নিক বা ভুল ব্যবহারের ফলে ফসলহানির কোনো প্রত্যক্ষ বা পরোক্ষ আর্থিক দায় শিখড় এআই গ্রহণ করবে না।
          </p>
        </Card>

        <Card className="p-6 space-y-3 border-line-200 bg-canvas">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <Tractor className="w-5 h-5 text-soil-700" />
            <h2>৩. কৃষিযন্ত্র ও ফসল মার্কেটপ্লেস সংক্রান্ত নিয়ম</h2>
          </div>
          <ul className="list-disc list-inside space-y-1.5 text-ink-700 text-xs sm:text-sm">
            <li>যন্ত্রের মালিকরা কেবলমাত্র প্রকৃত এবং কর্মক্ষম যন্ত্রপাতির তালিকা পোস্ট করবেন।</li>
            <li>কৃষিযন্ত্রের র‍্যাংকিং পদ্ধতি নির্ধারিত ৬৫% মূল্য ও ৩৫% দূরত্বের স্বচ্ছ গাণিতিক সূত্রে নির্ধারিত হয় (Rule 15)। কোনো অন্যায্য অর্থের বিনিময়ে কৃত্রিম প্লেসমেন্ট দেওয়া হয় না।</li>
            <li>ফসল কেনাবেচায় উভয় পক্ষের সমঝোতায় লেনদেন সম্পন্ন হবে। কোনো ধরনের জালিয়াতি, প্রতারণা বা ভুয়া তালিকা পোস্ট করা আইনত দণ্ডনীয়।</li>
          </ul>
        </Card>

        <Card className="p-6 space-y-3 border-line-200 bg-canvas">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <Handshake className="w-5 h-5 text-emerald-700" />
            <h2>৪. বার্তা আদান-প্রদান ও আচরণবিধি</h2>
          </div>
          <p className="text-xs sm:text-sm text-ink-700">
            কোনো প্রকার অশালীন ভাষা, অসঙ্গত আচরণ বা স্প্যামিং বরদাস্ত করা হবে না। অভিযোগের প্রেক্ষিতে মডারেশন দল তদন্ত সাপেক্ষে সংশ্লিষ্ট অ্যাকাউন্ট স্থগিত বা স্থায়ীভাবে বন্ধ করার অধিকার রাখে।
          </p>
        </Card>

        <Card className="p-6 space-y-3 border-line-200 bg-canvas">
          <div className="flex items-center gap-2.5 text-forest-900 font-bold text-base">
            <ShieldCheck className="w-5 h-5 text-forest-800" />
            <h2>৫. আইন ও বিরোধ নিষ্পত্তি</h2>
          </div>
          <p className="text-xs sm:text-sm text-ink-700">
            এই শর্তাবলী গণপ্রজাতন্ত্রী বাংলাদেশের প্রযোজ্য তথ্যপ্রযুক্তি ও ডিজিটাল নিরাপত্তা আইনের আওতায় পরিচালিত ও ব্যাখ্যাযোগ্য।
          </p>
        </Card>
      </div>
    </div>
  );
};
