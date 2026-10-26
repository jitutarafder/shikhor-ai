"""Pydantic v2 schemas for Durable Jobs API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.modules.jobs.models import JobStatus


class JobEnqueueRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    jobType: str = Field(alias="job_type", max_length=100)
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=10)
    delaySeconds: int = Field(default=0, ge=0, alias="delay_seconds")
    maxAttempts: int = Field(default=3, ge=1, le=10, alias="max_attempts")


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=(), populate_by_name=True)

    id: str
    jobType: str = Field(validation_alias="job_type", serialization_alias="jobType")
    payload: Dict[str, Any]
    status: JobStatus
    priority: int
    attempts: int
    maxAttempts: int = Field(validation_alias="max_attempts", serialization_alias="maxAttempts")
    lastError: Optional[str] = Field(None, validation_alias="last_error", serialization_alias="lastError")
    resultData: Optional[Dict[str, Any]] = Field(None, validation_alias="result_data", serialization_alias="resultData")
    lockedBy: Optional[str] = Field(None, validation_alias="locked_by", serialization_alias="lockedBy")
    scheduledAt: datetime = Field(validation_alias="scheduled_at", serialization_alias="scheduledAt")
    createdAt: datetime = Field(validation_alias="created_at", serialization_alias="createdAt")
    completedAt: Optional[datetime] = Field(None, validation_alias="completed_at", serialization_alias="completedAt")


class JobStatsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    pending: int
    processing: int
    completed: int
    failed: int
    deadLetter: int = Field(serialization_alias="deadLetter")
    activeWorkers: int = Field(serialization_alias="activeWorkers")
