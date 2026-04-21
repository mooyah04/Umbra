"""Validate the rotation timeline pipeline against known-good logs.

Pulls the top N Fury Warrior logs for a current-season dungeon directly
from WCL (no DB writes, no ingest), fetches each player's cast timeline
via get_player_cast_timeline, and prints the opener + cast frequency so
a human can eyeball whether the data matches what a Fury rotation looks
like (Bloodthirst / Raging Blow / Rampage / Whirlwind / Execute should
dominate the frequency table).

Usage:
    python -m scripts.validate_rotation
    python -m scripts.validate_rotation --limit 5 --encounter 12811
"""
from __future__ import annotations

import argparse
from collections import Counter

from app.wcl.client import WCLQueryError, WCLRateLimitedError, wcl_client


DEFAULT_CLASS = "Warrior"
DEFAULT_SPEC = "Fury"
DEFAULT_ENCOUNTER = 12811  # Magister's Terrace — Midnight S1 pool
DEFAULT_LIMIT = 5
OPENER_LEN = 15
TOP_N_ABILITIES = 12


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--class-name", default=DEFAULT_CLASS)
    parser.add_argument("--spec", default=DEFAULT_SPEC)
    parser.add_argument("--encounter", type=int, default=DEFAULT_ENCOUNTER)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()

    print(
        f"\n=== Rotation validation: {args.spec} {args.class_name} "
        f"on encounter {args.encounter} (top {args.limit}) ===\n"
    )

    try:
        top = wcl_client.get_top_characters_for_spec(
            encounter_id=args.encounter,
            class_name=args.class_name,
            spec_name=args.spec,
            metric="dps",
            limit=args.limit,
        )
    except WCLRateLimitedError as e:
        print(f"WCL rate-limited: retry after {e.retry_after}s")
        return 2
    except WCLQueryError as e:
        print(f"WCL query error: {e}")
        return 2

    if not top:
        print("No rankings returned — check class/spec casing or encounter ID.")
        return 1

    for idx, entry in enumerate(top, start=1):
        name = entry["name"]
        report_code = entry["report_code"]
        fight_id = entry["fight_id"]
        print(
            f"[{idx}] {name} — {report_code} fight {fight_id} "
            f"(amount={entry.get('amount')})"
        )

        # Resolve sourceID via the report's actor list.
        try:
            header = wcl_client.get_report_header_and_fights(report_code)
        except (WCLQueryError, WCLRateLimitedError) as e:
            print(f"    Could not read report header: {e}")
            continue
        actor_ids = (header.get("actors_by_name") or {}).get(name) or []
        if not actor_ids:
            print(f"    {name!r} not found in report actors.")
            continue
        source_id = actor_ids[0]

        try:
            payload = wcl_client.get_player_cast_timeline(
                report_code, fight_id, source_id
            )
        except (WCLQueryError, WCLRateLimitedError) as e:
            print(f"    Cast timeline fetch failed: {e}")
            continue

        casts = payload.get("casts", []) or []
        abilities = payload.get("abilities", {}) or {}

        if not casts:
            print("    No cast events — skipping.")
            continue

        duration_s = casts[-1]["t"] if casts else 0
        print(
            f"    {len(casts)} casts over {duration_s:.0f}s "
            f"({len(abilities)} distinct abilities)"
        )

        # Opener — first N cast sequence
        print(f"    Opener ({OPENER_LEN} casts):")
        for i, c in enumerate(casts[:OPENER_LEN], start=1):
            ab = abilities.get(c["s"]) or {}
            name_str = ab.get("name") or f"#{c['s']}"
            print(f"      {i:2d}. [{c['t']:6.2f}s] {name_str} (id={c['s']})")

        # Frequency table — top N by count
        counter = Counter(c["s"] for c in casts)
        print(f"    Top {TOP_N_ABILITIES} casts by frequency:")
        for spell_id, count in counter.most_common(TOP_N_ABILITIES):
            ab = abilities.get(spell_id) or {}
            name_str = ab.get("name") or f"Spell #{spell_id}"
            pct = 100.0 * count / len(casts)
            print(f"      {count:4d}x  ({pct:5.1f}%)  {name_str}  (id={spell_id})")
        print()

    print("=== Done. ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
