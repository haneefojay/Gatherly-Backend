"""add_refresh_token_id_and_tracking_fields_to_user_sessions

Revision ID: 06ef887eef56
Revises: 05d4c49a2e41
Create Date: 2026-02-10 23:31:03.382588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06ef887eef56'
down_revision: Union[str, None] = '05d4c49a2e41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
