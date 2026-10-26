"""Durable background job models for distributed worker execution.

Complies with AGENTS.md Rule 25:
- Durable queue persisting critical background work across restarts.
- Concurrency and duplicate execution prevention.
- Exponential backoff retry and Dead Letter Queue (DLQ).
"""

from datetime import datetime, timezone
import enum
import uuid
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Enum, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class Job(Base):
    """Represents a durable background job executed by distributed workers."""

    __tablename__ = "background_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, comment="Registered handler identifier"
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status_enum", native_enum=False),
        default=JobStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, index=True, comment="Higher integer = higher priority"
    )
    attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    result_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )
    locked_by: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True, comment="Worker process hostname or ID"
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
