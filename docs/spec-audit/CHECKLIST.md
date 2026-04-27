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

- [ ] **Hunter** — Beast Mastery / Marksmanship / Survival
- [ ] **Rogue** — Assassination / Outlaw / Subtlety
- [ ] **Mage** — Arcane / Fire / Frost
- [ ] **Warlock** — Affliction / Demonology / Destruction
- [ ] **Evoker** — Augmentation / Devastation / Preservation

---

## Tracker

When an agent completes a class report, update the checkbox above and add a line under the class's name with the date and a one-line summary of what changed.

When the codification PR for a class lands, add a second sub-line noting the commit SHA and changelog entry date.
