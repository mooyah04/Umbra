"""Cold-start player discovery via Blizzard mythic-keystone leaderboards.

Pulls per-realm per-dungeon top-500 leaderboards from Blizzard, extracts
unique (name, realm_slug, region, class_id, spec_name) tuples, and
upserts stub `Player` rows with `last_ingested_at=None`. The existing
WCL sweep picks those stubs up on its next tick and backfills their run
data.

Shared between:
- `/api/admin/discover-players` (dry-run, no DB writes)
- `app.scheduler_leaderboard` (persistent background thread)
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.bnet.client import bnet_client
from app.models import Player
from app.scoring.dungeons.registry import _DUNGEONS
from app.scoring.specializations import resolve_spec

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredPlayer:
    name: str
    realm: str
    region: str
    class_id: int
    spec_name: str


def _norm_dungeon_name(s: str) -> str:
    """Normalize dungeon names so ours match Blizzard's.

    Differences in the wild:
    - Possessive apostrophe position (Magister's vs Magisters')
    - Curly apostrophe U+2019
    - Leading "The " on our side but not Blizzard's (Seat of the Triumvirate)
    """
    s = (s or "").lower().replace("\u2019", "").replace("'", "").strip()
    if s.startswith("the "):
        s = s[4:]
    return " ".join(s.split())


def match_active_dungeons(region: str) -> list[dict]:
    """Name-match our active-season dungeon modules to Blizzard's dungeon
    index entries. Returns a dedup'd list, one entry per (wcl_encounter_id,
    bnet_dungeon_id) pair.

    Blizzard occasionally lists the same dungeon twice (Seat of the
    Triumvirate appears both under Legion and its Midnight rotation),
    so we dedupe by bnet_id while keeping the first-matched wcl entry.
    """
    bnet = bnet_client.get_keystone_dungeon_index(region)
    if not bnet:
        return []
    our = {_norm_dungeon_name(d.name): (eid, d.name) for eid, d in _DUNGEONS.items()}
    seen_bnet_ids: set[int] = set()
    out: list[dict] = []
    for bd in bnet:
        key = _norm_dungeon_name(bd["name"])
        if key not in our:
            continue
        if bd["id"] in seen_bnet_ids:
            continue
        seen_bnet_ids.add(bd["id"])
        wcl_eid, wcl_name = our[key]
        out.append({
            "bnet_id": bd["id"], "bnet_name": bd["name"],
            "wcl_encounter_id": wcl_eid, "wcl_name": wcl_name,
        })
    return out


def discover_from_realm(
    region: str,
    connected_realm_id: int,
    period_id: int,
    dungeons: list[dict],
) -> tuple[list[DiscoveredPlayer], set[int]]:
    """Fetch leaderboards for one realm × all dungeons, extract players.

    Returns (players, unknown_spec_ids). Unknown spec ids are collected
    across calls so the scheduler can log them once per tick rather than
    per-player.
    """
    slugs = bnet_client.get_connected_realm_slugs(region, connected_realm_id)
    primary_slug = slugs[0] if slugs else f"realm-{connected_realm_id}"

    discovered: dict[tuple[str, str, str], DiscoveredPlayer] = {}
    unknown_specs: set[int] = set()

    for d in dungeons:
        board = bnet_client.get_mythic_leaderboard(
            region, connected_realm_id, d["bnet_id"], period_id,
        )
        if not board:
            continue
        for group in board.get("leading_groups") or []:
            for m in group.get("members") or []:
                profile = m.get("profile") or {}
                spec = m.get("specialization") or {}
                name = profile.get("name")
                spec_id = spec.get("id")
                realm_obj = profile.get("realm") or {}
                player_realm_slug = realm_obj.get("slug") or primary_slug
                if not name or not isinstance(spec_id, int):
                    continue
                resolved = resolve_spec(spec_id)
                if not resolved:
                    unknown_specs.add(spec_id)
                    continue
                class_id, spec_name = resolved
                key = (region, player_realm_slug.lower(), name.lower())
                if key in discovered:
                    continue
                discovered[key] = DiscoveredPlayer(
                    name=name,
                    realm=player_realm_slug,
                    region=region,
                    class_id=class_id,
                    spec_name=spec_name,
                )
    return list(discovered.values()), unknown_specs


def upsert_stub_players(
    session: Session, players: Iterable[DiscoveredPlayer]
) -> int:
    """Insert stub Player rows for players we don't know about yet.

    Returns the number of NEW rows inserted. Existing rows (matched case-
    insensitively on name+realm+region) are left untouched — their
    class_id and other fields are owned by the ingest pipeline, not this
    discovery pass.

    The created rows have `last_ingested_at=None`, which puts them at the
    top of the WCL-sweep staleness queue. That pulls them in on the
    sweep's next tick.
    """
    new_count = 0
    for p in players:
        existing = session.execute(
            select(Player.id).where(
                Player.name.ilike(p.name),
                Player.realm.ilike(p.realm),
                Player.region == p.region,
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(Player(
            name=p.name,
            realm=p.realm,
            region=p.region,
            class_id=p.class_id,
            last_ingested_at=None,
        ))
        new_count += 1
    if new_count:
        session.commit()
    return new_count
