import { CropCase, CropFeedback, FeedbackType } from './types';

export async function submitCropCaseApi(
  token: string,
  imageFile: File,
  cropType: string,
  symptoms?: string
): Promise<CropCase> {
  const formData = new FormData();
  formData.append('image', imageFile);
  formData.append('crop_type', cropType);
  if (symptoms) {
    formData.append('symptoms', symptoms);
  }

  const res = await fetch('/api/v1/crop-cases', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ফসল যাচাইয়ে ত্রুটি ঘটেছে।');
  }

  return data;
}

export async function getMyCropCasesApi(token: string): Promise<CropCase[]> {
  const res = await fetch('/api/v1/crop-cases', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'ফসল হিস্ট্রি লোড করা যায়নি।');
  }

  return data;
}

export async function submitCropFeedbackApi(
  token: string,
  caseId: string,
  feedbackType: FeedbackType,
  comments?: string
): Promise<CropFeedback> {
  const res = await fetch(`/api/v1/crop-cases/${caseId}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      feedback_type: feedbackType,
      comments,
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'মতামত গ্রহণ ব্যর্থ হয়েছে।');
  }

  return data;
}

export async function sendCaseToExpertApi(
  token: string,
  caseId: string,
  notes?: string,
  additionalImage?: File
): Promise<CropCase> {
  const formData = new FormData();
  if (notes) {
    formData.append('notes', notes);
  }
  if (additionalImage) {
    formData.append('additional_image', additionalImage);
  }

  const res = await fetch(`/api/v1/crop-cases/${caseId}/send-to-expert`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || 'বিশেষজ্ঞের কাছে পাঠাতে ব্যর্থ হয়েছে।');
  }

  return data;
}

export async function predictCropDiseaseApi(
  imageFile: File,
  crop: string,
  symptoms?: string,
  threshold?: number
): Promise<import('./types').CropDiseasePredictionResult> {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('crop', crop);
  if (symptoms && symptoms.trim()) {
    formData.append('symptoms', symptoms.trim());
  }
  if (threshold !== undefined) {
    formData.append('threshold', threshold.toString());
  }

  const res = await fetch('/api/v1/crop-disease/predict', {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data?.error?.message || data?.detail || 'রোগ সনাক্তকরণে সমস্যা হয়েছে।');
  }

  return data;
}


