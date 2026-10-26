"""Audit Log and Admin Management database models.

Strictly complies with:
- AGENTS.md Rule 26: Error, logging, and audit rules.
- AGENTS.md Rule 26: Audit entries include actor, action, resource, timestamp, and request ID.
- AGENTS.md Rule 26: Redact PII and secrets in audit logs.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditLog(Base):
    """Tracks administrative and moderation actions with full accountability (Rule 26)."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    actor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="e.g. RESOLVE_REPORT, SUSPEND_USER"
    )
    resource_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="e.g. user, report, crop_listing, knowledge"
    )
    resource_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=False, comment="Redacted structured metadata")
    request_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )

    actor = relationship("User", foreign_keys=[actor_id], lazy="joined")
