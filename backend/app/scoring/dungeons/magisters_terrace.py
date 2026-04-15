"""Magister's Terrace (Burning Crusade).

Appearances: TBC Heroic, Midnight S1.

Encounter ID 12811 confirmed from Elonmunk's 2026-04-15 +10 run.

TODO: Populate avoidable_abilities. Bosses: Selin Fireheart, Vexallus,
Priestess Delrissa, Kael'thas Sunstrider. Use
/api/debug/wcl-damage-taken?code=<report>&encounter_id=12811 to sample
damage sources from real logs once we have a few.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=12811,
    name="Magister's Terrace",
    avoidable_abilities=(),
    appearances=("Midnight S1", "TBC Heroic"),
    last_reviewed=None,
    verified=False,
)
