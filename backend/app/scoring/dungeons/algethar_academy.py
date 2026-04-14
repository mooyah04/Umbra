"""Algeth'ar Academy (Dragonflight).

Appearances: DF S1, Midnight S1.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=112526,
    name="Algeth'ar Academy",
    avoidable_abilities=(
        (388862, "Astral Whirlwind"),
        (388537, "Mana Void"),
        (388954, "Arcane Fissure"),
    ),
    appearances=("Midnight S1", "Dragonflight S1"),
    last_reviewed="2026-04-14",
    verified=True,
)
