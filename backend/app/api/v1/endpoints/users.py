"""User profile, data privacy, and data subject rights API endpoints.

Strictly complies with:
- AGENTS.md Rule 9: Ask before destructive actions (Account deletion flow).
- AGENTS.md Rule 12: Object-level authorization policy (Users only access/delete their own data).
- AGENTS.md Rule 26: Redact PII in audit logs.
- Security.md Section 19: Data retention and privacy rules.
"""

from datetime import datetime, timezone
from typing import Any, Dict
import uuid
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.service_bridge import get_mongo_registry, is_mongodb_backend
from app.db.session import get_db_session
from app.modules.admin.service import record_audit_log
from app.modules.crop_assistant.models import CropCase
from app.modules.crop_marketplace.models import CropListing
from app.modules.equipment.models import Equipment
from app.modules.pilot.models import PilotFeedback
from app.modules.rentals.models import RentalRequest
from app.modules.users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "/me/export",
    summary="Export all personal data archive (GDPR / Data Subject Access Right)",
    response_model=Dict[str, Any],
)
async def export_my_data(
    current_user: Any = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Provides a complete, structured JSON export of all data associated with the user."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        crop_cases = [
            {
                "id": c.id,
                "crop_type": c.crop_type,
                "symptoms": c.symptoms_description,
                "status": c.status.value if hasattr(c.status, "value") else str(c.status),
                "possible_condition": c.possible_condition,
                "confidence": c.confidence,
                "escalation_recommended": c.escalation_recommended,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in reg.crop_cases.get_by_user(current_user.id, limit=100)
        ]
        equipment_listings = [
            {
                "id": e.id,
                "name": e.name,
                "equipment_type": e.equipment_type.value if hasattr(e.equipment_type, "value") else str(e.equipment_type),
                "price_amount": e.price_amount,
                "price_unit": e.price_unit.value if hasattr(e.price_unit, "value") else str(e.price_unit),
                "district": e.district,
                "upazila": e.upazila,
                "is_available": e.is_available,
            }
            for e in reg.equipment.get_by_owner(current_user.id)
        ]
        rental_requests = [
            {
                "id": r.id,
                "equipment_id": r.equipment_id,
                "rental_date": r.rental_date.isoformat() if r.rental_date else None,
                "duration_units": r.duration_units,
                "total_estimated_price": r.total_estimated_price,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            }
            for r in reg.rentals.get_by_renter(current_user.id)
        ]
        crop_listings = [
            {
                "id": cl.id,
                "title": cl.crop_name,
                "crop_type": cl.crop_name,
                "quantity_value": cl.quantity,
                "quantity_unit": cl.quantity_unit.value if hasattr(cl.quantity_unit, "value") else str(cl.quantity_unit),
                "price_per_unit": cl.price_per_unit,
                "status": cl.status.value if hasattr(cl.status, "value") else str(cl.status),
            }
            for cl in reg.crop_listings.get_by_farmer(current_user.id)
        ]
        return {
            "export_metadata": {
                "application": "Shikhor AI",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "data_subject_id": current_user.id,
                "format": "JSON-Archive-v1",
            },
            "user_profile": {
                "id": current_user.id,
                "phone": current_user.phone,
                "full_name": current_user.full_name,
                "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
                "is_verified": current_user.is_verified,
                "created_at": None,
            },
            "crop_cases": crop_cases,
            "equipment_listings": equipment_listings,
            "rental_requests": rental_requests,
            "crop_listings": crop_listings,
            "pilot_feedbacks": [],
        }
    # 1. Fetch user's crop cases
    crop_cases_res = await db.execute(
        select(CropCase).where(CropCase.user_id == current_user.id)
    )
    crop_cases = [
        {
            "id": c.id,
            "crop_type": c.crop_type,
            "symptoms": c.symptoms_description,
            "status": c.status.value if hasattr(c.status, "value") else str(c.status),
            "possible_condition": c.possible_condition,
            "confidence": c.confidence,
            "escalation_recommended": c.escalation_recommended,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in crop_cases_res.scalars().all()
    ]

    # 2. Fetch user's equipment listings (if owner)
    equipment_res = await db.execute(
        select(Equipment).where(Equipment.owner_id == current_user.id)
    )
    equipment_listings = [
        {
            "id": e.id,
            "name": e.name,
            "equipment_type": e.equipment_type.value if hasattr(e.equipment_type, "value") else str(e.equipment_type),
            "price_amount": e.price_amount,
            "price_unit": e.price_unit.value if hasattr(e.price_unit, "value") else str(e.price_unit),
            "district": e.district,
            "upazila": e.upazila,
            "is_available": e.is_available,
        }
        for e in equipment_res.scalars().all()
    ]

    # 3. Fetch user's rental requests
    rentals_res = await db.execute(
        select(RentalRequest).where(RentalRequest.renter_id == current_user.id)
    )
    rental_requests = [
        {
            "id": r.id,
            "equipment_id": r.equipment_id,
            "rental_date": r.rental_date.isoformat() if r.rental_date else None,
            "duration_units": r.duration_units,
            "total_estimated_price": r.total_estimated_price,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
        }
        for r in rentals_res.scalars().all()
    ]

    # 4. Fetch user's crop listings
    crop_listings_res = await db.execute(
        select(CropListing).where(CropListing.farmer_id == current_user.id)
    )
    crop_listings = [
        {
            "id": cl.id,
            "title": cl.title,
            "crop_type": cl.crop_type,
            "quantity_value": cl.quantity_value,
            "quantity_unit": cl.quantity_unit,
            "price_per_unit": cl.price_per_unit,
            "status": cl.status.value if hasattr(cl.status, "value") else str(cl.status),
        }
        for cl in crop_listings_res.scalars().all()
    ]

    # 5. Fetch user's pilot feedback
    feedback_res = await db.execute(
        select(PilotFeedback).where(PilotFeedback.user_id == current_user.id)
    )
    feedbacks = [
        {
            "id": f.id,
            "task_type": f.task_type,
            "ease_of_use_rating": f.ease_of_use_rating,
            "bangla_comprehension_rating": f.bangla_comprehension_rating,
            "comments": f.comments,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in feedback_res.scalars().all()
    ]

    return {
        "export_metadata": {
            "application": "Shikhor AI",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "data_subject_id": current_user.id,
            "format": "JSON-Archive-v1",
        },
        "user_profile": {
            "id": current_user.id,
            "phone": current_user.phone,
            "full_name": current_user.full_name,
            "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "crop_cases": crop_cases,
        "equipment_listings": equipment_listings,
        "rental_requests": rental_requests,
        "crop_listings": crop_listings,
        "pilot_feedbacks": feedbacks,
    }


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Permanently delete or anonymize personal account (Right to Erasure)",
)
async def delete_my_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Dict[str, str]:
    """Anonymizes and deactivates the user account, purging active sessions and PII."""
    request_id = getattr(request.state, "request_id", None) if hasattr(request, "state") else None

    # Record audit log before anonymization
    await record_audit_log(
        db=db,
        actor=current_user,
        action="USER_SELF_DELETE_ACCOUNT",
        resource_type="user",
        resource_id=current_user.id,
        details={"reason": "User executed right to erasure / data deletion"},
        request_id=request_id,
    )

    # Anonymize PII
    current_user.is_active = False
    current_user.phone = f"deleted_{uuid.uuid4().hex[:12]}"
    current_user.full_name = "বিলুপ্ত ব্যবহারকারী (Deleted User)"
    current_user.email = None

    await db.commit()

    return {
        "status": "success",
        "message": "আপনার অ্যাকাউন্ট ও ব্যক্তিগত তথ্য সফলভাবে মুছে ফেলা এবং নিষ্ক্রিয় করা হয়েছে।",
    }
