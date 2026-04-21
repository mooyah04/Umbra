"""Fury Warrior rotation data.

Pilot spec for the rotation-classification system. Spell IDs and alias
fragments sourced 2026-04-21 from a 5-log sampler of top Fury Warriors
on Magister's Terrace (see backend/scripts/validate_rotation.py).

Odyn's Fury is a textbook aliasing case: a single button press fires
four distinct combat-log events (385059, 385060, 385061, 385062 — main/
off-hand normal + triggered), each of which WCL returns as a separate
cast. Without the alias map, it dominates the frequency table as four
~2.7% entries when it should be one ~10% entry.

Reference opener is the standard Fury Slayer opener for boss/single-
target pulls — patterned on the Icy Veins guide's opener sequence with
adaptations for current-season talent defaults (Thunder Blast instead
of Thunderous Roar for AoE-heavy Midnight S1 content).
"""
from app.rotation.spec_data import OpenerStep, SpecRotationData


# Canonical spell IDs — the ones the frontend renders after alias merge.
BLOODTHIRST = 23881
RAGING_BLOW = 85288
RAMPAGE = 184367
EXECUTE = 5308
WHIRLWIND = 1680
THUNDER_CLAP = 6343
THUNDER_BLAST = 435222
BLOODBATH = 335096          # Slayer hero-tree proc
ODYNS_FURY = 385059
AVATAR = 107574
RECKLESSNESS = 1719
THUNDEROUS_ROAR = 384318
SPELL_REFLECTION = 23920
PUMMEL = 6552
CHARGE = 100
INTERVENE = 3411
SHIELD_BLOCK = 2565
DIE_BY_THE_SWORD = 118038
ENRAGED_REGEN = 184364
RALLYING_CRY = 97462
SHOCKWAVE = 46968
INTIMIDATING_SHOUT = 5246
BERSERKER_RAGE = 18499
STORM_BOLT = 107570
HEROIC_LEAP = 6544
HAMSTRING = 1715


SPEC = SpecRotationData(
    key="fury_warrior",
    display_name="Fury Warrior",
    class_id=1,
    spec_name="Fury",
    aliases={
        # Odyn's Fury — four combat-log IDs, one player button.
        385060: ODYNS_FURY,
        385061: ODYNS_FURY,
        385062: ODYNS_FURY,
        # Execute — Fury's Massacre talent gives it a different spell ID
        # (280735) while the baseline ability is 5308. Both represent
        # the same button to the player.
        280735: EXECUTE,
        # Charge follow-up (Double Time / second charge) shares the
        # button with the base Charge cast for rotation purposes.
        126664: CHARGE,
    },
    rotation_ids=frozenset({
        BLOODTHIRST,
        RAGING_BLOW,
        RAMPAGE,
        EXECUTE,
        WHIRLWIND,
        THUNDER_CLAP,
        THUNDER_BLAST,
        BLOODBATH,
    }),
    cooldown_ids=frozenset({
        AVATAR,
        RECKLESSNESS,
        ODYNS_FURY,
        THUNDEROUS_ROAR,
    }),
    utility_ids=frozenset({
        PUMMEL,              # interrupt
        SPELL_REFLECTION,    # defensive/utility
        SHIELD_BLOCK,        # defensive
        DIE_BY_THE_SWORD,    # defensive
        ENRAGED_REGEN,       # self-heal
        RALLYING_CRY,        # raid defensive
        SHOCKWAVE,           # AoE stun
        INTIMIDATING_SHOUT,  # fear
        STORM_BOLT,          # single-target stun
        BERSERKER_RAGE,      # fear break / rage boost
        CHARGE,              # engage / gap closer
        INTERVENE,           # mobility / ally protection
        HEROIC_LEAP,         # mobility
        HAMSTRING,           # slow
    }),
    ignore_ids=frozenset({
        1236616,             # Light's Potential — trinket proc
        383781,              # Algeth'ar Puzzle — dungeon item
        384110,              # Wrecking Throw — PvP talent, not rotational
    }),
    reference_opener=(
        OpenerStep(CHARGE, "Charge", note="Pre-pull"),
        OpenerStep(RECKLESSNESS, "Recklessness"),
        OpenerStep(AVATAR, "Avatar"),
        OpenerStep(ODYNS_FURY, "Odyn's Fury"),
        OpenerStep(THUNDER_BLAST, "Thunder Blast"),
        OpenerStep(RAMPAGE, "Rampage"),
        OpenerStep(BLOODTHIRST, "Bloodthirst"),
        OpenerStep(RAGING_BLOW, "Raging Blow"),
        OpenerStep(RAMPAGE, "Rampage"),
        OpenerStep(BLOODTHIRST, "Bloodthirst"),
        OpenerStep(RAGING_BLOW, "Raging Blow"),
        OpenerStep(THUNDER_BLAST, "Thunder Blast"),
        OpenerStep(RAMPAGE, "Rampage"),
        OpenerStep(EXECUTE, "Execute", note="If <35% or Massacre"),
        OpenerStep(BLOODTHIRST, "Bloodthirst"),
    ),
    guide_url=(
        "https://www.icy-veins.com/wow/"
        "fury-warrior-pve-dps-rotation-cooldowns-abilities"
    ),
    last_reviewed="2026-04-21",
)
