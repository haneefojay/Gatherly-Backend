from uuid import UUID
from pydantic import ConfigDict

from app.tasks.schemas.base import TaskBase


class TaskCreate(TaskBase):
    """Task creation schema"""

    assignee_id: UUID | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Setup registration desk",
                "description": "Prepare registration materials and setup desk",
                "assignee_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }
    )
