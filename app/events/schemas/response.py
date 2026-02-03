from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.events.models import EventStatus
from app.events.schemas.base import EventBase


from app.users.schemas.response import UserResponse


class EventResponse(EventBase):
    """Event response schema"""

    id: UUID
    status: EventStatus
    current_attendees: int
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    is_full: bool
    is_archived: bool
    available_spots: int
    organizer_ids: List[UUID] = []
    organizers: List[UserResponse] = []

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
                "is_archived": False,
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
    
class EventStatsResponse(BaseModel):
    """Event statistics response schema"""

    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    task_completion_percentage: float
    total_organizers: int
    total_attendees: int
    waitlisted_attendees: int
    cancelled_attendees: int
    capacity: int
    capacity_usage_percentage: float
    days_until_event: int | None

    model_config = ConfigDict(from_attributes=True)
