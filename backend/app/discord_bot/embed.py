"""Response formatting for the /umbra slash command.

Builds a Discord embed from the backend's PlayerProfileResponse payload.
Pure functions — no network, no state — so the command handler stays thin.
"""
from __future__ import annotations

from typing import Any

import discord

# WoW item-quality colors, matching the site's grade palette.
GRADE_COLORS: dict[str, int] = {
    "S": 0xFF8000,  # orange (legendary)
    "A": 0xA335EE,  # purple (epic)
    "B": 0x0070DD,  # blue (rare)
    "C": 0x1EFF00,  # green (uncommon)
    "D": 0xFFFFFF,  # white (common)
    "F": 0x9D9D9D,  # grey (poor)
}
UMBRA_PURPLE = 0x8A2BE2

# Maps backend category keys to human labels. Keys Umbra emits per role
# overlap enough that a single mapping covers everyone.
CATEGORY_LABELS: dict[str, str] = {
    "damage_output": "Damage Output",
    "healing_throughput": "Healing",
    "utility": "Utility",
    "survivability": "Survivability",
    "cooldown_usage": "Cooldown Usage",
    "casts_per_minute": "Casts/Min",
}


def _grade_color(grade: str | None) -> int:
    if not grade:
        return UMBRA_PURPLE
    letter = grade[0].upper()
    return GRADE_COLORS.get(letter, UMBRA_PURPLE)


def _profile_url(region: str, realm: str, name: str) -> str:
    return f"https://wowumbra.gg/player/{region.lower()}/{realm}/{name}"


def _pick_primary_score(scores: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the RoleScore for the player's primary role.

    Backend sets `primary_role: True` on exactly one entry when the player
    has enough runs to grade. Falls back to the first score if the flag is
    missing (older cached responses).
    """
    if not scores:
        return None
    for s in scores:
        if s.get("primary_role"):
            return s
    return scores[0]


def _recent_spec_for_role(recent_runs: list[dict[str, Any]], role: str) -> str | None:
    """Most-recent spec the player ran in the given role, or None."""
    for run in recent_runs:
        if run.get("role") == role and run.get("spec_name"):
            return run["spec_name"]
    return None


def not_indexed_message(region: str, realm: str, name: str) -> str:
    """Text reply for characters the backend has never ingested.

    Intentionally static — the bot never triggers WCL calls; the user must
    run the claim/parse flow on the website, where the per-IP cold-parse
    cooldown still applies to their real IP.
    """
    url = _profile_url(region, realm, name)
    return (
        f"**{name}-{realm}** ({region.upper()}) isn't indexed yet.\n"
        f"Claim with a Warcraft Logs URL at {url}"
    )


def still_indexing_message(region: str, realm: str, name: str) -> str:
    url = _profile_url(region, realm, name)
    return (
        f"**{name}-{realm}** ({region.upper()}) is still processing.\n"
        f"Try again in a minute, or watch progress at {url}"
    )


def ungraded_message(region: str, realm: str, name: str, total_runs: int) -> str:
    url = _profile_url(region, realm, name)
    return (
        f"**{name}-{realm}** ({region.upper()}) has {total_runs} run"
        f"{'s' if total_runs != 1 else ''} on record, "
        f"not enough to grade yet.\nFull profile: {url}"
    )


def build_profile_embed(
    region: str,
    realm: str,
    name: str,
    payload: dict[str, Any],
) -> discord.Embed:
    """Build the rich embed for a graded player."""
    primary = _pick_primary_score(payload.get("scores") or [])
    if primary is None:
        raise ValueError("build_profile_embed requires a graded player payload")

    grade = primary.get("grade") or "Unrated"
    role = (primary.get("role") or "").upper()
    runs_analyzed = int(primary.get("runs_analyzed") or 0)
    total_runs = int(payload.get("total_runs") or 0)
    timed_pct = float(payload.get("timed_pct") or 0.0)

    spec = _recent_spec_for_role(
        payload.get("recent_runs") or [], primary.get("role") or ""
    )
    subtitle_parts = [p for p in (spec, role) if p]
    subtitle = " · ".join(subtitle_parts) if subtitle_parts else "—"

    embed = discord.Embed(
        title=f"{name} · {realm} ({region.upper()})",
        url=_profile_url(region, realm, name),
        description=f"**Grade: {grade}** · {subtitle}",
        color=_grade_color(grade),
    )

    if thumb := payload.get("avatar_url"):
        embed.set_thumbnail(url=thumb)

    # Meta line as the first field — give it full width.
    embed.add_field(
        name="Runs",
        value=(
            f"{runs_analyzed} scored"
            f"{f' · {total_runs} total' if total_runs != runs_analyzed else ''}"
            f" · {timed_pct:.0f}% timed"
        ),
        inline=False,
    )

    # Category breakdown — one field per category, 3 per row via inline=True.
    categories = primary.get("category_scores") or {}
    for key, label in CATEGORY_LABELS.items():
        if key not in categories:
            continue
        score = categories[key]
        if score is None:
            continue
        embed.add_field(name=label, value=f"{float(score):.0f} / 100", inline=True)

    embed.set_footer(text="wowumbra.gg · /umbra")
    return embed
