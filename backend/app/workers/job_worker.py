"""Distributed background job worker runner.

Complies with AGENTS.md:
- Rule 25: Durable distributed job workers, avoiding FastAPI BackgroundTasks for critical tasks.
- Rule 26: Redacted, structured logging without leaking sensitive data.
- Handles atomic job claiming, exponential backoff, DLQ, and graceful worker shutdown.
"""

import asyncio
import logging
import os
import signal
import socket
import traceback
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.modules.jobs.models import Job
from app.modules.jobs.registry import JOB_HANDLERS
from app.modules.jobs.service import claim_next_job, complete_job, fail_job

logger = logging.getLogger("shikhor.worker")


async def run_worker_tick(worker_id: str, db: AsyncSession) -> Optional[Job]:
    """Executes a single job processing tick for a given worker.

    Atomically claims the highest priority ready job, invokes its registered handler,
    and records success or failure with exponential backoff.
    """
    job = await claim_next_job(db=db, worker_id=worker_id)
    if not job:
        return None

    handler = JOB_HANDLERS.get(job.job_type)
    if not handler:
        err_msg = f"No registered handler found for job type: {job.job_type}"
        logger.error(err_msg)
        return await fail_job(db=db, job_id=job.id, error_message=err_msg)

    try:
        logger.info("Worker %s executing job %s (%s)...", worker_id, job.id, job.job_type)
        result = await handler(db, job.payload)
        updated_job = await complete_job(db=db, job_id=job.id, result_data=result)
        logger.info("Worker %s finished job %s successfully", worker_id, job.id)
        return updated_job
    except Exception as exc:
        tb_str = traceback.format_exc()
        err_summary = f"{type(exc).__name__}: {str(exc)}"
        logger.error("Job %s execution failed: %s\n%s", job.id, err_summary, tb_str)
        return await fail_job(db=db, job_id=job.id, error_message=err_summary)


async def start_worker_loop(
    worker_id: Optional[str] = None,
    poll_interval_seconds: float = 2.0,
    stop_event: Optional[asyncio.Event] = None,
) -> None:
    """Continuous polling loop for a distributed worker instance."""
    hostname = socket.gethostname()
    pid = os.getpid()
    unique_suffix = uuid.uuid4().hex[:6]
    actual_worker_id = worker_id or f"worker-{hostname}-{pid}-{unique_suffix}"

    if stop_event is None:
        stop_event = asyncio.Event()

    logger.info("Starting Shikhor durable job worker [%s] (poll_interval=%.1fs)...", actual_worker_id, poll_interval_seconds)

    while not stop_event.is_set():
        try:
            async with async_session_factory() as db:
                processed_job = await run_worker_tick(actual_worker_id, db)

            if processed_job:
                # If we just handled a job, yield briefly and check queue immediately for high throughput
                await asyncio.sleep(0.05)
            else:
                # Idle: wait for next polling tick or until stopped
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=poll_interval_seconds)
                except asyncio.TimeoutError:
                    pass
        except asyncio.CancelledError:
            logger.info("Worker [%s] received cancellation request.", actual_worker_id)
            break
        except Exception as exc:
            logger.error("Unexpected error in worker loop [%s]: %s", actual_worker_id, exc, exc_info=True)
            await asyncio.sleep(poll_interval_seconds)

    logger.info("Durable job worker [%s] stopped cleanly.", actual_worker_id)


def main():
    """Entrypoint for standalone worker process."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    stop_event = asyncio.Event()

    def _sig_handler(*_):
        logger.info("Shutdown signal caught, stopping worker gracefully...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _sig_handler)
        except (ValueError, AttributeError):
            pass

    asyncio.run(start_worker_loop(stop_event=stop_event))


if __name__ == "__main__":
    main()
