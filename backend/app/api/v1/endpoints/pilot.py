"""API v1 endpoints for Phase 9 Controlled Pilot operations and telemetry."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_role
from app.db.session import get_db_session
from app.modules.pilot.schemas import (
    PilotDistrictCropConfig,
    PilotFeedbackCreate,
    PilotFeedbackResponse,
    PilotTelemetryMetrics,
)
from app.modules.pilot.service import (
    calculate_pilot_telemetry,
    get_pilot_configuration,
    get_pilot_feedback_feed,
    record_pilot_feedback,
)
from app.modules.users.models import User, UserRole

router = APIRouter(prefix="/pilot", tags=["pilot"])


@router.get("/config", response_model=PilotDistrictCropConfig)
async def get_controlled_pilot_config() -> PilotDistrictCropConfig:
    """Returns official controlled pilot configuration, focus districts, crops, and checklist."""
    return get_pilot_configuration()


@router.post(
    "/feedback",
    response_model=PilotFeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit pilot task experience and comprehension feedback",
)
async def submit_pilot_feedback(
    payload: PilotFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> PilotFeedbackResponse:
    """Records farmer or participant usability, Bangla comprehension, and device telemetry."""
    user_district = None
    user_upazila = None
    if current_user.farmer_profile:
        user_district = current_user.farmer_profile.district
        user_upazila = current_user.farmer_profile.upazila
    elif current_user.owner_profile:
        user_district = current_user.owner_profile.district
        user_upazila = current_user.owner_profile.upazila

    feedback = await record_pilot_feedback(
        db=db,
        user_id=current_user.id,
        data=payload,
        default_district=user_district,
        default_upazila=user_upazila,
    )
    return PilotFeedbackResponse.model_validate(feedback)


@router.get(
    "/metrics",
    response_model=PilotTelemetryMetrics,
    summary="Get authoritative Phase 9 pilot telemetry metrics (Admin/Moderator only)",
)
async def get_pilot_telemetry(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> PilotTelemetryMetrics:
    """Calculates all 7 Phase 9 pilot metrics and Go/No-Go readiness checklist directly from the DB."""
    return await calculate_pilot_telemetry(db=db)


@router.get(
    "/feedback-list",
    response_model=List[PilotFeedbackResponse],
    summary="Get qualitative pilot feedback stream (Admin/Moderator only)",
)
async def list_pilot_feedback(
    limit: int = Query(default=50, ge=1, le=200),
    task_type: Optional[str] = Query(default=None),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> List[PilotFeedbackResponse]:
    """Retrieves qualitative feedback stream for pilot observers and the moderation team."""
    feedbacks = await get_pilot_feedback_feed(db=db, limit=limit, task_type=task_type)
    return [PilotFeedbackResponse.model_validate(fb) for fb in feedbacks]
