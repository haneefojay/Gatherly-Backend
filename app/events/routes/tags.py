"""Event tag routes"""

import re
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import insert, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.exceptions import NotFoundException, ValidationException
from app.common.permissions import CurrentUser, require_resource_ownership
from app.events.models import Event, EventTag, event_tags
from app.events.schemas import AddTagsRequest, EventResponse, TagResponse
from app.events.selectors import get_popular_tags

router = APIRouter()


@router.get(
    "",
    response_model=list[TagResponse],
    summary="Get popular tags",
    description="List popular tags ordered by usage count",
)
async def list_tags(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(30, ge=1, le=100),
):
    """Get popular tags"""
    tags = await get_popular_tags(session, limit=limit)
    return tags


@router.post(
    "/{event_id}/tags",
    response_model=EventResponse,
    summary="Add tags to event",
    description="Add one or more tags to an event. Creates tags if they don't exist.",
)
async def add_tags_to_event(
    event_id: uuid.UUID,
    tag_data: AddTagsRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Add tags to an event"""
    for tag_name in tag_data.tags:
        tag_name = tag_name.strip()
        if not tag_name:
            continue

        slug = re.sub(r"[^a-z0-9]+", "-", tag_name.lower()).strip("-")

        result = await session.execute(
            select(EventTag).where(EventTag.slug == slug)
        )
        tag = result.scalar_one_or_none()

        if not tag:
            tag = EventTag(name=tag_name, slug=slug)
            session.add(tag)
            await session.flush()

        existing = await session.execute(
            select(event_tags).where(
                event_tags.c.event_id == event.id,
                event_tags.c.tag_id == tag.id,
            )
        )
        if not existing.first():
            await session.execute(
                insert(event_tags).values(event_id=event.id, tag_id=tag.id)
            )

    await session.commit()
    await session.refresh(event, ["organizers", "tags"])

    response = EventResponse.model_validate(event)
    response.organizer_ids = [org.id for org in event.organizers]
    return response


@router.delete(
    "/{event_id}/tags/{tag_id}",
    response_model=EventResponse,
    summary="Remove tag from event",
    description="Remove a tag from an event",
)
async def remove_tag_from_event(
    event_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Remove a tag from an event"""
    result = await session.execute(
        select(event_tags).where(
            event_tags.c.event_id == event.id,
            event_tags.c.tag_id == tag_id,
        )
    )
    if not result.first():
        raise NotFoundException("Tag not found on this event")

    await session.execute(
        delete(event_tags).where(
            event_tags.c.event_id == event.id,
            event_tags.c.tag_id == tag_id,
        )
    )
    await session.commit()
    await session.refresh(event, ["organizers", "tags"])

    response = EventResponse.model_validate(event)
    response.organizer_ids = [org.id for org in event.organizers]
    return response
