"""Admin bulk operations service"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User, UserStatus
from app.admin.services import log_admin_action
from app.admin.services.admin_users import (
    suspend_user,
    verify_user,
    export_user_data,
)


async def execute_bulk_action(
    session: AsyncSession,
    admin: User,
    action: str,
    user_ids: list[uuid.UUID],
    reason: Optional[str] = None,
) -> dict:
    """Execute bulk action on multiple users"""

    success_count = 0
    failed_count = 0
    errors = []
    results = []

    for uid in user_ids:
        try:
            if action == "suspend":
                if not reason:
                    raise ValueError("Reason is required for suspend")
                await suspend_user(session, admin, uid, reason)
                success_count += 1

            elif action == "verify":
                await verify_user(session, admin, uid)
                success_count += 1

            elif action == "export":
                data = await export_user_data(session, uid)
                results.append(data)
                success_count += 1

            elif action == "email":
                success_count += 1

        except Exception as e:
            failed_count += 1
            errors.append(f"User {uid}: {str(e)}")

    await log_admin_action(
        session,
        admin_id=admin.id,
        action=f"bulk_{action}",
        resource_type="users",
        changes={
            "user_ids": [str(uid) for uid in user_ids],
            "success_count": success_count,
            "failed_count": failed_count,
        },
    )

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors,
    }
