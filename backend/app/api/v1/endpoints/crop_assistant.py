"""API endpoints for Crop Assistant diagnosis, history, and feedback."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.modules.crop_assistant.schemas import (
    CropCaseResponse,
    CropFeedbackCreateRequest,
    CropFeedbackResponse,
)
from app.modules.crop_assistant.service import (
    create_crop_case,
    get_crop_case,
    list_user_crop_cases,
    submit_case_feedback,
)
from app.modules.users.models import User

router = APIRouter(prefix="/crop-cases", tags=["crop-assistant"])


@router.post("", response_model=CropCaseResponse, status_code=status.HTTP_201_CREATED)
async def submit_crop_case(
    image: UploadFile = File(..., description="Crop leaf photo in JPEG, PNG, or WebP format"),
    crop_type: str = Form(..., description="Target crop (e.g., ধান, আলু, গম)"),
    symptoms: Optional[str] = Form(None, description="Observed symptoms in Bangla or English"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CropCaseResponse:
    """Uploads crop image, sanitizes derivative, runs AI guidance model, and records case."""
    file_bytes = await image.read()
    crop_case = await create_crop_case(
        db=db,
        user=current_user,
        file_bytes=file_bytes,
        filename=image.filename or "leaf.jpg",
        content_type=image.content_type or "image/jpeg",
        crop_type=crop_type,
        symptoms=symptoms,
    )
    return crop_case


@router.get("", response_model=List[CropCaseResponse])
async def get_my_crop_cases(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[CropCaseResponse]:
    """Lists crop cases submitted by the authenticated user."""
    return await list_user_crop_cases(db=db, user=current_user, limit=limit, offset=offset)


@router.post("/predict-banglish", summary="Predict plant disease from Banglish symptom description using BanglishBERT V3")
async def predict_banglish_disease(
    symptoms: str = Form(..., min_length=1, max_length=1000, description="Farmer Banglish symptom description"),
) -> dict:
    """Predicts plant disease from Banglish textual symptoms using fine-tuned BanglishBERT V3 with temperature scaling."""
    from app.integrations.ai.banglishbert_v3 import banglishbert_predictor
    return banglishbert_predictor.predict(symptoms)


@router.post("/analyze-symptoms", summary="Analyze Bangla or Banglish symptoms with NLP intent classification")
async def analyze_symptoms_nlp(
    symptoms: str = Form(..., min_length=1, max_length=1000, description="Symptoms in Bangla or Banglish"),
    crop_type: Optional[str] = Form(None, description="Optional target crop"),
) -> dict:
    """Analyzes symptoms in Bangla or Banglish, detecting crop, intent, and matching certified guidance."""
    # 1. If Gemini API is configured, use Gemini with safety guardrails
    from app.integrations.ai.gemini_adapter import gemini_crop_advisor
    if gemini_crop_advisor.is_configured:
        gemini_result = await gemini_crop_advisor.analyze_symptoms_with_gemini(symptoms, crop_type)
        if gemini_result:
            return {
                "detectedCrop": gemini_result.get("detected_crop", crop_type),
                "detectedCropBn": gemini_result.get("detected_crop", crop_type),
                "detectedIntent": "DIAGNOSE_DISEASE",
                "intentConfidence": 0.90,
                "possibleConditionBn": gemini_result.get("possible_condition"),
                "confidence": gemini_result.get("confidence", 0.85),
                "confidenceBand": gemini_result.get("confidence_band", "high"),
                "matchedSymptomsBn": [],
                "matchedTokens": [],
                "reasonSummary": gemini_result.get("reason_summary", []),
                "guidance": gemini_result.get("guidance", []),
                "adviceSummaryBn": gemini_result.get("advice_summary_bn", ""),
                "escalationRecommended": gemini_result.get("escalation_recommended", False),
                "disclaimer": gemini_result.get("disclaimer", ""),
                "source": "gemini",
            }

    # 2. Otherwise, use deterministic Bangla/Banglish NLP & BanglishBERT V3 engine
    from app.modules.crop_assistant.nlp_intent import nlp_engine
    result = nlp_engine.analyze_crop_symptoms(symptoms_text=symptoms, user_crop=crop_type)
    return {
        "detectedCrop": result.detected_crop,
        "detectedCropBn": result.detected_crop_bn,
        "detectedIntent": result.detected_intent,
        "intentConfidence": result.intent_confidence,
        "possibleConditionBn": result.possible_condition_bn,
        "confidence": result.confidence,
        "confidenceBand": result.confidence_band,
        "matchedSymptomsBn": result.matched_symptoms_bn,
        "matchedTokens": result.matched_tokens,
        "reasonSummary": result.reason_summary,
        "guidance": result.guidance,
        "escalationRecommended": result.escalation_recommended,
        "disclaimer": result.disclaimer,
        "source": "banglishbert_v3_hybrid",
    }


@router.get("/crops", summary="List supported field crops and vegetables")
@router.get("/taxonomy", summary="List supported crops and taxonomy")
async def get_supported_crops() -> dict:
    """Returns officially supported field crops and vegetables for AI disease analysis."""
    from app.modules.crop_assistant.knowledge_base import SUPPORTED_CROPS
    return {"crops": SUPPORTED_CROPS}


@router.get("/{case_id}", response_model=CropCaseResponse)
async def get_crop_case_details(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CropCaseResponse:
    """Retrieves single crop case, verifying object-level ownership."""
    return await get_crop_case(db=db, user=current_user, case_id=case_id)


@router.post("/{case_id}/feedback", response_model=CropFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def give_case_feedback(
    case_id: str,
    req: CropFeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CropFeedbackResponse:
    """Submits farmer evaluation on AI diagnosis accuracy and safety."""
    return await submit_case_feedback(db=db, user=current_user, case_id=case_id, req=req)


@router.get("/{case_id}/image", summary="Get crop leaf photo derivative (Authorized only)")
async def get_crop_case_image(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Securely streams sanitized crop leaf derivative with object-level authorization."""
    from pathlib import Path
    from fastapi.responses import FileResponse
    from app.core.errors import ForbiddenException, NotFoundException
    from app.modules.crop_assistant.models import CropCase
    from app.modules.users.models import UserRole

    crop_case = await db.get(CropCase, case_id)
    if not crop_case:
        raise NotFoundException("Crop case not found", "ফসলের রোগ কেসটি পাওয়া যায়নি।")

    # Authorization: Case owner or Expert/Admin/Moderator (AGENTS.md Rule 12)
    is_owner = crop_case.user_id == current_user.id
    is_authorized_staff = current_user.role in [UserRole.EXPERT, UserRole.ADMIN, UserRole.MODERATOR]
    if not (is_owner or is_authorized_staff):
        raise ForbiddenException("Access denied", "এই ফসলের ছবি দেখার অনুমতি আপনার নেই।")

    # If image is stored in Cloudinary, return fast optimized redirect (f_auto, q_auto, w_800)
    if crop_case.image_filename.startswith("http://") or crop_case.image_filename.startswith("https://"):
        from fastapi.responses import RedirectResponse
        from app.integrations.storage import get_optimized_image_url
        optimized_url = get_optimized_image_url(crop_case.image_filename, width=800)
        return RedirectResponse(url=optimized_url, status_code=307)

    storage_dir = Path("storage/crop_images")
    file_path = storage_dir / crop_case.image_filename
    if file_path.exists() and file_path.is_file():
        media_type = "image/webp" if file_path.suffix.lower() == ".webp" else "image/jpeg"
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            headers={
                "Content-Disposition": "inline",
                "X-Content-Type-Options": "nosniff",
            },
        )

    # Check for crop-specific fallback in storage
    if crop_case.crop_type == "আলু" and (storage_dir / "demo_potato_leaf.jpg").exists():
        fallback_file = storage_dir / "demo_potato_leaf.jpg"
    elif crop_case.crop_type == "টমেটো" and (storage_dir / "demo_tomato_leaf.jpg").exists():
        fallback_file = storage_dir / "demo_tomato_leaf.jpg"
    elif (storage_dir / "demo_rice_leaf.jpg").exists():
        fallback_file = storage_dir / "demo_rice_leaf.jpg"
    else:
        raise NotFoundException("Image not found", "ছবিটি স্টোরেজে খুঁজে পাওয়া যায়নি।")

    return FileResponse(
        path=str(fallback_file),
        media_type="image/jpeg",
        headers={"Content-Disposition": "inline", "X-Content-Type-Options": "nosniff"},
    )


@router.post("/{case_id}/send-to-expert", response_model=CropCaseResponse, summary="Send crop case and photos to agricultural expert for diagnosis")
async def send_case_to_expert(
    case_id: str,
    notes: Optional[str] = Form(None, description="Farmer questions or additional symptom observations"),
    additional_image: Optional[UploadFile] = File(None, description="Optional extra crop photo"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> CropCaseResponse:
    """Escalates a crop case with optional extra photo and questions to the agricultural expert review queue."""
    from pathlib import Path
    from app.common.image_safety import sanitize_and_reencode_image
    from app.core.errors import ForbiddenException, NotFoundException
    from app.modules.crop_assistant.models import CropCase

    crop_case = await db.get(CropCase, case_id)
    if not crop_case:
        raise NotFoundException("Crop case not found", "ফসলের রোগ কেসটি পাওয়া যায়নি।")

    # Authorize: Only the owner farmer can send their case to the expert (AGENTS.md Rule 12)
    if crop_case.user_id != current_user.id:
        raise ForbiddenException("Access denied", "শুধুমাত্র কেসটির মালিক এই অনুরোধ করতে পারেন।")

    # If additional image is uploaded, sanitize and store directly in Cloudinary
    if additional_image and additional_image.filename:
        file_bytes = await additional_image.read()
        if len(file_bytes) > 0:
            sanitized_bytes, safe_filename, _, _ = sanitize_and_reencode_image(
                file_bytes=file_bytes,
                filename=additional_image.filename,
                content_type=additional_image.content_type or "image/jpeg",
            )
            from app.integrations.storage import upload_image_to_storage
            uploaded_url = await upload_image_to_storage(
                file_bytes=sanitized_bytes,
                filename=safe_filename,
                folder="crops",
            )
            # Update image_filename to Cloudinary secure_url for expert inspection
            crop_case.image_filename = uploaded_url

    # Update escalation flag so it appears immediately in expert queue
    crop_case.escalation_recommended = True

    # Append notes to symptoms description
    if notes and notes.strip():
        existing_desc = crop_case.symptoms_description or ""
        note_text = f"[কৃষকের প্রশ্ন/বার্তা]: {notes.strip()}"
        if note_text not in existing_desc:
            crop_case.symptoms_description = f"{existing_desc}\n{note_text}".strip()

    # Reset expert reviewed status if resubmitting with new photo
    crop_case.is_reviewed_by_expert = False

    await db.commit()
    await db.refresh(crop_case)
    return CropCaseResponse.model_validate(crop_case)


