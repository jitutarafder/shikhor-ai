"""Background Job Worker Admin & Monitoring Endpoints.

Strictly complies with:
- AGENTS.md Rule 11 & 12: Object-level authorization policy (Role guards deny-by-default for internal job queue).
- AGENTS.md Rule 25: Durable distributed queue for long-running critical work.
- AGENTS.md Rule 26: Redacted logging and audit trail.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_role
from app.db.session import get_db_session
from app.modules.jobs.models import JobStatus
from app.modules.jobs.schemas import (
    JobEnqueueRequest,
    JobResponse,
    JobStatsResponse,
)
from app.modules.jobs.service import (
    cancel_job,
    enqueue_job,
    get_job_stats,
    list_jobs,
    retry_job,
)
from app.modules.users.models import User, UserRole
from app.workers.job_worker import run_worker_tick

router = APIRouter(prefix="/jobs", tags=["Durable Background Jobs"])


@router.get(
    "/stats",
    response_model=JobStatsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_queue_statistics(
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> JobStatsResponse:
    """Returns aggregated job queue counts and active worker metrics."""
    return await get_job_stats(db=db)


@router.get(
    "",
    response_model=List[JobResponse],
    status_code=status.HTTP_200_OK,
)
async def get_jobs_list(
    status_filter: Optional[JobStatus] = Query(None, alias="status"),
    job_type: Optional[str] = Query(None, alias="job_type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MODERATOR)),
    db: AsyncSession = Depends(get_db_session),
) -> List[JobResponse]:
    """Lists persistent background jobs with optional status/type filtering."""
    jobs = await list_jobs(
        db=db,
        status=status_filter.value if status_filter else None,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )
    return [JobResponse.model_validate(j) for j in jobs]


@router.post(
    "/enqueue",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enqueue_background_job(
    request: JobEnqueueRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> JobResponse:
    """Enqueues a new background job into the durable queue."""
    job = await enqueue_job(
        db=db,
        job_type=request.jobType,
        payload=request.payload,
        priority=request.priority,
        delay_seconds=request.delaySeconds,
        max_attempts=request.maxAttempts,
    )
    return JobResponse.model_validate(job)


@router.post(
    "/{job_id}/retry",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
)
async def retry_failed_job(
    job_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> JobResponse:
    """Manually resets a failed or dead-letter job back to pending status."""
    job = await retry_job(db=db, job_id=job_id)
    return JobResponse.model_validate(job)


@router.post(
    "/{job_id}/cancel",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
)
async def cancel_background_job(
    job_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> JobResponse:
    """Cancels a pending or processing background job."""
    job = await cancel_job(db=db, job_id=job_id)
    return JobResponse.model_validate(job)


@router.post(
    "/run-tick",
    response_model=Optional[JobResponse],
    status_code=status.HTTP_200_OK,
)
async def trigger_worker_tick(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[JobResponse]:
    """Manually triggers a single worker execution tick from the API."""
    job = await run_worker_tick(worker_id=f"manual-admin-{current_user.id[:8]}", db=db)
    if job:
        return JobResponse.model_validate(job)
    return None
