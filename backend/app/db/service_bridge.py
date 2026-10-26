"""Database Backend Bridge and Unified Repository Service Layer.

Supports runtime switching between:
- DATABASE_BACKEND=sqlite (default)
- DATABASE_BACKEND=mongodb

Preserves:
- All API contracts, schemas, validation rules, and error envelopes.
- Object-level authorization and role permissions.
- In-memory AI inference and Cloudinary image persistence.
- Zero SQLite modification or premature data deletion.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel
from pymongo.database import Database

from app.core.config import settings
from app.core.errors import ShikhorException
from app.db.mongodb import get_mongo_db
from app.db.mongo.schemas import (
    AuditLogDocument,
    BackgroundJobDocument,
    ConversationDocument,
    CropCaseDocument,
    CropCaseFeedbackDoc,
    CropCaseStatusEnum,
    CropListingDocument,
    EquipmentDocument,
    EquipmentReviewDoc,
    ExpertCaseReviewDoc,
    FarmerProfileDoc,
    FeedbackTypeEnum,
    GeoJSONPoint,
    IdempotencyRecordDocument,
    KnowledgeArticleDocument,
    MessageDocument,
    ModerationReportDocument,
    NotificationDocument,
    PilotFeedbackDocument,
    RefreshSessionDocument,
    RentalRequestDocument,
    SavedBuyerSearchDocument,
    UnifiedOTPDocument,
    UserBlockDocument,
    UserDocument,
    UserRoleEnum,
)
from app.db.mongo.repositories import (
    AuditLogRepository,
    BackgroundJobRepository,
    ConversationRepository,
    CropCaseRepository,
    CropListingRepository,
    EquipmentRepository,
    IdempotencyRepository,
    KnowledgeRepository,
    MessageRepository,
    ModerationReportRepository,
    NotificationRepository,
    OTPRepository,
    PilotFeedbackRepository,
    RefreshSessionRepository,
    RentalRequestRepository,
    SavedBuyerSearchRepository,
    UserBlockRepository,
    UserRepository,
)

logger = logging.getLogger("shikhor.db.bridge")


def is_mongodb_backend() -> bool:
    """Returns True if DATABASE_BACKEND is configured to 'mongodb'."""
    return getattr(settings, "DATABASE_BACKEND", "sqlite").lower() == "mongodb"


def get_active_mongo_db() -> Database:
    """Returns target MongoDB database or raises safe exception if unavailable."""
    db = get_mongo_db()
    if db is None:
        logger.error("[MongoDB Bridge] MongoDB connection unavailable while DATABASE_BACKEND=mongodb")
        raise ShikhorException(
            code="DATABASE_UNAVAILABLE",
            message="MongoDB ডেটাবেস সংযোগ উপলব্ধ নয়। দয়া করে সংযোগ স্ট্রিং পরীক্ষা করুন।",
            status_code=503,
        )
    return db


class MongoRepositoryRegistry:
    """Registry providing initialized repository instances for all 18 domain models."""

    def __init__(self, db: Optional[Database] = None):
        self._db = db or get_active_mongo_db()
        self.users = UserRepository(self._db)
        self.crop_cases = CropCaseRepository(self._db)
        self.equipment = EquipmentRepository(self._db)
        self.rentals = RentalRequestRepository(self._db)
        self.crop_listings = CropListingRepository(self._db)
        self.saved_searches = SavedBuyerSearchRepository(self._db)
        self.conversations = ConversationRepository(self._db)
        self.messages = MessageRepository(self._db)
        self.user_blocks = UserBlockRepository(self._db)
        self.knowledge = KnowledgeRepository(self._db)
        self.notifications = NotificationRepository(self._db)
        self.moderation = ModerationReportRepository(self._db)
        self.audit_logs = AuditLogRepository(self._db)
        self.pilot_feedback = PilotFeedbackRepository(self._db)
        self.jobs = BackgroundJobRepository(self._db)
        self.idempotency = IdempotencyRepository(self._db)
        self.sessions = RefreshSessionRepository(self._db)
        self.otps = OTPRepository(self._db)


def get_mongo_registry(db: Optional[Database] = None) -> MongoRepositoryRegistry:
    """FastAPI dependency or direct helper for accessing MongoDB repositories."""
    return MongoRepositoryRegistry(db=db)


# -----------------------------------------------------------------------------
# Unified Service Operations (MongoDB Implementation)
# -----------------------------------------------------------------------------
class MongoServiceAdapter:
    """Adapts high-level business operations to MongoDB repositories when DATABASE_BACKEND=mongodb."""

    def __init__(self, registry: Optional[MongoRepositoryRegistry] = None):
        self.reg = registry or get_mongo_registry()

    # 1. Auth & Users
    def register_user(self, user_doc: UserDocument) -> UserDocument:
        if self.reg.users.get_by_phone(user_doc.phone):
            raise ShikhorException(code="PHONE_EXISTS", message="এই ফোন নম্বরটি ইতিমধ্যে নিবন্ধিত।", status_code=400)
        if user_doc.email and self.reg.users.get_by_email(user_doc.email):
            raise ShikhorException(code="EMAIL_EXISTS", message="এই ইমেইলটি ইতিমধ্যে নিবন্ধিত।", status_code=400)
        return self.reg.users.insert_one(user_doc)

    def find_user_by_id(self, user_id: str) -> Optional[UserDocument]:
        return self.reg.users.find_by_id(user_id)

    # 2. Crop Cases
    def create_crop_case(self, case_doc: CropCaseDocument) -> CropCaseDocument:
        return self.reg.crop_cases.insert_one(case_doc)

    def get_user_cases(self, user_id: str, skip: int = 0, limit: int = 20) -> List[CropCaseDocument]:
        return self.reg.crop_cases.get_by_user(user_id, skip=skip, limit=limit)

    def add_case_feedback(self, case_id: str, feedback: CropCaseFeedbackDoc) -> bool:
        return self.reg.crop_cases.add_feedback(case_id, feedback)

    def add_expert_review(self, case_id: str, review: ExpertCaseReviewDoc) -> bool:
        return self.reg.crop_cases.add_expert_review(case_id, review)

    # 3. Equipment & Rentals
    def create_equipment(self, eq_doc: EquipmentDocument) -> EquipmentDocument:
        return self.reg.equipment.insert_one(eq_doc)

    def search_equipment_nearby(
        self, lng: float, lat: float, max_dist_meters: float = 30000, eq_type: Optional[str] = None
    ) -> List[EquipmentDocument]:
        return self.reg.equipment.find_nearby(lng, lat, max_dist_meters, equipment_type=eq_type)

    def create_rental(self, rental_doc: RentalRequestDocument) -> RentalRequestDocument:
        return self.reg.rentals.insert_one(rental_doc)

    # 4. Crop Marketplace
    def create_crop_listing(self, listing_doc: CropListingDocument) -> CropListingDocument:
        return self.reg.crop_listings.insert_one(listing_doc)

    def search_crop_listings(self, category: Optional[str] = None, district: Optional[str] = None) -> List[CropListingDocument]:
        return self.reg.crop_listings.search_listings(category=category, district=district)

    # 5. Messaging & Moderation
    def send_message(self, msg_doc: MessageDocument) -> MessageDocument:
        return self.reg.messages.insert_one(msg_doc)

    def create_moderation_report(self, report_doc: ModerationReportDocument) -> ModerationReportDocument:
        return self.reg.moderation.insert_one(report_doc)

    # 6. Notifications & Audit
    def create_notification(self, notif_doc: NotificationDocument) -> NotificationDocument:
        return self.reg.notifications.insert_one(notif_doc)

    def record_audit(self, audit_doc: AuditLogDocument) -> AuditLogDocument:
        return self.reg.audit_logs.insert_one(audit_doc)

    # 7. Background Jobs & Idempotency
    def enqueue_job(self, job_doc: BackgroundJobDocument) -> BackgroundJobDocument:
        return self.reg.jobs.insert_one(job_doc)

    def save_idempotency(self, record_doc: IdempotencyRecordDocument) -> IdempotencyRecordDocument:
        return self.reg.idempotency.insert_one(record_doc)
