import {
  EquipmentAvailability,
  EquipmentCreateInput,
  EquipmentItem,
  EquipmentReviewCreateInput,
  EquipmentReviewItem,
  EquipmentType,
  EquipmentUpdateInput,
  PriceUnit,
} from './types';

export async function searchEquipmentApi(params: {
  equipmentType: EquipmentType;
  priceUnit: PriceUnit;
  latitude: number;
  longitude: number;
  maxRadiusKm?: number;
}): Promise<EquipmentItem[]> {
  const query = new URLSearchParams({
    equipmentType: params.equipmentType,
    priceUnit: params.priceUnit,
    latitude: params.latitude.toString(),
    longitude: params.longitude.toString(),
  });
  if (params.maxRadiusKm) {
    query.set('maxRadiusKm', params.maxRadiusKm.toString());
  }

  const res = await fetch(`/api/v1/equipment?${query.toString()}`);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'যন্ত্রের তালিকা অনুসন্ধানে ব্যর্থ হয়েছে।');
  }
  return data;
}

export async function createEquipmentApi(
  token: string,
  input: EquipmentCreateInput
): Promise<EquipmentItem> {
  const res = await fetch('/api/v1/equipment', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'যন্ত্র নিবন্ধন ব্যর্থ হয়েছে।');
  }
  return data;
}

export async function getMyEquipmentApi(token: string): Promise<EquipmentItem[]> {
  const res = await fetch('/api/v1/equipment/my', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'নিজের যন্ত্র তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function updateEquipmentApi(
  token: string,
  equipmentId: string,
  input: EquipmentUpdateInput
): Promise<EquipmentItem> {
  const res = await fetch(`/api/v1/equipment/${equipmentId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'যন্ত্রের তথ্য হালনাগাদ করা যায়নি।');
  }
  return data;
}

export async function getEquipmentAvailabilityApi(equipmentId: string): Promise<EquipmentAvailability> {
  const res = await fetch(`/api/v1/equipment/${equipmentId}/availability`);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'প্রাপ্যতা ক্যালেন্ডার লোড করা যায়নি।');
  }
  return data;
}

export async function getEquipmentReviewsApi(equipmentId: string): Promise<EquipmentReviewItem[]> {
  const res = await fetch(`/api/v1/equipment/${equipmentId}/reviews`);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'রিভিউ তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function submitEquipmentReviewApi(
  token: string,
  equipmentId: string,
  input: EquipmentReviewCreateInput
): Promise<EquipmentReviewItem> {
  const res = await fetch(`/api/v1/equipment/${equipmentId}/reviews`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'রিভিউ জমা দেওয়া যায়নি।');
  }
  return data;
}

