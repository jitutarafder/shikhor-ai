"""API endpoints for Crop Marketplace."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.modules.crop_marketplace.models import CropCategory
from app.modules.crop_marketplace.schemas import (
    CropListingCreateRequest,
    CropListingResponse,
    CropListingUpdateRequest,
    SavedBuyerSearchCreateRequest,
    SavedBuyerSearchResponse,
)
from app.modules.crop_marketplace.service import (
    create_crop_listing,
    create_saved_buyer_search,
    delete_saved_buyer_search,
    get_crop_listing,
    list_my_crop_listings,
    list_saved_buyer_searches,
    search_crop_listings,
    update_crop_listing,
)
from app.modules.users.models import User

router = APIRouter(prefix="/crop-listings", tags=["crop-marketplace"])


@router.post("", response_model=CropListingResponse, status_code=status.HTTP_201_CREATED)
async def create_new_crop_listing(
    req: CropListingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CropListingResponse:
    """Creates a new crop listing for farmers."""
    return await create_crop_listing(db=db, farmer=current_user, req=req)


@router.get("", response_model=List[CropListingResponse])
async def search_crops(
    category: Optional[CropCategory] = Query(None),
    district: Optional[str] = Query(None),
    max_price: Optional[int] = Query(None, alias="maxPrice", ge=1),
    min_quantity: Optional[float] = Query(None, alias="minQuantity", ge=0.1),
    db: AsyncSession = Depends(get_db_session),
) -> List[CropListingResponse]:
    """Public search for crop listings, hiding private contact details for user safety."""
    return await search_crop_listings(
        db=db,
        category=category,
        district=district,
        max_price=max_price,
        min_quantity=min_quantity,
    )


@router.get("/my", response_model=List[CropListingResponse])
async def get_my_crop_listings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[CropListingResponse]:
    """Retrieves all crop listings posted by current farmer."""
    return await list_my_crop_listings(db=db, user=current_user)


@router.post("/saved-searches", response_model=SavedBuyerSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_buyer_saved_search(
    req: SavedBuyerSearchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SavedBuyerSearchResponse:
    """Saves search filters for buyers to receive alerts on new matching crops."""
    return await create_saved_buyer_search(db=db, buyer=current_user, req=req)


@router.get("/saved-searches", response_model=List[SavedBuyerSearchResponse])
async def get_my_saved_searches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[SavedBuyerSearchResponse]:
    """Retrieves all active saved searches for the current buyer."""
    return await list_saved_buyer_searches(db=db, buyer=current_user)


@router.delete("/saved-searches/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_buyer_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Removes a saved search."""
    await delete_saved_buyer_search(db=db, buyer=current_user, search_id=search_id)


@router.get("/{listing_id}", response_model=CropListingResponse)
async def get_crop_listing_details(
    listing_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> CropListingResponse:
    """Retrieves single crop listing details."""
    return await get_crop_listing(db=db, listing_id=listing_id)


@router.patch("/{listing_id}", response_model=CropListingResponse)
async def update_crop_listing_details(
    listing_id: str,
    req: CropListingUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CropListingResponse:
    """Updates crop listing, verifying owner-only authorization (Rule 12)."""
    return await update_crop_listing(db=db, user=current_user, listing_id=listing_id, req=req)

