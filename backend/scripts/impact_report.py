"""Impact report — see how the spec audit edits would move grades.

For each target spec:
  - Find every player with min_runs_for_grade runs of that spec.
  - Recompute their PlayerScore using current engine logic.
  - Compare composite/grade to the stored PlayerScore.
  - Optionally refetch WCL BuffsTable so cooldowns.py edits show up.

Read-only — never writes to the DB.

Two modes:
  default   — uses cooldown_usage_pct already on DungeonRun. Captures
              HEALER_SPECS_WITH_INTERRUPT changes, weight changes, and
              any composite-logic shift that doesn't depend on the
              cd_usage value itself. Costs zero WCL budget.
  --refetch — refetches BuffsTable per run and recomputes cd_usage_pct
              under current cooldowns.py. Burns WCL (~1-2 calls/run).

Usage:
  python -m scripts.impact_report --spec Warrior:Arms
  python -m scripts.impact_report --class Druid
  python -m scripts.impact_report --all-edited
  python -m scripts.impact_report --spec Rogue:Outlaw --refetch
  python -m scripts.impact_report --all-edited --limit 50 --refetch
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore, Role
from app.pipeline.ingest import _get_cooldown_usage
from app.scoring.cooldowns import SPEC_MAJOR_COOLDOWNS, get_cooldowns_for_spec
from app.scoring.engine import score_player_runs
from app.scoring.roles import get_role
from app.wcl.client import WCLQueryError, WCLRateLimitedError, wcl_client


CLASS_NAME_TO_ID = {
    "Warrior": 1, "Paladin": 2, "Hunter": 3, "Rogue": 4, "Priest": 5,
    "Death Knight": 6, "Shaman": 7, "Mage": 8, "Warlock": 9,
    "Monk": 10, "Druid": 11, "Demon Hunter": 12, "Evoker": 13,
}
ID_TO_CLASS_NAME = {v: k for k, v in CLASS_NAME_TO_ID.items()}

# Specs touched by the 2026-04-27 audit (cooldowns.py edits or the
# Mistweaver HEALER_SPECS_WITH_INTERRUPT add-then-revert). Used by
# --all-edited.
EDITED_SPECS: list[tuple[int, str]] = [
    (1, "Arms"), (1, "Fury"), (1, "Protection"),
    (3, "Beast Mastery"), (3, "Survival"),
    (4, "Assassination"), (4, "Outlaw"),
    (5, "Discipline"), (5, "Shadow"),
    (6, "Blood"),
    (7, "Elemental"), (7, "Restoration"),
    (9, "Affliction"),
    (10, "Mistweaver"),
    (11, "Balance"), (11, "Feral"), (11, "Guardian"),
]


@dataclass
class PlayerImpact:
    name: str
    realm: str
    region: str
    role: Role
    old_grade: str | None
    new_grade: str
    old_composite: float | None
    new_composite: float
    old_cd_avg: float | None       # mean cd_usage_pct across spec runs (pre-refetch)
    new_cd_avg: float | None       # mean cd_usage_pct across spec runs (post-refetch)
    refetched: bool


def _zone_pct_or_none(existing, key: str) -> float | None:
    """Read a stored zone percentile, returning None when the value is
    the engine's "excluded at last scoring" placeholder.

    The engine writes `category_scores[key] = 0.0` when a category was
    excluded (no valid percentile across runs) and renormalizes weights
    to drop it from composite. `excluded_categories` is on ScoreResult
    but not persisted on PlayerScore, so we detect the placeholder by
    value: 0.0 is treated as None. A genuine 0th-percentile player
    looks the same — but that's vanishingly rare among graded players,
    and the engine's per-run recompute path gives a fairer read either
    way.
    """
    if not existing:
        return None
    v = existing.category_scores.get(key)
    if v is None or v == 0.0:
        return None
    return v


def _refetch_cd_usage(
    run: DungeonRun,
    player: Player,
    spec_cds,
    actor_cache: dict[str, dict[str, int]],
) -> float | None:
    """Refetch BuffsTable from WCL and recompute cd_usage_pct. Returns
    None when WCL data is unavailable (missing actor, query error)."""
    if run.wcl_report_id not in actor_cache:
        try:
            md = wcl_client.query("""
            query($c: String!) {
              reportData { report(code: $c) { masterData { actors(type: "Player") { id name } } } }
            }
            """, {"c": run.wcl_report_id})
            actors = md["reportData"]["report"]["masterData"]["actors"]
            actor_cache[run.wcl_report_id] = {
                a["name"].lower(): a["id"] for a in actors
            }
        except WCLQueryError:
            return None

    actor_id = actor_cache[run.wcl_report_id].get(player.name.lower())
    if not actor_id:
        return None

    try:
        buffs = wcl_client.query("""
        query($c: String!, $f: [Int!]!, $s: Int!) {
          reportData { report(code: $c) { buffsTable: table(fightIDs: $f, dataType: Buffs, sourceID: $s) } }
        }
        """, {"c": run.wcl_report_id, "f": [run.fight_id], "s": actor_id})
        return _get_cooldown_usage(
            buffs["reportData"]["report"]["buffsTable"], spec_cds, run.duration
        )
    except WCLQueryError:
        return None


def _process_spec(
    session,
    class_id: int,
    spec_name: str,
    refetch: bool,
    limit: int | None,
) -> list[PlayerImpact]:
    role = get_role(class_id, spec_name)
    spec_cds = get_cooldowns_for_spec(class_id, spec_name) if refetch else []

    if refetch and not spec_cds:
        print(f"  no cooldowns configured for {spec_name}; refetch is a no-op for this spec")

    player_ids = list(session.execute(
        select(DungeonRun.player_id)
        .join(Player, Player.id == DungeonRun.player_id)
        .where(Player.class_id == class_id, DungeonRun.spec_name == spec_name)
        .distinct()
    ).scalars())

    impacts: list[PlayerImpact] = []
    actor_cache: dict[str, dict[str, int]] = {}

    for pid in player_ids:
        if limit and len(impacts) >= limit:
            break

        player = session.get(Player, pid)
        if not player:
            continue

        all_runs = list(session.execute(
            select(DungeonRun)
            .where(DungeonRun.player_id == pid)
            .order_by(DungeonRun.logged_at.desc())
        ).scalars())
        recent_runs = all_runs[: settings.max_runs_to_analyze]

        runs_by_role: dict[Role, list[DungeonRun]] = defaultdict(list)
        for r in recent_runs:
            runs_by_role[r.role].append(r)

        role_runs = runs_by_role.get(role) or []
        spec_runs = [r for r in role_runs if r.spec_name == spec_name]
        if len(spec_runs) < settings.min_runs_for_grade:
            continue

        existing = session.execute(
            select(PlayerScore).where(
                PlayerScore.player_id == pid, PlayerScore.role == role
            )
        ).scalar_one_or_none()
        # `category_scores["damage_output"] == 0.0` ambiguously means
        # either "real 0th percentile" or "category was excluded at last
        # ingest and 0.0 is the placeholder". The engine writes 0.0 for
        # excluded categories but doesn't persist `excluded_categories`.
        # Treating that 0.0 as a real percentile here would re-include
        # it in the composite (dragging it down by ~5-6 points × the
        # category weight), which is exactly what produced the Roq /
        # Trbbstd "outlier" drops. Pass None instead so the engine
        # recomputes from per-fight r.dps values and re-excludes
        # cleanly when none are valid.
        zone_dps = _zone_pct_or_none(existing, "damage_output")
        zone_dps_ilvl = _zone_pct_or_none(existing, "damage_output_ilvl")

        old_cd_avg = None
        new_cd_avg = None
        originals: list[tuple[DungeonRun, float]] = []

        if refetch and spec_cds:
            old_pcts = []
            new_pcts = []
            for run in spec_runs:
                new_pct = _refetch_cd_usage(run, player, spec_cds, actor_cache)
                if new_pct is None:
                    continue
                old_pcts.append(run.cooldown_usage_pct or 0)
                new_pcts.append(new_pct)
                # Mutate in memory so score_player_runs picks up the new
                # value. Restored after scoring; never committed.
                originals.append((run, run.cooldown_usage_pct))
                run.cooldown_usage_pct = new_pct
            if new_pcts:
                old_cd_avg = sum(old_pcts) / len(old_pcts)
                new_cd_avg = sum(new_pcts) / len(new_pcts)

        try:
            result = score_player_runs(
                role_runs, role,
                zone_dps_percentile=zone_dps,
                zone_dps_ilvl_percentile=zone_dps_ilvl,
                class_id=class_id,
            )
        except Exception as e:
            print(
                f"  scoring error for {player.name}-{player.realm}: {e}",
                file=sys.stderr,
            )
            for run, old_pct in originals:
                run.cooldown_usage_pct = old_pct
            continue
        finally:
            for run, old_pct in originals:
                run.cooldown_usage_pct = old_pct

        impacts.append(PlayerImpact(
            name=player.name,
            realm=player.realm,
            region=player.region,
            role=role,
            old_grade=existing.overall_grade if existing else None,
            new_grade=result.overall_grade,
            old_composite=existing.composite_score if existing else None,
            new_composite=result.composite_score,
            old_cd_avg=old_cd_avg,
            new_cd_avg=new_cd_avg,
            refetched=refetch and spec_cds is not None and len(spec_cds) > 0,
        ))

    return impacts


def _print_report(label: str, impacts: list[PlayerImpact]) -> None:
    print(f"\n==== {label} ====")
    print(f"Players analyzed: {len(impacts)}")
    if not impacts:
        return

    measurable = [i for i in impacts if i.old_composite is not None]
    deltas = [i.new_composite - i.old_composite for i in measurable]

    if deltas:
        avg = sum(deltas) / len(deltas)
        moved_up = sum(1 for d in deltas if d > 0.05)
        moved_dn = sum(1 for d in deltas if d < -0.05)
        unchanged = len(deltas) - moved_up - moved_dn
        print(
            f"Composite delta: avg {avg:+.2f}, "
            f"max {max(deltas):+.2f} / min {min(deltas):+.2f}"
        )
        print(
            f"  unchanged ({unchanged}), up ({moved_up}), down ({moved_dn}) "
            f"of {len(deltas)} comparable"
        )

    grade_changes = [
        (i.old_grade, i.new_grade) for i in impacts
        if i.old_grade and i.old_grade != i.new_grade
    ]
    if grade_changes:
        print(f"Grade-tier moves: {len(grade_changes)} of {len(impacts)} players")
        for (old, new), n in Counter(grade_changes).most_common(8):
            print(f"  {old} -> {new}: {n}")
    else:
        print("Grade-tier moves: none")

    refetched = [
        i for i in impacts
        if i.refetched and i.new_cd_avg is not None and i.old_cd_avg is not None
    ]
    if refetched:
        old_mean = sum(i.old_cd_avg for i in refetched) / len(refetched)
        new_mean = sum(i.new_cd_avg for i in refetched) / len(refetched)
        print(
            f"cd_usage_pct mean (refetched, n={len(refetched)}): "
            f"{old_mean:.1f} -> {new_mean:.1f} ({new_mean - old_mean:+.1f})"
        )

    movers = sorted(
        measurable,
        key=lambda i: abs(i.new_composite - i.old_composite),
        reverse=True,
    )[:10]
    if movers and any(abs(i.new_composite - i.old_composite) >= 0.1 for i in movers):
        print("Top movers:")
        for i in movers:
            d = i.new_composite - i.old_composite
            if abs(d) < 0.1:
                continue
            print(
                f"  {i.name}-{i.realm} {i.region}: "
                f"{i.old_grade} ({i.old_composite:.1f}) -> "
                f"{i.new_grade} ({i.new_composite:.1f}) [{d:+.1f}]"
            )


def main() -> int:
    # Force UTF-8 stdout so non-ASCII player names from EU/KR/TW don't
    # crash printing on Windows terminals (cp1252 default).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--spec",
        help="ClassName:SpecName, e.g. 'Warrior:Arms' or 'Death Knight:Blood'",
    )
    g.add_argument(
        "--class", dest="class_name",
        help="All specs in the class, e.g. 'Druid'",
    )
    g.add_argument(
        "--all-edited", action="store_true",
        help="All specs touched by the 2026-04-27 audit",
    )
    parser.add_argument(
        "--refetch", action="store_true",
        help="Refetch WCL BuffsTable per run to pick up cooldowns.py edits "
             "(~1-2 WCL calls per run, watch the 18k/hr budget)",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Cap players processed per spec",
    )
    args = parser.parse_args()

    targets: list[tuple[int, str]] = []
    if args.spec:
        if ":" not in args.spec:
            print("--spec format: ClassName:SpecName", file=sys.stderr)
            return 1
        cls, spec = args.spec.split(":", 1)
        cid = CLASS_NAME_TO_ID.get(cls)
        if cid is None:
            print(f"Unknown class '{cls}'. Known: {sorted(CLASS_NAME_TO_ID)}", file=sys.stderr)
            return 1
        targets = [(cid, spec)]
    elif args.class_name:
        cid = CLASS_NAME_TO_ID.get(args.class_name)
        if cid is None:
            print(f"Unknown class '{args.class_name}'. Known: {sorted(CLASS_NAME_TO_ID)}", file=sys.stderr)
            return 1
        targets = sorted(
            [(c, s) for (c, s) in SPEC_MAJOR_COOLDOWNS if c == cid],
            key=lambda t: t[1],
        )
        if not targets:
            print(f"No specs in cooldowns.py for class_id {cid}", file=sys.stderr)
            return 1
    else:
        targets = list(EDITED_SPECS)

    print(f"Mode: {'--refetch' if args.refetch else 'composite-only (no WCL)'}")
    print(f"Targets: {len(targets)} spec(s)")
    if args.limit:
        print(f"Player limit per spec: {args.limit}")

    with SessionLocal() as session:
        for cid, spec in targets:
            label = f"{ID_TO_CLASS_NAME.get(cid, cid)}:{spec}"
            try:
                impacts = _process_spec(session, cid, spec, args.refetch, args.limit)
            except WCLRateLimitedError as e:
                print(
                    f"\n!! WCL rate-limited mid-{label}; stopping. "
                    f"retry_after={e.retry_after}s"
                )
                break
            _print_report(label, impacts)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
