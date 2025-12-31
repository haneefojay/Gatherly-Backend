from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskUpdate(BaseModel):
    """Task update schema"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    completed: bool | None = None
    assignee_id: UUID | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Updated task title",
                "completed": True,
            }
        }
    )
