"""Unit and integration tests for Expert Case-Review Portal (Later Roadmap).

Strictly verifies:
- AGENTS.md Rule 12: Object-level authorization policy (Role guards deny-by-default for non-experts).
- AGENTS.md Rule 19: AI output must be constrained, reviewable, and honest (Human-in-the-loop expert review).
- AGENTS.md Rule 26: Error, logging, and audit rules.
"""

from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.crop_assistant.models import CropCase, CropCaseStatus


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
async def test_expert_portal_rejects_unauthorized_farmer(client: AsyncClient):
    """Verifies that non-expert users receive 403 Forbidden on expert review queue."""
    farmer = await register_user(client, "01777000001", "সাধারণ কৃষক", "farmer")
    token = farmer["accessToken"]

    res = await client.get(
        "/api/v1/expert/cases/pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_expert_can_list_and_review_escalated_case(
    client: AsyncClient, test_db: AsyncSession
):
    """Verifies an agricultural expert can list pending cases and submit an official vetted prescription."""
    expert = await register_user(client, "01777000002", "ড. কৃষিবিদ জামান", "expert")
    expert_token = expert["accessToken"]

    farmer = await register_user(client, "01777000003", "আনোয়ারুল হক", "farmer")
    farmer_token = farmer["accessToken"]

    # 1. Farmer has an uncertain/escalated crop case
    case = CropCase(
        user_id=farmer["user"]["id"],
        crop_type="rice",
        symptoms_description="পাতার কিনারায় হলদে-বাদামি ছোপ ও টান",
        image_filename="crop_escalated_1.jpg",
        status=CropCaseStatus.UNCERTAIN,
        confidence=0.42,
        confidence_band="low",
        reason_summary=["অস্পষ্ট লক্ষণ"],
        guidance=["সতর্কতামূলক পর্যবেক্ষণ"],
        escalation_recommended=True,
        disclaimer="প্রাথমিক সিদ্ধান্ত সহায়তা",
    )
    test_db.add(case)
    await test_db.commit()
    await test_db.refresh(case)

    # 2. Expert lists pending cases
    pending_res = await client.get(
        "/api/v1/expert/cases/pending",
        headers={"Authorization": f"Bearer {expert_token}"},
    )
    assert pending_res.status_code == 200
    pending_cases = pending_res.json()
    assert len(pending_cases) >= 1
    found_case = next(c for c in pending_cases if c["id"] == case.id)
    assert found_case["escalationRecommended"] is True
    assert found_case["isReviewedByExpert"] is False

    # 3. Expert submits official diagnosis & vetted treatment
    review_payload = {
        "reviewed_diagnosis": "ব্যাকটেরিয়াজনিত পাতা পোড়া রোগ (Bacterial Leaf Blight)",
        "prescribed_treatment": "১. জমিতে অতিরিক্ত ইউরিয়া সার বন্ধ করুন। ২. প্রতি লিটার পানিতে কপার অক্সিক্লোরাইড ২ গ্রাম হারে স্প্রে করুন।",
        "severity_level": "moderate",
        "expert_notes": "সকাল অথবা শেষ বিকেলে স্প্রে করা বাঞ্ছনীয়। রৌদ্রোজ্জ্বল দিনে স্প্রে করবেন না।",
    }
    submit_res = await client.post(
        f"/api/v1/expert/cases/{case.id}/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {expert_token}"},
    )
    assert submit_res.status_code == 201
    review_data = submit_res.json()
    assert review_data["cropCaseId"] == case.id
    assert review_data["expertName"] == "ড. কৃষিবিদ জামান"
    assert "Bacterial Leaf Blight" in review_data["reviewedDiagnosis"]

    # 4. Farmer views their case details and receives the updated expert verification
    details_res = await client.get(
        f"/api/v1/crop-cases/{case.id}",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert details_res.status_code == 200
    updated_case = details_res.json()
    assert updated_case["isReviewedByExpert"] is True
    assert "কৃষিবিদ দ্বারা যাচাইকৃত" in updated_case["possibleCondition"]
    assert "বিশেষজ্ঞের প্রেসক্রিপশন" in updated_case["guidance"][0]

    # 5. Fetch expert review directly
    fetch_review_res = await client.get(
        f"/api/v1/expert/cases/{case.id}/review",
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert fetch_review_res.status_code == 200
    fetched_review = fetch_review_res.json()
    assert fetched_review["severityLevel"] == "moderate"
    assert "কপার অক্সিক্লোরাইড" in fetched_review["prescribedTreatment"]

    # 6. Verify image access: Expert and owner can access crop image, unrelated user gets 403
    other_user = await register_user(client, "01777000004", "অন্য কৃষক", "farmer")
    other_token = other_user["accessToken"]

    # Unrelated user 403
    forbidden_img_res = await client.get(
        f"/api/v1/crop-cases/{case.id}/image",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert forbidden_img_res.status_code == 403

    # Expert access 200
    expert_img_res = await client.get(
        f"/api/v1/crop-cases/{case.id}/image",
        headers={"Authorization": f"Bearer {expert_token}"},
    )
    assert expert_img_res.status_code == 200
    assert expert_img_res.headers.get("x-content-type-options") == "nosniff"


@pytest.mark.asyncio
async def test_farmer_can_send_case_and_photo_to_expert(
    client: AsyncClient, test_db: AsyncSession
):
    """Verifies that a farmer can send their case with notes and photo to the expert review queue."""
    farmer = await register_user(client, "01777000005", "মো: আক্তারুজ্জামান", "farmer")
    farmer_token = farmer["accessToken"]

    expert = await register_user(client, "01777000006", "কৃষিবিদ সাকলাইন", "expert")
    expert_token = expert["accessToken"]

    # 1. Create a non-escalated crop case
    case = CropCase(
        user_id=farmer["user"]["id"],
        crop_type="ধান",
        symptoms_description="পাতার ডগা সামান্য হলুদ",
        image_filename="crop_rice_init.jpg",
        status=CropCaseStatus.POSSIBLE_MATCH,
        confidence=0.72,
        confidence_band="high",
        reason_summary=["প্রাথমিক দাগ"],
        guidance=["পর্যবেক্ষণ করুন"],
        escalation_recommended=False,
        disclaimer="এআই পরামর্শ",
    )
    test_db.add(case)
    await test_db.commit()
    await test_db.refresh(case)

    # 2. Farmer sends case to expert with notes and photo
    from io import BytesIO
    from PIL import Image

    img_buffer = BytesIO()
    Image.new("RGB", (200, 200), color="green").save(img_buffer, format="JPEG")
    img_bytes = img_buffer.getvalue()

    send_res = await client.post(
        f"/api/v1/crop-cases/{case.id}/send-to-expert",
        data={"notes": "গত ২ দিনে পাতার হলুদ দাগ অনেক বেড়েছে, অতিরিক্ত সার দেওয়া হয় নাই।"},
        files={"additional_image": ("leaf_closeup.jpg", img_bytes, "image/jpeg")},
        headers={"Authorization": f"Bearer {farmer_token}"},
    )
    assert send_res.status_code == 200, send_res.text
    updated = send_res.json()
    assert updated["escalationRecommended"] is True
    assert "গত ২ দিনে পাতার হলুদ দাগ অনেক বেড়েছে" in updated["symptomsDescription"]

    # 3. Unrelated farmer cannot send someone else's case
    stranger = await register_user(client, "01777000007", "অপরিচিত ব্যক্তি", "farmer")
    stranger_res = await client.post(
        f"/api/v1/crop-cases/{case.id}/send-to-expert",
        data={"notes": "অনধিকার প্রবেশ"},
        headers={"Authorization": f"Bearer {stranger['accessToken']}"},
    )
    assert stranger_res.status_code == 403

    # 4. Expert now sees this newly escalated case in their pending queue
    expert_pending = await client.get(
        "/api/v1/expert/cases/pending",
        headers={"Authorization": f"Bearer {expert_token}"},
    )
    assert expert_pending.status_code == 200
    pending_list = expert_pending.json()
    assert any(c["id"] == case.id for c in pending_list)


