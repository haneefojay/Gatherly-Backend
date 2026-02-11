
"""User profile management services"""

import uuid
from datetime import datetime
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.users.models import RefreshToken, User, UserSession
from app.users.schemas import ProfileUpdate, SessionResponse

ph = PasswordHasher()

async def update_user_profile(
    session: AsyncSession, user: User, profile_data: ProfileUpdate
) -> User:
    """Update user profile information

    Args:
        session: Database session
        user: Current user
        profile_data: Profile update data

    Returns:
        Updated user instance

    Raises:
        ValidationException: If username already taken
    """
    from sqlalchemy.orm import selectinload
    from app.users.models import UserProfile
    
    if profile_data.username and profile_data.username != user.username:
        result = await session.execute(
            select(User).where(User.username == profile_data.username)
        )
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ValidationException("Username already taken")

    update_data = profile_data.model_dump(exclude_unset=True)
    
    # Separate User fields from UserProfile fields
    user_fields = {"full_name", "username"}
    profile_fields = {"bio", "phone", "location", "social_links"}
    
    # Update User table fields
    for field, value in update_data.items():
        if field in user_fields:
            setattr(user, field, value)
    
    # Update UserProfile table fields
    profile_updates = {k: v for k, v in update_data.items() if k in profile_fields}
    if profile_updates:
        # Load or create profile
        result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == user.id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            profile = UserProfile(user_id=user.id, **profile_updates)
            session.add(profile)
        else:
            for field, value in profile_updates.items():
                setattr(profile, field, value)

    await session.commit()
    
    # Eagerly load profile to avoid lazy-loading issues
    result = await session.execute(
        select(User).options(selectinload(User.profile)).where(User.id == user.id)
    )
    user = result.scalar_one()

    return user


async def change_user_password(
    session: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    """Change user password with history check and session invalidation

    Args:
        session: Database session
        user: Current user
        current_password: Current password for verification
        new_password: New password to set

    Raises:
        UnauthorizedException: If current password is incorrect
        ValidationException: If password was used recently
    """
    from app.users.models import PasswordHistory, RefreshToken
    from app.common.exceptions import ValidationException
    
    try:
        ph.verify(user.hashed_password, current_password)
    except VerifyMismatchError:
        raise UnauthorizedException("Current password is incorrect")

    result = await session.execute(
        select(PasswordHistory)
        .where(PasswordHistory.user_id == user.id)
        .order_by(PasswordHistory.created_at.desc())
        .limit(5)
    )
    password_history = result.scalars().all()
    
    for old_password in password_history:
        try:
            ph.verify(old_password.hashed_password, new_password)
            raise ValidationException("Password was used recently. Please choose a different password.")
        except VerifyMismatchError:
            continue

    password_record = PasswordHistory(
        user_id=user.id,
        hashed_password=user.hashed_password
    )
    session.add(password_record)
    
    user.hashed_password = ph.hash(new_password)
    
    await session.execute(
        select(RefreshToken)
        .where(RefreshToken.user_id == user.id)
    )
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.user_id == user.id)
    )
    tokens = result.scalars().all()
    
    for token in tokens:
        token.is_revoked = True
    
    await session.commit()


async def create_user_session(
    session: AsyncSession,
    user_id: uuid.UUID,
    refresh_token_id: uuid.UUID,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> UserSession:
    """Create a new user session

    Args:
        session: Database session
        user_id: User ID
        refresh_token_id: Associated refresh token ID
        device_info: Device/browser information
        ip_address: IP address

    Returns:
        Created session instance
    """
    from app.users.models import UserSession

    user_session = UserSession(
        user_id=user_id,
        refresh_token_id=refresh_token_id,
        device_info=device_info,
        ip_address=ip_address,
        last_active_at=datetime.utcnow(),
    )

    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)

    return user_session


async def get_user_sessions(
    session: AsyncSession, user_id: uuid.UUID, current_token_id: Optional[uuid.UUID] = None
) -> list[SessionResponse]:
    """Get all active sessions for a user

    Args:
        session: Database session
        user_id: User ID
        current_token_id: Current refresh token ID to mark as current

    Returns:
        List of session responses
    """
    from app.users.models import UserSession

    result = await session.execute(
        select(UserSession)
        .join(RefreshToken, UserSession.refresh_token_id == RefreshToken.id)
        .where(
            UserSession.user_id == user_id,
            RefreshToken.is_revoked == False,
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .order_by(UserSession.last_active_at.desc())
    )
    sessions = result.scalars().all()

    return [
        SessionResponse(
            id=str(s.id),
            device_info=s.device_info,
            ip_address=s.ip_address,
            last_active_at=s.last_active_at.isoformat() if s.last_active_at else "",
            created_at=s.created_at.isoformat() if s.created_at else "",
            is_current=(s.refresh_token_id == current_token_id),
        )
        for s in sessions
    ]


async def revoke_user_session(
    session: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID
) -> None:
    """Revoke a specific user session

    Args:
        session: Database session
        user_id: User ID (for authorization)
        session_id: Session ID to revoke

    Raises:
        NotFoundException: If session not found
        UnauthorizedException: If session doesn't belong to user
    """
    from app.users.models import UserSession

    result = await session.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    user_session = result.scalar_one_or_none()

    if not user_session:
        raise NotFoundException("Session not found")

    if user_session.user_id != user_id:
        raise UnauthorizedException("Session does not belong to user")

    result = await session.execute(
        select(RefreshToken).where(RefreshToken.id == user_session.refresh_token_id)
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token:
        refresh_token.is_revoked = True

    await session.commit()
