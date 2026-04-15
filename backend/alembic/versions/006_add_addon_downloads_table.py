"""add addon_downloads table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'addon_downloads',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'downloaded_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('ip_hash', sa.String(length=64), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
    )
    op.create_index(
        'ix_addon_downloads_downloaded_at',
        'addon_downloads',
        ['downloaded_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_addon_downloads_downloaded_at', table_name='addon_downloads')
    op.drop_table('addon_downloads')
