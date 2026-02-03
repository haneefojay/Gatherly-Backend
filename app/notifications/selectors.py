import uuid
from typing import List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Notification
from app.common.types import PaginationParamsType


async def get_notifications(
    session: AsyncSession,
    user_id: uuid.UUID,
    pagination: PaginationParamsType | None = None,
    is_read: bool | None = None,
) -> tuple[List[Notification], int]:
    """Get notifications for a user with filtering and pagination"""
    
    query = select(Notification).where(Notification.user_id == user_id)
    
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
        
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Sort and paginate
    query = query.order_by(Notification.created_at.desc())
    
    if pagination:
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
    result = await session.execute(query)
    notifications = list(result.scalars().all())
    
    return notifications, total


async def get_unread_count(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Get count of unread notifications for a user"""
    query = select(func.count()).where(
        and_(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    )
    result = await session.execute(query)
    return result.scalar() or 0


async def get_notification_by_id(
    session: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
) -> Notification | None:
    """Get a specific notification for a user"""
    query = select(Notification).where(
        and_(
            Notification.id == notification_id,
            Notification.user_id == user_id
        )
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()
