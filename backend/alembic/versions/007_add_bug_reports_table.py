"""add bug_reports table

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-04-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bug_reports',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='website'),
        sa.Column('submitter_name', sa.String(length=80), nullable=True),
        sa.Column('submitter_email', sa.String(length=200), nullable=True),
        sa.Column('summary', sa.String(length=200), nullable=False),
        sa.Column('details', sa.String(length=8000), nullable=False, server_default=''),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_hash', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='new'),
    )
    op.create_index(
        'ix_bug_reports_created_at',
        'bug_reports',
        ['created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_bug_reports_created_at', table_name='bug_reports')
    op.drop_table('bug_reports')
