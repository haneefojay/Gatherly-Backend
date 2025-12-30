from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse

from app.common.exceptions import (
    BadGatewayError,
    CustomHTTPException,
    InternalServerError,
)
from app.core.settings import get_settings

settings = get_settings()

from sqlalchemy.exc import IntegrityError


async def integrity_error_exception_handler(_: Request, exc: IntegrityError):
    """
    Exception handler for database integrity errors (unique constraints, foreign keys)
    """
    error_info = str(exc.orig) if exc.orig else str(exc)

    if "uq_event_title_date_loc" in error_info:
        msg = "An event with this title, start date, and location already exists."
    elif "unique constraint" in error_info.lower() or "duplicate key" in error_info.lower():
        msg = "A record with these unique details already exists."
    else:
        msg = "Database integrity error."

    return ORJSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=jsonable_encoder(
            {
                "status": "error",
                "error": {"msg": msg, "loc": []},
                "data": None,
            }
        ),
    )


async def base_exception_handler(_: Request, exc: Exception):
    """
    Exception handler for general Exception
    """
    # OPTIONAL: send email to staff
    print(exc)
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(
            {
                "status": "error",
                "error": {"msg": "Internal Server Error", "loc": []},
                "data": None,
            }
        ),
    )


async def request_validation_exception_handler(_: Request, exc: RequestValidationError):
    """
    Exception handler for 'RequestValidationError' raised by pydantic
    """

    # Get error message
    error = exc.errors()[0]

    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {
                "status": "error",
                "error": {"msg": error["msg"], "loc": error["loc"]},
                "data": None,
            }
        ),
    )


async def internal_server_error_exception_handler(_: Request, exc: InternalServerError):
    """
    Exception handler for 'InternalServerError' exception
    """
    # OPTIONAL: send email to staff
    print(exc)
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(
            {
                "status": "error",
                "error": {"msg": "Internal Server Error", "loc": []},
                "data": None,
            }
        ),
    )


async def bad_gateway_error_exception_handler(_: Request, exc: BadGatewayError):
    """
    Exception handler for 'BadGatewayError' exception
    """
    # OPTIONAL: send email to staff
    print(exc)
    return ORJSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content=jsonable_encoder(
            {
                "status": "error",
                "error": {"msg": "Bad Gateway Please Contact Support", "loc": exc.loc},
                "data": None,
            }
        ),
    )


async def custom_http_exception_handler(_: Request, exc: CustomHTTPException):
    """
    Exception handler for 'NotFound' exception
    """
    return ORJSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "status": "error",
                "error": {"msg": exc.msg, "loc": exc.loc},
                "data": None,
            }
        ),
    )
