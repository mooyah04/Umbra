"""Per-dungeon data (avoidable abilities, encounter IDs, etc.).

Each dungeon lives in its own module so data persists across seasons.
When Blizzard rotates a legacy dungeon back into M+, its writeup is
already archived here — review and update rather than rewrite.

The active season pool is declared in `seasons.py`. The `registry.py`
module aggregates all dungeon modules into lookup helpers used by scoring.
"""

from app.scoring.dungeons.registry import (
    get_avoidable_abilities,
    get_all_avoidable_ability_ids,
    get_dungeon,
    active_encounter_ids,
)

__all__ = [
    "get_avoidable_abilities",
    "get_all_avoidable_ability_ids",
    "get_dungeon",
    "active_encounter_ids",
]
