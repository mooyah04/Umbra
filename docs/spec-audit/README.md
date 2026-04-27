# Spec Audit

Per-class audits validating that Umbra grades each spec against its own kit. Goal: every player gets graded on the cooldowns, dispels, and interrupts their actual class/spec has, with talent-gated abilities skipped automatically when the player didn't pick the talent.

## Why this exists

The Brewmaster audit (2026-04-26) revealed two structural issues that almost certainly affect other specs:

1. **Talent-gated CDs were scored as 0** instead of skipped when the player didn't pick the talent. Fixed in `_get_cooldown_usage` — now checks aura presence in the run's BuffsTable. This audit verifies each spec's CD list is correct so the skip mechanism has the right targets.
2. **Build divergence within a spec.** Brewmaster Keg vs Black Ox Brew paths each have different CDs. Both alt-talents need to be tracked so the skip catches whichever one the player didn't pick.

Plus a third lesson the audit will systematize: **per-spec dispel TYPE coverage.** Brewmaster's Detox is poison/disease only, but the engine currently treats `class_has_dispel(Monk)=True` as a full Magic-cleanse. The audit produces a `(class_id, spec) → {schools}` registry that fixes this across every class.

## Workflow

```
For each class:
  1. Run `python -m scripts.sample_spec_cds --class "X" --spec "Y"` for each spec.
  2. Read the consensus tables. Apply BRM lessons:
       - <50% consensus on currently-tracked CDs → drop or alt-build flag
       - >70% consensus untracked auras → add
       - 30%-70% split → alt-build path; track both
  3. Sample dispels via `sample_dispels.py` (and per-spec spell list).
  4. Identify interrupt spell ID + observed median kicks per fight.
  5. Write findings to `docs/spec-audit/{class}.md` using `_template.md`.

After each class report lands, codification:
  6. Edit `app/scoring/cooldowns.py` for that class's specs.
  7. Add entries to the new dispel-school registry (location TBD; first
     class to land it picks the file).
  8. Backfill `cooldown_usage_pct` on existing runs if values change.
  9. Recompute PlayerScore for affected players.
 10. Add a per-class changelog entry.
```

## Files in this directory

- `README.md` — this file
- `CHECKLIST.md` — 13-class progress tracker, batched by role priority
- `_template.md` — structured report shape every class report follows
- `{class-slug}.md` — one report per class, e.g. `warrior.md`, `priest.md`

## Sampler quick reference

```bash
cd backend
PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds \
  --class "Death Knight" \
  --spec "Blood" \
  --samples-per-dungeon 1 \
  --top-n 8

# Bigger sample for low-population specs:
PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds \
  --class "Warrior" --spec "Arms" \
  --samples-per-dungeon 2 --top-n 12
```

The `PYTHONIOENCODING=utf-8` prefix is needed on Windows to print Chinese / Cyrillic / accented player names without crashing on the cp1252 console codec.

## What "done" looks like for a class

A class is considered audited when:
- [ ] Report file exists with all specs filled in
- [ ] Each spec has a consensus table covering at least 5 distinct top players
- [ ] Recommendations are actionable (specific aura IDs to add/drop/keep, dispel schools listed)
- [ ] Open questions section is empty or has been resolved with Logan
- [ ] Codification PR has landed
- [ ] Changelog entry is published
