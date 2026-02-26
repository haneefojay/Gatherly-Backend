"""Event media routes"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session
from app.common.exceptions import NotFoundException, ValidationException
from app.common.permissions import CurrentUser, require_resource_ownership
from app.core.settings import get_settings
from app.core.storage import get_storage_provider
from app.events.models import Event, EventMedia, MediaType
from app.events.schemas import MediaResponse

router = APIRouter()

settings = get_settings()
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_IMAGE_SIZE_BYTES = settings.MAX_EVENT_MEDIA_SIZE_MB * 1024 * 1024


def _validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file type and size"""
    if not file.filename:
        raise ValidationException("No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationException(
            f"Invalid image type. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )

    if file.size and file.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationException(
            f"Image too large. Maximum size: {settings.MAX_EVENT_MEDIA_SIZE_MB}MB"
        )


async def _unset_existing_primary(session: AsyncSession, event_id: uuid.UUID) -> None:
    """Remove primary flag from all media for an event"""
    result = await session.execute(
        select(EventMedia).where(
            EventMedia.event_id == event_id,
            EventMedia.is_primary == True,
        )
    )
    for media in result.scalars().all():
        media.is_primary = False


async def _get_next_order(session: AsyncSession, event_id: uuid.UUID) -> int:
    """Get next display order for event media"""
    result = await session.execute(
        select(EventMedia.order)
        .where(EventMedia.event_id == event_id)
        .order_by(EventMedia.order.desc())
        .limit(1)
    )
    max_order = result.scalar() or 0
    return max_order + 1


def _to_response(media: EventMedia) -> MediaResponse:
    return MediaResponse(
        id=media.id,
        event_id=media.event_id,
        url=media.url,
        type=media.type.value,
        is_primary=media.is_primary,
        order=media.order,
    )


@router.post(
    "/{event_id}/media",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image to event",
    description="Upload a cover or gallery image. The file is stored via the configured storage provider.",
)
async def upload_event_image(
    event_id: uuid.UUID,
    current_user: CurrentUser,
    file: UploadFile = File(..., description="Image file (jpg, png, webp, gif)"),
    is_primary: bool = Form(False, description="Set as cover image"),
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Upload an image to an event via the storage provider"""
    _validate_image_file(file)

    storage = get_storage_provider()

    if is_primary:
        await _unset_existing_primary(session, event.id)

    folder = f"events/{event.id}/media"
    url = await storage.upload(
        file.file,
        file.filename,
        file.content_type or "image/jpeg",
        folder=folder,
    )

    next_order = await _get_next_order(session, event.id)

    media = EventMedia(
        event_id=event.id,
        url=url,
        type=MediaType.IMAGE,
        is_primary=is_primary,
        order=next_order,
    )
    session.add(media)
    await session.commit()
    await session.refresh(media)

    return _to_response(media)


@router.post(
    "/{event_id}/media/video",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add video embed to event",
    description="Add a video embed URL (YouTube, Vimeo, etc.) to the event.",
)
async def add_event_video(
    event_id: uuid.UUID,
    current_user: CurrentUser,
    url: str = Form(..., description="Video embed URL (YouTube, Vimeo)"),
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Add a video embed URL to an event"""
    if not url.startswith(("https://", "http://")):
        raise ValidationException("Video URL must start with https:// or http://")

    next_order = await _get_next_order(session, event.id)

    media = EventMedia(
        event_id=event.id,
        url=url,
        type=MediaType.VIDEO,
        is_primary=False,
        order=next_order,
    )
    session.add(media)
    await session.commit()
    await session.refresh(media)

    return _to_response(media)


@router.delete(
    "/{event_id}/media/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete event media",
    description="Delete a media item. Images are also removed from storage.",
)
async def delete_event_media(
    event_id: uuid.UUID,
    media_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Delete a media item and clean up stored file"""
    result = await session.execute(
        select(EventMedia).where(
            EventMedia.id == media_id,
            EventMedia.event_id == event.id,
        )
    )
    media = result.scalar_one_or_none()
    if not media:
        raise NotFoundException("Media not found")

    if media.type == MediaType.IMAGE:
        storage = get_storage_provider()
        try:
            await storage.delete(media.url)
        except Exception:
            pass

    await session.delete(media)
    await session.commit()
    return None


@router.patch(
    "/{event_id}/media/{media_id}",
    response_model=MediaResponse,
    summary="Update event media",
    description="Set media as primary cover image or update its display order",
)
async def update_event_media(
    event_id: uuid.UUID,
    media_id: uuid.UUID,
    current_user: CurrentUser,
    is_primary: bool | None = Form(None),
    order: int | None = Form(None),
    session: AsyncSession = Depends(get_session),
    event: Event = Depends(require_resource_ownership(Event, "event_id")),
):
    """Update a media item (set primary, reorder)"""
    result = await session.execute(
        select(EventMedia).where(
            EventMedia.id == media_id,
            EventMedia.event_id == event.id,
        )
    )
    media = result.scalar_one_or_none()
    if not media:
        raise NotFoundException("Media not found")

    if is_primary is not None and is_primary:
        await _unset_existing_primary(session, event.id)
        media.is_primary = True

    if order is not None:
        media.order = order

    await session.commit()
    await session.refresh(media)

    return _to_response(media)
