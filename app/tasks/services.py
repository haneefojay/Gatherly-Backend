"""Task business logic and services"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import (
    EventStatusException,
    ForbiddenException,
    ValidationException,
)
from app.events.models import Event, EventStatus
from app.events.services import check_event_permission
from app.tasks.models import Task
from app.tasks.schemas import TaskCreate, TaskUpdate
from app.users.models import User


async def create_task(
    session: AsyncSession, event: Event, task_data: TaskCreate, current_user: User
) -> Task:
    """Create a task for an event

    Args:
        session: Database session
        event: Event to create task for
        task_data: Task creation data
        current_user: User creating the task

    Returns:
        Created task instance

    Raises:
        ForbiddenException: If user doesn't have permission
        EventStatusException: If event status doesn't allow task creation
    """
    # Check permissions (organizer/admin)
    await check_event_permission(session, event, current_user)

    # Check event status
    if event.status in [EventStatus.COMPLETED, EventStatus.CANCELLED]:
        raise EventStatusException(
            f"Cannot create tasks for events with status '{event.status.value}'"
        )

    # Check for duplicate task title in this event
    result = await session.execute(
        select(Task).where(Task.event_id == event.id, Task.title == task_data.title)
    )
    if result.scalars().first():
        raise ValidationException(f"Task with title '{task_data.title}' already exists for this event")

    # Create task
    task = Task(
        event_id=event.id,
        title=task_data.title,
        description=task_data.description,
        assignee_id=task_data.assignee_id,
    )

    session.add(task)
    await session.commit()
    await session.refresh(task)

    return task


async def update_task(
    session: AsyncSession, task: Task, task_data: TaskUpdate, current_user: User
) -> Task:
    """Update a task

    Args:
        session: Database session
        task: Task to update
        task_data: Update data
        current_user: User performing the update

    Returns:
        Updated task instance

    Raises:
        ForbiddenException: If user doesn't have permission
        EventStatusException: If event status doesn't allow modification
    """
    # Get event
    result = await session.execute(select(Event).where(Event.id == task.event_id))
    event = result.scalar_one()

    # Check permissions
    is_manager = True
    try:
        await check_event_permission(session, event, current_user)
    except ForbiddenException:
        is_manager = False

    if not is_manager:
        # If not organizer/admin, must be the assignee
        if task.assignee_id != current_user.id:
            raise ForbiddenException("You don't have permission to modify this task")

        # Assignees can ONLY update the 'completed' status
        if (
            task_data.title is not None
            or task_data.description is not None
            or task_data.assignee_id is not None
        ):
            raise ForbiddenException(
                "Assignees can only update the completion status of their assigned tasks"
            )

    # Check event status
    if event.status in [EventStatus.COMPLETED, EventStatus.CANCELLED]:
        raise EventStatusException(
            f"Cannot modify tasks for events with status '{event.status.value}'"
        )

    # Update fields
    if task_data.title is not None and task_data.title != task.title:
        # Check for duplicate title in this event
        result = await session.execute(
            select(Task).where(Task.event_id == event.id, Task.title == task_data.title)
        )
        if result.scalars().first():
            raise ValidationException(
                f"Task with title '{task_data.title}' already exists for this event"
            )
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.completed is not None:
        task.completed = task_data.completed
    if task_data.assignee_id is not None:
        task.assignee_id = task_data.assignee_id

    await session.commit()
    await session.refresh(task)

    return task


async def delete_task(session: AsyncSession, task: Task, current_user: User) -> None:
    """Delete a task

    Args:
        session: Database session
        task: Task to delete
        current_user: User performing the deletion

    Raises:
        ForbiddenException: If user doesn't have permission
    """
    # Get event
    result = await session.execute(select(Event).where(Event.id == task.event_id))
    event = result.scalar_one()

    # Check permissions
    await check_event_permission(session, event, current_user)

    await session.delete(task)
    await session.commit()
