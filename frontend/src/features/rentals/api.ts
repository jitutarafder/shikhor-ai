import {
  RentalRequestCreateInput,
  RentalRequestItem,
  RentalStatus,
  RentalStatusUpdateInput,
} from './types';

export async function createRentalRequestApi(
  token: string,
  input: RentalRequestCreateInput
): Promise<RentalRequestItem> {
  const res = await fetch('/api/v1/rentals', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(input),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ভাড়ার অনুরোধ পাঠানো ব্যর্থ হয়েছে।');
  }
  return data;
}

export async function getMyRentalsApi(token: string): Promise<RentalRequestItem[]> {
  const res = await fetch('/api/v1/rentals', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ভাড়ার অনুরোধ তালিকা লোড করা যায়নি।');
  }
  return data;
}

export async function updateRentalStatusApi(
  token: string,
  rentalId: string,
  targetStatus: RentalStatus
): Promise<RentalRequestItem> {
  const payload: RentalStatusUpdateInput = { targetStatus };
  const res = await fetch(`/api/v1/rentals/${rentalId}/status`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ভাড়ার অবস্থা পরিবর্তন করা যায়নি।');
  }
  return data;
}
