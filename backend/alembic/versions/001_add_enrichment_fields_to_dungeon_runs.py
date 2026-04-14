"""add enrichment fields to dungeon_runs

Revision ID: a1b2c3d4e5f6
Revises: None
Create Date: 2026-04-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('dungeon_runs', sa.Column('rating', sa.Integer(), nullable=True))
    op.add_column('dungeon_runs', sa.Column('average_item_level', sa.Float(), nullable=True))
    op.add_column('dungeon_runs', sa.Column('keystone_affixes', sa.JSON(), nullable=True))
    op.add_column('dungeon_runs', sa.Column('healing_received', sa.Float(), nullable=True))
    op.add_column('dungeon_runs', sa.Column('cc_casts', sa.Integer(), nullable=True))
    op.add_column('dungeon_runs', sa.Column('critical_interrupts', sa.Integer(), nullable=True))
    op.add_column('dungeon_runs', sa.Column('avoidable_deaths', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('dungeon_runs', 'avoidable_deaths')
    op.drop_column('dungeon_runs', 'critical_interrupts')
    op.drop_column('dungeon_runs', 'cc_casts')
    op.drop_column('dungeon_runs', 'healing_received')
    op.drop_column('dungeon_runs', 'keystone_affixes')
    op.drop_column('dungeon_runs', 'average_item_level')
    op.drop_column('dungeon_runs', 'rating')
