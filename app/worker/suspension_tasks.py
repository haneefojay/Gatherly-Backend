"""
Celery tasks for user suspension management.
Auto-lifts timed suspensions that have expired.
"""
import logging
from datetime import datetime

from celery import shared_task
from sqlalchemy import select, update
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@shared_task(name="app.worker.suspension_tasks.lift_expired_suspensions", bind=True, max_retries=3)
def lift_expired_suspensions(self):
    """
    Periodic task: find all SUSPENDED users whose suspended_until has passed
    and restore them to ACTIVE status.
    Runs every 5 minutes via Celery Beat.
    """
    from app.core.database import SyncSessionLocal
    from app.users.models import User, UserStatus

    try:
        with SyncSessionLocal() as session:
            now = datetime.utcnow()

            result = session.execute(
                select(User).where(
                    User.status == UserStatus.SUSPENDED,
                    User.suspended_until.isnot(None),
                    User.suspended_until <= now,
                )
            )
            expired_users = result.scalars().all()

            if not expired_users:
                logger.info("lift_expired_suspensions: no expired suspensions found")
                return {"lifted": 0}

            count = 0
            for user in expired_users:
                user.status = UserStatus.ACTIVE
                user.is_active = True
                user.suspended_until = None
                count += 1
                logger.info(f"Lifted suspension for user {user.id} ({user.email})")

            session.commit()
            logger.info(f"lift_expired_suspensions: lifted {count} suspension(s)")
            return {"lifted": count}

    except Exception as exc:
        logger.error(f"lift_expired_suspensions failed: {exc}")
        raise self.retry(exc=exc, countdown=60)
