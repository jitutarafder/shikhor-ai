import React from 'react';
import {
  CROP_CATEGORY_LABELS,
  CROP_STATUS_LABELS,
  CropListingItem,
  QUANTITY_UNIT_LABELS,
} from '../types';
import { MapPin, MessageSquare, Calendar, BadgeCheck } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface CropListingCardProps {
  listing: CropListingItem;
  onContact?: (listing: CropListingItem) => void;
  onEdit?: (listing: CropListingItem) => void;
  isOwner?: boolean;
}

export const CropListingCard: React.FC<CropListingCardProps> = ({
  listing,
  onContact,
  onEdit,
  isOwner = false,
}) => {
  const statusInfo = CROP_STATUS_LABELS[listing.status];

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col justify-between">
      <div>
        {/* Header: Name, Status & Category */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <div className="flex items-center gap-1.5 flex-wrap mb-1.5">
              <span className="inline-block px-2.5 py-0.5 text-xs font-medium rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/50">
                {CROP_CATEGORY_LABELS[listing.category] || listing.category}
              </span>
              {listing.isFarmerVerified && (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 shrink-0"
                  title="যাচাইকৃত কৃষক (পরিচয় ও নিবন্ধন নিশ্চিতকৃত)"
                >
                  <BadgeCheck className="w-3 h-3 text-emerald-600 shrink-0" />
                  যাচাইকৃত কৃষক
                </span>
              )}
            </div>
            <h3 className="text-xl font-bold text-slate-900 leading-snug">{listing.cropName}</h3>
            {listing.farmerName && (
              <span className="text-xs text-slate-500 block mt-0.5">কৃষক: {listing.farmerName}</span>
            )}
          </div>
          <span
            className={`px-2.5 py-1 text-xs font-semibold rounded-full shrink-0 ${statusInfo.color}`}
          >
            {statusInfo.label}
          </span>
        </div>

        {/* Price & Quantity Display (Rule 16: Exact quantities, units, and BDT) */}
        <div className="bg-slate-50 rounded-xl p-3.5 mb-4 border border-slate-100 flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-500 block">একক মূল্য</span>
            <span className="text-2xl font-extrabold text-emerald-700">
              ৳{listing.pricePerUnit.toLocaleString('bn-BD')}
            </span>
            <span className="text-xs text-slate-600 font-medium ml-1">
              /{QUANTITY_UNIT_LABELS[listing.quantityUnit] || listing.quantityUnit}
            </span>
          </div>
          <div className="text-right">
            <span className="text-xs text-slate-500 block">মজুদ পরিমাণ</span>
            <span className="text-lg font-bold text-slate-800">
              {listing.quantity.toLocaleString('bn-BD')}{' '}
              {QUANTITY_UNIT_LABELS[listing.quantityUnit] || listing.quantityUnit}
            </span>
          </div>
        </div>

        {/* Metadata Details */}
        <div className="space-y-2 text-sm text-slate-600 mb-4">
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              {listing.upazila}, {listing.district}
            </span>
            <span className="text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded ml-auto">
              আনুমানিক অবস্থান
            </span>
          </div>

          {listing.expectedHarvestDate && (
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
              <span>প্রত্যাশিত কর্তন: {listing.expectedHarvestDate}</span>
            </div>
          )}

          {listing.description && (
            <p className="text-xs text-slate-600 bg-emerald-50/40 p-2.5 rounded-lg border border-emerald-100/50 mt-2 line-clamp-2">
              {listing.description}
            </p>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-3">
        {isOwner ? (
          <Button
            variant="outline"
            className="w-full text-sm py-2"
            onClick={() => onEdit?.(listing)}
          >
            বিবরণ বা অবস্থা পরিবর্তন
          </Button>
        ) : (
          <Button
            variant="primary"
            className="w-full text-sm py-2.5 flex items-center justify-center gap-2"
            onClick={() => onContact?.(listing)}
            disabled={listing.status !== 'active'}
          >
            <MessageSquare className="w-4 h-4" />
            {listing.status === 'active' ? 'কৃষকের সাথে কথা বলুন' : 'বিক্রয় অনুপলব্ধ'}
          </Button>
        )}
      </div>
    </div>
  );
};
