"""Tests for Later Roadmap: Equipment Availability Calendar and Ratings/Reviews.

Strictly complies with:
- AGENTS.md Rule 11: Backend validation is always authoritative.
- AGENTS.md Rule 14: Centralized state machine transitions.
- AGENTS.md Rule 15: Fixed ranking formula preserved (ratings provide social proof, do not secretly skew 65/35 ranking).
- AGENTS.md Rule 28: Mandatory integration test suite for security & business logic.
- Security.md Line 328: Do not allow client-supplied ratings or completed-transaction claims without server validation.
"""

from datetime import date, timedelta
import pytest
from httpx import AsyncClient


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
async def test_availability_calendar_and_double_booking_guard(client: AsyncClient):
    """Verifies availability calendar reflects booked dates and prevents conflicting bookings."""
    owner = await register_user(client, "01766000001", "যন্ত্র মালিক কাশেম", "owner")
    farmer1 = await register_user(client, "01766000002", "কৃষক জামাল", "farmer")
    farmer2 = await register_user(client, "01766000003", "কৃষক কামাল", "farmer")

    owner_headers = {"Authorization": f"Bearer {owner['accessToken']}"}
    f1_headers = {"Authorization": f"Bearer {farmer1['accessToken']}"}
    f2_headers = {"Authorization": f"Bearer {farmer2['accessToken']}"}

    # 1. Create equipment
    eq_res = await client.post(
        "/api/v1/equipment",
        headers=owner_headers,
        json={
            "name": "পাওয়ার টিলার ২০২৪",
            "equipment_type": "power_tiller",
            "price_amount": 1200,
            "price_unit": "per_day",
            "district": "বগুড়া",
            "upazila": "শেরপুর",
            "latitude": 24.67,
            "longitude": 89.42,
            "service_radius_km": 15.0,
        },
    )
    assert eq_res.status_code == 201
    eq_id = eq_res.json()["id"]

    target_date = (date.today() + timedelta(days=5)).isoformat()

    # 2. Check initial availability: should be empty
    avail_res = await client.get(f"/api/v1/equipment/{eq_id}/availability")
    assert avail_res.status_code == 200
    assert len(avail_res.json()["bookedDates"]) == 0

    # 3. Farmer 1 creates rental request for target_date
    rent1_res = await client.post(
        "/api/v1/rentals",
        headers=f1_headers,
        json={
            "equipmentId": eq_id,
            "rentalDate": target_date,
            "durationUnits": 1,
            "note": "জমি চাষের জন্য প্রয়োজন",
        },
    )
    assert rent1_res.status_code == 201
    rental1_id = rent1_res.json()["id"]

    # 4. Owner accepts rental 1
    accept_res = await client.patch(
        f"/api/v1/rentals/{rental1_id}/status",
        headers=owner_headers,
        json={"targetStatus": "accepted"},
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["status"] == "accepted"

    # 5. Calendar now reflects target_date as booked
    avail_res2 = await client.get(f"/api/v1/equipment/{eq_id}/availability")
    assert avail_res2.status_code == 200
    booked_dates = [b["rentalDate"] for b in avail_res2.json()["bookedDates"]]
    assert target_date in booked_dates

    # 6. Farmer 2 attempts to book the SAME date -> must be rejected (Rule 11)
    rent2_res = await client.post(
        "/api/v1/rentals",
        headers=f2_headers,
        json={
            "equipmentId": eq_id,
            "rentalDate": target_date,
            "durationUnits": 1,
        },
    )
    assert rent2_res.status_code == 400
    assert rent2_res.json()["error"]["code"] == "DATE_ALREADY_BOOKED"

    # 7. Farmer 2 books a different available date -> succeeds
    other_date = (date.today() + timedelta(days=6)).isoformat()
    rent2_ok = await client.post(
        "/api/v1/rentals",
        headers=f2_headers,
        json={
            "equipmentId": eq_id,
            "rentalDate": other_date,
            "durationUnits": 1,
        },
    )
    assert rent2_ok.status_code == 201


@pytest.mark.asyncio
async def test_equipment_ratings_require_completed_rental(client: AsyncClient):
    """Verifies ratings strictly require a completed rental transaction (Security.md)."""
    owner = await register_user(client, "01766000010", "যন্ত্র মালিক রহমত", "owner")
    farmer = await register_user(client, "01766000011", "কৃষক মন্টু", "farmer")
    other_farmer = await register_user(client, "01766000012", "অন্য কৃষক", "farmer")

    owner_headers = {"Authorization": f"Bearer {owner['accessToken']}"}
    farmer_headers = {"Authorization": f"Bearer {farmer['accessToken']}"}
    other_headers = {"Authorization": f"Bearer {other_farmer['accessToken']}"}

    # 1. Create equipment
    eq_res = await client.post(
        "/api/v1/equipment",
        headers=owner_headers,
        json={
            "name": "আধুনিক ধান মাড়াই কল",
            "equipment_type": "harvester",
            "price_amount": 2000,
            "price_unit": "per_hour",
            "district": "রংপুর",
            "upazila": "মিঠাপুকুর",
            "latitude": 25.58,
            "longitude": 89.28,
            "service_radius_km": 15.0,
        },
    )
    assert eq_res.status_code == 201
    eq_id = eq_res.json()["id"]

    rental_date = (date.today() + timedelta(days=2)).isoformat()

    # 2. Farmer places rental
    rent_res = await client.post(
        "/api/v1/rentals",
        headers=farmer_headers,
        json={
            "equipmentId": eq_id,
            "rentalDate": rental_date,
            "durationUnits": 2,
        },
    )
    assert rent_res.status_code == 201
    rental_id = rent_res.json()["id"]

    # 3. Attempt to review while PENDING -> must fail (400)
    rev_pending = await client.post(
        f"/api/v1/equipment/{eq_id}/reviews",
        headers=farmer_headers,
        json={
            "rentalRequestId": rental_id,
            "rating": 5,
            "comment": "কাজ ভালো",
        },
    )
    assert rev_pending.status_code == 400
    assert rev_pending.json()["error"]["code"] == "RENTAL_NOT_COMPLETED"

    # 4. Owner accepts
    await client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        headers=owner_headers,
        json={"targetStatus": "accepted"},
    )

    # 5. Attempt to review while ACCEPTED -> still must fail (400)
    rev_accepted = await client.post(
        f"/api/v1/equipment/{eq_id}/reviews",
        headers=farmer_headers,
        json={"rentalRequestId": rental_id, "rating": 5},
    )
    assert rev_accepted.status_code == 400

    # 6. Complete the rental
    complete_res = await client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        headers=farmer_headers,
        json={"targetStatus": "completed"},
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"

    # 7. Non-renter attempts to submit review -> must fail (403)
    rev_unauth = await client.post(
        f"/api/v1/equipment/{eq_id}/reviews",
        headers=other_headers,
        json={"rentalRequestId": rental_id, "rating": 5},
    )
    assert rev_unauth.status_code == 403
    assert rev_unauth.json()["error"]["code"] == "FORBIDDEN_REVIEW"

    # 8. Renter submits valid 5-star review -> succeeds (201)
    rev_ok = await client.post(
        f"/api/v1/equipment/{eq_id}/reviews",
        headers=farmer_headers,
        json={
            "rentalRequestId": rental_id,
            "rating": 5,
            "comment": "যন্ত্রটি খুব ভালো চলেছে এবং সময়মতো পৌঁছেছে।",
        },
    )
    assert rev_ok.status_code == 201, rev_ok.text
    review_data = rev_ok.json()
    assert review_data["rating"] == 5
    assert review_data["renterName"] == "কৃষক মন্টু"

    # 9. Duplicate review attempt on same rental -> rejected (400)
    rev_dup = await client.post(
        f"/api/v1/equipment/{eq_id}/reviews",
        headers=farmer_headers,
        json={"rentalRequestId": rental_id, "rating": 4},
    )
    assert rev_dup.status_code == 400
    assert rev_dup.json()["error"]["code"] == "REVIEW_ALREADY_EXISTS"

    # 10. Check equipment details reflects averageRating = 5.0 and reviewCount = 1
    eq_details = await client.get(f"/api/v1/equipment/{eq_id}")
    assert eq_details.status_code == 200
    eq_data = eq_details.json()
    assert eq_data["averageRating"] == 5.0
    assert eq_data["reviewCount"] == 1

    # 11. Check public reviews endpoint
    reviews_list = await client.get(f"/api/v1/equipment/{eq_id}/reviews")
    assert reviews_list.status_code == 200
    assert len(reviews_list.json()) == 1
    assert reviews_list.json()[0]["rating"] == 5


@pytest.mark.asyncio
async def test_multi_date_rental_and_availability_calendar(client: AsyncClient):
    """Verifies that farmers can fix/book multiple dates and calendar marks all of them as booked."""
    owner = await register_user(client, "01766000020", "যন্ত্র মালিক সামসুল", "owner")
    farmer1 = await register_user(client, "01766000021", "কৃষক রফিক", "farmer")
    farmer2 = await register_user(client, "01766000022", "কৃষক শফিক", "farmer")

    owner_headers = {"Authorization": f"Bearer {owner['accessToken']}"}
    f1_headers = {"Authorization": f"Bearer {farmer1['accessToken']}"}
    f2_headers = {"Authorization": f"Bearer {farmer2['accessToken']}"}

    # 1. Create equipment
    eq_res = await client.post(
        "/api/v1/equipment",
        headers=owner_headers,
        json={
            "name": "কম্বাইন হার্ভেস্টার ২০২৬",
            "equipment_type": "harvester",
            "price_amount": 3000,
            "price_unit": "per_day",
            "district": "দিনাজপুর",
            "upazila": "কাহারোল",
            "latitude": 25.79,
            "longitude": 88.60,
            "service_radius_km": 20.0,
        },
    )
    assert eq_res.status_code == 201
    eq_id = eq_res.json()["id"]

    d1 = (date.today() + timedelta(days=10)).isoformat()
    d2 = (date.today() + timedelta(days=11)).isoformat()
    d3 = (date.today() + timedelta(days=12)).isoformat()

    # 2. Farmer 1 books 3 dates
    multi_rent_res = await client.post(
        "/api/v1/rentals",
        headers=f1_headers,
        json={
            "equipmentId": eq_id,
            "rentalDate": d1,
            "selectedDates": [d1, d2, d3],
            "durationUnits": 3,
            "note": "৩ দিনের জন্য ধান কাটার চুক্তি",
        },
    )
    assert multi_rent_res.status_code == 201
    rental_data = multi_rent_res.json()
    assert rental_data["durationUnits"] == 3
    assert rental_data["totalEstimatedPrice"] == 9000  # 3000 * 3
    rental_id = rental_data["id"]

    # 3. Owner accepts multi-date rental
    accept_res = await client.patch(
        f"/api/v1/rentals/{rental_id}/status",
        headers=owner_headers,
        json={"targetStatus": "accepted"},
    )
    assert accept_res.status_code == 200

    # 4. Check availability calendar -> all 3 dates must be marked as booked
    avail_res = await client.get(f"/api/v1/equipment/{eq_id}/availability")
    assert avail_res.status_code == 200
    booked_dates = [b["rentalDate"] for b in avail_res.json()["bookedDates"]]
    assert d1 in booked_dates
    assert d2 in booked_dates
    assert d3 in booked_dates

    # 5. Farmer 2 attempts to book including d2 -> must fail with DATE_ALREADY_BOOKED
    d_other = (date.today() + timedelta(days=13)).isoformat()
    conflict_res = await client.post(
        "/api/v1/rentals",
        headers=f2_headers,
        json={
            "equipmentId": eq_id,
            "rentalDate": d2,
            "selectedDates": [d2, d_other],
            "durationUnits": 2,
        },
    )
    assert conflict_res.status_code == 400
    assert conflict_res.json()["error"]["code"] == "DATE_ALREADY_BOOKED"

    # 6. Farmer 2 books non-conflicting dates -> succeeds
    d4 = (date.today() + timedelta(days=14)).isoformat()
    d5 = (date.today() + timedelta(days=15)).isoformat()
    ok_res = await client.post(
        "/api/v1/rentals",
        headers=f2_headers,
        json={
            "equipmentId": eq_id,
            "rentalDate": d4,
            "selectedDates": [d4, d5],
            "durationUnits": 2,
        },
    )
    assert ok_res.status_code == 201

