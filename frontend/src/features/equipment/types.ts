/**
 * Equipment Discovery and Machinery Management types.
 * Strictly complies with AGENTS.md Rule 15 (Fixed ranking formula) and Rule 17 (Approximate coordinates).
 */

export type EquipmentType = 'tractor' | 'harvester' | 'pump' | 'sprayer' | 'power_tiller';

export type PriceUnit = 'per_hour' | 'per_day' | 'per_acre';

export interface RankingBreakdown {
  priceScore: number;
  distanceScore: number;
  rankingScore: number;
  distanceKm: number;
}

export interface EquipmentItem {
  id: string;
  ownerId: string;
  name: string;
  equipmentType: EquipmentType;
  description?: string | null;
  priceAmount: number;
  priceUnit: PriceUnit;
  district: string;
  upazila: string;
  serviceRadiusKm: number;
  isAvailable: boolean;
  isPaused: boolean;
  approximateLat: number;
  approximateLon: number;
  ownerName?: string | null;
  isOwnerVerified?: boolean;
  averageRating?: number | null;
  reviewCount?: number;
  createdAt: string;
  ranking?: RankingBreakdown | null;
}

export interface BookedDateItem {
  date: string;
  rentalDate?: string;
  status: string;
}

export interface EquipmentAvailability {
  equipmentId: string;
  isAvailable: boolean;
  isPaused: boolean;
  bookedDates: BookedDateItem[];
}

export interface EquipmentReviewItem {
  id: string;
  equipmentId: string;
  renterId: string;
  renterName?: string | null;
  rentalRequestId: string;
  rating: number;
  comment?: string | null;
  createdAt: string;
}

export interface EquipmentReviewCreateInput {
  rentalRequestId: string;
  rating: number;
  comment?: string;
}

export interface EquipmentCreateInput {
  name: string;
  equipmentType: EquipmentType;
  description?: string;
  priceAmount: number;
  priceUnit: PriceUnit;
  district: string;
  upazila: string;
  latitude: number;
  longitude: number;
  serviceRadiusKm?: number;
}

export interface EquipmentUpdateInput {
  name?: string;
  description?: string;
  priceAmount?: number;
  serviceRadiusKm?: number;
  isAvailable?: boolean;
  isPaused?: boolean;
}
