"""add blizzard media fields to players

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('players', sa.Column('avatar_url', sa.String(length=500), nullable=True))
    op.add_column('players', sa.Column('inset_url', sa.String(length=500), nullable=True))
    op.add_column('players', sa.Column('render_url', sa.String(length=500), nullable=True))
    op.add_column('players', sa.Column('media_fetched_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('players', 'media_fetched_at')
    op.drop_column('players', 'render_url')
    op.drop_column('players', 'inset_url')
    op.drop_column('players', 'avatar_url')
