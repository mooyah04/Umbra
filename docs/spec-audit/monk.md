# Monk Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist (Opus 4.7)
**Sample depth:** 1 report per dungeon (top-8 cohort), 8 active-season Midnight S1 dungeons, key range +19 to +21
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Monk" --spec "{Mistweaver|Windwalker}" --samples-per-dungeon 1 --top-n 8`
**Fights sampled (this audit):** Mistweaver 8 / Windwalker 8 = 16 distinct top-cohort fights. **Brewmaster was previously audited 2026-04-26 and is summarized below from the prior pass.**

> **CORRECTION 2026-04-27 (post-codification):** This report incorrectly
> stated that Mistweaver has Spear Hand Strike as a baseline interrupt.
> That is wrong. Spear Hand Strike is Brewmaster / Windwalker only.
> Mistweaver's CC kit (Leg Sweep, Ring of Peace, Paralysis) is CC, not
> interrupts in the spell-school-lockout sense — MW should NOT be in
> `HEALER_SPECS_WITH_INTERRUPT`. The codification commit briefly added
> MW to that set; the correction removed it. All "MW has Spear Hand
> Strike" / "add MW to HEALER_SPECS_WITH_INTERRUPT" lines below are
> inaccurate and should be ignored.

> Class IDs verified from `app/scoring/roles.py`: Monk is class_id `10`. Brewmaster = tank, Mistweaver = healer, Windwalker = DPS. ~~All three specs share Spear Hand Strike (116705) as the kick.~~ **Brewmaster and Windwalker share Spear Hand Strike (116705) as the kick; Mistweaver does NOT have a baseline interrupt.** The dispel story splits: Brewmaster and Windwalker carry **Detox 218164** (Poison + Disease only); Mistweaver carries the **Detox 115450** healer variant which adds Magic. This is the BRM-lesson-3 fix that has been pending since 2026-04-26 — this audit explicitly produces all three dispel registry entries so codification can land them in one shot.

---

## Spec: Brewmaster (previously audited)

### Status

Brewmaster is the **founding audit** of this whole project — the BRM sample on 2026-04-26 surfaced both the talent-aware-skip mechanism and the dispel-school-registry idea that the rest of these reports depend on. Per the `CHECKLIST.md` line "talent-aware skip + Strength of the Black Ox added; dispel-type fix still pending," the cooldown side is current and the dispel side is what this report unblocks.

**Current tracking (`cooldowns.py` `(10, "Brewmaster")`):**

| Aura ID | Aura Name | Kind | Notes |
|---------|-----------|------|-------|
| 120954  | Fortifying Brew | defensive | baseline ~7-min CD; signature panic button |
| 132578  | Invoke Niuzao, the Black Ox | defensive | summoned ox stomps; aura present on Brewmaster while active |
| 325153  | Exploding Keg | defensive | mainline build; mutually exclusive with Strength of the Black Ox |
| 443113  | Strength of the Black Ox | defensive | alt-build branch; talent-aware skip excludes this for Keg builds |

The Keg vs Black Ox Brew split was the canonical alt-build that first proved the talent-aware skip mechanism works. Both branches are tracked and the engine excludes whichever the player didn't pick.

### Interrupt

Spear Hand Strike (116705) — see the cross-spec note in the Mistweaver and Windwalker sections below; same aura/cast across all three Monk specs.

### Dispel — pending fix

**Brewmaster's Detox is Detox (218164), Poison + Disease only.** The 2026-04-26 audit caught that `class_has_dispel(Monk)=True` is currently treated as a full Magic-cleanse, which over-credits Brewmaster (and Windwalker) for cleanses they cannot perform. The fix has been pending until the rest of the Monk class was audited — this report now produces the per-spec registry entries needed to land it.

### Recommended changes

1. `app/scoring/cooldowns.py` `(10, "Brewmaster")`: **no changes** — Pass 2 + Pass 3 fixes are landed and verified.
2. **Dispel registry** (new): `(10, "Brewmaster") = {Poison, Disease}`. NOT Magic.
3. **Interrupt:** Spear Hand Strike (116705) — tank role default of 12 expected kicks is fine.
4. **Talent-gate flags:** 325153 (Exploding Keg) and 443113 (Strength of the Black Ox) flagged as alt-build branches. Already in place.

---

## Spec: Mistweaver

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 443028  | Celestial Conduit | yes | 100% | 12 | keep |
| 443113  | Strength of the Black Ox | no | 100% | 58 | **add** — universal hero-talent (Master of Harmony) capstone in current MW builds; same aura BRM tracks but hero-tree-shared. See notes. |
| 443592  | Unity Within | no | 100% | 12 | **add** — Conduit of the Celestials hero-talent capstone. Med=12 lines up with a 1-min CD across a 12-15min key. Major performance CD for the alt hero tree. |
| 116680  | Thunder Focus Tea | no | 100% | 68 | hold — 30s CD spell empower, rotational not "major" |
| 115867  | Mana Tea | no | 100% | 313 | skip (mana regen passive ramp; rotational, not press-on-CD major) |
| 115294  | Mana Tea | no | 100% | 39 | hold — short-CD mana CD; talented in some builds but not a "major" by the same logic that excluded Tiger's Fury for Feral |
| 399497  | Sheilun's Gift | no | 100% | 457 | skip (rotational charge-stacking heal; 457 uses confirms this is the cast aura, not a major CD) |
| 388500  | Secret Infusion | no | 100% | 66 | skip (passive Thunder Focus Tea proc) |
| 414143  | Yu'lon's Grace | no | 100% | 225 | skip (passive proc/HoT effect from Sheilun's Gift) |
| 322118  | Invoke Yu'lon, the Jade Serpent | no | 0% in top 30 | — | **add as alt-build branch** — talent-aware skip target; cohort universally took Chi-Ji over Yu'lon |
| 325197  | Invoke Chi-Ji, the Red Crane | no | 0% in top 30 (but see 443569 Chi-Ji's Swiftness at 100%, 1238904 Heart of the Jade Serpent at 100%) | — | **add as alt-build branch** — implied present via downstream auras; the 325197 self-aura ID may not be the buff WCL surfaces, see notes |
| 115310  | Revival | no | 0% in top 30 | — | **add as alt-build branch** (talent swap with Restoral) |
| 388615  | Restoral | no | 0% in top 30 | — | **add as alt-build branch** (talent swap with Revival) |
| 388193  | Jadefire Stomp | no | not in top 30 | — | hold — talent-gated mobility/utility, situational AoE damage; not a "major" performance CD |

**Notes on splits / alt-builds:**
- **Strength of the Black Ox (443113) at 100% med=58** is a clear add. This is the **Master of Harmony** hero-talent capstone aura — same buff ID Brewmaster already tracks. Top MW cohort universally runs Master of Harmony, so 443113 sits at 100% in this sample. Adding it gives MW a hero-tree CD analogous to BRM's tracking.
- **Unity Within (443592) at 100% med=12** is the **Conduit of the Celestials** hero-talent capstone. Both MW hero trees showed up in the cohort (auras 443569 "Chi-Ji's Swiftness" and 1238904 "Heart of the Jade Serpent" both at 100% indicate Conduit of the Celestials is also represented). The 100% / med=12 on Unity Within itself suggests it's universal — either the cohort all picked Conduit, or the aura fires across both hero trees. Either way, add it.
- **Note on hero-tree alt-build:** Strength of the Black Ox (Master of Harmony) and Unity Within (Conduit of the Celestials) are mutually exclusive hero-tree capstones. **Both showing at 100% in this 8-fight sample is suspicious** — one of them may be a downstream buff that fires regardless of hero tree picked. Cleanest interpretation: track both and let the talent-aware skip handle the absent one if/when a non-Master-of-Harmony build shows up. Same pattern as BRM Keg vs Black Ox Brew.
- **Revival (115310) vs Restoral (388615) talent swap** is the canonical MW group-heal CD swap (3-min CD). Both are channeled/instant casts. The cohort showed neither in the top-30 (likely because neither produces a persistent BuffsTable aura — both are heal-burst events, like the Revival 2026-04-16 Pass-2 removal note). Recommend tracking both as alt-build paths so the talent-aware skip excludes whichever isn't taken; if neither produces a BuffsTable signal at all (the original Pass-2 reason), keep the current Celestial Conduit-only list and accept that this swap isn't BuffsTable-detectable. Logan should pick.
- **Invoke Yu'lon (322118) vs Invoke Chi-Ji (325197) split:** The cohort shows downstream Chi-Ji auras (443569 "Chi-Ji's Swiftness", 325202 "Dance of Chi-Ji" at 100%) but neither summoning aura at the IDs listed. Same caveat as Brewmaster's Niuzao initially — the *summon* of the celestial puts an aura on the Monk only while the celestial is up; Mistweaver's Yu'lon/Chi-Ji may not surface a self-aura at all. Worth a sampler retry with bigger top-N if we want to confirm an alt-build add here.
- **Jadefire Stomp (388193)** absent from top 30 — talent-gated, not currently meta in MW. Skip.
- **Mana Tea (115294 short-CD vs 115867 channel)** — both at 100%. The channel form (115867) at med=313 is the mana-regen ramp passive; the short-CD form (115294) at med=39 is the burst mana cooldown. Neither qualifies as a major performance CD — they're mana-management tools, not press-on-cooldown raid saves.

### Interrupts

- **Spell name (id):** `Spear Hand Strike` (116705)
- **Cast type:** instant melee kick (15s CD)
- **Sample observed kicks per fight (median):** Spear Hand Strike applies a 4s silence debuff to the target rather than a self-buff, so it doesn't appear in any sampled MW player's BuffsTable. Needs a CastsTable spot-check for verification.
- **Recommended expected count for scoring:** **MW should be added to `HEALER_SPECS_WITH_INTERRUPT`.** Mistweaver baselines Spear Hand Strike just like Holy Paladin baselines Rebuke and Resto Shaman baselines Wind Shear. Currently the set in `roles.py` only has `(2, "Holy")` and `(7, "Restoration")` — MW being missing is a clear oversight. Once added, default healer interrupt expectation applies (likely fewer than the DPS 15 default; Logan's discretion).
- **No-baseline-kick callout:** N/A — MW *does* have a baseline kick. The current state where MW is missing from `HEALER_SPECS_WITH_INTERRUPT` likely means utility scoring under-credits MW for kicks they actually have.

### Dispels

- **In-spec dispel ability:** **Detox (115450)** — the Mistweaver healer variant. Removes Magic, Poison, Disease.
- **Schools cleansable on allies:** Magic, Poison, Disease
- **Schools the engine should credit MW for:** `{Magic, Poison, Disease}` — full healer kit (the same retail behavior that has applied since Mists of Pandaria; verified for The War Within / Midnight)
- **Notes:** This is the asymmetry that makes the BRM-lesson-3 fix matter. **MW gets the full Magic-cleanse Detox; BRM and WW get the limited Poison + Disease Detox.** Today, the engine treats `class_has_dispel(Monk)=True` for all three specs uniformly — MW is correctly credited for Magic but BRM and WW are over-credited for Magic they cannot actually cleanse. The dispel-school registry fixes this by being spec-keyed.
- **Tip note:** WCL dispel events on a friendly target (cleanse) vs hostile target (offensive purge — Tranq, Purge, Mass Dispel offensive use) need to be filtered as per the `feedback_dispel_defensive_vs_offensive` memory. MW's Detox is defensive-only on allies; no offensive purge variant exists for the healer Detox.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Paralysis | 115078 | incapacitate | baseline single-target 60s incap (breaks on damage) |
| Leg Sweep | 119381 | stun (AoE) | baseline AoE 5s stun, 60s CD — universal Monk pull-opener tool |
| Ring of Peace | 116844 | disorient (AoE) | talent-gated, AoE knockback + disorient at center point |
| Tiger's Lust | 116841 | utility (movement) | observed at 100% med=7 in cohort; not CC but party utility (freedom + speed) |
| Disable | 116095 | slow + root | baseline single-target slow that roots after second cast |

### Recommended changes

1. `app/scoring/cooldowns.py` `(10, "Mistweaver")`: **add** `(443113, "Strength of the Black Ox", 58, "offensive")` and `(443592, "Unity Within", 12, "offensive")` as the two hero-tree capstone CDs. Both at 100% in cohort; treat as alt-build pair via the talent-aware skip. Keep Celestial Conduit (443028).
2. **Dispel registry** (new): `(10, "Mistweaver") = {Magic, Poison, Disease}`. Full healer kit.
3. **Add MW to `HEALER_SPECS_WITH_INTERRUPT`** in `roles.py`. Spear Hand Strike (116705) is baseline — currently the engine treats MW as kickless, which under-credits utility scoring.
4. **Talent-gate flags:**
   - 443113 (Strength of the Black Ox) and 443592 (Unity Within) — hero-tree capstone alt-build pair.
   - 322118 (Invoke Yu'lon) and 325197 (Invoke Chi-Ji) — celestial summon talent swap; flag both if added.
   - 115310 (Revival) and 388615 (Restoral) — group-heal talent swap; only add if a BuffsTable signal exists (Pass-2 noted Revival had no caster aura).

### Top-cohort raw output reference

```
=== Aggregate over 8 Monk Mistweaver fights ===

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    443028      100%        12   Celestial Conduit  [Celestial Conduit]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      427296   100%        31   Healing Elixir
     1263727   100%        87   Litany of Lightblind Wrath
      443113   100%        58   Strength of the Black Ox
      438443   100%       124   Dance of Chi-Ji
      406220   100%        22   Chi Cocoon
      443112   100%        83   Strength of the Black Ox
      388500   100%        66   Secret Infusion
      399497   100%       457   Sheilun's Gift
     1265145   100%        50   Refreshing Drink
     1265140   100%        62   Refreshing Drink
      414143   100%       225   Yu'lon's Grace
      443592   100%        12   Unity Within
      399510   100%       457   Sheilun's Gift
     1241715   100%       192   Might of the Void
      120954   100%        10   Fortifying Brew
      124682   100%        18   Enveloping Mist
     1238904   100%        11   Heart of the Jade Serpent
      443569   100%       213   Chi-Ji's Swiftness
      392883   100%       310   Vivacious Vivification
      115175   100%        74   Soothing Mist
      116680   100%        68   Thunder Focus Tea
      448508   100%        12   Jade Sanctuary
      115294   100%        39   Mana Tea
      119611   100%        75   Renewing Mist
      449609   100%        44   Lighter Than Air
     1229746   100%        98   Arcanoweave Insight
      443028   100%        12   Celestial Conduit (tracked)
      443616   100%        12   Heart of the Jade Serpent
      115867   100%       313   Mana Tea
      116841   100%         7   Tiger's Lust
```

---

## Spec: Windwalker

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 122470  | Touch of Karma | yes | 100% | 11 | keep |
| 137639  | Storm, Earth, and Fire | no | 0% in top 30 | — | hold — Pass-2 removed for "no aura at 50%"; cohort confirms it's still not surfacing. **Add as alt-build branch only if Serenity branch resolves with an aura.** See notes. |
| 152173  | Serenity | no | 0% in top 30 | — | hold — talent swap for SEF; same BuffsTable invisibility problem. If we want to honor the canonical SEF-vs-Serenity alt-build the engine has to use a different detection path (cast events). |
| 123904  | Invoke Xuen, the White Tiger | no | 0% in top 30 (but Xuen's Battlegear 392993 is at 100%, indicating Xuen procs are firing) | — | hold — pet-summon, no caster aura per 2026-04-16 Pass-2 removal. Sampler confirms still no surface. |
| 152175  | Whirling Dragon Punch | no | 0% in top 30 | — | hold — short-cycle (~24s) damage cooldown; not a "major" CD and likely no persistent aura |
| 392983  | Strike of the Windlord | no | 0% in top 30 | — | hold — same short-cycle reasoning |
| 1248705 | Skyfire Heel | no | 100% | 772 | skip (passive proc, hero-talent rotational) |
| 451021  | Flurry Charge | no | 100% | 885 | skip (passive proc / Flurry of Xuen stack) |
| 451297  | Momentum Boost | no | 100% | 2619 | skip (passive proc — 2619 fires confirms it's a stack/refresh aura) |
| 1261724 | Tigereye Brew | no | 100% | 460 | skip — Tigereye Brew at this volume is the stacking buff, not the press; rotational |
| 196741  | Hit Combo | no | 100% | 1051 | skip (passive combo-tracking buff) |
| 392993  | Xuen's Battlegear | no | 100% | 1 | skip (set-bonus-style passive aura) |
| 1236994 | Potion of Recklessness | no | 100% | 6 | skip (consumable, not a class CD) |

**Notes on splits / alt-builds:**
- **The major-CD picture for Windwalker is genuinely thin.** Touch of Karma is the only CD currently tracked, and it's a defensive. The signature offensive majors — Storm, Earth, and Fire (137639), Serenity (152173), Invoke Xuen (123904) — are all BuffsTable-invisible across this 8-fight sample, matching the 2026-04-16 Pass-2 findings. Windwalker scoring on cooldown_usage rests on a single defensive CD pressed med=11 times, which severely under-represents the spec.
- **Hero-talent landscape:** Combat Wisdom (129914) at 100%, Skyfire Heel (1248705) at 100%, Flurry Charge (451021) at 100%, Momentum Boost (451297) at 100% — these are all **Conduit of the Celestials** hero-tree passives. The cohort is clearly Conduit-dominant. **Shado-Pan** hero-tree passives don't appear in the top 30 at the meta level a hero-tree-exclusive add would require. So no hero-tree alt-build major surfaced.
- **Rushing Wind Kick (1250554)** at 100% med=62 is a Conduit of the Celestials key cooldown buff — could be a tracking candidate, but med=62 with a 24s CD suggests this is the per-press aura. Worth investigating in a follow-up sampler retry as a possible Conduit-tied major CD add.
- **Recommendation: sampler retry NOT currently warranted given WCL spend cap.** The cohort showed no reliable BuffsTable surface for SEF / Serenity / Xuen. Confirming this would require a CastsTable detection path — which is a larger engine change than this audit can scope. For now, Touch of Karma stays as the one tracked WW major; the cooldown_usage category for WW will inherently weight defensive press-on-CD over offensive cooldown play, which under-represents spec performance.
- **Tigereye Brew (1261724)** at med=460 is the stacking buff (every Combo Strikes adds a stack), not a press. Same skip reasoning as Resto Druid Barkskin / Guardian Ironfur — would saturate cooldown_usage at 100% if added.

### Interrupts

- **Spell name (id):** `Spear Hand Strike` (116705) — same kick as BRM and MW
- **Cast type:** instant melee kick (15s CD)
- **Sample observed kicks per fight (median):** not surfaced in BuffsTable (kicks are debuffs on target / cast events, not self-buffs). Needs CastsTable.
- **Recommended expected count for scoring:** 15 (DPS role default). Spear Hand Strike 15s CD is well-suited to the default benchmark.
- **No-baseline-kick callout:** N/A — WW has Spear Hand Strike.

### Dispels

- **In-spec dispel ability:** **Detox (218164)** — the limited Brewmaster/Windwalker variant. Poison + Disease only.
- **Schools cleansable on allies:** Poison, Disease
- **Schools the engine should credit WW for:** `{Poison, Disease}` — NOT Magic.
- **Notes:** This is the **same partial-Detox story as Brewmaster** and the second half of the BRM-lesson-3 fix. Currently `class_has_dispel(Monk)=True` over-credits WW for Magic-cleanses they cannot perform. The dispel-school registry fix is the same line item that's been pending since the 2026-04-26 BRM audit; explicitly producing the WW entry here closes the loop.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Paralysis | 115078 | incapacitate | baseline single-target 60s incap |
| Leg Sweep | 119381 | stun (AoE) | baseline AoE 5s stun, 60s CD — universal Monk pull-opener |
| Ring of Peace | 116844 | disorient (AoE) | talent, AoE knockback + disorient |
| Disable | 116095 | slow + root | baseline ground slow that roots on second hit |

### Recommended changes

1. `app/scoring/cooldowns.py` `(10, "Windwalker")`: **no high-confidence adds.** The sampler did not surface SEF / Serenity / Xuen / Whirling Dragon Punch as BuffsTable auras. Touch of Karma stays as the one tracked CD. **Optional follow-up:** investigate Rushing Wind Kick (1250554) as a Conduit-of-the-Celestials hero-tree CD add candidate (100% consensus, med=62, ~24s CD).
2. **Dispel registry** (new): `(10, "Windwalker") = {Poison, Disease}`. NOT Magic.
3. **Interrupt benchmark override:** none. DPS role default of 15 expected kicks fits Spear Hand Strike's 15s CD.
4. **Talent-gate flags:** none active. If SEF / Serenity ever get a CastsTable detection path, flag both as alt-build branches at that point.

### Top-cohort raw output reference

```
=== Aggregate over 8 Monk Windwalker fights ===

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    122470      100%        11   Touch of Karma  [Touch of Karma]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      451297   100%      2619   Momentum Boost
     1266687   100%      1034   Alnscorned Essence
      392993   100%         1   Xuen's Battlegear
      196741   100%      1051   Hit Combo
     1249758   100%       141   Combo Strikes: Fists of Fury
     1266686   100%        66   Alnsight
     1249757   100%       221   Combo Strikes: Blackout Kick
      449609   100%        40   Lighter Than Air
      116768   100%       118   Blackout Kick!
      414143   100%       191   Yu'lon's Grace
     1249753   100%       197   Combo Strikes: Rising Sun Kick
      129914   100%       105   Combat Wisdom
     1248705   100%       772   Skyfire Heel
      113656   100%       141   Fists of Fury
     1236994   100%         6   Potion of Recklessness
      325202   100%       104   Dance of Chi-Ji
      392883   100%       248   Vivacious Vivification
      120954   100%         9   Fortifying Brew
      451021   100%       885   Flurry Charge
      450574   100%         1   Flow of Chi
      383781   100%        12   Algeth'ar Puzzle
     1249756   100%       251   Combo Strikes: Tiger Palm
     1261724   100%       460   Tigereye Brew
      451298   100%       141   Momentum Boost
     1249754   100%       102   Combo Strikes: Spinning Crane Kick
      202090   100%       251   Teachings of the Monastery
     1229746   100%        52   Arcanoweave Insight
      451214   100%         9   Whirling Steel
     1250554   100%        62   Rushing Wind Kick
     1250987   100%        61   Combo Strikes: Rushing Wind Kick
```

---

## Open questions for review

1. **Mistweaver hero-tree dual-tracking:** Both `443113 Strength of the Black Ox` (Master of Harmony) and `443592 Unity Within` (Conduit of the Celestials) appear at 100% in the 8-fight cohort. Cleanest interpretation is to track both with talent-aware skip handling alt-builds (BRM Keg-vs-Black-Ox precedent). Logan: confirm whether one of these auras fires regardless of hero-tree pick (would change the recommendation to track only the genuinely-exclusive one).
2. **MW group-heal talent swap (Revival 115310 vs Restoral 388615):** Pass-2 noted Revival has no caster aura (heal-burst event with no persistent buff). Same likely true for Restoral. If neither produces a BuffsTable signal, the talent swap is fundamentally undetectable via the current path and should not be added — they'd be tracked but always score 0, which the talent-aware skip is meant to *fix*. Options: (a) skip both, accept the spec-coverage gap; (b) build a CastsTable path for these. Logan's call on prioritization.
3. **Add Mistweaver to `HEALER_SPECS_WITH_INTERRUPT`?** Spear Hand Strike (116705) is baseline on MW, same as Rebuke (Holy Pally) and Wind Shear (Resto Shaman). The current set excludes MW which means utility scoring under-credits MW kicks. **Strong recommend yes**, but flagging for explicit Logan sign-off since this changes how MW utility scoring computes today.
4. **Windwalker offensive-CD coverage gap:** The current single-CD list (Touch of Karma, defensive) doesn't represent how WW actually plays. SEF / Serenity / Xuen are all BuffsTable-invisible. Two paths forward: (a) build a CastsTable detection path for non-aura major CDs across multiple specs (broad engine work), (b) accept the gap and weight WW's cooldown_usage category lower. Path (a) also unblocks Survival Hunter (Spearhead), Rogue Assassination (Deathmark/Vendetta), Affliction Warlock (Darkglare), and several others — the WW gap is one instance of a class-wide pattern.
5. **Rushing Wind Kick (1250554) as a possible WW major CD add:** 100% consensus, med=62, ~24s CD. Conduit of the Celestials hero-tree-tied. Worth a focused sampler retry on a non-Conduit hero-tree pick to see if it disappears. If yes, it's an alt-build add; if no (it's somehow universal), it's a baseline add. Currently leaning Conduit-tied based on the cohort evidence.
6. **Brewmaster dispel-fix codification scope:** Now that all three Monk specs have explicit registry entries proposed below, the codification PR can either land (a) Monk-only as the BRM lesson-3 demo, or (b) wait for more of the audit to complete and land all classes' dispel registry entries together. Logan's call on PR boundary.

## Confidence

- **Sample size:** Mistweaver 8 fights / Windwalker 8 fights = 16 distinct top-cohort fights. **Both clear the 5-fight bar; no retry needed.** Brewmaster summary is from prior audit (2026-04-26).
- **High confidence** on **Mistweaver hero-tree adds** (Strength of the Black Ox 443113 and Unity Within 443592 both at 100% med>10). The only ambiguity is whether one fires across both hero trees (open question 1 above) — but both adds are net-positive even if one ends up being the dominant baseline.
- **High confidence** on **dispel-school splits**:
  - `(10, "Brewmaster") = {Poison, Disease}` — verified from BRM audit
  - `(10, "Mistweaver") = {Magic, Poison, Disease}` — Detox 115450 is baseline kit, well-documented retail behavior
  - `(10, "Windwalker") = {Poison, Disease}` — same Detox 218164 as BRM
- **High confidence** on **MW interrupt addition** to `HEALER_SPECS_WITH_INTERRUPT`. Spear Hand Strike is baseline on MW; this is a static class fact, not a sample-dependent finding.
- **Medium confidence** on the Windwalker no-action recommendation. The cohort cleanly showed no SEF / Serenity / Xuen surface at the 8-fight scale, but a one-off sampler retry might still find Rushing Wind Kick or another Conduit-tied aura worth tracking. Not pursued here to respect the WCL spend cap; flagged in open question 5.
- **Lower confidence** on the **Mistweaver group-heal talent swap (Revival/Restoral)** — recommended-add list flags both as candidates, but Pass-2 evidence suggests neither produces a BuffsTable signal, which would make tracking them functionally equivalent to not tracking them. Logan should confirm before codification.
- **No retry triggered.** Both non-BRM specs cleared the 5-fight bar on the first run.
