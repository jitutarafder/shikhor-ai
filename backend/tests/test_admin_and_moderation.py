"""Tests for Phase 8: Admin, Moderation, and Operational Readiness.

Strictly complies with:
- AGENTS.md Rule 12: Object-level authorization policy (Role guards deny-by-default).
- AGENTS.md Rule 26: Error, logging, and audit rules.
- AGENTS.md Rule 31: Definition of done (authoritative real data only).
- phases.md Phase 8 Exit Criteria:
  - Every privileged action is authorized and audited.
  - Shared admin accounts do not exist.
  - Production dashboard contains real data only.
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
async def test_admin_endpoints_reject_unauthorized_regular_users(client: AsyncClient):
    """Verifies that non-admin and non-moderator roles receive 403 Forbidden (Rule 12)."""
    farmer = await register_user(client, "01740000001", "সাধারণ কৃষক", "farmer")
    token = farmer["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Metrics
    res_metrics = await client.get("/api/v1/admin/metrics", headers=headers)
    assert res_metrics.status_code == 403
    assert res_metrics.json()["error"]["code"] == "FORBIDDEN_ROLE"

    # 2. Moderation reports
    res_reports = await client.get("/api/v1/admin/reports", headers=headers)
    assert res_reports.status_code == 403
    assert res_reports.json()["error"]["code"] == "FORBIDDEN_ROLE"

    # 3. Audit logs
    res_audit = await client.get("/api/v1/admin/audit-logs", headers=headers)
    assert res_audit.status_code == 403
    assert res_audit.json()["error"]["code"] == "FORBIDDEN_ROLE"

    # 4. Knowledge publishing
    res_know = await client.post(
        "/api/v1/admin/knowledge",
        headers=headers,
        json={
            "cropType": "paddy",
            "category": "disease",
            "titleBn": "অননুমোদিত লেখা",
            "summaryBn": "অননুমোদিত সারসংক্ষেপ",
            "contentBn": "অননুমোদিত বিস্তারিত বর্ণনা...",
        },
    )
    assert res_know.status_code == 403
    assert res_know.json()["error"]["code"] == "FORBIDDEN_ROLE"


@pytest.mark.asyncio
async def test_admin_can_view_metrics_and_real_system_state(client: AsyncClient):
    """Verifies that admin can view accurate system metrics computed from real database data (Rule 31)."""
    admin = await register_user(client, "01740000002", "প্রধান প্রশাসক", "admin")
    farmer = await register_user(client, "01740000003", "কৃষক কামরুল", "farmer")
    buyer = await register_user(client, "01740000004", "পাইকার জহির", "buyer")

    headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    res = await client.get("/api/v1/admin/metrics", headers=headers)
    assert res.status_code == 200, res.text
    metrics = res.json()

    assert metrics["totalUsers"] >= 3
    assert metrics["farmersCount"] >= 1
    assert metrics["buyersCount"] >= 1
    assert metrics["systemStatus"] == "healthy"
    assert "timestamp" in metrics


@pytest.mark.asyncio
async def test_moderation_report_resolution_and_audit_trail(client: AsyncClient):
    """Verifies report resolution, user suspension, and immutable audit logging (Rule 26 & Phase 8 Exit Criteria)."""
    admin = await register_user(client, "01740000005", "মডারেটর করিম", "admin")
    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    reporter = await register_user(client, "01740000006", "অভিযোগকারী", "farmer")
    spammer = await register_user(client, "01740000007", "স্প্যাম প্রেরণকারী", "buyer")

    # Reporter files moderation report
    rep_res = await client.post(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {reporter['accessToken']}"},
        json={
            "reportedUserId": spammer["user"]["id"],
            "contentType": "user",
            "contentId": spammer["user"]["id"],
            "reason": "স্প্যাম বা প্রতারণামূলক প্রস্তাব",
            "details": "অযাচিত ফোন কল ও বারবার মেসেজ দিচ্ছিলেন।",
        },
    )
    assert rep_res.status_code == 201
    report_id = rep_res.json()["id"]

    # Admin checks reports queue
    reports_res = await client.get("/api/v1/admin/reports?status=pending", headers=admin_headers)
    assert reports_res.status_code == 200
    pending = reports_res.json()
    assert any(r["id"] == report_id for r in pending)

    # Admin resolves report with suspend_user action
    resolve_res = await client.post(
        f"/api/v1/admin/reports/{report_id}/resolve",
        headers={**admin_headers, "X-Correlation-ID": "test-req-audit-999"},
        json={
            "action": "suspend_user",
            "resolutionNotes": "বারবার স্প্যাম প্রেরণের প্রমাণ পাওয়ায় সাময়িক স্থগিত করা হলো।",
        },
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    assert resolved["status"] == "resolved"

    # Verify that the spammer account is deactivated
    spammer_check = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {spammer['accessToken']}"},
    )
    assert spammer_check.status_code == 403
    assert spammer_check.json()["error"]["code"] == "ACCOUNT_INACTIVE"

    # Verify Audit Log entry was generated
    audit_res = await client.get("/api/v1/admin/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200
    logs = audit_res.json()

    matched_log = next((l for l in logs if l["resourceId"] == report_id), None)
    assert matched_log is not None
    assert matched_log["actorPhone"] == admin["user"]["phone"]
    assert matched_log["action"] == "REPORT_SUSPEND_USER"
    assert matched_log["resourceType"] == "report"
    assert "স্প্যাম" in matched_log["details"]


@pytest.mark.asyncio
async def test_admin_can_toggle_user_status(client: AsyncClient):
    """Verifies admin user status toggling and self-modification prevention."""
    admin = await register_user(client, "01740000008", "নিরাপত্তা অ্যাডমিন", "admin")
    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    target = await register_user(client, "01740000009", "লক্ষ্য ব্যবহারকারী", "farmer")

    # Admin deactivates target
    toggle_res = await client.post(
        f"/api/v1/admin/users/{target['user']['id']}/status",
        headers=admin_headers,
        json={"isActive": False, "reason": "নিয়ম লঙ্ঘন পর্যালোচনাধীন"},
    )
    assert toggle_res.status_code == 200
    assert toggle_res.json()["isActive"] is False

    # Admin attempts to deactivate themselves -> 400 CANNOT_MODIFY_SELF
    self_res = await client.post(
        f"/api/v1/admin/users/{admin['user']['id']}/status",
        headers=admin_headers,
        json={"isActive": False, "reason": "ভুলবশত চেষ্টা"},
    )
    assert self_res.status_code == 400
    assert self_res.json()["error"]["code"] == "CANNOT_MODIFY_SELF"


@pytest.mark.asyncio
async def test_admin_can_publish_knowledge_article(client: AsyncClient):
    """Verifies that admin/moderator can publish verified agricultural advisories."""
    admin = await register_user(client, "01740000010", "কৃষি বিশেষজ্ঞ অ্যাডমিন", "admin")
    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    payload = {
        "cropType": "mustard",
        "category": "disease",
        "titleBn": "সরিষার জাবপোকা দমন ব্যবস্থাপনা",
        "titleEn": "Mustard Aphid Control",
        "summaryBn": "সরিষার ফুল ও কচি পাতার রস চুষে খেয়ে ফলন মারাত্মকভাবে কমিয়ে দেয়।",
        "contentBn": "জাবপোকা সরিষার প্রধান ক্ষতিকারক পোকা। গাছে অতিরিক্ত আক্রমণ হলে ছত্রাকের আক্রমণ ঘটে এবং খেত কালো হয়ে যায়।",
        "recommendedPracticesBn": "১. প্রাথমিক অবস্থায় আক্রান্ত ডগা ছিঁড়ে ধ্বংস করুন। ২. আক্রমণ বেশি হলে ইমিডাক্লোপ্রিড গ্রুপের কীটনাশক স্প্রে করুন।",
    }

    pub_res = await client.post("/api/v1/admin/knowledge", headers=admin_headers, json=payload)
    assert pub_res.status_code == 201, pub_res.text
    created = pub_res.json()

    assert created["cropType"] == "mustard"
    assert created["version"] >= 1
    assert created["titleBn"] == "সরিষার জাবপোকা দমন ব্যবস্থাপনা"

    # Verify that public /knowledge catalog now returns this new advisory
    cat_res = await client.get("/api/v1/knowledge?crop_type=mustard")
    assert cat_res.status_code == 200
    mustard_articles = cat_res.json()["articles"]
    assert any(a["id"] == created["id"] for a in mustard_articles)
