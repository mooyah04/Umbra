"""Pit of Saron (Wrath of the Lich King).

Appearances: WotLK Heroic, Legion Timewalking, Midnight S1.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=10658,
    name="Pit of Saron",
    avoidable_abilities=(
        (69021, "Icy Blast"),
        (69024, "Icy Blast Ground"),
        (68989, "Overlord's Brand"),
        (69012, "Explosive Barrage"),
        (70827, "Ice Shards"),
    ),
    appearances=("Midnight S1", "Legion Timewalking", "WotLK Heroic"),
    last_reviewed="2026-04-14",
    verified=True,
)
