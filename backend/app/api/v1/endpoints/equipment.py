"""API endpoints for agricultural machinery discovery and owner listings."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.modules.equipment.models import EquipmentType, PriceUnit
from app.modules.equipment.schemas import (
    EquipmentAvailabilityResponse,
    EquipmentCreateRequest,
    EquipmentResponse,
    EquipmentReviewCreate,
    EquipmentReviewResponse,
    EquipmentUpdateRequest,
)
from app.modules.equipment.service import (
    create_equipment,
    create_equipment_review,
    get_equipment,
    get_equipment_availability,
    list_equipment_reviews,
    list_owner_equipment,
    search_and_rank_equipment,
    update_equipment,
)
from app.modules.users.models import User

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.post("", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_new_equipment(
    req: EquipmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> EquipmentResponse:
    """Creates a new machinery listing for an equipment owner."""
    return await create_equipment(db, current_user, req)


@router.get("", response_model=List[EquipmentResponse])
async def search_equipment(
    equipment_type: EquipmentType = Query(..., alias="equipmentType"),
    price_unit: PriceUnit = Query(..., alias="priceUnit"),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    max_radius_km: Optional[float] = Query(None, alias="maxRadiusKm", ge=1.0, le=100.0),
    db: AsyncSession = Depends(get_db_session),
) -> List[EquipmentResponse]:
    """Discovers nearby equipment ranked by the approved transparent 65/35 formula."""
    return await search_and_rank_equipment(
        db=db,
        equipment_type=equipment_type,
        price_unit=price_unit,
        user_lat=latitude,
        user_lon=longitude,
        max_radius_km=max_radius_km,
    )


@router.get("/my", response_model=List[EquipmentResponse])
async def get_my_equipment(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[EquipmentResponse]:
    """Retrieves all equipment listings managed by the current user."""
    return await list_owner_equipment(db, current_user)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment_details(
    equipment_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> EquipmentResponse:
    """Retrieves single machinery details."""
    return await get_equipment(db, equipment_id)


@router.patch("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment_details(
    equipment_id: str,
    req: EquipmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> EquipmentResponse:
    """Updates equipment details, verifying listing ownership."""
    return await update_equipment(db, current_user, equipment_id, req)


@router.get("/{equipment_id}/availability", response_model=EquipmentAvailabilityResponse)
async def get_machinery_availability(
    equipment_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> EquipmentAvailabilityResponse:
    """Returns booked and reserved dates for the machinery availability calendar."""
    return await get_equipment_availability(db=db, equipment_id=equipment_id)


@router.post(
    "/{equipment_id}/reviews",
    response_model=EquipmentReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_equipment_review(
    equipment_id: str,
    req: EquipmentReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> EquipmentReviewResponse:
    """Submits a post-completion review strictly validated against completed rentals (Rule 11)."""
    return await create_equipment_review(
        db=db, renter=current_user, equipment_id=equipment_id, req=req
    )


@router.get("/{equipment_id}/reviews", response_model=List[EquipmentReviewResponse])
async def get_machinery_reviews(
    equipment_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> List[EquipmentReviewResponse]:
    """Retrieves all farmer reviews for this agricultural machinery."""
    return await list_equipment_reviews(db=db, equipment_id=equipment_id)
