"""RBAC Permission system and dependencies"""

import uuid
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth import TokenGenerator
from app.common.dependencies import get_session
from app.common.exceptions import Forbidden, Unauthorized
from app.core.settings import get_settings
from app.users.models import User, UserRole

settings = get_settings()

# Access token verifier
access_token_verifier = TokenGenerator(
    secret_key=settings.SECRET_KEY,
    expire_in=15,  # Not used for verification, but required by TokenGenerator
)


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token

    Args:
        authorization: Authorization header with Bearer token
        session: Database session

    Returns:
        Current user instance

    Raises:
        Unauthorized: If token is missing or invalid
    """
    if not authorization:
        raise Unauthorized("Authorization header missing")

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise Unauthorized("Invalid authorization header format")

    token = parts[1]

    # Verify token and extract user ID
    user_id_str = await access_token_verifier.verify(token, "user")

    if not user_id_str:
        raise Unauthorized("Invalid access token")

    user_id = uuid.UUID(user_id_str)

    # Get user from database
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise Unauthorized("User not found or inactive")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user (alias for clarity)"""
    return current_user


def require_role(*allowed_roles: UserRole):
    """Dependency factory to require specific roles

    Args:
        *allowed_roles: Roles that are allowed to access the endpoint

    Returns:
        Dependency function that checks user role

    Example:
        @app.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """

    async def check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise Forbidden(
                f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user

    return check_role


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if admin

    Raises:
        Forbidden: If user is not admin
    """
    if current_user.role != UserRole.ADMIN:
        raise Forbidden("Admin access required")
    return current_user


async def require_organizer_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require organizer or admin role

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if organizer or admin

    Raises:
        Forbidden: If user is neither organizer nor admin
    """
    if current_user.role not in [UserRole.ORGANIZER, UserRole.ADMIN]:
        raise Forbidden("Organizer or Admin access required")
    return current_user


# Type aliases for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
OrganizerOrAdminUser = Annotated[User, Depends(require_organizer_or_admin)]
