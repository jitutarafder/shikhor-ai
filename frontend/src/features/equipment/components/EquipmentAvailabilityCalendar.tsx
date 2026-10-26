import React, { useEffect, useState } from 'react';
import { Calendar as CalendarIcon, AlertCircle, Loader2, Check, Sparkles, RotateCcw } from 'lucide-react';
import { getEquipmentAvailabilityApi } from '../api';
import { BookedDateItem } from '../types';
import { getErrorMessage } from '../../../lib/errors';

interface EquipmentAvailabilityCalendarProps {
  equipmentId: string;
  selectedDates?: string[];
  selectedDate?: string; // backwards compatibility
  onToggleDate?: (date: string) => void;
  onSelectDate?: (date: string) => void;
  onSelectDates?: (dates: string[]) => void;
}

export const EquipmentAvailabilityCalendar: React.FC<EquipmentAvailabilityCalendarProps> = ({
  equipmentId,
  selectedDates = [],
  selectedDate,
  onToggleDate,
  onSelectDate,
  onSelectDates,
}) => {
  const [loading, setLoading] = useState(true);
  const [bookedDates, setBookedDates] = useState<BookedDateItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Normalize active selected dates array
  const activeSelectedDates = selectedDates.length > 0
    ? selectedDates
    : selectedDate
    ? [selectedDate]
    : [];

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getEquipmentAvailabilityApi(equipmentId)
      .then((data) => {
        if (isMounted) {
          setBookedDates(data.bookedDates || []);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(getErrorMessage(err, 'প্রাপ্যতা তথ্য লোড করা যায়নি'));
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [equipmentId]);

  const bookedSet = new Set(
    bookedDates.map((b) => b.date || b.rentalDate || '').filter(Boolean)
  );

  // Generate upcoming 14 days starting from today
  const days: { dateStr: string; dayNum: number; dayName: string; isBooked: boolean; isToday: boolean }[] = [];
  const today = new Date();
  
  const banglaDayNames = ['রবি', 'সোম', 'মঙ্গল', 'বুধ', 'বৃহঃ', 'শুক্র', 'শনি'];

  for (let i = 0; i < 14; i++) {
    const d = new Date();
    d.setDate(today.getDate() + i);
    const dateStr = d.toISOString().split('T')[0];
    const isBooked = bookedSet.has(dateStr);
    days.push({
      dateStr,
      dayNum: d.getDate(),
      dayName: banglaDayNames[d.getDay()],
      isBooked,
      isToday: i === 0,
    });
  }

  const handleDateClick = (dateStr: string) => {
    if (onToggleDate) {
      onToggleDate(dateStr);
    } else if (onSelectDates) {
      if (activeSelectedDates.includes(dateStr)) {
        onSelectDates(activeSelectedDates.filter((d) => d !== dateStr));
      } else {
        onSelectDates([...activeSelectedDates, dateStr].sort());
      }
    } else if (onSelectDate) {
      onSelectDate(dateStr);
    }
  };

  const handleSelectConsecutive = (count: number) => {
    const availableDates = days
      .filter((d) => !d.isBooked && !d.isToday)
      .slice(0, count)
      .map((d) => d.dateStr);

    if (onSelectDates) {
      onSelectDates(availableDates);
    } else if (onSelectDate && availableDates.length > 0) {
      onSelectDate(availableDates[0]);
    }
  };

  const handleClear = () => {
    if (onSelectDates) {
      onSelectDates([]);
    } else if (onSelectDate) {
      onSelectDate('');
    }
  };

  const conflictingDates = activeSelectedDates.filter((d) => bookedSet.has(d));

  return (
    <div className="bg-surface rounded-card border border-line-200 p-3.5 space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-1.5 text-xs font-bold text-forest-900">
          <CalendarIcon className="w-4 h-4 text-forest-700" />
          <span>যন্ত্রের প্রাপ্যতা ক্যালেন্ডার (পরবর্তী ১৪ দিন)</span>
        </div>
        {loading ? (
          <Loader2 className="w-3.5 h-3.5 text-forest-700 animate-spin" />
        ) : (
          <span className="text-[11px] font-semibold text-forest-800 bg-leaf-100/70 border border-leaf-300/60 px-2 py-0.5 rounded-full flex items-center gap-1">
            <Check className="w-3 h-3 text-forest-700" />
            <span>নির্ধারিত: {activeSelectedDates.length.toLocaleString('bn-BD')} টি দিন</span>
          </span>
        )}
      </div>

      {error ? (
        <p className="text-xs text-danger-600">{error}</p>
      ) : loading ? (
        <div className="py-4 text-center text-xs text-ink-500">প্রাপ্যতা লোড হচ্ছে...</div>
      ) : (
        <>
          {/* Quick Selection Helpers */}
          <div className="flex items-center justify-between gap-1.5 flex-wrap text-xs">
            <span className="text-[11px] text-ink-600 font-medium">
              💡 ক্যালেন্ডারের যেকোনো তারিখে ক্লিক করে একাধিক দিন নির্ধারণ করুন:
            </span>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => handleSelectConsecutive(2)}
                className="text-[11px] px-2 py-0.5 rounded bg-leaf-100 text-forest-800 hover:bg-leaf-200 font-medium transition-colors flex items-center gap-1"
                title="পরবর্তী খালি ২ দিন নির্বাচন করুন"
              >
                <Sparkles className="w-3 h-3 text-forest-700" />
                <span>২ দিন</span>
              </button>
              <button
                type="button"
                onClick={() => handleSelectConsecutive(3)}
                className="text-[11px] px-2 py-0.5 rounded bg-leaf-100 text-forest-800 hover:bg-leaf-200 font-medium transition-colors flex items-center gap-1"
                title="পরবর্তী খালি ৩ দিন নির্বাচন করুন"
              >
                <Sparkles className="w-3 h-3 text-forest-700" />
                <span>৩ দিন</span>
              </button>
              {activeSelectedDates.length > 0 && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="text-[11px] px-2 py-0.5 rounded text-ink-600 hover:text-ink-900 bg-surface border border-line-200 flex items-center gap-1"
                  title="সব নির্বাচন মুছুন"
                >
                  <RotateCcw className="w-2.5 h-2.5" />
                  <span>মুছুন</span>
                </button>
              )}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-3 text-[11px] text-ink-600 bg-canvas px-2.5 py-1 rounded border border-line-200">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
              <span>খালি (উপলব্ধ)</span>
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
              <span>বুকড (অনুপলব্ধ)</span>
            </span>
            <span className="flex items-center gap-1 ml-auto text-forest-800 font-medium">
              <span>ইতিমধ্যে বুকড: {bookedDates.length.toLocaleString('bn-BD')} দিন</span>
            </span>
          </div>

          {/* 14-day interactive grid */}
          <div className="grid grid-cols-7 gap-1.5">
            {days.map((item) => {
              const isSelected = activeSelectedDates.includes(item.dateStr);
              return (
                <button
                  key={item.dateStr}
                  type="button"
                  disabled={item.isBooked}
                  onClick={() => handleDateClick(item.dateStr)}
                  className={`flex flex-col items-center justify-center p-1.5 rounded-md border text-center transition-all ${
                    item.isBooked
                      ? 'bg-rose-50 border-rose-200 text-rose-800 cursor-not-allowed opacity-75'
                      : isSelected
                      ? 'bg-forest-900 border-forest-900 text-white font-bold ring-2 ring-forest-600/40 shadow-sm'
                      : 'bg-canvas border-line-200 text-ink-800 hover:border-leaf-500 hover:bg-leaf-50'
                  }`}
                  title={
                    item.isBooked
                      ? 'এই তারিখে যন্ত্রটি বুকড রয়েছে'
                      : isSelected
                      ? 'ক্লিক করে এই তারিখ বাতিল করুন'
                      : 'ক্লিক করে এই তারিখ বুকিংয়ে যুক্ত করুন'
                  }
                >
                  <span className={`text-[10px] ${isSelected ? 'text-forest-200' : 'text-ink-500'}`}>
                    {item.dayName}
                  </span>
                  <span className="text-sm font-semibold leading-tight my-0.5">
                    {item.dayNum.toLocaleString('bn-BD')}
                  </span>
                  <span
                    className={`text-[9px] px-1 rounded-sm leading-tight font-medium ${
                      item.isBooked
                        ? 'bg-rose-100 text-rose-700'
                        : isSelected
                        ? 'bg-forest-800 text-forest-100'
                        : 'text-emerald-700'
                    }`}
                  >
                    {item.isBooked ? 'বুকড' : isSelected ? '✓ নির্ধারিত' : 'খালি'}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Validation Notice if any selected date is booked */}
          {conflictingDates.length > 0 && (
            <div className="p-2.5 bg-rose-50 border border-rose-200 rounded text-xs text-rose-800 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <span>
                <strong>সতর্কতা:</strong> আপনার নির্ধারিত তারিখগুলোর মধ্যে ({conflictingDates.join(', ')}) ইতিমধ্যে বুকড রয়েছে। অনুগ্রহ করে ক্যালেন্ডার থেকে শুধুমাত্র সবুজ 'খালি' তারিখ নির্বাচন করুন।
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
};
