"""Attendee API routes"""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.attendees.models import Attendee, AttendeeStatus
from app.attendees.schemas import AttendeeResponse, RegistrationResponse
from app.attendees.services import register_for_event, unregister_from_event
from app.common.dependencies import get_session
from app.common.exceptions import EventNotFoundException
from app.common.permissions import CurrentUser, OrganizerOrAdminUser
from app.events.selectors import get_event_by_id

router = APIRouter()


@router.post(
    "/events/{event_id}/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register for event",
    description="Register the current user for an event. May be added to waitlist if full.",
)
async def register_for_event_endpoint(
    event_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Register for an event"""
    event = await get_event_by_id(session, event_id)

    if not event:
        raise EventNotFoundException(event_id)

    attendee, message, waitlist_position = await register_for_event(
        session, event, current_user
    )

    return RegistrationResponse(
        attendee=AttendeeResponse.model_validate(attendee),
        message=message,
        waitlist_position=waitlist_position,
    )


@router.delete(
    "/events/{event_id}/register",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister from event",
    description="Unregister the current user from an event",
)
async def unregister_from_event_endpoint(
    event_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
):
    """Unregister from an event"""
    event = await get_event_by_id(session, event_id)

    if not event:
        raise EventNotFoundException(event_id)

    await unregister_from_event(session, event, current_user)
    return None


@router.get(
    "/events/{event_id}/attendees",
    response_model=list[AttendeeResponse],
    summary="List event attendees",
    description="Get all registered attendees for an event. Organizer/Admin only.",
)
async def list_event_attendees(
    event_id: uuid.UUID,
    current_user: OrganizerOrAdminUser,
    session: AsyncSession = Depends(get_session),
):
    """List event attendees"""
    result = await session.execute(
        select(Attendee)
        .where(
            Attendee.event_id == event_id,
            Attendee.status == AttendeeStatus.REGISTERED,
        )
        .order_by(Attendee.registered_at.asc())
    )
    attendees = result.scalars().all()
    return attendees


@router.get(
    "/events/{event_id}/waitlist",
    response_model=list[AttendeeResponse],
    summary="List event waitlist",
    description="Get all waitlisted users for an event. Organizer/Admin only.",
)
async def list_event_waitlist(
    event_id: uuid.UUID,
    current_user: OrganizerOrAdminUser,
    session: AsyncSession = Depends(get_session),
):
    """List event waitlist"""
    result = await session.execute(
        select(Attendee)
        .where(
            Attendee.event_id == event_id,
            Attendee.status == AttendeeStatus.WAITLISTED,
        )
        .order_by(Attendee.registered_at.asc())
    )
    attendees = result.scalars().all()
    return attendees
