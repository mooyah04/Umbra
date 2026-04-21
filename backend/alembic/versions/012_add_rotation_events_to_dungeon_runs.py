"""add rotation_events to dungeon_runs

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-04-21 00:00:00.000000

Lazy cache for per-run cast timelines. Populated on first user request
to the /rotation endpoint, not during ingest, so we don't pay the WCL
cost for runs nobody ever views.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f2a3b4c5d6e7'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'dungeon_runs',
        sa.Column('rotation_events', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('dungeon_runs', 'rotation_events')
