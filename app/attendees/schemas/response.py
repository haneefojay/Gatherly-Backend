from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.attendees.models import AttendeeStatus


class AttendeeResponse(BaseModel):
    """Attendee response schema"""

    id: UUID
    event_id: UUID
    user_id: UUID
    status: AttendeeStatus
    registered_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegistrationResponse(BaseModel):
    """Registration response with additional info"""

    attendee: AttendeeResponse
    message: str
    waitlist_position: int | None = None
