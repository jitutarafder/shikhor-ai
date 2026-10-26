"""User domain models and role profile tables."""

import enum
import uuid
from typing import Optional
from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(str, enum.Enum):
    FARMER = "farmer"
    OWNER = "owner"
    BUYER = "buyer"
    EXPERT = "expert"
    MODERATOR = "moderator"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    nid: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True, nullable=True)
    dob: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    nid_front_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    nid_back_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_nid_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nid_verification_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    nid_rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", native_enum=False),
        default=UserRole.FARMER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    farmer_profile: Mapped[Optional["FarmerProfile"]] = relationship(
        "FarmerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    owner_profile: Mapped[Optional["OwnerProfile"]] = relationship(
        "OwnerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    buyer_profile: Mapped[Optional["BuyerProfile"]] = relationship(
        "BuyerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    expert_profile: Mapped[Optional["ExpertProfile"]] = relationship(
        "ExpertProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        "RefreshSession", back_populates="user", cascade="all, delete-orphan"
    )


class FarmerProfile(Base, TimestampMixin):
    __tablename__ = "farmer_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    upazila: Mapped[str] = mapped_column(String(100), nullable=False)
    primary_crops: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship("User", back_populates="farmer_profile")


class OwnerProfile(Base, TimestampMixin):
    __tablename__ = "owner_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    upazila: Mapped[str] = mapped_column(String(100), nullable=False)
    service_radius_km: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="owner_profile")


class BuyerProfile(Base, TimestampMixin):
    __tablename__ = "buyer_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    upazila: Mapped[str] = mapped_column(String(100), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="buyer_profile")


class ExpertProfile(Base, TimestampMixin):
    __tablename__ = "expert_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    organization: Mapped[str] = mapped_column(String(150), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)

    user: Mapped[User] = relationship("User", back_populates="expert_profile")


# To resolve circular import with RefreshSession
from app.modules.auth.models import RefreshSession  # noqa: E402
