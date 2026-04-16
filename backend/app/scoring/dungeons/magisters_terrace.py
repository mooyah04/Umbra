"""Magister's Terrace (Burning Crusade).

Appearances: TBC Heroic, Midnight S1.

Avoidable abilities sourced 2026-04-16 from cross-log sampler (15 top +10 logs,
events API + masterData NPC/Boss source filter).
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=12811,
    name="Magister's Terrace",
    avoidable_abilities=(
        (1244907, "Runic Glaive"),
        (1215897, "Devouring Entropy"),
        (1254338, "Ignition"),
        (1227020, "Dimensional Shred"),
        (1246446, "Null Reaction"),
        (1284958, "Cosmic Sting"),
        (1224299, "Astral Grasp"),
        (1217087, "Consuming Shadows"),
        (1214081, "Arcane Expulsion"),
        (1252910, "Arcane Blade"),
        (1254595, "Energy Release"),
        (1271066, "Entropy Blast"),
        (1264951, "Void Eruption"),
        (1255187, "Holy Fire"),
        (1244985, "Arcane Volley"),
        (1243905, "Unstable Energy"),
        (1215157, "Unstable Void Essence"),
        (1280119, "Hulking Fragment"),
        (1284633, "Stygian Ichor"),
        (1282051, "Arcane Beam"),
    ),
    appearances=("Midnight S1", "TBC Heroic"),
    last_reviewed="2026-04-16",
    verified=True,
)
