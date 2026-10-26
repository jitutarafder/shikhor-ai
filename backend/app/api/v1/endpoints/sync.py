"""Synchronization API endpoints.

Strictly complies with:
- AGENTS.md Rule 11: Authoritative backend validation.
- AGENTS.md Rule 21: Idempotent offline mutations.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.modules.sync.schemas import SyncBatchRequest, SyncBatchResponse
from app.modules.sync.service import process_sync_batch
from app.modules.users.models import User

router = APIRouter(prefix="/sync", tags=["Offline Synchronization"])


@router.post("/batch", response_model=SyncBatchResponse, status_code=status.HTTP_200_OK)
async def sync_batch(
    req: SyncBatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> SyncBatchResponse:
    """Processes a batch of offline-queued mutations idempotently for the authenticated user."""
    return await process_sync_batch(db=db, user=current_user, req=req)


@router.get("/status", status_code=status.HTTP_200_OK)
async def sync_status(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Health and status check for synchronization service."""
    return {
        "status": "ready",
        "userId": current_user.id,
        "maxBatchSize": 50,
        "supportedOperations": [
            "CREATE_RENTAL_REQUEST",
            "CREATE_CROP_LISTING",
            "SEND_MESSAGE",
        ],
    }
