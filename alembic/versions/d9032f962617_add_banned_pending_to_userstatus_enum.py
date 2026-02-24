"""add_banned_pending_to_userstatus_enum

Revision ID: d9032f962617
Revises: 90d5deb884d9
Create Date: 2026-02-24 01:14:51.274848

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9032f962617'
down_revision: Union[str, None] = '90d5deb884d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alembic cannot auto-detect Python enum value additions.
    # We must add the missing values to the PostgreSQL enum type manually.
    op.execute("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'BANNED'")
    op.execute("ALTER TYPE userstatus ADD VALUE IF NOT EXISTS 'PENDING'")
    # Also add ORGANIZER to userrole if it's missing
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'ORGANIZER'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly via ALTER TYPE.
    # A full recreation of the type is required, which is destructive.
    # This is intentionally left as a no-op to prevent data loss.
    pass
