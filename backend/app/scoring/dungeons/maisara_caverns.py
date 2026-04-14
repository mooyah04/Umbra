"""Maisara Caverns (Midnight expansion).

Appearances: Midnight S1 (debut).

TODO: Populate avoidable_abilities. New Midnight content — must be sourced
from live logs once the season has sufficient +10 data on WCL.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=12874,  # TODO: verify — carried over from earlier draft, not confirmed
    name="Maisara Caverns",
    avoidable_abilities=(),
    appearances=("Midnight S1",),
    last_reviewed=None,
    verified=False,
)
