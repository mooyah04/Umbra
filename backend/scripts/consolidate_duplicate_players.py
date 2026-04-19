"""Consolidate duplicate Player rows into a single winner per identity.

When multiple Player rows exist for the same case/whitespace-normalized
(region, realm, name), `_find_player` returns one non-deterministically
because the underlying ILIKE query has no ORDER BY. Users see grades
appear and disappear between page loads.

This script picks a winner for each cluster and moves DungeonRun +
PlayerScore rows from the loser(s) onto the winner, then deletes the
empty loser Player rows.

Winner rule: row with the most data (runs + scores, tiebreaker
last_ingested_at DESC, then id ASC for determinism).

Usage:
    python -m scripts.consolidate_duplicate_players            # dry-run
    python -m scripts.consolidate_duplicate_players --commit   # apply
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime

from sqlalchemy import delete, select, update

from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore


def _identity_key(region: str, realm: str, name: str) -> str:
    norm_realm = "".join(c.lower() for c in realm if c.isalnum())
    return f"{region.lower()}|{norm_realm}|{name.lower()}"


def _score_player_completeness(
    p: Player, run_counts: dict[int, int], score_counts: dict[int, int]
) -> tuple:
    """Sort key — higher is better. Used to pick the cluster winner."""
    return (
        run_counts.get(p.id, 0) + score_counts.get(p.id, 0),
        p.last_ingested_at or datetime.min,
        -p.id,  # negate so a SMALLER id wins ties (earliest created)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist the consolidation. Default is dry-run.")
    args = parser.parse_args()

    with SessionLocal() as session:
        players = list(session.execute(select(Player)).scalars())

        clusters: dict[str, list[Player]] = defaultdict(list)
        for p in players:
            clusters[_identity_key(p.region, p.realm, p.name)].append(p)

        dupe_clusters = {k: v for k, v in clusters.items() if len(v) > 1}
        if not dupe_clusters:
            print("No duplicate Player rows found.")
            return 0

        # Bulk-count runs and scores per player id in one query each,
        # keyed in a dict for constant-time lookup in the sort key.
        from sqlalchemy import func
        run_counts_rows = session.execute(
            select(DungeonRun.player_id, func.count())
            .group_by(DungeonRun.player_id)
        ).all()
        run_counts = {pid: n for pid, n in run_counts_rows}

        score_counts_rows = session.execute(
            select(PlayerScore.player_id, func.count())
            .group_by(PlayerScore.player_id)
        ).all()
        score_counts = {pid: n for pid, n in score_counts_rows}

        print(f"Consolidating {len(dupe_clusters)} identity clusters.\n")

        total_runs_moved = 0
        total_scores_moved = 0
        losers_to_delete: list[int] = []

        for key, rows in sorted(dupe_clusters.items()):
            ranked = sorted(
                rows,
                key=lambda p: _score_player_completeness(p, run_counts, score_counts),
                reverse=True,
            )
            winner = ranked[0]
            losers = ranked[1:]

            winner_runs = run_counts.get(winner.id, 0)
            winner_scores = score_counts.get(winner.id, 0)
            print(f"=== {key} ===")
            print(f"  WINNER id={winner.id} "
                  f"realm={winner.realm!r} runs={winner_runs} "
                  f"scores={winner_scores}")

            for loser in losers:
                lr = run_counts.get(loser.id, 0)
                ls = score_counts.get(loser.id, 0)
                print(f"    loser  id={loser.id} "
                      f"realm={loser.realm!r} runs={lr} scores={ls}")

                # Reassign any runs/scores from the loser onto the winner.
                # When the winner already has a PlayerScore for a role
                # that the loser also has, delete the loser's score
                # rather than create a duplicate (same player+role is
                # meant to be unique conceptually).
                if ls > 0:
                    # PlayerScore is expected to have at most one row
                    # per (player_id, role). If the winner already has
                    # that role, drop the loser's row; otherwise move it.
                    loser_scores = list(session.execute(
                        select(PlayerScore).where(PlayerScore.player_id == loser.id)
                    ).scalars())
                    winner_roles = {
                        s.role for s in session.execute(
                            select(PlayerScore).where(PlayerScore.player_id == winner.id)
                        ).scalars()
                    }
                    for s in loser_scores:
                        if s.role in winner_roles:
                            if args.commit:
                                session.delete(s)
                        else:
                            if args.commit:
                                s.player_id = winner.id
                            total_scores_moved += 1

                if lr > 0:
                    if args.commit:
                        session.execute(
                            update(DungeonRun)
                            .where(DungeonRun.player_id == loser.id)
                            .values(player_id=winner.id)
                        )
                    total_runs_moved += lr

                if args.commit:
                    session.delete(loser)
                losers_to_delete.append(loser.id)

        print(f"\n{'Would delete' if not args.commit else 'Deleting'} "
              f"{len(losers_to_delete)} loser Player rows.")
        print(f"{'Would move' if not args.commit else 'Moved'} "
              f"{total_runs_moved} runs and {total_scores_moved} scores "
              "to their winner rows.")

        if not args.commit:
            print("\nDry-run. Re-run with --commit to apply.")
            return 0

        session.commit()
        print("\nCommitted.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
