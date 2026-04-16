"""Major cooldown buff IDs per spec for tracking usage via WCL Buffs table.

These are the "big" cooldowns that good players use on cooldown during M+.
A player who never uses their major CDs is leaving significant performance on the table.

IMPORTANT: These are WCL *buff* IDs (the aura that appears on the player),
not cast/spell IDs. WCL's Buffs table reports auras by their buff ID.

Organized by (class_id, spec_name).
Each entry is a list of (buff_id, ability_name, expected_uptime_pct) tuples.
"""

# (class_id, spec_name) -> [(buff_id, name, expected_uptime_pct), ...]
SPEC_MAJOR_COOLDOWNS: dict[tuple[int, str], list[tuple[int, str, float]]] = {
    # ── DPS Specs ────────────────────────────────────────────────────────

    # Warrior
    (1, "Arms"): [
        (227847, "Bladestorm", 5),
        (107574, "Avatar", 15),
    ],
    (1, "Fury"): [
        (1719, "Recklessness", 15),
        # Ravager (228920) removed 2026-04-16: summons a weapon (pet-like
        # entity), no self-buff aura on the player. Sampler confirmed 0
        # Fury logs had it in their BuffsTable.
    ],

    # Paladin
    (2, "Retribution"): [
        (31884, "Avenging Wrath", 20),
        (255937, "Wake of Ashes", 5),
    ],

    # Hunter
    (3, "Beast Mastery"): [
        (19574, "Bestial Wrath", 25),
        (359844, "Call of the Wild", 10),
    ],
    (3, "Marksmanship"): [
        (288613, "Trueshot", 15),
    ],
    (3, "Survival"): [
        (360966, "Spearhead", 12),
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
        (13750, "Adrenaline Rush", 20),
        (271896, "Blade Rush", 5),  # was 271877 — sampler showed 271896 as the actual buff ID (2026-04-16)
    ],
    (4, "Subtlety"): [
        (121471, "Shadow Blades", 15),
        # Shuriken Tornado removed 2026-04-15: talent-gated and rarely
        # picked in current M+ builds — Sub typically takes alternatives.
        # Audit showed 0 uses across observed Sub Rogue logs.
    ],

    # Priest
    (5, "Shadow"): [
        (228260, "Void Eruption", 15),
        (391109, "Dark Ascension", 10),
    ],

    # Death Knight
    (6, "Frost"): [
        (51271, "Pillar of Frost", 20),
        (279302, "Frostwyrm's Fury", 3),
    ],
    (6, "Unholy"): [
        # Apocalypse (275699) removed 2026-04-15: ~45s-90s CD (too short
        # for "major"), not a self-buff aura. Army of the Dead is the
        # real major CD for Unholy.
        (42650, "Army of the Dead", 3),
    ],

    # Shaman
    (7, "Elemental"): [
        (191634, "Stormkeeper", 10),
        # Fire Elemental (198067) removed 2026-04-16: summons a pet — the
        # elemental has its own buffs, the shaman does not. No self-aura
        # detectable via BuffsTable.
    ],
    (7, "Enhancement"): [
        # Feral Spirit (51533) removed 2026-04-16: summons wolves, no
        # self-buff on the shaman. Same pet-summon pattern as Fire Elemental.
        (114051, "Ascendance", 10),
    ],

    # Mage
    (8, "Arcane"): [
        (365362, "Arcane Surge", 10),  # was 365350 — sampler showed 365362 as the aura ID (2026-04-16)
        (321507, "Touch of the Magi", 8),
    ],
    (8, "Fire"): [
        (190319, "Combustion", 12),
    ],
    (8, "Frost"): [
        (12472, "Icy Veins", 20),
        # Frozen Orb (84714) removed 2026-04-16: cast-only spell with no
        # self-buff aura — same pattern as Kill Command. The orb effect
        # exists in the world, not on the caster, so BuffsTable can't
        # see it. Icy Veins remains; if it disappears across multiple
        # Frost Mage logs we'll revisit the ID (Midnight may have
        # renamed/replaced).
    ],

    # Warlock
    (9, "Affliction"): [
        # Summon Darkglare (205180) removed 2026-04-16: summons a demon,
        # no self-buff aura. Aff currently has no trackable major CD via
        # BuffsTable; flagged for future debuff-on-target detection
        # (Haunt / Malefic Rapture stacking) if we add that path.
    ],
    (9, "Demonology"): [
        (265187, "Summon Demonic Tyrant", 10),
        # Grimoire: Felguard (111898) removed 2026-04-15: creates a pet,
        # not a self-buff aura — BuffsTable never surfaces it. Demo has
        # comparatively few self-buff majors; Tyrant is the primary.
    ],
    (9, "Destruction"): [
        (111685, "Summon Infernal", 10),  # was 1122 — 111685 is the player-side aura (2026-04-16)
    ],

    # Monk
    (10, "Windwalker"): [
        (137639, "Storm, Earth, and Fire", 20),
        # Invoke Xuen (123904) removed 2026-04-16: summons a pet, no
        # self-buff. SEF stays (it buffs the monk via spirit clones).
    ],

    # Druid
    (11, "Balance"): [
        (194223, "Celestial Alignment", 15),
        (202770, "Fury of Elune", 5),
    ],
    (11, "Feral"): [
        (106951, "Berserk", 15),
        (102543, "Incarnation: Avatar of Ashamane", 15),
    ],

    # Demon Hunter
    (12, "Havoc"): [
        (162264, "Metamorphosis", 15),  # was 191427 — sampler showed 162264 as the DH Meta aura (2026-04-16)
        (258860, "Essence Break", 5),
    ],
    # Midnight-added 4th DH spec (ranged DPS). Void Metamorphosis is the
    # high-confidence major CD identified from Mvpewe's audit (659 buff
    # uses, name pattern matches Havoc/Vengeance Metamorphosis CDs).
    # Other observed buffs (Soul Fragments, Feast of Souls, Emptiness)
    # read as passive resources/procs and are intentionally excluded.
    (12, "Devourer"): [
        (1225789, "Void Metamorphosis", 15),
    ],

    # Evoker
    (13, "Devastation"): [
        (375087, "Dragonrage", 15),
    ],
    (13, "Augmentation"): [
        (395296, "Ebon Might", 30),  # was 395152 — sampler showed 395296 as the self-aura ID (2026-04-16)
        (404977, "Time Skip", 5),
    ],

    # ── Tank Specs (active mitigation cooldowns) ─────────────────────────

    (1, "Protection"): [
        (871, "Shield Wall", 3),
        (12975, "Last Stand", 5),
        (132404, "Shield Block", 40),  # was 2565 — sampler showed 132404 as the buff-on-warrior (2026-04-16)
    ],
    (2, "Protection"): [
        (31850, "Ardent Defender", 5),
        (393108, "Guardian of Ancient Kings", 5),  # was 86659 — sampler showed 393108 as the active aura (2026-04-16)
        (132403, "Shield of the Righteous", 40),  # was 53600 — sampler showed 132403 as the stacking buff (2026-04-16)
    ],
    (6, "Blood"): [
        (55233, "Vampiric Blood", 8),
        (81256, "Dancing Rune Weapon", 10),  # was 49028 — sampler showed 81256 as the DK self-buff (2026-04-16)
    ],
    (10, "Brewmaster"): [
        (120954, "Fortifying Brew", 8),
        (132578, "Invoke Niuzao, the Black Ox", 12),
        (325153, "Exploding Keg", 5),
    ],
    (11, "Guardian"): [
        (22812, "Barkskin", 10),
        (61336, "Survival Instincts", 5),
        (192081, "Ironfur", 50),
    ],
    (12, "Vengeance"): [
        (187827, "Metamorphosis", 10),
        # Fiery Brand (204021) removed 2026-04-15: applies a debuff to the
        # target (207771), not a self-buff — won't appear in the player's
        # BuffsTable regardless of use. Metamorphosis is the one reliable
        # self-buff major for Vengeance.
    ],

    # ── Healer Specs (major healing cooldowns) ───────────────────────────

    (2, "Holy"): [
        (31884, "Avenging Wrath", 20),
        (105809, "Holy Avenger", 10),
    ],
    (5, "Discipline"): [
        (47536, "Rapture", 8),
        # PW: Barrier (62618) removed 2026-04-16: ground effect, not a
        # self-buff aura on the priest — BuffsTable cannot see it.
    ],
    (5, "Holy"): [
        (200183, "Apotheosis", 10),
        (64843, "Divine Hymn", 3),
    ],
    (7, "Restoration"): [
        # Healing Tide Totem (108280) and original Spirit Link Totem (98008)
        # removed 2026-04-16: both drop totems, not self-buffs. Sampler showed
        # 325174 "Spirit Link Totem" as the actual self-aura on the shaman
        # while the totem is active — using that instead.
        (325174, "Spirit Link Totem", 5),
    ],
    (10, "Mistweaver"): [
        # Yu'lon (322118) removed 2026-04-16: summons a pet serpent, no
        # self-buff on the MW. Revival (115310) is retained as a self-cast
        # channel even though the sampler didn't see it consistently.
        (115310, "Revival", 2),
    ],
    # Core CDs every Resto Druid has regardless of talent build.
    # Tree of Life, Nature's Swiftness, and Flourish are talent choices
    # (mutually exclusive with other capstones) — scoring a player on
    # talents they didn't pick is unfair. Convoke sits between talent
    # and near-universal, but kept because it's the baseline assumption
    # in current Midnight S1 builds.
    (11, "Restoration"): [
        (740, "Tranquility", 4),                # baseline, ~3min CD
        (391528, "Convoke the Spirits", 3),     # commonly talented, ~2min CD
        (22812, "Barkskin", 15),                # baseline 1min CD personal
        (29166, "Innervate", 4),                # baseline ~3min CD (on self or ally)
        # Ironbark (102342) removed 2026-04-15: external CD — buff lands
        # on the tank/target, not the Resto Druid. Our BuffsTable query
        # only sees self-auras, so Ironbark is invisible here by design.
    ],
    (13, "Preservation"): [
        (363534, "Rewind", 3),
        (370960, "Emerald Communion", 5),
    ],
}


def get_cooldowns_for_spec(class_id: int, spec_name: str) -> list[tuple[int, str, float]]:
    """Get the major cooldown abilities for a spec.

    Returns list of (ability_id, ability_name, expected_uptime_pct).
    """
    return SPEC_MAJOR_COOLDOWNS.get((class_id, spec_name), [])
