"""Public profile service — view profiles by username, public events, and attending events"""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.attendees.models import Attendee, AttendeeStatus
from app.common.exceptions import NotFoundException
from app.events.models import Event, EventStatus, event_organizers
from app.social.models import Review, Follow
from app.users.models import User, UserPreferences, UserProfile
from app.users.schemas import PublicProfileResponse


async def get_public_profile(
    session: AsyncSession, username: str, current_user_id: UUID | None = None
) -> PublicProfileResponse:
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

    # Check if current user is following
    is_following = False
    if current_user_id and current_user_id != user.id:
        follow_result = await session.execute(
            select(Follow).where(
                Follow.follower_id == current_user_id,
                Follow.following_id == user.id
            )
        )
        is_following = follow_result.scalar_one_or_none() is not None

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

    # Calculate average rating and review count for events organized by this user
    rating_result = await session.execute(
        select(func.avg(Review.rating), func.count(Review.id))
        .join(Event, Review.event_id == Event.id)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(event_organizers.c.user_id == user.id)
    )
    avg_rating, review_count = rating_result.one()
    
    # Round to 1 decimal place if rating exists
    average_rating = round(float(avg_rating), 1) if avg_rating else None

    # Calculate rating distribution
    dist_result = await session.execute(
        select(Review.rating, func.count(Review.id))
        .join(Event, Review.event_id == Event.id)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(event_organizers.c.user_id == user.id)
        .group_by(Review.rating)
    )
    dist_map = {row[0]: row[1] for row in dist_result.all()}
    rating_distribution = {i: dist_map.get(i, 0) for i in range(1, 6)}

    return PublicProfileResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        job_title=user.job_title,
        bio=user.bio,
        location=user.location,
        avatar_url=user.avatar_url,
        cover_photo_url=user.cover_photo_url,
        social_links=user.social_links,
        events_organized_count=events_organized_count,
        events_attended_count=events_attended_count,
        average_rating=average_rating,
        review_count=review_count or 0,
        rating_distribution=rating_distribution,
        is_following=is_following,
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


async def get_user_reviews(
    session: AsyncSession, username: str, limit: int = 10, offset: int = 0
) -> tuple[list, int]:
    """Get reviews received by user (for events they organized)"""

    result = await session.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")

    base_query = (
        select(Review)
        .join(Event, Review.event_id == Event.id)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(event_organizers.c.user_id == user.id)
    )

    count_result = await session.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = count_result.scalar() or 0

    reviews_result = await session.execute(
        base_query
        .options(selectinload(Review.user), selectinload(Review.event))
        .order_by(Review.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    reviews = reviews_result.scalars().all()

    return reviews, total
