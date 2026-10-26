"""Centralized state transitions for Rental Requests.

Strictly complies with AGENTS.md Rule 14:
Allowed rental states: pending, accepted, rejected, cancelled, completed.
Any transition outside the transition map raises INVALID_STATE_TRANSITION.
"""

from typing import Set
from app.core.errors import ForbiddenException, ShikhorException
from app.modules.rentals.models import RentalRequest, RentalStatus

# Allowed state transition map: CurrentStatus -> Set of TargetStatuses
ALLOWED_RENTAL_TRANSITIONS: dict[RentalStatus, Set[RentalStatus]] = {
    RentalStatus.PENDING: {
        RentalStatus.ACCEPTED,
        RentalStatus.REJECTED,
        RentalStatus.CANCELLED,
    },
    RentalStatus.ACCEPTED: {
        RentalStatus.CANCELLED,
        RentalStatus.COMPLETED,
    },
    RentalStatus.REJECTED: set(),
    RentalStatus.CANCELLED: set(),
    RentalStatus.COMPLETED: set(),
}


def transition_rental_status(
    rental_request: RentalRequest,
    target_status: RentalStatus,
    actor_id: str,
    owner_id: str,
) -> RentalStatus:
    """Central domain transition function validating state rules and actor permissions."""
    current_status = rental_request.status

    # 1. Check if target status is in the allowed transition graph
    allowed_targets = ALLOWED_RENTAL_TRANSITIONS.get(current_status, set())
    if target_status not in allowed_targets:
        raise ShikhorException(
            code="INVALID_STATE_TRANSITION",
            message=f"Cannot transition rental request from '{current_status.value}' to '{target_status.value}'.",
            status_code=400,
        )

    # 2. Authorization rules based on actor (Rule 12: Object-level authorization)
    is_owner = (actor_id == owner_id)
    is_renter = (actor_id == rental_request.renter_id)

    if not (is_owner or is_renter):
        raise ForbiddenException(
            code="UNAUTHORIZED_RENTAL_ACTION",
            message="Only the equipment owner or the renter can update this request.",
        )

    # Specific actor transition permissions
    if target_status in (RentalStatus.ACCEPTED, RentalStatus.REJECTED) and not is_owner:
        raise ForbiddenException(
            code="OWNER_ACTION_REQUIRED",
            message="Only the equipment owner can accept or reject rental requests.",
        )

    rental_request.status = target_status
    return target_status
