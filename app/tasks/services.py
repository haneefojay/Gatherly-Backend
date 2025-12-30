"""Task business logic and services"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import BadRequest, Forbidden
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
        Forbidden: If user doesn't have permission
        BadRequest: If event status doesn't allow task creation
    """
    # Check permissions
    await check_event_permission(session, event, current_user)

    # Check event status
    if event.status in [EventStatus.COMPLETED, EventStatus.CANCELLED]:
        raise BadRequest(
            f"Cannot create tasks for events with status '{event.status.value}'"
        )

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
        Forbidden: If user doesn't have permission
        BadRequest: If event status doesn't allow modification
    """
    # Get event
    result = await session.execute(select(Event).where(Event.id == task.event_id))
    event = result.scalar_one()

    # Check permissions (organizer or assignee can update)
    try:
        await check_event_permission(session, event, current_user)
    except Forbidden:
        # If not organizer, check if user is assignee
        if task.assignee_id != current_user.id:
            raise Forbidden("You don't have permission to modify this task")

    # Check event status
    if event.status in [EventStatus.COMPLETED, EventStatus.CANCELLED]:
        raise BadRequest(
            f"Cannot modify tasks for events with status '{event.status.value}'"
        )

    # Update fields
    if task_data.title is not None:
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
        Forbidden: If user doesn't have permission
    """
    # Get event
    result = await session.execute(select(Event).where(Event.id == task.event_id))
    event = result.scalar_one()

    # Check permissions
    await check_event_permission(session, event, current_user)

    await session.delete(task)
    await session.commit()
