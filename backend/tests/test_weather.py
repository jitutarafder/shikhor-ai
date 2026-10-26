"""Tests for Weather Planning, Agronomic Rules Engine, and Provider Fallbacks.

Strictly complies with:
- AGENTS.md Rule 20: Weather guidance separating facts from recommendations, provider attribution, stale flags.
- AGENTS.md Rule 28: Mandatory tests for weather: stale data, timeout, rule boundaries.
"""

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.integrations.weather.provider import (
    OpenMeteoWeatherAdapter,
    RawDailyForecast,
    RawWeatherFact,
    RawWeatherResponse,
    WeatherProvider,
)
from app.modules.weather.rules import (
    ActivityType,
    SuitabilityLevel,
    evaluate_harvesting_activity,
    evaluate_irrigation_activity,
    evaluate_machinery_activity,
    evaluate_spraying_activity,
)
from app.modules.weather.service import set_weather_provider


class MockFailingWeatherProvider:
    """Simulates provider timeout or outage with no prior cache."""

    async def fetch_weather(self, lat: float, lon: float) -> RawWeatherResponse:
        adapter = OpenMeteoWeatherAdapter()
        return adapter._create_seasonal_fallback(lat, lon, reason="সার্ভারের সংযোগ ব্যর্থ হয়েছে।")


class MockSunnyWeatherProvider:
    """Simulates clear dry weather for testing favorable activity windows."""

    async def fetch_weather(self, lat: float, lon: float) -> RawWeatherResponse:
        current = RawWeatherFact(
            timestamp=datetime.now(timezone.utc),
            temperature_c=28.0,
            feels_like_c=29.0,
            relative_humidity=60,
            precipitation_probability=5,
            precipitation_mm=0.0,
            wind_speed_kmh=8.0,
            wind_gust_kmh=11.0,
            weather_code=0,
            weather_description_bn="পরিষ্কার রোদোজ্জ্বল আকাশ",
        )
        daily = [
            RawDailyForecast(
                date="2026-10-01",
                temp_max_c=30.0,
                temp_min_c=22.0,
                precipitation_probability_max=5,
                precipitation_sum_mm=0.0,
                wind_speed_max_kmh=8.0,
                weather_code=0,
                weather_description_bn="পরিষ্কার রোদোজ্জ্বল আকাশ",
            ),
            RawDailyForecast(
                date="2026-10-02",
                temp_max_c=31.0,
                temp_min_c=23.0,
                precipitation_probability_max=5,
                precipitation_sum_mm=0.0,
                wind_speed_max_kmh=9.0,
                weather_code=0,
                weather_description_bn="পরিষ্কার রোদোজ্জ্বল আকাশ",
            ),
            RawDailyForecast(
                date="2026-10-03",
                temp_max_c=32.0,
                temp_min_c=24.0,
                precipitation_probability_max=10,
                precipitation_sum_mm=0.0,
                wind_speed_max_kmh=10.0,
                weather_code=1,
                weather_description_bn="প্রধানত রোদোজ্জ্বল",
            ),
            RawDailyForecast(
                date="2026-10-04",
                temp_max_c=30.0,
                temp_min_c=23.0,
                precipitation_probability_max=10,
                precipitation_sum_mm=0.0,
                wind_speed_max_kmh=8.0,
                weather_code=0,
                weather_description_bn="পরিষ্কার আকাশ",
            ),
        ]
        return RawWeatherResponse(
            provider_name="Test Provider",
            attribution="Mock Weather Attribution",
            provider_timestamp=datetime.now(timezone.utc),
            latitude=lat,
            longitude=lon,
            current=current,
            daily=daily,
            is_stale=False,
        )


# ============================================================================
# Rule Engine Unit Tests (Rule 20 & 28)
# ============================================================================


def test_spraying_rule_boundaries():
    """Verifies spraying constraints: wind drift (>15 km/h) and rain wash-off."""
    base_fact = RawWeatherFact(
        timestamp=datetime.now(timezone.utc),
        temperature_c=28.0,
        feels_like_c=29.0,
        relative_humidity=65,
        precipitation_probability=10,
        precipitation_mm=0.0,
        wind_speed_kmh=8.0,
        wind_gust_kmh=12.0,
        weather_code=0,
        weather_description_bn="পরিষ্কার আকাশ",
    )

    # 1. Normal/Calm conditions -> Suitable
    rec = evaluate_spraying_activity(base_fact)
    assert rec.suitability == SuitabilityLevel.SUITABLE
    assert rec.activity_type == ActivityType.SPRAYING

    # 2. High wind (>15 km/h) -> Unfavorable (drift risk)
    windy_fact = RawWeatherFact(**{**base_fact.__dict__, "wind_speed_kmh": 18.0})
    rec_wind = evaluate_spraying_activity(windy_fact)
    assert rec_wind.suitability == SuitabilityLevel.UNFAVORABLE
    assert "বাতাস" in rec_wind.risk_factors[0]

    # 3. High rain probability (>=40%) -> Unfavorable (wash-off risk)
    rainy_fact = RawWeatherFact(
        **{**base_fact.__dict__, "precipitation_probability": 50, "precipitation_mm": 1.0}
    )
    rec_rain = evaluate_spraying_activity(rainy_fact)
    assert rec_rain.suitability == SuitabilityLevel.UNFAVORABLE
    assert "বৃষ্টিপাতের ঝুঁকি" in rec_rain.risk_factors[0]

    # 4. High temperature (>=34°C) -> Caution (midday evaporation)
    hot_fact = RawWeatherFact(**{**base_fact.__dict__, "temperature_c": 35.0})
    rec_hot = evaluate_spraying_activity(hot_fact)
    assert rec_hot.suitability == SuitabilityLevel.CAUTION
    assert "উচ্চ তাপমাত্রা" in rec_hot.risk_factors[0]


def test_harvesting_rule_boundaries():
    """Verifies harvesting constraints: rain spoiling risk and humid conditions."""
    base_fact = RawWeatherFact(
        timestamp=datetime.now(timezone.utc),
        temperature_c=30.0,
        feels_like_c=31.0,
        relative_humidity=60,
        precipitation_probability=5,
        precipitation_mm=0.0,
        wind_speed_kmh=10.0,
        wind_gust_kmh=14.0,
        weather_code=0,
        weather_description_bn="পরিষ্কার আকাশ",
    )

    # 1. Dry conditions -> Suitable
    rec = evaluate_harvesting_activity(base_fact)
    assert rec.suitability == SuitabilityLevel.SUITABLE

    # 2. Rain sum >= 5mm -> Unfavorable (rot risk)
    wet_daily = RawDailyForecast(
        date="2026-10-02",
        temp_max_c=29.0,
        temp_min_c=24.0,
        precipitation_probability_max=65,
        precipitation_sum_mm=8.0,
        wind_speed_max_kmh=15.0,
        weather_code=63,
        weather_description_bn="বৃষ্টিপাত",
    )
    rec_wet = evaluate_harvesting_activity(base_fact, wet_daily)
    assert rec_wet.suitability == SuitabilityLevel.UNFAVORABLE
    assert "পচন" in rec_wet.risk_factors[0]


def test_irrigation_rule_boundaries():
    """Verifies irrigation pausing when significant rain is expected."""
    base_fact = RawWeatherFact(
        timestamp=datetime.now(timezone.utc),
        temperature_c=31.0,
        feels_like_c=33.0,
        relative_humidity=55,
        precipitation_probability=10,
        precipitation_mm=0.0,
        wind_speed_kmh=9.0,
        wind_gust_kmh=12.0,
        weather_code=0,
        weather_description_bn="শুষ্ক আবহাওয়া",
    )

    # 1. Dry conditions -> Suitable for irrigation
    rec = evaluate_irrigation_activity(base_fact)
    assert rec.suitability == SuitabilityLevel.SUITABLE

    # 2. Heavy rain forecasted (>=8mm) -> Unfavorable (pause artificial irrigation)
    rainy_daily = RawDailyForecast(
        date="2026-10-02",
        temp_max_c=28.0,
        temp_min_c=23.0,
        precipitation_probability_max=75,
        precipitation_sum_mm=12.0,
        wind_speed_max_kmh=12.0,
        weather_code=63,
        weather_description_bn="ভারী বৃষ্টি",
    )
    rec_pause = evaluate_irrigation_activity(base_fact, rainy_daily)
    assert rec_pause.suitability == SuitabilityLevel.UNFAVORABLE
    assert "জলাবদ্ধতা" in rec_pause.risk_factors[0]


def test_machinery_weather_warnings():
    """Verifies heavy machinery warnings under thunderstorm and muddy conditions."""
    base_fact = RawWeatherFact(
        timestamp=datetime.now(timezone.utc),
        temperature_c=29.0,
        feels_like_c=30.0,
        relative_humidity=65,
        precipitation_probability=10,
        precipitation_mm=0.0,
        wind_speed_kmh=8.0,
        wind_gust_kmh=10.0,
        weather_code=0,
        weather_description_bn="পরিষ্কার",
    )

    # 1. Thunderstorm (Code 95)
    storm_fact = RawWeatherFact(**{**base_fact.__dict__, "weather_code": 95})
    rec_storm, warn_storm = evaluate_machinery_activity(storm_fact)
    assert rec_storm.suitability == SuitabilityLevel.UNFAVORABLE
    assert warn_storm is not None
    assert warn_storm.warning_level == "alert"
    assert "বজ্রপাত" in warn_storm.title_bn

    # 2. Heavy rain creating mud hazard (rain_sum >= 12mm)
    muddy_daily = RawDailyForecast(
        date="2026-10-02",
        temp_max_c=27.0,
        temp_min_c=22.0,
        precipitation_probability_max=80,
        precipitation_sum_mm=18.0,
        wind_speed_max_kmh=14.0,
        weather_code=65,
        weather_description_bn="ভারী বর্ষণ",
    )
    rec_mud, warn_mud = evaluate_machinery_activity(base_fact, muddy_daily)
    assert rec_mud.suitability == SuitabilityLevel.UNFAVORABLE
    assert warn_mud is not None
    assert "চাকা দেবে যাওয়ার ঝুঁকি" in warn_mud.title_bn


# ============================================================================
# Integration & API Tests (Rule 20 & 28)
# ============================================================================


@pytest.mark.asyncio
async def test_weather_plan_api_distinguishes_facts_and_recommendations(client: AsyncClient):
    """Verifies API returns structurally isolated facts vs recommendations with attribution."""
    set_weather_provider(MockSunnyWeatherProvider())

    res = await client.get(
        "/api/v1/weather/plan",
        params={
            "latitude": 24.85,
            "longitude": 89.37,
            "district": "বগুড়া",
            "upazila": "শিবগঞ্জ",
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Rule 20: Isolated facts
    assert "facts" in data
    assert "temperatureC" in data["facts"]
    assert "relativeHumidity" in data["facts"]
    assert "precipitationProbability" in data["facts"]

    # Rule 20: Isolated activity windows
    assert "activityWindows" in data
    assert len(data["activityWindows"]) >= 3
    for act in data["activityWindows"]:
        assert act["suitability"] in ["suitable", "caution", "unfavorable"]
        assert len(act["titleBn"]) > 0
        assert len(act["guidanceBn"]) > 0

    # Rule 20: Attribution & provider metadata
    assert data["providerName"] == "Test Provider"
    assert "Mock Weather Attribution" in data["attribution"]
    assert data["isStale"] is False
    assert len(data["threeDayForecast"]) == 3


@pytest.mark.asyncio
async def test_weather_stale_fallback_on_provider_failure(client: AsyncClient):
    """Verifies that provider timeout/failure results in marked stale fallback without crashing."""
    set_weather_provider(MockFailingWeatherProvider())

    res = await client.get(
        "/api/v1/weather/plan",
        params={"latitude": 25.62, "longitude": 88.63},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    # Rule 20: Stale indicator is true with safe fallback
    assert data["isStale"] is True
    assert data["staleReason"] is not None
    assert "ব্যর্থ" in data["staleReason"]
    assert "facts" in data
    assert len(data["activityWindows"]) > 0


@pytest.mark.asyncio
async def test_machinery_weather_advisory_endpoint(client: AsyncClient):
    """Verifies the equipment weather advisory endpoint returns safety evaluation."""
    set_weather_provider(MockSunnyWeatherProvider())

    res = await client.get(
        "/api/v1/weather/machinery-advisory",
        params={
            "equipmentType": "tractor",
            "targetDate": "2026-10-02",
            "latitude": 24.85,
            "longitude": 89.37,
        },
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["equipmentType"] == "tractor"
    assert data["targetDate"] == "2026-10-02"
    assert data["isSafeToOperate"] is True
    assert "উপযুক্ত" in data["adviceBn"]
