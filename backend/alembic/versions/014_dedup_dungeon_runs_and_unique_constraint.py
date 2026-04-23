"""dedup dungeon_runs + add unique constraint

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-04-23 00:00:00.000000

Closes a long-standing race: the ingest pipeline's dedup was
application-level only (`pipeline/ingest.py` built a set of existing
(wcl_report_id, fight_id) per player, then checked each new fight
against it). Two concurrent ingest calls for the same player —
triggered, e.g., by two party members clicking Refresh on the same
profile at once — can both pass the in-memory check before either
commits, producing duplicate rows. Observed live on
Luminès-EU-Ysondre: 7 groups of exact duplicates on
(wcl_report_id, fight_id) within a single player.

This migration:
  1. Deletes duplicate rows keeping the lowest id in each
     (player_id, wcl_report_id, fight_id) group. Lowest id = oldest
     row = the one that won the race and has had the most time to
     accumulate enrichment (pulls, rotation, etc.), so any back-
     references from other tables that happen to point at the first
     insert stay valid.
  2. Adds a unique constraint on (player_id, wcl_report_id, fight_id)
     so the race can never produce duplicates again. Future
     concurrent inserts will raise IntegrityError and the ingest
     path will treat that as "already stored" (handled in a
     separate code change in ingest.py).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b4c5d6e7f8a9'
down_revision: Union[str, None] = 'a3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cleanup: delete all but the earliest row per dedup-key group.
    # Written as plain SQL so the same statement runs on Postgres
    # (production) and SQLite (tests). Both support correlated
    # subqueries and MIN() + GROUP BY.
    op.execute("""
        DELETE FROM dungeon_runs
        WHERE id NOT IN (
            SELECT min_id FROM (
                SELECT MIN(id) AS min_id
                FROM dungeon_runs
                GROUP BY player_id, wcl_report_id, fight_id
            ) AS keepers
        )
    """)
    op.create_unique_constraint(
        'uq_dungeon_runs_player_report_fight',
        'dungeon_runs',
        ['player_id', 'wcl_report_id', 'fight_id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_dungeon_runs_player_report_fight',
        'dungeon_runs',
        type_='unique',
    )
    # No inverse for the cleanup — the deleted rows are gone.
