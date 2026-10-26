"""Database models for Crop Assistant cases, AI predictions, and user feedback."""

import enum
import uuid
from typing import Optional
from sqlalchemy import Boolean, Enum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class CropCaseStatus(str, enum.Enum):
    POSSIBLE_MATCH = "possible_match"
    UNCERTAIN = "uncertain"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class FeedbackType(str, enum.Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    UNSAFE = "unsafe"


class CropCase(Base, TimestampMixin):
    """Represents a crop health inquiry submitted by a farmer."""
    __tablename__ = "crop_cases"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    crop_type: Mapped[str] = mapped_column(String(50), nullable=False)
    symptoms_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_filename: Mapped[str] = mapped_column(String(100), nullable=False)

    # Structured AI Results (per Architecture.md 7.3 and AGENTS.md 19)
    status: Mapped[CropCaseStatus] = mapped_column(
        Enum(CropCaseStatus, name="crop_case_status_enum", native_enum=False),
        default=CropCaseStatus.POSSIBLE_MATCH,
        nullable=False,
    )
    possible_condition: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence_band: Mapped[str] = mapped_column(String(20), default="low", nullable=False)
    reason_summary: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    guidance: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    escalation_recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0.0-reviewed", nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    is_reviewed_by_expert: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Feedback relationship
    feedbacks: Mapped[list["CropCaseFeedback"]] = relationship(
        "CropCaseFeedback", back_populates="crop_case", cascade="all, delete-orphan"
    )
    expert_reviews: Mapped[list["ExpertCaseReview"]] = relationship(
        "ExpertCaseReview", back_populates="crop_case", cascade="all, delete-orphan"
    )


class CropCaseFeedback(Base, TimestampMixin):
    """User evaluation on crop diagnosis accuracy and safety."""
    __tablename__ = "crop_case_feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    crop_case_id: Mapped[str] = mapped_column(ForeignKey("crop_cases.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    feedback_type: Mapped[FeedbackType] = mapped_column(
        Enum(FeedbackType, name="feedback_type_enum", native_enum=False),
        nullable=False,
    )
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    crop_case: Mapped[CropCase] = relationship("CropCase", back_populates="feedbacks")


class ExpertCaseReview(Base, TimestampMixin):
    """Agricultural expert's reviewed evaluation and prescription for a crop case."""
    __tablename__ = "expert_case_reviews"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    crop_case_id: Mapped[str] = mapped_column(
        ForeignKey("crop_cases.id", ondelete="CASCADE"), index=True, nullable=False
    )
    expert_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    expert_name: Mapped[str] = mapped_column(String(100), nullable=False)
    reviewed_diagnosis: Mapped[str] = mapped_column(String(150), nullable=False)
    prescribed_treatment: Mapped[str] = mapped_column(Text, nullable=False)
    severity_level: Mapped[str] = mapped_column(String(50), default="moderate", nullable=False)
    expert_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    crop_case: Mapped["CropCase"] = relationship("CropCase", back_populates="expert_reviews")
    expert = relationship("User", foreign_keys=[expert_id], lazy="joined")

