"""Equipment domain database models."""

import enum
import uuid
from typing import Optional
from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class EquipmentType(str, enum.Enum):
    TRACTOR = "tractor"
    HARVESTER = "harvester"
    PUMP = "pump"
    SPRAYER = "sprayer"
    POWER_TILLER = "power_tiller"
    OTHER = "other"


class PriceUnit(str, enum.Enum):
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_ACRE = "per_acre"


class Equipment(Base, TimestampMixin):
    """Agricultural machinery listing owned by an equipment owner."""
    __tablename__ = "equipment"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    equipment_type: Mapped[EquipmentType] = mapped_column(
        Enum(EquipmentType, name="equipment_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Exact money & unit (Rule 16: store monetary value, currency, price unit)
    price_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # In BDT
    price_unit: Mapped[PriceUnit] = mapped_column(
        Enum(PriceUnit, name="price_unit_enum", native_enum=False),
        nullable=False,
        index=True,
    )

    # Geospatial location reference (Rule 17)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    upazila: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    service_radius_km: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)

    # Availability & State
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id], lazy="joined")
    rental_requests: Mapped[list["RentalRequest"]] = relationship(
        "RentalRequest", back_populates="equipment", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["EquipmentReview"]] = relationship(
        "EquipmentReview", back_populates="equipment", cascade="all, delete-orphan", lazy="selectin"
    )


class EquipmentReview(Base, TimestampMixin):
    """Post-completion ratings and feedback strictly validated by server (Security.md & Rule 11)."""
    __tablename__ = "equipment_reviews"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    equipment_id: Mapped[str] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"), index=True, nullable=False)
    renter_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    rental_request_id: Mapped[str] = mapped_column(ForeignKey("rental_requests.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 to 5 stars
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    equipment: Mapped["Equipment"] = relationship("Equipment", back_populates="reviews")
    renter: Mapped["User"] = relationship("User", foreign_keys=[renter_id], lazy="joined")
    rental_request: Mapped["RentalRequest"] = relationship("RentalRequest", foreign_keys=[rental_request_id])


from app.modules.rentals.models import RentalRequest  # noqa: E402
from app.modules.users.models import User  # noqa: E402
