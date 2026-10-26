"""Tests for Phase 7: Offline Knowledge Library and Idempotent Synchronization.

Strictly complies with:
- AGENTS.md Rule 11: Authoritative backend validation.
- AGENTS.md Rule 21: Offline synchronization must be idempotent.
- AGENTS.md Rule 21: Bind idempotency records to user, operation, and request-body hash.
- AGENTS.md Rule 28: Tests required for business and security logic.
- phases.md Phase 7 Exit Criteria:
  - Offline UI never reports server success prematurely.
  - Queued requests/messages synchronize without duplication.
  - Previously downloaded knowledge shows version/date.
"""

import uuid
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
async def test_knowledge_library_catalog_and_versioning(client: AsyncClient):
    """Verifies that agricultural knowledge articles are accessible with version tracking (Phase 7 Exit Criteria)."""
    res = await client.get("/api/v1/knowledge")
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["totalCount"] >= 4
    assert data["latestVersion"] >= 1
    assert "syncedAt" in data

    # Check structure of articles
    first = data["articles"][0]
    assert "id" in first
    assert "cropType" in first
    assert "category" in first
    assert "titleBn" in first
    assert "summaryBn" in first
    assert "contentBn" in first
    assert "version" in first
    assert "publishedAt" in first

    # Test filtering by cropType
    paddy_res = await client.get("/api/v1/knowledge?crop_type=paddy")
    assert paddy_res.status_code == 200
    paddy_data = paddy_res.json()
    for art in paddy_data["articles"]:
        assert art["cropType"] == "paddy"

    # Test incremental sync: querying with since_version higher than current yields 0 articles
    future_res = await client.get(f"/api/v1/knowledge?since_version={data['latestVersion'] + 10}")
    assert future_res.status_code == 200
    assert future_res.json()["totalCount"] == 0


@pytest.mark.asyncio
async def test_idempotent_offline_sync_batch_creation(client: AsyncClient):
    """Verifies that an offline-queued crop listing executes successfully via /sync/batch."""
    farmer = await register_user(client, "01730000001", "অফলাইন কৃষক", "farmer")
    token = farmer["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    local_uuid = str(uuid.uuid4())
    idempotency_key = f"offline-crop-{uuid.uuid4()}"

    batch_payload = {
        "mutations": [
            {
                "localUuid": local_uuid,
                "idempotencyKey": idempotency_key,
                "operationName": "CREATE_CROP_LISTING",
                "payload": {
                    "cropName": "বোরো ধান ব্রি-২৮",
                    "category": "paddy",
                    "quantity": 80.0,
                    "quantityUnit": "maund",
                    "pricePerUnit": 1250,
                    "expectedHarvestDate": "2026-10-25",
                    "district": "বগুড়া",
                    "upazila": "শেরপুর",
                    "latitude": 24.67,
                    "longitude": 89.42,
                    "description": "অফলাইনে সংরক্ষিত সফল সিঙ্ক",
                },
            }
        ]
    }

    res = await client.post("/api/v1/sync/batch", headers=headers, json=batch_payload)
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["syncedCount"] == 1, body
    assert body["failedCount"] == 0
    result = body["results"][0]
    assert result["localUuid"] == local_uuid
    assert result["status"] == "success"
    assert result["statusCode"] == 201
    assert result["data"]["cropName"] == "বোরো ধান ব্রি-২৮"


@pytest.mark.asyncio
async def test_duplicate_sync_retry_returns_cached_response_without_duplication(
    client: AsyncClient,
):
    """Verifies that resubmitting the identical idempotency key returns the cached response without creating duplicate records (Rule 21)."""
    farmer = await register_user(client, "01730000002", "পুনরাবৃত্তি পরীক্ষক", "farmer")
    token = farmer["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    local_uuid = str(uuid.uuid4())
    idempotency_key = f"offline-dup-{uuid.uuid4()}"

    payload = {
        "cropName": "বারি আলু-৭",
        "category": "potato",
        "quantity": 200.0,
        "quantityUnit": "kg",
        "pricePerUnit": 40,
        "expectedHarvestDate": "2026-11-10",
        "district": "রংপুর",
        "upazila": "মিঠাপুকুর",
        "latitude": 25.58,
        "longitude": 89.28,
    }

    batch_payload = {
        "mutations": [
            {
                "localUuid": local_uuid,
                "idempotencyKey": idempotency_key,
                "operationName": "CREATE_CROP_LISTING",
                "payload": payload,
            }
        ]
    }

    # First attempt: Fresh execution
    res1 = await client.post("/api/v1/sync/batch", headers=headers, json=batch_payload)
    assert res1.status_code == 200
    created_id = res1.json()["results"][0]["data"]["id"]

    # Second attempt: Duplicate retry (e.g. network reconnection replay)
    res2 = await client.post("/api/v1/sync/batch", headers=headers, json=batch_payload)
    assert res2.status_code == 200
    body2 = res2.json()

    assert body2["syncedCount"] == 1
    assert body2["failedCount"] == 0
    res2_item = body2["results"][0]
    assert res2_item["status"] == "success"
    assert res2_item["data"]["id"] == created_id  # Identical entity returned

    # Verify that only 1 listing exists for this farmer in database
    my_listings = await client.get("/api/v1/crop-listings/my", headers=headers)
    assert my_listings.status_code == 200
    assert len(my_listings.json()) == 1


@pytest.mark.asyncio
async def test_idempotency_payload_conflict_detection(client: AsyncClient):
    """Verifies that using the same idempotency key with a DIFFERENT payload triggers 409 Conflict (Rule 21)."""
    farmer = await register_user(client, "01730000003", "দ্বন্দ্ব পরীক্ষক", "farmer")
    token = farmer["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    idempotency_key = f"offline-conflict-{uuid.uuid4()}"

    # First attempt with payload A
    payload_a = {
        "cropName": "গম কাঞ্চন",
        "category": "wheat",
        "quantity": 50.0,
        "quantityUnit": "maund",
        "pricePerUnit": 1400,
        "expectedHarvestDate": "2026-12-01",
        "district": "রাজশাহী",
        "upazila": "পুঠিয়া",
        "latitude": 24.37,
        "longitude": 88.84,
    }
    await client.post(
        "/api/v1/sync/batch",
        headers=headers,
        json={
            "mutations": [
                {
                    "localUuid": str(uuid.uuid4()),
                    "idempotencyKey": idempotency_key,
                    "operationName": "CREATE_CROP_LISTING",
                    "payload": payload_a,
                }
            ]
        },
    )

    # Second attempt with same idempotency key but different payload B (different price)
    payload_b = {**payload_a, "pricePerUnit": 9999}
    res_conflict = await client.post(
        "/api/v1/sync/batch",
        headers=headers,
        json={
            "mutations": [
                {
                    "localUuid": str(uuid.uuid4()),
                    "idempotencyKey": idempotency_key,
                    "operationName": "CREATE_CROP_LISTING",
                    "payload": payload_b,
                }
            ]
        },
    )
    assert res_conflict.status_code == 200
    body = res_conflict.json()
    assert body["failedCount"] == 1
    assert body["results"][0]["status"] == "conflict"
    assert body["results"][0]["statusCode"] == 409
    assert body["results"][0]["code"] == "IDEMPOTENCY_CONFLICT"


@pytest.mark.asyncio
async def test_cross_user_idempotency_isolation(client: AsyncClient):
    """Verifies that an idempotency key used by User A does not conflict or block User B (Rule 12 & 21)."""
    user_a = await register_user(client, "01730000004", "কৃষক এ", "farmer")
    user_b = await register_user(client, "01730000005", "কৃষক বি", "farmer")

    common_key = "static-client-timestamp-key-12345"

    payload_a = {
        "cropName": "মরিচ",
        "category": "spice",
        "quantity": 10.0,
        "quantityUnit": "kg",
        "pricePerUnit": 200,
        "expectedHarvestDate": "2026-10-30",
        "district": "বগুড়া",
        "upazila": "বগুড়া সদর",
        "latitude": 24.85,
        "longitude": 89.37,
    }

    # User A syncs with common_key
    res_a = await client.post(
        "/api/v1/sync/batch",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        json={
            "mutations": [
                {
                    "localUuid": str(uuid.uuid4()),
                    "idempotencyKey": common_key,
                    "operationName": "CREATE_CROP_LISTING",
                    "payload": payload_a,
                }
            ]
        },
    )
    assert res_a.status_code == 200
    assert res_a.json()["results"][0]["status"] == "success"

    # User B syncs with SAME common_key and different crop
    payload_b = {
        "cropName": "সরিষা",
        "category": "other",
        "quantity": 15.0,
        "quantityUnit": "kg",
        "pricePerUnit": 110,
        "expectedHarvestDate": "2026-11-05",
        "district": "নাটোর",
        "upazila": "সিংড়া",
        "latitude": 24.50,
        "longitude": 89.15,
    }
    res_b = await client.post(
        "/api/v1/sync/batch",
        headers={"Authorization": f"Bearer {user_b['accessToken']}"},
        json={
            "mutations": [
                {
                    "localUuid": str(uuid.uuid4()),
                    "idempotencyKey": common_key,
                    "operationName": "CREATE_CROP_LISTING",
                    "payload": payload_b,
                }
            ]
        },
    )
    assert res_b.status_code == 200
    assert res_b.json()["results"][0]["status"] == "success"
    assert res_b.json()["results"][0]["data"]["cropName"] == "সরিষা"


@pytest.mark.asyncio
async def test_invalid_mutation_handled_gracefully_in_batch(client: AsyncClient):
    """Verifies that an invalid payload in a batch does not fail valid mutations or crash the server (Rule 11)."""
    farmer = await register_user(client, "01730000006", "মিশ্র ব্যাচ পরীক্ষক", "farmer")
    token = farmer["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    valid_uuid = str(uuid.uuid4())
    invalid_uuid = str(uuid.uuid4())

    batch_payload = {
        "mutations": [
            {
                "localUuid": valid_uuid,
                "idempotencyKey": f"valid-key-{uuid.uuid4()}",
                "operationName": "CREATE_CROP_LISTING",
                "payload": {
                    "cropName": "সুগন্ধি কাটারিভোগ",
                    "category": "paddy",
                    "quantity": 30.0,
                    "quantityUnit": "maund",
                    "pricePerUnit": 1800,
                    "expectedHarvestDate": "2026-11-15",
                    "district": "দিনাজপুর",
                    "upazila": "দিনাজপুর সদর",
                    "latitude": 25.62,
                    "longitude": 88.63,
                },
            },
            {
                "localUuid": invalid_uuid,
                "idempotencyKey": f"invalid-key-{uuid.uuid4()}",
                "operationName": "CREATE_CROP_LISTING",
                "payload": {
                    "cropName": "",  # Invalid: empty crop name
                    "category": "paddy",
                    "quantity": -5.0,  # Invalid: negative quantity
                    "quantityUnit": "maund",
                    "pricePerUnit": 0,
                    "district": "",
                    "upazila": "",
                    "latitude": 0.0,
                    "longitude": 0.0,
                },
            },
        ]
    }

    res = await client.post("/api/v1/sync/batch", headers=headers, json=batch_payload)
    assert res.status_code == 200
    body = res.json()

    assert body["syncedCount"] == 1
    assert body["failedCount"] == 1

    valid_res = next(r for r in body["results"] if r["localUuid"] == valid_uuid)
    assert valid_res["status"] == "success"

    invalid_res = next(r for r in body["results"] if r["localUuid"] == invalid_uuid)
    assert invalid_res["status"] == "error"
    assert invalid_res["statusCode"] == 422
