"""Integration tests for Saved Buyer Searches and Notifications (Later Roadmap).

Strictly complies with:
- AGENTS.md Rule 11: Backend validation is authoritative.
- AGENTS.md Rule 12: Object-level ownership (buyers access only their own saved searches and notifications).
- AGENTS.md Rule 28: Mandatory integration test suite for security and business logic.
"""

from datetime import date, timedelta
import pytest
from httpx import AsyncClient


async def register_user(client: AsyncClient, phone: str, name: str, role: str) -> dict:
    """Helper to register and obtain auth token and profile."""
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
async def test_saved_buyer_search_and_notifications_flow(client: AsyncClient):
    """End-to-end test verifying:
    1. Buyer saves a search filter.
    2. Other buyers cannot see or delete that search (Rule 12).
    3. New matching crop listings automatically trigger notifications.
    4. Non-matching crop listings do not trigger notifications.
    5. Read status and unread count update correctly.
    """
    buyer = await register_user(client, "01788000001", "ক্রেতা আনিস", "buyer")
    buyer2 = await register_user(client, "01788000002", "ক্রেতা করিম", "buyer")
    farmer = await register_user(client, "01788000003", "কৃষক মহসিন", "farmer")

    b1_headers = {"Authorization": f"Bearer {buyer['accessToken']}"}
    b2_headers = {"Authorization": f"Bearer {buyer2['accessToken']}"}
    f_headers = {"Authorization": f"Bearer {farmer['accessToken']}"}

    # 1. Buyer 1 saves a search for Potato in Bogura under 1500 BDT
    create_search_res = await client.post(
        "/api/v1/crop-listings/saved-searches",
        headers=b1_headers,
        json={
            "name": "বগুড়ার ডায়মন্ড আলু",
            "category": "potato",
            "cropName": "আলু",
            "district": "বগুড়া",
            "maxPrice": 1500,
            "minQuantity": 20,
        },
    )
    assert create_search_res.status_code == 201, create_search_res.text
    search_data = create_search_res.json()
    assert search_data["name"] == "বগুড়ার ডায়মন্ড আলু"
    assert search_data["category"] == "potato"
    assert search_data["maxPrice"] == 1500
    search_id = search_data["id"]

    # 2. Buyer 1 lists saved searches -> finds 1 item
    list1_res = await client.get("/api/v1/crop-listings/saved-searches", headers=b1_headers)
    assert list1_res.status_code == 200
    assert len(list1_res.json()) == 1
    assert list1_res.json()[0]["id"] == search_id

    # 3. Buyer 2 lists saved searches -> empty (strict user isolation)
    list2_res = await client.get("/api/v1/crop-listings/saved-searches", headers=b2_headers)
    assert list2_res.status_code == 200
    assert len(list2_res.json()) == 0

    # 4. Buyer 2 attempts to delete Buyer 1's saved search -> 403 Forbidden
    del_unauth = await client.delete(
        f"/api/v1/crop-listings/saved-searches/{search_id}",
        headers=b2_headers,
    )
    assert del_unauth.status_code == 403

    # 5. Initially, Buyer 1 has 0 notifications
    unread_res0 = await client.get("/api/v1/notifications/unread-count", headers=b1_headers)
    assert unread_res0.status_code == 200
    assert unread_res0.json()["unreadCount"] == 0

    # 6. Farmer creates a non-matching crop (Paddy in Dinajpur)
    non_match_res = await client.post(
        "/api/v1/crop-listings",
        headers=f_headers,
        json={
            "crop_name": "আমন ধান",
            "category": "paddy",
            "quantity": 100.0,
            "quantity_unit": "maund",
            "price_per_unit": 1100,
            "expected_harvest_date": (date.today() + timedelta(days=15)).isoformat(),
            "district": "দিনাজপুর",
            "upazila": "কাহারোল",
            "latitude": 25.79,
            "longitude": 88.60,
            "description": "উন্নত মানের ধান",
        },
    )
    assert non_match_res.status_code == 201

    # Buyer 1 still has 0 notifications
    unread_res1 = await client.get("/api/v1/notifications/unread-count", headers=b1_headers)
    assert unread_res1.json()["unreadCount"] == 0

    # 7. Farmer creates a MATCHING crop (Potato in Bogura at 1200 BDT)
    match_res = await client.post(
        "/api/v1/crop-listings",
        headers=f_headers,
        json={
            "crop_name": "ডায়মন্ড গোল আলু",
            "category": "potato",
            "quantity": 80.0,
            "quantity_unit": "maund",
            "price_per_unit": 1200,
            "expected_harvest_date": (date.today() + timedelta(days=5)).isoformat(),
            "district": "বগুড়া",
            "upazila": "শিবগঞ্জ",
            "latitude": 24.95,
            "longitude": 89.33,
            "description": "তাজা ডায়মন্ড আলু সরাসরি জমি থেকে",
        },
    )
    assert match_res.status_code == 201

    # 8. Buyer 1 receives notification!
    unread_res2 = await client.get("/api/v1/notifications/unread-count", headers=b1_headers)
    assert unread_res2.status_code == 200
    assert unread_res2.json()["unreadCount"] == 1

    # Check notification details
    notifs_res = await client.get("/api/v1/notifications", headers=b1_headers)
    assert notifs_res.status_code == 200
    notifs = notifs_res.json()
    assert len(notifs) == 1
    notif = notifs[0]
    assert notif["notificationType"] == "crop_match"
    assert "বগুড়ার ডায়মন্ড আলু" in notif["message"]
    assert notif["isRead"] is False
    notif_id = notif["id"]

    # 9. Buyer 2 should NOT have received this notification
    b2_unread = await client.get("/api/v1/notifications/unread-count", headers=b2_headers)
    assert b2_unread.json()["unreadCount"] == 0

    # 10. Buyer 2 cannot mark Buyer 1's notification as read -> 403 Forbidden
    cross_read = await client.patch(
        f"/api/v1/notifications/{notif_id}/read",
        headers=b2_headers,
    )
    assert cross_read.status_code == 403

    # 11. Buyer 1 marks notification as read
    read_res = await client.patch(
        f"/api/v1/notifications/{notif_id}/read",
        headers=b1_headers,
    )
    assert read_res.status_code == 200
    assert read_res.json()["isRead"] is True

    # Unread count is now 0
    unread_res3 = await client.get("/api/v1/notifications/unread-count", headers=b1_headers)
    assert unread_res3.json()["unreadCount"] == 0

    # 12. Buyer 1 deletes the saved search -> 204 No Content
    del_ok = await client.delete(
        f"/api/v1/crop-listings/saved-searches/{search_id}",
        headers=b1_headers,
    )
    assert del_ok.status_code == 204

    # Saved searches list is now empty
    final_list = await client.get("/api/v1/crop-listings/saved-searches", headers=b1_headers)
    assert len(final_list.json()) == 0
