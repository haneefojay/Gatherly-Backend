from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.attendees.models import Attendee, AttendeeStatus
from app.common.dependencies import get_session
from app.common.permissions import CurrentUser
from app.events.models import Event, EventStatus
from app.events.schemas.response import EventResponse
from app.tasks.models import Task
from app.users.models import User, UserRole

router = APIRouter()


@router.get("", summary="Get user dashboard stats")
async def get_dashboard_stats(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """
    Get statistics and upcoming events for the dashboard.
    Returns personalized stats for both attendees and organizers.
    """
    now = datetime.utcnow()

    # 1. Upcoming Registered Events (for everyone)
    # Events where user is REGISTERED and end_date > now
    upcoming_registered_query = (
        select(Event)
        .join(Attendee, Attendee.event_id == Event.id)
        .where(
            Attendee.user_id == current_user.id,
            Attendee.status == AttendeeStatus.REGISTERED,
            Event.status == EventStatus.UPCOMING
        )
        .options(selectinload(Event.organizers)) # efficient loading
        .order_by(Event.start_date.asc())
        .limit(5)
    )
    result = await session.execute(upcoming_registered_query)
    upcoming_events = result.scalars().all()

    # Count of all registered upcoming events
    registered_count_query = (
        select(func.count())
        .select_from(Attendee)
        .join(Event, Attendee.event_id == Event.id)
        .where(
            Attendee.user_id == current_user.id,
            Attendee.status == AttendeeStatus.REGISTERED,
            Event.status == EventStatus.UPCOMING
        )
    )
    result = await session.execute(registered_count_query)
    registered_events_count = result.scalar() or 0

    # 2. Organizer Stats (Events I organize)
    organized_events_count = 0
    total_attendees_count = 0
    pending_tasks_count = 0
    
    # Check if user organizes any events (by checking event.organizers via association or direct query on event table?)
    # Event has `organizers` relationship (M2M). 
    # Also manual check: Event.created_by_id == user.id OR user in organizers.
    # We query events where user is in organizer_ids (but that's a property/list). 
    # We use the association table `event_organizers`.
    # Let's import the association table? It's usually in models.
    # `app.events.models.event_organizers`
    
    from app.events.models import event_organizers
    
    organized_events_query = (
        select(Event)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(event_organizers.c.user_id == current_user.id)
    )
    # We just want count for now
    organized_count_exec = await session.execute(
        select(func.count())
        .select_from(Event)
        .join(event_organizers, event_organizers.c.event_id == Event.id)
        .where(event_organizers.c.user_id == current_user.id)
    )
    organized_events_count = organized_count_exec.scalar() or 0

    if organized_events_count > 0:
        # Sum of attendees for my organized events
        attendees_sum_exec = await session.execute(
            select(func.sum(Event.current_attendees))
            .join(event_organizers, event_organizers.c.event_id == Event.id)
            .where(event_organizers.c.user_id == current_user.id)
        )
        total_attendees_count = attendees_sum_exec.scalar() or 0

        # Pending tasks assigned to me
        tasks_count_exec = await session.execute(
            select(func.count())
            .select_from(Task)
            .where(
                Task.assignee_id == current_user.id,
                Task.completed == False
            )
        )
        pending_tasks_count = tasks_count_exec.scalar() or 0

    
    # 3. Admin Stats (Global View)
    admin_stats = {}
    if current_user.role == UserRole.ADMIN:
        # Global Users
        users_count_exec = await session.execute(select(func.count()).select_from(User))
        admin_stats["total_users"] = users_count_exec.scalar() or 0
        
        # Event Stats by Status
        event_stats_result = await session.execute(
            select(Event.status, func.count(Event.id))
            .group_by(Event.status)
        )
        event_counts = {row.status: row[1] for row in event_stats_result.all()}
        
        admin_stats["admin_events_upcoming"] = event_counts.get(EventStatus.UPCOMING, 0)
        admin_stats["admin_events_ongoing"] = event_counts.get(EventStatus.ONGOING, 0)
        admin_stats["admin_events_completed"] = event_counts.get(EventStatus.COMPLETED, 0)
        admin_stats["admin_events_cancelled"] = event_counts.get(EventStatus.CANCELLED, 0)
        admin_stats["admin_events_draft"] = event_counts.get(EventStatus.DRAFT, 0)
        
        # Task Stats by Completion
        task_stats_result = await session.execute(
            select(Task.completed, func.count(Task.id))
            .group_by(Task.completed)
        )
        task_counts = {row.completed: row[1] for row in task_stats_result.all()}
        
        admin_stats["admin_tasks_pending"] = task_counts.get(False, 0)
        admin_stats["admin_tasks_completed"] = task_counts.get(True, 0)
        
        # Override list with global upcoming events
        global_list_query = (
            select(Event)
            .where(Event.status == EventStatus.UPCOMING)
            .options(selectinload(Event.organizers))
            .order_by(Event.start_date.asc())
            .limit(10)
        )
        result = await session.execute(global_list_query)
        upcoming_events = result.scalars().all()

    return {
        "stats": {
            "upcoming_events_count": registered_events_count,
            "registered_events": registered_events_count,
            "organized_events": organized_events_count,
            "total_attendees": total_attendees_count,
            "pending_tasks": pending_tasks_count,
            **admin_stats,
        },
        "upcoming_events": [EventResponse.model_validate(e) for e in upcoming_events]
    }
