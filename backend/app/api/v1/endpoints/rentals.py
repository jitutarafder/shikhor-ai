"""API endpoints for rental requests and central state machine transitions."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.modules.rentals.schemas import (
    RentalRequestCreate,
    RentalRequestResponse,
    RentalStatusUpdateRequest,
)
from app.modules.rentals.service import (
    create_rental,
    get_rental_by_id,
    list_user_rentals,
    update_rental_request_status,
)
from app.modules.users.models import User

router = APIRouter(prefix="/rentals", tags=["rentals"])


@router.post("", response_model=RentalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_rental_request(
    req: RentalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalRequestResponse:
    """Creates a rental request for agricultural machinery with idempotency protection."""
    rental = await create_rental(db=db, renter=current_user, req=req)
    return RentalRequestResponse.model_validate(rental)


@router.get("", response_model=List[RentalRequestResponse])
async def get_my_rentals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[RentalRequestResponse]:
    """Retrieves all rental requests where current user is renter or equipment owner."""
    rentals = await list_user_rentals(db=db, user=current_user)
    return [RentalRequestResponse.model_validate(r) for r in rentals]


@router.get("/{rental_id}", response_model=RentalRequestResponse)
async def get_rental_details(
    rental_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalRequestResponse:
    """Retrieves a single rental request with object-level authorization."""
    rental = await get_rental_by_id(db=db, user=current_user, rental_id=rental_id)
    return RentalRequestResponse.model_validate(rental)


@router.patch("/{rental_id}/status", response_model=RentalRequestResponse)
async def update_rental_status(
    rental_id: str,
    req: RentalStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> RentalRequestResponse:
    """Transitions rental request status through the centralized state machine."""
    rental = await update_rental_request_status(
        db=db,
        actor=current_user,
        rental_id=rental_id,
        target_status=req.targetStatus,
    )
    return RentalRequestResponse.model_validate(rental)
