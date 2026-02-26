from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.events.models import EventStatus
from app.events.schemas.base import EventBase


from app.users.schemas.response import UserResponse


class CategoryResponse(BaseModel):
    """Category response schema"""

    id: UUID
    name: str
    slug: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TagResponse(BaseModel):
    """Tag response schema"""

    id: UUID
    name: str
    slug: str
    event_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MediaResponse(BaseModel):
    """Event media response schema"""

    id: UUID
    event_id: UUID
    url: str
    type: str
    is_primary: bool
    order: int

    model_config = ConfigDict(from_attributes=True)


class AddTagsRequest(BaseModel):
    """Request to add tags to an event"""

    tags: list[str] = Field(
        ..., min_length=1, max_length=10, description="List of tag names to add"
    )


class EventResponse(EventBase):
    """Event response schema"""

    id: UUID
    slug: str | None = None
    status: EventStatus
    current_attendees: int
    views_count: int = 0
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    is_full: bool
    is_archived: bool
    available_spots: int
    organizer_ids: List[UUID] = []
    organizers: List[UserResponse] = []
    category: CategoryResponse | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Tech Conference 2026",
                "slug": "tech-conference-2026-a1b2c3d4",
                "description": "Annual technology conference",
                "start_date": "2026-06-01T09:00:00",
                "end_date": "2026-06-01T17:00:00",
                "location": "Convention Center",
                "capacity": 500,
                "status": "upcoming",
                "is_archived": False,
                "current_attendees": 150,
                "views_count": 1024,
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


class EventAnalyticsResponse(BaseModel):
    """Event analytics response schema"""

    views: int
    registrations: int
    conversion_rate: float
    review_count: int
    average_rating: float

    model_config = ConfigDict(from_attributes=True)

