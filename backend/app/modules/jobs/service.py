"""Durable background jobs domain service.

Strictly complies with AGENTS.md Rule 25:
- Durable, persistent background job queue.
- Concurrency-safe job claiming.
- Exponential backoff retry logic and Dead Letter Queue.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException, ShikhorException
from app.modules.jobs.models import Job, JobStatus
from app.modules.jobs.registry import JOB_HANDLERS
from app.modules.jobs.schemas import JobResponse, JobStatsResponse

logger = logging.getLogger("shikhor.jobs")


async def enqueue_job(
    db: AsyncSession,
    job_type: str,
    payload: Dict[str, Any],
    priority: int = 1,
    delay_seconds: int = 0,
    max_attempts: int = 3,
) -> Job:
    """Enqueues a durable background job into persistent storage."""
    now = datetime.now(timezone.utc)
    scheduled_at = now + timedelta(seconds=max(0, delay_seconds))

    job = Job(
        job_type=job_type,
        payload=payload,
        status=JobStatus.PENDING,
        priority=priority,
        max_attempts=max_attempts,
        attempts=0,
        scheduled_at=scheduled_at,
        created_at=now,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    logger.info("Enqueued durable job %s of type %s (priority=%d)", job.id, job_type, priority)
    return job


async def claim_next_job(
    db: AsyncSession,
    worker_id: str,
) -> Optional[Job]:
    """Atomically claims the highest priority pending job that is ready to run.

    Uses atomic status update to guarantee no two distributed workers execute the same job.
    """
    now = datetime.now(timezone.utc)

    # 1. Query candidate job: pending and scheduled_at <= now, ordered by priority DESC, scheduled_at ASC
    stmt = (
        select(Job)
        .where(
            Job.status == JobStatus.PENDING,
            Job.scheduled_at <= now,
        )
        .order_by(Job.priority.desc(), Job.scheduled_at.asc())
        .limit(1)
    )

    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        return None

    # 2. Atomically lock and claim
    job.status = JobStatus.PROCESSING
    job.locked_by = worker_id
    job.locked_at = now
    job.attempts += 1

    await db.commit()
    await db.refresh(job)
    logger.info("Worker %s claimed job %s (attempt %d/%d)", worker_id, job.id, job.attempts, job.max_attempts)
    return job


async def complete_job(
    db: AsyncSession,
    job_id: str,
    result_data: Optional[Dict[str, Any]] = None,
) -> Job:
    """Marks a job as completed with execution results."""
    job = await db.get(Job, job_id)
    if not job:
        raise NotFoundException(code="JOB_NOT_FOUND", message="Job not found.")

    now = datetime.now(timezone.utc)
    job.status = JobStatus.COMPLETED
    job.result_data = result_data or {}
    job.completed_at = now
    job.locked_by = None

    await db.commit()
    await db.refresh(job)
    logger.info("Job %s marked COMPLETED successfully", job_id)
    return job


async def fail_job(
    db: AsyncSession,
    job_id: str,
    error_message: str,
) -> Job:
    """Marks job attempt as failed, applying exponential backoff or moving to Dead Letter Queue."""
    job = await db.get(Job, job_id)
    if not job:
        raise NotFoundException(code="JOB_NOT_FOUND", message="Job not found.")

    now = datetime.now(timezone.utc)
    job.last_error = error_message[:2000]  # Bound error log size
    job.locked_by = None

    if job.attempts >= job.max_attempts:
        # Reached max retry limit -> Move to Dead Letter Queue
        job.status = JobStatus.DEAD_LETTER
        job.completed_at = now
        logger.warning("Job %s exceeded max attempts (%d); moved to DEAD_LETTER", job_id, job.max_attempts)
    else:
        # Schedule next retry with exponential backoff: 2^attempts * 3 seconds
        delay_secs = (2 ** job.attempts) * 3
        job.status = JobStatus.PENDING
        job.scheduled_at = now + timedelta(seconds=delay_secs)
        logger.info("Job %s retry scheduled in %d seconds (attempt %d/%d)", job_id, delay_secs, job.attempts, job.max_attempts)

    await db.commit()
    await db.refresh(job)
    return job


async def retry_job(
    db: AsyncSession,
    job_id: str,
) -> Job:
    """Manually resets a failed or dead-letter job back to pending status."""
    job = await db.get(Job, job_id)
    if not job:
        raise NotFoundException(code="JOB_NOT_FOUND", message="Job not found.")

    now = datetime.now(timezone.utc)
    job.status = JobStatus.PENDING
    job.scheduled_at = now
    job.locked_by = None
    job.locked_at = None
    job.completed_at = None

    await db.commit()
    await db.refresh(job)
    logger.info("Job %s manually reset to PENDING", job_id)
    return job


async def cancel_job(
    db: AsyncSession,
    job_id: str,
) -> Job:
    """Cancels a pending or processing job."""
    job = await db.get(Job, job_id)
    if not job:
        raise NotFoundException(code="JOB_NOT_FOUND", message="Job not found.")

    if job.status == JobStatus.COMPLETED:
        raise ShikhorException(code="CANNOT_CANCEL_COMPLETED_JOB", message="Completed jobs cannot be cancelled.", status_code=400)

    job.status = JobStatus.CANCELLED
    job.completed_at = datetime.now(timezone.utc)
    job.locked_by = None

    await db.commit()
    await db.refresh(job)
    logger.info("Job %s CANCELLED", job_id)
    return job


async def list_jobs(
    db: AsyncSession,
    status: Optional[str] = None,
    job_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Job]:
    """Retrieves paginated list of background jobs for monitoring."""
    stmt = select(Job)
    if status:
        stmt = stmt.where(Job.status == status)
    if job_type:
        stmt = stmt.where(Job.job_type == job_type)

    stmt = stmt.order_by(Job.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_job_stats(
    db: AsyncSession,
) -> JobStatsResponse:
    """Aggregates queue status counts and active worker metrics."""
    counts_stmt = select(Job.status, func.count(Job.id)).group_by(Job.status)
    result = await db.execute(counts_stmt)
    counts = dict(result.all())

    # Count distinct active workers with active locks within last 5 minutes
    five_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
    worker_stmt = (
        select(func.count(func.distinct(Job.locked_by)))
        .where(
            Job.status == JobStatus.PROCESSING,
            Job.locked_at >= five_mins_ago,
            Job.locked_by.isnot(None),
        )
    )
    active_workers = (await db.execute(worker_stmt)).scalar() or 0

    return JobStatsResponse(
        total=sum(counts.values()),
        pending=counts.get(JobStatus.PENDING, 0),
        processing=counts.get(JobStatus.PROCESSING, 0),
        completed=counts.get(JobStatus.COMPLETED, 0),
        failed=counts.get(JobStatus.FAILED, 0),
        deadLetter=counts.get(JobStatus.DEAD_LETTER, 0),
        activeWorkers=active_workers,
    )
