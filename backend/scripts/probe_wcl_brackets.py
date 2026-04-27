"""Probe WCL's encounterRankings bracket options.

Goal: figure out whether WCL exposes a key-level-bracketed DPS percentile
for M+ runs. Ground truth: Elonmunk-TarrenMill, run 4750, Seat of
Triumvirate +6, Brewmaster — currently gets a 5% global rankPercent. We
want to see whether WCL has a "vs other +6 BrM" view available.

Run from backend/: python -m scripts.probe_wcl_brackets
"""

import json
from app.wcl.client import WCLClient

NAME = "Elonmunk"
SERVER_SLUG = "tarren-mill"
SERVER_REGION = "eu"
ENCOUNTER_ID = 361753  # Seat of Triumvirate
REPORT_CODE = "yYmLp2cRADdXh9kj"
FIGHT_ID = 1


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def run_query(client: WCLClient, label: str, query: str, variables: dict) -> dict:
    print(f"\n--- {label} ---")
    try:
        data = client.query(query, variables)
        return data
    except Exception as e:
        print(f"ERROR: {e}")
        return {}


def main():
    client = WCLClient()

    # Probe 1: default encounterRankings (what we already use).
    # See what the rank object actually contains for an M+ fight — does
    # it expose `bracketData` (key level) on each rank?
    section("Probe 1: default encounterRankings, dump rank shape")
    q1 = """
    query($name: String!, $serverSlug: String!, $serverRegion: String!, $eid: Int!) {
      characterData {
        character(name: $name, serverSlug: $serverSlug, serverRegion: $serverRegion) {
          encounterRankings(encounterID: $eid, difficulty: 10, metric: dps)
        }
      }
    }
    """
    d1 = run_query(client, "default", q1, {
        "name": NAME, "serverSlug": SERVER_SLUG, "serverRegion": SERVER_REGION,
        "eid": ENCOUNTER_ID,
    })
    er = (
        d1.get("characterData", {})
        .get("character", {})
        .get("encounterRankings", {})
    )
    print(f"top-level keys: {sorted(er.keys()) if isinstance(er, dict) else type(er)}")
    ranks = er.get("ranks") or []
    print(f"rank count: {len(ranks)}")
    if ranks:
        print("first rank keys:", sorted(ranks[0].keys()))
        print("first rank sample:", json.dumps(ranks[0], indent=2)[:600])
        # Look specifically for our run
        match = next(
            (
                r for r in ranks
                if r.get("report", {}).get("code") == REPORT_CODE
                and r.get("report", {}).get("fightID") == FIGHT_ID
            ),
            None,
        )
        if match:
            print("\nOUR FIGHT MATCH:")
            print(json.dumps(match, indent=2))

    # Probe 2: encounterRankings with byBracket: true
    section("Probe 2: encounterRankings with byBracket: true")
    q2 = """
    query($name: String!, $serverSlug: String!, $serverRegion: String!, $eid: Int!) {
      characterData {
        character(name: $name, serverSlug: $serverSlug, serverRegion: $serverRegion) {
          encounterRankings(encounterID: $eid, difficulty: 10, metric: dps, byBracket: true)
        }
      }
    }
    """
    d2 = run_query(client, "byBracket=true", q2, {
        "name": NAME, "serverSlug": SERVER_SLUG, "serverRegion": SERVER_REGION,
        "eid": ENCOUNTER_ID,
    })
    er2 = (
        d2.get("characterData", {})
        .get("character", {})
        .get("encounterRankings", {})
    )
    print(f"top-level keys: {sorted(er2.keys()) if isinstance(er2, dict) else type(er2)}")
    if isinstance(er2, dict):
        # Print the full structure (truncated) to see what byBracket
        # changes: does it return per-bracket statistics, per-bracket
        # ranks, or a flat list with bracket labels?
        print(json.dumps(er2, indent=2)[:3000])

    # Probe 3: encounterRankings with explicit bracket filter (hypothetical)
    # WCL's schema may support a `bracket` argument that filters to a
    # specific key level. Try it; if the API doesn't know the field,
    # the request will error and we move on.
    section("Probe 3: encounterRankings(bracket: 6) — does the arg exist?")
    q3 = """
    query($name: String!, $serverSlug: String!, $serverRegion: String!, $eid: Int!) {
      characterData {
        character(name: $name, serverSlug: $serverSlug, serverRegion: $serverRegion) {
          encounterRankings(encounterID: $eid, difficulty: 10, metric: dps, bracket: 6)
        }
      }
    }
    """
    d3 = run_query(client, "bracket=6", q3, {
        "name": NAME, "serverSlug": SERVER_SLUG, "serverRegion": SERVER_REGION,
        "eid": ENCOUNTER_ID,
    })
    if d3:
        er3 = (
            d3.get("characterData", {})
            .get("character", {})
            .get("encounterRankings", {})
        )
        print(json.dumps(er3, indent=2)[:1500])

    # Probe 4: schema introspection on encounterRankings args
    section("Probe 4: schema introspection — encounterRankings args")
    q4 = """
    {
      __type(name: "Character") {
        fields(includeDeprecated: false) {
          name
          args {
            name
            type { name kind ofType { name kind } }
          }
        }
      }
    }
    """
    d4 = run_query(client, "introspect Character", q4, {})
    fields = d4.get("__type", {}).get("fields") or []
    er_field = next((f for f in fields if f.get("name") == "encounterRankings"), None)
    if er_field:
        print("encounterRankings args:")
        for arg in er_field.get("args", []):
            t = arg.get("type", {})
            t_name = t.get("name") or (t.get("ofType") or {}).get("name") or t.get("kind")
            print(f"  - {arg.get('name')}: {t_name}")

    # Probe 5: introspect EncounterRankings JSON structure?
    # The return type is likely JSON (opaque). Try a worldData path that
    # sometimes returns more info.
    section("Probe 5: worldData encounter fightRankings filter options")
    q5 = """
    {
      __type(name: "Encounter") {
        fields {
          name
          args { name type { name kind ofType { name kind } } }
        }
      }
    }
    """
    d5 = run_query(client, "introspect Encounter", q5, {})
    e_fields = d5.get("__type", {}).get("fields") or []
    for f in e_fields:
        if f.get("name") in ("characterRankings", "fightRankings", "name"):
            print(f"\n{f.get('name')}:")
            for arg in f.get("args", []):
                t = arg.get("type", {})
                t_name = t.get("name") or (t.get("ofType") or {}).get("name") or t.get("kind")
                print(f"  - {arg.get('name')}: {t_name}")


if __name__ == "__main__":
    main()
