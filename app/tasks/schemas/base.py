"""Task base schemas"""

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Base task schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
