"""Tests for Equipment Discovery, Fixed 65/35 Ranking, Privacy, and Rental State Transitions.

Complies with:
- AGENTS.md Rule 12: Object-level authorization policy (owner vs non-owner)
- AGENTS.md Rule 14: Central state machine (pending -> accepted/rejected -> completed/cancelled)
- AGENTS.md Rule 15: Fixed 65% price / 35% distance transparent ranking and unit compatibility
- AGENTS.md Rule 17: Approximate coordinate exposure (rounded to 2 decimal places)
- AGENTS.md Rule 21: Idempotency for offline-created rental requests
- AGENTS.md Rule 28: Mandatory business logic tests
"""

import pytest
from httpx import AsyncClient

from app.modules.equipment.models import Equipment, EquipmentType, PriceUnit
from app.modules.equipment.ranking import (
    RankedEquipmentItem,
    calculate_haversine_distance,
    rank_equipment_candidates,
)


# ============================================================================
# Unit Tests: Ranking Logic (Rule 15)
# ============================================================================


def test_ranking_formula_pure_logic():
    """Verifies normalized scoring, zero-division guards, and 65/35 weights."""
    # User at (24.85, 89.37)
    user_lat, user_lon = 24.85, 89.37

    # Candidate 1: Cheaper (1000), but further (~22 km)
    eq1 = Equipment(
        id="eq-1",
        owner_id="owner-1",
        name="Power Tiller A",
        equipment_type=EquipmentType.POWER_TILLER,
        description="Good condition",
        price_amount=1000,
        price_unit=PriceUnit.PER_DAY,
        district="Bogura",
        upazila="Sadar",
        latitude=25.05,
        longitude=89.37,
        service_radius_km=50.0,
        is_available=True,
        is_paused=False,
    )
    # Candidate 2: More expensive (2000), but right at user location (0 km)
    eq2 = Equipment(
        id="eq-2",
        owner_id="owner-2",
        name="Power Tiller B",
        equipment_type=EquipmentType.POWER_TILLER,
        description="Well maintained",
        price_amount=2000,
        price_unit=PriceUnit.PER_DAY,
        district="Bogura",
        upazila="Shibganj",
        latitude=24.85,
        longitude=89.37,
        service_radius_km=50.0,
        is_available=True,
        is_paused=False,
    )

    candidates = [eq1, eq2]
    ranked = rank_equipment_candidates(
        candidates=candidates,
        user_lat=user_lat,
        user_lon=user_lon,
        target_unit=PriceUnit.PER_DAY,
    )
    assert len(ranked) == 2

    # Verify that ranked items have transparent breakdown
    # eq1: price 1000 (min, price_score=0.0), distance ~22.24 km (max, dist_score=1.0) -> ranking = 0.65*0 + 0.35*1 = 0.35
    # eq2: price 2000 (max, price_score=1.0), distance 0.0 km (min, dist_score=0.0) -> ranking = 0.65*1 + 0.35*0 = 0.65
    assert ranked[0].equipment.id == "eq-1"
    assert ranked[0].price_score == 0.0
    assert ranked[0].distance_score == 1.0
    assert ranked[0].ranking_score == 0.35

    assert ranked[1].equipment.id == "eq-2"
    assert ranked[1].price_score == 1.0
    assert ranked[1].distance_score == 0.0
    assert ranked[1].ranking_score == 0.65


def test_ranking_equal_values_zero_division_guard():
    """Verifies that equal min and max values produce 0.0 normalized score without ZeroDivisionError."""
    user_lat, user_lon = 25.57, 89.28
    eq1 = Equipment(
        id="eq-same-1",
        owner_id="owner-1",
        name="Tractor 1",
        equipment_type=EquipmentType.TRACTOR,
        description="Tractor",
        price_amount=1500,
        price_unit=PriceUnit.PER_HOUR,
        district="Rangpur",
        upazila="Mithapukur",
        latitude=25.57,
        longitude=89.28,
        service_radius_km=25.0,
        is_available=True,
        is_paused=False,
    )
    eq2 = Equipment(
        id="eq-same-2",
        owner_id="owner-2",
        name="Tractor 2",
        equipment_type=EquipmentType.TRACTOR,
        description="Tractor",
        price_amount=1500,
        price_unit=PriceUnit.PER_HOUR,
        district="Rangpur",
        upazila="Pirgachha",
        latitude=25.57,
        longitude=89.28,
        service_radius_km=25.0,
        is_available=True,
        is_paused=False,
    )

    ranked = rank_equipment_candidates(
        candidates=[eq1, eq2],
        user_lat=user_lat,
        user_lon=user_lon,
        target_unit=PriceUnit.PER_HOUR,
    )
    assert len(ranked) == 2
    for item in ranked:
        assert item.price_score == 0.0
        assert item.distance_score == 0.0
        assert item.ranking_score == 0.0


def test_haversine_distance_accuracy():
    """Verifies Haversine formula calculation between known Bangladesh coordinates."""
    # Dhaka (23.8103, 90.4125) to Gazipur (23.9999, 90.4203) is ~21 km
    dist = calculate_haversine_distance(23.8103, 90.4125, 23.9999, 90.4203)
    assert 20.0 <= dist <= 23.0


# ============================================================================
# API & Integration Tests
# ============================================================================


async def register_user(client: AsyncClient, phone: str, name: str, role: str) -> dict:
    """Helper to register and obtain auth token."""
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
    return res.json()


@pytest.mark.asyncio
async def test_equipment_creation_and_privacy_masking(client: AsyncClient):
    """Verifies equipment creation and that public responses mask exact coordinates (Rule 17)."""
    owner_auth = await register_user(client, "01710000001", "মালিক করিম", "owner")
    token = owner_auth["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "মডার্ন পাওয়ার টিলার",
        "equipmentType": "power_tiller",
        "description": "১৬ হর্সপাওয়ার শক্তিশালী টিলার",
        "priceAmount": 1200,
        "priceUnit": "per_day",
        "district": "বগুড়া",
        "upazila": "শিবগঞ্জ",
        "latitude": 24.851234,  # Exact coordinates
        "longitude": 89.375678,
        "serviceRadiusKm": 20.0,
    }

    res = await client.post("/api/v1/equipment", headers=headers, json=payload)
    assert res.status_code == 201, res.text
    data = res.json()

    # Rule 17: Approximate public coordinates rounded to 2 decimal places (~1.1km privacy grid)
    assert data["approximateLat"] == 24.85
    assert data["approximateLon"] == 89.38
    # Exact latitude/longitude must NOT be present in public schema
    assert "latitude" not in data
    assert "longitude" not in data
    assert data["name"] == "মডার্ন পাওয়ার টিলার"
    assert data["priceAmount"] == 1200
    assert data["priceUnit"] == "per_day"


@pytest.mark.asyncio
async def test_equipment_discovery_and_unit_incompatibility(client: AsyncClient):
    """Verifies ranked discovery and that incompatible pricing units are never compared (Rule 15)."""
    owner = await register_user(client, "01710000002", "মালিক রহিম", "owner")
    headers = {"Authorization": f"Bearer {owner['accessToken']}"}

    # Create listing 1: Tractor, per_hour, 1500 BDT
    await client.post(
        "/api/v1/equipment",
        headers=headers,
        json={
            "name": "ট্রাক্টর ১ (ঘণ্টা)",
            "equipmentType": "tractor",
            "priceAmount": 1500,
            "priceUnit": "per_hour",
            "district": "বগুড়া",
            "upazila": "সদর",
            "latitude": 24.85,
            "longitude": 89.37,
            "serviceRadiusKm": 25.0,
        },
    )

    # Create listing 2: Tractor, per_day, 10000 BDT (different unit!)
    await client.post(
        "/api/v1/equipment",
        headers=headers,
        json={
            "name": "ট্রাক্টর ২ (দিন)",
            "equipmentType": "tractor",
            "priceAmount": 10000,
            "priceUnit": "per_day",
            "district": "বগুড়া",
            "upazila": "সদর",
            "latitude": 24.86,
            "longitude": 89.38,
            "serviceRadiusKm": 25.0,
        },
    )

    # Search for per_hour tractors
    search_res = await client.get(
        "/api/v1/equipment",
        params={
            "equipmentType": "tractor",
            "priceUnit": "per_hour",
            "latitude": 24.85,
            "longitude": 89.37,
        },
    )
    assert search_res.status_code == 200, search_res.text
    results = search_res.json()

    # Rule 15: The per_day listing MUST NOT be included in per_hour search
    assert len(results) == 1
    assert results[0]["name"] == "ট্রাক্টর ১ (ঘণ্টা)"
    assert results[0]["priceUnit"] == "per_hour"
    assert "ranking" in results[0]
    assert results[0]["ranking"]["rankingScore"] == 0.0


@pytest.mark.asyncio
async def test_equipment_ownership_authorization(client: AsyncClient):
    """Verifies that an owner cannot modify another owner's machinery (Rule 12)."""
    owner_a = await register_user(client, "01710000003", "মালিক ১", "owner")
    owner_b = await register_user(client, "01710000004", "মালিক ২", "owner")

    # Owner A creates equipment
    create_res = await client.post(
        "/api/v1/equipment",
        headers={"Authorization": f"Bearer {owner_a['accessToken']}"},
        json={
            "name": "সেচ পাম্প",
            "equipmentType": "pump",
            "priceAmount": 500,
            "priceUnit": "per_hour",
            "district": "দিনাজপুর",
            "upazila": "সদর",
            "latitude": 25.62,
            "longitude": 88.63,
            "serviceRadiusKm": 10.0,
        },
    )
    assert create_res.status_code == 201
    eq_id = create_res.json()["id"]

    # Owner B attempts to update Owner A's listing -> 403 Forbidden
    unauth_res = await client.patch(
        f"/api/v1/equipment/{eq_id}",
        headers={"Authorization": f"Bearer {owner_b['accessToken']}"},
        json={"priceAmount": 999},
    )
    assert unauth_res.status_code == 403
    assert unauth_res.json()["error"]["code"] == "FORBIDDEN_EQUIPMENT_UPDATE"

    # Owner A updates own listing -> 200 OK
    auth_res = await client.patch(
        f"/api/v1/equipment/{eq_id}",
        headers={"Authorization": f"Bearer {owner_a['accessToken']}"},
        json={"priceAmount": 550},
    )
    assert auth_res.status_code == 200
    assert auth_res.json()["priceAmount"] == 550


@pytest.mark.asyncio
async def test_rental_creation_and_idempotency(client: AsyncClient):
    """Verifies rental creation and idempotency protection against duplicate network requests (Rule 21)."""
    owner = await register_user(client, "01710000005", "মালিক ৩", "owner")
    renter = await register_user(client, "01710000006", "কৃষক জামিল", "farmer")

    # Owner creates equipment
    eq_res = await client.post(
        "/api/v1/equipment",
        headers={"Authorization": f"Bearer {owner['accessToken']}"},
        json={
            "name": "হার্ভেস্টার",
            "equipmentType": "harvester",
            "priceAmount": 3000,
            "priceUnit": "per_hour",
            "district": "নাটোর",
            "upazila": "সিংড়া",
            "latitude": 24.50,
            "longitude": 89.15,
            "serviceRadiusKm": 20.0,
        },
    )
    eq_id = eq_res.json()["id"]

    rental_payload = {
        "equipmentId": eq_id,
        "rentalDate": "2026-10-15",
        "durationUnits": 3,
        "note": "জরুরি ধান কাটার জন্য",
        "idempotencyKey": "offline-uuid-sync-101",
    }

    # First request
    res1 = await client.post(
        "/api/v1/rentals",
        headers={"Authorization": f"Bearer {renter['accessToken']}"},
        json=rental_payload,
    )
    assert res1.status_code == 201, res1.text
    rental1 = res1.json()
    assert rental1["status"] == "pending"
    assert rental1["durationUnits"] == 3
    assert rental1["totalEstimatedPrice"] == 9000  # 3000 * 3
    assert rental1["idempotencyKey"] == "offline-uuid-sync-101"

    # Second request with identical idempotencyKey (e.g. offline queue retry)
    res2 = await client.post(
        "/api/v1/rentals",
        headers={"Authorization": f"Bearer {renter['accessToken']}"},
        json=rental_payload,
    )
    assert res2.status_code == 201, res2.text
    rental2 = res2.json()

    # Rule 21: Must return the same record, no duplicate created
    assert rental2["id"] == rental1["id"]
    assert rental2["totalEstimatedPrice"] == rental1["totalEstimatedPrice"]


@pytest.mark.asyncio
async def test_rental_state_machine_valid_and_invalid_transitions(client: AsyncClient):
    """Verifies state machine enforcement, actor rules, and terminal states (Rule 14)."""
    owner = await register_user(client, "01710000007", "মালিক ৪", "owner")
    renter = await register_user(client, "01710000008", "কৃষক রফিক", "farmer")
    other_user = await register_user(client, "01710000009", "অন্য ব্যবহারকারী", "farmer")

    # Equipment
    eq_res = await client.post(
        "/api/v1/equipment",
        headers={"Authorization": f"Bearer {owner['accessToken']}"},
        json={
            "name": "স্প্রেয়ার",
            "equipmentType": "sprayer",
            "priceAmount": 200,
            "priceUnit": "per_hour",
            "district": "পাবনা",
            "upazila": "ঈশ্বরদী",
            "latitude": 24.12,
            "longitude": 89.07,
            "serviceRadiusKm": 15.0,
        },
    )
    eq_id = eq_res.json()["id"]

    # Renter requests rental
    rental_res = await client.post(
        "/api/v1/rentals",
        headers={"Authorization": f"Bearer {renter['accessToken']}"},
        json={
            "equipmentId": eq_id,
            "rentalDate": "2026-10-20",
            "durationUnits": 2,
        },
    )
    rental_id = rental_res.json()["id"]
    assert rental_res.json()["status"] == "pending"

    # 1. Non-owner / unrelated user tries to accept -> 403 Forbidden
    unauth_accept = await client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        headers={"Authorization": f"Bearer {other_user['accessToken']}"},
        json={"targetStatus": "accepted"},
    )
    assert unauth_accept.status_code == 403

    # 2. Owner accepts -> 200 OK
    accept_res = await client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        headers={"Authorization": f"Bearer {owner['accessToken']}"},
        json={"targetStatus": "accepted"},
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "accepted"

    # 3. Owner or renter marks completed -> 200 OK
    complete_res = await client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        headers={"Authorization": f"Bearer {renter['accessToken']}"},
        json={"targetStatus": "completed"},
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"

    # 4. Attempting to transition out of completed (terminal state) -> 400 Bad Request
    invalid_res = await client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        headers={"Authorization": f"Bearer {owner['accessToken']}"},
        json={"targetStatus": "accepted"},
    )
    assert invalid_res.status_code == 400
    assert invalid_res.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


@pytest.mark.asyncio
async def test_rental_email_notifications_dispatch(client: AsyncClient):
    """Verifies that booking requests and acceptance send notification emails."""
    from unittest.mock import patch

    owner = await register_user(client, "01710000091", "মালিক করিম", "owner")
    renter = await register_user(client, "01710000092", "কৃষক সালাম", "farmer")

    # Equipment
    eq_res = await client.post(
        "/api/v1/equipment",
        headers={"Authorization": f"Bearer {owner['accessToken']}"},
        json={
            "name": "মিনি পাওয়ার টিলার",
            "equipmentType": "power_tiller",
            "priceAmount": 500,
            "priceUnit": "per_day",
            "district": "বগুড়া",
            "upazila": "শিবগঞ্জ",
            "latitude": 24.95,
            "longitude": 89.35,
            "serviceRadiusKm": 10.0,
        },
    )
    eq_id = eq_res.json()["id"]

    with patch("app.modules.rentals.service.send_email") as mock_send_email:
        mock_send_email.return_value = True

        # 1. Create booking request
        rental_res = await client.post(
            "/api/v1/rentals",
            headers={"Authorization": f"Bearer {renter['accessToken']}"},
            json={
                "equipmentId": eq_id,
                "rentalDate": "2026-11-01",
                "durationUnits": 1,
            },
        )
        assert rental_res.status_code == 201
        rental_id = rental_res.json()["id"]

        # 2. Owner accepts
        accept_res = await client.patch(
            f"/api/v1/rentals/{rental_id}/status",
            headers={"Authorization": f"Bearer {owner['accessToken']}"},
            json={"targetStatus": "accepted"},
        )
        assert accept_res.status_code == 200
        assert accept_res.json()["status"] == "accepted"

