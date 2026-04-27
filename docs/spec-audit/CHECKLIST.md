# Spec Audit Progress

**Goal:** Walk all 40 specs across 13 classes, sample top Midnight S1 logs, validate per-spec cooldown / interrupt / dispel / CC coverage. Result: `cooldowns.py` and a new dispel-school registry that grade each spec against its own kit, with talent-gated abilities skipped automatically when the player didn't pick the talent.

**Per-class output:** one report under `docs/spec-audit/{class-slug}.md` covering all of that class's specs in one document.

**Codification:** after each batch of class reports lands, edits to `app/scoring/cooldowns.py` and the new dispel registry get applied in a single mainline commit per class. One changelog entry per class summarizes what changed.

---

## Batch 1 — tanks-anchor (4 classes, 13 specs)

- [x] **Warrior** — ✅ audited 2026-04-27 (Arms / Fury / Protection). Codified: Avatar added to Fury+Prot, Demolish added to Arms.
- [x] **Paladin** — ✅ audited 2026-04-27 (Holy / Protection / Retribution). Zero `cooldowns.py` edits needed; Pass-2 work held up.
- [x] **Death Knight** — ✅ audited 2026-04-27 (Blood / Frost / Unholy). Codified: Icebound Fortitude + Anti-Magic Zone added to Blood. Frost/Unholy unchanged.
- [x] **Druid** — ✅ audited 2026-04-27 (Balance / Feral / Guardian / Restoration). Codified: alt-build branches added (CA for Balance, Avatar of Ashamane for Feral, Incarnation of Ursoc for Guardian); Convoke added to Feral; Fury of Elune (Balance) and Ironfur (Guardian) dropped for saturation.

## Batch 2 — tanks finish + healers (4 classes, 11 specs)

- [x] **Demon Hunter** — ✅ audited 2026-04-27 (Havoc / Vengeance / Devourer). No `cooldowns.py` edits in this pass; Vengeance Fiery Brand and Devourer aura mapping flagged for cast-event follow-up.
- [x] **Monk** — ✅ Brewmaster (audited 2026-04-26) + Mistweaver / Windwalker (audited 2026-04-27). Codified: Mistweaver got Strength of the Black Ox + Unity Within; Mistweaver added to `HEALER_SPECS_WITH_INTERRUPT`; dispel-school registry entries for all 3 specs.
- [x] **Priest** — ✅ audited 2026-04-27 (Discipline / Holy / Shadow). Codified: Evangelism added to Disc, Power Infusion added to Shadow.
- [x] **Shaman** — ✅ audited 2026-04-27 (Elemental / Enhancement / Restoration). Codified: Ascendance added to Elemental, Healing Tide Totem re-added to Resto.

## Batch 3 — DPS-only classes (5 classes, 16 specs)

- [x] **Hunter** — ✅ audited 2026-04-27 (Beast Mastery / Marksmanship / Survival). Codified: Call of the Wild dropped from BM (pet-summon BuffsTable-invisible); Aspect of the Eagle added to Survival.
- [x] **Rogue** — ✅ audited 2026-04-27 (Assassination / Outlaw / Subtlety). Codified: Kingsbane added to Sin (first BuffsTable-visible major); Blade Rush dropped from Outlaw (saturation).
- [x] **Mage** — ✅ audited 2026-04-27 (Arcane / Fire / Frost). Zero `cooldowns.py` edits; all current entries hit 100%.
- [x] **Warlock** — ✅ audited 2026-04-27 (Affliction / Demonology / Destruction). Codified: Summon Darkglare re-added to Aff (2026-04-16 removal note was wrong).
- [x] **Evoker** — ✅ audited 2026-04-27 (Augmentation / Devastation / Preservation). Zero `cooldowns.py` edits; Pres-Quell `HEALER_SPECS_WITH_INTERRUPT` question correctly flagged as open per MW guardrail.

---

## Status as of 2026-04-27

All 13 classes (40 specs counting Devourer) audited. Codification covers all `cooldowns.py` edits and the per-spec dispel-school registry (`backend/app/scoring/dispel_schools.py`, 40 entries).

**Engine wiring deferred:** the registry is built but not yet consumed by the scoring engine. Wiring follow-ups required before consumption:

1. Define how `Bleed` (Evoker-only) should score per dungeon — bleed availability varies and no other class can cleanse it.
2. Confirm Cauterizing Flame's school list with Logan before locking the Evoker entries (sampler suggests Bleed/Poison/Disease/Curse for the all-spec version; needs game-mechanic verification per the MW lesson).
3. Decide healer cleanse credit shape: per-spec set membership × per-dungeon dispellable count, or simpler "spec covers >=N of the dungeon's schools" boolean.

**Cast-event detection path** is the second major follow-up — debuff-on-target CDs (Deathmark, Apocalypse, Touch of the Magi, Fiery Brand, etc.) and hard-cast majors without auras (Empower Rune Weapon, Wake of Ashes-style) are still uncodifiable until that path exists. Multiple class audits flagged it as the gating factor on filling out their CD lists.

**Open questions still pending Logan sign-off:**

- Optional defensive-CD adds for plate/leather/cloth DPS specs (Die by the Sword for Arms, Enraged Regeneration for Fury, Evasion + Cloak for Rogues, Greater Invisibility for Mages, Unending Resolve + Dark Pact for Warlocks). Class-wide policy question.
- Per-spec interrupt expected-count overrides for ranged kicks (BM/MM Counter Shot 24s, Mage Counterspell 24s, Evoker Quell 40s).
- Pres Evoker Quell → `HEALER_SPECS_WITH_INTERRUPT` addition.
- Vengeance DH Fiery Brand re-add (sampler now shows 100%, contradicting Pass-2 removal).
- Devourer DH primary aura (current `Void Metamorphosis` may be a passive proc, not a press).

---

## Tracker

When an agent completes a class report, update the checkbox above and add a line under the class's name with the date and a one-line summary of what changed.

When the codification PR for a class lands, add a second sub-line noting the commit SHA and changelog entry date.
