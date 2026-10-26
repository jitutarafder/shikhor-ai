"""Rental request domain database models."""

import enum
import uuid
from datetime import date
from typing import Optional
from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class RentalStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class RentalRequest(Base, TimestampMixin):
    """Rental request placed by a farmer to an equipment owner."""
    __tablename__ = "rental_requests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    equipment_id: Mapped[str] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"), index=True, nullable=False)
    renter_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    rental_date: Mapped[date] = mapped_column(Date, nullable=False)
    selected_dates: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # comma-separated ISO dates e.g. "2026-10-10,2026-10-11"
    duration_units: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_estimated_price: Mapped[int] = mapped_column(Integer, nullable=False)  # in BDT
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[RentalStatus] = mapped_column(
        Enum(RentalStatus, name="rental_status_enum", native_enum=False),
        default=RentalStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Idempotency key for offline queued commands (Rule 21)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    # Relationships
    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="rental_requests")


from app.modules.equipment.models import Equipment  # noqa: E402
