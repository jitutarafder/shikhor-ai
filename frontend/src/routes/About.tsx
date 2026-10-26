import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Sprout, ArrowRight, Eye } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const About: React.FC = () => {
  return (
    <div className="space-y-20 sm:space-y-24 py-8">
      {/* 1. Hero */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
        <Badge variant="success">আমাদের লক্ষ্য ও উদ্দেশ্য</Badge>
        <h1 className="text-3xl sm:text-5xl font-bold text-forest-900 tracking-tight max-w-3xl mx-auto leading-tight">
          প্রযুক্তি যেন কৃষকের বাস্তব সমস্যার সহজ ও নিরাপদ সমাধান হয়
        </h1>
        <p className="text-lg text-ink-600 max-w-2xl mx-auto">
          শিকড় এআই তৈরি হয়েছে বাংলাদেশের কৃষকের হাতের নাগালে নির্ভরযোগ্য কৃষি সিদ্ধান্ত ও সংযোগ পৌঁছে দেওয়ার লক্ষ্যে।
        </p>
      </section>

      {/* 2. Mission & Vision */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card className="p-8 space-y-4 bg-leaf-100/50 border-leaf-500/20">
            <div className="w-12 h-12 rounded-btn bg-leaf-100 text-forest-700 flex items-center justify-center">
              <Sprout className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold text-forest-900">আমাদের মিশন</h2>
            <p className="text-ink-600 leading-relaxed text-sm sm:text-base">
              কৃষকদের তথ্যপ্রাপ্তির বাধা দূর করা, কৃষিযন্ত্রের অপ্রয়োজনীয় ভাড়া কমানো এবং দুর্যোগপূর্ণ আবহাওয়ায় আগাম সচেতনতা তৈরি করে ফসলের ক্ষয়ক্ষতি ন্যূনতম পর্যায়ে নামিয়ে আনা।
            </p>
          </Card>

          <Card className="p-8 space-y-4 bg-surface border-line-200">
            <div className="w-12 h-12 rounded-btn bg-paddy-400/20 text-soil-700 flex items-center justify-center">
              <Eye className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold text-forest-900">আমাদের ভিশন</h2>
            <p className="text-ink-600 leading-relaxed text-sm sm:text-base">
              এমন একটি অন্তর্ভুক্তিমূলক ডিজিটাল কৃষি ব্যবস্থা যেখানে প্রান্তিক কৃষকও স্মার্টফোনের মাধ্যমে সঠিক সময়ে সঠিক কৃষি সিদ্ধান্তের অধিকারী হবেন।
            </p>
          </Card>
        </div>
      </section>

      {/* 3. Responsible AI Statement */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <Card className="p-8 sm:p-12 border-forest-700/30 bg-canvas space-y-6">
          <div className="flex items-center gap-3">
            <ShieldCheck className="w-8 h-8 text-forest-700" />
            <h2 className="text-2xl sm:text-3xl font-bold text-forest-900">
              দায়িত্বশীল এআই নীতিমালা (Responsible AI)
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
            <div className="space-y-2">
              <h3 className="font-bold text-forest-900 text-base">১. সিদ্ধান্ত সহায়তা, বিকল্প নয়</h3>
              <p className="text-sm text-ink-600 leading-relaxed">
                এআই পরামর্শ শুধুমাত্র সিদ্ধান্ত গ্রহণের প্রাথমিক সহায়তা। এটি কোনো প্রত্যয়িত কৃষি কর্মকর্তার চূড়ান্ত নির্দেশনার বিকল্প নয়।
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="font-bold text-forest-900 text-base">২. স্বচ্ছ কনফিডেন্স স্কোর</h3>
              <p className="text-sm text-ink-600 leading-relaxed">
                ফলাফল কতটা নির্ভরযোগ্য তা স্পষ্টভাবে জানানো হয়। দুর্বল বা অস্পষ্ট ছবিতে কোনো মনগড়া সিদ্ধান্ত চাপিয়ে দেওয়া হয় না।
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="font-bold text-forest-900 text-base">৩. মানব বিশেষজ্ঞের সংযুক্তি</h3>
              <p className="text-sm text-ink-600 leading-relaxed">
                অনিশ্চিত বা জটিল লক্ষণ দেখা দিলে কৃষককে স্থানীয় উপজেলা কৃষি অফিসে যোগাযোগ করতে সরাসরি উদ্বুদ্ধ করা হয়।
              </p>
            </div>
          </div>
        </Card>
      </section>

      {/* 4. Contact CTA */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
        <h2 className="text-2xl sm:text-3xl font-bold text-forest-900">
          আমাদের সাথে যুক্ত হতে চান?
        </h2>
        <p className="text-ink-600 max-w-xl mx-auto text-base">
          কৃষি কর্মকর্তা, গবেষক বা অংশীদার হিসেবে আমাদের প্ল্যাটফর্মে অবদান রাখতে আমাদের সঙ্গে যোগাযোগ করুন।
        </p>
        <Link to="/contact">
          <Button variant="primary" size="lg">
            <span>যোগাযোগ করুন</span>
            <ArrowRight className="w-5 h-5 ml-1" />
          </Button>
        </Link>
      </section>
    </div>
  );
};
