import React, { useState } from 'react';
import {
  CROP_CATEGORY_LABELS,
  CropCategory,
  CropListingCreateInput,
  QUANTITY_UNIT_LABELS,
  QuantityUnit,
} from '../types';
import { X, AlertCircle } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { getErrorMessage } from '../../../lib/errors';

interface CreateCropListingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (input: CropListingCreateInput) => Promise<void>;
}

export const CreateCropListingModal: React.FC<CreateCropListingModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [cropName, setCropName] = useState('');
  const [category, setCategory] = useState<CropCategory>('paddy');
  const [quantity, setQuantity] = useState<number>(50);
  const [quantityUnit, setQuantityUnit] = useState<QuantityUnit>('maund');
  const [pricePerUnit, setPricePerUnit] = useState<number>(1200);
  const [expectedHarvestDate, setExpectedHarvestDate] = useState('');
  const [district, setDistrict] = useState('দিনাজপুর');
  const [upazila, setUpazila] = useState('বীরগঞ্জ');
  const [latitude] = useState(25.85);
  const [longitude] = useState(88.66);
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cropName.trim()) {
      setError('ফসলের নাম প্রদান করা আবশ্যক।');
      return;
    }
    if (quantity <= 0) {
      setError('পরিমাণ অবশ্যই শূন্যের বেশি হতে হবে।');
      return;
    }
    if (pricePerUnit <= 0) {
      setError('মূল্য অবশ্যই শূন্যের বেশি হতে হবে।');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await onSubmit({
        cropName: cropName.trim(),
        category,
        quantity: Number(quantity),
        quantityUnit,
        pricePerUnit: Math.round(Number(pricePerUnit)),
        expectedHarvestDate: expectedHarvestDate || undefined,
        district: district.trim(),
        upazila: upazila.trim(),
        latitude: Number(latitude),
        longitude: Number(longitude),
        description: description.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'সংরক্ষণ ব্যর্থ হয়েছে। আবার চেষ্টা করুন।'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-100 p-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-5">
          <div>
            <h2 className="text-xl font-bold text-slate-900">নতুন ফসলের তথ্য প্রকাশ করুন</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              পাইকার ও ক্রেতারা আপনার ফসলের তথ্য দেখে সরাসরি ইন-বক্সে যোগাযোগ করবেন
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm flex items-start gap-2">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-sm">
          <div>
            <label className="block text-slate-700 font-semibold mb-1">
              ফসলের নাম ও জাত <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="যেমন: মিনিকেট ধান, বারি আলু-৮, কাঁচা মরিচ"
              value={cropName}
              onChange={(e) => setCropName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">ফসলের ধরন</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as CropCategory)}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
              >
                {Object.entries(CROP_CATEGORY_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-slate-700 font-semibold mb-1">পরিমাপের একক</label>
              <select
                value={quantityUnit}
                onChange={(e) => setQuantityUnit(e.target.value as QuantityUnit)}
                className="w-full px-3 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 bg-white"
              >
                {Object.entries(QUANTITY_UNIT_LABELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                মজুদ পরিমাণ <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="any"
                min="0.1"
                required
                value={quantity}
                onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                একক প্রতি দাম (টাকা) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                min="1"
                required
                value={pricePerUnit}
                onChange={(e) => setPricePerUnit(parseInt(e.target.value, 10) || 0)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-700 font-semibold mb-1">
              প্রত্যাশিত ফসল তোলার তারিখ (ঐচ্ছিক)
            </label>
            <input
              type="date"
              value={expectedHarvestDate}
              onChange={(e) => setExpectedHarvestDate(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                জেলা <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="যেমন: দিনাজপুর"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                উপজেলা <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                required
                placeholder="যেমন: বীরগঞ্জ"
                value={upazila}
                onChange={(e) => setUpazila(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-700 font-semibold mb-1">বিস্তারিত বিবরণ (ঐচ্ছিক)</label>
            <textarea
              rows={3}
              placeholder="ফসলের গুণগত মান, আর্দ্রতা বা সরবরাহের শর্ত লিখুন..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
            />
          </div>

          <div className="bg-emerald-50/60 p-3 rounded-xl border border-emerald-100 text-xs text-emerald-800">
            🛡️ <strong>গোপনীয়তা সুরক্ষা:</strong> আপনার সঠিক ফোন নম্বর বা বাড়ির সঠিক অবস্থান ক্রেতাদের কাছে প্রকাশ পাবে না। ক্রেতারা প্ল্যাটফর্মের চ্যাটবক্সের মাধ্যমে যোগাযোগ করবেন।
          </div>

          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
            <Button variant="outline" type="button" onClick={onClose} disabled={loading}>
              বাতিল
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? 'প্রকাশ হচ্ছে...' : 'তালিকা প্রকাশ করুন'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
