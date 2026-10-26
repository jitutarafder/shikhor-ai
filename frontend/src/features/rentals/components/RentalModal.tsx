import React, { useEffect, useState } from 'react';
import { X, Clock, DollarSign, Send, AlertCircle, CheckCircle2, CloudSun, AlertTriangle } from 'lucide-react';
import { EquipmentItem } from '../../equipment/types';
import { EquipmentAvailabilityCalendar } from '../../equipment/components/EquipmentAvailabilityCalendar';
import { createRentalRequestApi } from '../api';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../../components/ui/Button';
import { getMachineryWeatherAdvisoryApi } from '../../weather/api';
import { EquipmentWeatherAdvisory } from '../../weather/types';
import { getErrorMessage } from '../../../lib/errors';

interface RentalModalProps {
  equipment: EquipmentItem;
  onClose: () => void;
  onSuccess: () => void;
}

export const RentalModal: React.FC<RentalModalProps> = ({ equipment, onClose, onSuccess }) => {
  const { token } = useAuth();

  // Tomorrow as default date in YYYY-MM-DD format
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const defaultDateStr = tomorrow.toISOString().split('T')[0];

  const [selectedDates, setSelectedDates] = useState<string[]>([defaultDateStr]);
  const [rentalDate, setRentalDate] = useState(defaultDateStr);
  const [durationUnits, setDurationUnits] = useState(1);
  const [note, setNote] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [weatherAdvisory, setWeatherAdvisory] = useState<EquipmentWeatherAdvisory | null>(null);

  useEffect(() => {
    let isMounted = true;
    getMachineryWeatherAdvisoryApi({
      equipmentType: equipment.equipmentType,
      targetDate: selectedDates[0] || rentalDate,
      latitude: equipment.approximateLat,
      longitude: equipment.approximateLon,
    })
      .then((adv) => {
        if (isMounted) setWeatherAdvisory(adv);
      })
      .catch(() => {
        // Silently ignore weather network advisory failures
      });
    return () => {
      isMounted = false;
    };
  }, [selectedDates, rentalDate, equipment]);

  const unitLabels: Record<string, string> = {
    per_hour: 'ঘণ্টা',
    per_day: 'দিন',
    per_acre: 'একর',
  };

  const effectiveUnits = equipment.priceUnit === 'per_day' ? Math.max(1, selectedDates.length) : Math.max(1, durationUnits);
  const totalEstimatedPrice = equipment.priceAmount * effectiveUnits;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) {
      setErrorMsg('ভাড়ার অনুরোধ পাঠাতে অনুগ্রহ করে লগ ইন করুন।');
      return;
    }

    if (selectedDates.length === 0) {
      setErrorMsg('অনুগ্রহ করে ক্যালেন্ডার থেকে অন্তত ১টি তারিখ নির্বাচন করুন।');
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      // Rule 21: Client-side idempotency key for replay-safe offline sync
      const idempotencyKey =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `rent-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

      await createRentalRequestApi(token, {
        equipmentId: equipment.id,
        rentalDate: selectedDates[0],
        selectedDates,
        durationUnits: effectiveUnits,
        note: note.trim() || undefined,
        idempotencyKey,
      });

      setIsSuccess(true);
      setTimeout(() => {
        onSuccess();
      }, 1500);
    } catch (err: unknown) {
      setErrorMsg(getErrorMessage(err, 'ভাড়ার অনুরোধ পাঠানো ব্যর্থ হয়েছে। পুনরায় চেষ্টা করুন।'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-900/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-canvas border border-line-200 rounded-card max-w-lg w-full p-6 shadow-float space-y-5 max-h-[92vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-3 border-b border-line-200 sticky top-0 bg-canvas z-10">
          <div>
            <h3 className="text-lg font-bold text-forest-900">ভাড়ার অনুরোধ প্রেরণ</h3>
            <p className="text-xs text-ink-600">{equipment.name}</p>
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
            <h4 className="text-lg font-bold text-forest-900">অনুরোধ সফলভাবে পাঠানো হয়েছে!</h4>
            <p className="text-xs text-ink-600">
              মালিকের সম্মতির পর আপনার বুকিং নিশ্চিত হবে। আপনি ড্যাশবোর্ড থেকে অগ্রগতি দেখতে পারেন।
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

            {/* Equipment Availability Calendar */}
            <EquipmentAvailabilityCalendar
              equipmentId={equipment.id}
              selectedDates={selectedDates}
              onSelectDates={(newDates) => {
                setSelectedDates(newDates);
                if (newDates.length > 0) {
                  setRentalDate(newDates[0]);
                }
              }}
              onToggleDate={(clickedDate) => {
                const next = selectedDates.includes(clickedDate)
                  ? selectedDates.filter((d) => d !== clickedDate)
                  : [...selectedDates, clickedDate].sort();
                setSelectedDates(next);
                if (next.length > 0) {
                  setRentalDate(next[0]);
                }
              }}
            />

            {/* Selected dates badge list */}
            {selectedDates.length > 0 ? (
              <div className="p-3 bg-leaf-50/70 border border-leaf-300/80 rounded-btn text-xs space-y-1.5">
                <div className="flex items-center justify-between text-forest-900 font-semibold">
                  <span>নির্ধারিত তারিখসমূহ ({selectedDates.length.toLocaleString('bn-BD')} টি দিন):</span>
                  {equipment.priceUnit === 'per_day' && (
                    <span className="text-[11px] font-bold text-forest-800 bg-white px-2 py-0.5 rounded border border-leaf-200">
                      মেয়াদ: {selectedDates.length.toLocaleString('bn-BD')} দিন
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5 pt-0.5">
                  {selectedDates.map((d) => (
                    <span
                      key={d}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-forest-900 text-white font-medium text-[11px] shadow-xs"
                    >
                      <span>{new Date(d).toLocaleDateString('bn-BD', { day: 'numeric', month: 'short' })}</span>
                      <button
                        type="button"
                        onClick={() => {
                          const next = selectedDates.filter((x) => x !== d);
                          setSelectedDates(next);
                          if (next.length > 0) setRentalDate(next[0]);
                        }}
                        className="hover:text-rose-300 font-bold ml-0.5"
                        title="এই তারিখটি বাদ দিন"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-btn text-xs text-amber-800">
                অনুগ্রহ করে উপরের ক্যালেন্ডার থেকে অন্তত ১টি তারিখ নির্ধারণ করুন।
              </div>
            )}

            {/* Weather Advisory for Machinery */}
            {weatherAdvisory && (
              <div
                className={`p-2.5 rounded-btn text-xs flex items-start gap-2 border ${
                  weatherAdvisory.isSafeToOperate
                    ? 'bg-leaf-100/60 border-leaf-500/20 text-forest-900'
                    : 'bg-paddy-400/20 border-paddy-400/30 text-soil-700'
                }`}
              >
                {weatherAdvisory.isSafeToOperate ? (
                  <CloudSun className="w-4 h-4 text-forest-700 shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-soil-700 shrink-0 mt-0.5" />
                )}
                <span className="leading-snug">{weatherAdvisory.adviceBn}</span>
              </div>
            )}

            {equipment.priceUnit !== 'per_day' && (
              <div>
                <label className="block text-xs font-semibold text-ink-900 mb-1 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-forest-700" />
                  <span>কাজের পরিমাণ ({unitLabels[equipment.priceUnit] || equipment.priceUnit})</span>
                </label>
                <input
                  type="number"
                  required
                  min={1}
                  max={100}
                  value={durationUnits}
                  onChange={(e) => setDurationUnits(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface focus:outline-none focus:ring-2 focus:ring-leaf-500/50 min-h-[44px]"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-ink-900 mb-1">
                বিশেষ দ্রষ্টব্য বা বিবরণ (ঐচ্ছিক)
              </label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                maxLength={300}
                placeholder="যেমন: জমির অবস্থান, মাটির ধরন বা বিশেষ সময়..."
                className="w-full px-3 py-2 text-sm rounded-btn border border-line-200 bg-surface focus:outline-none focus:ring-2 focus:ring-leaf-500/50 min-h-[80px]"
              />
            </div>

            {/* Total calculation banner */}
            <div className="p-3.5 bg-field-wash rounded-btn border border-line-200 flex items-center justify-between text-sm">
              <span className="text-ink-600 flex items-center gap-1.5">
                <DollarSign className="w-4 h-4 text-forest-700" />
                <span>আনুমানিক মোট খরচ:</span>
              </span>
              <span className="font-bold text-forest-900 text-base">
                {totalEstimatedPrice.toLocaleString('bn-BD')} ৳
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
                <span>অনুরোধ পাঠান</span>
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
