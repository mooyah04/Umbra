# Evoker Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 distinct top player per active dungeon (8 dungeons), Augmentation / Devastation / Preservation
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Evoker" --spec "{Spec}" --samples-per-dungeon 1 --top-n 8`

Cohort key range observed: **+18 to +22** (consistent with Midnight S1 top tier). Eight distinct fights collected per spec — minimum-confidence threshold met for all three specs without needing a retry pass.

Class context: Evoker (class_id 13) is a Dracthyr-only class with three specs split across the role triangle. Augmentation is a support DPS (group-uplift damage already wired into the engine elsewhere — not re-litigated here). Devastation is a ranged DPS. Preservation is a healer. All three share several baseline auras (Hover, Obsidian Scales, Renewing Blaze) and the empower mechanic (Fire Breath, Dream Breath, Eternity Surge, Disintegrate-as-channel).

---

## Spec: Augmentation

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 395296  | Ebon Might | yes               | 100%        | 54          | keep |
| 442204  | Breath of Eons | yes           | 100%        | 27          | keep |
| 459574  | Imminent Destruction | no      | 100%        | 27          | leave (passive proc/buff stack — see notes) |
| 459152  | Rumbling Earth | no            | 100%        | 61          | leave (passive Chronowarden hero-talent stack) |
| 374349  | Renewing Blaze | no            | 100%        | 16          | leave (rotational personal defensive — saturation risk) |
| 363916  | Obsidian Scales | no           | 0% (not seen on Aug top-30 here) | — | leave |

**Notes on splits / alt-builds:**
- Both currently-tracked Aug majors at 100% consensus across 8/8 logs. Pass-2 fixes (replacing the Time Skip line, locking 395296 as the Ebon Might self-aura) held up perfectly.
- **Ebon Might (395296) at med=54** is high but tracks the per-application aura on the Aug evoker, not the group-uplift damage. The engine already handles Aug's group-uplift contribution as a separate scoring axis (per project memory `project_rotation_and_aug_scoring.md`); this entry remains a clean "did the player press their major" signal and should NOT be re-scored as group damage.
- **Imminent Destruction (459574)** appears at 100% med=27. This matches the cadence of a per-Eruption proc rather than a manually-pressed CD; it's the Chronowarden hero-talent passive that empowers Mass Eruption. Adding it would saturate the category (BRM-lesson Barkskin pattern). Leave.
- **Rumbling Earth (459152)** at 100% med=61 is similarly a Mass Eruption stack/tracker, not a pressed CD.
- **No Time Skip / Temporal Anomaly aura** appeared above the noise floor — confirms the Pass-2 removal was correct. Aug's "press CD" story is genuinely a 2-major-CD spec via the BuffsTable lens.
- **Anti-Magic Zone (145629) at 100% med=3** in Aug's buff list is from a Blood DK groupmate's AMZ landing on this Aug — not Aug's own ability. Cross-actor contamination expected and ignored.

### Interrupts

- **Spell name (id):** `Quell` (351338)
- **Cast type:** instant (1.5s GCD action, no cast time, despite being technically classed as an empower in some patch notes)
- **Sample observed kicks per fight (median):** not derivable from BuffsTable sampler — Quell leaves no aura.
- **Recommended expected count for scoring:** 15 (DPS denom in `_score_utility_dps_tank`). Standard.
- **Baseline-kick callout:** Quell is baseline on all three Evoker specs. No engine override needed for Aug — it's a DPS spec, gets the standard DPS denom.

### Dispels

- **In-spec dispel ability:** `Cauterizing Flame` (374251) (baseline cross-spec) and `Expunge` (365585) (Aug-specific).
  - **Cauterizing Flame** removes Bleed + Poison + Disease + Curse from allies. Notably **NOT Magic** — this is a non-magic 4-school cleanse, the broadest non-magic cleanse footprint in the game.
  - **Expunge** removes Poison from allies (single-school cleanse). Often picked redundantly with Cauterizing Flame in current Aug builds for a faster Poison-only press without the longer Cauterizing Flame cooldown.
- **Schools cleansable on allies:** `{Bleed, Poison, Disease, Curse}` (via Cauterizing Flame; Expunge is a Poison-only subset)
- **Schools the engine should credit this spec for:** `{Bleed, Poison, Disease, Curse}` — Aug carries the broadest non-magic defensive cleanse in the game.
- **Notes:**
  - Aug is the **only DPS spec in the game with Curse + Disease + Bleed cleanse**. This is meaningful M+ utility — a healer with an Aug in the group can offload Curse/Disease cleanses to the Aug, which rotates dispel work off the healer's GCDs. The engine's per-spec dispel registry must encode this or Aug looks under-credited vs every other DPS spec.
  - **Expunge (365585)** is technically also available to Devastation in the spell list, but Aug builds favor it more often. For the registry, both Aug and Dev should get Poison cleanse via Expunge; the differentiator is whether Cauterizing Flame is used — which sample data confirms it is on both.
  - Evokers don't have a dedicated offensive purge (no Tranq Shot / Mass Dispel offensive analog).

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Sleep Walk | 360806 | incapacitate (single-target, ~20s, breaks on damage) | talent-gated, primarily Pres tool but available |
| Landslide | 358385 | root (AoE line) | talent-gated |
| Tail Swipe | 368970 | knockback (rear cone) | baseline racial |
| Wing Buffet | 357214 | knockback (front cone) | baseline racial |

Most Evoker CC is movement-disrupting (knockbacks/roots) rather than spell-school lockouts. This is intentional for Dracthyr kit design; affects how the engine should weight Evoker CC contributions if/when CC enters per-spec scoring.

### Recommended changes

1. `app/scoring/cooldowns.py` `(13, "Augmentation")`: **No drops, no adds.** Ebon Might + Breath of Eons both at 100% consensus.
2. **Dispel registry** (new): `(13, "Augmentation") = {Bleed, Poison, Disease, Curse}`. Critical — this is the broadest non-magic cleanse footprint and missing it under-credits Aug's utility significantly.
3. **Interrupt benchmark override:** none. DPS default of 15 stands.
4. Talent-gate flags: none currently needed. Ebon Might and Breath of Eons are universal in current builds.

### Top-cohort raw output reference

```
Aggregate over 8 Evoker Augmentation fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    395296      100%        54   Ebon Might  [Ebon Might]
    442204      100%        27   Breath of Eons  [Breath of Eons]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      404381   100%         2   Defy Fate
     1261395   100%        26   Command Squadron
     1263318   100%        90   The Wind Awoken
      381748   100%         2   Blessing of the Bronze
      442204   100%        27   Breath of Eons (tracked)
      459574   100%        27   Imminent Destruction
      370666   100%         5   Rescue
      374349   100%        16   Renewing Blaze
        8936   100%       457   Regrowth
     1252613   100%        27   Command Squadron
     1242775   100%        10   Farstrider's Step
      406043   100%        22   Nourishing Sands
      459152   100%        61   Rumbling Earth
     1259171   100%        27   Duplicate
     1261393   100%        26   Command Squadron
      145629   100%         3   Anti-Magic Zone
      441248   100%       165   Unrelenting Siege
     1236616   100%         6   Light's Potential
      403264   100%       113   Black Attunement
     1229746   100%       123   Arcanoweave Insight
      408005   100%       174   Momentum Shift
      375802   100%        11   Burnout
     1265145   100%        23   Refreshing Drink
     1265140   100%        34   Refreshing Drink
      438588   100%       158   Mass Eruption
      358267   100%        58   Hover
      392268   100%       187   Essence Burst
      357208   100%        52   Fire Breath
        1126   100%         3   Mark of the Wild
         774   100%        48   Rejuvenation
```

---

## Spec: Devastation

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 375087  | Dragonrage | yes               | 100%        | 40          | keep |
| 370553  | Tip the Scales | no            | 100%        | 13          | leave (empower modifier — see notes) |
| 363916  | Obsidian Scales | no           | 100%        | 28          | leave (1min personal defensive — saturation risk) |
| 374227  | Zephyr | no                    | 88%         | 5           | leave (group defensive — short, not "major" press) |
| 1271783 | Rising Fury | no               | 100%        | 69          | leave (Dragonrage stack tracker, not pressed) |
| 1271799 | Risen Fury | no                | 100%        | 13          | leave (Flameshaper hero-talent passive proc) |

**Notes on splits / alt-builds:**
- Dragonrage (375087) is the only currently-tracked aura, at 100% consensus — Pass-2 baseline holds.
- **Tip the Scales (370553) at 100% med=13** is the most defensible "should we add this?" candidate for Dev. It's a press: an active CD that converts the next empower into an instant max-rank cast. However, treating it as a major CD has two issues:
  1. Its value is gated by the *next* empower cast — it's a setup CD, not a damage window in itself. Tracking it as a CD risks double-counting against players who press it but don't follow with the right empower.
  2. Median 13 uses across an M+ run is roughly 1 per 3min — already saturating against any reasonable expected-uptime bench. Including it would push Dev's `cooldown_usage` toward 100 the same way Resto Druid Barkskin did pre-Pass-3. **Recommend: leave Tip the Scales out** until we have a cast-event detection path that pairs it with the empower it sets up.
- **Obsidian Scales / Zephyr / Renewing Blaze** are all rotational personal/group defensives that every Dev presses on cooldown. Same saturation logic applies.
- **No Time Skip aura** appeared at any meaningful consensus — confirms it's a niche talent pick on Dev currently. No alt-build pair needed for Dragonrage.
- **Eternity Surge / Fire Breath / Disintegrate** are rotational (channels and empowers), not majors. The sampler picks them up as buff-table residue but they're rotational APM, not press-on-CD majors. Correctly excluded.

### Interrupts

- **Spell name (id):** `Quell` (351338)
- **Cast type:** instant. 40s CD. Despite being filed under Evoker's empower-style spell organization in some Blizzard documentation, Quell is a hard-coded baseline interrupt — instant cast, applies a 4s school lockout. Confirmed baseline on Devastation.
- **Sample observed kicks per fight (median):** not derivable from BuffsTable sampler.
- **Recommended expected count for scoring:** 15 (DPS denom). Standard. Note: Quell's 40s CD is longer than Counterspell/Wind Shear (24s/12s), so Dev Evokers will naturally land fewer kicks per fight than e.g. a Wind Shear-equipped Resto Shaman. The engine's `interrupts / 15` denom already absorbs that mostly, but flag for cast-event audit if Dev distribution skews low on the utility category.

### Dispels

- **In-spec dispel ability:** `Cauterizing Flame` (374251). Removes Bleed + Poison + Disease + Curse from allies. Same baseline cross-spec ability as Aug.
  - **Expunge (365585)** — Devastation also has access in the talent tree; whether it's picked depends on the build. The sampler did not surface Expunge consumption on this cohort but its absence in BuffsTable is unsurprising (it's an instant cast with no aura on the caster).
- **Schools cleansable on allies:** `{Bleed, Poison, Disease, Curse}` (via Cauterizing Flame; Expunge adds redundant Poison cleanse if talented)
- **Schools the engine should credit this spec for:** `{Bleed, Poison, Disease, Curse}` — same as Aug.
- **Notes:**
  - Same cross-spec story as Aug. Cauterizing Flame's Bleed+Poison+Disease+Curse coverage is unique among ranged DPS specs in the game. Failing to credit Dev for it would treat Dev as if it had no defensive cleanse, which is wrong.
  - No Magic dispel on Devastation. Magic cleanse remains Pres-only on Evoker.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Sleep Walk | 360806 | incapacitate | talent-gated, less common on Dev |
| Landslide | 358385 | root (AoE line) | talent-gated |
| Tail Swipe | 368970 | knockback | baseline racial |
| Wing Buffet | 357214 | knockback | baseline racial |

### Recommended changes

1. `app/scoring/cooldowns.py` `(13, "Devastation")`: **No drops, no adds.** Dragonrage at 100% consensus, no untracked CDs above the saturation/setup-CD threshold.
2. **Dispel registry** (new): `(13, "Devastation") = {Bleed, Poison, Disease, Curse}`. Mirror Aug's entry.
3. **Interrupt benchmark override:** none recommended at this audit. Flag for cast-event distribution check (Quell's 40s CD vs the engine's `/15` denom may produce systemically lower DPS-utility scores for Dev/Aug; that's a tuning question, not an ID question).
4. Talent-gate flags: none.

### Top-cohort raw output reference

```
Aggregate over 8 Evoker Devastation fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    375087      100%        40   Dragonrage  [Dragonrage]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1271783   100%        69   Rising Fury
      381748   100%         4   Blessing of the Bronze
      359618   100%       409   Essence Burst
      390386   100%         7   Fury of the Aspects
     1235111   100%         1   Flask of the Shattered Sun
      376850   100%       211   Power Swell
      356995   100%       319   Disintegrate
      370553   100%        13   Tip the Scales
      374349   100%        15   Renewing Blaze
     1271799   100%        13   Risen Fury
     1241715   100%       178   Might of the Void
      375087   100%        40   Dragonrage (tracked)
      370901   100%        79   Leaping Flames
     1265871   100%        99   Azure Sweep
     1229746   100%       111   Arcanoweave Insight
      358267   100%        52   Hover
      363916   100%        28   Obsidian Scales
      375234   100%         4   Time Spiral
      375802   100%       200   Burnout
      106898    88%         3   Stampeding Roar
      410355    88%        59   Stretch Time
     1242775    88%        12   Farstrider's Step
        1126    88%         4   Mark of the Wild
      374227    88%         5   Zephyr
      155777    75%        47   Rejuvenation (Germination)
       33763    75%        68   Lifebloom
     1236616    75%         5   Light's Potential
     1265140    75%        32   Refreshing Drink
         774    75%        62   Rejuvenation
       48438    75%       127   Wild Growth
```

---

## Spec: Preservation

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 363534  | Rewind | yes                   | 100%        | 3           | keep |
| 370562  | Stasis | yes                   | 75%         | 16          | keep — alt-build path (see notes) |
| 355941  | Dream Breath | no              | 100%        | 88          | leave (rotational empower channel, not press) |
| 367364  | Reversion | no                 | 100%        | 112         | leave (rotational HoT) |
| 364343  | Echo | no                      | 100%        | 218         | leave (rotational buff/stack) |
| 357170  | Time Dilation | no             | 88%         | 8           | flag — see notes |
| 370553  | Tip the Scales | no            | 100%        | 19          | leave (empower modifier) |

**Notes on splits / alt-builds:**
- Rewind (363534) at 100% med=3 — exactly the cadence of a 3min raid-save CD over a typical M+ pull count. Universal on Pres. Keep tracked, expected_uptime=3 is correct.
- **Stasis (370562) at 75% med=16** is the audit's most actionable Pres finding. Two of eight top Pres logs (Yzmir-Ragnaros, Tritovoker-Twisting Nether by visual inspection of the dropouts) didn't run with Stasis up — likely a Chronowarden vs Flameshaper hero-talent split, where the non-Stasis build is leaning on a different empower-burst pattern. The current 75% sits exactly in the audit's "alt-build path" zone (50%-90%). Recommendation: **keep tracking, mark as talent-gated** so the talent-aware skip in `_get_cooldown_usage` excludes Stasis from scoring on the runs where the player didn't take it. Expected_uptime=17 still reasonable for the 75% who do take it.
- **Time Dilation (357170) at 88% med=8** is interesting. It's a 1-minute defensive CD that grants temporal protection to an ally. The 88% consensus is borderline — it's a press, not a passive proc. Two considerations against tracking:
  1. The healer-utility category already credits this kind of "external" defensive elsewhere if/when wired in (analogous to Pain Suppression / Ironbark / Life Cocoon).
  2. Rewind already covers the "did the Pres press their major saves" question.

  Recommend: **leave untracked for now**. Flag in open questions for Logan to weigh in on whether a second tracked Pres CD is desirable or if Rewind+Stasis is the right shape.
- **Dream Breath, Reversion, Echo** are rotational Hots/empowers. The 80+ median uses confirm they're rotational APM, not pressed CDs. Adding them would saturate the category. Correctly excluded.
- **No Spiritbloom / Eternity Surge auras** at major-CD consensus — these are situational empowers, not the spec's signature CD story. Correctly excluded.

### Interrupts

- **Spell name (id):** `Quell` (351338)
- **Cast type:** instant. 40s CD. Baseline.
- **Sample observed kicks per fight (median):** not derivable from BuffsTable sampler — Quell leaves no aura on the caster. Would need cast-event sampling against the same cohort.
- **Recommended expected count for scoring:** if Pres is added to `HEALER_SPECS_WITH_INTERRUPT`, the healer denom is 10 (`_score_utility_healer`'s `interrupts / 10`).
- **Healer-baseline-kick callout — open question, not assertion:** Preservation is currently **NOT** in `HEALER_SPECS_WITH_INTERRUPT` in `roles.py`. Quell appears to be baseline on all three Evoker specs in current Midnight content (per spell tooltip behavior and standard kit understanding), and the high-key M+ Pres community routinely contributes kicks alongside DPS. **However**, given the recent MW-audit error where the agent wrongly claimed MW had a baseline kick (corrected back out per `roles.py` comment), this audit will NOT recommend adding Pres without harder evidence than tooltip reading. The BuffsTable sampler can't validate Quell usage frequency. Concrete next step before changing `roles.py`: a cast-event sample of `351338 Quell` against the same Pres top-cohort would confirm whether top Pres Evokers actually press it at meaningful frequency (>=5 kicks/run median). **Until that evidence lands, this gets flagged in Open Questions, NOT recommended.**

### Dispels

- **In-spec dispel ability:** `Naturalize` (360823) — Pres-only, removes Magic + Poison from allies.
  - **Cauterizing Flame (374251)** — also baseline on Pres, removes Bleed + Poison + Disease + Curse from allies.
  - Combined defensive cleanse footprint on Pres: **Magic + Poison + Disease + Curse + Bleed** (5-school coverage, the broadest of any healer in the game).
- **Schools cleansable on allies:** `{Magic, Poison, Disease, Curse, Bleed}`
- **Schools the engine should credit this spec for:** `{Magic, Poison, Disease, Curse, Bleed}`
- **Notes:**
  - **Pres has the widest defensive cleanse coverage of any healer.** Holy Paladin gets Magic+Poison+Disease (3); Resto Druid gets Curse+Poison (2); Mistweaver gets Magic+Poison+Disease (3); Disc/Holy Priest gets Magic+Disease (2); Resto Shaman gets Magic+Curse (2); Pres Evoker gets all five schools. The dispel-school registry must encode the full set or Pres looks systematically under-credited.
  - **No offensive purge** on Pres (Evokers lack a Tranq Shot / Purge / Mass Dispel offensive analog).
  - The two-spell layered cleanse is a real M+ design feature: Naturalize handles the high-priority Magic dispels, Cauterizing Flame handles the mid-priority Curse/Disease/Poison/Bleed pile. Crediting only one of them undersells the spec.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Sleep Walk | 360806 | incapacitate (single-target, breaks on damage) | talent — most common on Pres of the three specs |
| Landslide | 358385 | root (AoE line) | talent-gated |
| Tail Swipe | 368970 | knockback | baseline racial |
| Wing Buffet | 357214 | knockback | baseline racial |

### Recommended changes

1. `app/scoring/cooldowns.py` `(13, "Preservation")`:
   - **Keep Rewind (363534).** Universal at 100% consensus.
   - **Keep Stasis (370562) but mark talent-gated.** 75% consensus signals an alt-build split. The talent-aware skip in `_get_cooldown_usage` already excludes auras the player's BuffsTable doesn't surface, so the 25% who don't run Stasis won't be punished.
   - **Do not add** Time Dilation, Dream Breath, Reversion, or Tip the Scales.
2. **Dispel registry** (new): `(13, "Preservation") = {Magic, Poison, Disease, Curse, Bleed}`. Critical — the broadest cleanse footprint among healers.
3. **Interrupt benchmark override / `HEALER_SPECS_WITH_INTERRUPT`:** **DO NOT add Pres without cast-event evidence.** Flagged for Logan in Open Questions. The MW audit precedent (where the agent wrongly added MW based on confidence in a baseline kick that turned out to be CC, not a kick) is an explicit warning here.
4. Talent-gate flags: tag `(370562, "Stasis")` so the talent-aware skip handles the 25% Chronowarden-style build that drops it.

### Top-cohort raw output reference

```
Aggregate over 8 Evoker Preservation fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    363534      100%         3   Rewind  [Rewind]
    370562       75%        16   Stasis  [Stasis] <- check alt-build split

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      358267   100%        51   Hover
     1229746   100%        91   Arcanoweave Insight
      363916   100%        31   Obsidian Scales
      370553   100%        19   Tip the Scales
      431654   100%       248   Primacy
      355941   100%        88   Dream Breath
     1256579   100%       287   Merithra's Blessing
      367364   100%       112   Reversion
      374227   100%         9   Zephyr
      362877   100%       713   Temporal Compression
      431872   100%        51   Temporality
      357208   100%        56   Fire Breath
      381748   100%         5   Blessing of the Bronze
      373267   100%       101   Lifebind
      356995   100%       133   Disintegrate
      364343   100%       218   Echo
      370901   100%        63   Leaping Flames
      372470   100%       179   Scarlet Adaptation
      409895   100%        57   Verdant Embrace (Reverberations)
      369299   100%       404   Essence Burst
      366155   100%        76   Reversion
      390386   100%         7   Fury of the Aspects
      376788   100%        17   Dream Breath
      429460   100%        13   Warp
      431698   100%        19   Temporal Burst
      363534   100%         3   Rewind (tracked)
      436036   100%        34   Warp
      355936   100%        67   Dream Breath
      357170    88%         8   Time Dilation
     1241715    88%       194   Might of the Void
```

---

## Open questions for review

1. **Preservation Quell as a healer-with-baseline-interrupt:** Pres is currently NOT in `HEALER_SPECS_WITH_INTERRUPT`. Quell is widely understood to be baseline on all three Evoker specs (instant 40s CD school lockout). However, after the MW audit error precedent, this audit explicitly avoids recommending the `roles.py` change without cast-event evidence. **Concrete ask:** before any change, run a cast-event sampler against the same 8-fight Pres top-cohort filtering for `351338 Quell` casts. If median kicks/run >= 5, add `(13, "Preservation")` to `HEALER_SPECS_WITH_INTERRUPT` in a separate change. If median < 5, leave Pres out and absorb the utility credit elsewhere.

2. **Stasis talent-gate alt-build pair:** Stasis at 75% suggests Chronowarden (with Stasis-banking) vs Flameshaper (without) hero-talent split. There's no "alternate Stasis" aura to track for the 25% who skip it — they're just leaning harder on rotational throughput rather than a banked-spell burst. The talent-aware skip handles this cleanly without requiring a second tracked aura. **Confirm understanding:** is dropping Stasis on certain Pres builds actually a hero-talent thing, or is it a key-level / fight-length thing where some logs just didn't enter Stasis range during the run? A second-pass sample (`--samples-per-dungeon 2 --top-n 12`) could disambiguate.

3. **Aug Tip the Scales / Time Dilation cross-spec utility:** Tip the Scales (370553) appeared at 100% on both Aug and Pres but zero on Dev's tracked-CD context. It's a setup CD for empowers, not a damage window itself. If the engine ever adds a "setup-CD pairing" detection path (track the next empower cast within X seconds of a Tip press), this is the canonical Evoker example.

4. **Interrupt denom calibration for Quell-specific specs:** Quell's 40s CD is significantly longer than Counterspell (24s) or Wind Shear (12s). Across the three Evoker specs, the engine's `interrupts / 15` (DPS) and `interrupts / 10` (healer) denoms may produce systematically lower utility scores than for Mage/Shaman counterparts even when the Evoker plays optimally. This is a tuning question for the cast-event audit pass — not actionable from BuffsTable data.

5. **Cauterizing Flame / Expunge cross-spec coverage:** the dispel registry entries proposed here treat Cauterizing Flame as baseline on all three Evoker specs, with Expunge as a Poison-redundant talent for Aug specifically. Confirm that the Cauterizing Flame schools are correct as `{Bleed, Poison, Disease, Curse}` — the schools list in the WoW spell tooltip is what this audit relies on, but registry entries that get any one school wrong systemically break the credit math.

## Confidence

- **Augmentation:** 8 distinct fights, +21 to +22 keys. **High confidence** on the cooldown story (Pass-2 fixes held; no edits). **Highest-impact deliverable** is the dispel registry entry — Aug's 4-school non-magic cleanse is unique among DPS and missing it under-credits the spec significantly.
- **Devastation:** 8 distinct fights, +18 to +19 keys. **High confidence** on cooldown story (single CD, no untracked candidates above the saturation/setup-CD threshold). Same dispel registry impact as Aug.
- **Preservation:** 8 distinct fights, +19 to +20 keys. **High confidence** on Rewind and on the talent-gate flag for Stasis. **Lower confidence** on the Quell/`HEALER_SPECS_WITH_INTERRUPT` question, which is intentionally flagged not asserted given the MW audit precedent. Dispel registry entry is the highest-impact deliverable: Pres's 5-school cleanse is the broadest in the healer pool.

All three specs cleared the 5-fight minimum without needing the retry pass.
