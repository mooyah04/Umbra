"""Magister's Terrace (Burning Crusade).

Appearances: TBC Heroic, Midnight S1.

TODO: Populate avoidable_abilities. Bosses: Selin Fireheart, Vexallus,
Priestess Delrissa, Kael'thas Sunstrider.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=0,  # TODO: confirm WCL encounter_id for Magister's Terrace in Midnight S1
    name="Magister's Terrace",
    avoidable_abilities=(),
    appearances=("Midnight S1", "TBC Heroic"),
    last_reviewed=None,
    verified=False,
)
