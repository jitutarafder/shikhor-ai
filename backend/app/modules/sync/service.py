"""Synchronization and Idempotent Offline Mutation execution service.

Strictly complies with:
- AGENTS.md Rule 11: Authoritative backend validation.
- AGENTS.md Rule 12: Object-level authorization policy.
- AGENTS.md Rule 21: Idempotent offline sync binding user, operation, and request hash.
"""

import hashlib
import json
from typing import Any, Dict
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ShikhorException
from app.modules.crop_marketplace.schemas import CropListingCreateRequest
from app.modules.crop_marketplace.service import create_crop_listing
from app.modules.messaging.service import send_message
from app.modules.rentals.schemas import RentalRequestCreate
from app.modules.rentals.service import create_rental
from app.modules.sync.models import IdempotencyRecord
from app.modules.sync.schemas import (
    SyncBatchRequest,
    SyncBatchResponse,
    SyncMutationItem,
    SyncMutationResult,
)
from app.modules.users.models import User


def _hash_payload(payload: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of mutation payload."""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


async def _execute_mutation(
    db: AsyncSession,
    user: User,
    mutation: SyncMutationItem,
) -> tuple[int, Any]:
    """Executes a single domain mutation according to operation name."""
    op = mutation.operationName.upper()

    if op == "CREATE_RENTAL_REQUEST":
        validated = RentalRequestCreate.model_validate(
            {**mutation.payload, "idempotencyKey": mutation.idempotencyKey}
        )
        rental = await create_rental(
            db=db,
            renter=user,
            req=validated,
        )
        return 201, {
            "id": rental.id,
            "equipmentId": rental.equipment_id,
            "renterId": rental.renter_id,
            "rentalDate": str(rental.rental_date),
            "durationUnits": rental.duration_units,
            "totalEstimatedPrice": rental.total_estimated_price,
            "status": rental.status.value,
        }

    elif op == "CREATE_CROP_LISTING":
        validated = CropListingCreateRequest.model_validate(mutation.payload)
        res = await create_crop_listing(db=db, farmer=user, req=validated)
        return 201, res.model_dump(mode="json")

    elif op == "SEND_MESSAGE":
        conv_id = mutation.payload.get("conversationId")
        content = mutation.payload.get("content")
        if not conv_id or not content:
            raise ShikhorException(
                code="INVALID_PAYLOAD",
                message="conversationId and content are required for SEND_MESSAGE",
                status_code=400,
            )
        res = await send_message(db=db, user=user, conversation_id=conv_id, content=content)
        return 201, res.model_dump(mode="json")

    else:
        raise ShikhorException(
            code="UNSUPPORTED_OPERATION",
            message=f"Operation '{mutation.operationName}' is not supported for offline sync.",
            status_code=400,
        )


async def process_sync_batch(
    db: AsyncSession,
    user: User,
    req: SyncBatchRequest,
) -> SyncBatchResponse:
    """Processes a batch of offline queued mutations idempotently (Rule 21)."""
    results = []
    synced_count = 0
    failed_count = 0

    for mut in req.mutations:
        payload_hash = _hash_payload(mut.payload)

        # 1. Check existing idempotency record
        existing_stmt = select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user.id,
            IdempotencyRecord.operation == mut.operationName,
            IdempotencyRecord.idempotency_key == mut.idempotencyKey,
        )
        existing = await db.scalar(existing_stmt)

        if existing:
            # Check for conflict vs exact duplicate
            if existing.request_hash == payload_hash:
                # Identical duplicate submission -> Return cached response (Rule 21)
                try:
                    cached_data = json.loads(existing.response_body)
                except Exception:
                    cached_data = existing.response_body

                results.append(
                    SyncMutationResult(
                        localUuid=mut.localUuid,
                        status="success",
                        statusCode=existing.response_status,
                        message="Operation already processed idempotently.",
                        data=cached_data,
                    )
                )
                synced_count += 1
                continue
            else:
                # Key reused with different payload -> 409 Conflict
                results.append(
                    SyncMutationResult(
                        localUuid=mut.localUuid,
                        status="conflict",
                        statusCode=409,
                        code="IDEMPOTENCY_CONFLICT",
                        message="Idempotency key was already used with different payload.",
                    )
                )
                failed_count += 1
                continue

        # 2. Execute fresh mutation
        try:
            status_code, response_data = await _execute_mutation(db, user, mut)

            # 3. Store idempotency record
            record = IdempotencyRecord(
                user_id=user.id,
                operation=mut.operationName,
                idempotency_key=mut.idempotencyKey,
                request_hash=payload_hash,
                response_status=status_code,
                response_body=json.dumps(response_data, default=str),
            )
            db.add(record)
            await db.commit()

            results.append(
                SyncMutationResult(
                    localUuid=mut.localUuid,
                    status="success",
                    statusCode=status_code,
                    message="Mutation successfully executed and synchronized.",
                    data=response_data,
                )
            )
            synced_count += 1

        except ValidationError as ve:
            await db.rollback()
            results.append(
                SyncMutationResult(
                    localUuid=mut.localUuid,
                    status="error",
                    statusCode=422,
                    code="VALIDATION_ERROR",
                    message="Payload validation failed on server.",
                    data={"errors": ve.errors()},
                )
            )
            failed_count += 1

        except ShikhorException as se:
            await db.rollback()
            results.append(
                SyncMutationResult(
                    localUuid=mut.localUuid,
                    status="error",
                    statusCode=se.status_code,
                    code=se.code,
                    message=se.message,
                )
            )
            failed_count += 1

        except Exception as e:
            await db.rollback()
            results.append(
                SyncMutationResult(
                    localUuid=mut.localUuid,
                    status="error",
                    statusCode=500,
                    code="INTERNAL_SYNC_ERROR",
                    message="An unexpected error occurred while processing mutation.",
                )
            )
            failed_count += 1

    return SyncBatchResponse(
        results=results,
        syncedCount=synced_count,
        failedCount=failed_count,
    )
