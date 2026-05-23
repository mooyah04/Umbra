"""dedup players + add unique constraint on (name, realm, region)

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-05-23 00:00:00.000000

Same shape of bug as migration 014 fixed for dungeon_runs, but for
players. The lookup-before-insert pattern in ingest/discovery
(`Player.name.ilike(...)` + `realm_key` comparison) is correct but
TOCTOU-racy: two near-simultaneous ingests for the same character —
e.g. the user clicking Search twice in quick succession, or a search
racing with crawler discovery — both see "no row exists" and both
INSERT. With no DB-level constraint, both rows persist. Each then
accumulates its own PlayerScore and the homepage /api/players/top
endpoint surfaces both, producing duplicate "Recently Graded" cards.
Observed live as `Mumzy-Illidan-US` and `Kuromigirl-Ysondre-US`.

The constraint is on the normalized identity (lower(name),
lower(realm), upper(region)) because realm casing has varied between
ingest paths historically — locking to literal-string equality would
let `Illidan` and `illidan` slip past as separate rows again.

Survivor-pick strategy: lowest id in each group. That's the row that
won the race and has had the longest to accumulate enrichment (runs,
scores, media). Dungeon_runs whose loser-row already has a matching
run on the survivor are deleted before re-pointing, so the
uq_dungeon_runs_player_report_fight constraint from migration 014
doesn't fire on the UPDATE. Loser PlayerScore rows are dropped
outright — the survivor already has its own score and the next
ingest will refresh anything stale.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f8a9b0c1d2e3'
down_revision: Union[str, None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Map every dup row to its survivor (lowest id in the normalized
    # identity group). Materialized as a temp table so each downstream
    # statement re-uses the same set without re-aggregating.
    op.execute("""
        CREATE TEMPORARY TABLE _player_dup_map AS
        SELECT
            p.id AS dup_id,
            survivors.survivor_id AS survivor_id
        FROM players p
        JOIN (
            SELECT
                LOWER(name) AS nk,
                LOWER(realm) AS rk,
                UPPER(region) AS gk,
                MIN(id) AS survivor_id
            FROM players
            GROUP BY LOWER(name), LOWER(realm), UPPER(region)
        ) AS survivors
          ON survivors.nk = LOWER(p.name)
         AND survivors.rk = LOWER(p.realm)
         AND survivors.gk = UPPER(p.region)
        WHERE p.id <> survivors.survivor_id
    """)

    # Drop loser dungeon_runs whose (wcl_report_id, fight_id) the
    # survivor already has — otherwise the UPDATE below would violate
    # uq_dungeon_runs_player_report_fight.
    op.execute("""
        DELETE FROM dungeon_runs
        WHERE id IN (
            SELECT dr.id
            FROM dungeon_runs dr
            JOIN _player_dup_map m ON dr.player_id = m.dup_id
            WHERE EXISTS (
                SELECT 1 FROM dungeon_runs dr2
                WHERE dr2.player_id = m.survivor_id
                  AND dr2.wcl_report_id = dr.wcl_report_id
                  AND dr2.fight_id = dr.fight_id
            )
        )
    """)

    # Re-point surviving loser dungeon_runs onto the survivor.
    op.execute("""
        UPDATE dungeon_runs
        SET player_id = (
            SELECT m.survivor_id
            FROM _player_dup_map m
            WHERE m.dup_id = dungeon_runs.player_id
        )
        WHERE player_id IN (SELECT dup_id FROM _player_dup_map)
    """)

    # Loser PlayerScores are derived state; survivor already has its
    # own and the next ingest recomputes if anything moved.
    op.execute("""
        DELETE FROM player_scores
        WHERE player_id IN (SELECT dup_id FROM _player_dup_map)
    """)

    # Finally drop the dup Player rows. wcl_id is the only unique
    # column; deleting the loser frees up its wcl_id slot so a future
    # ingest can re-attach it to the survivor without conflict.
    op.execute("""
        DELETE FROM players
        WHERE id IN (SELECT dup_id FROM _player_dup_map)
    """)

    op.execute("DROP TABLE _player_dup_map")

    # The constraint lives on the raw columns, not on lower()/upper()
    # expressions, because cross-dialect expression indexes are a
    # portability headache (Postgres supports them, SQLite needs a
    # generated column). The ingest path is responsible for writing
    # a single canonical casing per identity — the constraint is the
    # backstop against the TOCTOU race, not against casing drift.
    # If casing drift recurs, the right fix is to normalize on write,
    # not to push complexity into the schema.
    op.create_unique_constraint(
        'uq_players_name_realm_region',
        'players',
        ['name', 'realm', 'region'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_players_name_realm_region',
        'players',
        type_='unique',
    )
    # No inverse for the dedup — deleted rows are gone.
