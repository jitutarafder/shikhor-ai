"""MongoDB Repository and Data Access Layer for Shikhor AI.

Enforces:
- Clean abstraction over PyMongo operations.
- Preserves UUID/string ID contracts.
- Strongly typed Pydantic document conversions.
- Safe 2dsphere geospatial search queries.
- Zero local image persistence / Cloudinary-only references.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from pydantic import BaseModel
from pymongo import ASCENDING, DESCENDING
from pymongo.database import Database

from app.db.mongo.schemas import (
    AuditLogDocument,
    BackgroundJobDocument,
    ConversationDocument,
    CropCaseDocument,
    CropCaseFeedbackDoc,
    CropListingDocument,
    EquipmentDocument,
    EquipmentReviewDoc,
    ExpertCaseReviewDoc,
    IdempotencyRecordDocument,
    JobStatusEnum,
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
)

logger = logging.getLogger("shikhor.db.mongo.repositories")

T = TypeVar("T", bound=BaseModel)


class BaseMongoRepository(Generic[T]):
    """Generic base repository for MongoDB collection operations."""

    def __init__(self, db: Database, collection_name: str, model_cls: Type[T]):
        self.db = db
        self.collection_name = collection_name
        self.collection = db[collection_name]
        self.model_cls = model_cls

    def _to_doc(self, raw: Optional[Dict[str, Any]]) -> Optional[T]:
        if not raw:
            return None
        # Remove MongoDB native _id if present to avoid pydantic schema collision
        doc_data = {k: v for k, v in raw.items() if k != "_id"}
        return self.model_cls(**doc_data)

    def find_one(self, query: Dict[str, Any]) -> Optional[T]:
        raw = self.collection.find_one(query)
        return self._to_doc(raw)

    def find_by_id(self, doc_id: str) -> Optional[T]:
        return self.find_one({"id": doc_id})

    def find_many(
        self,
        query: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[T]:
        cursor = self.collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)
        return [self._to_doc(raw) for raw in cursor if raw is not None]  # type: ignore

    def insert_one(self, item: T) -> T:
        data = item.model_dump(mode="json")
        self.collection.insert_one(data)
        return item

    def update_by_id(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        if "updated_at" not in updates:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = self.collection.update_one({"id": doc_id}, {"$set": updates})
        return res.modified_count > 0

    def delete_by_id(self, doc_id: str) -> bool:
        res = self.collection.delete_one({"id": doc_id})
        return res.deleted_count > 0

    def count_documents(self, query: Dict[str, Any]) -> int:
        return self.collection.count_documents(query)


# -----------------------------------------------------------------------------
# 1. UserRepository
# -----------------------------------------------------------------------------
class UserRepository(BaseMongoRepository[UserDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "users", UserDocument)

    def get_by_phone(self, phone: str) -> Optional[UserDocument]:
        return self.find_one({"phone": phone})

    def get_by_email(self, email: str) -> Optional[UserDocument]:
        return self.find_one({"email": email})

    def get_by_nid(self, nid: str) -> Optional[UserDocument]:
        return self.find_one({"nid": nid})


# -----------------------------------------------------------------------------
# 2. CropCaseRepository
# -----------------------------------------------------------------------------
class CropCaseRepository(BaseMongoRepository[CropCaseDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "crop_cases", CropCaseDocument)

    def get_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> List[CropCaseDocument]:
        return self.find_many(
            {"user_id": user_id},
            sort=[("created_at", DESCENDING)],
            skip=skip,
            limit=limit,
        )

    def get_pending_expert_cases(self, skip: int = 0, limit: int = 20) -> List[CropCaseDocument]:
        return self.find_many(
            {"is_reviewed_by_expert": False, "escalation_recommended": True},
            sort=[("created_at", ASCENDING)],
            skip=skip,
            limit=limit,
        )

    def add_feedback(self, case_id: str, feedback: CropCaseFeedbackDoc) -> bool:
        res = self.collection.update_one(
            {"id": case_id},
            {"$push": {"feedbacks": feedback.model_dump(mode="json")}},
        )
        return res.modified_count > 0

    def add_expert_review(self, case_id: str, review: ExpertCaseReviewDoc) -> bool:
        res = self.collection.update_one(
            {"id": case_id},
            {
                "$push": {"expert_reviews": review.model_dump(mode="json")},
                "$set": {"is_reviewed_by_expert": True, "updated_at": datetime.now(timezone.utc).isoformat()},
            },
        )
        return res.modified_count > 0


# -----------------------------------------------------------------------------
# 3. EquipmentRepository (with 2dsphere Geo Queries)
# -----------------------------------------------------------------------------
class EquipmentRepository(BaseMongoRepository[EquipmentDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "equipment", EquipmentDocument)

    def find_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 30000,
        equipment_type: Optional[str] = None,
        price_unit: Optional[str] = None,
        is_available: bool = True,
        skip: int = 0,
        limit: int = 20,
    ) -> List[EquipmentDocument]:
        """Performs 2dsphere $near geospatial search on agricultural equipment."""
        query: Dict[str, Any] = {
            "is_available": is_available,
            "is_paused": False,
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "$maxDistance": max_distance_meters,
                }
            },
        }
        if equipment_type:
            query["equipment_type"] = equipment_type
        if price_unit:
            query["price_unit"] = price_unit

        cursor = self.collection.find(query).skip(skip).limit(limit)
        return [self._to_doc(raw) for raw in cursor if raw is not None]  # type: ignore

    def add_review(self, equipment_id: str, review: EquipmentReviewDoc) -> bool:
        res = self.collection.update_one(
            {"id": equipment_id},
            {"$push": {"reviews": review.model_dump(mode="json")}},
        )
        return res.modified_count > 0

    def get_by_owner(self, owner_id: str, skip: int = 0, limit: int = 50) -> List[EquipmentDocument]:
        return self.find_many(
            {"owner_id": owner_id},
            sort=[("created_at", DESCENDING)],
            skip=skip,
            limit=limit,
        )

    def get_owner_equipment(self, owner_id: str, skip: int = 0, limit: int = 50) -> List[EquipmentDocument]:
        return self.get_by_owner(owner_id, skip=skip, limit=limit)


# -----------------------------------------------------------------------------
# 4. RentalRequestRepository
# -----------------------------------------------------------------------------
class RentalRequestRepository(BaseMongoRepository[RentalRequestDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "rental_requests", RentalRequestDocument)

    def get_by_renter(self, renter_id: str) -> List[RentalRequestDocument]:
        return self.find_many({"renter_id": renter_id}, sort=[("created_at", DESCENDING)])

    def get_by_owner(self, owner_id: str) -> List[RentalRequestDocument]:
        return self.find_many({"owner_id": owner_id}, sort=[("created_at", DESCENDING)])


# -----------------------------------------------------------------------------
# 5. CropListingRepository (with 2dsphere Geo Queries)
# -----------------------------------------------------------------------------
class CropListingRepository(BaseMongoRepository[CropListingDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "crop_listings", CropListingDocument)

    def get_by_farmer(self, farmer_id: str, skip: int = 0, limit: int = 50) -> List[CropListingDocument]:
        return self.find_many(
            {"farmer_id": farmer_id},
            sort=[("created_at", DESCENDING)],
            skip=skip,
            limit=limit,
        )

    def search_listings(
        self,
        category: Optional[str] = None,
        district: Optional[str] = None,
        status: str = "active",
        skip: int = 0,
        limit: int = 20,
    ) -> List[CropListingDocument]:
        query: Dict[str, Any] = {"status": status}
        if category:
            query["category"] = category
        if district:
            query["district"] = district

        return self.find_many(query, sort=[("created_at", DESCENDING)], skip=skip, limit=limit)

    def find_nearby(
        self,
        longitude: float,
        latitude: float,
        max_distance_meters: float = 50000,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[CropListingDocument]:
        query: Dict[str, Any] = {
            "status": "active",
            "approximate_location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "$maxDistance": max_distance_meters,
                }
            },
        }
        if category:
            query["category"] = category

        cursor = self.collection.find(query).skip(skip).limit(limit)
        return [self._to_doc(raw) for raw in cursor if raw is not None]  # type: ignore


# -----------------------------------------------------------------------------
# 6. SavedBuyerSearchRepository
# -----------------------------------------------------------------------------
class SavedBuyerSearchRepository(BaseMongoRepository[SavedBuyerSearchDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "saved_buyer_searches", SavedBuyerSearchDocument)


# -----------------------------------------------------------------------------
# 7. ConversationRepository & 8. MessageRepository
# -----------------------------------------------------------------------------
class ConversationRepository(BaseMongoRepository[ConversationDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "conversations", ConversationDocument)

    def get_user_conversations(self, user_id: str) -> List[ConversationDocument]:
        return self.find_many(
            {"$or": [{"participants": user_id}, {"participant1_id": user_id}, {"participant2_id": user_id}]},
            sort=[("updated_at", DESCENDING)],
        )

    def find_or_create(
        self,
        user_a_id: str,
        user_b_id: str,
        context_type: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> ConversationDocument:
        raw = self.collection.find_one({
            "$or": [
                {"participant1_id": user_a_id, "participant2_id": user_b_id},
                {"participant1_id": user_b_id, "participant2_id": user_a_id},
                {"participants": {"$all": [user_a_id, user_b_id]}},
            ]
        })
        if raw:
            return self._to_doc(raw)  # type: ignore

        doc = ConversationDocument(
            participant1_id=user_a_id,
            participant2_id=user_b_id,
            participants=[user_a_id, user_b_id],
            context_type=context_type,
            context_id=context_id,
        )
        return self.insert_one(doc)


class MessageRepository(BaseMongoRepository[MessageDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "messages", MessageDocument)

    def get_conversation_messages(
        self, conversation_id: str, skip: int = 0, limit: int = 50
    ) -> List[MessageDocument]:
        return self.find_many(
            {"conversation_id": conversation_id},
            sort=[("created_at", ASCENDING)],
            skip=skip,
            limit=limit,
        )

    def get_by_conversation(
        self, conversation_id: str, skip: int = 0, limit: int = 50
    ) -> List[MessageDocument]:
        return self.get_conversation_messages(conversation_id, skip=skip, limit=limit)

    def mark_as_read(self, conversation_id: str, reader_id: str) -> int:
        res = self.collection.update_many(
            {"conversation_id": conversation_id, "sender_id": {"$ne": reader_id}, "is_read": False},
            {"$set": {"is_read": True}}
        )
        return res.modified_count


# -----------------------------------------------------------------------------
# 9. KnowledgeRepository
# -----------------------------------------------------------------------------
class KnowledgeRepository(BaseMongoRepository[KnowledgeArticleDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "knowledge_articles", KnowledgeArticleDocument)

    def get_by_crop_and_category(
        self, crop_type: str, category: Optional[str] = None
    ) -> List[KnowledgeArticleDocument]:
        query: Dict[str, Any] = {"crop_type": crop_type}
        if category:
            query["category"] = category
        return self.find_many(query, sort=[("version", DESCENDING)])


# -----------------------------------------------------------------------------
# 10. NotificationRepository
# -----------------------------------------------------------------------------
class NotificationRepository(BaseMongoRepository[NotificationDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "notifications", NotificationDocument)

    def get_user_notifications(
        self, user_id: str, unread_only: bool = False, skip: int = 0, limit: int = 20
    ) -> List[NotificationDocument]:
        query: Dict[str, Any] = {"user_id": user_id}
        if unread_only:
            query["is_read"] = False
        return self.find_many(query, sort=[("created_at", DESCENDING)], skip=skip, limit=limit)


# -----------------------------------------------------------------------------
# 11. ModerationRepository & 12. UserBlockRepository
# -----------------------------------------------------------------------------
class ModerationReportRepository(BaseMongoRepository[ModerationReportDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "moderation_reports", ModerationReportDocument)


class UserBlockRepository(BaseMongoRepository[UserBlockDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "user_blocks", UserBlockDocument)

    def is_blocked(self, user_a_id: str, user_b_id: str) -> bool:
        return self.collection.find_one({
            "$or": [
                {"blocker_id": user_a_id, "blocked_id": user_b_id},
                {"blocker_id": user_b_id, "blocked_id": user_a_id},
            ]
        }) is not None


# -----------------------------------------------------------------------------
# 13. PilotFeedbackRepository & 14. AuditLogRepository
# -----------------------------------------------------------------------------
class PilotFeedbackRepository(BaseMongoRepository[PilotFeedbackDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "pilot_feedback", PilotFeedbackDocument)


class AuditLogRepository(BaseMongoRepository[AuditLogDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "audit_logs", AuditLogDocument)


# -----------------------------------------------------------------------------
# 15. Auth & OTP Repositories (TTL Managed)
# -----------------------------------------------------------------------------
class RefreshSessionRepository(BaseMongoRepository[RefreshSessionDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "refresh_sessions", RefreshSessionDocument)

    def get_by_token_hash(self, token_hash: str) -> Optional[RefreshSessionDocument]:
        return self.find_one({"token_hash": token_hash, "is_revoked": False})

    def find_by_token_hash(self, token_hash: str) -> Optional[RefreshSessionDocument]:
        return self.get_by_token_hash(token_hash)

    def revoke_by_token_hash(self, token_hash: str) -> bool:
        res = self.collection.update_one(
            {"token_hash": token_hash},
            {"$set": {"is_revoked": True}}
        )
        return res.modified_count > 0

    def revoke_all_for_user(self, user_id: str) -> int:
        res = self.collection.update_many(
            {"user_id": user_id, "is_revoked": False},
            {"$set": {"is_revoked": True}}
        )
        return res.modified_count


class OTPRepository(BaseMongoRepository[UnifiedOTPDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "otps", UnifiedOTPDocument)

    def get_valid_otp(self, email: str, purpose: str, otp_hash: str) -> Optional[UnifiedOTPDocument]:
        return self.find_one({
            "email": email,
            "purpose": purpose,
            "otp_hash": otp_hash,
            "is_used": False,
        })


# -----------------------------------------------------------------------------
# 17. IdempotencyRepository (TTL + Compound Unique)
# -----------------------------------------------------------------------------
class IdempotencyRepository(BaseMongoRepository[IdempotencyRecordDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "idempotency_records", IdempotencyRecordDocument)

    def get_record(self, user_id: str, operation: str, idempotency_key: str) -> Optional[IdempotencyRecordDocument]:
        return self.find_one({
            "user_id": user_id,
            "operation": operation,
            "idempotency_key": idempotency_key,
        })


# -----------------------------------------------------------------------------
# 18. BackgroundJobRepository
# -----------------------------------------------------------------------------
class BackgroundJobRepository(BaseMongoRepository[BackgroundJobDocument]):
    def __init__(self, db: Database):
        super().__init__(db, "background_jobs", BackgroundJobDocument)

    def fetch_and_lock_next_job(self, worker_id: str) -> Optional[BackgroundJobDocument]:
        """Atomically locks the next highest priority pending job for execution."""
        now = datetime.now(timezone.utc)
        raw = self.collection.find_one_and_update(
            {"status": JobStatusEnum.PENDING.value, "scheduled_at": {"$lte": now}},
            {
                "$set": {
                    "status": JobStatusEnum.PROCESSING.value,
                    "locked_by": worker_id,
                    "locked_at": now,
                },
                "$inc": {"attempts": 1},
            },
            sort=[("priority", DESCENDING), ("scheduled_at", ASCENDING)],
        )
        return self._to_doc(raw)
