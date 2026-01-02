from contextlib import asynccontextmanager

import logfire
import redis.asyncio as redis
import jwt
from anyio import to_thread
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi_limiter import FastAPILimiter
from secure import Secure
from sqlalchemy import select
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
from app.core.logging import setup_logging
from app.core.rate_limit import role_based_rate_limiter
from app.core.settings import get_settings
from app.core.tags import RouteTags
from app.users.apis import router as users_router
from app.events.apis import router as events_router
from app.tasks.apis import router as tasks_router
from app.attendees.apis import router as attendees_router

setup_logging()

tags = RouteTags()
settings = get_settings()
secure_headers = Secure.with_default_headers()

async def rate_limit_identifier(request):
    """Identify the user for rate limiting (prefer user_id from JWT)"""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            sub = payload.get("sub")
            if sub:
                return sub
        except Exception:
            pass

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


@asynccontextmanager
async def lifespan(_: FastAPI):
    """This is the startup and shutdown code for the FastAPI application."""

    print("Starting Server...")

    limiter = to_thread.current_default_thread_limiter()
    limiter.total_tokens = 1000

    try:
        redis_connection = redis.from_url(
            settings.REDIS_BROKER_URL, encoding="utf-8", decode_responses=True
        )
        await FastAPILimiter.init(redis_connection, identifier=rate_limit_identifier)
        
        from app.core.redis import init_redis_cache
        await init_redis_cache()
        
        print("Rate limiter and Cache initialized")
    except Exception as e:
        print(f"Failed to initialize redis services: {e}")

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

if settings.LOGFIRE_TOKEN and not settings.TESTING:
    logfire.configure(
        token=settings.LOGFIRE_TOKEN, environment="dev" if settings.DEBUG else "prod"
    )
    logfire.instrument_fastapi(app)
    logfire.instrument_asyncpg()


from app.common.dependencies import get_session, get_redis_client

@app.get("/health", include_in_schema=False)
async def health(
    session: AsyncSession = Depends(get_session),
    redis_client = Depends(get_redis_client)
):
    """App Healthcheck with dependency verification"""
    # Check Database
    await session.execute(select(1))
    
    # Check Redis
    await redis_client.ping()
    
    return {
        "status": "healthy",
        "services": {
            "database": "online",
            "redis": "online"
        }
    }


rate_limit_deps = []
if not settings.TESTING:
    rate_limit_deps = [
        Depends(role_based_rate_limiter)
    ]


app.include_router(
    users_router,
    dependencies=rate_limit_deps,
)

app.include_router(
    events_router,
    prefix="/events",
    tags=["Events"],
    dependencies=rate_limit_deps,
)

app.include_router(
    tasks_router,
    tags=["Tasks"],
    dependencies=rate_limit_deps,
)

app.include_router(
    attendees_router,
    tags=["Attendees"],
    dependencies=rate_limit_deps,
)
