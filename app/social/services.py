"""Social interaction services"""

from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequest, NotFoundException
from app.social.models import Follow
from app.users.models import User


async def follow_user(session: AsyncSession, follower_id: UUID, username: str) -> None:
    """Follow a user by username"""
    
    # Get target user
    result = await session.execute(select(User).where(User.username == username))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise NotFoundException("User not found")
        
    if target_user.id == follower_id:
        raise BadRequest("You cannot follow yourself")
        
    # Check if already following
    existing = await session.execute(
        select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == target_user.id
        )
    )
    if existing.scalar_one_or_none():
        return  # Already following, idempotent
        
    # Create follow
    follow = Follow(follower_id=follower_id, following_id=target_user.id)
    session.add(follow)
    
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        # Race condition handling
        return


async def unfollow_user(session: AsyncSession, follower_id: UUID, username: str) -> None:
    """Unfollow a user by username"""
    
    # Get target user
    result = await session.execute(select(User).where(User.username == username))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise NotFoundException("User not found")
        
    # Delete follow
    await session.execute(
        delete(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == target_user.id
        )
    )
    await session.commit()
