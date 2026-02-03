"""Event selectors for querying and filtering"""

import uuid
from typing import List

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.types import PaginationParamsType
from app.events.models import Event, EventStatus, event_organizers
from app.events.schemas import EventFilterParams
from app.users.models import User, UserRole

from app.tasks.models import Task
from app.attendees.models import Attendee, AttendeeStatus
from datetime import datetime


async def get_event_by_id(session: AsyncSession, event_id: uuid.UUID) -> Event | None:
    """Get event by ID with eager loading

    Args:
        session: Database session
        event_id: Event ID

    Returns:
        Event instance or None
    """
    result = await session.execute(
        select(Event)
        .where(Event.id == event_id)
        .options(selectinload(Event.organizers), selectinload(Event.created_by))
    )
    return result.scalar_one_or_none()


async def get_events(
    session: AsyncSession,
    current_user: User | None = None,
    filters: EventFilterParams | None = None,
    pagination: PaginationParamsType | None = None,
    search_query: str | None = None,
) -> tuple[List[Event], int]:
    """Get events with filtering, search, and pagination

    Args:
        session: Database session
        current_user: Current user context for visibility rules
        filters: Filter parameters
        pagination: Pagination parameters
        search_query: Full-text search query

    Returns:
        Tuple of (events list, total count)
    """

    query = select(Event).options(
        selectinload(Event.organizers), selectinload(Event.created_by)
    )

    # Visibility Rules
    is_admin = current_user and current_user.role == UserRole.ADMIN

    if not is_admin:
        # Statuses visible to general public
        public_statuses = [EventStatus.UPCOMING, EventStatus.ONGOING]

        if current_user:
            # Users can see public events + events they created or organize
            query = query.outerjoin(
                event_organizers, Event.id == event_organizers.c.event_id
            )
            
            visibility_condition = or_(
                Event.status.in_(public_statuses),
                Event.created_by_id == current_user.id,
                event_organizers.c.user_id == current_user.id
            )
            query = query.where(visibility_condition).distinct()
        else:
            # Anonymous users only see public events
            query = query.where(Event.status.in_(public_statuses))


    conditions = []

    if filters:
        if filters.status:
            conditions.append(Event.status == filters.status)

        if filters.location:
            conditions.append(Event.location.ilike(f"%{filters.location}%"))

        if filters.start_date_from:
            conditions.append(Event.start_date >= filters.start_date_from)

        if filters.start_date_to:
            conditions.append(Event.start_date <= filters.start_date_to)

        if filters.has_capacity is not None:
            if filters.has_capacity:
                conditions.append(Event.current_attendees < Event.capacity)
            else:
                conditions.append(Event.current_attendees >= Event.capacity)

        if filters.organizer_id:
            query = query.join(
                event_organizers, Event.id == event_organizers.c.event_id
            ).where(event_organizers.c.user_id == filters.organizer_id)

        if filters.is_archived is not None:
            conditions.append(Event.is_archived == filters.is_archived)
        else:
            conditions.append(Event.is_archived == False)
    else:
        conditions.append(Event.is_archived == False)

    if search_query:
        search_pattern = f"%{search_query.strip()}%"
        conditions.append(
            or_(
                Event.title.ilike(search_pattern),
                Event.description.ilike(search_pattern),
                Event.location.ilike(search_pattern),
            )
        )

    if conditions:
        query = query.where(and_(*conditions))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    sort_mapping = {
        "date": Event.start_date,
        "popularity": Event.current_attendees,
        "title": Event.title,
        "created_at": Event.created_at,
    }
    sort_attr = sort_mapping.get(pagination.sort_by, Event.start_date) if pagination else Event.start_date

    if pagination and pagination.order_by == "asc":
        query = query.order_by(sort_attr.asc())
    else:
        query = query.order_by(sort_attr.desc())

    if pagination:
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
    result = await session.execute(query)
    events = list(result.scalars().all())

    return events, total


async def get_user_events(
    session: AsyncSession,
    user_id: uuid.UUID,
    pagination: PaginationParamsType | None = None,
    is_archived: bool = False,
    search_query: str | None = None,
) -> tuple[List[Event], int]:
    """Get events created by or organized by a user

    Args:
        session: Database session
        user_id: User ID
        pagination: Pagination parameters
        is_archived: Whether to fetch archived events
        search_query: Search query for title, description, and location

    Returns:
        Tuple of (events list, total count)
    """
    conditions = [
        or_(
            Event.created_by_id == user_id,
            event_organizers.c.user_id == user_id,
        )
    ]

    if is_archived:
        conditions.append(Event.is_archived == True)
    else:
        conditions.append(Event.is_archived == False)

    if search_query:
        search_pattern = f"%{search_query.strip()}%"
        conditions.append(
            or_(
                Event.title.ilike(search_pattern),
                Event.description.ilike(search_pattern),
                Event.location.ilike(search_pattern),
            )
        )

    query = (
        select(Event)
        .outerjoin(event_organizers, Event.id == event_organizers.c.event_id)
        .where(and_(*conditions))
        .options(selectinload(Event.organizers), selectinload(Event.created_by))
        .distinct()
    )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    sort_mapping = {
        "date": Event.start_date,
        "popularity": Event.current_attendees,
        "title": Event.title,
        "created_at": Event.created_at,
    }
    sort_attr = sort_mapping.get(pagination.sort_by, Event.start_date) if pagination else Event.start_date

    if pagination and pagination.order_by == "asc":
        query = query.order_by(sort_attr.asc())
    else:
        query = query.order_by(sort_attr.desc())

    if pagination:
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)

    result = await session.execute(query)
    events = list(result.scalars().all())

    return events, total


async def get_event_stats(session: AsyncSession, event: Event) -> dict:
    """Calculate statistics for a specific event"""
    
    # Task stats
    tasks_result = await session.execute(
        select(
            func.count(Task.id).label("total"),
            func.count(Task.id).filter(Task.completed == True).label("completed")
        ).where(Task.event_id == event.id)
    )
    task_stats = tasks_result.one()
    total_tasks = task_stats.total
    completed_tasks = task_stats.completed
    pending_tasks = total_tasks - completed_tasks
    task_completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Attendee stats
    attendees_result = await session.execute(
        select(
            func.count(Attendee.id).filter(Attendee.status == AttendeeStatus.REGISTERED).label("registered"),
            func.count(Attendee.id).filter(Attendee.status == AttendeeStatus.WAITLISTED).label("waitlisted"),
            func.count(Attendee.id).filter(Attendee.status == AttendeeStatus.CANCELLED).label("cancelled")
        ).where(Attendee.event_id == event.id)
    )
    attendee_stats = attendees_result.one()
    
    # Organizer stats - query directly to avoid lazy loading issues
    organizers_result = await session.execute(
        select(func.count()).select_from(event_organizers).where(event_organizers.c.event_id == event.id)
    )
    total_organizers = organizers_result.scalar() or 0
    
    capacity_usage_percentage = (attendee_stats.registered / event.capacity * 100) if event.capacity > 0 else 0
    
    days_until_event = None
    if event.start_date:
        now = datetime.utcnow()
        if event.start_date > now:
            days_until_event = (event.start_date - now).days

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "task_completion_percentage": round(task_completion_percentage, 2),
        "total_organizers": total_organizers,
        "total_attendees": attendee_stats.registered,
        "waitlisted_attendees": attendee_stats.waitlisted,
        "cancelled_attendees": attendee_stats.cancelled,
        "capacity": event.capacity,
        "capacity_usage_percentage": round(capacity_usage_percentage, 2),
        "days_until_event": days_until_event
    }
