"""Pit of Saron (Wrath of the Lich King).

Appearances: WotLK Heroic, Legion Timewalking, Midnight S1.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=10658,
    name="Pit of Saron",
    avoidable_abilities=(
        (1258802, "Dread Pulse"),
        (1263000, "Festering Pulse"),
        (1258464, "Leaping Maul"),
        (1258451, "Charging Slash"),
        (1258433, "Tormenting Blade"),
        (1264336, "Plague Expulsion"),
        (1261847, "Cryostomp"),
        (1258437, "Permeating Cold"),
        (1259202, "Cryoburst"),
        (1262739, "Frost Spit"),
        (1262750, "Rime Blast"),
        (1264299, "Blight"),
        (1258435, "Sunderstrike"),
        (1261546, "Orebreaker"),
    ),
    critical_interrupts=(
        (1258431, "Shadow Bolt"),
        (1258436, "Ice Bolt"),
        (1271479, "Netherburst"),
        (1271074, "Icy Blast"),
        (1262941, "Plague Bolt"),
        (1278893, "Death Bolt"),
        (1264186, "Shadowbind"),
    ),
    dispellable_debuffs=(
        # Re-sampled 2026-04-23 with defensive-only filter. Dropped
        # Plague Frenzy — enrage on enemies, not a healer cleanse.
        (1258434, "Curse of Torment"),
        (1258437, "Permeating Cold"),
        (1264186, "Shadowbind"),
        (1258459, "Rotting Strikes"),
        (1258997, "Plungegrip"),
        (1261921, "Cryoshards"),
        (1262930, "Rotting Strikes"),
    ),
    appearances=("Midnight S1", "Legion Timewalking", "WotLK Heroic"),
    last_reviewed="2026-04-23",
    verified=True,
)
