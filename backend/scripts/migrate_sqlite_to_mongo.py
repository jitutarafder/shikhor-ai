"""SQLite to MongoDB Atlas Migration Tool for Shikhor AI.

Strictly complies with:
- AGENTS.md Rule 1: Requested scope only (data migration script with dry-run/migrate/verify).
- AGENTS.md Rule 2 & 9: Non-destructive read-only on SQLite; zero modification to source tables.
- AGENTS.md Rule 4: Never print or expose MongoDB credentials.
- AGENTS.md Rule 11 & 16: Strict Pydantic schema validation & exact money/units.
- AGENTS.md Rule 17: Validates GeoJSON Point coordinates order: [longitude, latitude].
- AGENTS.md Rule 18: Preserves Cloudinary references; flags local /uploads/ warnings without inventing URLs.
- AGENTS.md Rule 21: Idempotent upserts ensuring duplicate runs are safe.
"""

import argparse
import asyncio
from datetime import date, datetime, timezone
import logging
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import ValidationError
from pymongo.database import Database
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

# Add project root to python path if run standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.mongodb import get_mongo_client, get_mongo_db, verify_mongodb_connection
from app.db.mongo.indexes import ensure_mongo_indexes
from app.db.session import async_session_factory

# MongoDB Document Schemas
from app.db.mongo.schemas import (
    AuditLogDocument,
    BackgroundJobDocument,
    BuyerProfileDoc,
    ConversationDocument,
    CropCaseDocument,
    CropCaseFeedbackDoc,
    CropCaseStatusEnum,
    CropCategoryEnum,
    CropListingDocument,
    CropListingStatusEnum,
    EquipmentDocument,
    EquipmentReviewDoc,
    EquipmentTypeEnum,
    ExpertCaseReviewDoc,
    ExpertProfileDoc,
    FarmerProfileDoc,
    FeedbackTypeEnum,
    GeoJSONPoint,
    IdempotencyRecordDocument,
    JobStatusEnum,
    KnowledgeArticleDocument,
    MessageDocument,
    ModerationReportDocument,
    NotificationDocument,
    OTPPurposeEnum,
    OwnerProfileDoc,
    PilotFeedbackDocument,
    PriceUnitEnum,
    QuantityUnitEnum,
    RefreshSessionDocument,
    RentalRequestDocument,
    RentalStatusEnum,
    SavedBuyerSearchDocument,
    UnifiedOTPDocument,
    UserBlockDocument,
    UserDocument,
    UserRoleEnum,
)

# SQLAlchemy Models
from app.modules.admin.models import AuditLog
from app.modules.auth.models import PasswordResetOTP, RefreshSession, SignupEmailOTP
from app.modules.crop_assistant.models import CropCase, CropCaseFeedback, ExpertCaseReview
from app.modules.crop_marketplace.models import CropListing, SavedBuyerSearch
from app.modules.equipment.models import Equipment, EquipmentReview
from app.modules.jobs.models import Job
from app.modules.knowledge.models import KnowledgeArticle
from app.modules.messaging.models import Conversation, Message, ModerationReport, UserBlock
from app.modules.notifications.models import Notification
from app.modules.pilot.models import PilotFeedback
from app.modules.rentals.models import RentalRequest
from app.modules.sync.models import IdempotencyRecord
from app.modules.users.models import BuyerProfile, ExpertProfile, FarmerProfile, OwnerProfile, User

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("shikhor.migration")


# -----------------------------------------------------------------------------
# Helper utilities for timezone & coordinate normalization
# -----------------------------------------------------------------------------
def ensure_utc_datetime(dt: Optional[datetime]) -> datetime:
    """Ensures datetime is timezone-aware in UTC."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_date_to_iso(val: Any) -> str:
    """Converts a date, datetime, or string to ISO date string (YYYY-MM-DD)."""
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    return str(val)


def validate_coordinates(longitude: float, latitude: float, entity_name: str, entity_id: str) -> List[str]:
    """Validates GeoJSON coordinate bounds."""
    warnings = []
    if not (-180.0 <= longitude <= 180.0):
        warnings.append(f"Longitude {longitude} for {entity_name}:{entity_id} is out of bounds [-180, 180].")
    if not (-90.0 <= latitude <= 90.0):
        warnings.append(f"Latitude {latitude} for {entity_name}:{entity_id} is out of bounds [-90, 90].")
    return warnings


def check_image_reference(url_or_path: Optional[str], field_name: str, entity_name: str, entity_id: str) -> List[str]:
    """Checks image references and flags legacy local storage paths without inventing fake URLs."""
    warnings = []
    if not url_or_path:
        return warnings
    if url_or_path.startswith("/uploads/") or "\\uploads\\" in url_or_path or (not url_or_path.startswith("http://") and not url_or_path.startswith("https://")):
        warnings.append(
            f"Legacy local image reference found in {entity_name}.{field_name} ('{url_or_path}') for ID {entity_id}. Preserved as-is without inventing Cloudinary URL."
        )
    return warnings


# -----------------------------------------------------------------------------
# Migration Step Result Dataclass
# -----------------------------------------------------------------------------
class StepResult:
    def __init__(self, domain: str, source_table: str):
        self.domain = domain
        self.source_table = source_table
        self.source_count = 0
        self.inserted = 0
        self.updated = 0
        self.skipped = 0
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "source_table": self.source_table,
            "source_count": self.source_count,
            "inserted": self.inserted,
            "updated": self.updated,
            "skipped": self.skipped,
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors),
        }


# -----------------------------------------------------------------------------
# Domain Extract & Transform Handlers
# -----------------------------------------------------------------------------
async def extract_and_transform_users(db_session) -> Tuple[List[UserDocument], StepResult]:
    res = StepResult("users", "users (+ profiles)")
    stmt = (
        select(User)
        .options(
            selectinload(User.farmer_profile),
            selectinload(User.owner_profile),
            selectinload(User.buyer_profile),
            selectinload(User.expert_profile),
        )
    )
    users_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(users_raw)

    docs: List[UserDocument] = []
    for u in users_raw:
        try:
            # Check legacy image references
            res.warnings.extend(check_image_reference(u.nid_front_image, "nid_front_image", "User", u.id))
            res.warnings.extend(check_image_reference(u.nid_back_image, "nid_back_image", "User", u.id))

            farmer_p = None
            if u.farmer_profile:
                farmer_p = FarmerProfileDoc(
                    district=u.farmer_profile.district,
                    upazila=u.farmer_profile.upazila,
                    primary_crops=u.farmer_profile.primary_crops,
                )

            owner_p = None
            if u.owner_profile:
                owner_p = OwnerProfileDoc(
                    district=u.owner_profile.district,
                    upazila=u.owner_profile.upazila,
                    service_radius_km=float(u.owner_profile.service_radius_km),
                )

            buyer_p = None
            if u.buyer_profile:
                buyer_p = BuyerProfileDoc(
                    district=u.buyer_profile.district,
                    upazila=u.buyer_profile.upazila,
                    business_name=u.buyer_profile.business_name,
                )

            expert_p = None
            if u.expert_profile:
                expert_p = ExpertProfileDoc(
                    district=u.expert_profile.district,
                    designation=u.expert_profile.designation,
                    organization=u.expert_profile.organization,
                )

            doc = UserDocument(
                id=str(u.id),
                phone=u.phone,
                email=u.email,
                nid=u.nid,
                dob=u.dob,
                nid_front_image=u.nid_front_image,
                nid_back_image=u.nid_back_image,
                is_nid_verified=bool(u.is_nid_verified),
                nid_verification_status=u.nid_verification_status or "pending",
                nid_rejection_reason=u.nid_rejection_reason,
                full_name=u.full_name,
                hashed_password=u.hashed_password,
                role=UserRoleEnum(u.role.value if hasattr(u.role, "value") else str(u.role)),
                is_active=bool(u.is_active),
                is_verified=bool(u.is_verified),
                is_email_verified=bool(u.is_email_verified),
                farmer_profile=farmer_p,
                owner_profile=owner_p,
                buyer_profile=buyer_p,
                expert_profile=expert_p,
                created_at=ensure_utc_datetime(u.created_at),
                updated_at=ensure_utc_datetime(u.updated_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform user {getattr(u, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_crop_cases(db_session) -> Tuple[List[CropCaseDocument], StepResult]:
    res = StepResult("crop_cases", "crop_cases (+ feedbacks, expert_reviews)")
    stmt = (
        select(CropCase)
        .options(
            selectinload(CropCase.feedbacks),
            selectinload(CropCase.expert_reviews),
        )
    )
    cases_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(cases_raw)

    docs: List[CropCaseDocument] = []
    for c in cases_raw:
        try:
            res.warnings.extend(check_image_reference(c.image_filename, "image_filename", "CropCase", c.id))

            feedbacks = [
                CropCaseFeedbackDoc(
                    id=str(f.id),
                    user_id=str(f.user_id),
                    feedback_type=FeedbackTypeEnum(f.feedback_type.value if hasattr(f.feedback_type, "value") else str(f.feedback_type)),
                    comments=f.comments,
                    created_at=ensure_utc_datetime(f.created_at),
                )
                for f in c.feedbacks
            ]

            expert_reviews = [
                ExpertCaseReviewDoc(
                    id=str(r.id),
                    expert_id=str(r.expert_id),
                    expert_name=r.expert_name,
                    reviewed_diagnosis=r.reviewed_diagnosis,
                    prescribed_treatment=r.prescribed_treatment,
                    severity_level=r.severity_level or "moderate",
                    expert_notes=r.expert_notes,
                    created_at=ensure_utc_datetime(r.created_at),
                )
                for r in c.expert_reviews
            ]

            doc = CropCaseDocument(
                id=str(c.id),
                user_id=str(c.user_id),
                crop_type=c.crop_type,
                symptoms_description=c.symptoms_description,
                image_url=c.image_filename,  # In SQLite, image_filename holds URL or legacy path
                image_public_id=None,
                status=CropCaseStatusEnum(c.status.value if hasattr(c.status, "value") else str(c.status)),
                possible_condition=c.possible_condition,
                confidence=float(c.confidence),
                confidence_band=c.confidence_band or "low",
                reason_summary=c.reason_summary or [],
                guidance=c.guidance or [],
                escalation_recommended=bool(c.escalation_recommended),
                model_version=c.model_version or "v1.0.0-reviewed",
                disclaimer=c.disclaimer or "শিখড় এআই একটি নির্দেশনামূলক সিদ্ধান্ত সহায়তা প্ল্যাটফর্ম।",
                is_reviewed_by_expert=bool(c.is_reviewed_by_expert),
                feedbacks=feedbacks,
                expert_reviews=expert_reviews,
                created_at=ensure_utc_datetime(c.created_at),
                updated_at=ensure_utc_datetime(c.updated_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform CropCase {getattr(c, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_equipment(db_session) -> Tuple[List[EquipmentDocument], StepResult]:
    res = StepResult("equipment", "equipment (+ equipment_reviews)")
    stmt = select(Equipment).options(selectinload(Equipment.reviews))
    equipments_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(equipments_raw)

    docs: List[EquipmentDocument] = []
    for eq in equipments_raw:
        try:
            coord_warns = validate_coordinates(float(eq.longitude), float(eq.latitude), "Equipment", eq.id)
            res.warnings.extend(coord_warns)

            reviews = [
                EquipmentReviewDoc(
                    id=str(r.id),
                    renter_id=str(r.renter_id),
                    rental_request_id=str(r.rental_request_id),
                    rating=int(r.rating),
                    comment=r.comment,
                    created_at=ensure_utc_datetime(r.created_at),
                )
                for r in eq.reviews
            ]

            doc = EquipmentDocument(
                id=str(eq.id),
                owner_id=str(eq.owner_id),
                name=eq.name,
                equipment_type=EquipmentTypeEnum(eq.equipment_type.value if hasattr(eq.equipment_type, "value") else str(eq.equipment_type)),
                description=eq.description,
                price_amount=int(eq.price_amount),
                price_unit=PriceUnitEnum(eq.price_unit.value if hasattr(eq.price_unit, "value") else str(eq.price_unit)),
                district=eq.district,
                upazila=eq.upazila,
                service_radius_km=float(eq.service_radius_km),
                is_available=bool(eq.is_available),
                is_paused=bool(eq.is_paused),
                location=GeoJSONPoint(
                    type="Point",
                    coordinates=[float(eq.longitude), float(eq.latitude)],  # GeoJSON standard: [lng, lat]
                ),
                reviews=reviews,
                created_at=ensure_utc_datetime(eq.created_at),
                updated_at=ensure_utc_datetime(eq.updated_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform Equipment {getattr(eq, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_rentals(db_session) -> Tuple[List[RentalRequestDocument], StepResult]:
    res = StepResult("rental_requests", "rental_requests")
    stmt = select(RentalRequest).options(selectinload(RentalRequest.equipment))
    rentals_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(rentals_raw)

    docs: List[RentalRequestDocument] = []
    for r in rentals_raw:
        try:
            owner_id = str(r.equipment.owner_id) if r.equipment else None
            selected_dates_list = (
                [d.strip() for d in r.selected_dates.split(",") if d.strip()]
                if r.selected_dates
                else None
            )

            doc = RentalRequestDocument(
                id=str(r.id),
                equipment_id=str(r.equipment_id),
                renter_id=str(r.renter_id),
                owner_id=owner_id,
                rental_date=parse_date_to_iso(r.rental_date),
                selected_dates=selected_dates_list,
                duration_units=int(r.duration_units),
                total_estimated_price=int(r.total_estimated_price),
                note=r.note,
                status=RentalStatusEnum(r.status.value if hasattr(r.status, "value") else str(r.status)),
                idempotency_key=r.idempotency_key,
                created_at=ensure_utc_datetime(r.created_at),
                updated_at=ensure_utc_datetime(r.updated_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform RentalRequest {getattr(r, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_crop_listings(db_session) -> Tuple[List[CropListingDocument], StepResult]:
    res = StepResult("crop_listings", "crop_listings")
    stmt = select(CropListing)
    listings_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(listings_raw)

    docs: List[CropListingDocument] = []
    for cl in listings_raw:
        try:
            coord_warns = validate_coordinates(float(cl.approximate_lon), float(cl.approximate_lat), "CropListing", cl.id)
            res.warnings.extend(coord_warns)

            doc = CropListingDocument(
                id=str(cl.id),
                farmer_id=str(cl.farmer_id),
                crop_name=cl.crop_name,
                category=CropCategoryEnum(cl.category.value if hasattr(cl.category, "value") else str(cl.category)),
                quantity=float(cl.quantity),
                quantity_unit=QuantityUnitEnum(cl.quantity_unit.value if hasattr(cl.quantity_unit, "value") else str(cl.quantity_unit)),
                price_per_unit=int(cl.price_per_unit),
                expected_harvest_date=parse_date_to_iso(cl.expected_harvest_date),
                district=cl.district,
                upazila=cl.upazila,
                approximate_location=GeoJSONPoint(
                    type="Point",
                    coordinates=[float(cl.approximate_lon), float(cl.approximate_lat)],  # [lng, lat]
                ),
                status=CropListingStatusEnum(cl.status.value if hasattr(cl.status, "value") else str(cl.status)),
                description=cl.description,
                created_at=ensure_utc_datetime(cl.created_at),
                updated_at=ensure_utc_datetime(cl.updated_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform CropListing {getattr(cl, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_saved_searches(db_session) -> Tuple[List[SavedBuyerSearchDocument], StepResult]:
    res = StepResult("saved_buyer_searches", "saved_buyer_searches")
    stmt = select(SavedBuyerSearch)
    searches_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(searches_raw)

    docs: List[SavedBuyerSearchDocument] = []
    for s in searches_raw:
        try:
            cat = (
                CropCategoryEnum(s.category.value if hasattr(s.category, "value") else str(s.category))
                if s.category
                else None
            )
            doc = SavedBuyerSearchDocument(
                id=str(s.id),
                buyer_id=str(s.buyer_id),
                name=s.name,
                category=cat,
                crop_name=s.crop_name,
                district=s.district,
                max_price=int(s.max_price) if s.max_price is not None else None,
                min_quantity=float(s.min_quantity) if s.min_quantity is not None else None,
                is_active=bool(s.is_active),
                created_at=ensure_utc_datetime(s.created_at),
                updated_at=ensure_utc_datetime(s.updated_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform SavedBuyerSearch {getattr(s, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_conversations(db_session) -> Tuple[List[ConversationDocument], StepResult]:
    res = StepResult("conversations", "conversations")
    stmt = select(Conversation)
    convs_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(convs_raw)

    docs: List[ConversationDocument] = []
    for c in convs_raw:
        try:
            doc = ConversationDocument(
                id=str(c.id),
                participants=[str(c.participant1_id), str(c.participant2_id)],
                context_type=c.context_type,
                context_id=str(c.context_id) if c.context_id else None,
                last_message=None,
                created_at=ensure_utc_datetime(c.created_at),
                updated_at=ensure_utc_datetime(c.updated_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform Conversation {getattr(c, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_messages(db_session) -> Tuple[List[MessageDocument], StepResult]:
    res = StepResult("messages", "messages")
    stmt = select(Message)
    msgs_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(msgs_raw)

    docs: List[MessageDocument] = []
    for m in msgs_raw:
        try:
            res.warnings.extend(check_image_reference(m.attachment_filename, "attachment_filename", "Message", m.id))
            doc = MessageDocument(
                id=str(m.id),
                conversation_id=str(m.conversation_id),
                sender_id=str(m.sender_id),
                content=m.content or "",
                attachment_url=m.attachment_filename if (m.attachment_filename and m.attachment_filename.startswith("http")) else None,
                attachment_filename=m.attachment_filename,
                is_read=bool(m.is_read),
                created_at=ensure_utc_datetime(m.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform Message {getattr(m, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_user_blocks(db_session) -> Tuple[List[UserBlockDocument], StepResult]:
    res = StepResult("user_blocks", "user_blocks")
    stmt = select(UserBlock)
    blocks_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(blocks_raw)

    docs: List[UserBlockDocument] = []
    for b in blocks_raw:
        try:
            doc = UserBlockDocument(
                id=str(b.id),
                blocker_id=str(b.blocker_id),
                blocked_id=str(b.blocked_id),
                created_at=ensure_utc_datetime(b.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform UserBlock {getattr(b, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_moderation(db_session) -> Tuple[List[ModerationReportDocument], StepResult]:
    res = StepResult("moderation_reports", "moderation_reports")
    stmt = select(ModerationReport)
    reports_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(reports_raw)

    docs: List[ModerationReportDocument] = []
    for r in reports_raw:
        try:
            doc = ModerationReportDocument(
                id=str(r.id),
                reporter_id=str(r.reporter_id),
                reported_user_id=str(r.reported_user_id) if r.reported_user_id else None,
                content_type=r.content_type,
                content_id=str(r.content_id),
                reason=r.reason,
                details=r.details,
                status=r.status or "pending",
                created_at=ensure_utc_datetime(r.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform ModerationReport {getattr(r, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_knowledge(db_session) -> Tuple[List[KnowledgeArticleDocument], StepResult]:
    res = StepResult("knowledge_articles", "knowledge_articles")
    stmt = select(KnowledgeArticle)
    arts_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(arts_raw)

    docs: List[KnowledgeArticleDocument] = []
    for a in arts_raw:
        try:
            doc = KnowledgeArticleDocument(
                id=str(a.id),
                crop_type=a.crop_type,
                category=a.category,
                title_bn=a.title_bn,
                title_en=a.title_en,
                summary_bn=a.summary_bn,
                content_bn=a.content_bn,
                recommended_practices_bn=a.recommended_practices_bn,
                version=int(a.version),
                published_at=ensure_utc_datetime(a.published_at),
                updated_at=ensure_utc_datetime(a.updated_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform KnowledgeArticle {getattr(a, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_notifications(db_session) -> Tuple[List[NotificationDocument], StepResult]:
    res = StepResult("notifications", "notifications")
    stmt = select(Notification)
    notifs_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(notifs_raw)

    docs: List[NotificationDocument] = []
    for n in notifs_raw:
        try:
            doc = NotificationDocument(
                id=str(n.id),
                user_id=str(n.user_id),
                title=n.title,
                message=n.message,
                notification_type=n.notification_type or "general",
                link=n.link,
                is_read=bool(n.is_read),
                created_at=ensure_utc_datetime(n.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform Notification {getattr(n, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_pilot_feedback(db_session) -> Tuple[List[PilotFeedbackDocument], StepResult]:
    res = StepResult("pilot_feedback", "pilot_feedback")
    stmt = select(PilotFeedback)
    feedbacks_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(feedbacks_raw)

    docs: List[PilotFeedbackDocument] = []
    for pf in feedbacks_raw:
        try:
            doc = PilotFeedbackDocument(
                id=str(pf.id),
                user_id=str(pf.user_id),
                task_type=pf.task_type,
                ease_of_use_rating=int(pf.ease_of_use_rating),
                bangla_comprehension_rating=int(pf.bangla_comprehension_rating),
                ai_limitations_understood=bool(pf.ai_limitations_understood),
                device_category=pf.device_category or "low_end_android",
                network_type=pf.network_type or "4g_wifi",
                latency_ms=int(pf.latency_ms) if pf.latency_ms is not None else None,
                comments=pf.comments,
                district=pf.district,
                upazila=pf.upazila,
                created_at=ensure_utc_datetime(pf.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform PilotFeedback {getattr(pf, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_audit_logs(db_session) -> Tuple[List[AuditLogDocument], StepResult]:
    res = StepResult("audit_logs", "audit_logs")
    stmt = select(AuditLog)
    logs_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(logs_raw)

    docs: List[AuditLogDocument] = []
    for al in logs_raw:
        try:
            doc = AuditLogDocument(
                id=str(al.id),
                actor_id=str(al.actor_id) if al.actor_id else None,
                actor_phone=al.actor_phone,
                actor_role=al.actor_role,
                action=al.action,
                resource_type=al.resource_type,
                resource_id=str(al.resource_id),
                details=al.details or "{}",
                request_id=al.request_id,
                created_at=ensure_utc_datetime(al.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform AuditLog {getattr(al, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_refresh_sessions(db_session) -> Tuple[List[RefreshSessionDocument], StepResult]:
    res = StepResult("refresh_sessions", "refresh_sessions")
    stmt = select(RefreshSession)
    sess_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(sess_raw)

    docs: List[RefreshSessionDocument] = []
    for s in sess_raw:
        try:
            doc = RefreshSessionDocument(
                id=str(s.id),
                user_id=str(s.user_id),
                token_hash=s.token_hash,
                expires_at=ensure_utc_datetime(s.expires_at),
                is_revoked=bool(s.is_revoked),
                client_ip=s.client_ip,
                user_agent=s.user_agent,
                created_at=ensure_utc_datetime(s.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform RefreshSession {getattr(s, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_otps(db_session) -> Tuple[List[UnifiedOTPDocument], StepResult]:
    res = StepResult("otps", "password_reset_otps + signup_email_otps")

    stmt_reset = select(PasswordResetOTP)
    resets_raw = (await db_session.execute(stmt_reset)).scalars().all()

    stmt_signup = select(SignupEmailOTP)
    signups_raw = (await db_session.execute(stmt_signup)).scalars().all()

    res.source_count = len(resets_raw) + len(signups_raw)

    docs: List[UnifiedOTPDocument] = []
    for r in resets_raw:
        try:
            doc = UnifiedOTPDocument(
                id=str(r.id),
                email=r.email,
                otp_hash=r.otp_hash,
                purpose=OTPPurposeEnum.PASSWORD_RESET,
                expires_at=ensure_utc_datetime(r.expires_at),
                is_used=bool(r.is_used),
                token=r.reset_token,
                attempts=int(r.attempts),
                created_at=ensure_utc_datetime(r.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform PasswordResetOTP {getattr(r, 'id', 'unknown')}: {str(exc)}")

    for s in signups_raw:
        try:
            doc = UnifiedOTPDocument(
                id=str(s.id),
                email=s.email,
                otp_hash=s.otp_hash,
                purpose=OTPPurposeEnum.SIGNUP,
                expires_at=ensure_utc_datetime(s.expires_at),
                is_used=bool(s.is_used),
                token=s.verification_token,
                attempts=int(s.attempts),
                created_at=ensure_utc_datetime(s.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform SignupEmailOTP {getattr(s, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_idempotency(db_session) -> Tuple[List[IdempotencyRecordDocument], StepResult]:
    res = StepResult("idempotency_records", "idempotency_records")
    stmt = select(IdempotencyRecord)
    recs_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(recs_raw)

    docs: List[IdempotencyRecordDocument] = []
    for r in recs_raw:
        try:
            doc = IdempotencyRecordDocument(
                id=str(r.id),
                user_id=str(r.user_id),
                operation=r.operation,
                idempotency_key=r.idempotency_key,
                request_hash=r.request_hash,
                response_status=int(r.response_status),
                response_body=r.response_body,
                created_at=ensure_utc_datetime(r.created_at),
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform IdempotencyRecord {getattr(r, 'id', 'unknown')}: {str(exc)}")

    return docs, res


async def extract_and_transform_jobs(db_session) -> Tuple[List[BackgroundJobDocument], StepResult]:
    res = StepResult("background_jobs", "background_jobs")
    stmt = select(Job)
    jobs_raw = (await db_session.execute(stmt)).scalars().all()
    res.source_count = len(jobs_raw)

    docs: List[BackgroundJobDocument] = []
    for j in jobs_raw:
        try:
            doc = BackgroundJobDocument(
                id=str(j.id),
                job_type=j.job_type,
                payload=j.payload or {},
                status=JobStatusEnum(j.status.value if hasattr(j.status, "value") else str(j.status)),
                priority=int(j.priority),
                attempts=int(j.attempts),
                max_attempts=int(j.max_attempts),
                last_error=j.last_error,
                result_data=j.result_data,
                locked_by=j.locked_by,
                locked_at=ensure_utc_datetime(j.locked_at) if j.locked_at else None,
                scheduled_at=ensure_utc_datetime(j.scheduled_at),
                created_at=ensure_utc_datetime(j.created_at),
                completed_at=ensure_utc_datetime(j.completed_at) if j.completed_at else None,
            )
            docs.append(doc)
        except Exception as exc:
            res.errors.append(f"Failed to transform Job {getattr(j, 'id', 'unknown')}: {str(exc)}")

    return docs, res


# -----------------------------------------------------------------------------
# Registry of Domain Extractors
# -----------------------------------------------------------------------------
MIGRATION_REGISTRY: Dict[str, Callable[[Any], Any]] = {
    "users": extract_and_transform_users,
    "crop_cases": extract_and_transform_crop_cases,
    "equipment": extract_and_transform_equipment,
    "rental_requests": extract_and_transform_rentals,
    "crop_listings": extract_and_transform_crop_listings,
    "saved_buyer_searches": extract_and_transform_saved_searches,
    "conversations": extract_and_transform_conversations,
    "messages": extract_and_transform_messages,
    "user_blocks": extract_and_transform_user_blocks,
    "moderation_reports": extract_and_transform_moderation,
    "knowledge_articles": extract_and_transform_knowledge,
    "notifications": extract_and_transform_notifications,
    "pilot_feedback": extract_and_transform_pilot_feedback,
    "audit_logs": extract_and_transform_audit_logs,
    "refresh_sessions": extract_and_transform_refresh_sessions,
    "otps": extract_and_transform_otps,
    "idempotency_records": extract_and_transform_idempotency,
    "background_jobs": extract_and_transform_jobs,
}


# -----------------------------------------------------------------------------
# Core Runner Functions: Dry-Run, Migrate, Verify
# -----------------------------------------------------------------------------
async def run_dry_run(selected_collections: Optional[List[str]] = None) -> Tuple[List[StepResult], bool]:
    """Reads and validates SQLite records only. Does not write to MongoDB."""
    logger.info("=" * 70)
    logger.info("SHIKHOR AI — SQLITE -> MONGODB MIGRATION (DRY-RUN / READ-ONLY)")
    logger.info("=" * 70)
    logger.info("Notice: No records will be modified or written to SQLite or MongoDB.")

    results: List[StepResult] = []
    has_errors = False

    target_domains = selected_collections or list(MIGRATION_REGISTRY.keys())

    async with async_session_factory() as session:
        for domain in target_domains:
            if domain not in MIGRATION_REGISTRY:
                logger.warning(f"Unknown domain '{domain}'. Skipping.")
                continue

            extractor = MIGRATION_REGISTRY[domain]
            docs, step_res = await extractor(session)

            # In dry-run, documents are successfully validated
            if not step_res.errors:
                step_res.inserted = len(docs)  # Projected to be inserted/upserted
            else:
                has_errors = True

            results.append(step_res)

            logger.info(
                f"[DRY-RUN] Domain: {domain:<22} | Source Rows: {step_res.source_count:<4} | Valid Docs: {len(docs):<4} | Warnings: {len(step_res.warnings):<2} | Errors: {len(step_res.errors)}"
            )
            for w in step_res.warnings:
                logger.warning(f"  |-- {w}")
            for e in step_res.errors:
                logger.error(f"  |-- {e}")

    logger.info("=" * 70)
    logger.info("DRY-RUN VALIDATION SUMMARY")
    logger.info("=" * 70)
    total_source = sum(r.source_count for r in results)
    total_valid = sum(r.inserted for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    total_errors = sum(len(r.errors) for r in results)

    logger.info(f"Total SQLite Source Records Scanned : {total_source}")
    logger.info(f"Total Validated Target Documents   : {total_valid}")
    logger.info(f"Total Warnings Logged              : {total_warnings}")
    logger.info(f"Total Validation Errors            : {total_errors}")

    if total_errors == 0:
        logger.info("[SUCCESS] All source SQLite records passed validation and schema transformation.")
    else:
        logger.error(f"[FAIL] {total_errors} validation error(s) detected. Fix errors before running --migrate.")

    return results, not has_errors


async def run_migrate(selected_collections: Optional[List[str]] = None, mongo_db: Optional[Database] = None) -> Tuple[List[StepResult], bool]:
    """Performs the actual idempotent migration to MongoDB."""
    logger.info("=" * 70)
    logger.info("SHIKHOR AI — SQLITE -> MONGODB MIGRATION (EXECUTION)")
    logger.info("=" * 70)

    db = mongo_db or get_mongo_db()
    if db is None:
        logger.error("MongoDB is not reachable. Ensure MONGODB_URL is configured and valid.")
        return [], False

    # 1. Ensure production indexes exist first
    logger.info("[Migration] Ensuring production indexes on MongoDB collections...")
    ensure_mongo_indexes(db)

    results: List[StepResult] = []
    has_errors = False
    target_domains = selected_collections or list(MIGRATION_REGISTRY.keys())

    async with async_session_factory() as session:
        for domain in target_domains:
            if domain not in MIGRATION_REGISTRY:
                continue

            extractor = MIGRATION_REGISTRY[domain]
            docs, step_res = await extractor(session)

            coll = db[domain]

            for doc in docs:
                try:
                    data = doc.model_dump(mode="json")
                    doc_id = data["id"]

                    # Idempotent upsert
                    existing = coll.find_one({"id": doc_id}, {"_id": 1})
                    coll.replace_one({"id": doc_id}, data, upsert=True)

                    if existing:
                        step_res.updated += 1
                    else:
                        step_res.inserted += 1
                except Exception as exc:
                    step_res.errors.append(f"Failed upserting document {getattr(doc, 'id', 'unknown')} into {domain}: {str(exc)}")
                    has_errors = True

            results.append(step_res)
            logger.info(
                f"[MIGRATED] Domain: {domain:<20} | Source: {step_res.source_count:<4} | Inserted: {step_res.inserted:<4} | Updated: {step_res.updated:<4} | Errors: {len(step_res.errors)}"
            )

    return results, not has_errors


async def run_verify(selected_collections: Optional[List[str]] = None, mongo_db: Optional[Database] = None) -> bool:
    """Compares SQLite source counts against MongoDB counts."""
    logger.info("=" * 70)
    logger.info("SHIKHOR AI — SQLITE vs MONGODB VERIFICATION AUDIT")
    logger.info("=" * 70)

    db = mongo_db or get_mongo_db()
    if db is None:
        logger.error("MongoDB is not reachable. Cannot perform verification.")
        return False

    all_matched = True
    target_domains = selected_collections or list(MIGRATION_REGISTRY.keys())

    async with async_session_factory() as session:
        for domain in target_domains:
            if domain not in MIGRATION_REGISTRY:
                continue

            extractor = MIGRATION_REGISTRY[domain]
            docs, step_res = await extractor(session)
            sqlite_count = step_res.source_count

            mongo_count = db[domain].count_documents({})

            status = "MATCH" if (sqlite_count == mongo_count) else "MISMATCH"
            if sqlite_count != mongo_count:
                all_matched = False
                logger.warning(
                    f"[{status}] {domain:<22} | SQLite: {sqlite_count:<4} | MongoDB: {mongo_count:<4}"
                )
            else:
                logger.info(
                    f"[{status}]    {domain:<22} | SQLite: {sqlite_count:<4} | MongoDB: {mongo_count:<4}"
                )

    if all_matched:
        logger.info("[SUCCESS] All domain document counts match exactly between SQLite and MongoDB.")
    else:
        logger.warning("[WARNING] Some document counts mismatched. Please review.")

    return all_matched


# -----------------------------------------------------------------------------
# Main CLI Entrypoint
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Shikhor AI SQLite to MongoDB Migration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate SQLite records without writing to MongoDB (Default mode).",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        default=False,
        help="Execute actual migration to MongoDB (Requires valid MONGODB_URL).",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        default=False,
        help="Audit document counts between SQLite and MongoDB.",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="Filter execution to a single collection/domain name (e.g. 'users', 'equipment').",
    )

    args = parser.parse_args()

    selected_cols = [args.collection] if args.collection else None

    # Determine execution mode: default to dry-run if neither --migrate nor --verify is explicitly provided
    if args.verify:
        success = asyncio.run(run_verify(selected_cols))
        sys.exit(0 if success else 1)
    elif args.migrate:
        _, success = asyncio.run(run_migrate(selected_cols))
        sys.exit(0 if success else 1)
    else:
        _, success = asyncio.run(run_dry_run(selected_cols))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
