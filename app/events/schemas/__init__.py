"""Event schemas package"""

from app.events.schemas.base import (
    AddOrganizerRequest,
    EventBase,
    EventFilterParams,
)
from app.events.schemas.create import EventCreate
from app.events.schemas.edit import EventUpdate
from app.events.schemas.response import (
    AddTagsRequest,
    CategoryResponse,
    EventAnalyticsResponse,
    EventResponse,
    EventStatsResponse,
    MediaResponse,
    TagResponse,
)

__all__ = [
    "EventBase",
    "EventCreate",
    "EventUpdate",
    "EventResponse",
    "EventStatsResponse",
    "EventAnalyticsResponse",
    "EventFilterParams",
    "AddOrganizerRequest",
    "AddTagsRequest",
    "CategoryResponse",
    "TagResponse",
    "MediaResponse",
]
