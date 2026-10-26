"""API endpoints for Expert Case-Review Portal (Later Roadmap).

Strictly complies with:
- AGENTS.md Rule 12: Object-level authorization policy (Role guards deny-by-default for non-experts).
- AGENTS.md Rule 19: AI output must be constrained, reviewable, and honest (Human-in-the-loop expert review).
- AGENTS.md Rule 26: Error, logging, and audit rules.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_role
from app.core.errors import NotFoundException, ShikhorException
from app.db.session import get_db_session
from app.modules.admin.service import record_audit_log
from app.modules.crop_assistant.models import CropCase, CropCaseStatus, ExpertCaseReview
from app.modules.crop_assistant.schemas import (
    CropCaseResponse,
    ExpertCaseReviewCreateRequest,
    ExpertCaseReviewResponse,
)
from app.modules.users.models import User, UserRole

router = APIRouter(prefix="/expert", tags=["expert"])


@router.get(
    "/cases/pending",
    response_model=List[CropCaseResponse],
    summary="List crop cases awaiting agricultural expert review (Expert/Admin only)",
)
async def list_pending_cases(
    limit: int = Query(default=50, ge=1, le=100),
    crop_type: Optional[str] = Query(default=None),
    current_user: User = Depends(require_role(UserRole.EXPERT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> List[CropCaseResponse]:
    """Retrieves uncertain, unsupported, or escalated crop cases requiring expert diagnosis."""
    query = (
        select(CropCase)
        .where(
            (CropCase.is_reviewed_by_expert == False)  # noqa: E712
            & (
                (CropCase.status.in_([CropCaseStatus.UNCERTAIN, CropCaseStatus.UNSUPPORTED]))
                | (CropCase.escalation_recommended == True)  # noqa: E712
            )
        )
        .order_by(desc(CropCase.created_at))
        .limit(limit)
    )

    if crop_type:
        query = query.where(CropCase.crop_type == crop_type)

    result = await db.execute(query)
    cases = result.scalars().all()
    return [CropCaseResponse.model_validate(c) for c in cases]


@router.post(
    "/cases/{case_id}/review",
    response_model=ExpertCaseReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit official agricultural diagnosis and vetted prescription (Expert/Admin only)",
)
async def submit_case_review(
    case_id: str,
    req: ExpertCaseReviewCreateRequest,
    request: Request,
    current_user: User = Depends(require_role(UserRole.EXPERT, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> ExpertCaseReviewResponse:
    """Submits vetted diagnosis, updates case state, and logs immutable audit trail."""
    crop_case = await db.get(CropCase, case_id)
    if not crop_case:
        raise NotFoundException("Crop case not found", "ফসলের রোগ কেসটি পাওয়া যায়নি।")

    request_id = getattr(request.state, "request_id", None) if hasattr(request, "state") else None

    # Create expert review record
    review = ExpertCaseReview(
        crop_case_id=crop_case.id,
        expert_id=current_user.id,
        expert_name=current_user.full_name,
        reviewed_diagnosis=req.reviewedDiagnosis,
        prescribed_treatment=req.prescribedTreatment,
        severity_level=req.severityLevel,
        expert_notes=req.expertNotes,
    )
    db.add(review)

    # Update crop case with expert verified information
    crop_case.is_reviewed_by_expert = True
    crop_case.possible_condition = f"{req.reviewedDiagnosis} (কৃষিবিদ দ্বারা যাচাইকৃত)"
    crop_case.confidence = 1.0
    crop_case.confidence_band = "expert_verified"
    crop_case.escalation_recommended = False

    # Add vetted prescription to guidance
    current_guidance = list(crop_case.guidance) if crop_case.guidance else []
    expert_prescription_item = f"বিশেষজ্ঞের প্রেসক্রিপশন: {req.prescribedTreatment}"
    if expert_prescription_item not in current_guidance:
        current_guidance.insert(0, expert_prescription_item)
    crop_case.guidance = current_guidance

    # Audit log (Rule 26)
    await record_audit_log(
        db=db,
        actor=current_user,
        action="EXPERT_CASE_REVIEW",
        resource_type="crop_case",
        resource_id=crop_case.id,
        details={
            "diagnosis": req.reviewedDiagnosis,
            "severity": req.severityLevel,
            "expert_name": current_user.full_name,
        },
        request_id=request_id,
    )

    # Fetch farmer user details for notification and email
    farmer = await db.get(User, crop_case.user_id)

    # 1. In-App Notification (AGENTS.md Rule 5 & 26)
    from app.modules.notifications.models import Notification
    farmer_notif = Notification(
        user_id=crop_case.user_id,
        title="🌿 কৃষি বিশেষজ্ঞের প্রেসক্রিপশন পাওয়া গেছে",
        message=f"আপনার {crop_case.crop_type} ফসলের জন্য কৃষিবিদ {current_user.full_name} রোগ যাচাই করে সমাধান ও প্রেসক্রিপশন দিয়েছেন।",
        notification_type="expert_review",
        link="/crop-assistant",
    )
    db.add(farmer_notif)

    # 2. Outbound Email Dispatch if farmer has email
    if farmer and farmer.email:
        import asyncio
        from app.integrations.email.sender import get_expert_review_email_html, send_email
        try:
            email_html = get_expert_review_email_html(
                farmer_name=farmer.full_name or "সম্মানিত কৃষক",
                crop_name=crop_case.crop_type,
                diagnosis=req.reviewedDiagnosis,
                treatment=req.prescribedTreatment,
                severity=req.severityLevel,
                expert_name=current_user.full_name,
                notes=req.expertNotes,
                case_id=crop_case.id,
            )
            asyncio.create_task(
                send_email(
                    to_email=farmer.email,
                    subject=f"🌿 [{crop_case.crop_type}] বিশেষজ্ঞের রোগ যাচাই ও প্রেসক্রিপশন রিপোর্ট - শিখড় এআই",
                    html_body=email_html,
                    text_body=(
                        f"প্রিয় {farmer.full_name},\n"
                        f"আপনার {crop_case.crop_type} ফসলের নমুনা কৃষিবিদ {current_user.full_name} যাচাই করেছেন।\n"
                        f"সনাক্তকৃত রোগ: {req.reviewedDiagnosis}\n"
                        f"প্রেসক্রিপশন ও করণীয়: {req.prescribedTreatment}\n\n"
                        f"শিখড় এআই অ্যাপে লগইন করে বিস্তারিত দেখুন: http://localhost:5173/crop-assistant"
                    ),
                )
            )
        except Exception as mail_exc:
            import logging
            logging.getLogger("shikhor.expert").warning(
                f"Failed to dispatch expert review email to {farmer.email}: {mail_exc}"
            )

    await db.commit()
    await db.refresh(review)
    return ExpertCaseReviewResponse.model_validate(review)


@router.get(
    "/cases/{case_id}/review",
    response_model=ExpertCaseReviewResponse,
    summary="Get expert review for a crop case (Open to case owner/authenticated)",
)
async def get_case_review(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ExpertCaseReviewResponse:
    """Retrieves the official expert review for a crop case."""
    crop_case = await db.get(CropCase, case_id)
    if not crop_case:
        raise NotFoundException("Crop case not found", "ফসলের রোগ কেসটি পাওয়া যায়নি।")

    # Fetch latest expert review
    query = (
        select(ExpertCaseReview)
        .where(ExpertCaseReview.crop_case_id == case_id)
        .order_by(desc(ExpertCaseReview.created_at))
        .limit(1)
    )
    res = await db.execute(query)
    review = res.scalar_one_or_none()
    if not review:
        raise NotFoundException("Review not found", "এই কেসটির জন্য এখনো কোনো বিশেষজ্ঞ রিভিউ দেওয়া হয়নি।")

    return ExpertCaseReviewResponse.model_validate(review)
