"""Generates UmbraData.lua from the player_scores table."""

import threading
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import DungeonRun, Player, PlayerScore, Role


# ── Export cache ────────────────────────────────────────────────────────────
# Generating the Lua is expensive (re-scores every player's runs per dungeon
# in memory — seconds for the full table). The output only changes when the
# player_scores table changes, and grading is on-demand, so between grades the
# same content is regenerated on every hit (hourly refresh workflow + any user
# downloads). We cache the rendered string per region, keyed on a cheap data
# signature: (row count, max id) over player_scores. Re-grading deletes and
# re-inserts score rows (see ingest.py), so max(id) strictly advances on any
# change — inserts, deletes, and re-grades all bust the cache; nothing else
# does. One aggregate query (~ms) gates a multi-second regeneration.
_lua_cache: dict[str | None, tuple[tuple[int, int], str]] = {}
_lua_cache_lock = threading.Lock()


def _data_signature(session: Session) -> tuple[int, int]:
    """Cheap fingerprint of player_scores state. Changes iff the export
    would change. max(id) is NULL on an empty table → normalize to 0."""
    count, max_id = session.execute(
        select(func.count(PlayerScore.id), func.max(PlayerScore.id))
    ).one()
    return (count or 0, max_id or 0)


def clear_lua_cache() -> None:
    """Drop all cached export content. Used by tests for isolation; safe to
    call in prod (next request just regenerates)."""
    with _lua_cache_lock:
        _lua_cache.clear()


# Role-specific fields to export in the Lua table
ROLE_EXPORT_FIELDS: dict[Role, list[str]] = {
    Role.dps: ["damage_output", "damage_output_ilvl", "utility", "survivability", "cooldown_usage", "casts_per_minute"],
    Role.healer: ["healing_throughput", "damage_output", "damage_output_ilvl", "utility", "survivability", "cooldown_usage", "casts_per_minute"],
    Role.tank: ["damage_output", "damage_output_ilvl", "utility", "survivability", "cooldown_usage", "casts_per_minute"],
}

# Friendly Lua key names for each category
LUA_KEY_NAMES: dict[str, str] = {
    "damage_output": "dps_perf",
    "damage_output_ilvl": "dps_ilvl",
    "healing_throughput": "throughput",
    "utility": "utility",
    "survivability": "survivability",
    "cooldown_usage": "cd_usage",
    "casts_per_minute": "cpm",
}


def _escape_lua_string(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _build_player_entry(
    player: Player,
    score: PlayerScore,
    timed_pct: int,
    spec_name: str,
    per_dungeon: list[dict],
) -> str:
    """Build a single Lua table entry for a player.

    per_dungeon: list of {encounter_id, name, grade, runs, best_timed}
    dicts, one per dungeon the player has runs in under their primary
    role. Empty list for players with no ingested runs yet. Rendered
    as a nested Lua table the addon iterates for the tooltip's
    per-dungeon section.
    """
    key = f"{player.name}-{player.realm}"
    lines = [f'    ["{_escape_lua_string(key)}"] = {{']
    lines.append(f'        role = "{score.role.value}",')
    lines.append(f'        spec = "{_escape_lua_string(spec_name)}",')
    lines.append(f'        grade = "{score.overall_grade}",')

    # Export role-specific category scores
    fields = ROLE_EXPORT_FIELDS.get(score.role, [])
    for field in fields:
        lua_key = LUA_KEY_NAMES.get(field, field)
        value = score.category_scores.get(field, 0)
        lines.append(f"        {lua_key} = {int(round(value))},")

    lines.append(f"        timed_pct = {timed_pct},")
    lines.append(f"        runs = {score.runs_analyzed},")

    # Per-dungeon breakdown. Keyed by encounter_id so the addon can
    # look up the specific dungeon a player is applying to in the LFG
    # viewer (future enhancement) and also rank-sort to show "best /
    # weak" in the world tooltip today. Omitted entirely when the
    # player has no runs — keeps the file small for stub rows.
    if per_dungeon:
        lines.append("        dungeons = {")
        for d in per_dungeon:
            bt = d["best_timed"] if d["best_timed"] is not None else "nil"
            lines.append(
                f'            [{d["encounter_id"]}] = {{ '
                f'name = "{_escape_lua_string(d["name"])}", '
                f'grade = "{d["grade"]}", '
                f'runs = {d["runs"]}, '
                f'best_timed = {bt} }},'
            )
        lines.append("        },")

    lines.append("    },")
    return "\n".join(lines)


def _load_runs_by_player(
    session: Session, player_ids: list[int],
) -> dict[int, list[DungeonRun]]:
    """Load every dungeon run for the given players in a single query and
    group them by player_id in memory.

    This is the spine of the Lua export's performance: the three derived
    values (timed %, primary spec, per-dungeon breakdown) are all pure
    functions of a player's runs, so we fetch the runs ONCE here and pass
    the grouped result to each helper. Previously each helper queried per
    player — O(n_players) round-trips that dominated wall-clock on a
    remote Postgres (≈1.2k queries / 16s for the full export). Now it's
    one round-trip regardless of player count.
    """
    if not player_ids:
        return {}

    runs = session.execute(
        select(DungeonRun).where(DungeonRun.player_id.in_(player_ids))
    ).scalars().all()

    by_player: dict[int, list[DungeonRun]] = defaultdict(list)
    for r in runs:
        by_player[r.player_id].append(r)
    return by_player


def _get_timed_percentages(
    runs_by_player: dict[int, list[DungeonRun]],
) -> dict[int, int]:
    """Calculate timed key percentage per player from their dungeon runs."""
    pct_map = {}
    for pid, runs in runs_by_player.items():
        total = len(runs)
        timed = sum(1 for r in runs if r.timed)
        pct_map[pid] = int(round((timed / total) * 100)) if total > 0 else 0
    return pct_map


def _get_primary_specs(
    runs_by_player: dict[int, list[DungeonRun]],
) -> dict[int, str]:
    """Get the spec name from each player's most recent run."""
    spec_map = {}
    for pid, runs in runs_by_player.items():
        if not runs:
            spec_map[pid] = "Unknown"
            continue
        latest = max(runs, key=lambda r: r.logged_at)
        spec_map[pid] = latest.spec_name or "Unknown"
    return spec_map


def _get_per_dungeon(
    runs_by_player: dict[int, list[DungeonRun]],
    player_scores: list[PlayerScore],
) -> dict[int, list[dict]]:
    """Compute per-dungeon grade/runs/best-timed for each player (keyed
    by player_id). Only the player's primary-role runs are scored —
    matches the lua export's single-entry-per-player shape.

    Output per player: list of dicts sorted by grade desc (best first)
    so the addon can render "best N / weakest 1" by slicing.
    Each dict: {encounter_id, name, grade, runs, best_timed}.
    """
    from app.scoring.dungeons.registry import _DUNGEONS
    from app.scoring.engine import score_player_runs

    if not player_scores:
        return {}

    # Runs are already loaded and grouped by player. We score per
    # (player, role, encounter) entirely in memory — filter the
    # player's runs to their primary role, bucket by encounter, and
    # score each bucket. O(n_players * avg_enc) scoring calls, zero
    # additional DB round-trips.
    out: dict[int, list[dict]] = {}

    for ps in player_scores:
        player_id = ps.player_id
        player_runs = [
            r for r in runs_by_player.get(player_id, []) if r.role == ps.role
        ]
        if not player_runs:
            out[player_id] = []
            continue

        by_enc: dict[int, list[DungeonRun]] = defaultdict(list)
        for r in player_runs:
            by_enc[r.encounter_id].append(r)

        entries: list[dict] = []
        class_id = ps.player.class_id
        for enc_id, runs_here in by_enc.items():
            dungeon_meta = _DUNGEONS.get(enc_id)
            if dungeon_meta is None:
                # Out-of-season dungeon — skip rather than surface a
                # "Dungeon 12345" entry the addon can't render cleanly.
                continue
            result = score_player_runs(
                runs=runs_here, role=ps.role, class_id=class_id,
            )
            timed_levels = [r.keystone_level for r in runs_here if r.timed]
            entries.append({
                "encounter_id": enc_id,
                "name": dungeon_meta.name,
                "grade": result.overall_grade,
                # User-facing "runs at this dungeon" count: report the
                # raw total, not result.runs_analyzed. Phase 2 run
                # selection (engine.py) collapses the scoring set to
                # one best run per dungeon; result.runs_analyzed
                # reflects that scoring choice, but the addon tooltip
                # wants "you've run this dungeon 5 times" — the raw
                # tally.
                "runs": len(runs_here),
                "best_timed": max(timed_levels) if timed_levels else None,
                # keep composite around internally for sort ordering;
                # stripped before rendering.
                "_composite": result.composite_score,
            })

        # Sort best → worst by composite so addon can take top-N / bottom-1.
        entries.sort(key=lambda e: -e["_composite"])
        for e in entries:
            e.pop("_composite", None)
        out[player_id] = entries

    return out


def generate_lua(session: Session, region: str | None = None) -> str:
    """Generate UmbraData.lua content, optionally filtered by region.

    Cached per region on the player_scores data signature — see the
    cache notes at the top of this module. A signature change in any
    region busts every region's entry (the fingerprint is table-global),
    which is correct if slightly conservative.
    """
    sig = _data_signature(session)
    cached = _lua_cache.get(region)
    if cached is not None and cached[0] == sig:
        return cached[1]

    content = _generate_lua_uncached(session, region)
    with _lua_cache_lock:
        _lua_cache[region] = (sig, content)
    return content


def _generate_lua_uncached(session: Session, region: str | None = None) -> str:
    """Render UmbraData.lua content from scratch (no caching)."""
    stmt = (
        select(PlayerScore)
        .where(PlayerScore.primary_role.is_(True))
        .options(selectinload(PlayerScore.player))
    )
    result = session.execute(stmt)
    scores = result.scalars().all()

    # Filter by region if specified
    if region:
        scores = [s for s in scores if s.player.region.upper() == region.upper()]

    # Load all runs for these players in one query, then derive timed
    # percentages, primary specs, and per-dungeon breakdowns from that
    # single in-memory dataset.
    player_ids = [s.player_id for s in scores]
    runs_by_player = _load_runs_by_player(session, player_ids)
    timed_pcts = _get_timed_percentages(runs_by_player)
    spec_names = _get_primary_specs(runs_by_player)
    per_dungeon = _get_per_dungeon(runs_by_player, scores)

    entries = []
    for score in scores:
        timed_pct = timed_pcts.get(score.player_id, 0)
        spec_name = spec_names.get(score.player_id, "Unknown")
        entries.append(_build_player_entry(
            score.player, score, timed_pct, spec_name,
            per_dungeon.get(score.player_id, []),
        ))

    body = "\n".join(entries) if entries else "    -- No data yet"

    return f"Umbra_Database = {{\n{body}\n}}\n"


def export_lua_file(session: Session, output_path: str, region: str | None = None) -> int:
    """Write UmbraData.lua to disk. Returns the number of players exported."""
    content = generate_lua(session, region)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    count = content.count('grade = "')
    return count


def export_all_regions(session: Session, output_dir: str) -> dict[str, int]:
    """Export separate Lua files per region. Returns {region: player_count}."""
    import os

    # Get all unique regions
    stmt = select(Player.region).distinct()
    regions = [r[0] for r in session.execute(stmt)]

    results = {}
    for region in regions:
        filename = f"UmbraData_{region.upper()}.lua"
        filepath = os.path.join(output_dir, filename)
        count = export_lua_file(session, filepath, region)
        results[region.upper()] = count

    return results
