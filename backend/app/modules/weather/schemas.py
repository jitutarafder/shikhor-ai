"""Pydantic v2 schemas for Weather Planning and Agronomic Guidance.

Strictly adheres to AGENTS.md Rule 20:
- Provider facts are structurally separated from product activity recommendations.
- Provider timestamp and attribution are explicitly captured.
- Stale indicators and reasons are clearly present.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.weather.rules import ActivityType, SuitabilityLevel


class WeatherFactSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    timestamp: datetime
    temperatureC: float = Field(alias="temperature_c", serialization_alias="temperatureC")
    feelsLikeC: float = Field(alias="feels_like_c", serialization_alias="feelsLikeC")
    relativeHumidity: int = Field(alias="relative_humidity", serialization_alias="relativeHumidity")
    precipitationProbability: int = Field(
        alias="precipitation_probability", serialization_alias="precipitationProbability"
    )
    precipitationMm: float = Field(
        alias="precipitation_mm", serialization_alias="precipitationMm"
    )
    windSpeedKmh: float = Field(alias="wind_speed_kmh", serialization_alias="windSpeedKmh")
    windGustKmh: float = Field(alias="wind_gust_kmh", serialization_alias="windGustKmh")
    weatherCode: int = Field(alias="weather_code", serialization_alias="weatherCode")
    weatherDescriptionBn: str = Field(
        alias="weather_description_bn", serialization_alias="weatherDescriptionBn"
    )


class ActivityRecommendationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    activityType: ActivityType = Field(alias="activity_type", serialization_alias="activityType")
    titleBn: str = Field(alias="title_bn", serialization_alias="titleBn")
    suitability: SuitabilityLevel
    reasonSummaryBn: str = Field(
        alias="reason_summary_bn", serialization_alias="reasonSummaryBn"
    )
    guidanceBn: str = Field(alias="guidance_bn", serialization_alias="guidanceBn")
    riskFactors: List[str] = Field(
        default_factory=list, alias="risk_factors", serialization_alias="riskFactors"
    )


class MachineryWeatherWarningSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    warningLevel: str = Field(alias="warning_level", serialization_alias="warningLevel")
    titleBn: str = Field(alias="title_bn", serialization_alias="titleBn")
    messageBn: str = Field(alias="message_bn", serialization_alias="messageBn")
    affectedEquipment: List[str] = Field(
        default_factory=list, alias="affected_equipment", serialization_alias="affectedEquipment"
    )


class DailyForecastSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    date: str
    tempMaxC: float = Field(alias="temp_max_c", serialization_alias="tempMaxC")
    tempMinC: float = Field(alias="temp_min_c", serialization_alias="tempMinC")
    precipitationProbabilityMax: int = Field(
        alias="precipitation_probability_max",
        serialization_alias="precipitationProbabilityMax",
    )
    precipitationSumMm: float = Field(
        alias="precipitation_sum_mm", serialization_alias="precipitationSumMm"
    )
    windSpeedMaxKmh: float = Field(
        alias="wind_speed_max_kmh", serialization_alias="windSpeedMaxKmh"
    )
    weatherCode: int = Field(alias="weather_code", serialization_alias="weatherCode")
    weatherDescriptionBn: str = Field(
        alias="weather_description_bn", serialization_alias="weatherDescriptionBn"
    )
    activityRecommendations: List[ActivityRecommendationSchema] = Field(
        default_factory=list,
        alias="activity_recommendations",
        serialization_alias="activityRecommendations",
    )


class WeatherLocationSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    district: Optional[str] = None
    upazila: Optional[str] = None
    approximateLat: float = Field(alias="approximate_lat", serialization_alias="approximateLat")
    approximateLon: float = Field(alias="approximate_lon", serialization_alias="approximateLon")


class WeatherPlanResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    location: WeatherLocationSchema
    # Rule 20: Provider forecast facts structurally isolated
    facts: WeatherFactSchema
    # Rule 20: Product-generated activity recommendations structurally isolated
    activityWindows: List[ActivityRecommendationSchema] = Field(
        alias="activity_windows", serialization_alias="activityWindows"
    )
    threeDayForecast: List[DailyForecastSchema] = Field(
        alias="three_day_forecast", serialization_alias="threeDayForecast"
    )
    equipmentWarnings: List[MachineryWeatherWarningSchema] = Field(
        default_factory=list,
        alias="equipment_warnings",
        serialization_alias="equipmentWarnings",
    )
    # Attribution and audit
    providerName: str = Field(alias="provider_name", serialization_alias="providerName")
    attribution: str
    providerTimestamp: datetime = Field(
        alias="provider_timestamp", serialization_alias="providerTimestamp"
    )
    isStale: bool = Field(default=False, alias="is_stale", serialization_alias="isStale")
    staleReason: Optional[str] = Field(
        None, alias="stale_reason", serialization_alias="staleReason"
    )


class EquipmentWeatherAdvisoryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    equipmentType: str = Field(alias="equipment_type", serialization_alias="equipmentType")
    targetDate: str = Field(alias="target_date", serialization_alias="targetDate")
    isSafeToOperate: bool = Field(
        alias="is_safe_to_operate", serialization_alias="isSafeToOperate"
    )
    warning: Optional[MachineryWeatherWarningSchema] = None
    adviceBn: str = Field(alias="advice_bn", serialization_alias="adviceBn")


class WeatherAlertItemSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    alertType: str = Field(alias="alert_type", serialization_alias="alertType", description="spraying | irrigation | storm | heatwave")
    severity: str = Field(description="danger | warning | success | info")
    titleBn: str = Field(alias="title_bn", serialization_alias="titleBn")
    messageBn: str = Field(alias="message_bn", serialization_alias="messageBn")
    actionGuidanceBn: str = Field(alias="action_guidance_bn", serialization_alias="actionGuidanceBn")
    urgencyLevel: str = Field(alias="urgency_level", serialization_alias="urgencyLevel", description="high | medium | low")
    iconType: str = Field(alias="icon_type", serialization_alias="iconType")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmergencyWeatherAlertsRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    district: Optional[str] = None
    upazila: Optional[str] = None
    sendNotification: bool = Field(default=True, alias="send_notification")


class EmergencyWeatherAlertsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    district: Optional[str] = None
    upazila: Optional[str] = None
    approximateLat: float = Field(alias="approximate_lat", serialization_alias="approximateLat")
    approximateLon: float = Field(alias="approximate_lon", serialization_alias="approximateLon")
    alerts: List[WeatherAlertItemSchema]
    hasUrgentAlert: bool = Field(alias="has_urgent_alert", serialization_alias="hasUrgentAlert")
    notificationDispatched: bool = Field(alias="notification_dispatched", serialization_alias="notificationDispatched")
    summaryBn: str = Field(alias="summary_bn", serialization_alias="summaryBn")

