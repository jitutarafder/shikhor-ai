"""Tests for manual NID photo upload, registration, and admin review workflow.
Complies with AGENTS.md:
- Rule 11: Authoritative backend validation
- Rule 12: Object-level & role authorization (Admin/Moderator only)
- Rule 18: Image validation & sanitization
- Rule 26: Immutable audit logs
- Rule 28: Mandatory tests
"""

import io
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
async def test_upload_nid_image_valid(client: AsyncClient):
    """Uploading a valid JPEG image succeeds and returns file path."""
    from PIL import Image

    buf = io.BytesIO()
    img = Image.new("RGB", (50, 50), color="green")
    img.save(buf, format="JPEG")
    valid_image_bytes = buf.getvalue()

    files = {"file": ("nid_card.jpg", io.BytesIO(valid_image_bytes), "image/jpeg")}

    res = await client.post("/api/v1/auth/upload-nid-image", files=files)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "fileUrl" in data
    assert data["fileUrl"].startswith("/uploads/nid/") or data["fileUrl"].startswith("http")
    assert "nid_" in data["filename"]


@pytest.mark.asyncio
async def test_upload_nid_image_invalid_type_rejected(client: AsyncClient):
    """Uploading an unapproved file type (e.g. text/plain or executable) is rejected with INVALID_FILE_TYPE."""
    files = {"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00\x03"), "application/x-msdownload")}
    res = await client.post("/api/v1/auth/upload-nid-image", files=files)
    assert res.status_code == 400
    err = res.json()
    assert err["error"]["code"] == "INVALID_FILE_TYPE"


@pytest.mark.asyncio
async def test_register_with_nid_photos_and_dob(client: AsyncClient):
    """Farmer registers with NID number, DOB, and front/back photos."""
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "01755112233",
            "password": "SecurePassword123!",
            "full_name": "রহিম মিয়া",
            "nid": "1990123456789",
            "dob": "1990-05-15",
            "nid_front_image": "/uploads/nid/front_sample.jpg",
            "nid_back_image": "/uploads/nid/back_sample.jpg",
            "role": "farmer",
        },
    )
    assert res.status_code == 201, res.text
    token = res.json()["accessToken"]

    # Verify profile data via /me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["nid"] == "1990123456789"
    assert user_data["dob"] == "1990-05-15"
    assert user_data["nidFrontImage"] == "/uploads/nid/front_sample.jpg"
    assert user_data["nidBackImage"] == "/uploads/nid/back_sample.jpg"
    assert user_data["isNidVerified"] is False
    assert user_data["nidVerificationStatus"] == "pending"


@pytest.mark.asyncio
async def test_admin_review_nid_approve_flow(client: AsyncClient):
    """Admin reviews and approves a farmer's NID verification."""
    # 1. Register admin and farmer
    admin = await register_user(client, "01999999999", "প্রধান প্রশাসক", "admin")
    admin_token = admin["accessToken"]

    farmer_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "01788223344",
            "password": "SecurePassword123!",
            "full_name": "করিম উদ্দিন",
            "nid": "1234567890",
            "dob": "1988-10-20",
            "nid_front_image": "/uploads/nid/front_karim.jpg",
            "nid_back_image": "/uploads/nid/back_karim.jpg",
            "role": "farmer",
        },
    )
    assert farmer_res.status_code == 201
    farmer_token = farmer_res.json()["accessToken"]

    # Get farmer id via /me
    me_res_initial = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    farmer_id = me_res_initial.json()["id"]

    # 2. Regular farmer cannot access admin verification list (Rule 12)
    unauth_res = await client.get(
        "/api/v1/admin/nid-verifications",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert unauth_res.status_code == 403

    # 3. Admin retrieves pending NID list
    list_res = await client.get(
        "/api/v1/admin/nid-verifications?status=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_res.status_code == 200
    pending_list = list_res.json()
    assert any(u["id"] == farmer_id for u in pending_list)

    # 4. Admin approves NID
    review_res = await client.post(
        f"/api/v1/admin/nid-verifications/{farmer_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"action": "approve"},
    )
    assert review_res.status_code == 200
    review_data = review_res.json()
    assert review_data["isNidVerified"] is True
    assert review_data["nidVerificationStatus"] == "approved"
    assert review_data["isVerified"] is True

    # 5. Farmer's /me profile reflects approved status
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["isNidVerified"] is True
    assert me_res.json()["nidVerificationStatus"] == "approved"


@pytest.mark.asyncio
async def test_admin_review_nid_reject_flow(client: AsyncClient):
    """Admin reviews and rejects a blurry NID with a justification reason."""
    # 1. Register admin and farmer
    admin = await register_user(client, "01999999998", "প্রধান প্রশাসক ২", "admin")
    admin_token = admin["accessToken"]

    farmer_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "01799334455",
            "password": "SecurePassword123!",
            "full_name": "সালাম মিয়া",
            "nid": "5555666677",
            "dob": "1995-03-01",
            "nid_front_image": "/uploads/nid/blurry_front.jpg",
            "nid_back_image": "/uploads/nid/blurry_back.jpg",
            "role": "farmer",
        },
    )
    assert farmer_res.status_code == 201
    farmer_token = farmer_res.json()["accessToken"]

    # Get farmer id via /me
    me_res_initial = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    farmer_id = me_res_initial.json()["id"]

    # 2. Admin rejects NID
    reject_reason = "এনআইডি ছবি অস্পষ্ট ও নম্বর পড়া যাচ্ছে না"
    review_res = await client.post(
        f"/api/v1/admin/nid-verifications/{farmer_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"action": "reject", "reason": reject_reason},
    )
    assert review_res.status_code == 200
    review_data = review_res.json()
    assert review_data["isNidVerified"] is False
    assert review_data["nidVerificationStatus"] == "rejected"
    assert review_data["nidRejectionReason"] == reject_reason

    # 3. Farmer's /me profile reflects rejected status and reason
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert me_res.status_code == 200
    user_me = me_res.json()
    assert user_me["isNidVerified"] is False
    assert user_me["nidVerificationStatus"] == "rejected"
    assert user_me["nidRejectionReason"] == reject_reason


@pytest.mark.asyncio
async def test_resubmit_nid_flow_with_validation(client: AsyncClient):
    """Rejected farmer resubmits NID with 10/13/17 digit validation and resets status to pending."""
    # 1. Register admin and farmer
    admin = await register_user(client, "01999999997", "অ্যাডমিন টেস্ট", "admin")
    admin_token = admin["accessToken"]

    farmer_res = await client.post(
        "/api/v1/auth/register",
        json={
            "phone": "01711224466",
            "password": "SecurePassword123!",
            "full_name": "জামাল হোসেন",
            "nid": "1234567890",
            "dob": "1992-06-10",
            "nid_front_image": "/uploads/nid/front_bad.jpg",
            "nid_back_image": "/uploads/nid/back_bad.jpg",
            "role": "farmer",
        },
    )
    assert farmer_res.status_code == 201
    farmer_token = farmer_res.json()["accessToken"]

    me_initial = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    farmer_id = me_initial.json()["id"]

    # 2. Admin rejects the submission
    await client.post(
        f"/api/v1/admin/nid-verifications/{farmer_id}/review",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"action": "reject", "reason": "ছবির ব্যাকসাইড ঝাপসা ও কাটা"},
    )

    # 3. Farmer attempts resubmission with invalid NID length (e.g. 9 digits) -> Validation fails
    invalid_res = await client.post(
        "/api/v1/auth/resubmit-nid",
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "nid": "123456789",  # 9 digits - invalid!
            "dob": "1992-06-10",
            "nid_front_image": "/uploads/nid/front_clear.jpg",
            "nid_back_image": "/uploads/nid/back_clear.jpg",
        },
    )
    assert invalid_res.status_code == 422, "Should reject invalid NID digit length"

    # 4. Farmer resubmits with valid 17-digit NID and fresh images
    valid_res = await client.post(
        "/api/v1/auth/resubmit-nid",
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "nid": "19921234567890123",  # 17 digits - valid!
            "dob": "1992-06-10",
            "nid_front_image": "/uploads/nid/front_clear.jpg",
            "nid_back_image": "/uploads/nid/back_clear.jpg",
        },
    )
    assert valid_res.status_code == 200, valid_res.text
    resubmit_data = valid_res.json()
    assert resubmit_data["nid"] == "19921234567890123"
    assert resubmit_data["nidVerificationStatus"] == "pending"
    assert resubmit_data["nidRejectionReason"] is None
    assert resubmit_data["nidFrontImage"] == "/uploads/nid/front_clear.jpg"
    assert resubmit_data["nidBackImage"] == "/uploads/nid/back_clear.jpg"

    # 5. Farmer's /me profile reflects reset to pending
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert me_res.status_code == 200
    user_me = me_res.json()
    assert user_me["nidVerificationStatus"] == "pending"
    assert user_me["nidRejectionReason"] is None

