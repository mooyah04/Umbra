"""Devourer Demon Hunter rotation data — Midnight expansion's ranged
DPS third spec for DH.

Sampled 2026-04-21 from WCL report ZLMmrt1vKgz39Q4p/fight 13
(4,609 casts across 18 distinct abilities).

Key sampling finding: Soul Fragment (1223412) fires as a proc/trigger
event at 77.5% of all recorded casts — every Devour and Consume
generates multiple Soul Fragment events. It is NOT a button the
player presses, so it goes in ignore_ids. Without the ignore, the
frequency table is nothing but Soul Fragment spam.
"""
from app.rotation.spec_data import SpecRotationData

SPEC = SpecRotationData(
    key="devourer_dh",
    display_name="Devourer Demon Hunter",
    class_id=12,
    spec_name="Devourer",
    aliases={},
    rotation_ids=frozenset({
        1217610,  # Devour — primary generator/builder
        473662,   # Consume — spender
        473728,   # Void Ray — ranged attack
        1226019,  # Reap — situational finisher
        1245453,  # Cull
    }),
    cooldown_ids=frozenset({
        1221150,  # Collapsing Star — major CD (2% of casts)
        1260459,  # Nullsight — CD
        1234195,  # Void Nova — big CD
        198589,   # Blur (shared DH defensive)
        196718,   # Darkness (shared DH raid defensive)
    }),
    utility_ids=frozenset({
        183752,   # Disrupt (shared DH interrupt)
        207684,   # Sigil of Misery (shared DH AoE fear)
        202138,   # Sigil of Chains (shared DH)
        179057,   # Chaos Nova (shared DH)
        217832,   # Imprison (shared DH)
        188501,   # Spectral Sight (shared DH)
        131347,   # Glide (shared DH)
        58984,    # Shadowmeld (Night Elf racial)
        420217,   # Rescue
    }),
    ignore_ids=frozenset({
        1223412,  # Soul Fragment — passive proc, not a button press.
                  # Dominates 77% of the cast stream without this filter.
        1236994,  # Potion of Recklessness (consumable)
        1234768,  # Silvermoon Health Potion (consumable)
    }),
    last_reviewed="2026-04-21",
)
