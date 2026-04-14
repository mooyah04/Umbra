"""The Seat of the Triumvirate (Legion).

Appearances: Legion launch, Midnight S1.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=361753,
    name="The Seat of the Triumvirate",
    avoidable_abilities=(
        (244598, "Void Diffusion"),
        (246026, "Collapsing Void"),
        (244579, "Hungering Vortex"),
        (248133, "Felblaze Rush"),
    ),
    appearances=("Midnight S1", "Legion"),
    last_reviewed="2026-04-14",
    verified=True,
)
