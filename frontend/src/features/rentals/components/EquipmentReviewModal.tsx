import React, { useState } from 'react';
import { X, Star, AlertCircle, CheckCircle2, Send } from 'lucide-react';
import { RentalRequestItem } from '../types';
import { submitEquipmentReviewApi } from '../../equipment/api';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../../components/ui/Button';
import { getErrorMessage } from '../../../lib/errors';

interface EquipmentReviewModalProps {
  rental: RentalRequestItem;
  equipmentName?: string;
  onClose: () => void;
  onSuccess: () => void;
}

export const EquipmentReviewModal: React.FC<EquipmentReviewModalProps> = ({
  rental,
  equipmentName,
  onClose,
  onSuccess,
}) => {
  const { token } = useAuth();
  const [rating, setRating] = useState<number>(5);
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [comment, setComment] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const starLabels: Record<number, string> = {
    1: 'খুবই অসন্তোষজনক (১/৫)',
    2: 'সন্তোষজনক নয় (২/৫)',
    3: 'মোটামুটি ভালো (৩/৫)',
    4: 'খুব ভালো (৪/৫)',
    5: 'অসাধারণ সেবা (৫/৫)',
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setErrorMsg('রিভিউ প্রদান করতে অনুগ্রহ করে লগইন করুন।');
      return;
    }

    if (rating < 1 || rating > 5) {
      setErrorMsg('অনুগ্রহ করে ১ থেকে ৫ এর মধ্যে স্টার রেটিং নির্বাচন করুন।');
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      await submitEquipmentReviewApi(token, rental.equipmentId, {
        rentalRequestId: rental.id,
        rating,
        comment: comment.trim() || undefined,
      });

      setIsSuccess(true);
      setTimeout(() => {
        onSuccess();
      }, 1500);
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, 'রিভিউ জমা দেওয়া সম্ভব হয়নি।'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-canvas border border-line-200 rounded-card max-w-md w-full p-6 shadow-float space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-line-200">
          <div>
            <h3 className="text-lg font-bold text-forest-900">যন্ত্রের রেটিং ও রিভিউ প্রদান</h3>
            <p className="text-xs text-ink-600">
              {equipmentName ? `যন্ত্র: ${equipmentName}` : `অনুরোধ আইডি: #${rental.id.substring(0, 8)}`}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-btn text-ink-600 hover:text-ink-900 hover:bg-surface min-w-[36px] min-h-[36px] flex items-center justify-center"
            aria-label="বন্ধ করুন"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {isSuccess ? (
          <div className="py-8 text-center space-y-3">
            <CheckCircle2 className="w-12 h-12 text-forest-700 mx-auto" />
            <h4 className="text-lg font-bold text-forest-900">আপনার মূল্যবান রিভিউ সফলভাবে গৃহীত হয়েছে!</h4>
            <p className="text-xs text-ink-600">
              আপনার মতামত অন্যান্য কৃষকদের সঠিক সিদ্ধান্ত নিতে সাহায্য করবে।
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {errorMsg && (
              <div className="p-3 bg-danger-600/10 border border-danger-600/20 rounded-btn text-xs text-danger-600 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Star selector */}
            <div className="text-center py-2 space-y-2">
              <label className="block text-xs font-semibold text-ink-900">
                কাজের গুণমান ও সেবায় আপনার অভিজ্ঞতা নির্বাচন করুন
              </label>

              <div className="flex items-center justify-center gap-2">
                {[1, 2, 3, 4, 5].map((starValue) => {
                  const activeRating = hoverRating !== null ? hoverRating : rating;
                  const isFilled = starValue <= activeRating;

                  return (
                    <button
                      key={starValue}
                      type="button"
                      onMouseEnter={() => setHoverRating(starValue)}
                      onMouseLeave={() => setHoverRating(null)}
                      onClick={() => setRating(starValue)}
                      className="p-1.5 focus:outline-none focus:ring-2 focus:ring-amber-400 rounded-md transition-transform hover:scale-110"
                      aria-label={`${starValue} স্টার`}
                    >
                      <Star
                        className={`w-8 h-8 transition-colors ${
                          isFilled
                            ? 'fill-amber-400 text-amber-500'
                            : 'text-line-300 hover:text-amber-200'
                        }`}
                      />
                    </button>
                  );
                })}
              </div>

              <p className="text-sm font-bold text-amber-700">
                {starLabels[hoverRating !== null ? hoverRating : rating]}
              </p>
            </div>

            {/* Comment */}
            <div>
              <label className="block text-xs font-semibold text-ink-900 mb-1">
                মতামত বা কাজের বিবরণ (ঐচ্ছিক)
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                maxLength={500}
                placeholder="যন্ত্রটির কার্যক্ষমতা, চালকের দক্ষতা বা সময়ানুবর্তিতা কেমন ছিল লিখুন..."
                className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface focus:outline-none focus:ring-2 focus:ring-leaf-500/50 min-h-[90px]"
              />
              <span className="text-[10px] text-ink-500 block text-right">
                সর্বোচ্চ ৫০০ অক্ষর
              </span>
            </div>

            <div className="pt-2 flex items-center gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                fullWidth
                disabled={isLoading}
              >
                বাতিল
              </Button>
              <Button
                type="submit"
                variant="primary"
                fullWidth
                isLoading={isLoading}
              >
                <Send className="w-4 h-4 mr-1.5" />
                <span>রিভিউ জমা দিন</span>
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
