"""Sample top Brewmaster M+ logs and aggregate which major-CD aura IDs
show up consistently in the BuffsTable. Use this to decide what to
track in app/scoring/cooldowns.py for (10, "Brewmaster").

The current cooldowns.py list (Fortifying Brew, Niuzao, Exploding Keg)
includes Exploding Keg, which is an enemy-debuff and never appears in a
self-buffs table — every BRM scores 0 on it. This sampler tells us
what the real major CDs are at top-end play.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from app.wcl.client import WCLClient

# Active Midnight S1 dungeons
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

SAMPLES_PER_DUNGEON = 1  # 1 dungeon * 8 = 8 BRMs (some may dedupe)
TOP_N_PER_DUNGEON_TO_SCAN = 8


def fetch_top_brms(client: WCLClient, encounter_id: int, n: int) -> list[dict]:
    data = client.query("""
    query($eid: Int!) {
      worldData {
        encounter(id: $eid) {
          characterRankings(
            className: "Monk"
            specName: "Brewmaster"
            difficulty: 10
            metric: dps
          )
        }
      }
    }
    """, {"eid": encounter_id})
    cr = data["worldData"]["encounter"]["characterRankings"]
    return (cr.get("rankings") or [])[:n]


def fetch_player_buffs(client: WCLClient, code: str, fight_id: int, name: str) -> list[dict]:
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
    client = WCLClient()
    seen_brms: set[tuple[str, str]] = set()  # (server, name) dedupe
    fight_count = 0

    # aura_id -> count of BRMs that had it
    appearance: Counter[int] = Counter()
    # aura_id -> name (last-seen)
    aura_names: dict[int, str] = {}
    # aura_id -> list of (uses, brm_name) for analysis
    usage_data: dict[int, list[tuple[int, str]]] = defaultdict(list)

    print(f"Sampling top {TOP_N_PER_DUNGEON_TO_SCAN} BRMs per dungeon, "
          f"taking {SAMPLES_PER_DUNGEON} fight per dungeon...")

    for eid, dname in DUNGEONS:
        print(f"\n=== {dname} ({eid}) ===")
        try:
            top = fetch_top_brms(client, eid, TOP_N_PER_DUNGEON_TO_SCAN)
        except Exception as e:
            print(f"  ranking fetch failed: {e}")
            continue

        sampled = 0
        for r in top:
            if sampled >= SAMPLES_PER_DUNGEON:
                break
            name = r.get("name")
            server = r.get("server", {}).get("name") if isinstance(r.get("server"), dict) else None
            if not name or not server:
                continue
            if (server, name.lower()) in seen_brms:
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
            seen_brms.add((server, name.lower()))
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

    print(f"\n=== Aggregate over {fight_count} BRM fights ===")

    # Highlight BRM-relevant CDs
    brm_candidates = {
        120954: "Fortifying Brew (currently tracked)",
        132578: "Invoke Niuzao (currently tracked)",
        325153: "Exploding Keg (currently tracked - BROKEN, debuff not buff)",
        443113: "Strength of the Black Ox (talent buff)",
        322507: "Celestial Brew",
        115203: "Fortifying Brew (cast id, not buff)",
        115399: "Black Ox Brew (cast id)",
        122470: "Touch of Karma",
        122783: "Diffuse Magic",
        115176: "Zen Meditation",
        122278: "Dampen Harm",
        383697: "Sal'salabim's Strength (talent)",
        383733: "Training of Niuzao",
        414143: "Yu'lon's Grace (tier proc)",
        1241059: "Celestial Infusion (tier proc)",
        1260619: "Elevated Stagger (passive)",
        195630: "Elusive Brawler (passive)",
        228563: "Blackout Combo",
        383800: "Counterstrike (talent proc)",
    }

    print("\nCandidate Brewmaster cooldowns — appearance % across the sample:")
    print(f"{'aura_id':>10}  {'consensus':>9}  {'med_uses':>8}  {'name'}")
    for gid, label in brm_candidates.items():
        cnt = appearance.get(gid, 0)
        if fight_count > 0:
            pct = cnt / fight_count * 100
        else:
            pct = 0
        uses = [u for u, _n in usage_data.get(gid, [])]
        med = sorted(uses)[len(uses) // 2] if uses else 0
        wcl_name = aura_names.get(gid, "")
        marker = " *" if pct >= 60 else ""
        print(f"{gid:>10}  {pct:>7.0f}%  {med:>8}   {label}  [{wcl_name}]{marker}")

    print("\nTop 30 most-common buffs across the BRM cohort (any aura, "
          "to spot anything we missed):")
    for gid, cnt in appearance.most_common(30):
        pct = cnt / fight_count * 100 if fight_count else 0
        med_uses = sorted([u for u, _n in usage_data[gid]])[len(usage_data[gid]) // 2]
        print(f"  {gid:>10}  {pct:>3.0f}%  med_uses={med_uses:>4}  {aura_names.get(gid, '?')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
