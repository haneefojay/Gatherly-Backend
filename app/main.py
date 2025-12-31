from contextlib import asynccontextmanager

import logfire
import redis.asyncio as redis
from anyio import to_thread
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from secure import Secure
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.exceptions import BehemothException
from app.core.handlers import (
    base_exception_handler,
    behemoth_exception_handler,
    integrity_error_exception_handler,
    request_validation_exception_handler,
)
from app.core.settings import get_settings
from app.core.tags import RouteTags
from app.users.apis import router as users_router
from app.events.apis import router as events_router
from app.tasks.apis import router as tasks_router
from app.attendees.apis import router as attendees_router


tags = RouteTags()
settings = get_settings()
secure_headers = Secure.with_default_headers()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """This is the startup and shutdown code for the FastAPI application."""

    print("Starting Server...")

    limiter = to_thread.current_default_thread_limiter()
    limiter.total_tokens = 1000

    print("Setting up rate limiter")
    redis_connection = redis.from_url(
        settings.REDIS_BROKER_URL, encoding="utf-8", decode_responses=True
    )
    await FastAPILimiter.init(redis_connection)

    yield
    print("Shutting Down Server...")


app = FastAPI(
    title="Event Management API",
    description="Production-ready Event Management API with JWT authentication, RBAC, and advanced features",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    contact={
        "name": "GrandGale Technologies",
        "url": "https://github.com/GrandGaleTechnologies",
        "email": "contact@grandgale.tech",
    },
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    GZipMiddleware,
    minimum_size=5000,
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """
    Middleware for adding security headers.
    Skip for documentation routes to prevent CSP issues.
    """
    response = await call_next(request)

    if request.url.path not in ["/docs", "/redoc", "/openapi.json"]:
        await secure_headers.set_headers_async(response)

    return response

app.add_exception_handler(Exception, base_exception_handler)
app.add_exception_handler(BehemothException, behemoth_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_exception_handler)

if settings.LOGFIRE_TOKEN:
    logfire.configure(
        token=settings.LOGFIRE_TOKEN, environment="dev" if settings.DEBUG else "prod"
    )
    logfire.instrument_fastapi(app)
    logfire.instrument_asyncpg()


@app.get("/health", include_in_schema=False)
async def health(_: AsyncSession = Depends(get_session)):
    """App Healthcheck"""
    return {"status": "Ok!"}


app.include_router(
    users_router,
    dependencies=[
        Depends(RateLimiter(times=settings.REQ_RATE, seconds=settings.REQ_RATE_TIME))
    ],
)

app.include_router(
    events_router,
    prefix="/events",
    tags=["Events"],
    dependencies=[
        Depends(RateLimiter(times=settings.REQ_RATE, seconds=settings.REQ_RATE_TIME))
    ],
)

app.include_router(
    tasks_router,
    tags=["Tasks"],
    dependencies=[
        Depends(RateLimiter(times=settings.REQ_RATE, seconds=settings.REQ_RATE_TIME))
    ],
)

app.include_router(
    attendees_router,
    tags=["Attendees"],
    dependencies=[
        Depends(RateLimiter(times=settings.REQ_RATE, seconds=settings.REQ_RATE_TIME))
    ],
)
