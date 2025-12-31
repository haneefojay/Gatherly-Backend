"""Event business logic and services"""

import uuid
from datetime import datetime

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.exceptions import (
    EventStatusException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.events.models import Event, EventStatus, event_organizers
from app.events.schemas import AddOrganizerRequest, EventCreate, EventUpdate
from app.users.models import User, UserRole

# Valid status transitions
STATUS_TRANSITIONS = {
    EventStatus.DRAFT: [EventStatus.UPCOMING, EventStatus.CANCELLED],
    EventStatus.UPCOMING: [EventStatus.ONGOING, EventStatus.CANCELLED],
    EventStatus.ONGOING: [EventStatus.COMPLETED, EventStatus.CANCELLED],
    EventStatus.COMPLETED: [],
    EventStatus.CANCELLED: [],
}


async def create_event(
    session: AsyncSession, event_data: EventCreate, creator: User
) -> Event:
    """Create a new event

    Args:
        session: Database session
        event_data: Event creation data
        creator: User creating the event

    Returns:
        Created event instance
    """
    # Create event
    event = Event(
        title=event_data.title,
        description=event_data.description,
        start_date=event_data.start_date,
        end_date=event_data.end_date,
        location=event_data.location,
        capacity=event_data.capacity,
        status=event_data.status,
        created_by_id=creator.id,
    )

    session.add(event)
    await session.flush()

    # Add creator as first organizer
    await session.execute(
        insert(event_organizers).values(event_id=event.id, user_id=creator.id)
    )

    await session.commit()
    await session.refresh(event, ["organizers"])

    return event


async def update_event(
    session: AsyncSession,
    event: Event,
    event_data: EventUpdate,
    current_user: User,
) -> Event:
    """Update an event

    Args:
        session: Database session
        event: Event to update
        event_data: Update data
        current_user: User performing the update

    Returns:
        Updated event instance

    Raises:
        ForbiddenException: If user doesn't have permission
        EventStatusException: If status transition invalid
        ValidationException: If update violates business rules
    """
    # Check permissions
    await check_event_permission(session, event, current_user)

    # Validate status transition if status is being changed
    if event_data.status and event_data.status != event.status:
        validate_status_transition(event.status, event_data.status)

    # Check if event can be modified
    if event.status in [EventStatus.COMPLETED, EventStatus.CANCELLED]:
        raise EventStatusException(
            f"Cannot modify event with status '{event.status.value}'"
        )

    # Update fields
    if event_data.title is not None:
        event.title = event_data.title
    if event_data.description is not None:
        event.description = event_data.description
    if event_data.start_date is not None:
        event.start_date = event_data.start_date
    if event_data.end_date is not None:
        event.end_date = event_data.end_date
    if event_data.location is not None:
        event.location = event_data.location
    if event_data.capacity is not None:
        # Validate capacity isn't reduced below current attendees
        if event_data.capacity < event.current_attendees:
            raise ValidationException(
                f"Cannot reduce capacity below current attendees ({event.current_attendees})"
            )
        event.capacity = event_data.capacity
    if event_data.status is not None:
        event.status = event_data.status

    event.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(event)

    return event


async def delete_event(session: AsyncSession, event: Event, current_user: User) -> None:
    """Delete an event

    Args:
        session: Database session
        event: Event to delete
        current_user: User performing the deletion

    Raises:
        ForbiddenException: If user doesn't have permission
    """
    await session.delete(event)
    await session.commit()


async def add_organizer(
    session: AsyncSession,
    event: Event,
    organizer_data: AddOrganizerRequest,
    current_user: User,
) -> Event:
    """Add an organizer to an event

    Args:
        session: Database session
        event: Event to add organizer to
        organizer_data: Organizer data
        current_user: User performing the action

    Returns:
        Updated event instance

    Raises:
        ForbiddenException: If user doesn't have permission
        NotFoundException: Is user not found
        ValidationException: If user is already an organizer
    """
    # Check permissions
    await check_event_permission(session, event, current_user)

    # Check if user exists
    result = await session.execute(
        select(User).where(User.id == organizer_data.user_id)
    )
    new_organizer = result.scalar_one_or_none()

    if not new_organizer:
        raise NotFoundException("User not found")

    # Validate target role
    if new_organizer.role not in [UserRole.ORGANIZER, UserRole.ADMIN]:
        raise ValidationException(
            "Only users with ORGANIZER or ADMIN roles can be added as event organizers"
        )

    # Only Admin can add an Admin
    if new_organizer.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise ForbiddenException(
            "Only an admin can add another admin as an event organizer"
        )

    # Check if already an organizer
    result = await session.execute(
        select(event_organizers).where(
            event_organizers.c.event_id == event.id,
            event_organizers.c.user_id == organizer_data.user_id,
        )
    )
    if result.first():
        raise ValidationException("User is already an organizer")

    # Add organizer
    await session.execute(
        insert(event_organizers).values(
            event_id=event.id, user_id=organizer_data.user_id
        )
    )

    await session.commit()
    await session.refresh(event, ["organizers"])

    return event


async def remove_organizer(
    session: AsyncSession,
    event: Event,
    organizer_id: uuid.UUID,
    current_user: User,
) -> Event:
    """Remove an organizer from an event

    Args:
        session: Database session
        event: Event to remove organizer from
        organizer_id: ID of organizer to remove
        current_user: User performing the action

    Returns:
        Updated event instance

    Raises:
        ForbiddenException: If user doesn't have permission
        ValidationException: If trying to remove last organizer
    """
    # Count current organizers
    result = await session.execute(
        select(event_organizers).where(event_organizers.c.event_id == event.id)
    )
    organizer_count = len(result.all())

    if organizer_count <= 1:
        raise ValidationException("Cannot remove the last organizer")

    # Remove organizer
    await session.execute(
        delete(event_organizers).where(
            event_organizers.c.event_id == event.id,
            event_organizers.c.user_id == organizer_id,
        )
    )

    await session.commit()
    await session.refresh(event, ["organizers"])

    return event


async def check_event_permission(
    session: AsyncSession, event: Event, user: User
) -> None:
    """Check if user has permission to modify event

    Args:
        session: Database session
        event: Event to check
        user: User to check permission for

    Raises:
        ForbiddenException: If user doesn't have permission
    """
    # Admin can do anything
    if user.role == UserRole.ADMIN:
        return

    # Creator can modify their events
    if event.created_by_id == user.id:
        return

    # Check if user is an organizer
    result = await session.execute(
        select(event_organizers).where(
            event_organizers.c.event_id == event.id,
            event_organizers.c.user_id == user.id,
        )
    )
    if result.first():
        return

    raise ForbiddenException("You don't have permission to modify this event")


def validate_status_transition(
    current_status: EventStatus, new_status: EventStatus
) -> None:
    """Validate event status transition

    Args:
        current_status: Current event status
        new_status: New event status

    Raises:
        EventStatusException: If transition is invalid
    """
    allowed_transitions = STATUS_TRANSITIONS.get(current_status, [])

    if new_status not in allowed_transitions:
        raise EventStatusException(
            f"Invalid status transition from '{current_status.value}' to '{new_status.value}'"
        )
