"""Tests for Crop Assistant AI analysis, image safety, and cross-user authorization.

Complies with:
- AGENTS.md Rule 12: Object-level authorization policy
- AGENTS.md Rule 18: File upload security (MIME, magic bytes, dimensions)
- AGENTS.md Rule 19: AI output constraints, uncertainty states, expert referral
- AGENTS.md Rule 28: Mandatory upload and AI security tests
"""

import io
import pytest
from httpx import AsyncClient
from PIL import Image


def create_test_image_bytes(format: str = "JPEG", size: tuple = (120, 120)) -> bytes:
    """Generates authentic valid in-memory test image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(33, 98, 69))
    img.save(buf, format=format)
    return buf.getvalue()


async def get_auth_token(client: AsyncClient, phone: str = "01711223344") -> str:
    """Helper creating a test user and returning Bearer token."""
    reg_payload = {
        "phone": phone,
        "password": "Password123#Strong",
        "full_name": "টেস্ট কৃষক",
        "role": "farmer",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    if res.status_code == 200:
        return res.json()["accessToken"]
    login_res = await client.post("/api/v1/auth/login", json={"phone": phone, "password": "Password123#Strong"})
    return login_res.json()["accessToken"]


@pytest.mark.asyncio
async def test_successful_crop_case_submission(client: AsyncClient):
    token = await get_auth_token(client, "01700112233")
    headers = {"Authorization": f"Bearer {token}"}
    image_bytes = create_test_image_bytes("JPEG")

    files = {
        "image": ("leaf.jpg", image_bytes, "image/jpeg"),
    }
    data = {
        "crop_type": "ধান",
        "symptoms": "পাতার কিনারায় হলুদ ও বাদামি ব্লাইট দাগ",
    }

    res = await client.post("/api/v1/crop-cases", headers=headers, data=data, files=files)
    assert res.status_code == 201, res.text
    case = res.json()

    assert case["cropType"] == "ধান"
    assert case["status"] == "possible_match"
    assert "ব্লাইট" in case["possibleCondition"] or "Bacterial Blight" in case["possibleCondition"] or case["confidence"] >= 0.70
    assert case["confidence"] >= 0.70
    assert len(case["reasonSummary"]) > 0
    assert len(case["guidance"]) > 0
    assert case["escalationRecommended"] is False
    assert "উপজেলা কৃষি কর্মকর্তা" in case["disclaimer"]


@pytest.mark.asyncio
async def test_rejection_of_fake_mimetype_and_magic_bytes(client: AsyncClient):
    # Attacker uploads text file disguised as a JPEG
    token = await get_auth_token(client, "01700223344")
    headers = {"Authorization": f"Bearer {token}"}
    malicious_bytes = b"<?php echo 'malicious shell'; ?>This is not a real image."

    files = {
        "image": ("exploit.jpg", malicious_bytes, "image/jpeg"),
    }
    data = {
        "crop_type": "ধান",
    }

    res = await client.post("/api/v1/crop-cases", headers=headers, data=data, files=files)
    assert res.status_code == 400
    error_data = res.json()
    assert error_data["error"]["code"] in ("UNSUPPORTED_IMAGE_FORMAT", "INVALID_FILE_HEADER")


@pytest.mark.asyncio
async def test_rejection_of_disallowed_mime_type(client: AsyncClient):
    token = await get_auth_token(client, "01700334455")
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "image": ("vector.svg", b"<svg><circle r='10'/></svg>", "image/svg+xml"),
    }
    data = {
        "crop_type": "ধান",
    }

    res = await client.post("/api/v1/crop-cases", headers=headers, data=data, files=files)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_MIME_TYPE"


@pytest.mark.asyncio
async def test_unsupported_crop_produces_escalation(client: AsyncClient):
    token = await get_auth_token(client, "01700445566")
    headers = {"Authorization": f"Bearer {token}"}
    image_bytes = create_test_image_bytes("WEBP")

    files = {
        "image": ("crop.webp", image_bytes, "image/webp"),
    }
    data = {
        "crop_type": "ড্রাগন ফল",  # Unsupported / unrecognized crop in current taxonomy
        "symptoms": "অজানা দাগ",
    }

    res = await client.post("/api/v1/crop-cases", headers=headers, data=data, files=files)
    assert res.status_code == 201
    case = res.json()

    # Must produce unsupported state with mandatory expert escalation
    assert case["status"] == "unsupported"
    assert case["escalationRecommended"] is True
    assert case["confidenceBand"] == "low"
    assert len(case["guidance"]) > 0


@pytest.mark.asyncio
async def test_vague_symptoms_produce_uncertain_state(client: AsyncClient):
    token = await get_auth_token(client, "01700556677")
    headers = {"Authorization": f"Bearer {token}"}
    image_bytes = create_test_image_bytes("PNG")

    files = {
        "image": ("leaf.png", image_bytes, "image/png"),
    }
    data = {
        "crop_type": "ধান",
        "symptoms": "দাগ",  # Too short / vague (< 5 chars)
    }

    res = await client.post("/api/v1/crop-cases", headers=headers, data=data, files=files)
    assert res.status_code == 201
    case = res.json()

    # Rule 19: low-confidence/vague input must produce uncertain state and escalate
    assert case["status"] == "uncertain"
    assert case["escalationRecommended"] is True
    assert case["confidence"] < 0.60


@pytest.mark.asyncio
async def test_cross_user_crop_case_isolation(client: AsyncClient):
    # Farmer 1 creates a case
    token1 = await get_auth_token(client, "01700667788")
    headers1 = {"Authorization": f"Bearer {token1}"}
    image_bytes = create_test_image_bytes("JPEG")

    files = {"image": ("leaf.jpg", image_bytes, "image/jpeg")}
    res = await client.post("/api/v1/crop-cases", headers=headers1, data={"crop_type": "আলু"}, files=files)
    case_id = res.json()["id"]

    # Farmer 2 tries to read Farmer 1's private crop case
    token2 = await get_auth_token(client, "01700778899")
    headers2 = {"Authorization": f"Bearer {token2}"}

    get_res = await client.get(f"/api/v1/crop-cases/{case_id}", headers=headers2)
    assert get_res.status_code == 403
    assert get_res.json()["error"]["code"] == "FORBIDDEN_CROP_CASE_ACCESS"


@pytest.mark.asyncio
async def test_crop_feedback_submission(client: AsyncClient):
    token = await get_auth_token(client, "01700889900")
    headers = {"Authorization": f"Bearer {token}"}
    image_bytes = create_test_image_bytes("JPEG")

    files = {"image": ("leaf.jpg", image_bytes, "image/jpeg")}
    case_res = await client.post("/api/v1/crop-cases", headers=headers, data={"crop_type": "টমেটো"}, files=files)
    case_id = case_res.json()["id"]

    feedback_payload = {
        "feedback_type": "helpful",
        "comments": "নির্দেশনা মেনে পানি সরানোয় উপকার পেয়েছি।",
    }
    fb_res = await client.post(f"/api/v1/crop-cases/{case_id}/feedback", headers=headers, json=feedback_payload)
    assert fb_res.status_code == 201
    assert fb_res.json()["feedbackType"] == "helpful"


@pytest.mark.asyncio
async def test_additional_crops_guidance_and_taxonomy(client: AsyncClient):
    """Verifies additional field crops and vegetables analysis models and taxonomy endpoint."""
    token = await get_auth_token(client, "01700990011")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Test taxonomy endpoint
    tax_res = await client.get("/api/v1/crop-cases/crops")
    assert tax_res.status_code == 200
    crops_list = tax_res.json()["crops"]
    crop_ids = [c["id"] for c in crops_list]
    for expected_crop in ["Rice", "Wheat", "Corn", "Potato", "Tomato"]:
        assert expected_crop in crop_ids or any(expected_crop.lower() in c["name_bn"].lower() for c in crops_list)

    # 2. Test Wheat (গম) analysis
    img_bytes = create_test_image_bytes("JPEG")
    wheat_res = await client.post(
        "/api/v1/crop-cases",
        headers=headers,
        data={"crop_type": "Wheat", "symptoms": "পাতার উপরিভাগে বাদামি গুঁড়া মরিচা দাগ"},
        files={"image": ("wheat.jpg", img_bytes, "image/jpeg")},
    )
    assert wheat_res.status_code == 201
    wheat_case = wheat_res.json()
    assert "Rust" in wheat_case.get("possibleCondition", "") or "গম" in wheat_case.get("possibleCondition", "") or wheat_case["status"] in ["possible_match", "uncertain"]
    assert wheat_case["confidence"] >= 0.50

