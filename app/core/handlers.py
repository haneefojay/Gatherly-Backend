from datetime import datetime, timezone

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from sqlalchemy.exc import IntegrityError

from app.common.exceptions import BehemothException
from app.common.schemas import ErrorResponse
from app.core.settings import get_settings

settings = get_settings()


async def behemoth_exception_handler(_: Request, exc: BehemothException):
    """
    Handler for all application specific exceptions
    """
    return ORJSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            ErrorResponse(
                error=exc.error_code,
                message=exc.message,
                details=exc.details,
                timestamp=exc.timestamp,
            ).model_dump()
        ),
    )


async def integrity_error_exception_handler(_: Request, exc: IntegrityError):
    """
    Handler for database integrity errors
    """
    error_info = str(exc.orig) if exc.orig else str(exc)

    if "uq_event_title_date_loc" in error_info:
        msg = "An event with this title, start date, and location already exists."
        code = "EventConflict"
    elif "unique constraint" in error_info.lower() or "duplicate key" in error_info.lower():
        msg = "A record with these unique details already exists."
        code = "DuplicateRecord"
    else:
        msg = "Database integrity error."
        code = "IntegrityError"

    return ORJSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=jsonable_encoder(
            ErrorResponse(
                error=code,
                message=msg,
                details={"original_error": str(exc)},
                timestamp=datetime.now(timezone.utc),
            ).model_dump()
        ),
    )


async def request_validation_exception_handler(_: Request, exc: RequestValidationError):
    """
    Handler for Pydantic validation errors
    """
    return ORJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            ErrorResponse(
                error="ValidationError",
                message="Input validation failed",
                details={"errors": exc.errors()},
                timestamp=datetime.now(timezone.utc),
            ).model_dump()
        ),
    )


async def base_exception_handler(_: Request, exc: Exception):
    """
    Fallback handler for unhandled exceptions
    """
    print(f"Unhandled Exception: {exc}")
    import traceback
    traceback.print_exc()

    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(
            ErrorResponse(
                error="InternalServerError",
                message="An unexpected error occurred",
                details=None,
                timestamp=datetime.now(timezone.utc),
            ).model_dump()
        ),
    )
