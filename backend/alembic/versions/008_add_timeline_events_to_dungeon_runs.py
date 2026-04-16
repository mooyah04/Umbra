"""add timeline_events to dungeon_runs

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-04-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # JSON column storing a small array of event objects — typical
    # payload is 1-2 KB per run (≤15 events), nullable because all
    # existing runs predate Level B and can't be backfilled cheaply.
    op.add_column(
        'dungeon_runs',
        sa.Column('timeline_events', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('dungeon_runs', 'timeline_events')
