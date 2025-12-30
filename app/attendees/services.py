"""Attendee business logic and services"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendees.models import Attendee, AttendeeStatus
from app.common.exceptions import BadRequest
from app.events.models import Event, EventStatus
from app.users.models import User


async def register_for_event(
    session: AsyncSession, event: Event, user: User
) -> tuple[Attendee, str, int | None]:
    """Register user for an event

    Args:
        session: Database session
        event: Event to register for
        user: User registering

    Returns:
        Tuple of (attendee, message, waitlist_position)

    Raises:
        BadRequest: If registration is not allowed
    """
    # Check if event allows registration
    if event.status not in [EventStatus.DRAFT, EventStatus.UPCOMING]:
        raise BadRequest(
            f"Cannot register for events with status '{event.status.value}'"
        )

    # Check if already registered
    result = await session.execute(
        select(Attendee).where(
            Attendee.event_id == event.id,
            Attendee.user_id == user.id,
            Attendee.status != AttendeeStatus.CANCELLED,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise BadRequest("Already registered for this event")

    # Determine status based on capacity
    if event.current_attendees < event.capacity:
        status = AttendeeStatus.REGISTERED
        message = "Successfully registered for event"
        waitlist_position = None

        # Increment attendee count
        event.current_attendees += 1
    else:
        status = AttendeeStatus.WAITLISTED
        # Get waitlist position
        result = await session.execute(
            select(func.count()).select_from(
                select(Attendee).where(
                    Attendee.event_id == event.id,
                    Attendee.status == AttendeeStatus.WAITLISTED,
                )
            )
        )
        waitlist_position = (result.scalar() or 0) + 1
        message = f"Event is full. Added to waitlist at position {waitlist_position}"

    # Create attendee record
    attendee = Attendee(
        event_id=event.id,
        user_id=user.id,
        status=status,
    )

    session.add(attendee)
    await session.commit()
    await session.refresh(attendee)
    await session.refresh(event)

    return attendee, message, waitlist_position


async def unregister_from_event(
    session: AsyncSession, event: Event, user: User
) -> None:
    """Unregister user from an event

    Args:
        session: Database session
        event: Event to unregister from
        user: User unregistering

    Raises:
        BadRequest: If not registered
    """
    # Get attendee record
    result = await session.execute(
        select(Attendee).where(
            Attendee.event_id == event.id,
            Attendee.user_id == user.id,
            Attendee.status != AttendeeStatus.CANCELLED,
        )
    )
    attendee = result.scalar_one_or_none()

    if not attendee:
        raise BadRequest("Not registered for this event")

    was_registered = attendee.status == AttendeeStatus.REGISTERED

    # Mark as cancelled
    attendee.status = AttendeeStatus.CANCELLED
    await session.flush()

    # If was registered, decrement count and promote from waitlist
    if was_registered:
        event.current_attendees -= 1

        # Promote first person from waitlist
        result = await session.execute(
            select(Attendee)
            .where(
                Attendee.event_id == event.id,
                Attendee.status == AttendeeStatus.WAITLISTED,
            )
            .order_by(Attendee.registered_at.asc())
            .limit(1)
        )
        next_in_line = result.scalar_one_or_none()

        if next_in_line:
            next_in_line.status = AttendeeStatus.REGISTERED
            event.current_attendees += 1

    await session.commit()
