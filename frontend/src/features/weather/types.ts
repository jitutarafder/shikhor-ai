/**
 * Types for Weather Planning and Agronomic Guidance.
 * Strictly adheres to AGENTS.md Rule 20 (Separation of facts from recommendations).
 */

export type ActivityType = 'spraying' | 'harvesting' | 'irrigation' | 'machinery';

export type SuitabilityLevel = 'suitable' | 'caution' | 'unfavorable';

export interface WeatherFact {
  timestamp: string;
  temperatureC: number;
  feelsLikeC: number;
  relativeHumidity: number;
  precipitationProbability: number;
  precipitationMm: number;
  windSpeedKmh: number;
  windGustKmh: number;
  weatherCode: number;
  weatherDescriptionBn: string;
}

export interface ActivityRecommendation {
  activityType: ActivityType;
  titleBn: string;
  suitability: SuitabilityLevel;
  reasonSummaryBn: string;
  guidanceBn: string;
  riskFactors: string[];
}

export interface MachineryWeatherWarning {
  warningLevel: 'warning' | 'alert' | 'info' | string;
  titleBn: string;
  messageBn: string;
  affectedEquipment: string[];
}

export interface DailyForecast {
  date: string;
  tempMaxC: number;
  tempMinC: number;
  precipitationProbabilityMax: number;
  precipitationSumMm: number;
  windSpeedMaxKmh: number;
  weatherCode: number;
  weatherDescriptionBn: string;
  activityRecommendations: ActivityRecommendation[];
}

export interface WeatherLocation {
  district?: string | null;
  upazila?: string | null;
  approximateLat: number;
  approximateLon: number;
}

export interface WeatherPlanResponse {
  location: WeatherLocation;
  facts: WeatherFact;
  activityWindows: ActivityRecommendation[];
  threeDayForecast: DailyForecast[];
  equipmentWarnings: MachineryWeatherWarning[];
  providerName: string;
  attribution: string;
  providerTimestamp: string;
  isStale: boolean;
  staleReason?: string | null;
}

export interface EquipmentWeatherAdvisory {
  equipmentType: string;
  targetDate: string;
  isSafeToOperate: boolean;
  warning?: MachineryWeatherWarning | null;
  adviceBn: string;
}

export interface WeatherAlertItem {
  alertType: 'spraying' | 'irrigation' | 'storm' | 'heatwave' | string;
  severity: 'danger' | 'warning' | 'success' | 'info';
  titleBn: string;
  messageBn: string;
  actionGuidanceBn: string;
  urgencyLevel: 'high' | 'medium' | 'low';
  iconType: 'wind' | 'rain' | 'sun' | 'droplet' | 'zap' | 'shield-check' | string;
  timestamp: string;
}

export interface EmergencyWeatherAlertsResponse {
  district?: string | null;
  upazila?: string | null;
  approximateLat: number;
  approximateLon: number;
  alerts: WeatherAlertItem[];
  hasUrgentAlert: boolean;
  notificationDispatched: boolean;
  summaryBn: string;
}

