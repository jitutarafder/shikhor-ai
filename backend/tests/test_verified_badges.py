"""Tests for Later Roadmap: Verified Owner and Buyer Badges.

Strictly complies with:
- AGENTS.md Rule 12: Object-level authorization policy (admin/moderator only for verification).
- AGENTS.md Rule 15: Transparent ranking formula preserved (65% price / 35% distance; badges are trust indicators only).
- AGENTS.md Rule 26: Error, logging, and audit rules (USER_VERIFIED / USER_UNVERIFIED audit log entries).
- AGENTS.md Rule 28: Mandatory integration test suite for security & business logic.
"""

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
async def test_verification_endpoint_forbidden_for_regular_users(client: AsyncClient):
    """Verifies that non-admin/moderator users cannot toggle verification badges (Rule 12)."""
    farmer = await register_user(client, "01755000001", "সাধারণ কৃষক", "farmer")
    target_owner = await register_user(client, "01755000002", "যন্ত্র মালিক", "owner")

    res = await client.post(
        f"/api/v1/admin/users/{target_owner['user']['id']}/verify",
        headers={"Authorization": f"Bearer {farmer['accessToken']}"},
        json={"isVerified": True, "notes": "নিজে নিজে ব্যাজ নেওয়ার চেষ্টা"},
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN_ROLE"


@pytest.mark.asyncio
async def test_admin_can_verify_and_unverify_user_with_audit_trail(client: AsyncClient):
    """Verifies that admin can award and revoke badges, recording immutable audit logs (Rule 26)."""
    admin = await register_user(client, "01755000010", "প্ল্যাটফর্ম অ্যাডমিন", "admin")
    owner = await register_user(client, "01755000011", "যন্ত্রের মালিক রফিক", "owner")

    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    # 1. Initially unverified
    assert owner["user"]["isVerified"] is False

    # 2. Grant verified badge
    res_verify = await client.post(
        f"/api/v1/admin/users/{owner['user']['id']}/verify",
        headers=admin_headers,
        json={"isVerified": True, "notes": "জাতীয় পরিচয়পত্র ও ট্রেড লাইসেন্স যাচাইকৃত"},
    )
    assert res_verify.status_code == 200, res_verify.text
    user_data = res_verify.json()
    assert user_data["isVerified"] is True

    # 3. Check audit log for USER_VERIFIED
    res_audit = await client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert res_audit.status_code == 200
    logs = res_audit.json()
    verify_log = next((l for l in logs if l["action"] == "USER_VERIFIED" and l["resourceId"] == owner["user"]["id"]), None)
    assert verify_log is not None
    assert "জাতীয় পরিচয়পত্র" in str(verify_log["details"])

    # 4. Revoke badge
    res_revoke = await client.post(
        f"/api/v1/admin/users/{owner['user']['id']}/verify",
        headers=admin_headers,
        json={"isVerified": False, "notes": "অভিযোগ তদন্তের প্রেক্ষিতে ব্যাজ সাময়িক স্থগিত"},
    )
    assert res_revoke.status_code == 200
    assert res_revoke.json()["isVerified"] is False

    # 5. Check audit log for USER_UNVERIFIED
    res_audit2 = await client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert res_audit2.status_code == 200
    logs2 = res_audit2.json()
    unverify_log = next((l for l in logs2 if l["action"] == "USER_UNVERIFIED" and l["resourceId"] == owner["user"]["id"]), None)
    assert unverify_log is not None


@pytest.mark.asyncio
async def test_equipment_listing_reflects_owner_verified_badge(client: AsyncClient):
    """Verifies that equipment search and details endpoints reflect isOwnerVerified and ownerName."""
    admin = await register_user(client, "01755000020", "প্রধান প্রশাসক", "admin")
    owner = await register_user(client, "01755000021", "করিম মেশিনারিজ", "owner")

    owner_headers = {"Authorization": f"Bearer {owner['accessToken']}"}
    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    # Create equipment listing
    create_res = await client.post(
        "/api/v1/equipment",
        headers=owner_headers,
        json={
            "name": "সোনালী কম্বাইন হার্ভেস্টার",
            "equipment_type": "harvester",
            "price_amount": 2500,
            "price_unit": "per_hour",
            "district": "বগুড়া",
            "upazila": "শেরপুর",
            "latitude": 24.67,
            "longitude": 89.42,
            "service_radius_km": 20.0,
            "description": "উন্নত মানের ধান কাটার মেশিন",
        },
    )
    assert create_res.status_code == 201, create_res.text
    eq_id = create_res.json()["id"]

    # Before verification: isOwnerVerified should be False
    search_res = await client.get(
        "/api/v1/equipment",
        params={
            "equipmentType": "harvester",
            "priceUnit": "per_hour",
            "latitude": 24.67,
            "longitude": 89.42,
        },
    )
    assert search_res.status_code == 200
    items = search_res.json()
    matched = next((item for item in items if item["id"] == eq_id), None)
    assert matched is not None
    assert matched["isOwnerVerified"] is False
    assert matched["ownerName"] == "করিম মেশিনারিজ"

    # Admin verifies the owner
    verify_res = await client.post(
        f"/api/v1/admin/users/{owner['user']['id']}/verify",
        headers=admin_headers,
        json={"isVerified": True, "notes": "কৃষি যন্ত্রপাতি মালিকানা সনদ যাচাইকৃত"},
    )
    assert verify_res.status_code == 200

    # After verification: isOwnerVerified should be True in search and get
    search_res2 = await client.get(
        "/api/v1/equipment",
        params={
            "equipmentType": "harvester",
            "priceUnit": "per_hour",
            "latitude": 24.67,
            "longitude": 89.42,
        },
    )
    assert search_res2.status_code == 200
    items2 = search_res2.json()
    matched2 = next((item for item in items2 if item["id"] == eq_id), None)
    assert matched2 is not None
    assert matched2["isOwnerVerified"] is True

    # Check single item get endpoint
    get_res = await client.get(f"/api/v1/equipment/{eq_id}")
    assert get_res.status_code == 200
    assert get_res.json()["isOwnerVerified"] is True


@pytest.mark.asyncio
async def test_crop_listing_reflects_farmer_verified_badge(client: AsyncClient):
    """Verifies that crop marketplace listing reflects isFarmerVerified badge."""
    admin = await register_user(client, "01755000030", "সুপার এডমিন", "admin")
    farmer = await register_user(client, "01755000031", "আমানউল্লাহ কৃষক", "farmer")

    farmer_headers = {"Authorization": f"Bearer {farmer['accessToken']}"}
    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    # Create crop listing
    create_res = await client.post(
        "/api/v1/crop-listings",
        headers=farmer_headers,
        json={
            "crop_name": "আমন সুবাসিত চাল",
            "category": "paddy",
            "quantity": 50.0,
            "quantity_unit": "maund",
            "price_per_unit": 1300,
            "expected_harvest_date": "2026-11-20",
            "district": "দিনাজপুর",
            "upazila": "বীরগঞ্জ",
            "latitude": 25.85,
            "longitude": 88.66,
            "description": "শতভাগ বিষমুক্ত সুগন্ধি ধান",
        },
    )
    assert create_res.status_code == 201, create_res.text
    crop_id = create_res.json()["id"]

    # Before verification: isFarmerVerified should be False
    list_res = await client.get("/api/v1/crop-listings", params={"category": "paddy"})
    assert list_res.status_code == 200
    crop_item = next((c for c in list_res.json() if c["id"] == crop_id), None)
    assert crop_item is not None
    assert crop_item["isFarmerVerified"] is False

    # Admin verifies the farmer
    verify_res = await client.post(
        f"/api/v1/admin/users/{farmer['user']['id']}/verify",
        headers=admin_headers,
        json={"isVerified": True, "notes": "কৃষক কার্ড ও জমি রেকর্ড যাচাই সম্পন্ন"},
    )
    assert verify_res.status_code == 200

    # After verification: isFarmerVerified should be True
    list_res2 = await client.get("/api/v1/crop-listings", params={"category": "paddy"})
    assert list_res2.status_code == 200
    crop_item2 = next((c for c in list_res2.json() if c["id"] == crop_id), None)
    assert crop_item2 is not None
    assert crop_item2["isFarmerVerified"] is True

    # Single crop item endpoint
    get_res = await client.get(f"/api/v1/crop-listings/{crop_id}")
    assert get_res.status_code == 200
    assert get_res.json()["isFarmerVerified"] is True
