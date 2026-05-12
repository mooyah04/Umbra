"""add bug_report_replies table

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, None] = 'd6e7f8a9b0c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'bug_report_replies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'bug_report_id',
            sa.Integer(),
            sa.ForeignKey('bug_reports.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'sent_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column('to_email', sa.String(length=200), nullable=False),
        sa.Column('subject', sa.String(length=300), nullable=False),
        sa.Column('body', sa.String(length=16000), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='sent'),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
    )
    op.create_index(
        'ix_bug_report_replies_bug_report_id',
        'bug_report_replies',
        ['bug_report_id'],
    )
    op.create_index(
        'ix_bug_report_replies_sent_at',
        'bug_report_replies',
        ['sent_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_bug_report_replies_sent_at', table_name='bug_report_replies')
    op.drop_index('ix_bug_report_replies_bug_report_id', table_name='bug_report_replies')
    op.drop_table('bug_report_replies')
