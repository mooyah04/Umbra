"""Rename DungeonRun.spec_name 'BeastMastery' -> 'Beast Mastery'.

WCL emits the compound spec name without a space; every scoring lookup
uses the canonical display form with a space. Existing rows in DB
silently fell through the empty-cooldowns branch and scored 100 on
cooldown_usage. Going forward, ingest normalizes; this one-shot fixes
the historical rows.

Usage:
    python -m scripts.backfill_bm_spec_name              # dry-run
    python -m scripts.backfill_bm_spec_name --commit
"""
from __future__ import annotations

import argparse

from sqlalchemy import text

from app.db import SessionLocal


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit", action="store_true",
                        help="Persist changes. Default dry-run.")
    args = parser.parse_args()

    with SessionLocal() as session:
        count = session.execute(
            text("SELECT COUNT(*) FROM dungeon_runs WHERE spec_name = 'BeastMastery'")
        ).scalar()
        print(f"Rows with spec_name='BeastMastery': {count}")

        if not count:
            return 0

        if args.commit:
            session.execute(
                text("UPDATE dungeon_runs SET spec_name = 'Beast Mastery' "
                     "WHERE spec_name = 'BeastMastery'")
            )
            session.commit()
            print(f"committed: renamed {count} rows")
        else:
            print(f"dry-run: would rename {count} rows; re-run with --commit")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
