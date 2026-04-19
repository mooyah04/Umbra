"""List Player rows that share a case/whitespace-normalized identity.

Ingest is supposed to look up players case-insensitively, but historical
paths (crawler, leaderboard poll, claim form, user search) have all
created Player rows with different casing on name/realm/region. When
_find_player matches with ILIKE and no ORDER BY, the winning row is
non-deterministic across requests — users see grades appear and
disappear between profile loads.

This script finds those clusters so we can consolidate. Read-only.

Usage:
    python -m scripts.find_duplicate_players
    python -m scripts.find_duplicate_players --name Peeli   # filter
"""
from __future__ import annotations

import argparse
from collections import defaultdict

from sqlalchemy import select

from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore


def _key(region: str, realm: str, name: str) -> str:
    norm_realm = "".join(c.lower() for c in realm if c.isalnum())
    return f"{region.lower()}|{norm_realm}|{name.lower()}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="Filter to players whose name matches (ilike)")
    args = parser.parse_args()

    with SessionLocal() as session:
        stmt = select(Player)
        if args.name:
            stmt = stmt.where(Player.name.ilike(args.name))
        players = list(session.execute(stmt).scalars())

        clusters: dict[str, list[Player]] = defaultdict(list)
        for p in players:
            clusters[_key(p.region, p.realm, p.name)].append(p)

        dupes = {k: v for k, v in clusters.items() if len(v) > 1}
        if not dupes:
            print("No duplicate Player rows found.")
            return 0

        print(f"Found {len(dupes)} identity clusters with duplicates:\n")
        for key, rows in sorted(dupes.items(), key=lambda x: -len(x[1])):
            print(f"=== {key} ({len(rows)} rows) ===")
            for p in rows:
                score_count = session.execute(
                    select(PlayerScore).where(PlayerScore.player_id == p.id)
                ).all()
                run_count = session.execute(
                    select(DungeonRun).where(DungeonRun.player_id == p.id)
                ).all()
                print(
                    f"  id={p.id:>6}  "
                    f"region={p.region!r}  realm={p.realm!r}  name={p.name!r}  "
                    f"scores={len(score_count):>2}  runs={len(run_count):>4}  "
                    f"last_ingested={p.last_ingested_at}"
                )
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
