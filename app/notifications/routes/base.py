import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session, pagination_params
from app.common.permissions import CurrentUser
from app.common.schemas import PaginatedResponse, ErrorResponse
from app.common.types import PaginationParamsType
from ..selectors import get_notifications, get_unread_count, get_notification_by_id
from ..services import mark_as_read, mark_all_as_read
from ..schemas import NotificationResponse, NotificationUnreadCount
from ..websocket import manager
from fastapi import WebSocket, WebSocketDisconnect
from app.common.permissions import access_token_verifier
from app.core.rate_limit import role_based_rate_limiter
from app.core.settings import get_settings

settings = get_settings()
rate_limit_deps = [Depends(role_based_rate_limiter)] if not settings.TESTING else []

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[NotificationResponse],
    summary="Get user notifications",
    description="Get a paginated list of notifications for the current user",
    dependencies=rate_limit_deps,
)
async def list_notifications(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParamsType = Depends(pagination_params),
    is_read: bool | None = Query(None),
):
    """List current user notifications"""
    notifications, total = await get_notifications(
        session, current_user.id, pagination, is_read
    )
    
    return PaginatedResponse(
        items=notifications,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=(total + pagination.size - 1) // pagination.size,
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCount,
    summary="Get unread notifications count",
    dependencies=rate_limit_deps,
)
async def unread_count_endpoint(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Get count of unread notifications for current user"""
    count = await get_unread_count(session, current_user.id)
    return {"count": count}


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read",
    responses={404: {"model": ErrorResponse}},
    dependencies=rate_limit_deps,
)
async def mark_read_endpoint(
    notification_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Mark a specific notification as read"""
    notification = await get_notification_by_id(session, notification_id, current_user.id)
    if not notification:
        from app.common.exceptions import NotFoundException
        raise NotFoundException("Notification not found")
        
    return await mark_as_read(session, notification)


@router.patch(
    "/read-all",
    summary="Mark all notifications as read",
    dependencies=rate_limit_deps,
)
async def mark_all_read_endpoint(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Mark all notifications for current user as read"""
    count = await mark_all_as_read(session, current_user.id)
    return {"message": f"{count} notifications marked as read"}


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    token: str = Query(...),
):
    """WebSocket endpoint for real-time notifications"""
    # Verify token
    try:
        verified_sub = await access_token_verifier.verify(token, "user")
        if not verified_sub:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Normalize to avoid hyphen mismatch
        if uuid.UUID(verified_sub) != uuid.UUID(user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive, though we mostly just push from server
            data = await websocket.receive_text()
            # We don't expect messages from client, but we could handle them if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        manager.disconnect(websocket, user_id)
