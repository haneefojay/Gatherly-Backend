"""Event selectors for querying and filtering"""

import uuid
from typing import List

from sqlalchemy import and_, func, or_, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.common.types import PaginationParamsType
from app.events.models import Event, EventCategory, EventMedia, EventStatus, EventTag, event_organizers, event_tags
from app.events.schemas import EventFilterParams
from app.users.models import User, UserRole

from app.tasks.models import Task
from app.attendees.models import Attendee, AttendeeStatus
from app.social.models import Review
from datetime import datetime


async def get_event_by_id(session: AsyncSession, event_id: uuid.UUID) -> Event | None:
    """Get event by ID with eager loading (excludes soft-deleted)"""
    result = await session.execute(
        select(Event)
        .where(Event.id == event_id, Event.is_deleted == False)
        .options(selectinload(Event.organizers), selectinload(Event.created_by))
    )
    return result.scalar_one_or_none()


async def get_event_by_slug(session: AsyncSession, slug: str) -> Event | None:
    """Get event by slug with eager loading and increment views"""
    result = await session.execute(
        select(Event)
        .where(Event.slug == slug, Event.is_deleted == False)
        .options(
            selectinload(Event.organizers),
            selectinload(Event.created_by),
            selectinload(Event.category),
        )
    )
    event = result.scalar_one_or_none()
    if event:
        await session.execute(
            sa_update(Event).where(Event.id == event.id).values(views_count=Event.views_count + 1)
        )
        await session.commit()
        await session.refresh(event)
    return event


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
    ).where(Event.is_deleted == False)

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

        if hasattr(filters, 'category_id') and filters.category_id:
            conditions.append(Event.category_id == filters.category_id)
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


async def get_categories_with_counts(session: AsyncSession) -> list[dict]:
    """Get all event categories with their event counts"""
    result = await session.execute(
        select(
            EventCategory.id,
            EventCategory.name,
            EventCategory.slug,
            EventCategory.description,
            EventCategory.icon,
            EventCategory.color,
            func.count(Event.id).filter(
                Event.is_deleted == False,
                Event.is_archived == False,
            ).label("event_count"),
        )
        .outerjoin(Event, Event.category_id == EventCategory.id)
        .group_by(EventCategory.id)
        .order_by(EventCategory.name)
    )
    rows = result.all()
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "slug": row.slug,
            "description": row.description,
            "icon": row.icon,
            "color": row.color,
            "event_count": row.event_count,
        }
        for row in rows
    ]


async def get_events_by_category(
    session: AsyncSession,
    category_slug: str,
    current_user: User | None = None,
    pagination: PaginationParamsType | None = None,
) -> tuple[list[Event], int, EventCategory | None]:
    """Get events belonging to a specific category by slug"""
    cat_result = await session.execute(
        select(EventCategory).where(EventCategory.slug == category_slug)
    )
    category = cat_result.scalar_one_or_none()
    if not category:
        return [], 0, None

    filters = EventFilterParams(category_id=category.id)
    events, total = await get_events(session, current_user, filters, pagination)
    return events, total, category


async def get_popular_tags(session: AsyncSession, limit: int = 30) -> list[dict]:
    """Get popular tags ordered by usage count"""
    result = await session.execute(
        select(
            EventTag.id,
            EventTag.name,
            EventTag.slug,
            func.count(event_tags.c.event_id).label("event_count"),
        )
        .outerjoin(event_tags, EventTag.id == event_tags.c.tag_id)
        .group_by(EventTag.id)
        .order_by(func.count(event_tags.c.event_id).desc())
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "slug": row.slug,
            "event_count": row.event_count,
        }
        for row in rows
    ]


async def get_event_analytics(session: AsyncSession, event: Event) -> dict:
    """Get analytics for a specific event (views, registrations, conversion rate)"""
    registrations_result = await session.execute(
        select(func.count(Attendee.id)).where(
            Attendee.event_id == event.id,
            Attendee.status == AttendeeStatus.REGISTERED,
        )
    )
    registrations = registrations_result.scalar() or 0

    reviews_result = await session.execute(
        select(
            func.count(Review.id).label("count"),
            func.coalesce(func.avg(Review.rating), 0).label("avg_rating"),
        ).where(Review.event_id == event.id)
    )
    review_stats = reviews_result.one()

    views = event.views_count or 0
    conversion_rate = (registrations / views * 100) if views > 0 else 0

    return {
        "views": views,
        "registrations": registrations,
        "conversion_rate": round(conversion_rate, 2),
        "review_count": review_stats.count,
        "average_rating": round(float(review_stats.avg_rating), 2),
    }
