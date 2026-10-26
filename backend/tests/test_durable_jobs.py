"""Tests for Durable Distributed Job Workers.

Strictly complies with:
- AGENTS.md Rule 11 & 12: Object-level authorization policy (Deny-by-default for non-admin).
- AGENTS.md Rule 25: Durable distributed queue for long-running critical work.
- AGENTS.md Rule 28: Mandatory unit and integration tests for state transitions and failures.
"""

from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.jobs.models import Job, JobStatus
from app.modules.jobs.service import (
    claim_next_job,
    complete_job,
    enqueue_job,
    fail_job,
    get_job_stats,
    retry_job,
)
from app.workers.job_worker import run_worker_tick


async def register_user(client: AsyncClient, phone: str, name: str, role: str) -> dict:
    """Helper to register and obtain auth token."""
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
    return res.json()


@pytest.mark.asyncio
async def test_job_endpoints_authorization(client: AsyncClient):
    """Verifies that non-admin and unauthenticated users cannot access or enqueue jobs (Rule 12)."""
    # 1. Unauthenticated request
    res = await client.get("/api/v1/jobs")
    assert res.status_code == 401

    # 2. Regular farmer user
    farmer = await register_user(client, "01780000001", "সাধারণ কৃষক", "farmer")
    farmer_headers = {"Authorization": f"Bearer {farmer['accessToken']}"}

    res_list = await client.get("/api/v1/jobs", headers=farmer_headers)
    assert res_list.status_code == 403
    assert res_list.json()["error"]["code"] == "FORBIDDEN_ROLE"

    res_stats = await client.get("/api/v1/jobs/stats", headers=farmer_headers)
    assert res_stats.status_code == 403

    res_enqueue = await client.post(
        "/api/v1/jobs/enqueue",
        headers=farmer_headers,
        json={"job_type": "test_echo_job", "payload": {"message": "hi"}},
    )
    assert res_enqueue.status_code == 403


@pytest.mark.asyncio
async def test_enqueue_and_run_worker_tick(client: AsyncClient):
    """Verifies enqueuing a job and successfully executing it via worker tick."""
    admin = await register_user(client, "01780000002", "অ্যাডমিন কর্মী", "admin")
    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    # 1. Enqueue job
    enqueue_res = await client.post(
        "/api/v1/jobs/enqueue",
        headers=admin_headers,
        json={
            "job_type": "test_echo_job",
            "payload": {"message": "অটোমেটেড টেস্ট ডাটা"},
            "priority": 5,
        },
    )
    assert enqueue_res.status_code == 201, enqueue_res.text
    job_data = enqueue_res.json()
    job_id = job_data["id"]
    assert job_data["status"] == "pending"
    assert job_data["priority"] == 5

    # 2. Check stats before running
    stats_res = await client.get("/api/v1/jobs/stats", headers=admin_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["pending"] >= 1

    # 3. Trigger worker tick
    tick_res = await client.post("/api/v1/jobs/run-tick", headers=admin_headers)
    assert tick_res.status_code == 200, tick_res.text
    processed = tick_res.json()
    assert processed["id"] == job_id
    assert processed["status"] == "completed"
    assert processed["resultData"]["echo"] == "অটোমেটেড টেস্ট ডাটা"
    assert processed["resultData"]["success"] is True

    # 4. Check stats after running
    stats_after = (await client.get("/api/v1/jobs/stats", headers=admin_headers)).json()
    assert stats_after["completed"] >= 1


@pytest.mark.asyncio
async def test_worker_retry_and_dead_letter_queue(client: AsyncClient, test_db: AsyncSession):
    """Verifies exponential backoff retries and transition to Dead Letter Queue when max_attempts is reached."""
    # Enqueue a failing job with max_attempts = 2
    job = await enqueue_job(
        db=test_db,
        job_type="test_echo_job",
        payload={"message": "fail", "simulate_error": True},
        priority=10,
        max_attempts=2,
    )
    job_id = job.id

    # 1. First execution attempt -> should fail and schedule retry
    first_tick = await run_worker_tick(worker_id="test-worker-1", db=test_db)
    assert first_tick is not None
    assert first_tick.id == job_id
    assert first_tick.attempts == 1
    assert first_tick.status == JobStatus.PENDING
    assert "Simulated job failure" in first_tick.last_error
    sched = first_tick.scheduled_at.replace(tzinfo=timezone.utc) if first_tick.scheduled_at.tzinfo is None else first_tick.scheduled_at
    assert sched > datetime.now(timezone.utc)

    # Force scheduled_at to past so it can be picked up again immediately
    from datetime import timedelta
    first_tick.scheduled_at = datetime.now(timezone.utc) - timedelta(seconds=10)
    await test_db.commit()

    # 2. Second execution attempt -> should reach max_attempts and become DEAD_LETTER
    second_tick = await run_worker_tick(worker_id="test-worker-2", db=test_db)
    assert second_tick is not None
    assert second_tick.id == job_id
    assert second_tick.attempts == 2
    assert second_tick.status == JobStatus.DEAD_LETTER

    # 3. Verify manual retry resets it to pending
    admin = await register_user(client, "01780000003", "সুপার অ্যাডমিন", "admin")
    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    retry_res = await client.post(f"/api/v1/jobs/{job_id}/retry", headers=admin_headers)
    assert retry_res.status_code == 200
    retried_data = retry_res.json()
    assert retried_data["status"] == "pending"


@pytest.mark.asyncio
async def test_cancel_job(client: AsyncClient):
    """Verifies that an admin can cancel a pending job."""
    admin = await register_user(client, "01780000004", "ক্যান্সেল অ্যাডমিন", "admin")
    admin_headers = {"Authorization": f"Bearer {admin['accessToken']}"}

    enqueue_res = await client.post(
        "/api/v1/jobs/enqueue",
        headers=admin_headers,
        json={"job_type": "test_echo_job", "payload": {"message": "to cancel"}},
    )
    job_id = enqueue_res.json()["id"]

    cancel_res = await client.post(f"/api/v1/jobs/{job_id}/cancel", headers=admin_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"
