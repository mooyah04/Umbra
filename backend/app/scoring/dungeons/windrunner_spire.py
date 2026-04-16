"""Windrunner Spire (Midnight expansion).

Appearances: Midnight S1 (debut).

Encounter ID 12805 confirmed 2026-04-16 from report 78AxZ4RH3FrPCB2b.
Avoidable abilities sourced same day from cross-log sampler (18 top +10
logs, events API + masterData NPC/Boss source filter).
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=12805,
    name="Windrunner Spire",
    avoidable_abilities=(
        (467621, "Rampage"),
        (1283371, "Squall Leap"),
        (1282272, "Splattered"),
        (468659, "Throw Axe"),
        (472054, "Reckless Leap"),
        (1216298, "Soul Torment"),
        (466091, "Searing Beak"),
        (1216963, "Spore Dispersal"),
        (466559, "Flaming Updraft"),
        (472758, "Splattering Spew"),
        (1216253, "Arcane Salvo"),
        (473668, "Pulsing Shriek"),
        (473868, "Shadowrive"),
        (1216042, "Squall Leap"),
        (1253978, "Gust Shot"),
        (1219491, "Debilitating Shriek"),
        (1270618, "Flame Nova"),
        (473786, "Fetid Spew"),
        (1216825, "Poison Spray"),
    ),
    appearances=("Midnight S1",),
    last_reviewed="2026-04-16",
    verified=True,
)
