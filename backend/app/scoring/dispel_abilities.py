"""Dispel cast spell IDs per class.

Lives separately from `app.scoring.dispel_capability` (boolean
capability flags) because the utility ability breakdown on the run
page needs the actual numeric cast IDs to filter WCL's Casts events
table.

Each class that can dispel in PvE M+ gets a list of the casts to
match against. Both defensive dispels (healer cleanse off ally) and
offensive dispels (Tranq Shot / Purge / Spellsteal) appear here —
the breakdown display wants to surface anything the player
intentionally cast as "utility", regardless of target. Scoring
separately decides which of those count toward the utility category
via `dispellable_debuffs` and the dispel opportunity check.
"""

# class_id -> [(cast_id, name), ...]
# Names match the in-game spell names so the UI renders cleanly
# without a separate lookup step.
CLASS_DISPEL_CASTS: dict[int, list[tuple[int, str]]] = {
    2: [
        (4987, "Cleanse"),                 # Pal — Poison/Disease (+Magic for Holy)
    ],
    3: [
        (19801, "Tranquilizing Shot"),     # Offensive: Enrage + Magic off enemies
    ],
    5: [
        (527, "Purify"),                   # Priest — Magic/Disease
        (213634, "Purify Disease"),        # fallback name on some patches
        (528, "Dispel Magic"),             # Offensive magic dispel on enemies
        (32375, "Mass Dispel"),            # AoE offensive magic dispel
    ],
    7: [
        (77130, "Purify Spirit"),          # Resto — Curse + Magic
        (51886, "Cleanse Spirit"),         # Non-resto — Curse only
    ],
    8: [
        (475, "Remove Curse"),             # Mage — Curse off allies
        (30449, "Spellsteal"),             # Offensive magic theft from enemies
    ],
    9: [
        (89808, "Singe Magic"),            # Imp pet, magic off allies
        (119905, "Sear Magic"),            # Felhunter pet, magic off enemies
    ],
    10: [
        (115450, "Detox"),                 # Monk — Poison/Disease (+Magic for MW)
    ],
    11: [
        (88423, "Nature's Cure"),          # Resto — Curse/Poison/Magic
        (2782, "Remove Corruption"),       # Non-resto — Curse/Poison
    ],
    13: [
        (365585, "Expunge"),               # Dev/Aug — Poison
        (360823, "Naturalize"),            # Preservation — Poison + Magic
    ],
}


def get_dispel_casts(class_id: int) -> list[tuple[int, str]]:
    """Return the dispel cast list for a class. Empty when the class
    has no practical PvE dispel (Warrior, Rogue, DK, DH)."""
    return CLASS_DISPEL_CASTS.get(class_id, [])
