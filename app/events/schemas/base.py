"""Event schemas for request/response validation"""

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

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


class EventCreate(EventBase):
    """Event creation schema"""

    status: EventStatus = EventStatus.DRAFT

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Tech Conference 2024",
                "description": "Annual technology conference",
                "start_date": "2024-06-01T09:00:00",
                "end_date": "2024-06-01T17:00:00",
                "location": "Convention Center",
                "capacity": 500,
                "status": "draft",
            }
        }


class EventUpdate(BaseModel):
    """Event update schema"""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    location: str | None = Field(None, max_length=255)
    capacity: int | None = Field(None, gt=0)
    status: EventStatus | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Tech Conference 2024",
                "status": "upcoming",
            }
        }


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

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "title": "Tech Conference 2024",
                "description": "Annual technology conference",
                "start_date": "2024-06-01T09:00:00",
                "end_date": "2024-06-01T17:00:00",
                "location": "Convention Center",
                "capacity": 500,
                "status": "upcoming",
                "current_attendees": 150,
                "created_by_id": "123e4567-e89b-12d3-a456-426614174001",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "is_full": False,
                "available_spots": 350,
                "organizer_ids": [],
            }
        }


class EventFilterParams(BaseModel):
    """Event filtering parameters"""

    status: EventStatus | None = None
    location: str | None = None
    start_date_from: datetime | None = None
    start_date_to: datetime | None = None
    organizer_id: UUID | None = None
    has_capacity: bool | None = None  # Filter events with available spots

    class Config:
        json_schema_extra = {
            "example": {
                "status": "upcoming",
                "location": "Convention Center",
                "start_date_from": "2024-01-01T00:00:00",
                "start_date_to": "2024-12-31T23:59:59",
                "has_capacity": True,
            }
        }


class AddOrganizerRequest(BaseModel):
    """Request to add organizer to event"""

    user_id: UUID

    class Config:
        json_schema_extra = {
            "example": {"user_id": "123e4567-e89b-12d3-a456-426614174002"}
        }
