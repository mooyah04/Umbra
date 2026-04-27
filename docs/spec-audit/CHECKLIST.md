# Spec Audit Progress

**Goal:** Walk all 40 specs across 13 classes, sample top Midnight S1 logs, validate per-spec cooldown / interrupt / dispel / CC coverage. Result: `cooldowns.py` and a new dispel-school registry that grade each spec against its own kit, with talent-gated abilities skipped automatically when the player didn't pick the talent.

**Per-class output:** one report under `docs/spec-audit/{class-slug}.md` covering all of that class's specs in one document.

**Codification:** after each batch of class reports lands, edits to `app/scoring/cooldowns.py` and the new dispel registry get applied in a single mainline commit per class. One changelog entry per class summarizes what changed.

---

## Batch 1 — tanks-anchor (4 classes, 13 specs)

- [ ] **Warrior** — Arms / Fury / Protection
- [ ] **Paladin** — Holy / Protection / Retribution
- [ ] **Death Knight** — Blood / Frost / Unholy
- [ ] **Druid** — Balance / Feral / Guardian / Restoration

## Batch 2 — tanks finish + healers (4 classes, 11 specs)

- [ ] **Demon Hunter** — Havoc / Vengeance / Devourer
- [x] **Monk** — ✅ Brewmaster (audited 2026-04-26) / Mistweaver / Windwalker
  - BRM: talent-aware skip + Strength of the Black Ox added. Dispel-type fix still pending (Detox = poison/disease only, not full magic dispel).
- [ ] **Priest** — Discipline / Holy / Shadow
- [ ] **Shaman** — Elemental / Enhancement / Restoration

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
