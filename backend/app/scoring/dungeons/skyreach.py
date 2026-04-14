"""Skyreach (Warlords of Draenor).

Appearances: WoD launch, Shadowlands S4, Midnight S1.

TODO: Populate avoidable_abilities. Source candidates:
- WCL damage-taken breakdowns for +10 Skyreach keys in Midnight S1
- Archon.gg / U.gg dungeon guides
- Wowhead strategy pages for each boss (Ranjit, Araknath, Rukhran, High Sage Viryx)
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=0,  # TODO: confirm WCL encounter_id for Skyreach in Midnight S1
    name="Skyreach",
    avoidable_abilities=(),
    appearances=("Midnight S1", "Shadowlands S4", "WoD"),
    last_reviewed=None,
    verified=False,
)
