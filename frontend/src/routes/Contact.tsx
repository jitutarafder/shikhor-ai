import React, { useState } from 'react';
import { Mail, Phone, MapPin, CheckCircle2, Send } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';

export const Contact: React.FC = () => {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    contact: '',
    role: 'farmer',
    subject: '',
    message: '',
    consent: false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.contact || !formData.message || !formData.consent) {
      alert('অনুগ্রহ করে সকল প্রয়োজনীয় তথ্য পূরণ করুন এবং সম্মতি দিন।');
      return;
    }
    setSubmitted(true);
  };

  return (
    <div className="space-y-16 py-8 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="text-center space-y-3">
        <Badge variant="info">সহায়তা ও যোগাযোগ</Badge>
        <h1 className="text-3xl sm:text-5xl font-bold text-forest-900 tracking-tight">
          আমাদের সঙ্গে যোগাযোগ করুন
        </h1>
        <p className="text-lg text-ink-600 max-w-xl mx-auto">
          যে কোনো জিজ্ঞাসা, মতামত বা কারিগরি সহায়তায় আমরা আছি আপনার পাশে।
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left 5 cols: Contact Cards */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="p-6 space-y-4 border-line-200">
            <h2 className="text-xl font-bold text-forest-900">জরুরি পরামর্শ ও তথ্য</h2>
            <div className="space-y-3 text-sm text-ink-600">
              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-leaf-500 shrink-0 mt-0.5" />
                <span>কৃষি তথ্য ও প্রযুক্তি সেল, বাংলাদেশ</span>
              </div>
              <div className="flex items-center gap-3">
                <Mail className="w-5 h-5 text-leaf-500 shrink-0" />
                <span>support@shikhorai.bd (ডেমো)</span>
              </div>
              <div className="flex items-center gap-3">
                <Phone className="w-5 h-5 text-leaf-500 shrink-0" />
                <span>+৮৮০ ১৬১১-০০০০০০ (ডেমো হেল্পলাইন)</span>
              </div>
            </div>
          </Card>

          <Card className="p-6 bg-surface border-line-200 space-y-2">
            <h3 className="font-bold text-forest-900 text-sm">যন্ত্র মালিক বা ক্রেতাদের জন্য</h3>
            <p className="text-xs text-ink-600 leading-relaxed">
              আপনি কি কৃষিযন্ত্রের মালিক অথবা পাইকারি ফসল ক্রেতা? প্ল্যাটফর্মে যুক্ত হতে বার্তা পাঠান অথবা সাইন আপ করুন।
            </p>
          </Card>
        </div>

        {/* Right 7 cols: Contact Form */}
        <div className="lg:col-span-7">
          <Card className="p-6 sm:p-8 border-line-200">
            {submitted ? (
              <div className="text-center py-12 space-y-4">
                <div className="w-16 h-16 rounded-full bg-leaf-100 text-forest-700 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-bold text-forest-900">আপনার বার্তা গৃহীত হয়েছে</h3>
                <p className="text-sm text-ink-600 max-w-md mx-auto leading-relaxed">
                  ধন্যবাদ! আমাদের প্রতিনিধি দ্রুততম সময়ের মধ্যে আপনার ফোন নম্বর বা ইমেইলে যোগাযোগ করবেন।
                </p>
                <Button variant="outline" size="md" onClick={() => setSubmitted(false)}>
                  আরেকটি বার্তা পাঠান
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label htmlFor="name" className="block text-sm font-semibold text-ink-900 mb-1.5">
                    আপনার নাম <span className="text-danger-600">*</span>
                  </label>
                  <input
                    type="text"
                    id="name"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full min-h-[50px] px-4 rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                    placeholder="যেমন: মো. করিম হোসেন"
                  />
                </div>

                <div>
                  <label htmlFor="contact" className="block text-sm font-semibold text-ink-900 mb-1.5">
                    ফোন নম্বর অথবা ইমেইল <span className="text-danger-600">*</span>
                  </label>
                  <input
                    type="text"
                    id="contact"
                    required
                    value={formData.contact}
                    onChange={(e) => setFormData({ ...formData, contact: e.target.value })}
                    className="w-full min-h-[50px] px-4 rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                    placeholder="০১৭১১-XXXXXX"
                  />
                </div>

                <div>
                  <label htmlFor="role" className="block text-sm font-semibold text-ink-900 mb-1.5">
                    আপনার পরিচয়
                  </label>
                  <select
                    id="role"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    className="w-full min-h-[50px] px-4 rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base bg-canvas"
                  >
                    <option value="farmer">কৃষক</option>
                    <option value="owner">কৃষিযন্ত্রের মালিক</option>
                    <option value="buyer">ফসল ক্রেতা / ব্যবসায়ী</option>
                    <option value="expert">কৃষি কর্মকর্তা / গবেষক</option>
                    <option value="other">অন্যান্য</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-semibold text-ink-900 mb-1.5">
                    আপনার বার্তা <span className="text-danger-600">*</span>
                  </label>
                  <textarea
                    id="message"
                    rows={4}
                    required
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    className="w-full p-4 rounded-btn border border-line-200 focus:border-forest-700 focus:ring-1 focus:ring-forest-700 text-base"
                    placeholder="আপনার প্রশ্ন বা মতামত বিস্তারিত লিখুন…"
                  />
                </div>

                <div className="flex items-start gap-2.5 pt-1">
                  <input
                    type="checkbox"
                    id="consent"
                    required
                    checked={formData.consent}
                    onChange={(e) => setFormData({ ...formData, consent: e.target.checked })}
                    className="w-5 h-5 rounded mt-0.5 text-forest-700 focus:ring-forest-700 border-line-200"
                  />
                  <label htmlFor="consent" className="text-xs text-ink-600 leading-normal">
                    আমি সম্মতি দিচ্ছি যে আমার যোগাযোগের তথ্য শুধুমাত্র এই বার্তা সংক্রান্ত যোগাযোগের কাজে ব্যবহৃত হবে। <span className="text-danger-600">*</span>
                  </label>
                </div>

                <Button type="submit" variant="primary" size="lg" fullWidth>
                  <span>বার্তা পাঠান</span>
                  <Send className="w-4 h-4 ml-2" />
                </Button>
              </form>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};
