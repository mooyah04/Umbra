"""Maisara Caverns (Midnight expansion).

Appearances: Midnight S1 (debut).

Avoidable abilities sourced 2026-04-16 from cross-log sampler (17 top +10 logs,
events API + masterData NPC/Boss source filter).
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=12874,
    name="Maisara Caverns",
    avoidable_abilities=(
        (1264989, "Withering Miasma"),
        (1258482, "Searing Presence"),
        (1259274, "Spectral Strikes"),
        (1246666, "Infected Pinions"),
        (1257920, "Dread Slash"),
        (1248879, "Deathgorged Vessel"),
        (1270085, "Grim Ward"),
        (1251813, "Lingering Dread"),
        (1263735, "Necrotic Convergence"),
        (1262900, "Ritual Drums"),
        (1257088, "Necrotic Wave"),
        (1251567, "Drain Soul"),
        (1253844, "Withering Soul"),
        (1257328, "Sear"),
        (1266485, "Flanking Spear"),
        (1260648, "Barrage"),
        (1256047, "Deafening Roar"),
        (1259631, "Staggering Blow"),
        (1259255, "Spirit Rend"),
        (1259664, "Soulstorms"),
    ),
    critical_interrupts=(
        (1259255, "Spirit Rend"),
        (1256015, "Shadow Bolt"),
        (1263292, "Shrink"),
        (1264327, "Shadowfrost Blast"),
        (1256008, "Hex"),
        (1259182, "Piercing Screech"),
        (1254010, "Eternal Suffering"),
        (1266381, "Hooked Snare"),
        (1250708, "Necrotic Convergence"),
        (1257716, "Reanimation"),
        (1255964, "Throw Spear"),
    ),
    dispellable_debuffs=(
        (1270079, "Grim Ward"),
        (1246666, "Infected Pinions"),
        (1259255, "Spirit Rend"),
        (1262411, "Ritual Firebrand"),
        (1260709, "Vilebranch Sting"),
        (1255765, "Blood Frenzy"),
        (1271623, "Frost Nova"),
        (1266488, "Open Wound"),
        (1259794, "Ritual Sacrifice"),
        (1254175, "Cries of the Fallen"),
        (1259731, "Cries of the Fallen"),
    ),
    appearances=("Midnight S1",),
    last_reviewed="2026-04-23",
    verified=True,
)
