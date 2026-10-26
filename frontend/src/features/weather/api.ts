import { EquipmentWeatherAdvisory, EmergencyWeatherAlertsResponse, WeatherPlanResponse } from './types';
import { getErrorMessage } from '../../lib/errors';

async function parseResponse<T>(res: Response, defaultErrorMsg: string): Promise<T> {
  let data: Record<string, unknown> | null = null;
  try {
    data = await res.json() as Record<string, unknown>;
  } catch {
    // response wasn't valid JSON
  }

  if (!res.ok) {
    const errorDetail = getErrorMessage(data, defaultErrorMsg);
    throw new Error(errorDetail);
  }

  return data as unknown as T;
}

export async function getWeatherPlanApi(params: {
  latitude: number;
  longitude: number;
  district?: string;
  upazila?: string;
}): Promise<WeatherPlanResponse> {
  const query = new URLSearchParams({
    latitude: params.latitude.toString(),
    longitude: params.longitude.toString(),
  });
  if (params.district) query.set('district', params.district);
  if (params.upazila) query.set('upazila', params.upazila);

  try {
    const res = await fetch(`/api/v1/weather/plan?${query.toString()}`);
    return await parseResponse<WeatherPlanResponse>(res, 'আবহাওয়ার পূর্বাভাস লোড করা যায়নি।');
  } catch (err: unknown) {
    throw new Error(getErrorMessage(err, 'আবহাওয়ার পূর্বাভাস লোড করা যায়নি।'));
  }
}

export async function getMachineryWeatherAdvisoryApi(params: {
  equipmentType: string;
  targetDate: string;
  latitude: number;
  longitude: number;
}): Promise<EquipmentWeatherAdvisory> {
  const query = new URLSearchParams({
    equipmentType: params.equipmentType,
    targetDate: params.targetDate,
    latitude: params.latitude.toString(),
    longitude: params.longitude.toString(),
  });

  try {
    const res = await fetch(`/api/v1/weather/machinery-advisory?${query.toString()}`);
    return await parseResponse<EquipmentWeatherAdvisory>(res, 'যন্ত্রের আবহাওয়া সতর্কতা যাচাই ব্যর্থ হয়েছে।');
  } catch (err: unknown) {
    throw new Error(getErrorMessage(err, 'যন্ত্রের আবহাওয়া সতর্কতা যাচাই ব্যর্থ হয়েছে।'));
  }
}

export async function checkEmergencyWeatherAlertsApi(
  params: {
    latitude: number;
    longitude: number;
    district?: string;
    upazila?: string;
    sendNotification?: boolean;
  },
  token?: string | null
): Promise<EmergencyWeatherAlertsResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const res = await fetch('/api/v1/weather/check-alerts', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        latitude: params.latitude,
        longitude: params.longitude,
        district: params.district,
        upazila: params.upazila,
        send_notification: params.sendNotification !== false,
      }),
    });

    return await parseResponse<EmergencyWeatherAlertsResponse>(
      res,
      'জরুরি আবহাওয়া সতর্কতা যাচাই করা যায়নি।'
    );
  } catch (err: unknown) {
    throw new Error(getErrorMessage(err, 'জরুরি আবহাওয়া সতর্কতা যাচাই করা যায়নি।'));
  }
}
