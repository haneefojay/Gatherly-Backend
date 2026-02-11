"""Avatar upload and management services"""

import uuid
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import ValidationException
from app.core.settings import get_settings
from app.core.storage import get_storage_provider
from app.users.models import User, UserProfile

settings = get_settings()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_SIZE_BYTES = settings.MAX_AVATAR_SIZE_MB * 1024 * 1024


def validate_avatar_file(file: UploadFile) -> None:
    """Validate avatar file type and size
    
    Args:
        file: Uploaded file
        
    Raises:
        ValidationException: If file is invalid
    """
    if not file.filename:
        raise ValidationException("No filename provided")
    
    file_ext = file.filename.lower()[file.filename.rfind("."):]
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(
            f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if file.size and file.size > MAX_SIZE_BYTES:
        raise ValidationException(
            f"File too large. Maximum size: {settings.MAX_AVATAR_SIZE_MB}MB"
        )


async def upload_user_avatar(
    session: AsyncSession, user: User, file: UploadFile
) -> str:
    """Upload user avatar and update profile
    
    Args:
        session: Database session
        user: Current user
        file: Avatar image file
        
    Returns:
        Public URL of uploaded avatar
        
    Raises:
        ValidationException: If file is invalid
    """
    from sqlalchemy import select
    
    validate_avatar_file(file)
    
    storage = get_storage_provider()
    
    # Load profile to check for existing avatar
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    
    # Delete old avatar if exists
    if profile and profile.avatar_url:
        try:
            await storage.delete(profile.avatar_url)
        except Exception:
            pass
    
    # Upload new avatar
    folder = f"avatars/{user.id}"
    avatar_url = await storage.upload(
        file.file,
        file.filename,
        file.content_type or "image/jpeg",
        folder=folder
    )
    
    # Update or create profile with avatar_url
    if not profile:
        profile = UserProfile(user_id=user.id, avatar_url=avatar_url)
        session.add(profile)
    else:
        profile.avatar_url = avatar_url
    
    await session.commit()
    await session.refresh(profile)
    
    return avatar_url


async def delete_user_avatar(session: AsyncSession, user: User) -> None:
    """Delete user avatar
    
    Args:
        session: Database session
        user: Current user
    """
    from sqlalchemy import select
    
    # Load profile
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile or not profile.avatar_url:
        return
    
    storage = get_storage_provider()
    
    try:
        await storage.delete(profile.avatar_url)
    except Exception:
        pass
    
    profile.avatar_url = None
    await session.commit()
