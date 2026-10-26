"""Job Registry for typed background job handlers."""

import logging
from typing import Any, Callable, Coroutine, Dict
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("shikhor.jobs")

# Type alias for async job handler: func(db: AsyncSession, payload: dict) -> dict
JobHandler = Callable[[AsyncSession, Dict[str, Any]], Coroutine[Any, Any, Dict[str, Any]]]

JOB_HANDLERS: Dict[str, JobHandler] = {}


def register_handler(job_type: str):
    """Decorator registering an asynchronous handler for a specific job_type."""
    def decorator(func: JobHandler) -> JobHandler:
        JOB_HANDLERS[job_type] = func
        return func
    return decorator


# -------------------------------------------------------------
# Concrete Built-in Job Handlers
# -------------------------------------------------------------

@register_handler("notification_dispatch")
async def handle_notification_dispatch(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Background handler dispatching notification to user."""
    from app.modules.notifications.service import create_notification

    user_id = payload.get("user_id")
    title = payload.get("title", "কৃষি আপডেট")
    message = payload.get("message", "")
    notification_type = payload.get("notification_type", "crop_match")
    link = payload.get("link")

    if not user_id:
        raise ValueError("Missing user_id in notification_dispatch payload")

    notif = await create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )
    return {"notification_id": notif.id, "status": "dispatched"}


@register_handler("weather_cache_warmup")
async def handle_weather_cache_warmup(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Background handler pre-warming weather forecast cache for focus districts."""
    from app.modules.weather.service import get_district_weather

    district = payload.get("district", "বগুড়া")
    weather_data = await get_district_weather(db=db, district=district)
    return {"district": district, "cached_at": weather_data.forecast_timestamp.isoformat() if hasattr(weather_data, "forecast_timestamp") else "ok"}


@register_handler("telemetry_aggregation")
async def handle_telemetry_aggregation(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Background handler aggregating pilot operational metrics."""
    from app.modules.pilot.service import calculate_pilot_telemetry

    metrics = await calculate_pilot_telemetry(db=db)
    return {
        "farmers_count": metrics.total_registered_farmers,
        "cases_count": metrics.total_crop_cases_submitted,
        "readiness": metrics.go_no_go_readiness,
    }


@register_handler("test_echo_job")
async def handle_test_echo_job(db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Simple echo job for worker testing and verification."""
    message = payload.get("message", "hello")
    if payload.get("simulate_error"):
        raise RuntimeError("Simulated job failure for retry test")
    return {"echo": message, "success": True}
