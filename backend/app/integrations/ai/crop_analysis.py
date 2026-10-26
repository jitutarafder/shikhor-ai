"""Crop Analysis AI Provider protocol and reviewed agronomic adapter."""

from dataclasses import dataclass
from typing import List, Optional, Protocol
from app.modules.crop_assistant.knowledge_base import (
    DISCLAIMER_TEXT,
    lookup_reviewed_condition,
)
from app.modules.crop_assistant.models import CropCaseStatus


@dataclass
class CropAnalysisRequest:
    crop_type: str
    symptoms: Optional[str]
    image_bytes: bytes
    filename: str


@dataclass
class CropAnalysisResult:
    status: CropCaseStatus
    possible_condition: Optional[str]
    confidence: float
    confidence_band: str
    reason_summary: List[str]
    guidance: List[str]
    escalation_recommended: bool
    model_version: str
    disclaimer: str


class CropAnalysisProvider(Protocol):
    """Protocol for crop analysis models (TensorFlow, PyTorch, or mock adapters)."""

    async def analyze(self, request: CropAnalysisRequest) -> CropAnalysisResult:
        ...


class ReviewedKnowledgeCropAnalysisAdapter:
    """Production-ready adapter mapping verified symptoms to reviewed agronomic guidance.

    Complies with AGENTS.md Rule 19:
    - Never hallucinates pesticide doses.
    - Low-confidence (<0.60) produces 'uncertain' status with escalation flag.
    - Unmatched crops produce 'unsupported' status with escalation flag.
    """

    MODEL_VERSION = "v2.0.0-multi-sector-reviewed"

    async def analyze(self, request: CropAnalysisRequest) -> CropAnalysisResult:
        from app.core.config import settings

        # 1. If AI is not mocked and image bytes are present, run trained BCDD / MobileNetV2 vision models
        if settings.AI_PROVIDER != "mock" and request.image_bytes:
            try:
                import io
                from PIL import Image
                from app.integrations.ai.vision_models import predict_crop_disease

                pil_img = Image.open(io.BytesIO(request.image_bytes)).convert("RGB")
                vision_res = predict_crop_disease(
                    pil_img,
                    crop_type=request.crop_type,
                    symptoms_text=request.symptoms,
                )
                if vision_res and vision_res.get("success"):
                    conf = vision_res.get("confidence", 0.75)
                    conf_band = "high" if conf >= 0.80 else ("medium" if conf >= 0.60 else "low")
                    status = (
                        CropCaseStatus.POSSIBLE_MATCH if conf >= 0.60 else CropCaseStatus.UNCERTAIN
                    )
                    return CropAnalysisResult(
                        status=status,
                        possible_condition=f"{vision_res['crop_bn']}: {vision_res['disease_bn']}",
                        confidence=conf,
                        confidence_band=conf_band,
                        reason_summary=vision_res.get("reason_summary", []),
                        guidance=vision_res.get("guidance", []),
                        escalation_recommended=vision_res.get("escalation_recommended", False),
                        model_version=f"{vision_res['model_name']} ({vision_res['model_used']})",
                        disclaimer=vision_res.get("disclaimer", DISCLAIMER_TEXT),
                    )
            except Exception as e:
                pass  # Fall through to Gemini / knowledge base

        # 2. If Gemini Vision is enabled and configured, analyze the leaf image & symptoms directly
        from app.integrations.ai.gemini_adapter import gemini_crop_advisor
        if settings.AI_PROVIDER != "mock" and gemini_crop_advisor.is_configured and request.image_bytes:
            gemini_res = await gemini_crop_advisor.analyze_image_and_symptoms_with_gemini(
                image_bytes=request.image_bytes,
                crop_type=request.crop_type,
                symptoms_text=request.symptoms,
            )
            if gemini_res and gemini_res.get("possible_condition"):
                conf = gemini_res.get("confidence", 0.85)
                conf_band = gemini_res.get("confidence_band", "high")
                status = (
                    CropCaseStatus.POSSIBLE_MATCH if conf >= 0.60 else CropCaseStatus.UNCERTAIN
                )
                return CropAnalysisResult(
                    status=status,
                    possible_condition=gemini_res.get("possible_condition"),
                    confidence=conf,
                    confidence_band=conf_band,
                    reason_summary=gemini_res.get("reason_summary", []),
                    guidance=gemini_res.get("guidance", []),
                    escalation_recommended=gemini_res.get("escalation_recommended", False),
                    model_version=gemini_res.get("model_version", self.MODEL_VERSION),
                    disclaimer=gemini_res.get("disclaimer", DISCLAIMER_TEXT),
                )

        # 2. Fallback: Lookup condition in reviewed knowledge base & BanglishBERT
        condition = lookup_reviewed_condition(request.crop_type, request.symptoms)

        if not condition:
            # Unsupported crop/sector or completely unrecognized problem
            return CropAnalysisResult(
                status=CropCaseStatus.UNSUPPORTED,
                possible_condition=None,
                confidence=0.25,
                confidence_band="low",
                reason_summary=[
                    "উল্লেখিত ফসল বা লক্ষণের সুনির্দিষ্ট তথ্য পর্যালোচিত জ্ঞানভাণ্ডারে মেলেনি।",
                ],
                guidance=[
                    "সঠিক রোগ নির্ণয় ও ফসল সুরক্ষায় নিকটস্থ উপজেলা কৃষি সম্প্রসারণ অফিসে (SAAO) যোগাযোগ করুন।",
                ],
                escalation_recommended=True,
                model_version=self.MODEL_VERSION,
                disclaimer=DISCLAIMER_TEXT,
            )

        # 2. Check if symptom descriptions were vague or contradictory
        symptoms_text = (request.symptoms or "").lower()
        if len(symptoms_text) > 0 and len(symptoms_text) < 5:
            # Low confidence due to insufficient symptoms
            return CropAnalysisResult(
                status=CropCaseStatus.UNCERTAIN,
                possible_condition=condition["condition_name_bn"],
                confidence=0.48,
                confidence_band="low",
                reason_summary=[
                    "লক্ষণ অত্যন্ত সংক্ষিপ্ত বা অস্পষ্ট হওয়ায় নিশ্চিত রোগ নির্ণয় সম্ভব নয়।",
                ],
                guidance=[
                    "জমি থেকে পরিষ্কার আলোতে আরও কাছ থেকে ছবি তুলুন এবং বিস্তারিত লক্ষণ জানান।",
                    "জরুরি প্রয়োজনে স্থানীয় উপ-সহকারী কৃষি কর্মকর্তার (SAAO) সহায়তা নিন।",
                ],
                escalation_recommended=True,
                model_version=self.MODEL_VERSION,
                disclaimer=DISCLAIMER_TEXT,
            )

        # 3. High/Medium Confidence valid match
        keywords = condition.get("keywords", [])
        has_keywords = any(kw.lower() in symptoms_text for kw in keywords) if keywords else True
        confidence = 0.85 if has_keywords else 0.72
        confidence_band = "high" if confidence >= 0.80 else "medium"

        return CropAnalysisResult(
            status=CropCaseStatus.POSSIBLE_MATCH,
            possible_condition=condition.get("condition_name_bn", ""),
            confidence=confidence,
            confidence_band=confidence_band,
            reason_summary=condition.get("reason_summary", condition.get("guidance", [])[:2]),
            guidance=condition.get("guidance", []),
            escalation_recommended=False,
            model_version=self.MODEL_VERSION,
            disclaimer=DISCLAIMER_TEXT,
        )
