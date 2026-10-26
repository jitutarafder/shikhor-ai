"""Unit and integration test suite for MongoDB production data layer.

Complies with:
- AGENTS.md Rule 4: No hardcoded secrets.
- AGENTS.md Rule 11: Authoritative schema validation.
- AGENTS.md Rule 17: Geospatial Point validation.
- AGENTS.md Rule 18: No local image paths, Cloudinary URL only.
- AGENTS.md Rule 28: Mandatory testing for all changed data and business logic.
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock

from app.db.mongo.schemas import (
    CropCaseDocument,
    CropCaseFeedbackDoc,
    CropCaseStatusEnum,
    CropListingDocument,
    EquipmentDocument,
    EquipmentReviewDoc,
    EquipmentTypeEnum,
    ExpertCaseReviewDoc,
    FarmerProfileDoc,
    FeedbackTypeEnum,
    GeoJSONPoint,
    IdempotencyRecordDocument,
    JobStatusEnum,
    PriceUnitEnum,
    RefreshSessionDocument,
    RentalRequestDocument,
    RentalStatusEnum,
    UnifiedOTPDocument,
    UserDocument,
    UserRoleEnum,
)
from app.db.mongo.indexes import (
    INDEX_SPECIFICATIONS,
    ensure_mongo_indexes,
)
from app.db.mongo.repositories import (
    CropCaseRepository,
    EquipmentRepository,
    UserRepository,
)


def test_user_document_with_embedded_profiles():
    """Verifies UserDocument serialization with embedded farmer profile."""
    user = UserDocument(
        phone="01711223344",
        email="farmer@shikhor.ai",
        full_name="Md. Rahim Farmer",
        hashed_password="$argon2id$v=19$samplehash",
        role=UserRoleEnum.FARMER,
        farmer_profile=FarmerProfileDoc(
            district="Bogura",
            upazila="Sherpur",
            primary_crops="Rice, Potato",
        ),
    )
    data = user.model_dump(mode="json")
    assert data["phone"] == "01711223344"
    assert data["role"] == "farmer"
    assert data["farmer_profile"]["district"] == "Bogura"
    assert data["farmer_profile"]["primary_crops"] == "Rice, Potato"
    assert data["owner_profile"] is None


def test_crop_case_document_with_embedded_reviews_and_feedback():
    """Verifies CropCaseDocument with embedded feedback and expert reviews."""
    case = CropCaseDocument(
        user_id="user_uuid_123",
        crop_type="paddy",
        symptoms_description="Yellow lesions with gray center on leaves",
        image_url="https://res.cloudinary.com/shikhor/image/upload/v1/shikhor_ai/crops/leaf.webp",
        image_public_id="shikhor_ai/crops/leaf",
        status=CropCaseStatusEnum.POSSIBLE_MATCH,
        possible_condition="Rice Blast",
        confidence=0.88,
        confidence_band="high",
        reason_summary=["Spindle-shaped lesions observed"],
        guidance=[{"step": 1, "action": "Drain standing water"}],
        disclaimer="Advisory only.",
        feedbacks=[
            CropCaseFeedbackDoc(
                user_id="user_uuid_123",
                feedback_type=FeedbackTypeEnum.HELPFUL,
                comments="Very accurate diagnosis",
            )
        ],
        expert_reviews=[
            ExpertCaseReviewDoc(
                expert_id="expert_uuid_456",
                expert_name="Dr. Agronomist",
                reviewed_diagnosis="Rice Blast (Magnaporthe oryzae)",
                prescribed_treatment="Apply Tricyclazole 75 WP at 0.6g/L",
                severity_level="moderate",
            )
        ],
    )
    data = case.model_dump(mode="json")
    assert data["possible_condition"] == "Rice Blast"
    assert len(data["feedbacks"]) == 1
    assert data["feedbacks"][0]["feedback_type"] == "helpful"
    assert len(data["expert_reviews"]) == 1
    assert data["expert_reviews"][0]["prescribed_treatment"].startswith("Apply Tricyclazole")
    assert "https://res.cloudinary.com" in data["image_url"]


def test_equipment_document_with_geojson_point():
    """Verifies EquipmentDocument schema with 2dsphere GeoJSON geometry."""
    eq = EquipmentDocument(
        owner_id="owner_uuid_789",
        name="John Deere 5050D Tractor",
        equipment_type=EquipmentTypeEnum.TRACTOR,
        price_amount=1200,
        price_unit=PriceUnitEnum.PER_HOUR,
        district="Dinajpur",
        upazila="Birganj",
        location=GeoJSONPoint(coordinates=[88.6514, 25.8569]),
        reviews=[
            EquipmentReviewDoc(
                renter_id="renter_123",
                rental_request_id="req_999",
                rating=5,
                comment="Well maintained tractor",
            )
        ],
    )
    data = eq.model_dump(mode="json")
    assert data["location"]["type"] == "Point"
    assert data["location"]["coordinates"] == [88.6514, 25.8569]
    assert data["price_amount"] == 1200
    assert len(data["reviews"]) == 1


def test_ttl_documents_serialization():
    """Verifies TTL expiry timestamps for refresh sessions, OTPs, and idempotency records."""
    exp_time = datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)

    session = RefreshSessionDocument(
        user_id="u123",
        token_hash="sha256_hash_here",
        expires_at=exp_time,
    )
    assert session.expires_at == exp_time

    otp = UnifiedOTPDocument(
        email="test@shikhor.ai",
        otp_hash="otp_hash_123",
        purpose="signup",
        expires_at=exp_time,
    )
    assert otp.purpose == "signup"

    idempotency = IdempotencyRecordDocument(
        user_id="u123",
        operation="CREATE_RENTAL",
        idempotency_key="idemp_abc_123",
        request_hash="sha256_payload_hash",
        response_status=201,
        response_body='{"status":"accepted"}',
    )
    assert idempotency.idempotency_key == "idemp_abc_123"


def test_index_specifications_cover_all_collections():
    """Verifies that all 18 production collections have index specifications defined."""
    required_collections = [
        "users",
        "crop_cases",
        "equipment",
        "rental_requests",
        "crop_listings",
        "saved_buyer_searches",
        "conversations",
        "messages",
        "knowledge_articles",
        "notifications",
        "moderation_reports",
        "user_blocks",
        "pilot_feedback",
        "audit_logs",
        "refresh_sessions",
        "otps",
        "idempotency_records",
        "background_jobs",
    ]
    for coll in required_collections:
        assert coll in INDEX_SPECIFICATIONS, f"Missing index specification for {coll}"
        assert len(INDEX_SPECIFICATIONS[coll]) > 0


def test_ensure_mongo_indexes_execution():
    """Verifies that ensure_mongo_indexes calls create_indexes on all target collections."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_collection.create_indexes.return_value = ["idx_1", "idx_2"]
    mock_db.__getitem__.return_value = mock_collection

    summary = ensure_mongo_indexes(mock_db)
    assert len(summary) == len(INDEX_SPECIFICATIONS)
    assert "users" in summary
    assert "equipment" in summary
    assert "refresh_sessions" in summary
    assert mock_collection.create_indexes.called


def test_user_repository_crud():
    """Verifies UserRepository data transformations and find methods with mock collection."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    user_doc = UserDocument(
        phone="01799887766",
        full_name="Rahim",
        hashed_password="hash",
        role=UserRoleEnum.FARMER,
    )

    repo = UserRepository(mock_db)

    # Test insert
    repo.insert_one(user_doc)
    assert mock_coll.insert_one.called

    # Test find_by_phone
    mock_coll.find_one.return_value = user_doc.model_dump(mode="json")
    found = repo.get_by_phone("01799887766")
    assert found is not None
    assert found.phone == "01799887766"
    assert found.full_name == "Rahim"


def test_equipment_repository_geospatial_query():
    """Verifies EquipmentRepository builds correct 2dsphere $near query."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = []
    mock_coll.find.return_value = mock_cursor

    repo = EquipmentRepository(mock_db)
    repo.find_nearby(
        longitude=88.65,
        latitude=25.85,
        max_distance_meters=20000,
        equipment_type="tractor",
    )

    assert mock_coll.find.called
    call_query = mock_coll.find.call_args[0][0]
    assert "$near" in call_query["location"]
    assert call_query["location"]["$near"]["$geometry"]["coordinates"] == [88.65, 25.85]
    assert call_query["location"]["$near"]["$maxDistance"] == 20000
    assert call_query["equipment_type"] == "tractor"

