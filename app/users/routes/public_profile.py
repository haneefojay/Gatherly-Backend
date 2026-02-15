"""Public profile routes — view profiles and events by username"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.permissions import OptionalCurrentUser
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
    current_user: OptionalCurrentUser = None,
):
    """Get public profile by username"""
    return await get_public_profile(
        session, 
        username, 
        current_user.id if current_user else None
    )


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


@router.get(
    "/{username}/reviews",
    summary="Get reviews received by user",
    description="View reviews for events organized by the user",
)
async def get_reviews(
    username: str,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """Get reviews received by user"""
    from app.social.schemas import ReviewResponse
    from app.users.services.public_profile import get_user_reviews

    reviews, total = await get_user_reviews(session, username, limit, offset)
    
    return {
        "reviews": [
            ReviewResponse(
                id=r.id,
                rating=r.rating,
                title=r.title,
                content=r.content,
                helpful_count=r.helpful_count,
                created_at=r.created_at,
                event_id=r.event_id,
                event_title=r.event.title if r.event else None,
                user_id=r.user_id,
                user_name=r.user.full_name,
                user_avatar=r.user.avatar_url,
            )
            for r in reviews
        ],
        "total": total,
    }
