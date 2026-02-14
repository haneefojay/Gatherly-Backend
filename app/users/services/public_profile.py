"""Public profile service — view profiles by username, public events, and attending events"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.attendees.models import Attendee, AttendeeStatus
from app.common.exceptions import NotFoundException
from app.events.models import Event, EventStatus, event_organizers
from app.users.models import User, UserPreferences, UserProfile
from app.users.schemas import PublicProfileResponse


async def get_public_profile(session: AsyncSession, username: str) -> PublicProfileResponse:
    """Fetch a user's public profile by username"""

    result = await session.execute(
        select(User)
        .options(selectinload(User.profile), selectinload(User.preferences))
        .where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise NotFoundException("User not found")

    prefs = user.preferences
    if prefs and prefs.profile_visibility == "private":
        raise NotFoundException("User not found")

    organized_count_result = await session.execute(
        select(func.count())
        .select_from(Event)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(event_organizers.c.user_id == user.id)
    )
    events_organized_count = organized_count_result.scalar() or 0

    attended_count_result = await session.execute(
        select(func.count())
        .select_from(Attendee)
        .where(
            Attendee.user_id == user.id,
            Attendee.status.in_([AttendeeStatus.REGISTERED, AttendeeStatus.CHECKED_IN]),
        )
    )
    events_attended_count = attended_count_result.scalar() or 0

    return PublicProfileResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        location=user.location,
        avatar_url=user.avatar_url,
        cover_photo_url=user.cover_photo_url,
        social_links=user.social_links,
        events_organized_count=events_organized_count,
        events_attended_count=events_attended_count,
        member_since=user.created_at,
    )


async def get_user_public_events(
    session: AsyncSession, username: str, limit: int = 10, offset: int = 0
) -> tuple[list, int]:
    """Get events created/organized by user (only public-visible statuses)"""

    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    public_statuses = [EventStatus.UPCOMING, EventStatus.ONGOING, EventStatus.COMPLETED]

    base_query = (
        select(Event)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(
            event_organizers.c.user_id == user.id,
            Event.status.in_(public_statuses),
        )
    )

    count_result = await session.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    events_result = await session.execute(
        base_query
        .options(selectinload(Event.organizers))
        .order_by(Event.start_date.desc())
        .offset(offset)
        .limit(limit)
    )
    events = events_result.scalars().all()

    return events, total


async def get_user_attending_events(
    session: AsyncSession, username: str, limit: int = 10, offset: int = 0
) -> tuple[list, int]:
    """Get events a user is attending (respects show_attending_events privacy)"""

    result = await session.execute(
        select(User)
        .options(selectinload(User.preferences))
        .where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    prefs = user.preferences
    if prefs and not prefs.show_attending_events:
        return [], 0

    base_query = (
        select(Event)
        .join(Attendee, Attendee.event_id == Event.id)
        .where(
            Attendee.user_id == user.id,
            Attendee.status.in_([AttendeeStatus.REGISTERED, AttendeeStatus.CHECKED_IN]),
            Event.status.in_([EventStatus.UPCOMING, EventStatus.ONGOING]),
        )
    )

    count_result = await session.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    events_result = await session.execute(
        base_query
        .options(selectinload(Event.organizers))
        .order_by(Event.start_date.asc())
        .offset(offset)
        .limit(limit)
    )
    events = events_result.scalars().all()

    return events, total
