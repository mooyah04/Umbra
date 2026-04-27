# Hunter Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent (Batch 3)
**Sample depth:** 1 report per dungeon, top-8 per dungeon scan, 8 active-season Midnight S1 dungeons (Windrunner Spire, Maisara Caverns, Magister's Terrace, Algeth'ar Academy, Nexus-Point Xenas, Skyreach, Pit of Saron, Seat of the Triumvirate)
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Hunter" --spec "{BeastMastery|Marksmanship|Survival}" --samples-per-dungeon 1 --top-n 8`
**Fights sampled:** Beast Mastery 8 / Marksmanship 8 (one with 0 auras due to a buffsTable empty-fetch — effectively 7) / Survival 8

> Class IDs verified from `app/scoring/roles.py`: Hunter is class_id `3`. All three specs are DPS, all use the `dps` metric. **Note for tooling:** WCL's `characterRankings` query takes Beast Mastery as `BeastMastery` (no space). The internal `SPEC_MAJOR_COOLDOWNS` key is `(3, "Beast Mastery")` (with space) — the sampler ran with the wireform key, so its "Currently tracked" diff was empty. The actual Bestial Wrath / Call of the Wild tracking-state diff is computed by hand below.
>
> All three Hunter specs share the same off-spec dispel pattern: **Tranquilizing Shot (19801)** is an offensive purge (Enrage + Magic from enemies), NOT a defensive cleanse. Hunters have **no defensive cleanse on allies** in any spec.

---

## Spec: Beast Mastery

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 19574   | Bestial Wrath | yes            | 100%        | 53          | keep |
| 359844  | Call of the Wild | yes         | 0%          | 0           | **drop (not in top 60 buffs across 8 top-cohort BMs; appears displaced by the Pack Leader hero-tree's Howl/Wyvern's Cry kit)** |
| 268877  | Beast Cleave | no             | 100%        | 172         | skip (Multi-Shot proc / rotational AoE buff, not a major CD) |
| 246152  | Barbed Shot | no              | 100%        | 430         | skip (rotational ~12s focus generator with stacking pet buff; not a major CD) |
| 472640  | Hogstrider | no               | 50%         | 150         | skip (Pack Leader hero-talent passive on Pack Leader builds; not a player-pressed CD) |
| 459731  | Huntmaster's Call | no         | 50%         | 217         | skip (Pack Leader hero-talent proc summon; passive) |
| 1258345 / 1258338 | Stampede / Stampede! | no | 50%      | 55          | hold (Sentinel hero-talent talented effect; alt-build path, not universal) |

**Notes on splits / alt-builds:**
- **Bestial Wrath (19574) at 100% with med=53** confirms the existing track. 53 uses on a ~2min CD over a ~30min M+ run is over-saturated relative to the 25 expected uptime currently in `cooldowns.py` — but BM's Bestial Wrath aura is a 15s window with multiple Aspect of the Wild / Barbed Shot extensions, so 53 individual aura-use events across hits/refreshes is expected. The expected-uptime number is more about scoring shape than a strict use-count target; flagging this as worth a re-look but not an immediate edit.
- **Call of the Wild (359844) at 0%** is the headline finding. It does not appear in the top 60 buffs across any of 8 top-cohort BM hunters. CotW is a Pack Leader hero-talent that summons additional pets (a pet-summon pattern that won't surface on the Hunter's BuffsTable — same reason Feral Spirit was dropped from Enhancement Shaman in Pass 2). What DOES surface in top BM cohorts is the cluster of Pack Leader passive auras: Howl of the Pack Leader (471877/472324/472325/471878), Wyvern's Cry (471881), and Hogstrider (472640). None of these are press-on-cooldown CDs — they're passive procs from the Pack Leader hero tree. Recommend dropping Call of the Wild from BM tracking; without a cast-event detection path BM is left with one tracked CD (Bestial Wrath), which is honest.
- **No alt-build CD pair surfaced.** The Pack Leader vs Sentinel hero-talent split (Stampede shows in only 50% of fights, suggesting a Sentinel minority) doesn't surface a clean second major-CD aura the way Druid's Incarnation/CA pair does. If a future build standardizes on Sentinel and surfaces a tractable Stampede self-aura, revisit.
- **Aspect of the Cheetah (186257/186258), Aspect of the Turtle (186265)** appear at 88-100% but are utility — Cheetah is a movement speed buff hunters press routinely between pulls, Turtle is a panic-button immunity. Not "major DPS CDs" in the cooldown_usage sense.
- **Aspect of the Wild (193530)** does NOT appear in the top 60 — surprising for BM, but this confirms it was likely retired/replaced in current Midnight tuning, or its aura ID changed. Not a candidate for tracking from this sample.

### Interrupts

- **Spell name (id):** `Counter Shot` (147362)
- **Cast type:** instant, ranged (40yd), 24s CD
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable. Counter Shot applies a 3s silence debuff to the target rather than a self-buff, so it doesn't appear in any of the sampled players' aura lists. Needs a CastsTable spot-check for verification.
- **Recommended expected count for scoring:** **flag for review.** The DPS role default is 15. Counter Shot's **24s CD** is meaningfully longer than most DPS kicks (Pummel/Mind Freeze/Kick are 15s; Skull Bash/Solar Beam are 15s). Over a typical 30-minute M+ key, a perfectly-rotated Counter Shot maxes around 12-13 kicks vs Pummel's ~18+. The 15-kick role default likely under-rates BM/MM Hunter on interrupt scoring. Flag for engine-level review (interrupt-benchmark override).
- **No-baseline-kick callout:** N/A — BM has Counter Shot baseline.

### Dispels

- **In-spec dispel ability:** **none in baseline kit** for defensive cleansing. Hunters have **Tranquilizing Shot (19801)** baseline across all three specs, but it is an OFFENSIVE purge that removes Enrage / Magic effects from enemies — not a friendly cleanse. Should be tracked separately if/when an offensive-purge utility metric is added, but does NOT belong in the defensive-cleanse registry.
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** State explicitly in the new dispel-school registry: `(3, "Beast Mastery") = set()`. Same as Warriors/Rogues/Mages/Warlocks/DKs — Hunters have zero ally-side cleanse.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Concussive Shot | 5116 | slow | baseline single-target slow |
| Wing Clip | 195645 | slow | baseline (also serves as on-melee-snare for SV — but the spell is on all hunters in their kit) |
| Disengage | 781 | movement (self) | baseline mobility |
| Freezing Trap | 187650 | incapacitate | baseline 60s incapacitate (humanoid/beast/dragonkin); breaks on damage |
| Binding Shot | 109248 | AoE stun | talent-gated AoE stun (stuns on cross of binding line) |
| Intimidation | 19577 | stun | talent-gated single-target pet stun (BM-favored due to pet emphasis) |
| Scare Beast | 1513 | fear | baseline fear (beast-only) |

### Recommended changes

1. `app/scoring/cooldowns.py` `(3, "Beast Mastery")`: **drop** `(359844, "Call of the Wild", 10, "offensive")` — 0% consensus, displaced by Pack Leader passive procs that aren't trackable as press-on-cooldown CDs. **Keep** `(19574, "Bestial Wrath", 25, "offensive")`. After this drop BM has only one tracked CD; that's honest given the spec's CD-light current design.
2. **Dispel registry** (new): `(3, "Beast Mastery") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** flag `(3, "Beast Mastery")` for a possible per-spec expected-kicks count of 12 (vs role default 15) due to Counter Shot's 24s CD. Open question for Logan; do not codify without confirmation.
4. Talent-gate flags: none needed after the CotW drop. BM's remaining tracked CD (Bestial Wrath) is baseline — every BM has it at 100%.

### Top-cohort raw output reference

```
Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
       19574   100%        53   Bestial Wrath
      268877   100%       172   Beast Cleave
      118922   100%        12   Posthaste
      186257   100%         5   Aspect of the Cheetah
      264735   100%        43   Survival of the Fittest
     1276720   100%       948   Nature's Ally
      385540   100%        24   Rejuvenating Wind
      246152   100%       430   Barbed Shot
     1264426   100%         1   Void-Touched
     1241715   100%       206   Might of the Void
      186258   100%         5   Aspect of the Cheetah
     1229746   100%        68   Arcanoweave Insight
      383781    88%        13   Algeth'ar Puzzle
      186265    88%         4   Aspect of the Turtle
       65116    88%         2   Stoneform
     1242775    88%        12   Farstrider's Step
     1236998    75%         6   Draught of Rampant Abandon
     1265140    75%        28   Refreshing Drink
     1265145    75%        23   Refreshing Drink
     1277389    75%         1   Vantus Rune: Radiant
        1126    75%         2   Mark of the Wild
       34477    62%        16   Misdirection
     1235108    62%         1   Flask of the Magisters
     1263727    62%        60   Litany of Lightblind Wrath
       35079    62%        16   Misdirection
        8936    62%        66   Regrowth
     1258886    50%        21   Nordrassil's Sagacity
      459731    50%       217   Huntmaster's Call
     1276715    50%         1   Vantus Rune: Crown of the Cosmos
     1258887    50%        24   Amirdrassil's Swiftness
```

(Call of the Wild ID 359844 is conspicuously absent from this list AND the extended top-60 — it's not in the BM cohort at any consensus.)

---

## Spec: Marksmanship

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 288613  | Trueshot  | yes                | 88%         | 13          | keep (the missing 8th fight returned 0 auras due to BuffsTable fetch hiccup; effective consensus is 100% on returning data) |
| 260402  | Double Tap | no                | 88%         | 58          | hold (talent buff window, ~60s CD; could be tracked but it's a Lock-and-Load adjacent rotational, not a "major" CD pressed standalone) |
| 260243  | Volley    | no                 | 88%         | 46          | skip (talent shot ability with stacking aura per cast, ~45s CD — but the 46 median uses suggests it's rotational AoE, not a major) |
| 257622  | Trick Shots | no               | 88%         | 47          | skip (passive Multi-Shot proc, not pressed) |
| 194594  | Lock and Load | no             | 88%         | 39          | skip (RNG proc) |
| 451447  | Don't Look Back | no           | 88%         | 318         | skip (Sentinel hero-talent passive stack) |
| 1279347 | Quick Draw | no               | 88%         | 318         | skip (passive stacking buff) |
| 389020  | Bulletstorm | no              | 88%         | 1785        | skip (passive proc stack) |
| 1253750 | Stargazer | no                | 88%         | 701         | skip (Sentinel hero-talent passive) |

**Notes on splits / alt-builds:**
- **Trueshot (288613)** is the only universal press-on-cooldown major and stays tracked. Its expected-uptime in `cooldowns.py` was already corrected to 13 in Pass 2, which matches this sample's median exactly. Good.
- **Volley vs Salvo:** The audit instructions called out Volley (talent) and Salvo (hero-talent that auto-applies Volley) as candidates. Volley (260243) shows at 88% with med=46 — that's per-shot Volley window aura, not the press-the-button event. Salvo's actual aura ID (400456) does NOT appear in top 60. Neither is a clean major-CD addition.
- **Double Tap (260402)** at 88% med=58 is interesting — it's a 60s-CD talent buff that empowers the next Aimed Shot. Would be trackable but median uses (58) is high enough to suggest it stacks on every Aimed Shot rather than a one-press-per-window press, similar to how Demolish surfaces. NOT recommending add without further investigation; it's not at the same "always pressed major" tier as Avatar/Demolish.
- **The 0-auras Banshers fight** in Algeth'ar Academy reduces effective sample to 7. That's a buffsTable fetch quirk (likely the player switched specs mid-pull or the fight had no completed buffs window) — sample size is still ≥5.
- **Sentinel hero-tree dominance:** The cluster of `Don't Look Back (451447)`, `Quick Draw (1279347)`, `Bulletstorm (389020)`, `Stargazer (1253750)` at 88% all suggests every top MM is running Sentinel. The Dark Ranger hero-tree (the Sentinel alternative) doesn't surface any 88%+ aura — not enough cohort spread to detect alt-build divergence. Top MM is currently mono-build.

### Interrupts

- **Spell name (id):** `Counter Shot` (147362)
- **Cast type:** instant, ranged (40yd), 24s CD
- **Sample observed kicks per fight (median):** Same caveat as BM — Counter Shot applies a debuff, not a self-buff. Not in BuffsTable.
- **Recommended expected count for scoring:** Same flag as BM. 24s CD vs 15s CD on most DPS kicks suggests the 15-default may be too high for ranged Hunters. Suggested override: 12.
- **No-baseline-kick callout:** N/A — MM has Counter Shot baseline.

### Dispels

- **In-spec dispel ability:** **none in baseline kit** for defensive cleansing. Tranquilizing Shot is offensive only.
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Same as BM. Registry entry: `(3, "Marksmanship") = set()`.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Concussive Shot | 5116 | slow | baseline single-target slow |
| Disengage | 781 | movement (self) | baseline mobility |
| Freezing Trap | 187650 | incapacitate | baseline 60s incapacitate |
| Binding Shot | 109248 | AoE stun | talent-gated |
| Scatter Shot | 213691 | disorient | talent-gated single-target disorient (MM-favored as the canonical MM control) |
| Steady Focus / Aimed Shot snare | — | slow | passive snare on Aimed if talented |
| Scare Beast | 1513 | fear | baseline (beast-only) |

### Recommended changes

1. `app/scoring/cooldowns.py` `(3, "Marksmanship")`: **no edits.** Trueshot is correctly tracked and at the right uptime (13). No Volley/Salvo/Double Tap addition warranted — none rise to the universal-major-CD tier.
2. **Dispel registry** (new): `(3, "Marksmanship") = set()`.
3. **Interrupt benchmark override:** same flag as BM — Counter Shot 24s CD warrants a possible per-spec expected-kicks of 12.
4. Talent-gate flags: none — Trueshot is baseline MM.

### Top-cohort raw output reference

```
Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      204090    88%      1142   Bullseye
      264735    88%        19   Survival of the Fittest
     1236616    88%         6   Light's Potential
      383781    88%        12   Algeth'ar Puzzle
     1265140    88%        12   Refreshing Drink
      260402    88%        58   Double Tap
      288613    88%        13   Trueshot (tracked)
      257622    88%        47   Trick Shots
      451447    88%       318   Don't Look Back
      186265    88%         3   Aspect of the Turtle
       35079    88%        12   Misdirection
     1241715    88%       170   Might of the Void
      260242    88%       420   Precise Shots
     1265145    88%         9   Refreshing Drink
      260243    88%        46   Volley
     1229746    88%        34   Arcanoweave Insight
      186258    88%         5   Aspect of the Cheetah
     1264946    88%        13   Moonlight Chakram
     1279347    88%       318   Quick Draw
      389020    88%      1785   Bulletstorm
      194594    88%        39   Lock and Load
       34477    88%        12   Misdirection
      118922    88%        13   Posthaste
      466904    88%         3   Harrier's Cry
      385540    88%        11   Rejuvenating Wind
     1253750    88%       701   Stargazer
      186257    88%         6   Aspect of the Cheetah
        6673    75%         8   Battle Shout
       97463    75%         4   Rallying Cry
     1235111    75%         1   Flask of the Shattered Sun
```

---

## Spec: Survival

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 186289  | Aspect of the Eagle | no       | 100%        | 13          | **add (every top SV ran it; ~90s CD ranged-Raptor-Strike window; signature SV major)** |
| 259388  | Mongoose Fury | no            | 100%        | 1047        | skip (rotational stacking buff per Mongoose Bite cast; not a major CD) |
| 260286  | Tip of the Spear | no         | 100%        | 491         | skip (rotational buff per Kill Command, not a major) |
| 260249  | Bloodseeker | no              | 100%        | 93          | skip (DoT-derived stacking buff, passive) |
| 1250646 | Takedown  | no                 | 100%        | 25          | hold (Sentinel hero-talent buff per execute; med=25 over a key — a real press cadence, but the buff is auto-applied by other casts rather than pressed standalone. Not currently a "major" CD.) |
| 1258345 / 1258338 | Stampede / Stampede! | no | 100%      | 25          | **add candidate (Sentinel hero-talent capstone, 100% consensus, ~2min CD, ~25 uses ≈ on-CD over a 30min key)** |
| 471877 / 472324 / 472325 / 471878 | Howl of the Pack Leader | no | 100% | 79     | skip (passive Pack Leader proc; though SV runs Pack Leader at 100% in this cohort, the auras are passive procs from auto-attacks, not pressed CDs) |
| 472640  | Hogstrider | no               | 100%        | 108         | skip (passive Pack Leader stack) |
| 471881  | Wyvern's Cry | no             | 100%        | 361         | skip (Pack Leader pet ability proc) |
| 1292687 | Shrapnel Bomb | no            | 100%        | 170         | skip (Wildfire-Bomb-derived DoT aura, rotational) |
| 1261193 | Boomstick | no                | 100%        | 50          | skip (talent Wildfire Bomb upgrade aura, rotational) |

**Notes on splits / alt-builds:**
- **Aspect of the Eagle (186289) at 100% with med=13** is the headline finding for SV. Currently SV has zero tracked cooldowns in `cooldowns.py` — this gives the spec its first trackable major CD. AotE is a 15s buff that turns Raptor Strike / Mongoose Bite into ranged abilities; SV presses it on cooldown for the ~15s burst window. Median 13 uses on a ~90s CD across a 30min key is roughly on-cooldown. Recommend: `(186289, "Aspect of the Eagle", 13, "offensive")`.
- **Stampede (1258345 / 1258338) at 100% with med=25** is also worth considering. Both IDs surface at 100% — the difference is likely Stampede the press (1258345) vs Stampede! the per-tick aura while the ability is active (1258338). The 25 median uses across a 30min key matches a ~60-90s CD on-cooldown rotation. Note that Stampede is a Sentinel hero-talent capstone — top SV is 100% Sentinel in this cohort, so Stampede alongside AotE would mean SV gets 2 tracked CDs instead of 1. Calling out as a strong "consider" but recommending just the AotE add as the safe baseline; Stampede being hero-talent-gated is a weaker argument for tracking when Sentinel's universal-pick-rate could shift in a future tuning pass.
- **Spearhead (360966) confirmed absent** from top 60 — the Pass 2 removal note still holds. The 3s buff is too short to register reliably in BuffsTable snapshots.
- **Coordinated Assault (266779) confirmed absent** from top 60 — was a candidate per audit instructions but doesn't surface as an aura. Either retired in current SV builds or its aura ID changed; not a candidate.
- **Wildfire Bomb (259495)** also absent as a self-aura — the proc spawns a debuff/DoT on enemies (Shrapnel Bomb 1292687 etc.), not a self-buff. Not a candidate via BuffsTable.
- **Pack Leader vs Sentinel hero-tree split:** Top SV cohort is running BOTH simultaneously? No — it's that the Pack Leader passive procs (Howl 471877, Wyvern's Cry 471881, Hogstrider 472640) are showing on Sentinel-hero-tree SV as well, suggesting either (a) one of these is actually a baseline pet proc, or (b) the cohort is mixed and the sampler is mis-aggregating. More likely: the auras at 100% across all 8 SV samples confirm the cohort is mono-build — most likely Pack Leader as the primary, with Sentinel providing Stampede via a non-hero-talent path (talent node, not capstone). If a future audit needs to distinguish Pack Leader vs Sentinel Survival, sample more deeply.

### Interrupts

- **Spell name (id):** `Muzzle` (187707)
- **Cast type:** instant, melee-range, 15s CD
- **Sample observed kicks per fight (median):** Same caveat — Muzzle applies a 3s silence debuff to the target, not a self-buff. Not in BuffsTable.
- **Recommended expected count for scoring:** **15 (DPS role default).** Survival is melee, has the 15s-CD Muzzle (not the 24s Counter Shot), so the role-default 15 expected kicks is realistic — same as melee DPS like Outlaw/Feral/Havoc. **Do NOT** apply the BM/MM ranged-kick override to Survival.
- **No-baseline-kick callout:** N/A — SV has Muzzle baseline.

### Dispels

- **In-spec dispel ability:** **none in baseline kit** for defensive cleansing. Tranquilizing Shot (19801) is offensive only — same as BM and MM.
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Registry entry: `(3, "Survival") = set()`.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Wing Clip | 195645 | slow | baseline (SV-flavored on-melee snare) |
| Disengage | 781 | movement (self) | baseline mobility |
| Harpoon | 190925 | gap-close + root | baseline SV gap-closer with 3s root on impact |
| Freezing Trap | 187650 | incapacitate | baseline 60s incapacitate |
| Binding Shot | 109248 | AoE stun | talent-gated |
| Intimidation | 19577 | stun | talent-gated single-target pet stun |
| Tar Trap | 187698 | slow (AoE ground) | baseline AoE slow trap |
| Scare Beast | 1513 | fear | baseline (beast-only) |

(Survival is the most CC-rich Hunter spec — Harpoon's root, Tar Trap's AoE slow, plus the universal Hunter trap kit.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(3, "Survival")`: **add** `(186289, "Aspect of the Eagle", 13, "offensive")`. This gives SV its first tracked major CD via the BuffsTable path. Optionally consider adding `(1258345, "Stampede", 25, "offensive")` as a Sentinel-hero-tree-flagged alt-build addition; flagged for Logan to weigh in.
2. **Dispel registry** (new): `(3, "Survival") = set()`.
3. **Interrupt benchmark override:** none. Muzzle's 15s CD makes the DPS-role-default 15 kicks realistic. Do NOT apply the BM/MM 12-kick override to SV.
4. Talent-gate flags: Aspect of the Eagle is baseline SV — no skip needed. If Stampede gets added, flag it as Sentinel-hero-tree alt-build so the talent-aware skip catches non-Sentinel builds.

### Top-cohort raw output reference

```
Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1250646   100%        25   Takedown
     1235108   100%         1   Flask of the Magisters
      186258   100%         7   Aspect of the Cheetah
      472640   100%       108   Hogstrider
      118922   100%        11   Posthaste
      385540   100%         8   Rejuvenating Wind
     1261193   100%        50   Boomstick
      264735   100%        15   Survival of the Fittest
     1258338   100%        25   Stampede!
      259388   100%      1047   Mongoose Fury
      471877   100%        79   Howl of the Pack Leader
     1275630   100%        37   Raptor Swipe!
      260286   100%       491   Tip of the Spear
     1273155   100%       205   Raptor Swipe!
      383781   100%        13   Algeth'ar Puzzle
      471881   100%       361   Wyvern's Cry
     1292687   100%       170   Shrapnel Bomb
      471878   100%        34   Howl of the Pack Leader
      186289   100%        13   Aspect of the Eagle
     1229746   100%        79   Arcanoweave Insight
      186257   100%         7   Aspect of the Cheetah
      260249   100%        93   Bloodseeker
      472324   100%        33   Howl of the Pack Leader
      186265   100%         6   Aspect of the Turtle
      472325   100%        32   Howl of the Pack Leader
     1258345   100%        25   Stampede
     1241759    88%       174   Genius Insight
       35079    88%        15   Misdirection
     1265145    88%        23   Refreshing Drink
       34477    88%        15   Misdirection
```

---

## Open questions for review

- **Counter Shot 24s CD vs DPS-default 15 expected kicks:** BM and MM both have Counter Shot (147362) at a 24s CD, while every other DPS kick (Pummel, Mind Freeze, Kick, Skull Bash) is on a 15s CD. Over a 30min M+ key, the per-spec opportunity ceiling for Hunters is ~12-13 kicks, vs 18-20 for melee. The role-default 15 expected kicks may systematically under-rate ranged Hunters on interrupt scoring. Recommend a per-spec override of 12 for `(3, "Beast Mastery")` and `(3, "Marksmanship")`. **Survival uses Muzzle (15s CD) and should keep the role default.** Logan, do we want to introduce per-spec interrupt benchmarks, or is the noise acceptable? (Answer informs whether we add the override or just document the asymmetry.)
- **Tranquilizing Shot as offensive purge tracking:** All three Hunter specs have Tranquilizing Shot (19801) baseline — it removes Enrage and Magic from enemies. It's not a defensive cleanse and shouldn't go in the dispel-school registry. But there's currently no place in scoring for "offensive purge" utility (Mass Dispel offensive use, Spellsteal, Tranq Shot, Purge, Soothe). If Logan wants to credit specs for using these, that's a new utility category. Flagging here so it isn't lost.
- **Call of the Wild drop confidence:** 0% in 8 fights is conclusive that the aura isn't surfacing in BuffsTable, but the underlying question — is CotW a current-meta talent that just doesn't surface as a self-aura (pet-summon pattern, like Feral Spirit/Tyrant), or is it talented out entirely in the Pack Leader meta? — matters for whether dropping it is the "right" answer. If CotW is universally taken but un-trackable, dropping it from `cooldowns.py` is correct (we can't track it via BuffsTable regardless). If it's actually un-talented, dropping is also correct. Either way, drop is safe — flagging the reason for transparency.
- **SV Stampede as a Sentinel-hero-tree alt-build CD:** Stampede surfaces at 100% in this 8-fight cohort, but the cohort appears to be mono-Sentinel. If the Sentinel-vs-Pack Leader hero-tree split shifts in a future tuning pass, Stampede may drop below universal threshold. Adding it as a Sentinel-flagged alt-build CD would let the talent-aware skip handle Pack Leader builds correctly. Logan: do we add Stampede now, or wait for the second SV audit pass after the next tuning?
- **BM Bestial Wrath expected uptime of 25 vs observed med=53:** BW's expected uptime in `cooldowns.py` is 25; observed median is 53 uses. The 53 likely reflects aura tick events (the buff has refresh-on-pet-Frenzy mechanics with extensions), not 53 distinct presses. Not recommending an immediate change — the expected uptime drives the scoring CURVE, not a hard target. But worth reviewing if cooldown_usage saturates to 100% on every BM run (the same Pass-3 saturation pattern that killed Resto Druid Barkskin).

## Confidence

- **Sample size:** 8 distinct top players per spec across 8 dungeons, all at +19 to +21. MM had one fight with 0 auras returned (Banshers/Stormrage on Algeth'ar Academy — likely a transient WCL fetch hiccup) so its effective sample is 7. All three specs cleared the ≥5 fights bar; no retries needed.
- **Confidence on Beast Mastery Call of the Wild drop:** very high. 0% across 8 fights with the top-60 expansion confirming no false-negative. Either the talent isn't taken or the aura doesn't surface — either way the BuffsTable can't see it, so tracking is dishonest.
- **Confidence on Survival Aspect of the Eagle add:** very high. 100% consensus, med=13 matching expected on-cooldown press cadence, baseline ability (no talent gate).
- **Confidence on Marksmanship no-change verdict:** high. Trueshot is correctly tracked at 88% (effectively 100% of returning samples), and no other aura crosses the universal-major-CD bar. Volley/Salvo/Double Tap are rotational, not press-on-cooldown majors.
- **Confidence on dispel registry empty-set entries:** very high. Hunter has zero defensive cleanses on allies in any spec; this is a static class fact dating back ~15 years. Tranquilizing Shot is offensive-only.
- **Confidence on interrupt benchmark override flag:** medium. The 24s vs 15s CD difference is real and the math (12-13 kicks max vs 18-20 for melee) is straightforward, but whether to act on it depends on Logan's appetite for per-spec interrupt-count overrides — currently none exist in the engine. Documenting as an open question rather than recommending a change.
- **Lower-confidence items:** the optional Stampede add for Survival (mono-build cohort means we can't validate it survives a Sentinel-vs-Pack Leader meta shift), and the BM Bestial Wrath expected-uptime 25→? recalibration (would need a saturation check on real Umbra runs to know if it's an issue).
