"""Tests for SQLite -> MongoDB Atlas Migration Tool.

Verifies:
- Complete dry-run execution on active SQLite tables without errors.
- Correct schema extraction and transformations across all domains.
- Embedded profile mappings (farmer, owner, buyer, expert).
- Embedded subdocuments (crop_case feedbacks/reviews, equipment reviews).
- GeoJSON Point coordinate structure [longitude, latitude].
- Legacy /uploads/ image warnings without fake URL fabrication.
- Unified OTPs collection transformation.
- Idempotent upsert behavior on multiple migration runs.
- Verification comparison between SQLite and MongoDB.
"""

import pytest
from typing import Any, Dict, List, Optional

class MockCollection:
    def __init__(self, name: str):
        self.name = name
        self.docs: Dict[str, Dict[str, Any]] = {}

    def find_one(self, query: Dict[str, Any], projection: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        target_id = query.get("id")
        return self.docs.get(target_id)

    def replace_one(self, query: Dict[str, Any], data: Dict[str, Any], upsert: bool = False):
        target_id = query.get("id") or data.get("id")
        self.docs[target_id] = data

    def count_documents(self, query: Dict[str, Any]) -> int:
        return len(self.docs)

    def create_indexes(self, models: List[Any]) -> List[str]:
        return ["mock_index"]


class MockDatabase:
    def __init__(self):
        self._collections: Dict[str, MockCollection] = {}

    def __getitem__(self, name: str) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection(name)
        return self._collections[name]

from app.db.session import async_session_factory
from app.db.mongo.schemas import GeoJSONPoint, OTPPurposeEnum, UserRoleEnum
from scripts.migrate_sqlite_to_mongo import (
    check_image_reference,
    ensure_utc_datetime,
    extract_and_transform_crop_cases,
    extract_and_transform_crop_listings,
    extract_and_transform_equipment,
    extract_and_transform_otps,
    extract_and_transform_users,
    run_dry_run,
    run_migrate,
    run_verify,
    validate_coordinates,
)


@pytest.mark.asyncio
async def test_migration_dry_run_all_domains():
    """Verifies that full dry run executes across all 18 domains with zero validation errors."""
    results, ok = await run_dry_run()
    assert ok is True
    assert len(results) == 18

    # Ensure no step had fatal validation errors
    for step in results:
        assert len(step.errors) == 0, f"Domain '{step.domain}' had errors: {step.errors}"


@pytest.mark.asyncio
async def test_migration_dry_run_specific_domain():
    """Verifies filtering dry run by specific domain names."""
    results, ok = await run_dry_run(selected_collections=["users", "equipment"])
    assert ok is True
    assert len(results) == 2
    domains = [r.domain for r in results]
    assert "users" in domains
    assert "equipment" in domains


@pytest.mark.asyncio
async def test_extract_and_transform_users():
    """Verifies users extraction and profile embedding."""
    async with async_session_factory() as session:
        docs, step_res = await extract_and_transform_users(session)
        assert step_res.errors == []
        assert len(docs) == step_res.source_count

        for doc in docs:
            assert isinstance(doc.id, str)
            assert isinstance(doc.role, UserRoleEnum)
            # If user has a role, check that profile mapping was parsed correctly
            if doc.farmer_profile:
                assert doc.farmer_profile.district != ""
                assert doc.farmer_profile.upazila != ""
            if doc.owner_profile:
                assert doc.owner_profile.service_radius_km > 0
            if doc.expert_profile:
                assert doc.expert_profile.designation != ""


@pytest.mark.asyncio
async def test_extract_and_transform_equipment_geojson():
    """Verifies equipment extraction and GeoJSON Point coordinate structure."""
    async with async_session_factory() as session:
        docs, step_res = await extract_and_transform_equipment(session)
        assert step_res.errors == []
        assert len(docs) == step_res.source_count

        for doc in docs:
            assert isinstance(doc.location, GeoJSONPoint)
            assert doc.location.type == "Point"
            assert len(doc.location.coordinates) == 2
            lng, lat = doc.location.coordinates
            # Longitude [-180, 180], Latitude [-90, 90]
            assert -180.0 <= lng <= 180.0
            assert -90.0 <= lat <= 90.0
            assert isinstance(doc.reviews, list)


@pytest.mark.asyncio
async def test_extract_and_transform_crop_cases_embedded():
    """Verifies crop cases extraction and embedded feedbacks/expert reviews."""
    async with async_session_factory() as session:
        docs, step_res = await extract_and_transform_crop_cases(session)
        assert step_res.errors == []
        assert len(docs) == step_res.source_count

        for doc in docs:
            assert isinstance(doc.feedbacks, list)
            assert isinstance(doc.expert_reviews, list)
            assert isinstance(doc.guidance, list)


@pytest.mark.asyncio
async def test_extract_and_transform_crop_listings_geojson():
    """Verifies crop listings approximate GeoJSON point."""
    async with async_session_factory() as session:
        docs, step_res = await extract_and_transform_crop_listings(session)
        assert step_res.errors == []
        assert len(docs) == step_res.source_count

        for doc in docs:
            assert isinstance(doc.approximate_location, GeoJSONPoint)
            lng, lat = doc.approximate_location.coordinates
            assert -180.0 <= lng <= 180.0
            assert -90.0 <= lat <= 90.0


@pytest.mark.asyncio
async def test_extract_and_transform_otps_unified():
    """Verifies unification of password reset and signup OTPs."""
    async with async_session_factory() as session:
        docs, step_res = await extract_and_transform_otps(session)
        assert step_res.errors == []
        assert len(docs) == step_res.source_count

        purposes = {doc.purpose for doc in docs}
        if docs:
            assert all(isinstance(p, OTPPurposeEnum) for p in purposes)


def test_coordinate_validation_helper():
    """Verifies coordinate validation helper."""
    assert validate_coordinates(90.4125, 23.8103, "Test", "123") == []
    warns = validate_coordinates(200.0, -100.0, "Test", "123")
    assert len(warns) == 2


def test_legacy_image_warning_flag():
    """Verifies that legacy local paths produce warnings without inventing URLs."""
    warns = check_image_reference("/uploads/nid/test.jpg", "nid_front_image", "User", "u1")
    assert len(warns) == 1
    assert "Legacy local image reference" in warns[0]

    # Cloudinary URLs should produce zero warnings
    assert check_image_reference("https://res.cloudinary.com/demo/image/upload/v1/test.jpg", "image", "Case", "c1") == []


@pytest.mark.asyncio
async def test_mock_mongo_migration_idempotent():
    """Tests actual migration and verification against a mock MongoDB database."""
    mock_db = MockDatabase()

    # First migration run: all records should be inserted
    results1, ok1 = await run_migrate(selected_collections=["users", "equipment"], mongo_db=mock_db)
    assert ok1 is True
    for r in results1:
        assert r.inserted == r.source_count
        assert r.updated == 0

    # Verification: should match exactly
    match = await run_verify(selected_collections=["users", "equipment"], mongo_db=mock_db)
    assert match is True

    # Second migration run: all records should be updated, 0 new insertions, 0 duplicates
    results2, ok2 = await run_migrate(selected_collections=["users", "equipment"], mongo_db=mock_db)
    assert ok2 is True
    for r in results2:
        assert r.inserted == 0
        assert r.updated == r.source_count

    # Collection count remains identical
    assert mock_db["users"].count_documents({}) == results1[0].source_count
    assert mock_db["equipment"].count_documents({}) == results1[1].source_count
