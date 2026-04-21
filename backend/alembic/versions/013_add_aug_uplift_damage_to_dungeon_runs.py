"""add aug_uplift_damage to dungeon_runs

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-04-21 00:00:00.000000

Scoring fairness for Augmentation Evoker. `aug_uplift_damage` is the
sum of damage dealt by teammates while the Aug had Ebon Might or
Prescience on them, weighted by the buff's uplift factor — a direct
measure of the contribution Aug makes to the group that's otherwise
invisible on the Aug's own damage bar.

Nullable because the value is computed only for Aug runs (and only
on ingest paths that run after this ships). Null on non-Aug runs and
legacy Aug runs.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'dungeon_runs',
        sa.Column('aug_uplift_damage', sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('dungeon_runs', 'aug_uplift_damage')
