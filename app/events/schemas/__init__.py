"""Event schemas package"""

from app.events.schemas.base import (
    AddOrganizerRequest,
    EventBase,
    EventFilterParams,
)
from app.events.schemas.create import EventCreate
from app.events.schemas.edit import EventUpdate
from app.events.schemas.response import EventResponse, EventStatsResponse

__all__ = [
    "EventBase",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "EventStatsResponse",
    "EventFilterParams",
    "AddOrganizerRequest",
]
