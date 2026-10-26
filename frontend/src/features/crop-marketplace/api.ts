import {
  CropFilterParams,
  CropListingCreateInput,
  CropListingItem,
  CropListingUpdateInput,
  SavedBuyerSearchCreateInput,
  SavedBuyerSearchItem,
} from './types';

export async function getCropListingsApi(
  filters?: CropFilterParams
): Promise<CropListingItem[]> {
  const params = new URLSearchParams();
  if (filters?.category) params.append('category', filters.category);
  if (filters?.district) params.append('district', filters.district);
  if (filters?.minPrice !== undefined) params.append('minPrice', filters.minPrice.toString());
  if (filters?.maxPrice !== undefined) params.append('maxPrice', filters.maxPrice.toString());
  if (filters?.minQuantity !== undefined) params.append('minQuantity', filters.minQuantity.toString());

  const url = `/api/v1/crop-listings${params.toString() ? `?${params.toString()}` : ''}`;
  const res = await fetch(url);
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ফসলের তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function getMyCropListingsApi(token: string): Promise<CropListingItem[]> {
  const res = await fetch('/api/v1/crop-listings/my', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'আপনার ফসলের তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function createCropListingApi(
  token: string,
  input: CropListingCreateInput
): Promise<CropListingItem> {
  const res = await fetch('/api/v1/crop-listings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ফসলের তথ্য প্রকাশ করা সম্ভব হয়নি।');
  }
  return data;
}

export async function updateCropListingApi(
  token: string,
  listingId: string,
  input: CropListingUpdateInput
): Promise<CropListingItem> {
  const res = await fetch(`/api/v1/crop-listings/${listingId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ফসলের তথ্য হালনাগাদ করা যায়নি।');
  }
  return data;
}

export async function getSavedSearchesApi(token: string): Promise<SavedBuyerSearchItem[]> {
  const res = await fetch('/api/v1/crop-listings/saved-searches', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'সংরক্ষিত অনুসন্ধান লোড করা যায়নি।');
  }
  return data;
}

export async function createSavedSearchApi(
  token: string,
  input: SavedBuyerSearchCreateInput
): Promise<SavedBuyerSearchItem> {
  const res = await fetch('/api/v1/crop-listings/saved-searches', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'অনুসন্ধান সংরক্ষণ করা যায়নি।');
  }
  return data;
}

export async function deleteSavedSearchApi(token: string, searchId: string): Promise<void> {
  const res = await fetch(`/api/v1/crop-listings/saved-searches/${searchId}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data?.error?.message || 'সংরক্ষিত অনুসন্ধান মুছে ফেলা যায়নি।');
  }
}

