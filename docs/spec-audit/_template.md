# {Class} Spec Audit

**Date sampled:** YYYY-MM-DD
**Auditor:** {agent name or "Logan"}
**Sample depth:** N reports per spec, top {keystone_min}+ keys, {dungeon_count} active-season dungeons
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "{Class}" --spec "{Spec}" ...`

> Replace this template's `{placeholders}` and bullet stubs with real findings. Keep the structure intact so the codification phase can mechanically apply edits across all 13 reports.

---

## Spec: {Spec Name 1}

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 12345   | Spell A   | yes                | 95%         | 8           | keep |
| 67890   | Spell B   | yes                | 35%         | 4           | drop (alt-build at <50%) |
| 11111   | Spell C   | no                 | 80%         | 6           | add (baseline >70%) |
| 22222   | Spell D   | no                 | 55%         | 3           | alt-build path; track but mark as talent-gated |

**Notes on splits / alt-builds:**
- Spell B at 35% suggests build divergence. Top logs split between "{build A}" (takes Spell B) and "{build B}" (takes Spell D). Recommend tracking both with the talent-aware skip catching the absent one.
- ...

### Interrupts

- **Spell name (id):** `{Spell Name}` ({spell_id})
- **Cast type:** instant | hard-cast | charge-based | none
- **Sample observed kicks per fight (median):** N
- **Recommended expected count for scoring:** N (default role-level is 12 for tank, 15 for DPS — flag if this spec's mechanics make that unrealistic)
- **No-baseline-kick callout (only for healers/specs that lack one):** "..."

### Dispels

- **In-spec dispel ability:** `{Spell Name}` ({spell_id}), or "none in baseline kit"
- **Schools cleansable on allies:** `{Magic, Poison, Disease, Curse, Enrage}` — list only what the spec actually purges defensively. Offensive purges (Tranquilizing Shot, Mass Dispel offensive use) get noted separately.
- **Schools the engine should credit this spec for:** `{...}` (the subset the engine should use when computing healer-utility-of-cleanses)
- **Notes:** "Brewmaster's Detox is poison/disease only" type findings go here.

### CC

| Spell name | ID | Type (stun/silence/disorient/root/incapacitate/fear) | Notes |
|---|---|---|---|
| Stun X | 12345 | stun | baseline |
| Disorient Y | 67890 | disorient | talent-gated |

(Bullet form is fine if the spec only has 1-2 CC tools. Just list them.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(class_id, "{Spec}")`: drop X, add Y, change Z's expected uptime from N to M.
2. **Dispel registry** (new): `(class_id, "{Spec}") = {Magic, Poison}` or whatever subset applies.
3. **Interrupt benchmark override** (only if needed): "{Spec} should expect {N} kicks/fight not the role default".
4. Talent-gate flags: any CD that's <90% and >40% should be tagged so we know it's an alt-build path the talent-aware skip should pick up automatically.

### Top-cohort raw output reference

Paste the top 20-30 most-common buffs from the sampler output here for traceability. Future audits will diff against this snapshot.

```
   aura_id    pct  med_uses  name
   ...
```

---

## Spec: {Spec Name 2}

(repeat the structure above)

---

## Spec: {Spec Name 3}

(repeat the structure above)

---

## Open questions for review

- Things the auditor saw but isn't sure how to act on. Flagged for Logan to read before codification.

## Confidence

- Sample size N. Note any specs where the cohort was too small to be confident (e.g. fewer than 3 distinct logs). Those need a second pass with broader sampling before edits land.
