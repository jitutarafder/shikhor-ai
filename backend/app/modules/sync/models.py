"""Idempotency and Synchronization database models.

Strictly complies with:
- AGENTS.md Rule 21: Offline synchronization must be idempotent.
- AGENTS.md Rule 21: Bind idempotency records to user, operation, and request-body hash.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IdempotencyRecord(Base):
    """Stores executed mutation idempotency records to prevent duplicate deliveries."""

    __tablename__ = "idempotency_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    operation: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    request_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="SHA-256 hash of payload"
    )
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_body: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "operation", "idempotency_key", name="uq_user_op_idempotency_key"),
    )
