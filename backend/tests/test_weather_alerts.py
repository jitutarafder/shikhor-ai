"""Tests for Weather Emergency Alerts (Spraying, Irrigation, Storms) and Notification Dispatch.

Strictly complies with:
- AGENTS.md Rule 20: Weather guidance separates facts from recommendations
- AGENTS.md Rule 26: In-app notification creation without credential leaks
- AGENTS.md Rule 28: Mandatory rule boundary tests
"""

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.integrations.weather.provider import (
    RawDailyForecast,
    RawWeatherFact,
    RawWeatherResponse,
    WeatherProvider,
)
from app.modules.weather.service import set_weather_provider


class MockAlertWeatherProvider(WeatherProvider):
    def __init__(self, wind_speed: float = 18.0, rain_sum: float = 12.0, rain_prob: int = 75, weather_code: int = 95):
        self.wind_speed = wind_speed
        self.rain_sum = rain_sum
        self.rain_prob = rain_prob
        self.weather_code = weather_code

    async def fetch_weather(self, lat: float, lon: float) -> RawWeatherResponse:
        now = datetime.now(timezone.utc)
        current = RawWeatherFact(
            timestamp=now,
            temperature_c=26.0,
            feels_like_c=27.0,
            relative_humidity=65,
            precipitation_probability=self.rain_prob,
            precipitation_mm=self.rain_sum,
            wind_speed_kmh=self.wind_speed,
            wind_gust_kmh=self.wind_speed * 1.2,
            weather_code=self.weather_code,
            weather_description_bn="আবহাওয়া পরিস্থিতি",
        )
        daily = [
            RawDailyForecast(
                date="2026-10-02",
                temp_max_c=30.0,
                temp_min_c=24.0,
                precipitation_probability_max=self.rain_prob,
                precipitation_sum_mm=self.rain_sum,
                wind_speed_max_kmh=self.wind_speed,
                weather_code=self.weather_code,
                weather_description_bn="বজ্রবিদ্যুৎসহ ঝড়ো বৃষ্টি",
            ),
            RawDailyForecast(
                date="2026-10-03",
                temp_max_c=31.0,
                temp_min_c=25.0,
                precipitation_probability_max=self.rain_prob,
                precipitation_sum_mm=self.rain_sum,
                wind_speed_max_kmh=self.wind_speed,
                weather_code=self.weather_code,
                weather_description_bn="ভারী বৃষ্টি",
            ),
        ]
        return RawWeatherResponse(
            provider_name="MockOpenMeteo",
            attribution="Mock Weather Data",
            provider_timestamp=now,
            latitude=lat,
            longitude=lon,
            current=current,
            daily=daily,
            is_stale=False,
            stale_reason=None,
        )


@pytest.mark.asyncio
async def test_emergency_weather_alerts_evaluation_and_notification(client: AsyncClient):
    """Severe weather (high wind, heavy rain, storm code 95) generates danger alerts and in-app notification."""
    from app.integrations.weather.provider import OpenMeteoWeatherAdapter

    # Register a farmer
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "01766998877",
            "password": "Password123#Strong",
            "full_name": "আনিসুর রহমান",
            "role": "farmer",
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["accessToken"]

    # Inject Mock Severe Weather Provider
    mock_prov = MockAlertWeatherProvider(wind_speed=22.0, rain_sum=15.0, rain_prob=85, weather_code=95)
    set_weather_provider(mock_prov)

    try:
        # Call POST /api/v1/weather/check-alerts
        alert_res = await client.post(
            "/api/v1/weather/check-alerts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "latitude": 24.85,
                "longitude": 89.37,
                "district": "বগুড়া",
                "upazila": "শেরপুর",
                "send_notification": True,
            },
        )
        assert alert_res.status_code == 200, alert_res.text
        data = alert_res.json()

        assert data["hasUrgentAlert"] is True
        assert data["notificationDispatched"] is True
        assert len(data["alerts"]) >= 3

        # Check spraying alert (danger due to high wind & rain)
        spray_alert = next((a for a in data["alerts"] if a["alertType"] == "spraying"), None)
        assert spray_alert is not None
        assert spray_alert["severity"] == "danger"
        assert "তীব্র বাতাস" in spray_alert["titleBn"] or "বৃষ্টি" in spray_alert["titleBn"]

        # Check irrigation alert (danger: pause artificial irrigation)
        irrig_alert = next((a for a in data["alerts"] if a["alertType"] == "irrigation"), None)
        assert irrig_alert is not None
        assert irrig_alert["severity"] == "danger"
        assert "সেচ প্রদান স্থগিত" in irrig_alert["titleBn"]

        # Check storm alert (danger)
        storm_alert = next((a for a in data["alerts"] if a["alertType"] == "storm"), None)
        assert storm_alert is not None
        assert storm_alert["severity"] == "danger"

        # Verify notification was inserted into the farmer's inbox
        notif_res = await client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert notif_res.status_code == 200
        notifications = notif_res.json()
        assert len(notifications) >= 1
        weather_notif = next((n for n in notifications if n["notificationType"] == "weather_alert"), None)
        assert weather_notif is not None
        assert "স্প্রে" in weather_notif["title"] or "সতর্কতা" in weather_notif["title"] or "বাতাস" in weather_notif["title"]

        # Repeat call within 6 hours -> does not spam duplicate notifications
        second_res = await client.post(
            "/api/v1/weather/check-alerts",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "latitude": 24.85,
                "longitude": 89.37,
                "send_notification": True,
            },
        )
        assert second_res.status_code == 200
        assert second_res.json()["notificationDispatched"] is False
    finally:
        set_weather_provider(OpenMeteoWeatherAdapter())


@pytest.mark.asyncio
async def test_favorable_weather_alerts(client: AsyncClient):
    """Calm weather produces success status with no danger alerts."""
    from app.integrations.weather.provider import OpenMeteoWeatherAdapter

    mock_prov = MockAlertWeatherProvider(wind_speed=6.0, rain_sum=0.0, rain_prob=5, weather_code=0)
    set_weather_provider(mock_prov)

    try:
        alert_res = await client.get(
            "/api/v1/weather/alerts?latitude=24.85&longitude=89.37&sendNotification=false"
        )
        assert alert_res.status_code == 200
        data = alert_res.json()
        assert data["hasUrgentAlert"] is False

        spray_alert = next((a for a in data["alerts"] if a["alertType"] == "spraying"), None)
        assert spray_alert is not None
        assert spray_alert["severity"] == "success"
        assert "অনুকূল" in spray_alert["titleBn"]
    finally:
        set_weather_provider(OpenMeteoWeatherAdapter())

