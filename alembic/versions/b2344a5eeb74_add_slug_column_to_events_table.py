"""add slug column to events table

Revision ID: b2344a5eeb74
Revises: a3f1e9b72c04
Create Date: 2026-02-25 04:07:03.191624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2344a5eeb74'
down_revision: Union[str, None] = 'a3f1e9b72c04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('events', sa.Column('slug', sa.String(length=300), nullable=True))
    op.add_column('events', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('events', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('events', sa.Column('views_count', sa.Integer(), nullable=False, server_default=sa.text('0')))

    conn = op.get_bind()
    events = conn.execute(sa.text("SELECT id, title FROM events WHERE slug IS NULL"))
    import re, uuid as _uuid
    for row in events:
        base = re.sub(r"[^a-z0-9]+", "-", row.title.lower()).strip("-")
        slug = f"{base}-{_uuid.uuid4().hex[:8]}"
        conn.execute(
            sa.text("UPDATE events SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": row.id},
        )

    op.create_index('ix_events_active_listing', 'events', ['is_deleted', 'status', 'start_date'], unique=False)
    op.create_index(op.f('ix_events_is_deleted'), 'events', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_events_slug'), 'events', ['slug'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_events_slug'), table_name='events')
    op.drop_index(op.f('ix_events_is_deleted'), table_name='events')
    op.drop_index('ix_events_active_listing', table_name='events')
    op.drop_column('events', 'views_count')
    op.drop_column('events', 'deleted_at')
    op.drop_column('events', 'is_deleted')
    op.drop_column('events', 'slug')
