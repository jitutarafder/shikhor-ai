"""Tests for Crop Marketplace, Messaging, Object-level Authorization, and Anti-Abuse Controls.

Strictly complies with Phase 6 exit criteria and AGENTS.md:
- Rule 12: Object-level authorization policy (only conversation participants access messages).
- Rule 14: Centralized crop listing state transitions.
- Rule 16: Exact quantities, units, and integer money.
- Rule 17: Approximate coordinate exposure and contact privacy.
- Rule 27: Rate limiting, abuse prevention (blocking, reporting, spam frequency control).
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
async def test_crop_listing_creation_and_privacy_masking(client: AsyncClient):
    """Verifies crop listing creation and that public listings never expose private phone numbers (Phase 6 Exit Criteria)."""
    farmer = await register_user(client, "01720000001", "কৃষক আকবর", "farmer")
    token = farmer["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "cropName": "মিনিকেট ধান",
        "category": "paddy",
        "quantity": 120.0,
        "quantityUnit": "maund",
        "pricePerUnit": 1350,
        "expectedHarvestDate": "2026-10-25",
        "district": "দিনাজপুর",
        "upazila": "বীরগঞ্জ",
        "latitude": 25.8521,  # Exact coordinates
        "longitude": 88.6634,
        "description": "উন্নত মানের শুকনো ধান, আর্দ্রতা ১২%",
    }

    create_res = await client.post("/api/v1/crop-listings", headers=headers, json=payload)
    assert create_res.status_code == 201, create_res.text
    created = create_res.json()

    assert created["cropName"] == "মিনিকেট ধান"
    assert created["category"] == "paddy"
    assert created["quantity"] == 120.0
    assert created["quantityUnit"] == "maund"
    assert created["pricePerUnit"] == 1350
    assert created["status"] == "active"
    # Privacy check (Rule 17)
    assert created["approximateLat"] == 25.85
    assert created["approximateLon"] == 88.66

    # Public search endpoint: Must NOT expose phone or exact coordinates
    public_res = await client.get("/api/v1/crop-listings?category=paddy")
    assert public_res.status_code == 200
    listings = public_res.json()
    assert len(listings) >= 1
    found = next(item for item in listings if item["id"] == created["id"])

    assert "phone" not in found
    assert "latitude" not in found
    assert "longitude" not in found
    assert found["farmerName"] == "কৃষক আকবর"


@pytest.mark.asyncio
async def test_crop_listing_ownership_authorization(client: AsyncClient):
    """Verifies that only the listing creator can modify or close it (Rule 12)."""
    farmer_a = await register_user(client, "01720000002", "কৃষক ১", "farmer")
    buyer_b = await register_user(client, "01720000003", "পাইকার ১", "buyer")

    # Farmer A creates listing
    create_res = await client.post(
        "/api/v1/crop-listings",
        headers={"Authorization": f"Bearer {farmer_a['accessToken']}"},
        json={
            "cropName": "ডায়মন্ড আলু",
            "category": "potato",
            "quantity": 50.0,
            "quantityUnit": "maund",
            "pricePerUnit": 800,
            "expectedHarvestDate": "2026-11-01",
            "district": "মুন্সীগঞ্জ",
            "upazila": "টঙ্গীবাড়ি",
            "latitude": 23.50,
            "longitude": 90.45,
        },
    )
    listing_id = create_res.json()["id"]

    # Buyer B attempts to modify Farmer A's listing -> 403 Forbidden
    unauth_res = await client.patch(
        f"/api/v1/crop-listings/{listing_id}",
        headers={"Authorization": f"Bearer {buyer_b['accessToken']}"},
        json={"pricePerUnit": 500},
    )
    assert unauth_res.status_code == 403
    assert unauth_res.json()["error"]["code"] == "FORBIDDEN_CROP_UPDATE"

    # Farmer A updates own listing -> 200 OK
    auth_res = await client.patch(
        f"/api/v1/crop-listings/{listing_id}",
        headers={"Authorization": f"Bearer {farmer_a['accessToken']}"},
        json={"pricePerUnit": 850, "status": "paused"},
    )
    assert auth_res.status_code == 200
    assert auth_res.json()["pricePerUnit"] == 850
    assert auth_res.json()["status"] == "paused"


@pytest.mark.asyncio
async def test_conversation_participant_authorization(client: AsyncClient):
    """Verifies that only conversation participants can view and post messages (Phase 6 Exit Criteria)."""
    user_a = await register_user(client, "01720000004", "কৃষক রফিক", "farmer")
    user_b = await register_user(client, "01720000005", "পাইকার জলিল", "buyer")
    user_c = await register_user(client, "01720000006", "অনাহূত ব্যক্তি", "farmer")

    # User A initiates conversation with User B
    conv_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        json={
            "recipientId": user_b["user"]["id"],
            "contextType": "crop_listing",
            "initialMessage": "আসসালামু আলাইকুম, আলু কি এখনো অবশিষ্ট আছে?",
        },
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # User C (non-participant) attempts to view messages -> 403 Forbidden
    unauth_get = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_c['accessToken']}"},
    )
    assert unauth_get.status_code == 403
    assert unauth_get.json()["error"]["code"] == "UNAUTHORIZED_CONVERSATION_ACCESS"

    # User C attempts to post a message -> 403 Forbidden
    unauth_post = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_c['accessToken']}"},
        json={"content": "আমিও অংশ নিতে চাই"},
    )
    assert unauth_post.status_code == 403
    assert unauth_post.json()["error"]["code"] == "UNAUTHORIZED_CONVERSATION_ACCESS"

    # Participant User B views messages -> 200 OK
    auth_get = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_b['accessToken']}"},
    )
    assert auth_get.status_code == 200
    messages = auth_get.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "আসসালামু আলাইকুম, আলু কি এখনো অবশিষ্ট আছে?"
    assert messages[0]["senderName"] == "কৃষক রফিক"

    # Participant User B replies -> 201 Created
    auth_reply = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_b['accessToken']}"},
        json={"content": "জি ভাই, ৩০ মন আলু মজুদ আছে।"},
    )
    assert auth_reply.status_code == 201
    assert auth_reply.json()["content"] == "জি ভাই, ৩০ মন আলু মজুদ আছে।"


@pytest.mark.asyncio
async def test_user_blocking_and_moderation_reporting(client: AsyncClient):
    """Verifies that blocking a user prevents them from sending messages, and moderation reports work (Phase 6 Exit Criteria)."""
    user_a = await register_user(client, "01720000007", "ব্যবহারকারী ক", "farmer")
    user_b = await register_user(client, "01720000008", "ব্যবহারকারী খ", "buyer")

    # Start conversation
    conv_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        json={"recipientId": user_b["user"]["id"]},
    )
    conv_id = conv_res.json()["id"]

    # User B blocks User A
    block_res = await client.post(
        "/api/v1/users/block",
        headers={"Authorization": f"Bearer {user_b['accessToken']}"},
        json={"targetUserId": user_a["user"]["id"]},
    )
    assert block_res.status_code == 200

    # User A tries to send a message to User B -> 403 Forbidden (USER_BLOCKED)
    blocked_send = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        json={"content": "হ্যালো, শুনতে পাচ্ছেন?"},
    )
    assert blocked_send.status_code == 403
    assert blocked_send.json()["error"]["code"] == "USER_BLOCKED"

    # User B reports User A for inappropriate behavior
    report_res = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {user_b['accessToken']}"},
        json={
            "reportedUserId": user_a["user"]["id"],
            "contentType": "user",
            "contentId": user_a["user"]["id"],
            "reason": "স্প্যাম বা অপ্রাসঙ্গিক বার্তা",
            "details": "বারবার অযাচিত বার্তা প্রেরণ করছিলেন।",
        },
    )
    assert report_res.status_code == 201
    report_data = report_res.json()
    assert report_data["status"] == "pending"
    assert report_data["reason"] == "স্প্যাম বা অপ্রাসঙ্গিক বার্তা"


@pytest.mark.asyncio
async def test_anti_spam_message_rate_control(client: AsyncClient):
    """Verifies anti-spam limit triggers 429 when messages are sent in rapid burst (Rule 27)."""
    user_a = await register_user(client, "01720000009", "দ্রুত বার্তা প্রেরক", "farmer")
    user_b = await register_user(client, "01720000010", "প্রাপক", "buyer")

    conv_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        json={"recipientId": user_b["user"]["id"]},
    )
    conv_id = conv_res.json()["id"]

    # Send 10 messages rapidly
    for i in range(10):
        res = await client.post(
            f"/api/v1/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {user_a['accessToken']}"},
            json={"content": f"বার্তা নম্বর {i+1}"},
        )
        assert res.status_code == 201

    # 11th message within 60s -> Rate limit exceeded (429)
    spam_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        json={"content": "বার্তা নম্বর ১১ (স্প্যাম)"},
    )
    assert spam_res.status_code == 429
    assert spam_res.json()["error"]["code"] == "MESSAGE_RATE_LIMIT_EXCEEDED"
