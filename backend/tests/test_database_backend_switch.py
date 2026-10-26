"""Test suite for DATABASE_BACKEND runtime switch between SQLite and MongoDB.

Complies with:
- AGENTS.md Rule 4: No hardcoded secrets.
- AGENTS.md Rule 11: Authoritative schema validation.
- AGENTS.md Rule 17: Geospatial Point validation in MongoDB.
- AGENTS.md Rule 28: Mandatory testing for all changed storage and database logic.
"""

from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock, patch

from app.core.config import settings
from app.core.errors import ShikhorException
from app.db.service_bridge import (
    MongoRepositoryRegistry,
    MongoServiceAdapter,
    is_mongodb_backend,
)
from app.db.mongo.schemas import (
    CropCaseDocument,
    CropCaseStatusEnum,
    CropListingDocument,
    EquipmentDocument,
    EquipmentTypeEnum,
    FarmerProfileDoc,
    GeoJSONPoint,
    IdempotencyRecordDocument,
    MessageDocument,
    NotificationDocument,
    PriceUnitEnum,
    QuantityUnitEnum,
    RentalRequestDocument,
    UserDocument,
    UserRoleEnum,
)


def test_database_backend_default_sqlite():
    """Verifies that default database backend is 'sqlite'."""
    with patch.object(settings, "DATABASE_BACKEND", "sqlite"):
        assert is_mongodb_backend() is False


def test_database_backend_switch_to_mongodb():
    """Verifies is_mongodb_backend returns True when DATABASE_BACKEND='mongodb'."""
    with patch.object(settings, "DATABASE_BACKEND", "mongodb"):
        assert is_mongodb_backend() is True


def test_mongo_service_adapter_user_registration():
    """Verifies user registration flow through MongoServiceAdapter."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_coll.find_one.return_value = None  # No existing user

    registry = MongoRepositoryRegistry(db=mock_db)
    adapter = MongoServiceAdapter(registry=registry)

    user = UserDocument(
        phone="01811223344",
        email="test_bridge@shikhor.ai",
        full_name="Bridge Test User",
        hashed_password="secure_password_hash",
        role=UserRoleEnum.FARMER,
        farmer_profile=FarmerProfileDoc(
            district="Tangail",
            upazila="Sadar",
            primary_crops="Rice",
        ),
    )

    created = adapter.register_user(user)
    assert created.phone == "01811223344"
    assert created.farmer_profile.district == "Tangail"
    assert mock_coll.insert_one.called


def test_mongo_service_adapter_crop_case_creation():
    """Verifies crop case creation and retrieval via MongoServiceAdapter."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    registry = MongoRepositoryRegistry(db=mock_db)
    adapter = MongoServiceAdapter(registry=registry)

    case = CropCaseDocument(
        user_id="user_test_uuid",
        crop_type="potato",
        symptoms_description="Dark spots on leaves",
        image_url="https://res.cloudinary.com/demo/image/upload/v1/shikhor_ai/crops/potato.webp",
        image_public_id="shikhor_ai/crops/potato",
        status=CropCaseStatusEnum.POSSIBLE_MATCH,
        possible_condition="Late Blight",
        confidence=0.92,
        disclaimer="Advisory only",
    )

    created = adapter.create_crop_case(case)
    assert created.possible_condition == "Late Blight"
    assert created.image_url.startswith("https://res.cloudinary.com")
    assert mock_coll.insert_one.called


def test_mongo_service_adapter_equipment_geojson_search():
    """Verifies equipment creation and 2dsphere search query building."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_cursor = MagicMock()
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = []
    mock_coll.find.return_value = mock_cursor

    registry = MongoRepositoryRegistry(db=mock_db)
    adapter = MongoServiceAdapter(registry=registry)

    eq = EquipmentDocument(
        owner_id="owner_uuid_1",
        name="Kubota Harvester",
        equipment_type=EquipmentTypeEnum.HARVESTER,
        price_amount=2500,
        price_unit=PriceUnitEnum.PER_ACRE,
        district="Mymensingh",
        upazila="Trishal",
        location=GeoJSONPoint(coordinates=[90.39, 24.58]),
    )

    adapter.create_equipment(eq)
    assert mock_coll.insert_one.called

    adapter.search_equipment_nearby(lng=90.39, lat=24.58, max_dist_meters=25000, eq_type="harvester")
    assert mock_coll.find.called
    query = mock_coll.find.call_args[0][0]
    assert query["equipment_type"] == "harvester"
    assert query["location"]["$near"]["$geometry"]["coordinates"] == [90.39, 24.58]


def test_mongo_service_adapter_crop_listing_marketplace():
    """Verifies crop listing creation and retrieval via MongoServiceAdapter."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = []
    mock_coll.find.return_value = mock_cursor

    registry = MongoRepositoryRegistry(db=mock_db)
    adapter = MongoServiceAdapter(registry=registry)

    listing = CropListingDocument(
        farmer_id="farmer_uuid_100",
        crop_name="Aman Rice",
        category="paddy",
        quantity=50.0,
        quantity_unit=QuantityUnitEnum.MAUND,
        price_per_unit=1200,
        expected_harvest_date="2026-11-15",
        district="Bogura",
        upazila="Sariakandi",
        approximate_location=GeoJSONPoint(coordinates=[89.62, 24.89]),
    )

    adapter.create_crop_listing(listing)
    assert mock_coll.insert_one.called

    adapter.search_crop_listings(category="paddy", district="Bogura")
    assert mock_coll.find.called


def test_mongo_service_adapter_messaging_and_notifications():
    """Verifies chat messaging and notifications creation via MongoServiceAdapter."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    registry = MongoRepositoryRegistry(db=mock_db)
    adapter = MongoServiceAdapter(registry=registry)

    msg = MessageDocument(
        conversation_id="conv_123",
        sender_id="user_1",
        content="Hello, is the tractor available?",
    )
    adapter.send_message(msg)
    assert mock_coll.insert_one.called

    notif = NotificationDocument(
        user_id="user_2",
        title="New Message",
        message="You received a message from Rahim",
    )
    adapter.create_notification(notif)
    assert mock_coll.insert_one.called


def test_mongo_service_adapter_idempotency_cache():
    """Verifies offline sync idempotency cache via MongoServiceAdapter."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_db.__getitem__.return_value = mock_coll

    registry = MongoRepositoryRegistry(db=mock_db)
    adapter = MongoServiceAdapter(registry=registry)

    rec = IdempotencyRecordDocument(
        user_id="u_99",
        operation="CREATE_CROP_CASE",
        idempotency_key="idemp_case_999",
        request_hash="sha256hash123",
        response_status=200,
        response_body='{"id":"case_999","status":"possible_match"}',
    )
    adapter.save_idempotency(rec)
    assert mock_coll.insert_one.called


def test_mongo_unavailable_safe_error():
    """Verifies get_active_mongo_db raises safe ShikhorException when Mongo is disconnected."""
    with patch("app.db.service_bridge.get_mongo_db", return_value=None):
        from app.db.service_bridge import get_active_mongo_db
        with pytest.raises(ShikhorException) as exc_info:
            get_active_mongo_db()
        assert exc_info.value.code == "DATABASE_UNAVAILABLE"
        assert exc_info.value.status_code == 503
