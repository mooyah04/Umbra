"""Nexus-Point Xenas (Midnight expansion).

Appearances: Midnight S1 (debut).

Avoidable abilities sourced 2026-04-16 from cross-log sampler (19 top +10 logs,
events API + masterData NPC/Boss source filter).
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=12915,
    name="Nexus-Point Xenas",
    avoidable_abilities=(
        (1271433, "Lightscar Flare"),
        (1252406, "Dreadbellow"),
        (1249818, "Arcane Zap"),
        (1250553, "Arcane Zap"),
        (1255503, "Brilliant Dispersion"),
        (1252429, "Nullwark Blast"),
        (1257745, "Searing Rend"),
        (1252875, "Eclipsing Step"),
        (1249806, "Arcing Mana"),
        (1255335, "Searing Rend"),
        (1281657, "Blistering Smite"),
        (1248007, "Umbral Lash"),
        (1257613, "Divine Guile"),
        (1280168, "Dark Beckoning"),
        (1282915, "Reflux Charge"),
        (1255208, "Searing Rend"),
        (1277557, "Burning Radiance"),
        (1282950, "Suppression Field"),
    ),
    appearances=("Midnight S1",),
    last_reviewed="2026-04-16",
    verified=True,
)
