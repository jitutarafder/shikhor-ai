"""Crop Marketplace database models and enums.

Strictly complies with:
- AGENTS.md Rule 14: Centralized status lifecycle (active, paused, closed).
- AGENTS.md Rule 16: Money, quantity, and units must be exact.
- AGENTS.md Rule 17: Approximate coordinate exposure for privacy.
"""

from datetime import date, datetime, timezone
from enum import Enum
import uuid
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CropCategory(str, Enum):
    PADDY = "paddy"          # ধান
    WHEAT = "wheat"          # গম
    MAIZE = "maize"          # ভুট্টা
    POTATO = "potato"        # আলু
    VEGETABLE = "vegetable"  # শাকসবজি
    PULSE = "pulse"          # ডাল
    OILSEED = "oilseed"      # সরিষা / তেলবীজ
    SPICE = "spice"          # পেঁয়াজ / মসলা
    FRUIT = "fruit"          # ফলমূল
    OTHER = "other"          # অন্যান্য


class QuantityUnit(str, Enum):
    MAUND = "maund"  # মন (৪০ কেজি)
    KG = "kg"        # কেজি
    TON = "ton"      # মেট্রিক টন


class CropListingStatus(str, Enum):
    ACTIVE = "active"    # বিক্রয়ের জন্য প্রস্তুত ও দৃশ্যমান
    PAUSED = "paused"    # সাময়িক স্থগিত
    CLOSED = "closed"    # বিক্রি সম্পন্ন / সমাপ্ত


class CropListing(Base):
    __tablename__ = "crop_listings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    farmer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crop_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[CropCategory] = mapped_column(String(50), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_unit: Mapped[QuantityUnit] = mapped_column(String(20), nullable=False)
    price_per_unit: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Price in integer BDT"
    )
    expected_harvest_date: Mapped[date] = mapped_column(Date, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    upazila: Mapped[str] = mapped_column(String(100), nullable=False)

    # Rule 17: Masked approximate coordinates (~1.1km grid)
    approximate_lat: Mapped[float] = mapped_column(Float, nullable=False)
    approximate_lon: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[CropListingStatus] = mapped_column(
        String(20), default=CropListingStatus.ACTIVE, nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    farmer = relationship("User", foreign_keys=[farmer_id], lazy="joined")


class SavedBuyerSearch(Base):
    """Saved search criteria created by a crop buyer to monitor new matching listings."""
    __tablename__ = "saved_buyer_searches"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    buyer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[CropCategory]] = mapped_column(String(50), nullable=True)
    crop_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    max_price: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id], lazy="joined")

