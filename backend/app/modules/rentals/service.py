"""Rental requests domain service managing creation, state transitions, and idempotency."""

from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException, ShikhorException
from app.modules.equipment.models import Equipment
from app.modules.rentals.models import RentalRequest, RentalStatus
from app.modules.rentals.schemas import RentalRequestCreate
from app.modules.rentals.state_machine import transition_rental_status
from app.modules.users.models import User


import logging
from app.integrations.email import (
    get_rental_accepted_email_html,
    get_rental_rejected_email_html,
    get_rental_request_email_html,
    send_email,
)

logger = logging.getLogger("shikhor.rentals")


async def create_rental(
    db: AsyncSession,
    renter: User,
    req: RentalRequestCreate,
) -> RentalRequest:
    """Creates a rental request with idempotency protection (Rule 21)."""
    # 1. Idempotency replay check
    if req.idempotencyKey:
        existing = await db.scalar(
            select(RentalRequest).where(
                RentalRequest.idempotency_key == req.idempotencyKey,
                RentalRequest.renter_id == renter.id,
            )
        )
        if existing:
            # Replay existing result without duplicating records
            return existing

    # 2. Check equipment availability
    equipment = await db.get(Equipment, req.equipmentId)
    if not equipment:
        raise NotFoundException(code="EQUIPMENT_NOT_FOUND", message="Equipment listing not found.")

    if not equipment.is_available or equipment.is_paused:
        raise ShikhorException(
            code="EQUIPMENT_UNAVAILABLE",
            message="This machinery is currently unavailable for rental.",
            status_code=400,
        )

    # 1. Determine all requested dates
    requested_dates: list[date] = []
    if req.selectedDates and len(req.selectedDates) > 0:
        requested_dates = sorted(list(set(req.selectedDates)))
    else:
        requested_dates = [req.rentalDate]
        if equipment.price_unit == "per_day" and req.durationUnits > 1:
            for i in range(1, req.durationUnits):
                requested_dates.append(req.rentalDate + timedelta(days=i))

    primary_date = requested_dates[0]
    duration_units = (
        len(requested_dates)
        if (req.selectedDates and len(req.selectedDates) > 0 and equipment.price_unit == "per_day")
        else req.durationUnits
    )

    # 2. Check conflict against all ACCEPTED bookings for this equipment
    accepted_stmt = select(RentalRequest).where(
        RentalRequest.equipment_id == req.equipmentId,
        RentalRequest.status == RentalStatus.ACCEPTED,
    )
    res = await db.execute(accepted_stmt)
    accepted_rentals = res.scalars().all()

    existing_booked_dates: set[date] = set()
    for r in accepted_rentals:
        if r.selected_dates:
            for s in r.selected_dates.split(","):
                s = s.strip()
                if s:
                    try:
                        existing_booked_dates.add(date.fromisoformat(s))
                    except ValueError:
                        pass
        else:
            existing_booked_dates.add(r.rental_date)
            if r.duration_units > 1:
                for i in range(1, r.duration_units):
                    existing_booked_dates.add(r.rental_date + timedelta(days=i))

    for d in requested_dates:
        if d in existing_booked_dates:
            raise ShikhorException(
                code="DATE_ALREADY_BOOKED",
                message=f"নির্বাচিত তারিখগুলোর মধ্যে {d.isoformat()} ইতিমধ্যে অন্য একজন কৃষকের জন্য বুক করা রয়েছে। অনুগ্রহ করে ক্যালেন্ডার দেখে অন্য তারিখ নির্বাচন করুন।",
                status_code=400,
            )

    # 3. Calculate exact total estimated price
    total_price = equipment.price_amount * duration_units

    # 4. Create rental request
    selected_dates_str = ",".join(d.isoformat() for d in requested_dates)
    rental = RentalRequest(
        equipment_id=equipment.id,
        renter_id=renter.id,
        rental_date=primary_date,
        selected_dates=selected_dates_str,
        duration_units=duration_units,
        total_estimated_price=total_price,
        note=req.note,
        status=RentalStatus.PENDING,
        idempotency_key=req.idempotencyKey,
    )
    db.add(rental)
    await db.commit()
    await db.refresh(rental)

    # 5. Send Email notification to Equipment Owner if owner has email
    try:
        owner = await db.get(User, equipment.owner_id)
        if owner and owner.email:
            email_html = get_rental_request_email_html(
                owner_name=owner.full_name or "যন্ত্রের মালিক",
                renter_name=renter.full_name or "কৃষক",
                renter_phone=renter.phone or "প্রদান করা হয়নি",
                equipment_name=equipment.name,
                dates_str=selected_dates_str,
                duration_units=duration_units,
                price_unit=equipment.price_unit,
                total_price=float(total_price),
            )
            await send_email(
                to_email=owner.email,
                subject=f"[শিখড় এআই] নতুন যন্ত্রপাতি ভাড়ার অনুরোধ: {equipment.name}",
                html_content=email_html,
            )
            logger.info(f"Rental request notification email sent to owner {owner.email}")
    except Exception as e:
        logger.warning(f"Failed to dispatch rental request email to owner: {e}")

    return rental


async def update_rental_request_status(
    db: AsyncSession,
    actor: User,
    rental_id: str,
    target_status: RentalStatus,
) -> RentalRequest:
    """Transitions rental request status via the central state machine (Rule 14)."""
    rental = await db.get(RentalRequest, rental_id)
    if not rental:
        raise NotFoundException(code="RENTAL_NOT_FOUND", message="Rental request not found.")

    equipment = await db.get(Equipment, rental.equipment_id)
    owner_id = equipment.owner_id if equipment else ""

    transition_rental_status(
        rental_request=rental,
        target_status=target_status,
        actor_id=actor.id,
        owner_id=owner_id,
    )

    await db.commit()
    await db.refresh(rental)

    # Dispatch status change email to Renter (Farmer)
    try:
        renter = await db.get(User, rental.renter_id)
        owner = await db.get(User, owner_id) if owner_id else None

        if renter and renter.email and equipment:
            selected_dates_display = rental.selected_dates or rental.rental_date.isoformat()

            if target_status == RentalStatus.ACCEPTED:
                email_html = get_rental_accepted_email_html(
                    renter_name=renter.full_name or "কৃষক",
                    owner_name=owner.full_name if owner else "যন্ত্রের মালিক",
                    owner_phone=owner.phone if owner else "প্রদান করা হয়নি",
                    equipment_name=equipment.name,
                    dates_str=selected_dates_display,
                    total_price=float(rental.total_estimated_price),
                )
                await send_email(
                    to_email=renter.email,
                    subject=f"[শিখড় এআই] অভিনন্দন! আপনার ভাড়ার অনুরোধ গৃহীত হয়েছে: {equipment.name}",
                    html_content=email_html,
                )
                logger.info(f"Rental acceptance notification sent to renter {renter.email}")

            elif target_status == RentalStatus.REJECTED:
                email_html = get_rental_rejected_email_html(
                    renter_name=renter.full_name or "কৃষক",
                    equipment_name=equipment.name,
                    dates_str=selected_dates_display,
                )
                await send_email(
                    to_email=renter.email,
                    subject=f"[শিখড় এআই] ভাড়ার অনুরোধ সংক্রান্ত বিজ্ঞপ্তি: {equipment.name}",
                    html_content=email_html,
                )
                logger.info(f"Rental rejection notification sent to renter {renter.email}")
    except Exception as e:
        logger.warning(f"Failed to dispatch rental transition email to renter: {e}")

    return rental


async def list_user_rentals(
    db: AsyncSession,
    user: User,
) -> List[RentalRequest]:
    """Lists rental requests where user is either the renter or the machinery owner."""
    stmt = (
        select(RentalRequest)
        .join(Equipment, RentalRequest.equipment_id == Equipment.id)
        .where(
            (RentalRequest.renter_id == user.id) | (Equipment.owner_id == user.id)
        )
        .order_by(RentalRequest.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_rental_by_id(
    db: AsyncSession,
    user: User,
    rental_id: str,
) -> RentalRequest:
    """Retrieves a single rental request ensuring user is renter or equipment owner (Rule 12)."""
    rental = await db.get(RentalRequest, rental_id)
    if not rental:
        raise NotFoundException(code="RENTAL_NOT_FOUND", message="Rental request not found.")

    equipment = await db.get(Equipment, rental.equipment_id)
    owner_id = equipment.owner_id if equipment else ""

    if user.id != rental.renter_id and user.id != owner_id:
        raise ShikhorException(
            code="UNAUTHORIZED_ACCESS",
            message="You are not authorized to view this rental request.",
            status_code=403,
        )

    return rental
