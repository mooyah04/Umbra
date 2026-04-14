"""Avoidable damage lookup — thin wrapper over the dungeon registry.

The data itself lives in `app.scoring.dungeons.*` (one module per dungeon,
archived across seasons). This module exists only for backwards-compatible
imports; new code should import from `app.scoring.dungeons` directly.
"""
from app.scoring.dungeons.registry import (
    get_avoidable_abilities,
    get_all_avoidable_ability_ids,
    UNIVERSAL_AVOIDABLE,
)

__all__ = [
    "get_avoidable_abilities",
    "get_all_avoidable_ability_ids",
    "UNIVERSAL_AVOIDABLE",
]
