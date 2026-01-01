from datetime import datetime

from pydantic import ConfigDict, field_validator

from app.events.models import EventStatus
from app.events.schemas.base import EventBase


class EventCreate(EventBase):
    """Event creation schema"""

    status: EventStatus = EventStatus.DRAFT

    @field_validator("start_date")
    @classmethod
    def validate_start_date(cls, v: datetime):
        """Validate that start_date is not in the past"""
        now = datetime.now(v.tzinfo)
        if v < now:
            raise ValueError("start_date cannot be in the past")
        return v

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Tech Conference 2026",
                "description": "Annual technology conference",
                "start_date": "2026-06-01T09:00:00",
                "end_date": "2026-06-01T17:00:00",
                "location": "Convention Center",
                "capacity": 500,
                "status": "draft",
            }
        },
    )
