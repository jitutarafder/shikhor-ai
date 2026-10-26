"""Pydantic document schemas for MongoDB production data layer.

Strictly complies with:
- AGENTS.md Rule 4: No secrets.
- AGENTS.md Rule 11: Authoritative schemas with strict type validation.
- AGENTS.md Rule 16: Exact money & units.
- AGENTS.md Rule 17: Geospatial Point coordinates for equipment & approximate crop locations.
- AGENTS.md Rule 18: Only Cloudinary secure_url/public_id persisted for images (no raw binaries).
- AGENTS.md Rule 21: Idempotency records with payload hashes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------
class UserRoleEnum(str, Enum):
    FARMER = "farmer"
    OWNER = "owner"
    BUYER = "buyer"
    EXPERT = "expert"
    MODERATOR = "moderator"
    ADMIN = "admin"


class CropCaseStatusEnum(str, Enum):
    POSSIBLE_MATCH = "possible_match"
    UNCERTAIN = "uncertain"
    UNSUPPORTED = "unsupported"
    FAILED = "failed"


class FeedbackTypeEnum(str, Enum):
    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    INCORRECT = "incorrect"
    UNSAFE = "unsafe"


class EquipmentTypeEnum(str, Enum):
    TRACTOR = "tractor"
    HARVESTER = "harvester"
    PUMP = "pump"
    SPRAYER = "sprayer"
    POWER_TILLER = "power_tiller"
    OTHER = "other"


class PriceUnitEnum(str, Enum):
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_ACRE = "per_acre"


class RentalStatusEnum(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class CropCategoryEnum(str, Enum):
    PADDY = "paddy"
    WHEAT = "wheat"
    MAIZE = "maize"
    POTATO = "potato"
    VEGETABLE = "vegetable"
    PULSE = "pulse"
    OILSEED = "oilseed"
    SPICE = "spice"
    FRUIT = "fruit"
    OTHER = "other"


class QuantityUnitEnum(str, Enum):
    MAUND = "maund"
    KG = "kg"
    TON = "ton"


class CropListingStatusEnum(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"


class JobStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


# -----------------------------------------------------------------------------
# GeoJSON Models
# -----------------------------------------------------------------------------
class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometry for MongoDB 2dsphere indexing."""
    type: str = "Point"
    coordinates: List[float] = Field(
        ...,
        description="[longitude, latitude] pair in degrees",
        min_length=2,
        max_length=2,
    )


# -----------------------------------------------------------------------------
# 1. User & Embedded Profiles
# -----------------------------------------------------------------------------
class FarmerProfileDoc(BaseModel):
    district: str
    upazila: str
    primary_crops: Optional[str] = None


class OwnerProfileDoc(BaseModel):
    district: str
    upazila: str
    service_radius_km: float = 15.0


class BuyerProfileDoc(BaseModel):
    district: str
    upazila: str
    business_name: Optional[str] = None


class ExpertProfileDoc(BaseModel):
    district: str
    designation: str
    organization: str


class UserDocument(BaseModel):
    """User collection document with embedded role-specific profiles."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phone: str
    email: Optional[str] = None
    nid: Optional[str] = None
    dob: Optional[str] = None
    nid_front_image: Optional[str] = None  # Cloudinary secure_url
    nid_back_image: Optional[str] = None   # Cloudinary secure_url
    is_nid_verified: bool = False
    nid_verification_status: str = "pending"
    nid_rejection_reason: Optional[str] = None
    full_name: str
    hashed_password: str
    role: UserRoleEnum = UserRoleEnum.FARMER
    is_active: bool = True
    is_verified: bool = False
    is_email_verified: bool = False

    # Embedded profiles
    farmer_profile: Optional[FarmerProfileDoc] = None
    owner_profile: Optional[OwnerProfileDoc] = None
    buyer_profile: Optional[BuyerProfileDoc] = None
    expert_profile: Optional[ExpertProfileDoc] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 2. Crop Cases & Embedded Feedback / Reviews
# -----------------------------------------------------------------------------
class CropCaseFeedbackDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    feedback_type: FeedbackTypeEnum
    comments: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExpertCaseReviewDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expert_id: str
    expert_name: str
    reviewed_diagnosis: str
    prescribed_treatment: str
    severity_level: str = "moderate"
    expert_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CropCaseDocument(BaseModel):
    """Crop Case diagnosis document storing AI predictions and embedded feedback."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    crop_type: str
    symptoms_description: Optional[str] = None
    image_url: str  # Cloudinary secure_url
    image_public_id: Optional[str] = None

    status: CropCaseStatusEnum = CropCaseStatusEnum.POSSIBLE_MATCH
    possible_condition: Optional[str] = None
    confidence: float = 0.0
    confidence_band: str = "low"
    reason_summary: List[str] = Field(default_factory=list)
    guidance: List[Union[str, Dict[str, Any]]] = Field(default_factory=list)
    escalation_recommended: bool = False
    model_config = {"protected_namespaces": ()}
    model_version: str = "v1.0.0-reviewed"
    disclaimer: str
    is_reviewed_by_expert: bool = False

    # Embedded Subdocuments
    feedbacks: List[CropCaseFeedbackDoc] = Field(default_factory=list)
    expert_reviews: List[ExpertCaseReviewDoc] = Field(default_factory=list)

    @property
    def image_filename(self) -> str:
        return self.image_url

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 3. Equipment & Embedded Reviews
# -----------------------------------------------------------------------------
class EquipmentReviewDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    renter_id: str
    rental_request_id: str
    rating: int  # 1 to 5
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EquipmentDocument(BaseModel):
    """Agricultural equipment listing with 2dsphere GeoJSON location."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    name: str
    equipment_type: EquipmentTypeEnum
    description: Optional[str] = None
    price_amount: int  # In BDT
    price_unit: PriceUnitEnum
    district: str
    upazila: str
    service_radius_km: float = 15.0
    is_available: bool = True
    is_paused: bool = False

    # GeoJSON Location for 2dsphere index: [longitude, latitude]
    location: GeoJSONPoint

    # Embedded reviews
    reviews: List[EquipmentReviewDoc] = Field(default_factory=list)

    @property
    def latitude(self) -> float:
        return self.location.coordinates[1]

    @property
    def longitude(self) -> float:
        return self.location.coordinates[0]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 4. Rental Requests
# -----------------------------------------------------------------------------
class RentalRequestDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str
    renter_id: str
    owner_id: Optional[str] = None
    rental_date: str  # ISO date string e.g. "2026-10-10"
    selected_dates: Optional[List[str]] = None
    duration_units: int = 1
    total_estimated_price: int  # in BDT
    note: Optional[str] = None
    status: RentalStatusEnum = RentalStatusEnum.PENDING
    idempotency_key: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 5. Crop Marketplace Listings
# -----------------------------------------------------------------------------
class CropListingDocument(BaseModel):
    """Farmer crop listing with approximate GeoJSON coordinates."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    farmer_id: str
    crop_name: str
    category: CropCategoryEnum
    quantity: float
    quantity_unit: QuantityUnitEnum
    price_per_unit: int  # in integer BDT
    expected_harvest_date: str  # ISO date string
    district: str
    upazila: str
    approximate_location: GeoJSONPoint  # Masked approximate coordinates
    status: CropListingStatusEnum = CropListingStatusEnum.ACTIVE
    description: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 6. Saved Buyer Searches
# -----------------------------------------------------------------------------
class SavedBuyerSearchDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    buyer_id: str
    name: str
    category: Optional[CropCategoryEnum] = None
    crop_name: Optional[str] = None
    district: Optional[str] = None
    max_price: Optional[int] = None
    min_quantity: Optional[float] = None
    is_active: bool = True

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 7. Conversations & 8. Messages
# -----------------------------------------------------------------------------
class ConversationDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participants: List[str] = Field(default_factory=list)  # [user_id_1, user_id_2]
    participant1_id: Optional[str] = None
    participant2_id: Optional[str] = None
    context_type: Optional[str] = None  # e.g. "crop_listing" or "equipment"
    context_id: Optional[str] = None
    last_message: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.participants:
            pts = []
            if self.participant1_id:
                pts.append(self.participant1_id)
            if self.participant2_id:
                pts.append(self.participant2_id)
            self.participants = pts
        elif len(self.participants) >= 2:
            if not self.participant1_id:
                self.participant1_id = self.participants[0]
            if not self.participant2_id:
                self.participant2_id = self.participants[1]
        elif len(self.participants) == 1:
            if not self.participant1_id:
                self.participant1_id = self.participants[0]

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MessageDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str
    content: Optional[str] = ""
    attachment_url: Optional[str] = None  # Cloudinary secure_url
    attachment_filename: Optional[str] = None
    is_read: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 9. Knowledge Articles
# -----------------------------------------------------------------------------
class KnowledgeArticleDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    crop_type: str
    category: str
    title_bn: str
    title_en: Optional[str] = None
    summary_bn: str
    content_bn: str
    recommended_practices_bn: Optional[str] = None
    version: int = 1

    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 10. Notifications
# -----------------------------------------------------------------------------
class NotificationDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    notification_type: str = "general"
    link: Optional[str] = None
    is_read: bool = False

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 11. Moderation Reports & 12. User Blocks
# -----------------------------------------------------------------------------
class ModerationReportDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reporter_id: str
    reported_user_id: Optional[str] = None
    content_type: str  # crop_listing, message, or user
    content_id: str
    reason: str
    details: Optional[str] = None
    status: str = "pending"

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserBlockDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    blocker_id: str
    blocked_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 13. Pilot Feedback & 14. Audit Logs
# -----------------------------------------------------------------------------
class PilotFeedbackDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    task_type: str
    ease_of_use_rating: int
    bangla_comprehension_rating: int
    ai_limitations_understood: bool = True
    device_category: str = "low_end_android"
    network_type: str = "4g_wifi"
    latency_ms: Optional[int] = None
    comments: Optional[str] = None
    district: Optional[str] = None
    upazila: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditLogDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: Optional[str] = None
    actor_phone: str
    actor_role: str
    action: str
    resource_type: str
    resource_id: str
    details: str
    request_id: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# -----------------------------------------------------------------------------
# 15. Refresh Sessions (TTL) & 16. Unified OTPs (TTL)
# -----------------------------------------------------------------------------
class RefreshSessionDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token_hash: str
    expires_at: datetime  # MongoDB TTL index expires document at this time
    is_revoked: bool = False
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OTPPurposeEnum(str, Enum):
    SIGNUP = "signup"
    PASSWORD_RESET = "password_reset"


class UnifiedOTPDocument(BaseModel):
    """Unified single-use OTP document with TTL expiration."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    otp_hash: str
    purpose: OTPPurposeEnum
    expires_at: datetime  # MongoDB TTL index expires document at this time
    is_used: bool = False
    token: Optional[str] = None
    verification_token: Optional[str] = None
    attempts: int = 0

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


OTPDocument = UnifiedOTPDocument


# -----------------------------------------------------------------------------
# 17. Idempotency Records (Unique compound + TTL)
# -----------------------------------------------------------------------------
class IdempotencyRecordDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    operation: str
    idempotency_key: str
    request_hash: str
    response_status: int
    response_body: str

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # TTL Index


# -----------------------------------------------------------------------------
# 18. Background Jobs (Durable Queue)
# -----------------------------------------------------------------------------
class BackgroundJobDocument(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: JobStatusEnum = JobStatusEnum.PENDING
    priority: int = 1
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    locked_by: Optional[str] = None
    locked_at: Optional[datetime] = None
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
