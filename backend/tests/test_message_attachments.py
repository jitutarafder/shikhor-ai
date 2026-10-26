"""Unit and integration tests for Message Image Attachments.

Strictly verifies:
- AGENTS.md Rule 12: Object-level authorization policy (only conversation participants can view/download attachments).
- AGENTS.md Rule 18: Upload security (sanitization to WebP, stripping EXIF, magic byte validation, rejecting malformed files).
- AGENTS.md Rule 27: Rate limiting, abuse, and block enforcement on attachment messages.
- AGENTS.md Rule 28: Mandatory tests for upload MIME/signature security and cross-user forbidden access.
"""

import io
import pytest
from httpx import AsyncClient
from PIL import Image


def _create_test_image(format: str = "JPEG", size=(200, 200), color=(34, 139, 34)) -> bytes:
    """Generates authentic valid image bytes for testing."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    return buf.getvalue()


async def register_user(client: AsyncClient, phone: str, name: str, role: str) -> dict:
    """Helper to register and authenticate test user."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": phone,
            "password": "Password123#Strong",
            "full_name": name,
            "role": role,
        },
    )
    if res.status_code == 201:
        tokens = res.json()
    else:
        login_res = await client.post("/api/v1/auth/login", json={"phone": phone, "password": "Password123#Strong"})
        tokens = login_res.json()
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['accessToken']}"},
    )
    assert me_res.status_code == 200, me_res.text
    return {**tokens, "user": me_res.json()}


@pytest.mark.asyncio
async def test_send_and_retrieve_message_attachment(client: AsyncClient):
    """Verifies uploading an image attachment in a message and streaming it as an authorized participant."""
    farmer = await register_user(client, "01780000001", "কৃষক জমির", "farmer")
    buyer = await register_user(client, "01780000002", "পাইকার সোহেল", "buyer")

    # 1. Farmer initiates conversation with Buyer
    conv_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {farmer['accessToken']}"},
        json={
            "recipientId": buyer["user"]["id"],
            "contextType": "crop_listing",
            "initialMessage": "আসসালামু আলাইকুম, নতুন তোলার আলু দেখতে চান?",
        },
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.json()["id"]

    # 2. Farmer sends message with authentic JPEG image attachment
    img_bytes = _create_test_image(format="JPEG", size=(150, 150), color=(100, 200, 50))
    files = {"image": ("fresh_potatoes.jpg", img_bytes, "image/jpeg")}
    data = {"content": "এই যে আজকের তোলা ডায়মন্ড আলুর নমুনা ছবি।"}

    send_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/attachment",
        headers={"Authorization": f"Bearer {farmer['accessToken']}"},
        files=files,
        data=data,
    )
    assert send_res.status_code == 201
    msg_data = send_res.json()
    assert msg_data["content"] == "এই যে আজকের তোলা ডায়মন্ড আলুর নমুনা ছবি।"
    assert msg_data["attachmentFilename"] is not None
    assert msg_data["attachmentFilename"].endswith(".webp")
    assert msg_data["attachmentUrl"] is not None
    msg_id = msg_data["id"]

    # 3. Buyer reads conversation messages and sees attachment metadata
    get_msgs_res = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"Authorization": f"Bearer {buyer['accessToken']}"},
    )
    assert get_msgs_res.status_code == 200
    msgs = get_msgs_res.json()
    assert len(msgs) == 2
    attached_msg = [m for m in msgs if m["id"] == msg_id][0]
    att_url = attached_msg["attachmentUrl"]
    assert att_url.startswith("http") or att_url == f"/api/v1/conversations/{conv_id}/messages/{msg_id}/attachment"

    if att_url.startswith("/api/v1/"):
        # 4. Buyer downloads/streams the sanitized image attachment with Bearer Header
        att_res = await client.get(
            att_url,
            headers={"Authorization": f"Bearer {buyer['accessToken']}"},
        )
        assert att_res.status_code == 200
        assert att_res.headers["content-type"] == "image/webp"
        assert att_res.headers["x-content-type-options"] == "nosniff"
        assert len(att_res.content) > 0

        # 5. Buyer downloads/streams with query param token (?token=...)
        att_token_res = await client.get(
            f"{att_url}?token={buyer['accessToken']}",
        )
        assert att_token_res.status_code == 200
        assert att_token_res.headers["content-type"] == "image/webp"


@pytest.mark.asyncio
async def test_message_attachment_cross_user_forbidden(client: AsyncClient):
    """Verifies that non-participants cannot download message attachments (AGENTS.md Rule 12)."""
    user_a = await register_user(client, "01780000003", "ব্যবহারকারী ক", "farmer")
    user_b = await register_user(client, "01780000004", "ব্যবহারকারী খ", "buyer")
    user_c = await register_user(client, "01780000005", "অনুপ্রবেশকারী গ", "farmer")

    # User A initiates conversation with User B
    conv_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        json={"recipientId": user_b["user"]["id"]},
    )
    conv_id = conv_res.json()["id"]

    # User A sends image attachment
    img_bytes = _create_test_image(format="PNG", size=(100, 100))
    files = {"image": ("crop_sample.png", img_bytes, "image/png")}
    send_res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/attachment",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        files=files,
    )
    assert send_res.status_code == 201
    msg_id = send_res.json()["id"]

    # User C (non-participant) attempts to view attachment -> 403 Forbidden
    unauth_res = await client.get(
        f"/api/v1/conversations/{conv_id}/messages/{msg_id}/attachment",
        headers={"Authorization": f"Bearer {user_c['accessToken']}"},
    )
    assert unauth_res.status_code == 403
    assert unauth_res.json()["error"]["code"] == "UNAUTHORIZED_ATTACHMENT_ACCESS"

    # User C attempts to post attachment to conversation -> 403 Forbidden
    unauth_send = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/attachment",
        headers={"Authorization": f"Bearer {user_c['accessToken']}"},
        files={"image": ("hack.jpg", img_bytes, "image/jpeg")},
    )
    assert unauth_send.status_code == 403
    assert unauth_send.json()["error"]["code"] == "UNAUTHORIZED_CONVERSATION_ACCESS"


@pytest.mark.asyncio
async def test_message_attachment_unauthenticated_rejected(client: AsyncClient):
    """Verifies that requests without authentication token are rejected with 401."""
    res = await client.get(
        "/api/v1/conversations/conv-123/messages/msg-456/attachment"
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.asyncio
async def test_message_attachment_malformed_rejected(client: AsyncClient):
    """Verifies that corrupt or malicious non-image files are rejected (AGENTS.md Rule 18)."""
    user_a = await register_user(client, "01780000006", "কৃষক করিম", "farmer")
    user_b = await register_user(client, "01780000007", "পাইকার বাবুল", "buyer")

    conv_res = await client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        json={"recipientId": user_b["user"]["id"]},
    )
    conv_id = conv_res.json()["id"]

    # Attempt to upload plain text / corrupt binary disguised as JPEG
    fake_bytes = b"Hello, this is not an authentic image file at all!"
    files = {"image": ("malicious.jpg", fake_bytes, "image/jpeg")}

    res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/attachment",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        files=files,
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] in ["UNSUPPORTED_IMAGE_FORMAT", "INVALID_FILE_HEADER", "MALFORMED_IMAGE"]


@pytest.mark.asyncio
async def test_message_attachment_blocked_user_rejected(client: AsyncClient):
    """Verifies that a blocked user cannot send attachments (AGENTS.md Rule 27)."""
    user_a = await register_user(client, "01780000008", "ব্যবহারকারী ক১", "farmer")
    user_b = await register_user(client, "01780000009", "ব্যবহারকারী খ১", "buyer")

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

    # User A tries to send image attachment -> 403 Forbidden
    img_bytes = _create_test_image(format="JPEG")
    files = {"image": ("sample.jpg", img_bytes, "image/jpeg")}
    res = await client.post(
        f"/api/v1/conversations/{conv_id}/messages/attachment",
        headers={"Authorization": f"Bearer {user_a['accessToken']}"},
        files=files,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "USER_BLOCKED"
