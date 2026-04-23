"""add utility_events to dungeon_runs

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-04-23 00:00:00.000000

Lazy-fetch cache for the per-run utility ability breakdown that
powers the run page's Utility tile receipts ("Solar Beam x3,
Mighty Bash x1, Nature's Cure x4"). Populated on first request
to /runs/{id}/utility from a WCL Casts events query filtered to
the player's class/spec-specific interrupt + CC + dispel spell
IDs, then served cached on subsequent views.

Nullable because every existing run starts empty and gets
populated only if the utility endpoint is hit — keeps the
migration cheap and the storage cost proportional to actual use.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c5d6e7f8a9b0'
down_revision: Union[str, None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'dungeon_runs',
        sa.Column('utility_events', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('dungeon_runs', 'utility_events')
