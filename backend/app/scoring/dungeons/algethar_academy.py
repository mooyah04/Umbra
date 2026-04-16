"""Algeth'ar Academy (Dragonflight).

Appearances: DF S1, Midnight S1.

Avoidable abilities re-sourced 2026-04-16 from cross-log sampler (19 top +10 logs).
Some DF-era IDs (389011, 388537, 388940, 386181, 388923) still appear in Midnight S1
data and are retained; others replaced with current-season IDs.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=112526,
    name="Algeth'ar Academy",
    avoidable_abilities=(
        (377009, "Deafening Screech"),
        (396716, "Splinterbark"),
        (1282244, "Vile Bite"),
        (1270098, "Spellbound Weapon"),
        (389011, "Overwhelming Power"),
        (376997, "Savage Peck"),
        (389055, "Vicious Lunge"),
        (1270356, "Arcane Smash"),
        (386181, "Mana Bomb"),
        (1285509, "Blistering Fire"),
        (1282252, "Astral Blast"),
        (385958, "Arcane Expulsion"),
        (1276632, "Raging Screech"),
        (388940, "Vicious Ambush"),
        (388537, "Arcane Fissure"),
        (388544, "Barkbreaker"),
        (388923, "Burst Forth"),
        (390944, "Darting Sting"),
        (385981, "Arcane Orb"),
        (373326, "Arcane Missiles"),
    ),
    appearances=("Midnight S1", "Dragonflight S1"),
    last_reviewed="2026-04-16",
    verified=True,
)
