"""Public profile routes — view profiles and events by username"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.events.schemas.response import EventResponse
from app.users.schemas import PublicProfileResponse
from app.users.services.public_profile import (
    get_public_profile,
    get_user_public_events,
    get_user_attending_events,
)

router = APIRouter()


@router.get(
    "/{username}",
    response_model=PublicProfileResponse,
    summary="Get public profile",
    description="View a user's public profile by username",
)
async def get_profile_by_username(
    username: str,
    session: AsyncSession = Depends(get_session),
):
    """Get public profile by username"""
    return await get_public_profile(session, username)


@router.get(
    "/{username}/events",
    summary="Get user's public events",
    description="View events organized by a user (only public-visible statuses)",
)
async def get_user_events(
    username: str,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get user's public events"""
    events, total = await get_user_public_events(session, username, limit, offset)
    return {
        "events": [EventResponse.model_validate(e) for e in events],
        "total": total,
    }


@router.get(
    "/{username}/attending",
    summary="Get events user is attending",
    description="View events a user is attending (respects privacy settings)",
)
async def get_user_attending(
    username: str,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get events user is attending"""
    events, total = await get_user_attending_events(session, username, limit, offset)
    return {
        "events": [EventResponse.model_validate(e) for e in events],
        "total": total,
    }
