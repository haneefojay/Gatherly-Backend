"""Task schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Base task schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class TaskCreate(TaskBase):
    """Task creation schema"""

    assignee_id: UUID | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Setup registration desk",
                "description": "Prepare registration materials and setup desk",
                "assignee_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }


class TaskUpdate(BaseModel):
    """Task update schema"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    completed: bool | None = None
    assignee_id: UUID | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated task title",
                "completed": True,
            }
        }


class TaskResponse(TaskBase):
    """Task response schema"""

    id: UUID
    event_id: UUID
    completed: bool
    assignee_id: UUID | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
