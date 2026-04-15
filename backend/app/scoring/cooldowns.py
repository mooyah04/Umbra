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
        (228920, "Ravager", 5),
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
        (360194, "Deathmark", 10),
        (79140, "Vendetta", 15),
    ],
    (4, "Outlaw"): [
        (13750, "Adrenaline Rush", 20),
        (271877, "Blade Rush", 5),
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
        (198067, "Fire Elemental", 15),
    ],
    (7, "Enhancement"): [
        (51533, "Feral Spirit", 15),
        (114051, "Ascendance", 10),
    ],

    # Mage
    (8, "Arcane"): [
        (365350, "Arcane Surge", 10),
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
        (205180, "Summon Darkglare", 10),
    ],
    (9, "Demonology"): [
        (265187, "Summon Demonic Tyrant", 10),
        # Grimoire: Felguard (111898) removed 2026-04-15: creates a pet,
        # not a self-buff aura — BuffsTable never surfaces it. Demo has
        # comparatively few self-buff majors; Tyrant is the primary.
    ],
    (9, "Destruction"): [
        (1122, "Summon Infernal", 10),
    ],

    # Monk
    (10, "Windwalker"): [
        (137639, "Storm, Earth, and Fire", 20),
        (123904, "Invoke Xuen", 12),
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
        (191427, "Metamorphosis", 15),
        (258860, "Essence Break", 5),
    ],

    # Evoker
    (13, "Devastation"): [
        (375087, "Dragonrage", 15),
    ],
    (13, "Augmentation"): [
        (395152, "Ebon Might", 30),
        (404977, "Time Skip", 5),
    ],

    # ── Tank Specs (active mitigation cooldowns) ─────────────────────────

    (1, "Protection"): [
        (871, "Shield Wall", 3),
        (12975, "Last Stand", 5),
        (2565, "Shield Block", 40),
    ],
    (2, "Protection"): [
        (31850, "Ardent Defender", 5),
        (86659, "Guardian of Ancient Kings", 5),
        (53600, "Shield of the Righteous", 40),
    ],
    (6, "Blood"): [
        (55233, "Vampiric Blood", 8),
        (49028, "Dancing Rune Weapon", 10),
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
        (62618, "Power Word: Barrier", 3),
    ],
    (5, "Holy"): [
        (200183, "Apotheosis", 10),
        (64843, "Divine Hymn", 3),
    ],
    (7, "Restoration"): [
        (108280, "Healing Tide Totem", 5),
        (98008, "Spirit Link Totem", 3),
    ],
    (10, "Mistweaver"): [
        (322118, "Yu'lon", 12),
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
