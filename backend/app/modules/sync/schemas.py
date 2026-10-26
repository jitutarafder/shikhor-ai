"""Synchronization and Idempotency Pydantic schemas.

Strictly complies with:
- AGENTS.md Rule 11: Authoritative backend validation.
- AGENTS.md Rule 21: Idempotent offline mutations with local UUID, key, operation name, and payload.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SyncMutationItem(BaseModel):
    localUuid: str = Field(..., min_length=10, max_length=64)
    idempotencyKey: str = Field(..., min_length=8, max_length=128)
    operationName: str = Field(..., min_length=3, max_length=100)
    payload: Dict[str, Any]
    createdAt: Optional[str] = None


class SyncBatchRequest(BaseModel):
    mutations: List[SyncMutationItem] = Field(..., max_length=50)


class SyncMutationResult(BaseModel):
    localUuid: str
    status: str  # 'success' | 'conflict' | 'error'
    statusCode: int
    code: Optional[str] = None
    message: str
    data: Optional[Any] = None


class SyncBatchResponse(BaseModel):
    results: List[SyncMutationResult]
    syncedCount: int
    failedCount: int
