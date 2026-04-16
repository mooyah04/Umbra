"""replace timeline_events with pulls

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-04-16 00:00:00.000000

Level B v2 swaps the flat top-15 event list for a pull-by-pull breakdown.
Column is re-typed (same JSON under the hood) and renamed so semantics
match the new shape.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old per-run flat event list. Level B v1 data was only a
    # couple days old and will be regenerated on next ingest — no value
    # in preserving it through the shape change.
    op.drop_column('dungeon_runs', 'timeline_events')
    # New pulls column: JSON array of pull objects, each with events
    # nested. Shape documented on models.py DungeonRun.pulls.
    op.add_column(
        'dungeon_runs',
        sa.Column('pulls', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('dungeon_runs', 'pulls')
    op.add_column(
        'dungeon_runs',
        sa.Column('timeline_events', sa.JSON(), nullable=True),
    )
