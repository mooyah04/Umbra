"""add discovered_keystone_level to players

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-04-17 00:00:00.000000

Lets the scheduler prefer high-keystone leaderboard stubs over the
long tail when WCL budget is tight. Column is nullable so it doesn't
need backfill — null rows just sort after non-null ones.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd0e1f2a3b4c5'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'players',
        sa.Column('discovered_keystone_level', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('players', 'discovered_keystone_level')
