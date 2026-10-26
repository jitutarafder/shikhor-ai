"""Database models for Phase 9 Controlled Pilot telemetry and user feedback.

Strictly complies with:
- AGENTS.md Rule 11: Backend validation is always authoritative.
- AGENTS.md Rule 12: Object-level authorization and user binding.
- AGENTS.md Rule 26: Redact PII and sensitive data.
- AGENTS.md Rule 31: Real data only, no fake or mock statistics.
"""

from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PilotFeedback(Base):
    """Stores farmer and participant feedback during the controlled pilot."""

    __tablename__ = "pilot_feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="e.g. crop_diagnosis, equipment_rental, weather_plan, crop_marketplace, offline_sync, general_onboarding",
    )
    ease_of_use_rating: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1 (very difficult) to 5 (very easy)"
    )
    bangla_comprehension_rating: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1 (unclear) to 5 (crystal clear)"
    )
    ai_limitations_understood: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="User acknowledges AI is advisory and does not replace an agricultural officer",
    )
    device_category: Mapped[str] = mapped_column(
        String(50),
        default="low_end_android",
        nullable=False,
        comment="low_end_android, mid_android, feature_browser, desktop, other",
    )
    network_type: Mapped[str] = mapped_column(
        String(50),
        default="4g_wifi",
        nullable=False,
        comment="2g_slow, 3g, 4g_wifi, offline_intermittent",
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Client-reported operation latency in milliseconds"
    )
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    upazila: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user = relationship("User", foreign_keys=[user_id], lazy="joined")
