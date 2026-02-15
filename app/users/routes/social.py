"""Social interaction routes (follow/unfollow)"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import Response

from app.common.dependencies import get_session
from app.common.permissions import CurrentUser
from app.social.services import follow_user, unfollow_user

router = APIRouter()


@router.post(
    "/{username}/follow",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Follow a user",
    description="Follow a user by their username",
)
async def follow(
    username: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Follow a user"""
    await follow_user(session, current_user.id, username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{username}/follow",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfollow a user",
    description="Unfollow a user by their username",
)
async def unfollow(
    username: str,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Unfollow a user"""
    await unfollow_user(session, current_user.id, username)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
