"""Nexus-Point Xenas (Midnight expansion).

Appearances: Midnight S1 (debut).

TODO: Populate avoidable_abilities from WCL damage-taken data.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=12915,  # TODO: verify — carried over from earlier draft, not confirmed
    name="Nexus-Point Xenas",
    avoidable_abilities=(),
    appearances=("Midnight S1",),
    last_reviewed=None,
    verified=False,
)
