# Priest Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 distinct top player per active dungeon (8 dungeons), Discipline / Holy / Shadow
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Priest" --spec "{Spec}" --samples-per-dungeon 1 --top-n 8`

Cohort key range observed: **+18 to +21** (consistent with the Midnight S1 top-tier band). Eight distinct fights collected per spec — confidence threshold met for all three specs.

---

## Spec: Discipline

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 421453  | Ultimate Penitence | yes        | 100%        | 4           | keep |
| 472433  | Evangelism | no                 | 100%        | 15          | **add (baseline >70%)** |
| 81700   | Archangel | no                  | 100%        | 15          | **add candidate (see notes)** |
| 47753   | Divine Aegis | no               | 100%        | 113         | leave (passive absorb proc, not pressed CD) |
| 390787  | Weal and Woe | no               | 100%        | 1943        | leave (rotational stack tracker) |
| 390978  | Twist of Fate | no              | 100%        | 609         | leave (passive damage/heal proc) |
| 390692  | Borrowed Time | no              | 100%        | 224         | leave (rotational proc) |
| 47536   | Rapture | no                    | not seen in top-30 | — | leave dropped (Pass-2 decision validated — not a persistent self-aura) |
| 62618   | Power Word: Barrier | no          | not seen in top-30 | — | leave (ground effect — already understood) |
| 33206   | Pain Suppression | no             | not seen in top-30 | — | leave (lands on ally target, not self — same pattern as Ironbark) |

**Notes on splits / alt-builds:**
- **Evangelism (472433) at 100% med=15** is the most actionable add. It's a self-aura that extends Atonement durations — central to every Disc rotation, every player presses it, and it shows reliably in BuffsTable. Recommend adding `(472433, "Evangelism", 15, "offensive")`.
- **Archangel (81700) at 100% med=15** is a Voidweaver/Oracle hero-talent aura that triggers alongside Evangelism in current Midnight S1 builds. Two ways to read this:
  1. It's a near-universal hero-talent companion buff to Evangelism. If tracked, it would essentially mirror Evangelism's signal.
  2. Tracking both could double-count the same player action.

  Recommend tracking **only Evangelism** (the universal cast) and leaving Archangel as a passive secondary indicator. If a future hero-talent shift breaks the pairing, revisit.
- **Power Infusion (10060) at 100% med=13** appears across all three Priest specs. It's a self-buff Disc usually keeps for themselves in M+ (vs raid Twins-of-the-Sun glyph play), and at med=13 it's a real pressed CD. Worth considering as a tracked CD — but the cross-spec consideration is that PI is Priest-class-wide, not Disc-specific. Recommend deferring until the Holy/Shadow audit sections converge on whether to track PI on all three specs (consistency argument).
- **Mindbender / Shadowfiend** (the Disc throughput pet) didn't appear in the top-30 at the universal-aura level — sampler shows no consistent fiend aura on Disc cohort. Disc throughput comes from atonement damage + Penance + Smite, not a fiend press. Confirms cooldowns.py's omission is correct.
- **Ultimate Penitence (421453) at 100% med=4** validates the Pass-2 fix. Keep as-is.

### Interrupts

- **Spell name (id):** **none** — Discipline lacks a baseline interrupt. (Silence 15487 is Shadow-only; Disc/Holy do not have it.)
- **Cast type:** n/a
- **Sample observed kicks per fight (median):** 0 — Disc cannot kick.
- **Recommended expected count for scoring:** **exclude from interrupt scoring entirely.**
- **No-baseline-kick callout:** Confirmed. `HEALER_SPECS_WITH_INTERRUPT` in `roles.py` correctly excludes `(5, "Discipline")` — only Holy Paladin and Resto Shaman are in that set. The healer-utility scorer (`_score_utility_healer`) needs to fall through to a kicks=0-doesn't-penalize branch for Disc, which it currently does via the `healer_can_interrupt` check. **Verified correct.**

### Dispels

- **In-spec dispel ability:** `Purify` (527). Removes Magic + Disease from allies.
- **Schools cleansable on allies:** `{Magic, Disease}`
- **Schools the engine should credit this spec for:** `{Magic, Disease}`
- **Notes:**
  - Disc does NOT cleanse Poison or Curse. Healer dispel coverage is Magic+Disease only — narrower than Holy Paladin (Magic+Poison+Disease) or Resto Druid (Curse+Poison) but includes the most M+-relevant school (Magic).
  - **Mass Dispel (32375)** is a Priest-class-wide tool. Group dispel of up to 5 hostile (defensive: removes magic from allies) or 5 beneficial (offensive: purges enemies). Cast-time AoE, ~1 min CD. Ambiguous in offensive/defensive intent depending on use. Does NOT replace Purify for the per-spec defensive cleanse registry — Mass Dispel hits Magic only and is too situational to be the primary cleanse benchmark. Note as a separate utility flag if the engine ever credits group/AoE dispels.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Psychic Scream | 8122 | fear (AoE, 8s) | baseline, ~60s CD — universal panic button |
| Mind Control | 605 | mind control | situational, mostly meme-tier in M+ |
| Shackle Undead | 9484 | incapacitate (Undead only) | PvE niche — only relevant in Pit of Saron / Skyreach pulls |
| Holy Word: Chastise | 88625 | incapacitate / stun (Apotheosis) | Holy-only, n/a for Disc |

### Recommended changes

1. `app/scoring/cooldowns.py` `(5, "Discipline")`: **add `(472433, "Evangelism", 15, "offensive")`**. Keep Ultimate Penitence as-is.
2. **Dispel registry** (new): `(5, "Discipline") = {Magic, Disease}`.
3. **Interrupt benchmark override:** **none — exclude from interrupt scoring**. Verify the `_score_utility_healer` path correctly routes Disc through a no-kick-penalty branch.
4. **Mass Dispel utility note:** flag for a future "AoE/group dispel" credit category if the engine ever expands beyond single-target cleanses. Disc and Holy both have it; not a primary scoring signal.
5. **Talent-gate flags:** none currently needed. Evangelism is universally taken in current S1 builds; no <90% / >40% split observed.

### Top-cohort raw output reference

```
Aggregate over 8 Priest Discipline fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    421453      100%         4   Ultimate Penitence  [Ultimate Penitence]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1235193   100%      1839   Holy Ray
       81700   100%        15   Archangel
       21562   100%         3   Power Word: Fortitude
       47753   100%       113   Divine Aegis
      121557   100%        20   Angelic Feather
      390787   100%      1943   Weal and Woe
       45242   100%        22   Focused Will
       10060   100%        13   Power Infusion
      472433   100%        15   Evangelism
      374227   100%         5   Zephyr
     1252217   100%       233   Shadow Mend
      421453   100%         4   Ultimate Penitence (tracked)
      390978   100%       609   Twist of Fate
         586   100%        40   Fade
      114255   100%       101   Surge of Light
     1229746   100%        92   Arcanoweave Insight
     1253591   100%        89   Master the Darkness
      404381   100%         2   Defy Fate
      194384   100%       382   Atonement
      390692   100%       224   Borrowed Time
      390386   100%         3   Fury of the Aspects
       19236   100%        12   Desperate Prayer
      390677   100%        93   Inspiration
      381753   100%         3   Blessing of the Bronze
          17   100%        47   Power Word: Shield
      198069   100%        96   Power of the Dark Side
     1253593   100%        53   Void Shield
      193065   100%       178   Protective Light
     1241715   100%       180   Might of the Void
       41635   100%       171   Prayer of Mending
```

---

## Spec: Holy

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 200183  | Apotheosis | yes               | 100%        | 12          | keep |
| 64843   | Divine Hymn | yes              | 100%        | 9           | keep |
| 64844   | Divine Hymn (tick aura) | no    | 100%        | 39          | leave (per-tick aura of the same channel — would double-count Divine Hymn) |
| 47788   | Guardian Spirit | no            | 88%         | 2           | leave (lands on ally target, not self — same Ironbark pattern) |
| 372617  | Empyreal Blaze | no             | 88%         | 116         | leave (Holy Word proc/passive, not pressed CD) |
| 405963  | Divine Image | no               | 100%        | 450         | leave (passive proc tracker — saturation risk) |
| 1262766 | Benediction | no                | 100%        | 111         | leave (passive HoT proc tracker) |
| 265202  | Holy Word: Salvation | no       | not seen in top-30 | — | leave (talent-gated AND no consistent self-aura — see notes) |
| 19236   | Desperate Prayer | no            | 100%        | 12          | leave (1-min personal defensive — saturation trap) |
| 10060   | Power Infusion | no              | 100%        | 13          | candidate — see notes |

**Notes on splits / alt-builds:**
- Both currently-tracked Holy CDs (Apotheosis and Divine Hymn) hit 100% consensus. Apotheosis at med=12 and Divine Hymn at med=9 are realistic press counts — Pass-2 fixes hold.
- **`64844` (Divine Hymn tick aura) at 100% med=39** is the per-tick aura applied while the channel is active, not a separate cast. Tracking it would double-count the same press. **Leave untracked.**
- **Holy Word: Salvation (265202)** is the signature Holy CD per the user-supplied audit guidance, but it does NOT appear in the top-30 buff list. Two interpretations:
  1. Salvation places a HoT on each ally, not a self-aura on the priest — same off-target Ironbark/PainSup/Innervate pattern that's bitten other classes. BuffsTable on the priest's own actor wouldn't surface it.
  2. The current top-cohort builds are not running Salvation (it's a high-end capstone competing with Lightwell and Apotheosis upgrades).

  Either way, **do not add 265202** to the tracked list — the BuffsTable path can't see it. Flag for cast-event audit if the engine adds that path later.
- **Apotheosis** is talent-gated in the strictest sense (capstone in the Holy tree) but is universally taken — no alt-build flag needed for the current meta.
- **Divine Hymn** is baseline. The 100% consensus is reassuring.
- **Power Infusion (10060) at 100% med=13** mirrors Disc and Shadow. Consistent class-wide tool. Same recommendation: defer adding until a class-wide PI policy is set; tracking it on Holy alone would create cross-spec inconsistency.
- **Lightwell / Holy Word: Sanctify spam concern raised in audit guidance** — Holy Word: Sanctify is a rotational ground-effect heal, not a "major" CD. Saturation trap if added. Confirmed not present in the top-30 as a self-aura. Lightwell (724) likewise leaves no self-aura on the priest. Both correctly excluded.

### Interrupts

- **Spell name (id):** **none** — Holy lacks a baseline interrupt. Silence (15487) is Shadow-only.
- **Cast type:** n/a
- **Sample observed kicks per fight (median):** 0 — Holy cannot kick.
- **Recommended expected count for scoring:** **exclude from interrupt scoring entirely.**
- **No-baseline-kick callout:** Confirmed. `HEALER_SPECS_WITH_INTERRUPT` in `roles.py` correctly excludes `(5, "Holy")`. **Verified correct.**

### Dispels

- **In-spec dispel ability:** `Purify` (527). Removes Magic + Disease from allies. Same as Disc.
- **Schools cleansable on allies:** `{Magic, Disease}`
- **Schools the engine should credit this spec for:** `{Magic, Disease}`
- **Notes:**
  - Holy and Disc share the same cleanse profile (Magic+Disease via Purify 527).
  - Holy also has **Mass Dispel (32375)** — same notes as Disc. Group/AoE Magic dispel, ambiguous offensive vs defensive depending on cast, situational. Not the primary cleanse benchmark.
  - Holy does NOT cleanse Poison. Resto Druid / Holy Paladin own Poison cleanse on the healer side.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Psychic Scream | 8122 | fear (AoE, 8s) | baseline |
| Holy Word: Chastise | 88625 | incapacitate / stun (during Apotheosis) | baseline-talented; reliable single-target stop |
| Shackle Undead | 9484 | incapacitate (Undead only) | situational PvE |
| Mind Control | 605 | mind control | meme-tier in M+ |

### Recommended changes

1. `app/scoring/cooldowns.py` `(5, "Holy")`: **No changes.** Apotheosis + Divine Hymn at 100% med=12 / med=9 are validated. No additions needed.
2. **Dispel registry** (new): `(5, "Holy") = {Magic, Disease}`. Same as Disc.
3. **Interrupt benchmark override:** **none — exclude from interrupt scoring**. Same as Disc.
4. **Holy Word: Salvation note:** if/when a cast-event detection path is added, register the Salvation cast (265202) — until then, BuffsTable cannot see it.
5. **Talent-gate flags:** none currently needed.

### Top-cohort raw output reference

```
Aggregate over 8 Priest Holy fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    200183      100%        12   Apotheosis  [Apotheosis]
     64843      100%         9   Divine Hymn  [Divine Hymn]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      193065   100%       372   Protective Light
       77489   100%       990   Echo of Light
       64843   100%         9   Divine Hymn (tracked)
      373456   100%         1   Unwavering Will
     1252488   100%        91   Masterful Hunt
      390978   100%       275   Twist of Fate
      114255   100%       235   Surge of Light
       41635   100%       126   Prayer of Mending
     1262766   100%       111   Benediction
       64844   100%        39   Divine Hymn
     1229746   100%        95   Arcanoweave Insight
         586   100%        40   Fade
      405963   100%       450   Divine Image
       21562   100%         4   Power Word: Fortitude
       10060   100%        13   Power Infusion
       19236   100%        12   Desperate Prayer
      200183   100%        12   Apotheosis (tracked)
      121557   100%        26   Angelic Feather
     1252486    88%        14   Hasty Hunt
     1252487    88%         9   Focused Hunt
     1252489    88%        13   Versatile Hunt
      114214    88%         5   Angelic Bulwark
       45242    88%        17   Focused Will
      372617    88%       116   Empyreal Blaze
     1241715    88%       180   Might of the Void
       47788    88%         2   Guardian Spirit
     1236616    75%         3   Light's Potential
     1263727    75%        85   Litany of Lightblind Wrath
     1277389    75%         1   Vantus Rune: Radiant
     1265140    75%        23   Refreshing Drink
```

---

## Spec: Shadow

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 194249  | Voidform | yes                  | 100%        | 13          | keep |
| 10060   | Power Infusion | no              | 100%        | 13          | **add candidate (see notes)** |
| 47585   | Dispersion | no                  | 100%        | 3           | leave (1.5min personal defensive — same Barkskin saturation concern) |
| 232698  | Shadowform | no                  | 100%        | 15          | leave (passive form, always up — saturation guaranteed) |
| 1280172 | Shadowfiend | no                 | 100%        | 36          | leave (pet aura — 36 uses likely reflects pet-applied buff, not Priest CD presses) |
| 391109  | Dark Ascension | no              | not seen in top-30 | — | leave dropped (Pass-2 decision validated — alt to Voidform, not in current meta) |
| 450193  | Entropic Rift | no               | 88%         | 48          | leave (Voidweaver hero-talent rotational proc, not pressed CD) |
| 373213  | Insidious Ire | no               | 100%        | 530         | leave (passive stack tracker) |
| 375981  | Shadowy Insight | no              | 100%        | 163         | leave (passive proc tracker) |
| 120644  | Halo | no                          | not seen in top-30 | — | leave (cast spell, no persistent self-aura — same hard-cast pattern) |

**Notes on splits / alt-builds:**
- **Voidform at 100% med=13** validates the Pass-2 fix (replacing Void Eruption 228260 with Voidform 194249). Keep as-is.
- **Power Infusion (10060) at 100% med=13** is a real pressed CD on Shadow. The audit guidance flagged the Twins of the Sun glyph implications: top Shadow Priests in M+ either:
  1. Self-cast PI for personal damage (most M+ runs).
  2. Glyph PI to give to a different DPS (more common in raid; rare in M+ pug-tier play, but seen in coordinated push groups).

  At med=13 across 8/8 logs, the press is happening — what we cannot tell from BuffsTable alone is whether the Shadow Priest cast it on themselves or received it from another priest. For scoring purposes that distinction may not matter (the CD is being pressed, the aura lands on someone, the priest's button is on cooldown). **Recommend adding `(10060, "Power Infusion", 13, "offensive")` to Shadow** as a high-signal pressed CD. Note that this would also imply tracking PI on Disc and Holy for class-wide consistency — flag for codification decision.
- **Dark Ascension (391109)** removed in Pass 2 — sampler confirms zero appearance in current top-cohort. Voidform is the universal pick. No alt-build needed.
- **Voidweaver vs Archon hero talent split:** Entropic Rift (450193) and Alnscorned Essence (1266687) at 88% indicate most of the cohort is Voidweaver. Archon-specific signature auras don't surface in the top-30 reliably enough to indicate split tracking. If Archon becomes meta in a future patch, revisit.
- **Mindbender / Shadowfiend (1280172) at 100% med=36** is unusual — that's a lot of "uses" for a 1-3 min CD. The aura is likely the periodic shadow-damage proc applied while the fiend is up, not the priest's button press count. **Leave untracked.** If we want to track Shadowfiend press, it needs the cast-event path (same as Salvation, Halo).
- **Halo (120644)** is mentioned in audit guidance but it's a hard-cast with no persistent self-aura. Same pattern as Wake of Ashes / Frozen Orb. Cannot be tracked via BuffsTable.

### Interrupts

- **Spell name (id):** `Silence` (15487) — **Shadow-only**.
- **Cast type:** instant
- **Sample observed kicks per fight (median):** not derivable from BuffsTable (Silence applies a debuff to the target, not a self-aura). Needs cast-event sample to validate the engine's `interrupts / 15` denominator for Shadow.
- **Recommended expected count for scoring:** 15 (DPS denom in `_score_utility_dps_tank`). Standard. Silence is a 45s CD vs the ~15s typical melee kick — Shadow Priest M+ kick volume is structurally lower. Flag for cast-event audit; a Shadow-specific override (e.g. denom of 8-10) may be warranted if real-world median is well below 15.
- **No-baseline-kick callout:** Shadow IS the only Priest spec with a kick. Disc and Holy correctly excluded from `HEALER_SPECS_WITH_INTERRUPT`.

### Dispels

- **In-spec dispel ability:** `Dispel Magic` (528).
  - **Defensive (ally-targeted):** removes Magic from allies. **Cleanse mode.**
  - **Offensive (enemy-targeted):** purges Magic-school buffs from enemies. **Offensive purge mode.**
- **Schools cleansable on allies:** `{Magic}` (defensive cleanse mode only)
- **Schools the engine should credit this spec for:** `{Magic}` (defensive only — the offensive-purge path is a different scoring axis if/when added)
- **Notes:**
  - Dispel Magic on Shadow is **dual-mode** — the BRM-lesson-3 dispel registry must encode the ally-targeted defensive mode for the cleanse credit. Offensive purges (analogous to Tranq Shot, Mass Dispel offensive) are a separate utility category.
  - Shadow does NOT cleanse Disease (unlike Disc/Holy's Purify). This is a real per-spec difference: Disc dispels Magic+Disease defensively, Shadow dispels Magic only.
  - **Mass Dispel (32375)** also available to Shadow — same notes as Disc/Holy. Group/AoE dispel, ambiguous direction.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Psychic Scream | 8122 | fear (AoE, 8s) | baseline |
| Psychic Horror | 64044 | stun (single-target, 4s) | talent-gated, Shadow-favored |
| Silence | 15487 | silence | baseline interrupt (Shadow-only) — counts as the kick |
| Shackle Undead | 9484 | incapacitate (Undead only) | situational PvE |
| Mind Control | 605 | mind control | meme-tier in M+ |

### Recommended changes

1. `app/scoring/cooldowns.py` `(5, "Shadow")`: **add `(10060, "Power Infusion", 13, "offensive")`**. Keep Voidform as-is.
2. **Class-wide PI tracking decision:** if PI is tracked on Shadow, also track it on Disc and Holy for consistency (med=13 across all three specs). Flag for codification — see Open Questions.
3. **Dispel registry** (new): `(5, "Shadow") = {Magic}` (defensive cleanse mode). Note offensive-purge mode as a separate category if/when scored.
4. **Interrupt benchmark override:** **flag for cast-event sample.** Silence is 45s CD; if real-world median kicks/run is significantly below 15, a Shadow-specific denom override (e.g. 8-10) is warranted to avoid unfairly penalizing the spec.
5. **Talent-gate flags:** none currently needed. Voidform is universal; PI is universal-class.

### Top-cohort raw output reference

```
Aggregate over 8 Priest Shadow fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    194249      100%        13   Voidform  [Voidform]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
       10060   100%        13   Power Infusion
      375981   100%       163   Shadowy Insight
      373213   100%       530   Insidious Ire
       21562   100%         6   Power Word: Fortitude
      193065   100%        12   Protective Light
      377066   100%       201   Mental Fortitude
      390978   100%      1074   Twist of Fate
       19236   100%        13   Desperate Prayer
      426401   100%        15   Focused Will
      232698   100%        15   Shadowform
      393919   100%       192   Screams of the Void
     1243113   100%       123   Horrific Vision
       47585   100%         3   Dispersion
      121557   100%        12   Angelic Feather
      373316   100%        20   Idol of Y'Shaarj
       65081   100%        46   Body and Soul
     1236616   100%         5   Light's Potential
     1229746   100%       107   Arcanoweave Insight
     1280172   100%        36   Shadowfiend
     1243114   100%        76   Vision of N'Zoth
          17   100%        47   Power Word: Shield
         586   100%        38   Fade
       15286   100%        12   Vampiric Embrace
      194249   100%        13   Voidform (tracked)
      373277   100%        69   Thing from Beyond
       15407   100%       264   Mind Flay
      373276   100%      1135   Idol of Yogg-Saron
     1266687    88%       883   Alnscorned Essence
      450193    88%        48   Entropic Rift
     1266686    88%        57   Alnsight
```

---

## Open questions for review

1. **Class-wide Power Infusion tracking:** PI (10060) appears at 100% med=13 across all three Priest specs. Tracking it would be the highest-signal class-wide CD. Counter-argument: PI is "give-and-receive" via Twins of the Sun glyph, so the aura on a priest could be self-cast or received from another priest — for Disc/Holy especially, you may receive PI from a Shadow Priest in your group rather than press it yourself. Recommend Logan decide: track PI on all three specs (consistency), only Shadow (clean self-press signal), or none (avoid the self-vs-received ambiguity).
2. **Evangelism on Disc:** confident add at `(472433, "Evangelism", 15, "offensive")`. No ambiguity — it's a self-cast self-aura central to the Disc rotation.
3. **Holy Word: Salvation invisibility:** Salvation (265202) is the audit-flagged signature Holy capstone but doesn't appear in the priest's BuffsTable. Likely lands on each ally as a HoT, not on the priest. If/when a cast-event detection path is added, register Salvation there. Until then, BuffsTable can't see it — Apotheosis + Divine Hymn cover the active Holy CD story.
4. **Shadow interrupt denom:** Silence (15487) on a 45s CD is structurally lower-volume than melee kicks (15-30s CD). The current DPS denom of 15 in `_score_utility_dps_tank` may unfairly penalize Shadow. Recommend a cast-event sample of `15487 Silence` for the same top-cohort — if median kicks/run is ≤8, a Shadow-specific override is warranted.
5. **Mass Dispel as utility category:** all three Priest specs have Mass Dispel (32375), an AoE 5-target Magic dispel. Currently the engine only credits single-target cleanses. Flag for a future "AoE / group dispel" utility credit if expanded — Priest is the sole class with this tool and currently goes uncredited.
6. **Shadowfiend press count on Shadow:** the 1280172 aura at med=36 is too high to be the priest pressing the button (Shadowfiend is a 3min CD). It's almost certainly a periodic damage aura applied while the fiend is up. If we want Shadowfiend press tracking, it needs the cast-event path. Same applies to Disc Mindbender.

## Confidence

- **Discipline:** 8 distinct fights, +19 to +20 keys. **High confidence.** Evangelism add is unambiguous (100% consensus, clean self-aura). Ultimate Penitence holds at med=4. Power Infusion observation is consistent with class-wide pattern.
- **Holy:** 8 distinct fights, +18 to +19 keys. **High confidence** that no edits are needed — both tracked CDs at 100%. Salvation invisibility is a structural BuffsTable limitation, not a sampler miss.
- **Shadow:** 8 distinct fights, +20 to +21 keys. **High confidence** on Voidform validation and PI add candidate. Lower confidence on the interrupt benchmark (need cast-event data) and the Shadowfiend aura interpretation (need cast-event data).

All three specs cleared the 5-fight minimum without needing the retry pass.
