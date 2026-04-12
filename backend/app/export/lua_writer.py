"""Generates UmbraData.lua from the player_scores table."""

from sqlalchemy import Integer, select, func
from sqlalchemy.orm import Session, selectinload

from app.models import DungeonRun, Player, PlayerScore, Role


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


def _build_player_entry(player: Player, score: PlayerScore, timed_pct: int, spec_name: str) -> str:
    """Build a single Lua table entry for a player."""
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
    lines.append("    },")
    return "\n".join(lines)


def _get_timed_percentages(session: Session, player_ids: list[int]) -> dict[int, int]:
    """Calculate timed key percentage per player from their dungeon runs."""
    if not player_ids:
        return {}

    stmt = (
        select(
            DungeonRun.player_id,
            func.count().label("total"),
            func.sum(DungeonRun.timed.cast(Integer)).label("timed"),
        )
        .where(DungeonRun.player_id.in_(player_ids))
        .group_by(DungeonRun.player_id)
    )
    result = session.execute(stmt)

    pct_map = {}
    for row in result:
        total = row.total or 0
        timed = row.timed or 0
        pct_map[row.player_id] = int(round((timed / total) * 100)) if total > 0 else 0

    return pct_map


def _get_primary_specs(session: Session, player_ids: list[int]) -> dict[int, str]:
    """Get the most-used spec name per player from their most recent runs."""
    if not player_ids:
        return {}

    # Get the most recent run's spec for each player
    spec_map = {}
    for pid in player_ids:
        stmt = (
            select(DungeonRun.spec_name)
            .where(DungeonRun.player_id == pid)
            .order_by(DungeonRun.logged_at.desc())
            .limit(1)
        )
        result = session.execute(stmt).scalar_one_or_none()
        spec_map[pid] = result or "Unknown"

    return spec_map


def generate_lua(session: Session, region: str | None = None) -> str:
    """Generate UmbraData.lua content, optionally filtered by region."""
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

    # Get timed percentages and spec names for all players
    player_ids = [s.player_id for s in scores]
    timed_pcts = _get_timed_percentages(session, player_ids)
    spec_names = _get_primary_specs(session, player_ids)

    entries = []
    for score in scores:
        timed_pct = timed_pcts.get(score.player_id, 0)
        spec_name = spec_names.get(score.player_id, "Unknown")
        entries.append(_build_player_entry(score.player, score, timed_pct, spec_name))

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
