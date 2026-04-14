"""High-priority interruptible spell IDs per M+ dungeon.

These are the casts that MUST be interrupted — heals, dangerous AoE,
fear/charm effects, etc. Interrupting these is far more valuable than
kicking filler casts.

Organized by encounter_id (WCL dungeon encounter ID).
Each entry is a list of (spell_id, spell_name) tuples.

Current M+ Season (The War Within S2) dungeons.
"""

# encounter_id -> [(spell_id, spell_name), ...]
CRITICAL_INTERRUPTS: dict[int, list[tuple[int, str]]] = {
    # ── Cinderbrew Meadery (12661) ──────────────────────────────────────
    12661: [
        (453909, "Boiling Flames"),
        (440687, "Honey Volley"),
        (441242, "Free Samples?"),
        (423051, "Burning Light"),
    ],

    # ── Darkflame Cleft (12651) ─────────────────────────────────────────
    12651: [
        (423479, "Wicklighter Bolt"),
        (425536, "Mole Frenzy"),
        (424322, "Explosive Flame"),
        (427176, "Drain Light"),
        (426145, "Paranoid Mind"),
    ],

    # ── The Rookery (12648) ─────────────────────────────────────────────
    12648: [
        (427260, "Lightning Surge"),
        (205448, "Void Bolt"),
    ],

    # ── Priory of the Sacred Flame (12649) ──────────────────────────────
    12649: [
        (427356, "Greater Heal"),
        (427357, "Holy Smite"),
        (444743, "Fireball Volley"),
        (424421, "Fireball"),
        (424419, "Battle Cry"),
        (423051, "Burning Light"),
        (283650, "Blinding Faith"),
        (424431, "Holy Radiance"),
    ],

    # ── Operation: Floodgate (12773) ────────────────────────────────────
    12773: [
        (1214468, "Trickshot"),
        (462771, "Surveying Beam"),
        (463058, "Bloodthirsty Cackle"),
        (468631, "Harpoon"),
        (265084, "Blood Bolt"),
        (471733, "Restorative Algae"),
        (465813, "Lethargic Venom"),
    ],

    # ── The MOTHERLODE!! (61594) ────────────────────────────────────────
    61594: [
        (280604, "Iced Spritzer"),
        (263202, "Rock Lance"),
        (268702, "Furious Quake"),
        (268797, "Transmute: Enemy to Goo"),
    ],

    # ── Theater of Pain (62293) ─────────────────────────────────────────
    62293: [
        (341902, "Unholy Fervor"),
        (330784, "Necrotic Bolt"),
        (330868, "Necrotic Bolt Volley"),
        (330810, "Bind Soul"),
        (330716, "Soulstorm"),
        (342675, "Bone Spear"),
        (330875, "Spirit Frost"),
    ],

    # ── Operation: Mechagon - Workshop (112098) ─────────────────────────
    112098: [
        (293827, "Giga-Wallop"),
        (293729, "Tune Up"),
    ],
}

# Universally critical cast types across all dungeons (heals, mass CC, etc.)
UNIVERSAL_CRITICAL_INTERRUPTS: list[tuple[int, str]] = [
    # Common M+ mob heals and dangerous casts that appear across dungeons
    # These should be populated per season
]


def get_critical_interrupt_ids(encounter_id: int) -> set[int]:
    """Get the set of high-priority interruptible spell IDs for a dungeon.

    Returns spell IDs (not names) for fast lookup.
    Includes both dungeon-specific and universal critical casts.
    """
    ids = set()

    for spell_id, _ in CRITICAL_INTERRUPTS.get(encounter_id, []):
        ids.add(spell_id)

    for spell_id, _ in UNIVERSAL_CRITICAL_INTERRUPTS:
        ids.add(spell_id)

    return ids
