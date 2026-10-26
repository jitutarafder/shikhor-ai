import { CropCase } from '../crop-assistant/types';
import { ExpertCaseReview, ExpertCaseReviewCreateInput } from './types';

export async function getPendingExpertCasesApi(
  token: string,
  cropType?: string
): Promise<CropCase[]> {
  const url = new URL('/api/v1/expert/cases/pending', window.location.origin);
  if (cropType) {
    url.searchParams.set('crop_type', cropType);
  }

  const res = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'পেন্ডিং কেস তালিকা লোড করা যায়নি।');
  }

  return data;
}

export async function submitExpertCaseReviewApi(
  caseId: string,
  payload: ExpertCaseReviewCreateInput,
  token: string
): Promise<ExpertCaseReview> {
  const res = await fetch(`/api/v1/expert/cases/${caseId}/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'বিশেষজ্ঞ রিভিউ জমা দিতে সমস্যা হয়েছে।');
  }

  return data;
}

export async function getExpertCaseReviewApi(
  caseId: string,
  token: string
): Promise<ExpertCaseReview> {
  const res = await fetch(`/api/v1/expert/cases/${caseId}/review`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'বিশেষজ্ঞ রিভিউ লোড করা যায়নি।');
  }

  return data;
}
