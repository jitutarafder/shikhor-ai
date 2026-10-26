"""Crop Marketplace domain service."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenException, NotFoundException, ShikhorException
from app.modules.crop_marketplace.models import (
    CropCategory,
    CropListing,
    CropListingStatus,
    SavedBuyerSearch,
)
from app.modules.crop_marketplace.schemas import (
    CropListingCreateRequest,
    CropListingResponse,
    CropListingUpdateRequest,
    SavedBuyerSearchCreateRequest,
    SavedBuyerSearchResponse,
)
from app.modules.notifications.service import create_notification
from app.modules.users.models import User


def _map_to_response(listing: CropListing) -> CropListingResponse:
    farmer_name = listing.farmer.full_name if listing.farmer else "কৃষক"
    farmer_role = listing.farmer.role if listing.farmer else "farmer"
    is_farmer_verified = listing.farmer.is_verified if listing.farmer else False

    return CropListingResponse(
        id=listing.id,
        farmerId=listing.farmer_id,
        farmerName=farmer_name,
        farmerRole=farmer_role,
        cropName=listing.crop_name,
        category=listing.category,
        quantity=listing.quantity,
        quantityUnit=listing.quantity_unit,
        pricePerUnit=listing.price_per_unit,
        expectedHarvestDate=listing.expected_harvest_date,
        district=listing.district,
        upazila=listing.upazila,
        approximateLat=round(listing.approximate_lat, 2),
        approximateLon=round(listing.approximate_lon, 2),
        status=listing.status,
        isFarmerVerified=is_farmer_verified,
        description=listing.description,
        createdAt=listing.created_at,
        updatedAt=listing.updated_at,
    )


async def create_crop_listing(
    db: AsyncSession,
    farmer: User,
    req: CropListingCreateRequest,
) -> CropListingResponse:
    """Creates a new crop listing with coordinate privacy protection (Rule 17)."""
    listing = CropListing(
        farmer_id=farmer.id,
        crop_name=req.cropName,
        category=req.category,
        quantity=req.quantity,
        quantity_unit=req.quantityUnit,
        price_per_unit=req.pricePerUnit,
        expected_harvest_date=req.expectedHarvestDate,
        district=req.district,
        upazila=req.upazila,
        approximate_lat=round(req.latitude, 2),
        approximate_lon=round(req.longitude, 2),
        status=CropListingStatus.ACTIVE,
        description=req.description,
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)

    # Re-fetch with farmer relationship loaded
    stmt = select(CropListing).where(CropListing.id == listing.id)
    result = await db.execute(stmt)
    loaded = result.scalar_one()

    # Check and trigger notifications for matching saved buyer searches
    await check_and_notify_matching_saved_searches(db, loaded)

    return _map_to_response(loaded)


async def search_crop_listings(
    db: AsyncSession,
    category: Optional[CropCategory] = None,
    district: Optional[str] = None,
    max_price: Optional[int] = None,
    min_quantity: Optional[float] = None,
) -> List[CropListingResponse]:
    """Discovers active crop listings without exposing private phone numbers or exact locations."""
    stmt = select(CropListing).where(CropListing.status == CropListingStatus.ACTIVE)

    if category:
        stmt = stmt.where(CropListing.category == category)
    if district:
        stmt = stmt.where(CropListing.district.ilike(f"%{district}%"))
    if max_price is not None:
        stmt = stmt.where(CropListing.price_per_unit <= max_price)
    if min_quantity is not None:
        stmt = stmt.where(CropListing.quantity >= min_quantity)

    stmt = stmt.order_by(CropListing.created_at.desc())
    result = await db.execute(stmt)
    listings = result.scalars().all()

    return [_map_to_response(item) for item in listings]


async def list_my_crop_listings(
    db: AsyncSession,
    user: User,
) -> List[CropListingResponse]:
    """Retrieves all crop listings created by the current user."""
    stmt = (
        select(CropListing)
        .where(CropListing.farmer_id == user.id)
        .order_by(CropListing.created_at.desc())
    )
    result = await db.execute(stmt)
    listings = result.scalars().all()

    return [_map_to_response(item) for item in listings]


async def get_crop_listing(
    db: AsyncSession,
    listing_id: str,
) -> CropListingResponse:
    """Retrieves a single crop listing."""
    stmt = select(CropListing).where(CropListing.id == listing_id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing:
        raise NotFoundException(code="CROP_NOT_FOUND", message="Crop listing not found.")

    return _map_to_response(listing)


async def update_crop_listing(
    db: AsyncSession,
    user: User,
    listing_id: str,
    req: CropListingUpdateRequest,
) -> CropListingResponse:
    """Updates crop listing ensuring owner-only authorization (Rule 12)."""
    stmt = select(CropListing).where(CropListing.id == listing_id)
    result = await db.execute(stmt)
    listing = result.scalar_one_or_none()

    if not listing:
        raise NotFoundException(code="CROP_NOT_FOUND", message="Crop listing not found.")

    # Rule 12: Object-level ownership check
    if listing.farmer_id != user.id:
        raise ShikhorException(
            code="FORBIDDEN_CROP_UPDATE",
            message="You do not have permission to modify this crop listing.",
            status_code=403,
        )

    if req.cropName is not None:
        listing.crop_name = req.cropName
    if req.quantity is not None:
        listing.quantity = req.quantity
    if req.pricePerUnit is not None:
        listing.price_per_unit = req.pricePerUnit
    if req.expectedHarvestDate is not None:
        listing.expected_harvest_date = req.expectedHarvestDate
    if req.status is not None:
        listing.status = req.status
    if req.description is not None:
        listing.description = req.description

    await db.commit()
    await db.refresh(listing)

    return _map_to_response(listing)


async def check_and_notify_matching_saved_searches(
    db: AsyncSession,
    listing: CropListing,
) -> int:
    """Finds active saved buyer searches that match a newly listed crop and dispatches in-app notifications."""
    stmt = select(SavedBuyerSearch).where(
        SavedBuyerSearch.is_active == True,  # noqa: E712
        SavedBuyerSearch.buyer_id != listing.farmer_id,
    )
    result = await db.execute(stmt)
    searches = result.scalars().all()

    matched_count = 0
    for s in searches:
        # 1. Category check
        if s.category and s.category != listing.category:
            continue
        # 2. Crop name check (case-insensitive substring)
        if s.crop_name and s.crop_name.strip():
            if s.crop_name.strip().lower() not in listing.crop_name.lower():
                continue
        # 3. District check
        if s.district and s.district.strip():
            if s.district.strip().lower() not in listing.district.lower():
                continue
        # 4. Max price check
        if s.max_price is not None and listing.price_per_unit > s.max_price:
            continue
        # 5. Min quantity check
        if s.min_quantity is not None and listing.quantity < s.min_quantity:
            continue

        # Match! Dispatch notification
        unit_label = "কেজি" if listing.quantity_unit == "kg" else "মন" if listing.quantity_unit == "maund" else "টন"
        await create_notification(
            db=db,
            user_id=s.buyer_id,
            title="নতুন ফসলের সন্ধান পাওয়া গেছে!",
            message=(
                f"আপনার সংরক্ষিত সন্ধান '{s.name}'-এর সাথে মিলে নতুন {listing.crop_name} তালিকাভুক্ত হয়েছে "
                f"({listing.district}, {listing.price_per_unit} ৳/{unit_label}, পরিমাণ: {listing.quantity:g} {unit_label})।"
            ),
            notification_type="crop_match",
            link="/app/crops",
        )
        matched_count += 1

    return matched_count


def _map_saved_search_to_response(s: SavedBuyerSearch) -> SavedBuyerSearchResponse:
    return SavedBuyerSearchResponse(
        id=s.id,
        buyerId=s.buyer_id,
        name=s.name,
        category=s.category,
        cropName=s.crop_name,
        district=s.district,
        maxPrice=s.max_price,
        minQuantity=s.min_quantity,
        isActive=s.is_active,
        createdAt=s.created_at,
        updatedAt=s.updated_at,
    )


async def create_saved_buyer_search(
    db: AsyncSession,
    buyer: User,
    req: SavedBuyerSearchCreateRequest,
) -> SavedBuyerSearchResponse:
    """Creates a new saved crop search criteria for a buyer."""
    search_item = SavedBuyerSearch(
        buyer_id=buyer.id,
        name=req.name,
        category=req.category,
        crop_name=req.cropName,
        district=req.district,
        max_price=req.maxPrice,
        min_quantity=req.minQuantity,
        is_active=True,
    )
    db.add(search_item)
    await db.commit()
    await db.refresh(search_item)
    return _map_saved_search_to_response(search_item)


async def list_saved_buyer_searches(
    db: AsyncSession,
    buyer: User,
) -> List[SavedBuyerSearchResponse]:
    """Lists saved searches belonging strictly to the current buyer (Rule 12)."""
    stmt = (
        select(SavedBuyerSearch)
        .where(SavedBuyerSearch.buyer_id == buyer.id, SavedBuyerSearch.is_active == True)  # noqa: E712
        .order_by(SavedBuyerSearch.created_at.desc())
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [_map_saved_search_to_response(item) for item in items]


async def delete_saved_buyer_search(
    db: AsyncSession,
    buyer: User,
    search_id: str,
) -> None:
    """Soft deletes or removes a saved search ensuring buyer ownership (Rule 12)."""
    search_item = await db.get(SavedBuyerSearch, search_id)
    if not search_item:
        raise NotFoundException(code="SAVED_SEARCH_NOT_FOUND", message="Saved search not found.")

    if search_item.buyer_id != buyer.id:
        raise ForbiddenException(code="FORBIDDEN_SAVED_SEARCH", message="Cannot delete another user's saved search.")

    await db.delete(search_item)
    await db.commit()

