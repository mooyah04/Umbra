"""add keystone_bonus to dungeon_runs

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-04-17 00:00:00.000000

WCL's keystoneBonus (1/2/3 for +1/+2/+3 chest, 0/null for depleted) is
authoritative for the timed flag. Our prior heuristic compared log
duration to keystoneTime and misclassified razor-thin finishes.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'dungeon_runs',
        sa.Column('keystone_bonus', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('dungeon_runs', 'keystone_bonus')
