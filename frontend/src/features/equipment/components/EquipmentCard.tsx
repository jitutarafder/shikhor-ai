import React, { useState } from 'react';
import { MapPin, Navigation, HelpCircle, PhoneCall, Calendar, BadgeCheck, Star } from 'lucide-react';
import { EquipmentItem } from '../types';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { EquipmentRankingExplainer } from './EquipmentRankingExplainer';

interface EquipmentCardProps {
  equipment: EquipmentItem;
  onBook: (equipment: EquipmentItem) => void;
}

export const EquipmentCard: React.FC<EquipmentCardProps> = ({ equipment, onBook }) => {
  const [showExplainer, setShowExplainer] = useState(false);

  const typeLabels: Record<string, string> = {
    tractor: 'ট্রাক্টর',
    harvester: 'হার্ভেস্টার',
    pump: 'সেচ পাম্প',
    sprayer: 'স্প্রেয়ার',
    power_tiller: 'পাওয়ার টিলার',
  };

  const unitLabels: Record<string, string> = {
    per_hour: 'ঘণ্টা',
    per_day: 'দিন',
    per_acre: 'একর',
  };

  return (
    <>
      <Card hoverEffect className="p-5 flex flex-col justify-between border-line-200 bg-canvas space-y-4">
        <div className="space-y-3">
          {/* Header row: Type badge & Availability */}
          <div className="flex items-center justify-between gap-2">
            <Badge variant="success">
              {typeLabels[equipment.equipmentType] || equipment.equipmentType}
            </Badge>

            {equipment.isAvailable && !equipment.isPaused ? (
              <span className="text-[11px] font-semibold text-forest-700 bg-leaf-100 px-2 py-0.5 rounded-full">
                ভাড়ার জন্য প্রস্তুত
              </span>
            ) : (
              <span className="text-[11px] font-semibold text-ink-600 bg-surface px-2 py-0.5 rounded-full">
                সাময়িক অনুপলব্ধ
              </span>
            )}
          </div>

          {/* Name & Owner Details */}
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-forest-900 line-clamp-1">{equipment.name}</h3>
              {equipment.isOwnerVerified && (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shrink-0"
                  title="যাচাইকৃত যন্ত্রের মালিক (প্রশাসনিক নিরীক্ষা সম্পন্ন)"
                >
                  <BadgeCheck className="w-3 h-3 text-emerald-600 shrink-0" />
                  যাচাইকৃত মালিক
                </span>
              )}
            </div>

            {/* Ratings and Reviews */}
            {equipment.reviewCount && equipment.reviewCount > 0 && equipment.averageRating ? (
              <div className="flex items-center gap-1.5 mt-1 text-xs text-amber-800 font-semibold bg-amber-50 border border-amber-200/80 px-2 py-0.5 rounded-full w-fit">
                <Star className="w-3.5 h-3.5 fill-amber-500 text-amber-500" />
                <span>{equipment.averageRating.toFixed(1)}</span>
                <span className="text-[11px] text-ink-500 font-normal">
                  ({equipment.reviewCount.toLocaleString('bn-BD')} টি রিভিউ)
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-1 mt-1 text-[11px] text-ink-500 bg-surface px-2 py-0.5 rounded-full w-fit border border-line-200">
                <Star className="w-3 h-3 text-ink-400" />
                <span>নতুন তালিকা</span>
              </div>
            )}

            {equipment.ownerName && (
              <span className="text-[11px] text-ink-500 block mt-1">মালিক: {equipment.ownerName}</span>
            )}
            {equipment.description && (
              <p className="text-xs text-ink-600 line-clamp-2 mt-1 leading-relaxed">
                {equipment.description}
              </p>
            )}
          </div>

          {/* Location & Approximate Distance */}
          <div className="space-y-1 text-xs text-ink-600">
            <div className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-forest-700 shrink-0" />
              <span>
                {equipment.district}, {equipment.upazila}
              </span>
            </div>

            {equipment.ranking && (
              <div className="flex items-center gap-1.5 text-forest-700 font-medium">
                <Navigation className="w-3.5 h-3.5 shrink-0" />
                <span>আপনার অবস্থান থেকে ~ {equipment.ranking.distanceKm} কিমি</span>
              </div>
            )}
          </div>

          {/* Price & Service Radius */}
          <div className="pt-2 border-t border-line-200 flex items-baseline justify-between">
            <div>
              <span className="text-xs text-ink-600 block">ভাড়ার হার:</span>
              <span className="text-lg font-bold text-forest-900">
                {equipment.priceAmount.toLocaleString('bn-BD')} ৳
              </span>
              <span className="text-xs text-ink-600 ml-1">
                / {unitLabels[equipment.priceUnit] || equipment.priceUnit}
              </span>
            </div>

            <div className="text-right text-[11px] text-ink-600">
              <span>কভারেজ ব্যাসার্ধ:</span>
              <span className="block font-semibold text-ink-900">
                {equipment.serviceRadiusKm} কিমি
              </span>
            </div>
          </div>

          {/* Rule 15: Transparent ranking pill */}
          {equipment.ranking && (
            <div className="bg-field-wash rounded p-2 flex items-center justify-between text-xs border border-line-200">
              <span className="text-ink-600 flex items-center gap-1">
                <span>র‍্যাঙ্কিং স্কোর:</span>
                <strong className="font-mono text-forest-900">
                  {equipment.ranking.rankingScore.toFixed(3)}
                </strong>
              </span>
              <button
                onClick={() => setShowExplainer(true)}
                className="text-forest-700 hover:text-forest-900 font-semibold flex items-center gap-0.5 underline text-[11px]"
              >
                <span>কেন এই স্থান?</span>
                <HelpCircle className="w-3 h-3" />
              </button>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => alert(`মালিকের ফোন নম্বর যোগাযোগের জন্য সংরক্ষিত রয়েছে। ভাড়ার অনুরোধ পাঠান।`)}
            className="flex-1 text-xs"
            aria-label="মালিকের সাথে যোগাযোগ"
          >
            <PhoneCall className="w-3.5 h-3.5 mr-1 text-forest-700" />
            <span>যোগাযোগ</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => onBook(equipment)}
            disabled={!equipment.isAvailable || equipment.isPaused}
            className="flex-1 text-xs"
          >
            <Calendar className="w-3.5 h-3.5 mr-1" />
            <span>ভাড়া নিন</span>
          </Button>
        </div>
      </Card>

      {showExplainer && equipment.ranking && (
        <EquipmentRankingExplainer
          ranking={equipment.ranking}
          equipmentName={equipment.name}
          onClose={() => setShowExplainer(false)}
        />
      )}
    </>
  );
};
