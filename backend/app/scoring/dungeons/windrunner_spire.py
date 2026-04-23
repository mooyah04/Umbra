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
    critical_interrupts=(
        (1216135, "Spirit Bolt"),
        (472724, "Shadow Bolt"),
        (473794, "Poison Blades"),
        (468659, "Throw Axe"),
        (1216592, "Chain Lightning"),
        (473657, "Shadow Bolt"),
        (1216819, "Fungal Bolt"),
        (1216419, "Shoot"),
        (1251981, "Chain Lightning"),
        (473663, "Pulsing Shriek"),
    ),
    dispellable_debuffs=(
        # Re-sampled 2026-04-23 with defensive-only filter. Dropped
        # Ephemeral Bloodlust (enrage on enemies, offensive purge) and
        # Bolstering Flames (enemy buff). Throw Axe / Puncturing Bite
        # stay — they apply dispellable physical/magic debuffs to the
        # party.
        (1216298, "Soul Torment"),
        (1216825, "Poison Spray"),
        (1253834, "Curse of Darkness"),
        (468659, "Throw Axe"),
        (1216985, "Puncturing Bite"),
    ),
    # Sampler 2026-04-23: 163 dispels across 5 logs ≈ 33/run.
    expected_defensive_dispels_per_run=32.6,
    appearances=("Midnight S1",),
    last_reviewed="2026-04-23",
    verified=True,
)
