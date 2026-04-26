"""Per-spec methodology copy — what we actually measure for a given class/spec.

The category-breakdown tile on the run page has a "How this is measured"
section that used to be generic across every player. This module builds the
spec-aware version: a Resto Druid sees "no interrupt, so kicks don't count;
we score Nature's Cure dispels and your CC kit"; an Assassination Rogue sees
"we count Kick for interrupts; your class has no dispel so that weight
shifts to CC".

Source of truth for the underlying data:
  - app.scoring.roles         → healer interrupt capability
  - app.scoring.dispel_capability → which classes have a useful PvE dispel
  - app.scoring.cc_abilities  → per-class CC spell list (names + ids)
  - app.scoring.cooldowns     → per-spec tracked major cooldowns
  - app.scoring.cpm_benchmarks → per-spec CPM thresholds

The one gap in those modules is human-readable naming for interrupts and
dispel spells (they're only referenced by class capability flag). The two
lookup tables below fill that gap. They're intentionally hand-curated so
the tooltip copy reads naturally (e.g. "Nature's Cure (Magic) and Remove
Corruption (Curse)") rather than a dumb id list.
"""

from __future__ import annotations

from app.models import Role
from app.scoring.cc_abilities import CC_ABILITIES
from app.scoring.cooldowns import get_cooldowns_for_spec
from app.scoring.cpm_benchmarks import get_benchmark
from app.scoring.dispel_capability import class_has_dispel
from app.scoring.roles import SPEC_ROLE_MAP, healer_can_interrupt


CLASS_NAMES: dict[int, str] = {
    1: "Warrior",
    2: "Paladin",
    3: "Hunter",
    4: "Rogue",
    5: "Priest",
    6: "Death Knight",
    7: "Shaman",
    8: "Mage",
    9: "Warlock",
    10: "Monk",
    11: "Druid",
    12: "Demon Hunter",
    13: "Evoker",
}


# Interrupt ability name per class. Used when a single interrupt is shared
# by every non-healer spec of the class. Spec-level overrides in
# SPEC_INTERRUPT_OVERRIDES take precedence — classes with per-spec
# variation (Druid, Priest, Evoker) live there.
_CLASS_INTERRUPT: dict[int, str] = {
    1: "Pummel",
    2: "Rebuke",
    3: "Counter Shot",
    4: "Kick",
    6: "Mind Freeze",
    7: "Wind Shear",
    8: "Counterspell",
    9: "Spell Lock",           # Felhunter pet ability
    10: "Spear Hand Strike",
    12: "Disrupt",
}


# Spec-specific interrupt overrides. None = this spec explicitly has no
# baseline interrupt (all four "pure healer" specs without Rebuke/Wind Shear,
# plus Balance/Feral/Guardian/Resto druids which all have different kicks).
_SPEC_INTERRUPT_OVERRIDES: dict[tuple[int, str], str | None] = {
    # Druid — spec-specific interrupt names
    (11, "Balance"): "Solar Beam",
    (11, "Feral"): "Skull Bash",
    (11, "Guardian"): "Skull Bash",
    (11, "Restoration"): None,
    # Priest — only Shadow has Silence
    (5, "Shadow"): "Silence",
    (5, "Discipline"): None,
    (5, "Holy"): None,
    # Evoker — Preservation has no kick, Devastation/Augmentation have Quell
    (13, "Devastation"): "Quell",
    (13, "Augmentation"): "Quell",
    (13, "Preservation"): None,
    # Healers without a baseline interrupt
    (10, "Mistweaver"): None,  # MW does not have Spear Hand Strike
    # Paladin — Holy does have Rebuke, so no override needed.
    # Shaman — Resto keeps Wind Shear, no override needed.
    # Monk — only Brewmaster and Windwalker have Spear Hand Strike.
}


# Dispel toolkit per class. Each entry is one practical PvE dispel spell
# with the magic schools / effect types it removes. Spec-specific extras
# (e.g. Holy Paladin gains Magic on Cleanse) live in `spec_extras`.
#
# Shape: class_id -> list[{ name, types, spec_extras? }]
#   - types       : comma-separated effect schools the spell can dispel
#   - spec_extras : optional {spec_name: extra_types} for healer-only adds
#
# Classes without entries can't meaningfully dispel in PvE M+ — those are
# the 4 dispel-less classes (Warrior, Rogue, DK, DH) and scoring handles
# them via class_has_dispel().
_DISPEL_BY_CLASS: dict[int, list[dict]] = {
    2: [
        {
            "name": "Cleanse",
            "types": "Poison, Disease",
            "spec_extras": {"Holy": "Magic"},
        },
    ],
    3: [
        # Tranquilizing Shot is an offensive dispel (strips Enrage/Magic
        # buffs from enemies) — still counts for the utility category.
        {"name": "Tranquilizing Shot", "types": "Enrage and Magic off enemies"},
    ],
    5: [
        {
            "name": "Purify (Holy) / Purify Disease (all)",
            "types": "Disease",
            "spec_extras": {
                "Holy": "Magic",
                "Discipline": "Magic",
            },
        },
        {"name": "Dispel Magic / Mass Dispel", "types": "Magic off enemies"},
    ],
    7: [
        {
            "name": "Purify Spirit (Resto) / Cleanse Spirit (Enh)",
            "types": "Curse",
            "spec_extras": {"Restoration": "Magic"},
        },
    ],
    8: [
        {"name": "Remove Curse", "types": "Curse"},
    ],
    9: [
        # Warlock dispel comes from the Felhunter / Imp pet.
        {"name": "Singe Magic / Sear Magic", "types": "Magic (pet dispel)"},
    ],
    10: [
        {
            "name": "Detox",
            "types": "Poison, Disease",
            "spec_extras": {"Mistweaver": "Magic"},
        },
    ],
    11: [
        {
            "name": "Nature's Cure (Resto) / Remove Corruption (all)",
            "types": "Curse, Poison",
            "spec_extras": {"Restoration": "Magic"},
        },
    ],
    13: [
        {
            "name": "Expunge / Naturalize (Preservation)",
            "types": "Poison",
            "spec_extras": {"Preservation": "Magic"},
        },
    ],
}


def _dispel_text(class_id: int, spec_name: str) -> str | None:
    """Human-readable list of dispel abilities for this class/spec.

    Returns None when the class has no practical PvE dispel — the caller
    uses that to phrase the utility description as "no dispel, we shift
    that weight to kicks and CC".
    """
    entries = _DISPEL_BY_CLASS.get(class_id)
    if not entries:
        return None
    parts: list[str] = []
    for e in entries:
        types = e["types"]
        extras = e.get("spec_extras", {})
        if spec_name in extras:
            types = f"{types}, {extras[spec_name]}"
        parts.append(f"{e['name']} ({types})")
    return "; ".join(parts)


def _resolve_interrupt(class_id: int, spec_name: str) -> str | None:
    """The interrupt ability name for this spec, or None if none exists.

    Rules:
      - Healer specs default to no interrupt, except those flagged in
        HEALER_SPECS_WITH_INTERRUPT (Holy Pally, Resto Shaman) and
        Mistweaver (who keeps the monk kick).
      - Any spec in the override table wins, even for non-healers, to
        handle Druid (per-spec kick) and Priest/Evoker (spec-gated).
      - Everything else falls back to the class-level interrupt.
    """
    if (class_id, spec_name) in _SPEC_INTERRUPT_OVERRIDES:
        return _SPEC_INTERRUPT_OVERRIDES[(class_id, spec_name)]
    role = SPEC_ROLE_MAP.get((class_id, spec_name), Role.dps)
    if role is Role.healer and not healer_can_interrupt(class_id, spec_name):
        return None
    return _CLASS_INTERRUPT.get(class_id)


def _cc_ability_names(class_id: int) -> list[str]:
    """Names only — the caller decides how to render (bullet list, inline)."""
    return [name for _id, name in CC_ABILITIES.get(class_id, [])]


def _class_name(class_id: int) -> str:
    return CLASS_NAMES.get(class_id, f"Class {class_id}")


def _role_label(role: Role) -> str:
    return {Role.dps: "DPS", Role.healer: "healer", Role.tank: "tank"}[role]


# ── Per-category copy builders ───────────────────────────────────────────


def _utility_copy(
    class_id: int,
    spec_name: str,
    role: Role,
    interrupt: str | None,
    dispel_text: str | None,
    cc_names: list[str],
) -> dict[str, str]:
    """Utility paragraph for a specific spec.

    Healers weight toward dispels; DPS/tanks toward interrupts + CC. We
    mirror the engine's redistribution logic (engine.py _score_utility_*)
    so the copy matches how the number is actually computed.
    """
    spec_label = f"{spec_name} {_class_name(class_id)}"
    can_dispel = dispel_text is not None
    has_cc = bool(cc_names)

    pieces: list[str] = []
    pieces.append(
        f"Utility scoring for {spec_label}. "
    )

    # Interrupt framing differs by "has an interrupt" vs "doesn't"
    if interrupt:
        if role is Role.healer:
            pieces.append(
                f"You have a baseline interrupt ({interrupt}), so kicks count toward your grade "
                f"alongside dispels and CC. "
            )
        else:
            pieces.append(
                f"We count every {interrupt} cast you land; priority kicks (boss heals, mass CC) "
                f"are weighted 1.5x when we have the data for this dungeon. "
            )
    else:
        pieces.append(
            f"{spec_label} doesn't have a baseline interrupt, so kicks are not counted against you. "
            f"Your utility weight shifts entirely to dispels and CC. "
        )

    # Dispels
    if can_dispel:
        pieces.append(f"Your class dispels: {dispel_text}. ")
    else:
        pieces.append(
            f"{_class_name(class_id)} has no practical PvE dispel, so dispel contribution is "
            f"redistributed into interrupts and CC. "
        )

    # CC
    if has_cc:
        cc_list = ", ".join(cc_names)
        pieces.append(f"CC abilities we track: {cc_list}. ")
    else:
        pieces.append("No tracked CC abilities for this class. ")

    # Role weighting
    if role is Role.healer:
        if interrupt and can_dispel and has_cc:
            pieces.append("Rough split: ~50% dispels, ~30% interrupts, ~20% CC.")
        elif can_dispel and has_cc:
            pieces.append("Rough split: ~75% dispels, ~25% CC.")
        elif can_dispel:
            pieces.append("Dispels carry the category for you this season.")
    else:
        if can_dispel and has_cc:
            pieces.append("Rough split: ~55% interrupts, ~25% CC, ~20% dispels.")
        elif has_cc:
            pieces.append("Rough split: ~70% interrupts, ~30% CC.")
        elif can_dispel:
            pieces.append("Rough split: ~80% interrupts, ~20% dispels.")

    description = "".join(pieces).strip()

    # Spec-tailored improvement tip
    if interrupt:
        improve = (
            f"Install a kick-announcer (WeakAura or the OmniCD suite) and commit to a kick rotation with your team. "
            f"For {spec_label}, {interrupt} is your bread and butter. Aim to cover at least the priority casts "
            f"flagged in each dungeon guide."
        )
    else:
        # Healers without a kick lean harder on dispels + CC.
        if can_dispel:
            improve = (
                f"Dispels are your primary utility lever. Many M+ deaths are one-shot magic effects; "
                f"if a mob is casting a dispellable debuff, a same-GCD dispel is often the difference between a "
                f"wipe and a clean pull. Pair it with your CC kit ({', '.join(cc_names[:3])}...) for priority mobs."
            )
        else:
            improve = (
                f"Without kicks or dispels, your utility contribution is almost entirely CC. Pre-pull CCs "
                f"(sheep, sap, polymorph lookalikes) on priority mobs and AoE stuns on big pulls are where the grade moves."
            )

    return {"description": description, "howToImprove": improve}


def _cooldown_copy(
    class_id: int,
    spec_name: str,
    cooldowns: list[tuple[int, str, float, str]],
) -> dict[str, str]:
    """Cooldown usage paragraph — names the CDs we actually track for this spec."""
    spec_label = f"{spec_name} {_class_name(class_id)}"
    if not cooldowns:
        description = (
            f"We didn't find any reliably-trackable major cooldowns for {spec_label} this season. "
            f"This usually means the spec's big CDs are debuff-on-target abilities (which Warcraft Logs' "
            f"BuffsTable can't see) or short-duration auras that our sampling passes don't pick up. "
            f"This category is weighted down or excluded for you until we add a debuff-detection path."
        )
        improve = (
            f"Nothing you can do in-game changes this; it's a data-availability gap on our side. "
            f"Your grade falls through to the other categories until we expand CD tracking for {spec_name}."
        )
        return {"description": description, "howToImprove": improve}

    parts = []
    for _id, name, uptime, kind in cooldowns:
        parts.append(f"{name} ({kind}, ~{uptime:.0f}% expected uptime)")
    cd_list = ", ".join(parts)

    description = (
        f"We track the cooldowns every {spec_label} has access to regardless of talent build: {cd_list}. "
        f"Expected uses are computed from fight duration, then compared against what you actually pressed. "
        f"Talent-gated cooldowns (ones only some builds take) are intentionally excluded: we don't penalize "
        f"you for not picking a specific talent. Missing a single major CD can meaningfully drop this category; "
        f"hoarding it through the whole key is the most common sub-grade cause."
    )
    improve = (
        f"Rebind your majors to a prominent key and treat them as rotational, not emergency. If you're "
        f"sitting {cooldowns[0][1]} through a 30-minute dungeon, that's 10+ minutes of its window wasted. "
        f"Consider an OmniCD- or WeakAura-style cooldown tracker so the whole party can see each other's windows."
    )
    return {"description": description, "howToImprove": improve}


def _cpm_copy(role: Role, spec_name: str, class_id: int, benchmark) -> dict[str, str]:
    """CPM paragraph — names the spec's actual CPM thresholds."""
    spec_label = f"{spec_name} {_class_name(class_id)}"
    description = (
        f"Total casts divided by fight duration, scored against benchmarks specific to {spec_label}. "
        f"Our thresholds for your spec: "
        f"below {benchmark.poor:.0f} CPM = 0, "
        f"{benchmark.fair:.0f} = 50, "
        f"{benchmark.good:.0f} = 80, "
        f"{benchmark.excellent:.0f}+ = 100. "
        f"A high-CPM melee spec like Fury Warrior and a low-CPM ranged caster like Marksmanship Hunter will "
        f"have very different benchmarks; we don't apply a universal curve. Low CPM usually maps to rotation "
        f"gaps, over-movement on mechanics, or extended time with no valid target."
    )
    improve = (
        f"Check your Details timeline for long gaps between casts. Most gaps map to movement, mechanics you "
        f"could have precast through, or a dead target before the pull ends. For {spec_name}, pre-pulling "
        f"right before the puller engages is an easy 2-3 extra casts per pack, and that compounds over a dungeon."
    )
    return {"description": description, "howToImprove": improve}


# ── Public API ───────────────────────────────────────────────────────────


def build_methodology(class_id: int, spec_name: str) -> dict:
    """Return a spec-aware methodology payload for the run breakdown UI.

    Shape is picked so the frontend can either render the pre-baked
    category copy directly (what the run page does today) or re-render
    from the structured fields if we want to tweak presentation later.

    Unknown (class_id, spec_name) pairs still produce a valid payload —
    we fall back to DPS-shaped weighting so downstream callers don't need
    defensive null-checks. Category copy will read generically in that case.
    """
    role = SPEC_ROLE_MAP.get((class_id, spec_name), Role.dps)
    interrupt = _resolve_interrupt(class_id, spec_name)
    dispel_text = _dispel_text(class_id, spec_name)
    cc_names = _cc_ability_names(class_id)
    cooldowns = get_cooldowns_for_spec(class_id, spec_name)
    benchmark = get_benchmark(role, spec_name=spec_name, class_id=class_id)

    utility = _utility_copy(
        class_id, spec_name, role, interrupt, dispel_text, cc_names
    )
    cooldown = _cooldown_copy(class_id, spec_name, cooldowns)
    cpm = _cpm_copy(role, spec_name, class_id, benchmark)

    return {
        "class_id": class_id,
        "class_name": _class_name(class_id),
        "spec_name": spec_name,
        "role": role.value,
        "role_label": _role_label(role),
        "interrupt": {
            "has_interrupt": interrupt is not None,
            "ability_name": interrupt,
        },
        "dispels": {
            "can_dispel": class_has_dispel(class_id),
            "text": dispel_text,
        },
        "cc_abilities": [
            {"id": cid, "name": cname}
            for cid, cname in CC_ABILITIES.get(class_id, [])
        ],
        "major_cooldowns": [
            {
                "id": cid,
                "name": cname,
                "expected_uptime_pct": uptime,
                "kind": kind,
            }
            for cid, cname, uptime, kind in cooldowns
        ],
        "cpm_benchmark": {
            "poor": benchmark.poor,
            "fair": benchmark.fair,
            "good": benchmark.good,
            "excellent": benchmark.excellent,
        },
        "categories": {
            "utility": utility,
            "cooldown_usage": cooldown,
            "casts_per_minute": cpm,
        },
    }
