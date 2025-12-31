"""User authentication and management services"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth import TokenGenerator
from app.common.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.settings import get_settings
from app.users.models import RefreshToken, User, UserRole
from app.users.schemas import UserCreate

settings = get_settings()
ph = PasswordHasher()

# Token generators
access_token_generator = TokenGenerator(
    secret_key=settings.SECRET_KEY,
    expire_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
)

refresh_token_generator = TokenGenerator(
    secret_key=settings.SECRET_KEY,
    expire_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60,
)


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user with hashed password

    Args:
        session: Database session
        user_data: User creation data

    Returns:
        Created user instance

    Raises:
        ValidationException: If email already exists
    """
    # Check if email already exists
    result = await session.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ValidationException("Email already registered")

    # Hash password
    hashed_password = ph.hash(user_data.password)

    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> User | None:
    """Authenticate user with email and password

    Args:
        session: Database session
        email: User email
        password: User password

    Returns:
        User instance if authentication successful, None otherwise
    """
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    try:
        ph.verify(user.hashed_password, password)
        return user
    except VerifyMismatchError:
        return None


async def create_access_token(user: User) -> str:
    """Create JWT access token for user

    Args:
        user: User instance

    Returns:
        JWT access token string
    """
    sub = f"user-{user.id}"
    return await access_token_generator.generate(sub, token_type="access")


async def create_refresh_token(session: AsyncSession, user: User) -> str:
    """Create and store refresh token for user

    Args:
        session: Database session
        user: User instance

    Returns:
        JWT refresh token string
    """
    # Generate refresh token
    sub = f"user-{user.id}"
    token = await refresh_token_generator.generate(sub, token_type="refresh")

    # Hash token for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Store refresh token in database
    refresh_token = RefreshToken(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    session.add(refresh_token)
    await session.commit()

    return token


async def verify_refresh_token(session: AsyncSession, token: str) -> User:
    """Verify refresh token and return associated user

    Args:
        session: Database session
        token: Refresh token string

    Returns:
        User instance

    Raises:
        UnauthorizedException: If token is invalid or expired
    """
    # Verify token signature and extract user ID
    user_id_str = await refresh_token_generator.verify(token, "user")

    if not user_id_str:
        raise UnauthorizedException("Invalid refresh token")

    user_id = uuid.UUID(user_id_str)

    # Hash token to check against database
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Check if token exists and is not revoked
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False,  # noqa: E712
            RefreshToken.expires_at > datetime.utcnow(),
        )
    )
    refresh_token = result.scalar_one_or_none()

    if not refresh_token:
        raise UnauthorizedException("Invalid or expired refresh token")

    # Get user
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    return user


async def revoke_refresh_token(session: AsyncSession, token: str) -> None:
    """Revoke a refresh token

    Args:
        session: Database session
        token: Refresh token string

    Raises:
        UnauthorizedException: If token is invalid
    """
    # Hash token
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    # Find and revoke token
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token:
        refresh_token.is_revoked = True
        await session.commit()


async def update_user_role(
    session: AsyncSession, user_id: uuid.UUID, new_role: UserRole
) -> User:
    """Update user role (Admin only)

    Args:
        session: Database session
        user_id: User ID to update
        new_role: New role to assign

    Returns:
        Updated user instance

    Raises:
        NotFoundException: If user not found
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User not found")

    user.role = new_role
    await session.commit()
    await session.refresh(user)

    return user
