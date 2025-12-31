from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict

from app.tasks.schemas.base import TaskBase


class TaskResponse(TaskBase):
    """Task response schema"""

    id: UUID
    event_id: UUID
    completed: bool
    assignee_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
