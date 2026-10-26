/**
 * Crop Marketplace and Buyer Connection types.
 * Strictly complies with:
 * - AGENTS.md Rule 16: Exact quantities, units (maund, kg, ton), and BDT price.
 * - AGENTS.md Rule 17: Approximate coordinate exposure and contact privacy.
 * - AGENTS.md Rule 23: Bangla-first typography and labels.
 */

export type CropCategory =
  | 'paddy'
  | 'wheat'
  | 'maize'
  | 'potato'
  | 'vegetable'
  | 'fruit'
  | 'pulse'
  | 'spice'
  | 'other';

export type QuantityUnit = 'maund' | 'kg' | 'ton';

export type CropListingStatus = 'active' | 'paused' | 'closed';

export const CROP_CATEGORY_LABELS: Record<CropCategory, string> = {
  paddy: 'ধান (Paddy)',
  wheat: 'গম (Wheat)',
  maize: 'ভুট্টা (Maize)',
  potato: 'আলু (Potato)',
  vegetable: 'শাকসবজি (Vegetables)',
  fruit: 'ফলমূল (Fruits)',
  pulse: 'ডাল (Pulses)',
  spice: 'মসলা (Spices)',
  other: 'অন্যান্য (Other)',
};

export const QUANTITY_UNIT_LABELS: Record<QuantityUnit, string> = {
  maund: 'মণ (Maund)',
  kg: 'কেজি (Kg)',
  ton: 'টন (Ton)',
};

export const CROP_STATUS_LABELS: Record<CropListingStatus, { label: string; color: string }> = {
  active: { label: 'বিক্রয়ের জন্য উন্মুক্ত', color: 'bg-emerald-100 text-emerald-800' },
  paused: { label: 'সাময়িক স্থগিত', color: 'bg-amber-100 text-amber-800' },
  closed: { label: 'বিক্রয় সম্পন্ন', color: 'bg-slate-100 text-slate-800' },
};

export interface CropListingItem {
  id: string;
  farmerId: string;
  farmerName?: string;
  farmerRole?: string;
  cropName: string;
  category: CropCategory;
  quantity: number;
  quantityUnit: QuantityUnit;
  pricePerUnit: number;
  expectedHarvestDate?: string | null;
  district: string;
  upazila: string;
  approximateLat: number;
  approximateLon: number;
  isFarmerVerified?: boolean;
  description?: string | null;
  status: CropListingStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CropListingCreateInput {
  cropName: string;
  category: CropCategory;
  quantity: number;
  quantityUnit: QuantityUnit;
  pricePerUnit: number;
  expectedHarvestDate?: string;
  district: string;
  upazila: string;
  latitude: number;
  longitude: number;
  description?: string;
}

export interface CropListingUpdateInput {
  quantity?: number;
  pricePerUnit?: number;
  expectedHarvestDate?: string;
  description?: string;
  status?: CropListingStatus;
}

export interface CropFilterParams {
  category?: CropCategory;
  district?: string;
  minPrice?: number;
  maxPrice?: number;
  minQuantity?: number;
}

export interface SavedBuyerSearchItem {
  id: string;
  buyerId: string;
  name: string;
  category?: CropCategory | null;
  cropName?: string | null;
  district?: string | null;
  maxPrice?: number | null;
  minQuantity?: number | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface SavedBuyerSearchCreateInput {
  name: string;
  category?: CropCategory;
  cropName?: string;
  district?: string;
  maxPrice?: number;
  minQuantity?: number;
}

