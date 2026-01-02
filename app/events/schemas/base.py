"""Event base schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.events.models import EventStatus


class EventBase(BaseModel):
    """Base event schema"""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime
    end_date: datetime
    location: str | None = Field(None, max_length=255)
    capacity: int = Field(default=100, gt=0)

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, end_date, info):
        """Validate that end_date is after start_date"""
        if "start_date" in info.data and end_date <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return end_date


class EventFilterParams(BaseModel):
    """Event filtering parameters"""

    status: EventStatus | None = None
    location: str | None = None
    start_date_from: datetime | None = None
    start_date_to: datetime | None = None
    organizer_id: UUID | None = None
    has_capacity: bool | None = None
    is_archived: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "upcoming",
                "location": "Convention Center",
                "start_date_from": "2026-01-01T00:00:00",
                "start_date_to": "2026-12-31T23:59:59",
                "has_capacity": True,
            }
        }
    )


class AddOrganizerRequest(BaseModel):
    """Request to add organizer to event"""

    user_id: UUID

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {"user_id": "123e4567-e89b-12d3-a456-426614174002"}
        },
    )
