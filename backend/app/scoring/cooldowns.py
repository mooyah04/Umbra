"""Major cooldown buff IDs per spec for tracking usage via WCL Buffs table.

These are the "big" cooldowns that good players use on cooldown during M+.
A player who never uses their major CDs is leaving significant performance on the table.

IMPORTANT: These are WCL *buff* IDs (the aura that appears on the player),
not cast/spell IDs. WCL's Buffs table reports auras by their buff ID.

Organized by (class_id, spec_name).
Each entry is (buff_id, ability_name, expected_uptime_pct, kind) where kind
is "offensive" (damage/throughput boost) or "defensive" (damage reduction /
mitigation / emergency heal). The run page uses kind to pick the per-pull
icon (red sword vs blue shield); scoring doesn't care about it.
"""

from typing import Literal

CooldownKind = Literal["offensive", "defensive"]

# (class_id, spec_name) -> [(buff_id, name, expected_uptime_pct, kind), ...]
SPEC_MAJOR_COOLDOWNS: dict[tuple[int, str], list[tuple[int, str, float, CooldownKind]]] = {
    # ── DPS Specs ────────────────────────────────────────────────────────

    # Warrior
    (1, "Arms"): [
        # Bladestorm (227847) removed 2026-04-16 (Pass 2): channel with no
        # persistent self-aura — sampler didn't see it at 50% consensus.
        (107574, "Avatar", 15, "offensive"),
    ],
    (1, "Fury"): [
        (1719, "Recklessness", 15, "offensive"),
        # Ravager (228920) removed 2026-04-16: summons a weapon (pet-like
        # entity), no self-buff aura on the player. Sampler confirmed 0
        # Fury logs had it in their BuffsTable.
    ],

    # Paladin
    (2, "Retribution"): [
        (31884, "Avenging Wrath", 20, "offensive"),
        # Wake of Ashes (255937) replaced 2026-04-16 (Pass 2): WoA is a
        # hard cast with no self-aura. Execution Sentence is the
        # trackable major CD per sampler (90% consensus, med=24).
        (1234189, "Execution Sentence", 24, "offensive"),
    ],

    # Hunter
    (3, "Beast Mastery"): [
        (19574, "Bestial Wrath", 25, "offensive"),
        (359844, "Call of the Wild", 10, "offensive"),
    ],
    (3, "Marksmanship"): [
        (288613, "Trueshot", 13, "offensive"),  # Pass 2: observed at 70% consensus, med=13 (uptime was 15, now realistic)
    ],
    (3, "Survival"): [
        # Spearhead (360966) removed 2026-04-16 (Pass 2): 3s buff too
        # short to register reliably in BuffsTable — sampler didn't see
        # it at 50% consensus. Surv currently has no trackable major CD
        # via the BuffsTable path; needs a cast-event path if we add one.
        # Kill Command removed 2026-04-15: ~6s CD rotational spam, not a
        # "major" cooldown. Audit showed 0 buff uses — appears as a cast
        # event but not in the player's buff aura table.
    ],

    # Rogue
    (4, "Assassination"): [
        # Deathmark (360194) and Vendetta (79140) removed 2026-04-16:
        # both apply debuffs to enemies rather than buffs to the rogue,
        # so BuffsTable cannot see them. Needs a different detection path
        # (debuff-on-target count) to audit properly. Until then, Assn
        # has no trackable major CD here.
    ],
    (4, "Outlaw"): [
        (13750, "Adrenaline Rush", 20, "offensive"),
        (271896, "Blade Rush", 5, "offensive"),  # was 271877 — sampler showed 271896 as the actual buff ID (2026-04-16)
    ],
    (4, "Subtlety"): [
        (121471, "Shadow Blades", 15, "offensive"),
        # Shuriken Tornado removed 2026-04-15: talent-gated and rarely
        # picked in current M+ builds — Sub typically takes alternatives.
        # Audit showed 0 uses across observed Sub Rogue logs.
    ],

    # Priest
    (5, "Shadow"): [
        # Void Eruption (228260) replaced 2026-04-16 (Pass 2): VE is the
        # cast, Voidform (194249) is the resulting self-aura — that's
        # what BuffsTable reports. Sampler confirmed at 80% med=12.
        (194249, "Voidform", 12, "offensive"),
        # Dark Ascension (391109) removed: alternative talent to Void
        # Eruption, not universally taken. Sampler didn't see it at 50%.
    ],

    # Death Knight
    (6, "Frost"): [
        (51271, "Pillar of Frost", 20, "offensive"),
        # Frostwyrm's Fury (279302) removed 2026-04-16 (Pass 2): cast
        # with no self-aura. Sampler didn't see it at 50% consensus.
    ],
    (6, "Unholy"): [
        # Apocalypse (275699) removed 2026-04-15: ~45s-90s CD (too short
        # for "major"), not a self-buff aura. Army of the Dead is the
        # real major CD for Unholy.
        (42650, "Army of the Dead", 3, "offensive"),
    ],

    # Shaman
    (7, "Elemental"): [
        (191634, "Stormkeeper", 10, "offensive"),
        # Fire Elemental (198067) removed 2026-04-16: summons a pet — the
        # elemental has its own buffs, the shaman does not. No self-aura
        # detectable via BuffsTable.
    ],
    (7, "Enhancement"): [
        # Feral Spirit (51533) removed 2026-04-16: summons wolves, no
        # self-buff on the shaman. Same pet-summon pattern as Fire Elemental.
        # Ascendance (114051) replaced 2026-04-16 (Pass 2): Ascendance is
        # the alternate-form DPS CD but didn't show in the sampler;
        # Doom Winds is the current-meta major CD (90% consensus, med=25).
        (466772, "Doom Winds", 25, "offensive"),
    ],

    # Mage
    (8, "Arcane"): [
        (365362, "Arcane Surge", 10, "offensive"),  # was 365350 — sampler showed 365362 as the aura ID (2026-04-16)
        # Touch of the Magi (321507) removed 2026-04-16 (Pass 2): applies
        # a debuff to target, not a buff on the mage — BuffsTable can't
        # see it. Needs a debuff-on-target detection path if we add one.
    ],
    (8, "Fire"): [
        (190319, "Combustion", 12, "offensive"),
    ],
    (8, "Frost"): [
        # Icy Veins (12472) removed 2026-04-16 (Pass 2): sampler didn't
        # see any Icy Veins aura at 50% consensus across 10 top Frost
        # Mages. The aura ID must have changed in Midnight — until we
        # identify the correct one, track Mirror Image instead (90%
        # consensus, med=6). Mirror Image is an 80s-CD DPS decoy that
        # every Frost Mage talents.
        (55342, "Mirror Image", 6, "offensive"),
        # Frozen Orb (84714) removed 2026-04-16: cast-only spell with no
        # self-buff aura — same pattern as Kill Command.
    ],

    # Warlock
    (9, "Affliction"): [
        # Summon Darkglare (205180) removed 2026-04-16: summons a demon,
        # no self-buff aura. Aff currently has no trackable major CD via
        # BuffsTable; flagged for future debuff-on-target detection
        # (Haunt / Malefic Rapture stacking) if we add that path.
    ],
    (9, "Demonology"): [
        (265187, "Summon Demonic Tyrant", 10, "offensive"),
        # Grimoire: Felguard (111898) removed 2026-04-15: creates a pet,
        # not a self-buff aura — BuffsTable never surfaces it. Demo has
        # comparatively few self-buff majors; Tyrant is the primary.
    ],
    (9, "Destruction"): [
        (111685, "Summon Infernal", 10, "offensive"),  # was 1122 — 111685 is the player-side aura (2026-04-16)
    ],

    # Monk
    (10, "Windwalker"): [
        # Storm, Earth, and Fire (137639) replaced 2026-04-16 (Pass 2):
        # no SEF aura showed at 50% consensus. Aura ID must have
        # changed in Midnight. Touch of Karma (122470) is a universally-
        # taken WW defensive that sampler confirmed at 90% med=10.
        # Karma is classified defensive: it's an absorb-then-reflect
        # CD. Damage is a side effect; the primary use is survival.
        (122470, "Touch of Karma", 10, "defensive"),
        # Invoke Xuen (123904) removed 2026-04-16: summons a pet.
    ],

    # Druid
    (11, "Balance"): [
        # Celestial Alignment (194223) replaced 2026-04-16 (Pass 2):
        # Incarnation: Chosen of Elune is the current-meta major (90%
        # consensus, med=15) — it's the talent upgrade to CA.
        (102560, "Incarnation: Chosen of Elune", 15, "offensive"),
        (202770, "Fury of Elune", 5, "offensive"),
    ],
    (11, "Feral"): [
        (106951, "Berserk", 15, "offensive"),
        # Incarnation: Avatar of Ashamane (102543) removed 2026-04-16
        # (Pass 2): alternate talent to Berserk, not universally taken
        # in Midnight S1 Feral builds. Sampler didn't see it at 50%.
    ],

    # Demon Hunter
    (12, "Havoc"): [
        (162264, "Metamorphosis", 15, "offensive"),  # was 191427 — sampler showed 162264 as the DH Meta aura (2026-04-16)
        # Essence Break (258860) removed 2026-04-16 (Pass 2): target
        # debuff, not self-buff — BuffsTable can't see it.
        (370965, "The Hunt", 22, "offensive"),  # Pass 2 add: 80% consensus, med=22 — Havoc's reliable hero-talent CD
    ],
    # Midnight-added 4th DH spec (ranged DPS). Void Metamorphosis is the
    # high-confidence major CD identified from Mvpewe's audit (659 buff
    # uses, name pattern matches Havoc/Vengeance Metamorphosis CDs).
    # Other observed buffs (Soul Fragments, Feast of Souls, Emptiness)
    # read as passive resources/procs and are intentionally excluded.
    (12, "Devourer"): [
        (1225789, "Void Metamorphosis", 15, "offensive"),
    ],

    # Evoker
    (13, "Devastation"): [
        (375087, "Dragonrage", 15, "offensive"),
    ],
    (13, "Augmentation"): [
        (395296, "Ebon Might", 30, "offensive"),  # was 395152 — sampler showed 395296 as the self-aura ID (2026-04-16)
        # Time Skip (404977) removed 2026-04-16 (Pass 2): talented, not
        # universal. Breath of Eons is the Aug signature major CD the
        # sampler confirmed at 100% med=22.
        (442204, "Breath of Eons", 22, "offensive"),
    ],

    # ── Tank Specs (active mitigation cooldowns) ─────────────────────────
    # Every tank CD below is defensive — they're mitigation or emergency
    # damage-reduction auras. The big cooldown story for a tank in M+ is
    # "did you survive the incoming burst", not "did you press a DPS CD".

    (1, "Protection"): [
        (871, "Shield Wall", 3, "defensive"),
        # Last Stand (12975) removed 2026-04-16 (Pass 2): 15s aura too
        # short to register reliably via BuffsTable snapshots — sampler
        # didn't see it at 50% consensus.
        (132404, "Shield Block", 40, "defensive"),  # was 2565 — sampler showed 132404 as the buff-on-warrior (2026-04-16)
    ],
    (2, "Protection"): [
        (31850, "Ardent Defender", 5, "defensive"),
        (393108, "Guardian of Ancient Kings", 5, "defensive"),  # was 86659 — sampler showed 393108 as the active aura (2026-04-16)
        (132403, "Shield of the Righteous", 40, "defensive"),  # was 53600 — sampler showed 132403 as the stacking buff (2026-04-16)
    ],
    (6, "Blood"): [
        (55233, "Vampiric Blood", 8, "defensive"),
        (81256, "Dancing Rune Weapon", 10, "defensive"),  # was 49028 — sampler showed 81256 as the DK self-buff (2026-04-16)
    ],
    (10, "Brewmaster"): [
        (120954, "Fortifying Brew", 8, "defensive"),
        (132578, "Invoke Niuzao, the Black Ox", 12, "defensive"),
        (325153, "Exploding Keg", 5, "defensive"),
    ],
    (11, "Guardian"): [
        (22812, "Barkskin", 10, "defensive"),
        (61336, "Survival Instincts", 5, "defensive"),
        (192081, "Ironfur", 50, "defensive"),
    ],
    (12, "Vengeance"): [
        (187827, "Metamorphosis", 10, "defensive"),
        # Fiery Brand (204021) removed 2026-04-15: applies a debuff to the
        # target (207771), not a self-buff — won't appear in the player's
        # BuffsTable regardless of use. Metamorphosis is the one reliable
        # self-buff major for Vengeance.
    ],

    # ── Healer Specs (major healing cooldowns) ───────────────────────────
    # Kind tagging for healers is intent-driven: a CD whose primary job is
    # "keep the group alive" (channeled raid heals, damage-reduction
    # totems, rewinds) is defensive; a CD whose primary job is "boost my
    # damage/throughput window" (Wings, Conduit, Convoke, Stasis) is
    # offensive. Most healer CDs technically do both, but the visual
    # signal on the run page follows the primary intent.

    (2, "Holy"): [
        (31884, "Avenging Wrath", 20, "offensive"),
        # Holy Avenger (105809) removed 2026-04-16 (Pass 2): not taken in
        # current-meta M+ Holy Paladin builds — sampler didn't see it at
        # 50% consensus.
    ],
    (5, "Discipline"): [
        # Rapture (47536) replaced 2026-04-16 (Pass 2): Rapture empowers
        # PW:Shield but isn't a persistent self-buff. Ultimate Penitence
        # (421453) is Disc's big hero-talent CD that does show reliably
        # (80% consensus, med=4).
        (421453, "Ultimate Penitence", 4, "offensive"),
        # PW: Barrier (62618) removed 2026-04-16: ground effect.
    ],
    (5, "Holy"): [
        (200183, "Apotheosis", 10, "offensive"),
        (64843, "Divine Hymn", 3, "defensive"),
    ],
    (7, "Restoration"): [
        # Healing Tide Totem (108280) and original Spirit Link Totem (98008)
        # removed 2026-04-16: both drop totems, not self-buffs. Sampler showed
        # 325174 "Spirit Link Totem" as the actual self-aura on the shaman
        # while the totem is active — using that instead.
        (325174, "Spirit Link Totem", 5, "defensive"),
    ],
    (10, "Mistweaver"): [
        # Yu'lon (322118) removed 2026-04-16: summons a pet serpent.
        # Revival (115310) replaced 2026-04-16 (Pass 2): self-cast heal
        # burst with no aura on caster. Celestial Conduit (443028) is
        # the current-meta MW major CD (90% consensus, med=11).
        (443028, "Celestial Conduit", 11, "offensive"),
    ],
    # Core CDs every Resto Druid has regardless of talent build.
    # Tree of Life, Nature's Swiftness, and Flourish are talent choices
    # (mutually exclusive with other capstones) — scoring a player on
    # talents they didn't pick is unfair. Convoke sits between talent
    # and near-universal, but kept because it's the baseline assumption
    # in current Midnight S1 builds.
    (11, "Restoration"): [
        (740, "Tranquility", 4, "defensive"),                 # baseline, ~3min CD
        (391528, "Convoke the Spirits", 3, "offensive"),      # commonly talented, ~2min CD
        # Barkskin (22812) removed 2026-04-16 (Pass 3): 1-min rotational
        # personal defensive, not a "major" CD. Its inclusion saturated
        # Dobbermon's cooldown_usage at flat 100 across every run — the
        # category lost all signal. Tranq + Convoke are the true signature
        # CDs for a Resto Druid; score on those alone.
        # Innervate removed in Pass 2 (cast on allies, not self).
        # Ironbark removed 2026-04-15 (external, lands on target).
    ],
    (13, "Preservation"): [
        (363534, "Rewind", 3, "defensive"),
        # Emerald Communion (370960) replaced 2026-04-16 (Pass 2): mana-
        # recovery channel, not a performance major. Stasis (370562) is
        # the signature Pres cooldown the sampler caught at 100% med=17.
        (370562, "Stasis", 17, "offensive"),
    ],
}


def get_cooldowns_for_spec(
    class_id: int, spec_name: str
) -> list[tuple[int, str, float, CooldownKind]]:
    """Get the major cooldown abilities for a spec.

    Returns list of (ability_id, ability_name, expected_uptime_pct, kind).
    """
    return SPEC_MAJOR_COOLDOWNS.get((class_id, spec_name), [])
