"""The Seat of the Triumvirate (Legion).

Appearances: Legion launch, Midnight S1.

Avoidable abilities re-sourced 2026-04-16 from cross-log sampler (17 top +10 logs).
Prior Legion-era IDs (244598 Void Diffusion et al.) did not appear in Midnight S1
damage-taken data — replaced wholesale with current-season spell IDs.
"""
from app.scoring.dungeons._types import DungeonData

DUNGEON = DungeonData(
    encounter_id=361753,
    name="The Seat of the Triumvirate",
    avoidable_abilities=(
        (1265424, "Dirge of Despair"),
        (1264569, "Void Expulsion"),
        (1265030, "Void Storm"),
        (1268733, "Mind Flay"),
        (1263523, "Overload"),
        (1277343, "Chains of Subjugation"),
        (1263399, "Oozing Slam"),
        (245742, "Shadow Pounce"),
        (1262519, "Backstab"),
        (1263542, "Mass Void Infusion"),
        (1264678, "Devouring Frenzy"),
        (1264512, "Rift Tear"),
        (1263508, "Umbral Nova"),
        (249082, "Unstable Entrance"),
        (1263297, "Crashing Void"),
        (1269469, "Rupture"),
        (1262441, "Eruption"),
        (1280326, "Void Bash"),
        (1264257, "Umbral Waves"),
    ),
    critical_interrupts=(
        (1262510, "Umbral Bolt"),
        (244750, "Mind Blast"),
        (1262526, "Abyssal Enhancement"),
        (248831, "Dread Screech"),
        (1277340, "Shadowmend"),
        (1262523, "Summon Voidcaller"),
    ),
    dispellable_debuffs=(
        # Re-sampled 2026-04-23 with defensive-only filter. Dropped
        # Battle Rage — enrage on enemies, offensive purge target.
        (1262509, "Chains of Subjugation"),
        (1280330, "Rift Essence"),
        (1262519, "Backstab"),
        (245742, "Shadow Pounce"),
    ),
    appearances=("Midnight S1", "Legion"),
    last_reviewed="2026-04-23",
    verified=True,
)
