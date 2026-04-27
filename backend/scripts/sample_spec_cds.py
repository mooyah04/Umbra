"""Sample top M+ logs for any (class, spec) and aggregate which auras
appear consistently in the BuffsTable. The cohort signal feeds the
per-spec audit: tracked CDs at <50% consensus get pruned, baseline-
but-untracked auras at >70% consensus get added, and split (~30/70)
distributions flag alt-build paths that need both branches tracked.

Generalized from sample_brewmaster_cds.py. Same filters and dedupe;
only the class/spec args + the candidate-CD overlay change.

Usage:
    python -m scripts.sample_spec_cds --class Monk --spec Brewmaster
    python -m scripts.sample_spec_cds --class Paladin --spec Retribution \\
        --samples-per-dungeon 2 --top-n 12

Output: per-fight aura listing while sampling, then a final aggregate
table with appearance % and median uses across the cohort. The agent
or human reading this picks the cutoffs (drop / keep / add) and turns
those into edits to app/scoring/cooldowns.py.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict

from app.scoring.cooldowns import SPEC_MAJOR_COOLDOWNS
from app.wcl.client import WCLClient

# Active Midnight S1 dungeons. Mirrored from the BRM sampler so output
# stays consistent. If the season pool changes, update here AND in
# sample_brewmaster_cds.py — the audit reports baseline against the
# active pool, not legacy dungeons that happen to be in WCL.
DUNGEONS = [
    (12805, "Windrunner Spire"),
    (12874, "Maisara Caverns"),
    (12811, "Magister's Terrace"),
    (112526, "Algeth'ar Academy"),
    (12915, "Nexus-Point Xenas"),
    (61209, "Skyreach"),
    (10658, "Pit of Saron"),
    (361753, "Seat of the Triumvirate"),
]

# Monk → Class.MonkID. WCL's characterRankings query takes className as
# the display string ("Death Knight" not "DeathKnight"), so this maps
# our internal names to that wire format. Spec names are passed through
# as-is — they already match WCL's casing.
WCL_CLASS_NAMES: dict[str, str] = {
    "Warrior": "Warrior",
    "Paladin": "Paladin",
    "Hunter": "Hunter",
    "Rogue": "Rogue",
    "Priest": "Priest",
    "Death Knight": "DeathKnight",
    "Shaman": "Shaman",
    "Mage": "Mage",
    "Warlock": "Warlock",
    "Monk": "Monk",
    "Druid": "Druid",
    "Demon Hunter": "DemonHunter",
    "Evoker": "Evoker",
}

# (class_name, class_id) — needed to look up SPEC_MAJOR_COOLDOWNS so
# the report can show which auras are currently tracked. Source of
# truth is roles.py; duplicated here to avoid the import dance.
CLASS_NAME_TO_ID: dict[str, int] = {
    "Warrior": 1, "Paladin": 2, "Hunter": 3, "Rogue": 4, "Priest": 5,
    "Death Knight": 6, "Shaman": 7, "Mage": 8, "Warlock": 9, "Monk": 10,
    "Druid": 11, "Demon Hunter": 12, "Evoker": 13,
}


def fetch_top_players(
    client: WCLClient,
    encounter_id: int,
    class_name: str,
    spec_name: str,
    n: int,
    metric: str,
) -> list[dict]:
    """One characterRankings page. metric=dps for DPS/tank specs,
    metric=hps for healers — WCL ranks healers by HPS, so dps would
    return a near-empty cohort for them."""
    wcl_class = WCL_CLASS_NAMES.get(class_name, class_name)
    data = client.query("""
    query($eid: Int!, $cls: String!, $spec: String!, $metric: CharacterRankingMetricType!) {
      worldData {
        encounter(id: $eid) {
          characterRankings(
            className: $cls
            specName: $spec
            difficulty: 10
            metric: $metric
          )
        }
      }
    }
    """, {"eid": encounter_id, "cls": wcl_class, "spec": spec_name, "metric": metric})
    cr = data["worldData"]["encounter"]["characterRankings"]
    return (cr.get("rankings") or [])[:n]


def fetch_player_buffs(
    client: WCLClient, code: str, fight_id: int, name: str
) -> list[dict]:
    actors = client.query("""
    query($c: String!) {
      reportData { report(code: $c) { masterData { actors(type: "Player") { id name } } } }
    }
    """, {"c": code})
    actor = next(
        (a for a in actors["reportData"]["report"]["masterData"]["actors"] if a["name"] == name),
        None,
    )
    if not actor:
        return []
    buffs = client.query("""
    query($c: String!, $f: [Int!]!, $s: Int!) {
      reportData { report(code: $c) { buffsTable: table(fightIDs: $f, dataType: Buffs, sourceID: $s) } }
    }
    """, {"c": code, "f": [fight_id], "s": actor["id"]})
    auras = buffs["reportData"]["report"]["buffsTable"]["data"]["auras"]
    return auras


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--class", dest="class_name", required=True,
                    help='Class display name, e.g. "Monk", "Death Knight"')
    ap.add_argument("--spec", dest="spec_name", required=True,
                    help='Spec name, e.g. "Brewmaster", "Holy"')
    ap.add_argument("--samples-per-dungeon", type=int, default=1,
                    help="Distinct players to sample per dungeon (after dedupe)")
    ap.add_argument("--top-n", type=int, default=8,
                    help="How deep into the rankings list to scan per dungeon")
    ap.add_argument("--metric", choices=["dps", "hps"], default=None,
                    help="WCL ranking metric. Default: hps for healer specs, dps otherwise")
    ap.add_argument("--top-cd-show", type=int, default=30,
                    help="How many top-appearing auras to print at the end")
    args = ap.parse_args()

    class_id = CLASS_NAME_TO_ID.get(args.class_name)
    if class_id is None:
        print(f"ERROR: unknown class '{args.class_name}'. "
              f"Valid: {', '.join(CLASS_NAME_TO_ID)}")
        return 2

    # Default metric: healers rank by hps, everyone else by dps. Caller
    # can override if WCL has poor coverage for a spec on the default
    # metric (rare but possible for off-meta tank specs).
    if args.metric is None:
        from app.scoring.roles import get_role
        from app.models import Role
        role = get_role(class_id, args.spec_name)
        args.metric = "hps" if role == Role.healer else "dps"

    client = WCLClient()
    seen: set[tuple[str, str]] = set()
    fight_count = 0
    appearance: Counter[int] = Counter()
    aura_names: dict[int, str] = {}
    usage_data: dict[int, list[tuple[int, str]]] = defaultdict(list)

    print(
        f"Sampling {args.class_name} {args.spec_name}: "
        f"top {args.top_n} per dungeon, taking {args.samples_per_dungeon} "
        f"per dungeon (metric={args.metric})"
    )

    for eid, dname in DUNGEONS:
        print(f"\n=== {dname} ({eid}) ===")
        try:
            top = fetch_top_players(
                client, eid, args.class_name, args.spec_name,
                args.top_n, args.metric,
            )
        except Exception as e:
            print(f"  ranking fetch failed: {e}")
            continue

        sampled = 0
        for r in top:
            if sampled >= args.samples_per_dungeon:
                break
            name = r.get("name")
            server = r.get("server", {}).get("name") if isinstance(r.get("server"), dict) else None
            if not name or not server:
                continue
            if (server, name.lower()) in seen:
                continue
            report = r.get("report") or {}
            code = report.get("code")
            fight_id = report.get("fightID")
            if not code or not fight_id:
                continue
            keylvl = r.get("hardModeLevel") or "?"
            try:
                auras = fetch_player_buffs(client, code, fight_id, name)
            except Exception as e:
                print(f"  {name}-{server} (key+{keylvl}): buffs fetch failed: {e}")
                continue
            seen.add((server, name.lower()))
            sampled += 1
            fight_count += 1
            print(f"  {name}-{server} (key+{keylvl}): {len(auras)} auras")
            for a in auras:
                gid = a.get("guid")
                if gid is None:
                    continue
                appearance[gid] += 1
                aura_names[gid] = a.get("name") or aura_names.get(gid, "?")
                usage_data[gid].append((a.get("totalUses") or 0, name))

    print(f"\n=== Aggregate over {fight_count} {args.class_name} "
          f"{args.spec_name} fights ===")

    # Currently-tracked CDs in cooldowns.py — show their consensus
    # so the auditor can decide what stays vs goes.
    tracked = SPEC_MAJOR_COOLDOWNS.get((class_id, args.spec_name), [])
    if tracked:
        print("\nCurrently tracked cooldowns — appearance % across the sample:")
        print(f"{'aura_id':>10}  {'consensus':>9}  {'med_uses':>8}  {'name'}")
        for buff_id, name, _uptime, _kind in tracked:
            cnt = appearance.get(buff_id, 0)
            pct = (cnt / fight_count * 100) if fight_count else 0
            uses = [u for u, _n in usage_data.get(buff_id, [])]
            med = sorted(uses)[len(uses) // 2] if uses else 0
            wcl_name = aura_names.get(buff_id, "")
            verdict = ""
            if pct < 50:
                verdict = " <- DROP candidate (<50%)"
            elif 30 < pct < 90:
                verdict = " <- check alt-build split"
            print(f"{buff_id:>10}  {pct:>7.0f}%  {med:>8}   {name}  [{wcl_name}]{verdict}")
    else:
        print(f"\nNo currently-tracked cooldowns for ({class_id}, {args.spec_name}).")

    print(f"\nTop {args.top_cd_show} most-common buffs across the cohort "
          "(spot anything we should add):")
    print(f"{'aura_id':>10}  {'pct':>5}  {'med_uses':>8}  name")
    for gid, cnt in appearance.most_common(args.top_cd_show):
        pct = cnt / fight_count * 100 if fight_count else 0
        med_uses = (
            sorted([u for u, _n in usage_data[gid]])[len(usage_data[gid]) // 2]
            if usage_data[gid] else 0
        )
        already_tracked = " (tracked)" if any(
            b == gid for b, _n, _u, _k in tracked
        ) else ""
        print(
            f"  {gid:>10}  {pct:>4.0f}%  {med_uses:>8}   "
            f"{aura_names.get(gid, '?')}{already_tracked}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
