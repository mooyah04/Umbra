"""Skyreach (Warlords of Draenor).

Appearances: WoD launch, Shadowlands S4, Midnight S1.

Avoidable abilities sourced 2026-04-16 from cross-log sampler (14 top +10 logs,
events API + masterData NPC/Boss source filter).
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=61209,
    name="Skyreach",
    avoidable_abilities=(
        (1253543, "Scorching Ray"),
        (1253368, "Burning Pursuit"),
        (153757, "Fan of Blades"),
        (1287905, "Light Ray"),
        (1254475, "Blade Rush"),
        (1254672, "Fiery Talon"),
        (1253510, "Sunbreak"),
        (1254569, "Dire Screech"),
        (1253446, "Solar Flame"),
        (1273358, "Solar Barrier"),
        (1254666, "Ricocheting Chakram"),
        (1253519, "Burning Claws"),
        (154135, "Supernova"),
        (1254679, "Wrathful Wind"),
        (1254332, "Solar Flare"),
        (1252691, "Gale Surge"),
        (1258174, "Dread Wind"),
    ),
    critical_interrupts=(
        (1255377, "Repel"),
        (1254669, "Solar Bolt"),
        (152953, "Blinding Light"),
        (154396, "Solar Blast"),
        (1254686, "Mark of Death"),
    ),
    dispellable_debuffs=(
        (1254678, "Wrathful Wind"),
        (1254475, "Blade Rush"),
        (153757, "Fan of Blades"),
    ),
    appearances=("Midnight S1", "Shadowlands S4", "WoD"),
    last_reviewed="2026-04-23",
    verified=True,
)
