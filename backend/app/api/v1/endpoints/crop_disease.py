"""Crop Disease Image Prediction & Multimodal AI Reasoning Endpoints.

Implements full three-source AI reasoning architecture:
1. Crop-Aware Vision Models: BASE BCDD MobileNetV2 + SECONDARY Plant Disease MobileNetV2
2. BanglishBERT V3: Executed ONLY when farmer provides symptom text
3. Gemini Multimodal AI: Fusion layer producing ONE unified diagnosis
- Mandatory Crop Selection (Enforced before inference)
- OOD / Non-Plant Image Guardrail
- Deterministic Local Fusion Fallback on Gemini 429/quota/offline
"""

import io
import logging
from typing import Optional
from fastapi import APIRouter, File, Form, UploadFile, status
from PIL import Image

from app.core.errors import ValidationException
from app.modules.crop_assistant.knowledge_base import (
    DISCLAIMER_TEXT,
    get_crop_disease_knowledge,
)
from app.integrations.ai.vision_models import (
    CROP_LABELS_BN,
    CROP_LOOKUP_TO_CANONICAL,
    check_is_plant_or_leaf,
    predict_crop_disease,
)
from app.integrations.ai.banglishbert_v3 import banglishbert_predictor
from app.integrations.ai.gemini_adapter import gemini_crop_advisor

logger = logging.getLogger("shikhor.ai.crop_disease")

router = APIRouter(tags=["crop-disease-vision"])


@router.post(
    "/crop-disease/predict",
    summary="Predict plant disease from leaf image using Crop-Aware Vision + Banglish + Gemini Multimodal Reasoning",
    status_code=status.HTTP_200_OK,
)
async def predict_crop_disease_endpoint(
    file: Optional[UploadFile] = File(None, description="Uploaded crop leaf image file"),
    image: Optional[UploadFile] = File(None, description="Alternative field name for uploaded leaf image"),
    crop: Optional[str] = Form(None, description="Selected crop in English or Bangla (MANDATORY)"),
    crop_type: Optional[str] = Form(None, description="Alias for crop field"),
    symptoms: Optional[str] = Form(None, description="Optional Banglish/Bangla symptom description"),
    description: Optional[str] = Form(None, description="Alias for symptoms field"),
    threshold: Optional[float] = Form(None, description="Optional custom base confidence routing threshold (default 0.70)"),
) -> dict:
    """Classifies plant leaf disease with mandatory crop selection and three-source multimodal reasoning.

    Execution Flow:
    1. Mandatory Crop Selection validation.
    2. Uploaded image validation (JPEG, PNG, WebP).
    3. [Step 1] OOD / Foliage Guardrail (rejects non-plant/road/vehicle images).
    4. [Step 2] Crop-Aware Vision Classifier (BASE + SECONDARY fallback).
    5. [Step 3] BanglishBERT V3 NLP model (ONLY if symptom text is provided).
    6. [Step 4] Gemini Multimodal Fusion Layer (if available).
    7. [Step 5] Local Deterministic Fusion (if Gemini unavailable or quota exceeded).
    8. Produces ONE final disease decision for the farmer.
    """
    # -----------------------------------------------------------------------
    # 1. Mandatory Crop Selection Validation
    # -----------------------------------------------------------------------
    raw_crop = crop or crop_type
    if not raw_crop or not raw_crop.strip():
        logger.warning("[CropDisease] Prediction rejected: No crop selected.")
        raise ValidationException(
            code="CROP_REQUIRED",
            message="অনুগ্রহ করে আগে ফসল নির্বাচন করুন।",
        )

    clean_crop = raw_crop.strip()
    canonical_crop = CROP_LOOKUP_TO_CANONICAL.get(clean_crop) or CROP_LOOKUP_TO_CANONICAL.get(clean_crop.title())
    if not canonical_crop and clean_crop in CROP_LABELS_BN:
        canonical_crop = clean_crop

    if not canonical_crop or canonical_crop not in CROP_LABELS_BN:
        logger.warning(f"[CropDisease] Prediction rejected: Invalid crop '{clean_crop}'.")
        raise ValidationException(
            code="INVALID_CROP",
            message="অনুগ্রহ করে সমর্থিত ১৬টি ফসলের যেকোনো একটি নির্বাচন করুন।",
        )

    selected_crop_bn = CROP_LABELS_BN[canonical_crop]
    logger.info(f"[CropDisease] Mandatory crop validated: {canonical_crop} ({selected_crop_bn})")

    # -----------------------------------------------------------------------
    # 2. Image Validation & Decoding
    # -----------------------------------------------------------------------
    upload_target = file or image
    if not upload_target:
        raise ValidationException(
            code="IMAGE_REQUIRED",
            message="অনুগ্রহ করে ফসলের আক্রান্ত পাতার ছবি আপলোড করুন।",
        )

    file_bytes = await upload_target.read()
    if len(file_bytes) == 0:
        raise ValidationException(
            code="EMPTY_IMAGE",
            message="আপলোডকৃত ফাইলটি খালি।",
        )

    try:
        pil_img = Image.open(io.BytesIO(file_bytes))
        pil_img.verify()
        pil_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception:
        raise ValidationException(
            code="INVALID_IMAGE_FORMAT",
            message="সঠিক ফরম্যাটের ছবি (JPEG, PNG বা WebP) আপলোড করুন।",
        )

    # -----------------------------------------------------------------------
    # 3. [Step 1] OOD / Foliage Guardrail Check
    # -----------------------------------------------------------------------
    logger.info("[CropDisease] OOD/Foliage check started")
    is_plant, veg_ratio = check_is_plant_or_leaf(pil_img)

    if not is_plant:
        logger.warning(f"[CropDisease] Plant detected: False. Rejecting image (foliage ratio: {veg_ratio:.3f})")
        return {
            "success": False,
            "reason": "no_plant_detected",
            "is_plant_leaf": False,
            "selected_crop": canonical_crop,
            "selected_crop_bn": selected_crop_bn,
            "crop": canonical_crop,
            "crop_bn": selected_crop_bn,
            "disease": "গাছ বা পাতার ছবি নয়",
            "disease_bn": "গাছ বা পাতার ছবি নয়",
            "confidence": 0.0,
            "sources_used": ["ood_guardrail"],
            "vision_result": None,
            "banglish_result": None,
            "gemini_result": None,
            "gemini_available": False,
            "banglish_used": False,
            "top_predictions": [],
            "guidance": [
                "আক্রান্ত ফসল বা গাছের পাতার একটি পরিষ্কার ও সরাসরি ছবি আপলোড করুন।",
                "রাস্তাঘাট, যানবাহন বা অন্য কোনো অপ্রাসঙ্গিক বস্তুর ছবি রোগ নির্ণয়ে প্রযোজ্য নয়।",
            ],
            "reason_summary": [
                "ছবিটিতে ফসল বা পাতার কোনো স্বাভাবিক জৈব বৈশিষ্ট্য পরিলক্ষিত হয়নি।"
            ],
            "escalation_recommended": False,
            "disclaimer": DISCLAIMER_TEXT,
        }

    logger.info(f"[CropDisease] Plant detected: True (ratio: {veg_ratio:.4f}).")

    # -----------------------------------------------------------------------
    # 4. [Step 2] Crop-Aware Vision Prediction
    # -----------------------------------------------------------------------
    logger.info(f"[CropDisease] Running Crop-Aware Vision for {canonical_crop}...")
    vision_res = predict_crop_disease(image=pil_img, crop=canonical_crop, threshold=threshold)
    logger.info(
        f"[CropDisease] Vision result: {vision_res['disease_bn']} "
        f"({vision_res['disease']}) - Conf: {vision_res['confidence']:.4f}"
    )

    # -----------------------------------------------------------------------
    # 5. [Step 3] Banglish Model (ONLY if symptom text exists)
    # -----------------------------------------------------------------------
    symptoms_text = (symptoms or description or "").strip()
    banglish_res = None
    banglish_used = False

    if symptoms_text:
        logger.info(f"[CropDisease] Symptom text provided ('{symptoms_text[:40]}...'). Running BanglishBERT V3...")
        banglish_res = banglishbert_predictor.predict(symptoms_text)
        banglish_used = True
        logger.info(
            f"[CropDisease] BanglishBERT result: {banglish_res.get('disease_bn')} "
            f"({banglish_res.get('disease')}) - Conf: {banglish_res.get('confidence', 0.0):.4f}"
        )
    else:
        logger.info("[CropDisease] No symptom text provided. BanglishBERT model skipped as per specification.")

    # -----------------------------------------------------------------------
    # 6. [Step 4] Gemini Multimodal Fusion Layer
    # -----------------------------------------------------------------------
    gemini_res = None
    gemini_available = False
    sources_used = ["vision"]
    if banglish_used:
        sources_used.append("banglish")

    if gemini_crop_advisor.is_configured:
        try:
            logger.info("[CropDisease] Invoking Gemini Multimodal Fusion reasoning layer...")
            gemini_res = await gemini_crop_advisor.fuse_multimodal_crop_diagnosis(
                image_bytes=file_bytes,
                selected_crop=canonical_crop,
                selected_crop_bn=selected_crop_bn,
                vision_result=vision_res,
                banglish_result=banglish_res,
                symptoms_text=symptoms_text if banglish_used else None,
                mime_type=upload_target.content_type or "image/jpeg",
            )
            if gemini_res:
                if (
                    gemini_res.get("is_plant_leaf") is False
                    or gemini_res.get("disease") == "গাছ বা পাতার ছবি নয়"
                    or "গাছ বা পাতার ছবি নয়" in str(gemini_res.get("disease_bn", ""))
                    or gemini_res.get("confidence", 1.0) == 0.0
                ):
                    logger.warning(f"[CropDisease] Gemini detected non-plant/non-leaf image: {gemini_res.get('reason_summary')}. Rejecting image.")
                    return {
                        "success": False,
                        "reason": "no_plant_detected",
                        "is_plant_leaf": False,
                        "selected_crop": canonical_crop,
                        "selected_crop_bn": selected_crop_bn,
                        "crop": canonical_crop,
                        "crop_bn": selected_crop_bn,
                        "disease": "গাছ বা পাতার ছবি নয়",
                        "disease_bn": "গাছ বা পাতার ছবি নয়",
                        "confidence": 0.0,
                        "sources_used": ["gemini_guardrail"],
                        "vision_result": vision_res,
                        "banglish_result": banglish_res,
                        "gemini_result": gemini_res,
                        "gemini_available": True,
                        "banglish_used": banglish_used,
                        "top_predictions": [],
                        "guidance": [
                            "আক্রান্ত ফসল বা গাছের পাতার একটি পরিষ্কার ও সরাসরি ছবি আপলোড করুন।",
                            "প্রাণী, মানুষ, ফুলদানি বা অপ্রাসঙ্গিক কোনো বস্তুর ছবি রোগ নির্ণয়ে প্রযোজ্য নয়।",
                        ],
                        "reason_summary": gemini_res.get("reason_summary", [
                            "ছবিটিতে ফসল বা পাতার কোনো স্বাভাবিক জৈব বৈশিষ্ট্য পরিলক্ষিত হয়নি।"
                        ]),
                        "escalation_recommended": False,
                        "disclaimer": DISCLAIMER_TEXT,
                    }
                elif gemini_res.get("disease"):
                    gemini_available = True
                    sources_used.append("gemini")
                    logger.info(f"[CropDisease] Gemini Multimodal Fusion succeeded: {gemini_res['disease_bn']}")
                else:
                    logger.warning("[CropDisease] Gemini returned empty/unparsed output. Falling back to local fusion.")
            else:
                logger.warning("[CropDisease] Gemini returned empty output. Falling back to local fusion.")
        except Exception as exc:
            logger.warning(f"[CropDisease] Gemini API error or quota limit: {exc}. Falling back to local fusion.")

    # -----------------------------------------------------------------------
    # 7. [Step 5] Final Decision Consensus (ONE Final Diagnosis)
    # -----------------------------------------------------------------------
    if gemini_available and gemini_res:
        final_decision = {
            "crop": canonical_crop,
            "crop_bn": selected_crop_bn,
            "disease": gemini_res.get("disease", vision_res["disease"]),
            "disease_bn": gemini_res.get("disease_bn", vision_res["disease_bn"]),
            "confidence": gemini_res.get("confidence", vision_res["confidence"]),
            "uncertain": gemini_res.get("uncertain", False),
            "guidance": gemini_res.get("guidance", vision_res["guidance"]),
            "reason_summary": gemini_res.get("reason_summary", vision_res["reason_summary"]),
            "decision_source": gemini_res.get("decision_source", "gemini_multimodal_fusion"),
        }
    else:
        # Local Deterministic Fusion
        if not banglish_used or not banglish_res:
            final_decision = {
                "crop": canonical_crop,
                "crop_bn": selected_crop_bn,
                "disease": vision_res["disease"],
                "disease_bn": vision_res["disease_bn"],
                "confidence": vision_res["confidence"],
                "uncertain": vision_res["confidence"] < 0.60,
                "guidance": vision_res["guidance"],
                "reason_summary": vision_res["reason_summary"],
                "decision_source": "vision_only_local",
            }
        else:
            # Consensus check between Vision and Banglish
            v_dis = (vision_res["disease"] or "").lower()
            b_dis = (banglish_res.get("disease") or "").lower()
            v_dis_bn = vision_res["disease_bn"]
            b_dis_bn = banglish_res.get("disease_bn", "")

            is_agreement = (
                (b_dis and b_dis in v_dis) or
                (v_dis and v_dis in b_dis) or
                (b_dis_bn and b_dis_bn in v_dis_bn)
            )

            if is_agreement:
                logger.info(f"[CropDisease] Vision and Banglish agree on condition: {vision_res['disease_bn']}")
                final_decision = {
                    "crop": canonical_crop,
                    "crop_bn": selected_crop_bn,
                    "disease": vision_res["disease"],
                    "disease_bn": vision_res["disease_bn"],
                    "confidence": max(vision_res["confidence"], banglish_res.get("confidence", 0.0)),
                    "uncertain": False,
                    "guidance": vision_res["guidance"],
                    "reason_summary": vision_res["reason_summary"] + (banglish_res.get("reason_summary", [])),
                    "decision_source": "vision_banglish_consensus",
                }
            else:
                logger.info(
                    f"[CropDisease] Vision ({vision_res['disease_bn']}) and Banglish ({banglish_res.get('disease_bn')}) "
                    "conflict. Prioritizing visual evidence with uncertainty flag."
                )
                final_decision = {
                    "crop": canonical_crop,
                    "crop_bn": selected_crop_bn,
                    "disease": vision_res["disease"],
                    "disease_bn": vision_res["disease_bn"],
                    "confidence": vision_res["confidence"],
                    "uncertain": True,
                    "fusion_status": "conflicting_evidence",
                    "guidance": vision_res["guidance"],
                    "reason_summary": [
                        f"দৃষ্টিগত মডেলে {vision_res['disease_bn']} নির্দেশিত হয়েছে, তবে লিখিত লক্ষণের সাথে কিছু অমিল থাকায় সতর্কতা অবলম্বন করুন।"
                    ] + vision_res["reason_summary"],
                    "decision_source": "vision_preferred_with_conflict",
                }

    # Augment final decision with reviewed knowledge base advice
    final_cond_knowledge = get_crop_disease_knowledge(
        crop=final_decision["crop"],
        disease=final_decision["disease"],
    )
    final_decision["primary_solution"] = final_cond_knowledge.get("primary_solution") or vision_res.get("primary_solution", "")
    final_decision["guidance"] = final_cond_knowledge.get("guidance") or final_decision.get("guidance") or vision_res.get("guidance", [])
    final_decision["avoid"] = final_cond_knowledge.get("avoid") or vision_res.get("avoid")
    final_decision["prevention"] = final_cond_knowledge.get("prevention") or vision_res.get("prevention")
    final_decision["special_warning"] = final_cond_knowledge.get("special_warning") or vision_res.get("special_warning")
    final_decision["is_healthy"] = (
        final_cond_knowledge.get("is_healthy", False) or
        vision_res.get("is_healthy", False) or
        "healthy" in (final_decision["disease"] or "").lower()
    )

    logger.info(f"[CropDisease] FINAL DIAGNOSIS: {final_decision['crop_bn']} - {final_decision['disease_bn']} (Sources: {sources_used})")

    # -----------------------------------------------------------------------
    # 8. Clean Structured Output
    # -----------------------------------------------------------------------
    return {
        "success": True,
        "selected_crop": canonical_crop,
        "selected_crop_bn": selected_crop_bn,
        "final_decision": final_decision,
        "sources_used": sources_used,
        "vision_result": vision_res,
        "banglish_result": banglish_res,
        "gemini_result": gemini_res if gemini_available else None,
        "gemini_available": gemini_available,
        "banglish_used": banglish_used,
        "is_plant_leaf": True,
        # Preserve top-level fields for backwards compatibility
        "crop": final_decision["crop"],
        "crop_bn": final_decision["crop_bn"],
        "disease": final_decision["disease"],
        "disease_bn": final_decision["disease_bn"],
        "raw_class": vision_res.get("raw_class", "Processed"),
        "confidence": final_decision["confidence"],
        "uncertain": final_decision.get("uncertain", False),
        "model_used": vision_res.get("model_used", "hybrid"),
        "model_name": vision_res.get("model_name", "মাল্টি-মডেল এআই"),
        "top_predictions": vision_res.get("top_predictions", []),
        "primary_solution": final_decision["primary_solution"],
        "guidance": final_decision["guidance"],
        "avoid": final_decision.get("avoid"),
        "prevention": final_decision.get("prevention"),
        "special_warning": final_decision.get("special_warning"),
        "is_healthy": final_decision.get("is_healthy", False),
        "reason_summary": final_decision.get("reason_summary", vision_res.get("reason_summary", [])),
        "escalation_recommended": vision_res.get("escalation_recommended", False) or final_decision.get("uncertain", False),
        "disclaimer": DISCLAIMER_TEXT,
    }
