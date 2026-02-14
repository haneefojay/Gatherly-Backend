"""User activity and stats service — aggregated counts and activity timeline"""

from datetime import datetime

from sqlalchemy import select, func, union_all, literal, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.attendees.models import Attendee, AttendeeStatus
from app.events.models import Event, event_organizers
from app.social.models import Review
from app.users.schemas import UserStatsResponse, UserActivityItem, UserActivityResponse


async def get_user_stats(session: AsyncSession, user_id) -> UserStatsResponse:
    """Get aggregated user stats"""

    organized_result = await session.execute(
        select(func.count())
        .select_from(event_organizers)
        .where(event_organizers.c.user_id == user_id)
    )
    events_organized = organized_result.scalar() or 0

    attended_result = await session.execute(
        select(func.count())
        .select_from(Attendee)
        .where(
            Attendee.user_id == user_id,
            Attendee.status.in_([AttendeeStatus.REGISTERED, AttendeeStatus.CHECKED_IN]),
        )
    )
    events_attended = attended_result.scalar() or 0

    reviews_given_result = await session.execute(
        select(func.count())
        .select_from(Review)
        .where(Review.user_id == user_id)
    )
    reviews_given = reviews_given_result.scalar() or 0

    reviews_received_result = await session.execute(
        select(func.count())
        .select_from(Review)
        .join(Event, Review.event_id == Event.id)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(event_organizers.c.user_id == user_id)
    )
    reviews_received = reviews_received_result.scalar() or 0

    from app.social.models import SavedEvent
    saved_result = await session.execute(
        select(func.count())
        .select_from(SavedEvent)
        .where(SavedEvent.user_id == user_id)
    )
    saved_events_count = saved_result.scalar() or 0

    return UserStatsResponse(
        events_organized=events_organized,
        events_attended=events_attended,
        reviews_given=reviews_given,
        reviews_received=reviews_received,
        saved_events_count=saved_events_count,
    )


async def get_user_activity(
    session: AsyncSession, user_id, limit: int = 20, offset: int = 0
) -> UserActivityResponse:
    """Get user activity timeline by querying registrations, event creations, and reviews"""

    items = []

    registrations_result = await session.execute(
        select(Attendee, Event)
        .join(Event, Attendee.event_id == Event.id)
        .where(
            Attendee.user_id == user_id,
            Attendee.status.in_([AttendeeStatus.REGISTERED, AttendeeStatus.CHECKED_IN]),
        )
        .order_by(Attendee.registered_at.desc())
        .limit(limit)
    )
    for attendee, event in registrations_result.all():
        items.append(UserActivityItem(
            type="registration",
            title="Registered for event",
            description=f"Registered for '{event.title}'",
            timestamp=attendee.registered_at,
            event_id=event.id,
            event_title=event.title,
        ))

    created_events_result = await session.execute(
        select(Event)
        .where(Event.created_by_id == user_id)
        .order_by(Event.created_at.desc())
        .limit(limit)
    )
    for event in created_events_result.scalars().all():
        items.append(UserActivityItem(
            type="event_created",
            title="Created an event",
            description=f"Created '{event.title}'",
            timestamp=event.created_at,
            event_id=event.id,
            event_title=event.title,
        ))

    reviews_result = await session.execute(
        select(Review, Event)
        .join(Event, Review.event_id == Event.id)
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(limit)
    )
    for review, event in reviews_result.all():
        items.append(UserActivityItem(
            type="review_posted",
            title="Posted a review",
            description=f"Reviewed '{event.title}' with {review.rating}★",
            timestamp=review.created_at,
            event_id=event.id,
            event_title=event.title,
        ))

    items.sort(key=lambda x: x.timestamp, reverse=True)
    total = len(items)

    paginated = items[offset:offset + limit]

    return UserActivityResponse(items=paginated, total=total)
