"""RBAC Permission system and dependencies"""

import uuid
from typing import Annotated, Type, TypeVar

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth import TokenGenerator
from app.common.dependencies import get_session
from app.common.exceptions import (
    BadRequest,
    ForbiddenException,
    InternalServerError,
    NotFoundException,
    UnauthorizedException,
)
from app.core.database import DBBase
from app.core.settings import get_settings
from app.users.models import User, UserRole

settings = get_settings()

ModelT = TypeVar("ModelT", bound=DBBase)


# Define security scheme
security = HTTPBearer()

# Access token verifier
access_token_verifier = TokenGenerator(
    secret_key=settings.SECRET_KEY,
    expire_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,  # Not used for verification, but required by TokenGenerator
)


def require_resource_ownership(
    model: Type[ModelT],
    id_param: str = "id",
    owner_field: str = "created_by_id",
):
    """Dependency factory to require resource ownership or admin role.

    Fetches the resource by ID (from path params) and ensures the current user
    is either the owner (based on owner_field) or an Admin.

    Args:
        model: SQLAlchemy model class
        id_param: Name of the path parameter containing the resource ID
        owner_field: Name of the model field containing the owner's ID

    Returns:
        The requested resource instance
    """

    async def dependency(
        request: Request,
        session: AsyncSession = Depends(get_session),
        user: User = Depends(get_current_user),
    ) -> ModelT:
        resource_id = request.path_params.get(id_param)
        if not resource_id:
            raise InternalServerError(f"Path parameter '{id_param}' not found")

        try:
            # Handle UUID conversion if necessary
            resource_uuid = uuid.UUID(str(resource_id))
        except ValueError:
            raise BadRequest("Invalid ID format")

        resource = await session.get(model, resource_uuid)
        if not resource:
            raise NotFoundException(f"{model.__name__} with ID {resource_id} not found")

        # Check permission: Admin or Owner
        if user.role != UserRole.ADMIN:
            owner_id = getattr(resource, owner_field, None)
            if owner_id != user.id:
                raise ForbiddenException("Only the creator or an admin can perform this action")

        return resource

    return dependency


async def get_current_user(
    token_creds: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token

    Args:
        token_creds: HTTPBearer credentials (automatically extracts "Bearer <token>")
        session: Database session

    Returns:
        Current user instance

    Raises:
        Unauthorized: If token is missing or invalid
    """
    token = token_creds.credentials

    user_id_str = await access_token_verifier.verify(token, "user")

    if not user_id_str:
        raise Unauthorized("Invalid access token")

    user_id = uuid.UUID(user_id_str)

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


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
OrganizerOrAdminUser = Annotated[
    User, Depends(require_role(UserRole.ADMIN, UserRole.ORGANIZER))
]
