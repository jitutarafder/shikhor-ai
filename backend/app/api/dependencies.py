"""FastAPI authentication and authorization dependencies."""

from typing import Annotated, Any, Callable, List, Optional, Union
from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.db.service_bridge import get_mongo_registry, is_mongodb_backend
from app.db.session import get_db_session
from app.modules.users.models import User, UserRole


async def get_current_user(
    authorization: Annotated[str, Header()] = None,
    db: AsyncSession = Depends(get_db_session),
) -> Any:
    """Validates access token and resolves current authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(
            code="UNAUTHENTICATED",
            message="Valid Bearer access token is required.",
        )

    token = authorization.split(" ")[1]
    payload = decode_token(token, expected_type="access")
    user_id = payload.get("sub")

    if is_mongodb_backend():
        reg = get_mongo_registry()
        user = reg.users.find_by_id(user_id)
        if not user:
            raise UnauthorizedException(code="USER_NOT_FOUND", message="User account no longer exists.")
        if not user.is_active:
            raise ForbiddenException(code="ACCOUNT_INACTIVE", message="Account is deactivated.")
        return user

    stmt = (
        select(User)
        .options(
            selectinload(User.farmer_profile),
            selectinload(User.owner_profile),
            selectinload(User.buyer_profile),
            selectinload(User.expert_profile),
        )
        .where(User.id == user_id)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException(code="USER_NOT_FOUND", message="User account no longer exists.")

    if not user.is_active:
        raise ForbiddenException(code="ACCOUNT_INACTIVE", message="Account is deactivated.")

    return user


def require_role(*allowed_roles: UserRole) -> Callable:
    """Dependency factory checking that user holds at least one allowed role."""
    allowed_str_roles = {
        r.value if hasattr(r, "value") else str(r) for r in allowed_roles
    }

    async def role_checker(current_user: Any = Depends(get_current_user)) -> Any:
        user_role_str = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )
        if user_role_str not in allowed_str_roles:
            raise ForbiddenException(
                code="FORBIDDEN_ROLE",
                message="You do not have permission to perform this action.",
            )
        return current_user

    return role_checker


async def get_optional_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db_session),
) -> Any | None:
    """Optionally resolves current user if Bearer token is provided without failing on unauthenticated."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        payload = decode_token(token, expected_type="access")
        user_id = payload.get("sub")
        if not user_id:
            return None

        if is_mongodb_backend():
            reg = get_mongo_registry()
            user = reg.users.find_by_id(user_id)
            if user and user.is_active:
                return user
            return None

        stmt = (
            select(User)
            .options(
                selectinload(User.farmer_profile),
                selectinload(User.owner_profile),
                selectinload(User.buyer_profile),
                selectinload(User.expert_profile),
            )
            .where(User.id == user_id)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user and user.is_active:
            return user
    except Exception:
        return None
    return None

