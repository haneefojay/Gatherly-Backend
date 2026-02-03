import uuid
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Notification, NotificationType
from .schemas import NotificationCreate


async def create_notification(
    session: AsyncSession, data: NotificationCreate
) -> Notification:
    """Create a new notification"""
    notification = Notification(
        user_id=data.user_id,
        type=data.type,
        title=data.title,
        message=data.message,
        link=data.link,
    )
    session.add(notification)
    await session.commit()
    await session.refresh(notification)

    # Real-time update via WebSocket
    try:
        from .websocket import manager
        from .selectors import get_unread_count
        from .schemas import NotificationResponse
        
        # Get response model for JSON serialization
        resp = NotificationResponse.model_validate(notification)
        unread_count = await get_unread_count(session, data.user_id)
        
        await manager.send_personal_message({
            "type": "new_notification",
            "notification": resp.model_dump(mode="json"),
            "unread_count": unread_count
        }, str(data.user_id))
    except Exception as e:
        print(f"Failed to send real-time notification: {e}")

    return notification


async def mark_as_read(
    session: AsyncSession, notification: Notification
) -> Notification:
    """Mark a specific notification as read"""
    notification.is_read = True
    await session.commit()
    await session.refresh(notification)
    return notification


async def mark_all_as_read(session: AsyncSession, user_id: uuid.UUID) -> int:
    """Mark all notifications for a user as read"""
    query = (
        update(Notification)
        .where(Notification.user_id == user_id, Notification.is_read == False)
        .values(is_read=True)
    )
    result = await session.execute(query)
    await session.commit()
    return result.rowcount
