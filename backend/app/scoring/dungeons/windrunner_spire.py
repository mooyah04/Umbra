"""Windrunner Spire (Midnight expansion).

Appearances: Midnight S1 (debut).

TODO: Populate avoidable_abilities from WCL damage-taken data.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=0,  # TODO: confirm WCL encounter_id for Windrunner Spire
    name="Windrunner Spire",
    avoidable_abilities=(),
    appearances=("Midnight S1",),
    last_reviewed=None,
    verified=False,
)
