"""Unit and integration tests for Phase 9 Controlled Pilot operations and telemetry.

Strictly verifies:
- AGENTS.md Rule 11: Backend validation is always authoritative.
- AGENTS.md Rule 12: Object-level authorization policy (admin/moderator only for metrics).
- AGENTS.md Rule 19: AI output must be constrained, reviewable, and honest.
- AGENTS.md Rule 31: Real data only on pilot dashboards, no fake statistics.
"""

from datetime import date
from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crop_assistant.models import CropCase, CropCaseStatus
from app.modules.equipment.models import Equipment
from app.modules.rentals.models import RentalRequest, RentalStatus
from app.modules.sync.models import IdempotencyRecord


async def register_user(client: AsyncClient, phone: str, name: str, role: str) -> dict:
    """Helper to register and obtain auth token and user profile."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone,
            "password": "Password123#Strong",
            "full_name": name,
            "role": role,
        },
    )
    assert res.status_code == 201, res.text
    tokens = res.json()
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['accessToken']}"},
    )
    assert me_res.status_code == 200, me_res.text
    return {**tokens, "user": me_res.json()}


@pytest.mark.asyncio
async def test_get_pilot_config(client: AsyncClient):
    """Verifies the public/authenticated pilot configuration endpoint."""
    response = await client.get("/api/v1/pilot/config")
    assert response.status_code == 200
    data = response.json()

    assert "approved_districts" in data
    assert len(data["approved_districts"]) >= 5
    assert any(d["code"] == "bogura" for d in data["approved_districts"])

    assert "approved_crops" in data
    assert any(c["code"] == "rice" for c in data["approved_crops"])

    assert "onboarding_checklist" in data
    assert len(data["onboarding_checklist"]) >= 5
    assert "ai_limitations_notice" in data
    assert "কীটনাশক" in data["ai_limitations_notice"]


@pytest.mark.asyncio
async def test_submit_pilot_feedback_authenticated(client: AsyncClient):
    """Verifies a farmer can submit pilot usability and device feedback."""
    farmer = await register_user(client, "01799000001", "মো: রফিকুল ইসলাম", "farmer")
    token = farmer["accessToken"]

    feedback_payload = {
        "task_type": "crop_diagnosis",
        "ease_of_use_rating": 5,
        "bangla_comprehension_rating": 4,
        "ai_limitations_understood": True,
        "device_category": "low_end_android",
        "network_type": "3g",
        "latency_ms": 1250,
        "comments": "সহজেই ধানের ব্লাইট রোগের লক্ষণ বুঝতে পেরেছি।",
        "district": "Bogura",
        "upazila": "Shibganj",
    }

    response = await client.post(
        "/api/v1/pilot/feedback",
        json=feedback_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["user_id"] == farmer["user"]["id"]
    assert res_data["task_type"] == "crop_diagnosis"
    assert res_data["ease_of_use_rating"] == 5
    assert res_data["ai_limitations_understood"] is True


@pytest.mark.asyncio
async def test_submit_pilot_feedback_validation_bounds(client: AsyncClient):
    """Verifies strict validation bounds on feedback ratings and fields."""
    farmer = await register_user(client, "01799000002", "আব্দুল করিম", "farmer")
    token = farmer["accessToken"]

    # Rating out of bounds (6 is > 5)
    bad_payload = {
        "task_type": "equipment_rental",
        "ease_of_use_rating": 6,
        "bangla_comprehension_rating": 0,  # 0 is < 1
    }
    response = await client.post(
        "/api/v1/pilot/feedback",
        json=bad_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_pilot_metrics_rejects_unauthorized_regular_user(client: AsyncClient):
    """Verifies non-admin/moderator users receive 403 on pilot metrics and feedback list."""
    farmer = await register_user(client, "01799000003", "কামাল হোসেন", "farmer")
    token = farmer["accessToken"]

    res_metrics = await client.get(
        "/api/v1/pilot/metrics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_metrics.status_code == 403

    res_feed = await client.get(
        "/api/v1/pilot/feedback-list",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_feed.status_code == 403


@pytest.mark.asyncio
async def test_admin_pilot_telemetry_metrics_and_go_no_go(
    client: AsyncClient, test_db: AsyncSession
):
    """Verifies real calculation of Phase 9 pilot metrics and Go/No-Go readiness evaluation."""
    admin = await register_user(client, "01799000004", "সিস্টেম অ্যাডমিন", "admin")
    admin_token = admin["accessToken"]

    farmer = await register_user(client, "01799000005", "জয়নাল আবেদিন", "farmer")
    farmer_token = farmer["accessToken"]

    # Submit feedback with latency and ratings
    await client.post(
        "/api/v1/pilot/feedback",
        json={
            "task_type": "general_onboarding",
            "ease_of_use_rating": 4,
            "bangla_comprehension_rating": 5,
            "ai_limitations_understood": True,
            "device_category": "low_end_android",
            "network_type": "3g",
            "latency_ms": 1100,
            "comments": "অনবোর্ডিং নির্দেশনা পরিষ্কার।",
        },
        headers={"Authorization": f"Bearer {farmer_token}"},
    )

    # Seed a crop case and a rental request to verify metrics calculations
    crop_case = CropCase(
        user_id=farmer["user"]["id"],
        crop_type="rice",
        symptoms_description="ধানের পাতায় হলুদাভ দাগ",
        image_filename="crop_test.jpg",
        status=CropCaseStatus.UNCERTAIN,
        confidence=0.45,
        escalation_recommended=True,
        disclaimer="পরীক্ষামূলক ডায়াগনোসিস",
    )
    test_db.add(crop_case)

    # Seed equipment and rental
    owner = await register_user(client, "01799000006", "যন্ত্র মালিক", "owner")
    eq = Equipment(
        owner_id=owner["user"]["id"],
        name="পাওয়ার টিলার",
        equipment_type="power_tiller",
        price_unit="per_day",
        price_amount=2500,
        district="Bogura",
        upazila="Sadar",
        latitude=24.8465,
        longitude=89.3777,
        is_available=True,
    )
    test_db.add(eq)
    await test_db.flush()

    rental = RentalRequest(
        equipment_id=eq.id,
        renter_id=farmer["user"]["id"],
        rental_date=date(2026, 10, 15),
        duration_units=2,
        total_estimated_price=5000,
        status=RentalStatus.ACCEPTED,
    )
    test_db.add(rental)

    # Seed sync idempotency record
    sync_rec = IdempotencyRecord(
        user_id=farmer["user"]["id"],
        operation="submit_rental_request",
        idempotency_key="key-pilot-test-1",
        request_hash="hash123",
        response_status=201,
        response_body="{}",
    )
    test_db.add(sync_rec)
    await test_db.commit()

    # Query pilot metrics as Admin
    res = await client.get(
        "/api/v1/pilot/metrics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    metrics = res.json()

    # Check activation & tasks
    assert metrics["activation_and_tasks"]["total_users"] >= 3
    assert metrics["activation_and_tasks"]["completed_crop_cases"] >= 1
    assert metrics["activation_and_tasks"]["created_rental_requests"] >= 1
    assert metrics["activation_and_tasks"]["processed_sync_records"] >= 1

    # Check AI Escalation
    assert metrics["ai_escalation"]["uncertain_or_unsupported_cases"] >= 1
    assert metrics["ai_escalation"]["escalation_rate_pct"] > 0.0

    # Check Rental Conversion
    assert metrics["rental_conversion"]["accepted_rentals"] >= 1
    assert metrics["rental_conversion"]["conversion_rate_pct"] == 100.0

    # Check Offline Sync Reliability
    assert metrics["offline_sync_reliability"]["successful_syncs"] >= 1
    assert metrics["offline_sync_reliability"]["sync_success_rate_pct"] == 100.0

    # Check Network and Latency
    assert metrics["network_and_latency"]["avg_latency_ms"] == 1100.0
    assert "3g" in metrics["network_and_latency"]["network_breakdown"]
    assert "low_end_android" in metrics["network_and_latency"]["device_breakdown"]

    # Check Comprehension and Usability
    assert metrics["comprehension_and_usability"]["avg_ease_of_use"] == 4.0
    assert metrics["comprehension_and_usability"]["avg_bangla_comprehension"] == 5.0
    assert metrics["comprehension_and_usability"]["ai_limitations_comprehension_pct"] == 100.0

    # Check Go/No-Go Readiness
    go_no_go = metrics["go_no_go_checklist"]
    assert go_no_go["security_safety_ok"] is True
    assert go_no_go["core_journeys_ok"] is True
    assert go_no_go["moderation_capacity_ok"] is True
    assert go_no_go["ai_limitations_understood_ok"] is True
    assert go_no_go["architecture_bottlenecks_measured"] is True
    assert go_no_go["overall_status"] == "READY_FOR_GO_NO_GO"

    # Verify feedback list
    res_list = await client.get(
        "/api/v1/pilot/feedback-list?limit=10",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_list.status_code == 200
    feed_items = res_list.json()
    assert len(feed_items) >= 1
    assert feed_items[0]["comments"] == "অনবোর্ডিং নির্দেশনা পরিষ্কার।"
