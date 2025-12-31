from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import ConfigDict

from app.events.models import EventStatus
from app.events.schemas.base import EventBase


class EventResponse(EventBase):
    """Event response schema"""

    id: UUID
    status: EventStatus
    current_attendees: int
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    is_full: bool
    available_spots: int
    organizer_ids: List[UUID] = []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Tech Conference 2026",
                "description": "Annual technology conference",
                "start_date": "2026-06-01T09:00:00",
                "end_date": "2026-06-01T17:00:00",
                "location": "Convention Center",
                "capacity": 500,
                "status": "upcoming",
                "current_attendees": 150,
                "created_by_id": "123e4567-e89b-12d3-a456-426614174001",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
                "is_full": False,
                "available_spots": 350,
                "organizer_ids": [],
            }
        },
    )
