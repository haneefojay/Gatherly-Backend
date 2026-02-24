"""add_suspended_until_to_users

Revision ID: a3f1e9b72c04
Revises: d9032f962617
Create Date: 2026-02-24 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3f1e9b72c04'
down_revision: Union[str, None] = 'd9032f962617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('suspended_until', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'suspended_until')
