"""add dps_percentile_global to dungeon_runs

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-04-27 00:00:00.000000

Stores the un-bracketed (global) DPS percentile alongside the
bracketed value in `dps`. After the byBracket=true rollout (commit
e5b725c), `dps` holds rankPercent computed within the run's keystone
bracket — fair to low-key players. The global percentile is still
useful as a display signal that tells the player "you're 45/100 vs
+6s, but only 5/100 vs +12s — pushing higher would move this".

Nullable because existing runs were ingested before we fetched both
views and we don't want to backfill the entire table; runs without
the global value just won't show the second number on the run page.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd6e7f8a9b0c1'
down_revision: Union[str, None] = 'c5d6e7f8a9b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'dungeon_runs',
        sa.Column('dps_percentile_global', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('dungeon_runs', 'dps_percentile_global')
