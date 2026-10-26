from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_optional_current_user
from app.db.session import get_db_session
from app.modules.users.models import User
from app.modules.weather.schemas import (
    EmergencyWeatherAlertsRequest,
    EmergencyWeatherAlertsResponse,
    EquipmentWeatherAdvisoryResponse,
    WeatherPlanResponse,
)
from app.modules.weather.service import (
    check_and_dispatch_emergency_weather_alerts,
    get_equipment_advisory,
    get_weather_plan,
)

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/plan", response_model=WeatherPlanResponse)
async def get_farming_weather_plan(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    district: Optional[str] = Query(None),
    upazila: Optional[str] = Query(None),
) -> WeatherPlanResponse:
    """Retrieves 3-day weather forecast and rule-based agricultural activity guidance.

    Strictly complies with AGENTS.md Rule 20:
    - Provider facts are structurally separated from product activity recommendations.
    - Captures provider timestamp, attribution, and stale/fallback indicators.
    """
    return await get_weather_plan(
        lat=latitude,
        lon=longitude,
        district=district,
        upazila=upazila,
    )


@router.get("/machinery-advisory", response_model=EquipmentWeatherAdvisoryResponse)
async def check_machinery_weather_advisory(
    equipment_type: str = Query(..., alias="equipmentType"),
    target_date: str = Query(..., alias="targetDate"),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
) -> EquipmentWeatherAdvisoryResponse:
    """Evaluates whether weather on the target rental date is safe for machinery operations."""
    return await get_equipment_advisory(
        equipment_type=equipment_type,
        target_date=target_date,
        lat=latitude,
        lon=longitude,
    )


@router.post("/check-alerts", response_model=EmergencyWeatherAlertsResponse)
async def check_emergency_weather_alerts(
    req: EmergencyWeatherAlertsRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> EmergencyWeatherAlertsResponse:
    """Checks real-time emergency spray, irrigation, and storm alerts based on GPS/district location.

    Dispatches in-app notification to logged-in user if critical weather hazard is detected.
    """
    return await check_and_dispatch_emergency_weather_alerts(
        db=db,
        lat=req.latitude,
        lon=req.longitude,
        district=req.district,
        upazila=req.upazila,
        user=current_user,
        send_notification=req.sendNotification,
    )


@router.get("/alerts", response_model=EmergencyWeatherAlertsResponse)
async def get_emergency_weather_alerts(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    district: Optional[str] = Query(None),
    upazila: Optional[str] = Query(None),
    send_notification: bool = Query(True, alias="sendNotification"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> EmergencyWeatherAlertsResponse:
    """GET endpoint to fetch emergency spray, irrigation, and storm alerts for GPS coordinates."""
    return await check_and_dispatch_emergency_weather_alerts(
        db=db,
        lat=latitude,
        lon=longitude,
        district=district,
        upazila=upazila,
        user=current_user,
        send_notification=send_notification,
    )

