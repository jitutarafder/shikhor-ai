"""Pydantic v2 schemas for Crop Assistant requests and structured responses."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.modules.crop_assistant.models import CropCaseStatus, FeedbackType


class CropCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    user_id: str = Field(serialization_alias="userId")
    crop_type: str = Field(serialization_alias="cropType")
    symptoms_description: Optional[str] = Field(None, serialization_alias="symptomsDescription")
    image_filename: str = Field(serialization_alias="imageFilename")

    # Structured AI response matching Architecture.md 7.3
    status: CropCaseStatus
    possible_condition: Optional[str] = Field(None, serialization_alias="possibleCondition")
    confidence: float
    confidence_band: str = Field(serialization_alias="confidenceBand")
    reason_summary: List[str] = Field(serialization_alias="reasonSummary")
    guidance: List[str]
    escalation_recommended: bool = Field(serialization_alias="escalationRecommended")
    model_version: str = Field(serialization_alias="modelVersion")
    disclaimer: str
    is_reviewed_by_expert: bool = Field(default=False, serialization_alias="isReviewedByExpert")
    created_at: datetime = Field(serialization_alias="createdAt")


class CropFeedbackCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    feedbackType: FeedbackType = Field(alias="feedback_type")
    comments: Optional[str] = Field(None, max_length=500)


class CropFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    crop_case_id: str = Field(serialization_alias="cropCaseId")
    feedback_type: FeedbackType = Field(serialization_alias="feedbackType")
    comments: Optional[str] = None
    created_at: datetime = Field(serialization_alias="createdAt")


class ExpertCaseReviewCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    reviewedDiagnosis: str = Field(..., alias="reviewed_diagnosis", min_length=2, max_length=150)
    prescribedTreatment: str = Field(..., alias="prescribed_treatment", min_length=10, max_length=2000)
    severityLevel: str = Field(default="moderate", alias="severity_level", max_length=50)
    expertNotes: Optional[str] = Field(None, alias="expert_notes", max_length=1000)


class ExpertCaseReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    crop_case_id: str = Field(serialization_alias="cropCaseId")
    expert_id: str = Field(serialization_alias="expertId")
    expert_name: str = Field(serialization_alias="expertName")
    reviewed_diagnosis: str = Field(serialization_alias="reviewedDiagnosis")
    prescribed_treatment: str = Field(serialization_alias="prescribedTreatment")
    severity_level: str = Field(serialization_alias="severityLevel")
    expert_notes: Optional[str] = Field(None, serialization_alias="expertNotes")
    created_at: datetime = Field(serialization_alias="createdAt")
class SymptomAnalysisRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    text: str = Field(..., min_length=1, max_length=1000, description="Symptoms in Bangla, Banglish, or English")
    cropType: Optional[str] = Field(None, alias="crop_type", max_length=50)


class SymptomAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    detectedCrop: Optional[str] = Field(None, serialization_alias="detectedCrop")
    detectedCropBn: Optional[str] = Field(None, serialization_alias="detectedCropBn")
    detectedIntent: str = Field(serialization_alias="detectedIntent")
    intentConfidence: float = Field(serialization_alias="intentConfidence")
    possibleConditionBn: Optional[str] = Field(None, serialization_alias="possibleConditionBn")
    confidence: float
    confidenceBand: str = Field(serialization_alias="confidenceBand")
    matchedSymptomsBn: List[str] = Field(default_factory=list, serialization_alias="matchedSymptomsBn")
    matchedTokens: List[str] = Field(default_factory=list, serialization_alias="matchedTokens")
    reasonSummary: List[str] = Field(default_factory=list, serialization_alias="reasonSummary")
    guidance: List[str] = Field(default_factory=list)
    escalationRecommended: bool = Field(serialization_alias="escalationRecommended")
    disclaimer: str
