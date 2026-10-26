/**
 * API client functions for Phase 9 Controlled Pilot.
 */

import {
  PilotDistrictCropConfig,
  PilotFeedback,
  PilotFeedbackCreateInput,
  PilotTelemetryMetrics,
} from './types';

const API_BASE = '/api/v1/pilot';

export async function getPilotConfigApi(): Promise<PilotDistrictCropConfig> {
  const res = await fetch(`${API_BASE}/config`, {
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    throw new Error('পাইলট কনফিগারেশন লোড করা সম্ভব হয়নি।');
  }
  return res.json();
}

export async function submitPilotFeedbackApi(
  payload: PilotFeedbackCreateInput,
  token: string
): Promise<PilotFeedback> {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'পাইলট মতামত সংরক্ষণ করা যায়নি।');
  }
  return res.json();
}

export async function getPilotMetricsApi(token: string): Promise<PilotTelemetryMetrics> {
  const res = await fetch(`${API_BASE}/metrics`, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'পাইলট পরিমাপক লোড করা যায়নি।');
  }
  return res.json();
}

export async function getPilotFeedbackListApi(
  token: string,
  limit: number = 50,
  taskType?: string
): Promise<PilotFeedback[]> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (taskType) {
    params.set('task_type', taskType);
  }

  const res = await fetch(`${API_BASE}/feedback-list?${params.toString()}`, {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error?.message || 'মতামত তালিকা লোড করা যায়নি।');
  }
  return res.json();
}
