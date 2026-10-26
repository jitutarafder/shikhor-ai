from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.weather.provider import (
    OpenMeteoWeatherAdapter,
    RawDailyForecast,
    RawWeatherFact,
    WeatherProvider,
)
from app.modules.notifications.models import Notification
from app.modules.notifications.service import create_notification
from app.modules.users.models import User
from app.modules.weather.rules import (
    ActivityRecommendation,
    MachineryWeatherWarning,
    evaluate_machinery_activity,
    generate_all_activity_plans,
)
from app.modules.weather.schemas import (
    ActivityRecommendationSchema,
    DailyForecastSchema,
    EmergencyWeatherAlertsResponse,
    EquipmentWeatherAdvisoryResponse,
    MachineryWeatherWarningSchema,
    WeatherAlertItemSchema,
    WeatherFactSchema,
    WeatherLocationSchema,
    WeatherPlanResponse,
)

# Singleton provider instance
_weather_provider: WeatherProvider = OpenMeteoWeatherAdapter()


def get_weather_provider() -> WeatherProvider:
    return _weather_provider


def set_weather_provider(provider: WeatherProvider) -> None:
    """Allows test fixtures to inject custom or mock providers."""
    global _weather_provider
    _weather_provider = provider


async def get_weather_plan(
    lat: float,
    lon: float,
    district: Optional[str] = None,
    upazila: Optional[str] = None,
    provider: Optional[WeatherProvider] = None,
) -> WeatherPlanResponse:
    """Retrieves weather facts and generates rule-based agronomic recommendations."""
    active_provider = provider or _weather_provider

    # 1. Fetch raw weather facts from provider adapter
    raw_res = await active_provider.fetch_weather(lat, lon)

    # 2. Evaluate current activity windows & machinery warnings
    current_recs, current_warnings = generate_all_activity_plans(raw_res.current)

    # 3. Process 3-day daily forecasts and their respective activity windows
    forecast_schemas: List[DailyForecastSchema] = []
    all_machinery_warnings: List[MachineryWeatherWarning] = list(current_warnings)

    for daily in raw_res.daily[1:4]:  # Next 3 days
        # Synthesize a temporary fact representing the daily peak
        daily_fact = RawWeatherFact(
            timestamp=datetime.now(timezone.utc),
            temperature_c=daily.temp_max_c,
            feels_like_c=daily.temp_max_c + 2.0,
            relative_humidity=70,
            precipitation_probability=daily.precipitation_probability_max,
            precipitation_mm=daily.precipitation_sum_mm,
            wind_speed_kmh=daily.wind_speed_max_kmh,
            wind_gust_kmh=daily.wind_speed_max_kmh * 1.3,
            weather_code=daily.weather_code,
            weather_description_bn=daily.weather_description_bn,
        )

        daily_recs, daily_warns = generate_all_activity_plans(daily_fact, daily)

        for w in daily_warns:
            # Avoid duplicate warnings
            if not any(existing.title_bn == w.title_bn for existing in all_machinery_warnings):
                all_machinery_warnings.append(w)

        forecast_schemas.append(
            DailyForecastSchema(
                date=daily.date,
                temp_max_c=daily.temp_max_c,
                temp_min_c=daily.temp_min_c,
                precipitation_probability_max=daily.precipitation_probability_max,
                precipitation_sum_mm=daily.precipitation_sum_mm,
                wind_speed_max_kmh=daily.wind_speed_max_kmh,
                weather_code=daily.weather_code,
                weather_description_bn=daily.weather_description_bn,
                activity_recommendations=[
                    ActivityRecommendationSchema(
                        activity_type=r.activity_type,
                        title_bn=r.title_bn,
                        suitability=r.suitability,
                        reason_summary_bn=r.reason_summary_bn,
                        guidance_bn=r.guidance_bn,
                        risk_factors=r.risk_factors,
                    )
                    for r in daily_recs
                ],
            )
        )

    # 4. Assemble response cleanly separating facts from recommendations (Rule 20)
    return WeatherPlanResponse(
        location=WeatherLocationSchema(
            district=district,
            upazila=upazila,
            approximate_lat=round(lat, 2),
            approximate_lon=round(lon, 2),
        ),
        facts=WeatherFactSchema(
            timestamp=raw_res.current.timestamp,
            temperature_c=raw_res.current.temperature_c,
            feels_like_c=raw_res.current.feels_like_c,
            relative_humidity=raw_res.current.relative_humidity,
            precipitation_probability=raw_res.current.precipitation_probability,
            precipitation_mm=raw_res.current.precipitation_mm,
            wind_speed_kmh=raw_res.current.wind_speed_kmh,
            wind_gust_kmh=raw_res.current.wind_gust_kmh,
            weather_code=raw_res.current.weather_code,
            weather_description_bn=raw_res.current.weather_description_bn,
        ),
        activity_windows=[
            ActivityRecommendationSchema(
                activity_type=r.activity_type,
                title_bn=r.title_bn,
                suitability=r.suitability,
                reason_summary_bn=r.reason_summary_bn,
                guidance_bn=r.guidance_bn,
                risk_factors=r.risk_factors,
            )
            for r in current_recs
        ],
        three_day_forecast=forecast_schemas,
        equipment_warnings=[
            MachineryWeatherWarningSchema(
                warning_level=w.warning_level,
                title_bn=w.title_bn,
                message_bn=w.message_bn,
                affected_equipment=w.affected_equipment,
            )
            for w in all_machinery_warnings
        ],
        provider_name=raw_res.provider_name,
        attribution=raw_res.attribution,
        provider_timestamp=raw_res.provider_timestamp,
        is_stale=raw_res.is_stale,
        stale_reason=raw_res.stale_reason,
    )


async def get_equipment_advisory(
    equipment_type: str,
    target_date: str,
    lat: float,
    lon: float,
    provider: Optional[WeatherProvider] = None,
) -> EquipmentWeatherAdvisoryResponse:
    """Specifically evaluates whether weather on target date is safe for machinery operations."""
    active_provider = provider or _weather_provider
    raw_res = await active_provider.fetch_weather(lat, lon)

    # Find forecast matching target_date
    matching_daily: Optional[RawDailyForecast] = None
    for d in raw_res.daily:
        if d.date == target_date:
            matching_daily = d
            break

    if not matching_daily:
        matching_daily = raw_res.daily[0] if raw_res.daily else None

    # Evaluate machinery conditions
    if matching_daily:
        dummy_fact = RawWeatherFact(
            timestamp=datetime.now(timezone.utc),
            temperature_c=matching_daily.temp_max_c,
            feels_like_c=matching_daily.temp_max_c,
            relative_humidity=70,
            precipitation_probability=matching_daily.precipitation_probability_max,
            precipitation_mm=matching_daily.precipitation_sum_mm,
            wind_speed_kmh=matching_daily.wind_speed_max_kmh,
            wind_gust_kmh=matching_daily.wind_speed_max_kmh * 1.3,
            weather_code=matching_daily.weather_code,
            weather_description_bn=matching_daily.weather_description_bn,
        )
        _, warning = evaluate_machinery_activity(dummy_fact, matching_daily)
    else:
        _, warning = evaluate_machinery_activity(raw_res.current)

    is_safe = warning is None

    if is_safe:
        advice = f"নির্বাচিত তারিখে আবহাওয়া শান্ত রয়েছে। {equipment_type} পরিচালনা ও ভাড়া নেওয়ার জন্য উপযুক্ত।"
    else:
        advice = f"সতর্কতা: {warning.message_bn}। ভাড়ার তারিখ পরিবর্তনের কথা বিবেচনা করতে পারেন।"

    return EquipmentWeatherAdvisoryResponse(
        equipment_type=equipment_type,
        target_date=target_date,
        is_safe_to_operate=is_safe,
        warning=(
            MachineryWeatherWarningSchema(
                warning_level=warning.warning_level,
                title_bn=warning.title_bn,
                message_bn=warning.message_bn,
                affected_equipment=warning.affected_equipment,
            )
            if warning
            else None
        ),
        advice_bn=advice,
    )


async def check_and_dispatch_emergency_weather_alerts(
    db: AsyncSession,
    lat: float,
    lon: float,
    district: Optional[str] = None,
    upazila: Optional[str] = None,
    user: Optional[User] = None,
    send_notification: bool = True,
    provider: Optional[WeatherProvider] = None,
) -> EmergencyWeatherAlertsResponse:
    """Evaluates critical weather alerts (Spraying, Irrigation, Storms) and dispatches in-app alerts."""
    active_provider = provider or _weather_provider
    raw_res = await active_provider.fetch_weather(lat, lon)
    current = raw_res.current
    today_daily = raw_res.daily[0] if raw_res.daily else None
    next_daily = raw_res.daily[1] if len(raw_res.daily) > 1 else None

    alerts: List[WeatherAlertItemSchema] = []
    has_urgent = False

    # -------------------------------------------------------------
    # 1. EMERGENCY SPRAY ALERT EVALUATION
    # -------------------------------------------------------------
    spray_rain_prob = today_daily.precipitation_probability_max if today_daily else current.precipitation_probability
    spray_rain_sum = today_daily.precipitation_sum_mm if today_daily else current.precipitation_mm

    if current.wind_speed_kmh > 15.0 or (today_daily and today_daily.wind_speed_max_kmh > 20.0):
        has_urgent = True
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="spraying",
                severity="danger",
                title_bn="⚠️ তীব্র বাতাস: বালাইনাশক স্প্রে স্থগিত রাখুন",
                message_bn=f"বর্তমান বাতাসের বেগ {current.wind_speed_kmh:.1f} কিমি/ঘণ্টা। বালাইনাশক বা ভিটামিন স্প্রে করলে বাতাসে ওষুধ ভেসে গিয়ে কার্যকারিতা নষ্ট হবে ও পার্শ্ববর্তী জমিতে বিষাক্ততার ঝুঁকি তৈরি করবে।",
                action_guidance_bn="বাতাসের বেগ ১০ কিমি/ঘণ্টার নিচে শান্ত হওয়া পর্যন্ত স্প্রে কার্যক্রম স্থগিত রাখুন।",
                urgency_level="high",
                icon_type="wind",
                timestamp=datetime.now(timezone.utc),
            )
        )
    elif spray_rain_prob >= 40 or spray_rain_sum >= 2.0 or current.precipitation_mm > 0.5:
        has_urgent = True
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="spraying",
                severity="danger",
                title_bn="🌧️ বৃষ্টির আশঙ্কা: বালাইনাশক ও ছত্রাকনাশক স্প্রে বন্ধ রাখুন",
                message_bn="বৃষ্টিপাতের উচ্চ সম্ভাবনা রয়েছে (বৃষ্টির সম্ভাবনা ৪০% বা তার বেশি)। এখন স্প্রে করলে বৃষ্টির পানিতে ওষুধ ধুয়ে যাবে এবং কৃষক আর্থিক ক্ষতির সম্মুখীন হবেন।",
                action_guidance_bn="বৃষ্টিপাত থেমে আকাশ পরিষ্কার ও রোদ না ওঠা পর্যন্ত স্প্রে বন্ধ রাখুন।",
                urgency_level="high",
                icon_type="rain",
                timestamp=datetime.now(timezone.utc),
            )
        )
    elif current.temperature_c >= 34.0:
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="spraying",
                severity="warning",
                title_bn="☀️ উচ্চ তাপমাত্রা: দুপুরের কড়া রোদে স্প্রে করবেন না",
                message_bn=f"তাপমাত্রা {current.temperature_c:.1f}°C ছাড়িয়েছে। কড়া রোদে স্প্রে করলে রাসায়নিক দ্রুত বাষ্পীভূত হয় এবং পাতা ঝলসে যাওয়ার ঝুঁকি থাকে।",
                action_guidance_bn="সকাল ৯টার পূর্বে অথবা বিকাল ৪টার পরে শীতল তাপমাত্রায় স্প্রে সম্পন্ন করুন।",
                urgency_level="medium",
                icon_type="sun",
                timestamp=datetime.now(timezone.utc),
            )
        )
    else:
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="spraying",
                severity="success",
                title_bn="✅ স্প্রে করার অনুকূল আবহাওয়া",
                message_bn="বাতাস শান্ত রয়েছে এবং বৃষ্টির কোনো ঝুঁকি নেই। স্প্রে করার জন্য আদর্শ পরিবেশ।",
                action_guidance_bn="নিরাপত্তা মাস্ক ও গ্লাভস পরিধান করে আজ স্প্রে কার্যক্রম পরিচালনা করতে পারেন।",
                urgency_level="low",
                icon_type="shield-check",
                timestamp=datetime.now(timezone.utc),
            )
        )

    # -------------------------------------------------------------
    # 2. EMERGENCY IRRIGATION ALERT EVALUATION
    # -------------------------------------------------------------
    irrig_rain_prob = next_daily.precipitation_probability_max if next_daily else spray_rain_prob
    irrig_rain_sum = next_daily.precipitation_sum_mm if next_daily else spray_rain_sum

    if irrig_rain_sum >= 8.0 or irrig_rain_prob >= 60:
        has_urgent = True
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="irrigation",
                severity="danger",
                title_bn="⛔ জমিতে সেচ প্রদান স্থগিত রাখুন (খরচ ও জলাবদ্ধতা বাঁচান)",
                message_bn="আসন্ন সময়ে পর্যাপ্ত বৃষ্টিপাতের জোরালো পূর্বাভাস রয়েছে। এখন সেচ দিলে জ্বালানি/বিদ্যুৎ খরচ অপচয় হবে এবং জমিতে অতিরিক্ত জলাবদ্ধতা তৈরি হতে পারে।",
                action_guidance_bn="কৃত্রিম সেচ সাময়িক বন্ধ রাখুন এবং জমির অতিরিক্ত পানি নিষ্কাশনের ড্রেন পরিষ্কার রাখুন।",
                urgency_level="high",
                icon_type="droplet",
                timestamp=datetime.now(timezone.utc),
            )
        )
    elif irrig_rain_sum >= 3.0 or irrig_rain_prob >= 35:
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="irrigation",
                severity="warning",
                title_bn="💧 পরিমিত হালকা সেচ দিন বা বৃষ্টির অপেক্ষা করুন",
                message_bn="মাঝারি বৃষ্টির সম্ভাবনা রয়েছে। জমিতে গভীর বা প্লাবন সেচ দেওয়া থেকে বিরত থাকুন।",
                action_guidance_bn="মাটির রস পরীক্ষা করে শুধুমাত্র শুকিয়ে যাওয়া জমিতে হালকা সেচ দিন।",
                urgency_level="medium",
                icon_type="droplet",
                timestamp=datetime.now(timezone.utc),
            )
        )
    elif current.temperature_c >= 30.0 and current.relative_humidity <= 60 and spray_rain_prob < 15:
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="irrigation",
                severity="warning",
                title_bn="🌾 জমিতে সেচ প্রদান প্রয়োজন (শুষ্ক আবহাওয়া)",
                message_bn="শুষ্ক আবহাওয়ায় মাটির রস কমে গেছে এবং বৃষ্টির সম্ভাবনা কম। ফসলের স্বাভাবিক বৃদ্ধির জন্য সেচ প্রয়োজন।",
                action_guidance_bn="ফসলের পর্যায় ও মাটির আর্দ্রতা দেখে রুটিন অনুযায়ী জমিতে সেচ প্রদান করুন।",
                urgency_level="medium",
                icon_type="sun",
                timestamp=datetime.now(timezone.utc),
            )
        )
    else:
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="irrigation",
                severity="info",
                title_bn="ℹ️ স্বাভাবিক সেচ বজায় রাখুন",
                message_bn="আবহাওয়া স্থিতিশীল রয়েছে। ফসলের বর্তমান চাহিদা অনুযায়ী নিয়মমাফিক সেচ অব্যাহত রাখুন।",
                action_guidance_bn="মাটির রস পর্যবেক্ষণ করে পরিমিত সেচ বজায় রাখুন।",
                urgency_level="low",
                icon_type="droplet",
                timestamp=datetime.now(timezone.utc),
            )
        )

    # -------------------------------------------------------------
    # 3. SEVERE STORM / THUNDERSTORM ALERT
    # -------------------------------------------------------------
    if current.weather_code in [95, 96, 99] or current.wind_speed_kmh >= 30.0:
        has_urgent = True
        alerts.append(
            WeatherAlertItemSchema(
                alert_type="storm",
                severity="danger",
                title_bn="⚡ জরুরি বজ্রপাত ও কালবৈশাখী ঝড় সতর্কতা",
                message_bn="বজ্রবিদ্যুৎসহ তীব্র ঝড়-বৃষ্টির চরম ঝুঁকি রয়েছে। খোলা মাঠে অবস্থান বা কৃষিযন্ত্র পরিচালনা জীবননাশের কারণ হতে পারে।",
                action_guidance_bn="মাঠের সব কাজ বন্ধ করে দ্রুত নিরাপদ পাকা ঘরে আশ্রয় নিন এবং বৈদ্যুতিক ও ধাতব যন্ত্রপাতি থেকে দূরে থাকুন।",
                urgency_level="high",
                icon_type="zap",
                timestamp=datetime.now(timezone.utc),
            )
        )

    # -------------------------------------------------------------
    # 4. DISPATCH IN-APP NOTIFICATION IF CRITICAL (AND NO DUPLICATE IN 6 HOURS)
    # -------------------------------------------------------------
    notification_dispatched = False
    if user and send_notification and has_urgent:
        six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=6)
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user.id,
                Notification.notification_type == "weather_alert",
                Notification.created_at >= six_hours_ago,
            )
            .limit(1)
        )
        recent = (await db.execute(stmt)).scalars().first()
        if not recent:
            # Build consolidated notification
            danger_alerts = [a for a in alerts if a.severity == "danger"]
            primary = danger_alerts[0] if danger_alerts else alerts[0]
            notif_title = f"{primary.titleBn}"
            notif_msg = f"{primary.messageBn} পরামর্শ: {primary.actionGuidanceBn}"
            
            await create_notification(
                db=db,
                user_id=user.id,
                title=notif_title,
                message=notif_msg,
                notification_type="weather_alert",
                link="/app/weather",
            )
            notification_dispatched = True

    # Summary text
    if has_urgent:
        summary_bn = "⚠️ আপনার বর্তমান এলাকায় জরুরি আবহাওয়া সতর্কতা সক্রিয় রয়েছে। স্প্রে ও সেচ কার্যক্রম সংক্রান্ত পরামর্শ মেনে চলুন।"
    else:
        summary_bn = "✅ আপনার বর্তমান এলাকায় কৃষি কার্যক্রমের আবহাওয়া স্বাভাবিক ও অনুকূল রয়েছে।"

    return EmergencyWeatherAlertsResponse(
        district=district,
        upazila=upazila,
        approximate_lat=round(lat, 2),
        approximate_lon=round(lon, 2),
        alerts=alerts,
        has_urgent_alert=has_urgent,
        notification_dispatched=notification_dispatched,
        summary_bn=summary_bn,
    )

