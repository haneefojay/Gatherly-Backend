"""User preferences service — get and update user preferences"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import UserPreferences
from app.users.schemas import UserPreferencesResponse, UserPreferencesUpdate


async def get_user_preferences(
    session: AsyncSession, user_id
) -> UserPreferencesResponse:
    """Get user preferences, creating defaults if none exist"""

    result = await session.execute(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        session.add(prefs)
        await session.commit()
        await session.refresh(prefs)

    return UserPreferencesResponse.model_validate(prefs)


async def update_user_preferences(
    session: AsyncSession, user_id, data: UserPreferencesUpdate
) -> UserPreferencesResponse:
    """Update user preferences (partial update)"""

    result = await session.execute(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(user_id=user_id)
        session.add(prefs)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)

    await session.commit()
    await session.refresh(prefs)

    return UserPreferencesResponse.model_validate(prefs)
