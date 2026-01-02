from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.events.models import EventStatus


class EventUpdate(BaseModel):
    """Event update schema"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    location: str | None = Field(None, max_length=255)
    capacity: int | None = Field(None, gt=0)
    status: EventStatus | None = None
    is_archived: bool | None = None

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: datetime | None):
        """Validate that start_date is not in the past"""
        if v is None:
            return v
        now = datetime.now(v.tzinfo)
        if v < now:
            raise ValueError("start_date cannot be in the past")
        return v

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Updated Tech Conference 2026",
                "status": "upcoming",
            }
        },
    )
