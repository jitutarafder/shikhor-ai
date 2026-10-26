"""Crop Assistant workflow domain service."""

import os
from pathlib import Path
from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.image_safety import sanitize_and_reencode_image
from app.core.config import settings
from app.core.errors import ForbiddenException, NotFoundException
from app.db.mongo.schemas import (
    CropCaseDocument,
    CropCaseFeedbackDoc,
    CropCaseStatusEnum,
    FeedbackTypeEnum,
)
from app.db.service_bridge import get_mongo_registry, is_mongodb_backend
from app.integrations.ai.crop_analysis import (
    CropAnalysisRequest,
    ReviewedKnowledgeCropAnalysisAdapter,
)
from app.integrations.storage import get_optimized_image_url, upload_image_to_storage
from app.modules.crop_assistant.models import CropCase, CropCaseFeedback
from app.modules.crop_assistant.schemas import CropFeedbackCreateRequest
from app.modules.users.models import User

# Local storage path for sanitized images
STORAGE_DIR = Path("storage/crop_images")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

ai_provider = ReviewedKnowledgeCropAnalysisAdapter()


async def create_crop_case(
    db: AsyncSession,
    user: Any,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    crop_type: str,
    symptoms: Optional[str] = None,
) -> Any:
    """Sanitizes image, executes reviewed AI analysis, and saves case."""
    # 1. Sanitize image, check magic bytes, strip EXIF, and re-encode to safe WebP
    sanitized_bytes, safe_filename, _, _ = sanitize_and_reencode_image(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
    )

    # 2. Upload directly to Cloudinary centralized storage
    uploaded_url = await upload_image_to_storage(
        file_bytes=sanitized_bytes,
        filename=safe_filename,
        folder="crops",
    )
    stored_image_ref = uploaded_url if uploaded_url.startswith("http") else safe_filename

    # 3. Analyze symptoms and derivative with AI provider
    analysis_req = CropAnalysisRequest(
        crop_type=crop_type,
        symptoms=symptoms,
        image_bytes=sanitized_bytes,
        filename=safe_filename,
    )
    result = await ai_provider.analyze(analysis_req)

    if is_mongodb_backend():
        reg = get_mongo_registry()
        status_val = (
            result.status.value
            if hasattr(result.status, "value")
            else str(result.status)
        )
        case_doc = CropCaseDocument(
            user_id=user.id,
            crop_type=crop_type,
            symptoms_description=symptoms,
            image_url=stored_image_ref,
            status=CropCaseStatusEnum(status_val),
            possible_condition=result.possible_condition,
            confidence=result.confidence,
            confidence_band=result.confidence_band,
            reason_summary=result.reason_summary or [],
            guidance=result.guidance or [],
            escalation_recommended=result.escalation_recommended,
            model_version=result.model_version,
            disclaimer=result.disclaimer,
        )
        return reg.crop_cases.insert_one(case_doc)

    # 5. Persist Crop Case with audit details
    crop_case = CropCase(
        user_id=user.id,
        crop_type=crop_type,
        symptoms_description=symptoms,
        image_filename=stored_image_ref,
        status=result.status,
        possible_condition=result.possible_condition,
        confidence=result.confidence,
        confidence_band=result.confidence_band,
        reason_summary=result.reason_summary,
        guidance=result.guidance,
        escalation_recommended=result.escalation_recommended,
        model_version=result.model_version,
        disclaimer=result.disclaimer,
    )
    db.add(crop_case)
    await db.commit()
    await db.refresh(crop_case)

    return crop_case


async def list_user_crop_cases(
    db: AsyncSession,
    user: Any,
    limit: int = 20,
    offset: int = 0,
) -> List[Any]:
    """Retrieves crop cases strictly owned by the authenticated user."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        return reg.crop_cases.get_by_user(user.id, skip=offset, limit=limit)

    stmt = (
        select(CropCase)
        .where(CropCase.user_id == user.id)
        .order_by(CropCase.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_crop_case(
    db: AsyncSession,
    user: Any,
    case_id: str,
) -> Any:
    """Fetches a specific crop case, enforcing strict object-level ownership."""
    if is_mongodb_backend():
        reg = get_mongo_registry()
        crop_case = reg.crop_cases.find_by_id(case_id)
        if not crop_case:
            raise NotFoundException(
                code="CROP_CASE_NOT_FOUND",
                message="The requested crop case does not exist.",
            )
        user_role_str = (
            user.role.value
            if hasattr(user.role, "value")
            else str(user.role)
        )
        if crop_case.user_id != user.id and user_role_str not in ("admin", "moderator"):
            raise ForbiddenException(
                code="FORBIDDEN_CROP_CASE_ACCESS",
                message="You do not have permission to view this crop case.",
            )
        return crop_case

    crop_case = await db.get(CropCase, case_id)
    if not crop_case:
        raise NotFoundException(
            code="CROP_CASE_NOT_FOUND",
            message="The requested crop case does not exist.",
        )

    # Rule 12: Farmers access only their private crop cases
    if crop_case.user_id != user.id and user.role.value not in ("admin", "moderator"):
        raise ForbiddenException(
            code="FORBIDDEN_CROP_CASE_ACCESS",
            message="You do not have permission to view this crop case.",
        )

    return crop_case


async def submit_case_feedback(
    db: AsyncSession,
    user: Any,
    case_id: str,
    req: CropFeedbackCreateRequest,
) -> Any:
    """Submits farmer feedback on AI accuracy and safety."""
    crop_case = await get_crop_case(db, user, case_id)

    if is_mongodb_backend():
        reg = get_mongo_registry()
        fb_type = (
            req.feedbackType.value
            if hasattr(req.feedbackType, "value")
            else str(req.feedbackType)
        )
        fb_doc = CropCaseFeedbackDoc(
            user_id=user.id,
            feedback_type=FeedbackTypeEnum(fb_type),
            comments=req.comments,
        )
        reg.crop_cases.add_feedback(crop_case.id, fb_doc)
        return CropCaseFeedback(
            id=fb_doc.id,
            crop_case_id=crop_case.id,
            user_id=user.id,
            feedback_type=req.feedbackType,
            comments=req.comments,
            created_at=fb_doc.created_at,
        )

    feedback = CropCaseFeedback(
        crop_case_id=crop_case.id,
        user_id=user.id,
        feedback_type=req.feedbackType,
        comments=req.comments,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return feedback
