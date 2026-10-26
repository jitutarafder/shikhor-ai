import React from 'react';
import { Link } from 'react-router-dom';
import { Sprout, ShieldCheck, HeartHandshake } from 'lucide-react';
import { useLocale } from '../../i18n/LocaleContext';

export const Footer: React.FC = () => {
  const { t } = useLocale();

  return (
    <footer className="bg-surface border-t border-line-200 mt-20 pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-line-200">
          {/* Brand info */}
          <div className="space-y-4 md:col-span-1">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-btn bg-leaf-100 border border-leaf-500/20 flex items-center justify-center text-forest-700">
                <Sprout className="w-5 h-5" />
              </div>
              <span className="font-bold text-xl text-forest-900">{t.brand.name}</span>
            </Link>
            <p className="text-sm text-ink-600 leading-relaxed">
              {t.footer.desc}
            </p>
          </div>

          {/* Product links */}
          <div>
            <h4 className="text-sm font-semibold text-forest-900 tracking-wider uppercase mb-4">
              সেবাসমূহ
            </h4>
            <ul className="space-y-2.5 text-sm text-ink-600">
              <li><Link to="/features" className="hover:text-forest-700 transition-colors">ফসল সমস্যা সহচর</Link></li>
              <li><Link to="/features" className="hover:text-forest-700 transition-colors">কৃষিযন্ত্র আবিষ্কার ও ভাড়া</Link></li>
              <li><Link to="/features" className="hover:text-forest-700 transition-colors">আবহাওয়ার ৩ দিনের পরিকল্পনা</Link></li>
              <li><Link to="/features" className="hover:text-forest-700 transition-colors">ফসল ক্রেতা সংযোগ</Link></li>
            </ul>
          </div>

          {/* Company links */}
          <div>
            <h4 className="text-sm font-semibold text-forest-900 tracking-wider uppercase mb-4">
              প্রতিষ্ঠান
            </h4>
            <ul className="space-y-2.5 text-sm text-ink-600">
              <li><Link to="/about" className="hover:text-forest-700 transition-colors">আমাদের লক্ষ্য ও উদ্দেশ্য</Link></li>
              <li><Link to="/about" className="hover:text-forest-700 transition-colors">দায়িত্বশীল এআই নীতিমালা</Link></li>
              <li><Link to="/contact" className="hover:text-forest-700 transition-colors">যোগাযোগ ও সহায়তা</Link></li>
            </ul>
          </div>

          {/* Trust & Safety notice */}
          <div className="space-y-3 bg-canvas p-4 rounded-card border border-line-200">
            <div className="flex items-center gap-2 text-forest-900 font-semibold text-sm">
              <ShieldCheck className="w-4 h-4 text-leaf-500" />
              <span>নিরাপদ ও নির্ভরযোগ্য</span>
            </div>
            <p className="text-xs text-ink-600 leading-normal">
              {t.footer.disclaimer}
            </p>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-ink-600">
          <p>© {new Date().getFullYear()} {t.brand.name}। {t.footer.rights}</p>
          <div className="flex items-center gap-6">
            <Link to="/privacy" className="hover:text-forest-700">গোপনীয়তা নীতি</Link>
            <Link to="/terms" className="hover:text-forest-700">ব্যবহারের শর্তাবলী</Link>
            <Link to="/support" className="hover:text-forest-700">সহায়তা কেন্দ্র</Link>
            <span className="flex items-center gap-1 text-soil-700">
              <HeartHandshake className="w-3.5 h-3.5" />
              <span>কৃষকের সাথে, সবসময়</span>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};
