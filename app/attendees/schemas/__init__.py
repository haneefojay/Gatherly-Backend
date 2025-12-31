"""Attendee schemas package"""

from app.attendees.schemas.base import AttendeeBase
from app.attendees.schemas.create import AttendeeCreate
from app.attendees.schemas.edit import AttendeeUpdate
from app.attendees.schemas.response import AttendeeResponse, RegistrationResponse

__all__ = [
    "AttendeeBase",
    "AttendeeCreate",
    "AttendeeUpdate",
    "AttendeeResponse",
    "RegistrationResponse",
]
