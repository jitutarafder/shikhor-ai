from datetime import date, timedelta
from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenException, NotFoundException, ShikhorException
from app.db.mongo.schemas import (
    EquipmentDocument,
    EquipmentReviewDoc,
    EquipmentTypeEnum,
    GeoJSONPoint,
    PriceUnitEnum,
)
from app.db.service_bridge import get_mongo_registry, is_mongodb_backend
from app.modules.equipment.models import Equipment, EquipmentReview, EquipmentType, PriceUnit
from app.modules.equipment.ranking import (
    RankingBreakdown,
    rank_equipment_candidates,
)
from app.modules.equipment.schemas import (
    BookedDateItem,
    EquipmentAvailabilityResponse,
    EquipmentCreateRequest,
    EquipmentResponse,
    EquipmentReviewCreate,
    EquipmentReviewResponse,
    EquipmentUpdateRequest,
    RankingBreakdownSchema,
)
from app.modules.rentals.models import RentalRequest, RentalStatus
from app.modules.users.models import User


def _to_equipment_response_from_mongo(
    item: EquipmentDocument,
    ranking_breakdown: Optional[RankingBreakdown] = None,
    owner_name: Optional[str] = None,
    is_owner_verified: bool = False,
) -> EquipmentResponse:
    """Helper converting Equipment MongoDB document to API response."""
    reviews = getattr(item, "reviews", []) or []
    review_count = len(reviews)
    average_rating = (
        round(sum(r.rating for r in reviews) / review_count, 1)
        if review_count > 0
        else None
    )

    eq_type_str = item.equipment_type.value if hasattr(item.equipment_type, "value") else str(item.equipment_type)
    price_unit_str = item.price_unit.value if hasattr(item.price_unit, "value") else str(item.price_unit)

    return EquipmentResponse(
        id=item.id,
        owner_id=item.owner_id,
        name=item.name,
        equipment_type=EquipmentType(eq_type_str),
        description=item.description,
        price_amount=item.price_amount,
        price_unit=PriceUnit(price_unit_str),
        district=item.district,
        upazila=item.upazila,
        service_radius_km=item.service_radius_km,
        is_available=item.is_available,
        is_paused=item.is_paused,
        approximate_lat=round(item.latitude, 2),
        approximate_lon=round(item.longitude, 2),
        owner_name=owner_name,
        is_owner_verified=is_owner_verified,
        average_rating=average_rating,
        review_count=review_count,
        created_at=item.created_at,
        ranking=(
            RankingBreakdownSchema(
                priceScore=ranking_breakdown.price_score,
                distanceScore=ranking_breakdown.distance_score,
                rankingScore=ranking_breakdown.ranking_score,
                distanceKm=ranking_breakdown.distance_km,
            )
            if ranking_breakdown
            else None
        ),
    )


def _to_equipment_response(
    item: Equipment,
    ranking_breakdown: Optional[RankingBreakdown] = None,
) -> EquipmentResponse:
    """Helper converting Equipment ORM model to response with rounded coordinates (Rule 17)."""
    reviews = getattr(item, "reviews", []) or []
    review_count = len(reviews)
    average_rating = (
        round(sum(r.rating for r in reviews) / review_count, 1)
        if review_count > 0
        else None
    )

    return EquipmentResponse(
        id=item.id,
        owner_id=item.owner_id,
        name=item.name,
        equipment_type=item.equipment_type,
        description=item.description,
        price_amount=item.price_amount,
        price_unit=item.price_unit,
        district=item.district,
        upazila=item.upazila,
        service_radius_km=item.service_radius_km,
        is_available=item.is_available,
        is_paused=item.is_paused,
        # Rule 17: Approximate coordinate obfuscation (~1.1km grid)
        approximate_lat=round(item.latitude, 2),
        approximate_lon=round(item.longitude, 2),
        owner_name=item.owner.full_name if item.owner else None,
        is_owner_verified=item.owner.is_verified if item.owner else False,
        average_rating=average_rating,
        review_count=review_count,
        created_at=item.created_at,
        ranking=(
            RankingBreakdownSchema(
                priceScore=ranking_breakdown.price_score,
                distanceScore=ranking_breakdown.distance_score,
                rankingScore=ranking_breakdown.ranking_score,
                distanceKm=ranking_breakdown.distance_km,
            )
            if ranking_breakdown
            else None
        ),
    )


async def create_equipment(
    db: AsyncSession,
    owner: Any,
    req: EquipmentCreateRequest,
) -> EquipmentResponse:
    """Creates a new equipment listing owned by the current user."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        eq_type_str = req.equipmentType.value if hasattr(req.equipmentType, "value") else str(req.equipmentType)
        price_unit_str = req.priceUnit.value if hasattr(req.priceUnit, "value") else str(req.priceUnit)
        eq_doc = EquipmentDocument(
            owner_id=owner.id,
            name=req.name,
            equipment_type=EquipmentTypeEnum(eq_type_str),
            description=req.description,
            price_amount=req.priceAmount,
            price_unit=PriceUnitEnum(price_unit_str),
            district=req.district,
            upazila=req.upazila,
            service_radius_km=req.serviceRadiusKm,
            location=GeoJSONPoint(coordinates=[req.longitude, req.latitude]),
            is_available=True,
            is_paused=False,
        )
        saved = reg.equipment.insert_one(eq_doc)
        return _to_equipment_response_from_mongo(
            saved,
            owner_name=owner.full_name,
            is_owner_verified=owner.is_verified,
        )

    item = Equipment(
        owner_id=owner.id,
        name=req.name,
        equipment_type=req.equipmentType,
        description=req.description,
        price_amount=req.priceAmount,
        price_unit=req.priceUnit,
        district=req.district,
        upazila=req.upazila,
        latitude=req.latitude,
        longitude=req.longitude,
        service_radius_km=req.serviceRadiusKm,
        is_available=True,
        is_paused=False,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _to_equipment_response(item)


async def update_equipment(
    db: AsyncSession,
    owner: Any,
    equipment_id: str,
    req: EquipmentUpdateRequest,
) -> EquipmentResponse:
    """Updates equipment details, strictly verifying ownership (Rule 12)."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        item = reg.equipment.find_by_id(equipment_id)
        if not item:
            raise NotFoundException(code="EQUIPMENT_NOT_FOUND", message="Equipment listing not found.")
        owner_role_str = owner.role.value if hasattr(owner.role, "value") else str(owner.role)
        if item.owner_id != owner.id and owner_role_str not in ("admin", "moderator"):
            raise ForbiddenException(
                code="FORBIDDEN_EQUIPMENT_UPDATE",
                message="You do not have permission to modify this equipment listing.",
            )
        update_fields = {}
        if req.name is not None: item.name = req.name; update_fields["name"] = req.name
        if req.description is not None: item.description = req.description; update_fields["description"] = req.description
        if req.priceAmount is not None: item.price_amount = req.priceAmount; update_fields["price_amount"] = req.priceAmount
        if req.serviceRadiusKm is not None: item.service_radius_km = req.serviceRadiusKm; update_fields["service_radius_km"] = req.serviceRadiusKm
        if req.isAvailable is not None: item.is_available = req.isAvailable; update_fields["is_available"] = req.isAvailable
        if req.isPaused is not None: item.is_paused = req.isPaused; update_fields["is_paused"] = req.isPaused

        if update_fields:
            reg.equipment.collection.update_one({"_id": equipment_id}, {"$set": update_fields})
        return _to_equipment_response_from_mongo(item, owner_name=owner.full_name, is_owner_verified=owner.is_verified)

    item = await db.get(Equipment, equipment_id)
    if not item:
        raise NotFoundException(code="EQUIPMENT_NOT_FOUND", message="Equipment listing not found.")

    if item.owner_id != owner.id and owner.role.value not in ("admin", "moderator"):
        raise ForbiddenException(
            code="FORBIDDEN_EQUIPMENT_UPDATE",
            message="You do not have permission to modify this equipment listing.",
        )

    if req.name is not None:
        item.name = req.name
    if req.description is not None:
        item.description = req.description
    if req.priceAmount is not None:
        item.price_amount = req.priceAmount
    if req.serviceRadiusKm is not None:
        item.service_radius_km = req.serviceRadiusKm
    if req.isAvailable is not None:
        item.is_available = req.isAvailable
    if req.isPaused is not None:
        item.is_paused = req.isPaused

    await db.commit()
    await db.refresh(item)
    return _to_equipment_response(item)


async def list_owner_equipment(
    db: AsyncSession,
    owner: Any,
) -> List[EquipmentResponse]:
    """Retrieves all equipment listings owned by the user."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        items = reg.equipment.get_by_owner(owner.id)
        return [_to_equipment_response_from_mongo(item, owner_name=owner.full_name, is_owner_verified=owner.is_verified) for item in items]

    stmt = select(Equipment).where(Equipment.owner_id == owner.id).order_by(Equipment.created_at.desc())
    result = await db.execute(stmt)
    return [_to_equipment_response(item) for item in result.scalars().all()]


async def get_equipment(
    db: AsyncSession,
    equipment_id: str,
) -> EquipmentResponse:
    """Retrieves a single equipment listing."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        item = reg.equipment.find_by_id(equipment_id)
        if not item:
            raise NotFoundException(code="EQUIPMENT_NOT_FOUND", message="Equipment listing not found.")
        owner = reg.users.find_by_id(item.owner_id)
        return _to_equipment_response_from_mongo(
            item,
            owner_name=owner.full_name if owner else None,
            is_owner_verified=owner.is_verified if owner else False,
        )

    item = await db.get(Equipment, equipment_id)
    if not item:
        raise NotFoundException(code="EQUIPMENT_NOT_FOUND", message="Equipment listing not found.")
    return _to_equipment_response(item)


async def search_and_rank_equipment(
    db: AsyncSession,
    equipment_type: EquipmentType,
    price_unit: PriceUnit,
    user_lat: float,
    user_lon: float,
    max_radius_km: Optional[float] = None,
) -> List[EquipmentResponse]:
    """Discovers available equipment and ranks candidates using the approved 65/35 formula."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        eq_type_str = equipment_type.value if hasattr(equipment_type, "value") else str(equipment_type)
        price_unit_str = price_unit.value if hasattr(price_unit, "value") else str(price_unit)
        mongo_candidates = [
            EquipmentDocument.model_validate(c)
            for c in reg.equipment.collection.find({
                "equipment_type": eq_type_str,
                "price_unit": price_unit_str,
                "is_available": True,
                "is_paused": False,
            })
        ]

        ranked_items = rank_equipment_candidates(
            candidates=mongo_candidates,
            user_lat=user_lat,
            user_lon=user_lon,
            target_unit=price_unit,
            max_radius_km=max_radius_km,
        )

        responses = []
        for ranked in ranked_items:
            owner = reg.users.find_by_id(ranked.equipment.owner_id)
            resp = _to_equipment_response_from_mongo(
                ranked.equipment,
                ranking_breakdown=RankingBreakdown(
                    price_score=ranked.price_score,
                    distance_score=ranked.distance_score,
                    ranking_score=ranked.ranking_score,
                    distance_km=ranked.distance_km,
                ),
                owner_name=owner.full_name if owner else None,
                is_owner_verified=owner.is_verified if owner else False,
            )
            responses.append(resp)
        return responses
    stmt = select(Equipment).where(
        Equipment.equipment_type == equipment_type,
        Equipment.price_unit == price_unit,
        Equipment.is_available == True,
        Equipment.is_paused == False,
    )
    result = await db.execute(stmt)
    candidates = list(result.scalars().all())

    ranked_items = rank_equipment_candidates(
        candidates=candidates,
        user_lat=user_lat,
        user_lon=user_lon,
        target_unit=price_unit,
        max_radius_km=max_radius_km,
    )

    return [
        _to_equipment_response(
            ranked.equipment,
            ranking_breakdown=RankingBreakdown(
                price_score=ranked.price_score,
                distance_score=ranked.distance_score,
                ranking_score=ranked.ranking_score,
                distance_km=ranked.distance_km,
            ),
        )
        for ranked in ranked_items
    ]


async def get_equipment_availability(
    db: AsyncSession,
    equipment_id: str,
) -> EquipmentAvailabilityResponse:
    """Retrieves upcoming accepted booking dates for machinery calendar."""
    equipment = await db.get(Equipment, equipment_id)
    if not equipment:
        raise NotFoundException(code="EQUIPMENT_NOT_FOUND", message="Equipment listing not found.")

    stmt = (
        select(RentalRequest)
        .where(
            RentalRequest.equipment_id == equipment_id,
            RentalRequest.status == RentalStatus.ACCEPTED,
        )
        .order_by(RentalRequest.rental_date.asc())
    )
    result = await db.execute(stmt)
    rentals = result.scalars().all()

    from datetime import timedelta
    all_booked_dates: dict[date, int] = {}
    for r in rentals:
        if r.selected_dates:
            for s in r.selected_dates.split(","):
                s = s.strip()
                if s:
                    try:
                        d = date.fromisoformat(s)
                        all_booked_dates[d] = 1
                    except ValueError:
                        pass
        else:
            all_booked_dates[r.rental_date] = r.duration_units
            if r.duration_units > 1:
                for i in range(1, r.duration_units):
                    all_booked_dates[r.rental_date + timedelta(days=i)] = 1

    booked_items = [
        BookedDateItem(
            rental_date=d,
            date=d.isoformat(),
            duration_units=all_booked_dates[d],
            status="booked",
        )
        for d in sorted(all_booked_dates.keys())
    ]
    return EquipmentAvailabilityResponse(equipment_id=equipment_id, booked_dates=booked_items)


async def create_equipment_review(
    db: AsyncSession,
    renter: User,
    equipment_id: str,
    req: EquipmentReviewCreate,
) -> EquipmentReviewResponse:
    """Submits a post-completion review strictly validated against completed transactions (Security.md & Rule 11)."""
    equipment = await db.get(Equipment, equipment_id)
    if not equipment:
        raise NotFoundException(code="EQUIPMENT_NOT_FOUND", message="Equipment listing not found.")

    rental = await db.get(RentalRequest, req.rentalRequestId)
    if not rental or rental.equipment_id != equipment_id:
        raise NotFoundException(code="RENTAL_NOT_FOUND", message="Rental transaction not found for this equipment.")

    if rental.renter_id != renter.id:
        raise ForbiddenException(code="FORBIDDEN_REVIEW", message="You can only review rentals that you booked.")

    if rental.status != RentalStatus.COMPLETED:
        raise ShikhorException(
            code="RENTAL_NOT_COMPLETED",
            message="ভাড়া সম্পন্ন হওয়ার পরেই কেবল রেটিং ও রিভিউ প্রদান করা সম্ভব।",
            status_code=400,
        )

    # Check for existing review
    existing = await db.scalar(
        select(EquipmentReview).where(EquipmentReview.rental_request_id == req.rentalRequestId)
    )
    if existing:
        raise ShikhorException(
            code="REVIEW_ALREADY_EXISTS",
            message="আপনি ইতিমধ্যে এই ভাড়ার জন্য রিভিউ জমা দিয়েছেন।",
            status_code=400,
        )

    review = EquipmentReview(
        equipment_id=equipment_id,
        renter_id=renter.id,
        rental_request_id=req.rentalRequestId,
        rating=req.rating,
        comment=req.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return EquipmentReviewResponse(
        id=review.id,
        equipment_id=review.equipment_id,
        renter_id=review.renter_id,
        renter_name=renter.full_name,
        rental_request_id=review.rental_request_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


async def list_equipment_reviews(
    db: AsyncSession,
    equipment_id: str,
) -> List[EquipmentReviewResponse]:
    """Retrieves all reviews for a piece of agricultural machinery."""
    stmt = (
        select(EquipmentReview)
        .where(EquipmentReview.equipment_id == equipment_id)
        .order_by(EquipmentReview.created_at.desc())
    )
    result = await db.execute(stmt)
    reviews = result.scalars().all()

    return [
        EquipmentReviewResponse(
            id=r.id,
            equipment_id=r.equipment_id,
            renter_id=r.renter_id,
            renter_name=r.renter.full_name if r.renter else "কৃষক",
            rental_request_id=r.rental_request_id,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in reviews
    ]
