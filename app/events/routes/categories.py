"""Event category routes"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies import get_session, pagination_params
from app.common.permissions import OptionalCurrentUser
from app.common.schemas import PaginatedResponse
from app.common.types import PaginationParamsType
from app.events.schemas import CategoryResponse, EventResponse
from app.events.selectors import get_categories_with_counts, get_events_by_category

router = APIRouter()


@router.get(
    "",
    response_model=list[CategoryResponse],
    summary="List all event categories",
    description="Get all event categories with their event counts",
)
async def list_categories(
    session: AsyncSession = Depends(get_session),
):
    """List all event categories with counts"""
    categories = await get_categories_with_counts(session)
    return categories


@router.get(
    "/{category_slug}",
    response_model=PaginatedResponse[EventResponse],
    summary="Get events in a category",
    description="List all events belonging to a specific category by its slug",
)
async def get_category_events(
    category_slug: str,
    session: AsyncSession = Depends(get_session),
    current_user: OptionalCurrentUser = None,
    pagination: PaginationParamsType = Depends(pagination_params),
):
    """Get events in a specific category"""
    events, total, category = await get_events_by_category(
        session, category_slug, current_user, pagination
    )

    if category is None:
        from app.common.exceptions import NotFoundException
        raise NotFoundException(f"Category '{category_slug}' not found")

    items = []
    for event in events:
        response = EventResponse.model_validate(event)
        response.organizer_ids = [org.id for org in event.organizers]
        items.append(response)

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=(total + pagination.size - 1) // pagination.size,
    )
