"""Sample dispellable debuffs for every active-season dungeon.

One-off tooling to populate `DungeonData.dispellable_debuffs` across
every dungeon module in one pass. Hits the backend's admin sampler
endpoint (/api/admin/sample-dungeon-dispels) for each active encounter,
prints a summary per dungeon, and emits a ready-to-paste tuple literal
for each module.

Runs against a deployed backend — the sampler endpoint itself queries
WCL, which needs the server's WCL credentials. Running locally against
a dev backend works if WCL creds are in that env; running against prod
is the usual path.

Usage:
    # Production
    API_URL=https://api.wowumbra.gg \\
    ADMIN_API_KEY=<key> \\
    python -m scripts.sample_dispels

    # Local dev backend
    API_URL=http://localhost:8000 ADMIN_API_KEY=<key> \\
    python -m scripts.sample_dispels

    # Tweak consensus threshold or sample count
    CONSENSUS_PCT=40 TOP_N=15 python -m scripts.sample_dispels

Output: per-dungeon summary + a copy-paste block at the end with the
tuple-literal for each module's `dispellable_debuffs=` field.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

from app.scoring.dungeons.seasons import ACTIVE_SEASON
from app.scoring.dungeons.registry import _load_active_dungeons


API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")
TOP_N = int(os.environ.get("TOP_N", "10"))
CONSENSUS_PCT = float(os.environ.get("CONSENSUS_PCT", "30"))


def fetch_sample(encounter_id: int) -> dict:
    url = (
        f"{API_URL}/api/admin/sample-dungeon-dispels"
        f"?encounter_id={encounter_id}&top_n={TOP_N}&consensus_pct={CONSENSUS_PCT}"
    )
    req = urllib.request.Request(
        url,
        headers={
            "X-API-Key": ADMIN_API_KEY or "",
            # Cloudflare's browser-integrity-check rejects the default
            # `Python-urllib/3.x` UA with code 1010. Any non-default
            # UA passes, so just identify ourselves.
            "User-Agent": "umbra-admin-cli/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode(errors='replace')}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection error: {e.reason}"}


def format_tuple_literal(debuffs: list[dict]) -> str:
    """Emit a Python tuple literal suitable for pasting into a module.

    Empty tuple has explicit () so the scoring layer can distinguish
    "sampled and confirmed empty" from "not yet sampled" (None).
    """
    if not debuffs:
        return "()  # sampled 2026-04-23, no consistently-dispelled debuffs"
    lines = ["("]
    for d in debuffs:
        # Drop any stray quotes/backslashes in names so the output is
        # always valid Python without escaping.
        safe_name = (d["name"] or "?").replace('"', "'")
        lines.append(f'    ({d["guid"]}, "{safe_name}"),  # seen in {d["logs_pct"]}% of logs, {d["total_dispels"]} total')
    lines.append(")")
    return "\n".join(lines)


def main() -> int:
    if not ADMIN_API_KEY:
        print("ERROR: ADMIN_API_KEY env var is required.", file=sys.stderr)
        return 2

    resolved, _unresolved = _load_active_dungeons()
    # Stable ordering: match seasons.py dungeon_modules for readable output.
    module_name_to_encounter = {
        _module_name_from_dungeon(d): eid for eid, d in resolved.items()
    }

    print(f"Sampling {len(resolved)} active dungeons")
    print(f"  API:  {API_URL}")
    print(f"  top_n={TOP_N}, consensus_pct={CONSENSUS_PCT}%\n")

    # {module_name: (encounter_id, tuple_literal_string)}
    paste_blocks: dict[str, tuple[int, str]] = {}

    for module_name in ACTIVE_SEASON.dungeon_modules:
        eid = module_name_to_encounter.get(module_name)
        if eid is None:
            print(f"[SKIP] {module_name}: encounter_id unresolved on the module")
            continue
        print(f"[...] {module_name} (encounter_id={eid})")
        result = fetch_sample(eid)
        if "error" in result:
            print(f"      {result['error']}")
            continue
        n = result.get("debuffs_passing_threshold", 0)
        sampled = result.get("logs_sampled", 0)
        print(
            f"      sampled {sampled} logs; "
            f"{n} debuffs >= {CONSENSUS_PCT}% consensus"
        )
        for d in result.get("debuffs", []):
            print(
                f"        {d['guid']:>8}  {d['name']:<40}  "
                f"{d['logs_pct']:>5}% of logs  ({d['total_dispels']} dispels)"
            )
        paste_blocks[module_name] = (
            eid, format_tuple_literal(result.get("debuffs", [])),
        )
        # Polite pacing so we don't hammer WCL through the endpoint if
        # the rate limiter is active.
        time.sleep(1)

    print("\n" + "=" * 72)
    print("COPY-PASTE BLOCK (one per dungeon module)")
    print("=" * 72 + "\n")
    for module_name, (eid, literal) in paste_blocks.items():
        print(f"# backend/app/scoring/dungeons/{module_name}.py  (encounter_id={eid})")
        print(f"dispellable_debuffs={literal},\n")

    return 0


def _module_name_from_dungeon(dungeon) -> str:
    """Best-effort reverse lookup: match a DungeonData to its module name
    via the registry. ACTIVE_SEASON.dungeon_modules is the source of
    truth for the list — we just need to pair each resolved DungeonData
    to its module slug. The only thing the registry stores is the
    DungeonData itself, so we re-import each module to find the match.
    """
    import importlib
    for name in ACTIVE_SEASON.dungeon_modules:
        mod = importlib.import_module(f"app.scoring.dungeons.{name}")
        if getattr(mod, "DUNGEON", None) is dungeon:
            return name
    return "<unknown>"


if __name__ == "__main__":
    sys.exit(main())
