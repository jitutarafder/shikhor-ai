import React from 'react';
import { Link } from 'react-router-dom';
import { Sprout, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex items-center justify-center py-16 px-4">
      <div className="text-center max-w-md space-y-5">
        <div className="w-16 h-16 rounded-full bg-leaf-100 text-forest-700 flex items-center justify-center mx-auto">
          <Sprout className="w-8 h-8" />
        </div>
        <h1 className="text-4xl font-bold text-forest-900">৪০৪ — পৃষ্ঠা খুঁজে পাওয়া যায়নি</h1>
        <p className="text-ink-600 text-base leading-relaxed">
          দুঃখিত, আপনি যে পৃষ্ঠাটি খুঁজছেন তা স্থানান্তরিত হয়েছে অথবা আর বিদ্যমান নেই।
        </p>
        <Link to="/">
          <Button variant="primary" size="md">
            <ArrowLeft className="w-4 h-4 mr-2" />
            <span>মূল পাতায় ফিরে যান</span>
          </Button>
        </Link>
      </div>
    </div>
  );
};
