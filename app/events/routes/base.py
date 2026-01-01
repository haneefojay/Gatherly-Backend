"""Event API routes"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.cache import CacheManager
from app.common.dependencies import get_session, pagination_params
from app.common.exceptions import EventNotFoundException
from app.common.permissions import (
    CurrentUser,
    OrganizerOrAdminUser,
    require_resource_ownership,
)
from app.common.schemas import ErrorResponse, PaginatedResponse
from app.common.types import PaginationParamsType
from app.events.models import Event, EventStatus
from app.events.schemas import (
    AddOrganizerRequest,
    EventCreate,
    EventFilterParams,
    EventResponse,
    EventUpdate,
)
from app.events.selectors import get_event_by_id, get_events, get_user_events
from app.events.services import (
    add_organizer,
    create_event,
    delete_event,
    remove_organizer,
    update_event,
)

router = APIRouter()


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
    description="Create a new event. Creator is automatically added as first organizer.",
)
async def create_event_endpoint(
    event_data: EventCreate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Create a new event"""
    event = await create_event(session, event_data, current_user)

    response = EventResponse.model_validate(event)
    response.organizer_ids = [org.id for org in event.organizers]

    return response


@router.get(
    "",
    response_model=PaginatedResponse[EventResponse],
    summary="List and search events",
    description="Get a paginated list of events with optional filtering and search",
)
async def list_events(
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParamsType = Depends(pagination_params),
    status_filter: EventStatus | None = Query(None, alias="status"),
    location: str | None = Query(None),
    start_date_from: str | None = Query(None),
    start_date_to: str | None = Query(None),
    organizer_id: uuid.UUID | None = Query(None),
    has_capacity: bool | None = Query(None),
    search: str | None = Query(None, description="Search in title and description"),
):
    """List events with filtering and search"""
    filters = EventFilterParams(
        status=status_filter,
        location=location,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        organizer_id=organizer_id,
        has_capacity=has_capacity,
    )

    cache_data = {
        "page": pagination.page,
        "size": pagination.size,
        "order_by": pagination.order_by,
        "filters": filters.model_dump() if hasattr(filters, "model_dump") else filters.__dict__,
        "search": search
    }
    cache = CacheManager(ttl=60, cache_prefix="events:list:", data=cache_data)
    cached_response = await cache.get()
    if cached_response:
        return cached_response

    events, total = await get_events(session, filters, pagination, search)

    items = []
    for event in events:
        response = EventResponse.model_validate(event)
        response.organizer_ids = [org.id for org in event.organizers]
        items.append(response.model_dump())

    response_data = {
        "items": items,
        "total": total,
        "page": pagination.page,
        "size": pagination.size,
        "pages": (total + pagination.size - 1) // pagination.size,
    }
    
    await cache.set(response_data)

    return response_data


@router.get(
    "/my-events",
    response_model=PaginatedResponse[EventResponse],
    summary="Get current user's events",
    description="Get events created by or organized by the current user",
)
async def get_my_events(
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    pagination: PaginationParamsType = Depends(pagination_params),
):
    """Get current user's events"""
    events, total = await get_user_events(session, current_user.id, pagination)

    items = []
    for event in events:
        response = EventResponse.model_validate(event)
        response.organizer_ids = [org.id for org in event.organizers]
        items.append(response)

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=(total + pagination.size - 1) // pagination.size,
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get event details",
    description="Get detailed information about a specific event",
    responses={404: {"model": ErrorResponse, "description": "Event not found"}},
)
async def get_event(
    event_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get event by ID"""
    event = await get_event_by_id(session, event_id)

    if not event:
        raise EventNotFoundException(event_id)

    response = EventResponse.model_validate(event)
    response.organizer_ids = [org.id for org in event.organizers]

    return response


@router.put(
    "/{event_id}",
    response_model=EventResponse,
    summary="Update event",
    description="Update event details. Requires organizer or admin permissions.",
    responses={
        404: {"model": ErrorResponse, "description": "Event not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        409: {"model": ErrorResponse, "description": "Invalid status transition"},
    },
)
async def update_event_endpoint(
    event_id: uuid.UUID,
    event_data: EventUpdate,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Update an event"""
    event = await get_event_by_id(session, event_id)

    if not event:
        raise EventNotFoundException(event_id)

    event = await update_event(session, event, event_data, current_user)

    response = EventResponse.model_validate(event)
    response.organizer_ids = [org.id for org in event.organizers]

    return response


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete event",
    description="Delete an event. Only creator or admin can delete.",
    responses={
        404: {"model": ErrorResponse, "description": "Event not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
    },
)
async def delete_event_endpoint(
    event_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Delete an event"""
    await delete_event(session, event, current_user)
    return None


@router.post(
    "/{event_id}/organizers",
    response_model=EventResponse,
    summary="Add organizer to event",
    description="Add a user as an organizer to the event. Only creator or admin can add.",
    responses={
        404: {"model": ErrorResponse, "description": "Event or User not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        422: {"model": ErrorResponse, "description": "User already organizer"},
    },
)
async def add_organizer_endpoint(
    event_id: uuid.UUID,
    organizer_data: AddOrganizerRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Add organizer to event"""
    event = await add_organizer(session, event, organizer_data, current_user)

    response = EventResponse.model_validate(event)
    response.organizer_ids = [org.id for org in event.organizers]

    return response


@router.delete(
    "/{event_id}/organizers/{organizer_id}",
    response_model=EventResponse,
    summary="Remove organizer from event",
    description="Remove a user from event organizers. Only creator or admin can remove.",
    responses={
        404: {"model": ErrorResponse, "description": "Event not found"},
        403: {"model": ErrorResponse, "description": "Permission denied"},
        422: {"model": ErrorResponse, "description": "Cannot remove last organizer"},
    },
)
async def remove_organizer_endpoint(
    event_id: uuid.UUID,
    organizer_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Remove organizer from event"""
    event = await remove_organizer(session, event, organizer_id, current_user)

    response = EventResponse.model_validate(event)
    response.organizer_ids = [org.id for org in event.organizers]

    return response
