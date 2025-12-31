from datetime import datetime
from typing import Any


class BehemothException(Exception):
    """Base class for all application exceptions"""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        self.timestamp = datetime.utcnow()

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


# --- Core Exceptions ---


class UnauthorizedException(BehemothException):
    """User is not authenticated or token is invalid"""

    def __init__(self, message: str = "Unauthorized", details: dict | None = None):
        super().__init__(message, "Unauthorized", 401, details)


class ForbiddenException(BehemothException):
    """User is authenticated but does not have permission"""

    def __init__(self, message: str = "Access Denied", details: dict | None = None):
        super().__init__(message, "Forbidden", 403, details)


class NotFoundException(BehemothException):
    """Resource not found"""

    def __init__(self, message: str = "Resource not found", details: dict | None = None):
        super().__init__(message, "ResourceNotFound", 404, details)


class ValidationException(BehemothException):
    """Input validation failed"""

    def __init__(self, message: str = "Validation Failed", details: dict | None = None):
        super().__init__(message, "ValidationError", 422, details)


class InternalServerError(BehemothException):
    """Unexpected server error"""

    def __init__(self, message: str = "Internal Server Error", details: dict | None = None):
        super().__init__(message, "InternalServerError", 500, details)


# --- Event Domain Exceptions ---


class EventNotFoundException(NotFoundException):
    """Specific event not found error"""

    def __init__(self, event_id: Any, details: dict | None = None):
        super().__init__("Event not found", details)
        self.error_code = "EventNotFound"


class CapacityExceededException(BehemothException):
    """Event is full"""

    def __init__(self, message: str = "Event capacity exceeded", details: dict | None = None):
        super().__init__(message, "CapacityExceeded", 409, details)


class EventStatusException(BehemothException):
    """Invalid event status transition or operation"""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, "InvalidEventStatus", 409, details)


# --- Backward Compatibility aliases (for existing code) ---
# Mapping old exception names to new ones to avoid breaking imports immediately

class CustomHTTPException(BehemothException):
    """Adapter for old CustomHTTPException usage"""
    def __init__(self, msg: str, status_code: int, loc: list | None = None):
        super().__init__(msg, "Error", status_code, details={"loc": loc} if loc else None)
        self.msg = msg
        self.loc = loc

class BadRequest(BehemothException):
    def __init__(self, msg: str, *, loc: list | None = None):
        super().__init__(msg, "BadRequest", 400, details={"loc": loc} if loc else None)

class Unauthorized(UnauthorizedException):
    def __init__(self, msg: str, *, loc: list | None = None):
        super().__init__(msg, details={"loc": loc} if loc else None)

class Forbidden(ForbiddenException):
    def __init__(self, msg: str = "Forbidden", *, loc: list | None = None):
        super().__init__(msg, details={"loc": loc} if loc else None)

class NotFound(NotFoundException):
    def __init__(self, msg: str, *, loc: list | None = None):
        super().__init__(msg, details={"loc": loc} if loc else None)

class BadGatewayError(BehemothException):
    def __init__(self, msg: str, **kwargs):
         super().__init__(msg, "BadGateway", 502, details=kwargs)
