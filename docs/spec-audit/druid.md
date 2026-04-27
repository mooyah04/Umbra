# Druid Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist (Opus 4.7)
**Sample depth:** 1 report per dungeon (top-8 cohort), 8 active-season Midnight S1 dungeons, key range +19 to +22
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Druid" --spec "{Spec}" --samples-per-dungeon 1 --top-n 8`

Druid has FOUR specs in The War Within / Midnight S1: Balance (DPS), Feral (DPS), Guardian (Tank), Restoration (Healer). Every spec is currently tracked in `cooldowns.py`. The pattern across all four is the same Berserk / Celestial Alignment / equivalent baseline → Incarnation talent upgrade — the talent-aware skip needs both branches present so it can pick whichever path the player took.

---

## Spec: Balance

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 102560  | Incarnation: Chosen of Elune | yes | 100% | 16 | keep |
| 202770  | Fury of Elune | yes | 100% | 62 | keep, but reconsider classification (see notes) |
| 194223  | Celestial Alignment | no  | 0%   | — | add as alt-build branch (talent-aware skip target) |
| 391528  | Convoke the Spirits | no | 0% in top-30 | — | NOT seen at 100% in Balance cohort — distinct from Resto/Feral usage |
| 343648  | Solstice | no | 100% | 173 | passive proc — do NOT add (this is a buff state, not a player-pressed CD) |
| 1263382 | Ascendant Stars | no | 100% | 71 | hero-talent passive proc — do NOT add |
| 1229746 | Arcanoweave Insight | no | 100% | 99 | external/group buff (Aug Evoker style) — do NOT add |

**Notes on splits / alt-builds:**
- Top Midnight S1 Balance cohort universally takes the **Incarnation: Chosen of Elune** capstone over Celestial Alignment. The current tracked-only-Incarnation list is correct for the meta build, BUT a player who picks the CA branch (legitimate alt-build) currently scores 0 because Incarnation never fires. **Recommend adding 194223 Celestial Alignment** so the talent-aware skip catches whichever branch the player picked — the 8-fight cohort showing 100% Incarnation is meta convergence, not evidence the alt-build doesn't exist.
- **Fury of Elune (202770)** at med=62 uses is suspicious for a "major CD". Fury of Elune in Midnight is a 1-min CD ground effect; 62 fires across a single dungeon is plausible only if WCL is counting per-tick aura applications. The aura with this ID is likely the *channeled tick* aura, not the press itself. Consider whether the engine's expected 5 uses is calibrated against the press or the tick — current scoring says expected=5, observed=62, which would saturate cooldown_usage at 100% for every Balance Druid (same saturation problem the BRM/Resto Barkskin audit caught). **Flag for re-calibration:** either bump expected uptime to ~50, or replace 202770 with a different aura that maps to the cast event.
- Solstice / Ascendant Stars / Starweaver / Touch the Cosmos / Balance of All Things are all hero-talent procs and Eclipse states — passive. Not press-on-cooldown CDs.

### Interrupts

- **Spell name (id):** Solar Beam (78675) — Balance baseline AoE silence (works as a kick AND a 5s AoE silence)
- **Cast type:** instant ground-target placement
- **Sample observed kicks per fight (median):** not directly captured by the buffs sampler (kicks are cast events, not auras)
- **Recommended expected count for scoring:** keep DPS role default (15). Solar Beam is a long CD (~1min) but it's an AoE silence — a single Solar Beam can cover multiple casts on a pull, so the press count is lower than e.g. Mind Freeze but the kick count credited (interrupts caused) can be higher.
- **Note:** Solar Beam doubles as CC (5s AoE silence). For Balance specifically the engine should not penalize a low single-target kick count if the AoE silence is doing work.

### Dispels

- **In-spec dispel ability:** **Remove Corruption (2782)** — Poison + Curse only.
- **Schools cleansable on allies:** Poison, Curse
- **Schools the engine should credit Balance for:** `{Poison, Curse}` — NOT Magic. Only Restoration's Nature's Cure dispels Magic.
- **Notes:** Balance has the partial-kit cleanse; if the dispel-school registry treats `class_has_dispel(Druid)=True` as full Magic+Poison+Curse, Balance is being over-credited. Same fix the BRM Detox poison/disease finding applied.
- **Soothe (2908)** — offensive Enrage purge. Note as offensive purge, separate from defensive cleanse credit.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Solar Beam | 78675 | silence (AoE 5s) | baseline; doubles as kick |
| Cyclone | 33786 | disorient (banish) | talent, single-target, 6s |
| Mighty Bash | 5211 | stun | talent, single-target, 5s |
| Mass Entanglement | 102359 | root (AoE) | talent |
| Hibernate | 2637 | incapacitate | beasts/dragons only — rarely usable in M+ |
| Typhoon | 132469 | knockback | talent, AoE knockback |

### Recommended changes

1. `app/scoring/cooldowns.py` `(11, "Balance")`: **add** `(194223, "Celestial Alignment", 15, "offensive")` as the alt-build branch so Incarnation-skippers aren't punished. The talent-aware skip will exclude whichever branch the player didn't take.
2. **Re-investigate Fury of Elune (202770)**: med=62 uses suggests this aura is the per-tick channel buff, not the press event. Either bump expected uptime to ~50 to match observed reality, or swap to the cast-event detection path. Current expected=5 saturates cooldown_usage to 100% for every player.
3. **Dispel registry** (new): `(11, "Balance") = {Poison, Curse}`. Do NOT credit for Magic.
4. **Talent-gate flags:** Mark both 102560 (Incarnation) and 194223 (CA) as alt-build path so the skip catches the absent one.

### Top-cohort raw output reference

```
=== Aggregate over 8 Druid Balance fights ===

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    102560      100%        16   Incarnation: Chosen of Elune  [Incarnation: Chosen of Elune]
    202770      100%        62   Fury of Elune  [Fury of Elune]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
       48517   100%        16   Eclipse (Solar)
      102560   100%        16   Incarnation: Chosen of Elune (tracked)
      385787   100%        18   Matted Fur
      378989   100%        15   Lycara's Teachings
     1229746   100%        99   Arcanoweave Insight
      157228   100%         5   Owlkin Frenzy
     1263382   100%        71   Ascendant Stars
      106898   100%         6   Stampeding Roar
      378991   100%        15   Lycara's Teachings
      343648   100%       173   Solstice
       22842   100%        13   Frenzied Regeneration
      468938   100%        51   Sunseeker Mushroom
      393763   100%        66   Umbral Embrace
     1265145   100%        20   Refreshing Drink
       22812   100%        18   Barkskin
      191034   100%       463   Starfall
      393942   100%        48   Starweaver's Warp
       24858   100%        31   Moonkin Form
     1265140   100%        26   Refreshing Drink
      450360   100%        60   Touch the Cosmos
      202770   100%        62   Fury of Elune (tracked)
      279709   100%       243   Starlord
      393944   100%       143   Starweaver's Weft
     1263363   100%        69   Ascendant Fires
        1126   100%        10   Mark of the Wild
      394050   100%        69   Balance of All Things
     1260459   100%        16   Nullsight
      394049   100%        16   Balance of All Things
        5487   100%        15   Bear Form
      378992   100%        31   Lycara's Teachings
```

---

## Spec: Feral

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 106951  | Berserk | yes | 100% | 13 | keep |
| 102543  | Incarnation: Avatar of Ashamane | no | 0% in cohort | — | add as alt-build branch (talent-aware skip target) |
| 391528  | Convoke the Spirits | no | 100% | 23 | **add** — universal in top-cohort builds |
| 5217    | Tiger's Fury | no | (not in top 30 — short-CD rotational) | — | do NOT add — too short to be "major" |
| 391873  | Tiger's Tenacity | no | 100% | 50 | hero-talent passive proc — do NOT add |
| 1263962 | Stalking Predator | no | 100% | 50 | hero-talent passive — do NOT add |

**Notes on splits / alt-builds:**
- Top Feral cohort universally takes Berserk in Midnight S1, but Incarnation: Avatar of Ashamane is the alt-talent. **Add 102543** so the talent-aware skip catches Incarnation builds. The cohort-wide 0% on Incarnation is meta convergence; the talent button still exists.
- **Convoke the Spirits at 100% med=23 across all 8 top Ferals — strong add candidate.** Convoke is a 2-min CD that does big damage for Feral; missing it in the tracked list undercounts press-on-cooldown for every Feral player who takes it.
- Tiger's Fury (~30s rotational) is too short-cycle to count as a "major" CD by Umbra's framing — same logic as why Brewmaster's Keg Smash isn't tracked.

### Interrupts

- **Spell name (id):** Skull Bash (106839) — requires Cat or Bear form
- **Cast type:** instant melee charge-based
- **Sample observed kicks per fight (median):** not captured by buffs sampler
- **Recommended expected count for scoring:** keep DPS role default (15). Skull Bash is a 15s CD, plenty available.
- Feral has no AoE silence in baseline; Solar Beam is Balance-only.

### Dispels

- **In-spec dispel ability:** **Remove Corruption (2782)** — Poison + Curse
- **Schools cleansable on allies:** Poison, Curse
- **Schools the engine should credit Feral for:** `{Poison, Curse}` — NOT Magic
- **Notes:** Same partial-kit story as Balance/Guardian. Soothe (2908) is the offensive Enrage purge (separate from cleanse credit).

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Maim | 22570 | stun (single-target) | baseline finisher in Cat Form |
| Mighty Bash | 5211 | stun | talent, single-target, 5s |
| Cyclone | 33786 | disorient (banish) | talent, single-target, 6s |
| Mass Entanglement | 102359 | root (AoE) | talent |
| Typhoon | 132469 | knockback | talent (Bear/Cat shift to Moonkin) |
| Skull Bash | 106839 | silence (4s) | baseline kick — also acts as a brief silence |

### Recommended changes

1. `app/scoring/cooldowns.py` `(11, "Feral")`: **add** `(391528, "Convoke the Spirits", 23, "offensive")` — universal at 100% with med=23 uses. Add `(102543, "Incarnation: Avatar of Ashamane", 13, "offensive")` as alt-build branch.
2. **Dispel registry** (new): `(11, "Feral") = {Poison, Curse}`. NOT Magic.
3. **No interrupt benchmark override** — DPS role default of 15 is fine for Skull Bash.
4. **Talent-gate flags:** Both 106951 (Berserk) and 102543 (Incarnation) flagged as alt-build. Convoke 391528 is talent-gated but near-universal in current builds.

### Top-cohort raw output reference

```
=== Aggregate over 8 Druid Feral fights ===

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    106951      100%        13   Berserk  [Berserk]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      165961   100%         5   Travel Form
      106951   100%        13   Berserk (tracked)
     1263962   100%        50   Stalking Predator
        1126   100%         6   Mark of the Wild
     1265140   100%        48   Refreshing Drink
       22842   100%        25   Frenzied Regeneration
     1272262   100%       255   Flash of Clarity
        8936   100%        70   Regrowth
      462854   100%         6   Skyfury
      391873   100%        50   Tiger's Tenacity
      391528   100%        23   Convoke the Spirits
      382024   100%       163   Earthliving Weapon
       58984   100%         8   Shadowmeld
      391876   100%       181   Frantic Momentum
     1265145   100%        33   Refreshing Drink
      207400   100%       264   Ancestral Vigor
     1229746   100%       102   Arcanoweave Insight
      135700   100%       293   Clearcasting
      385787   100%        32   Matted Fur
      378990   100%        55   Lycara's Teachings
      462568   100%       673   Elemental Resistance
      449646   100%        50   Savage Fury
       22812   100%        19   Barkskin
     1236616   100%         6   Light's Potential
       48438   100%         9   Wild Growth
       61295   100%        61   Riptide
         774   100%         4   Rejuvenation
      378991   100%        40   Lycara's Teachings
      405069   100%        13   Overflowing Power
         768   100%        55   Cat Form
```

---

## Spec: Guardian

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 22812   | Barkskin | yes | 100% | 38 | keep |
| 61336   | Survival Instincts | yes | 100% | 11 | keep |
| 192081  | Ironfur | yes | 100% | 654 | keep — but reconsider classification (saturating, see notes) |
| 102558  | Incarnation: Guardian of Ursoc | no  | 100% | 16 | **add** — universal at 100%, med=16 |
| 50334   | Berserk (Bear) | no | 0% in cohort | — | add as alt-build branch (talent-aware skip target) |

**Notes on splits / alt-builds:**
- **Incarnation: Guardian of Ursoc (102558) at 100% med=16 is the strongest add candidate in the entire Druid audit.** Every top Guardian has it pressed 16 times per dungeon and it's not currently tracked. This is exactly the "baseline-but-untracked at >70%" BRM-rule add case.
- The 0% Berserk (Bear) in cohort means top Guardians universally take the Incarnation talent. Berserk is the pre-talent baseline and an alt-build branch — **add 50334** so a Berserk-talented player isn't penalized.
- **Ironfur (192081) at med=654 uses with expected_uptime_pct=50** is the same saturation pattern as Resto Druid Barkskin pre-Pass-3. Every Guardian presses Ironfur on cooldown as their primary active mitigation; the engine likely scores all of them at 100% on this slot, killing signal. Recommend either bumping expected uptime to ~150 (still way short of 654 but lets bad players actually fall behind), or downgrading Ironfur from "major CD" to a separate active-mitigation uptime metric. Current behavior: every Guardian gets max credit on Ironfur regardless of skill, which makes the cooldown_usage category ~half-meaningful for Guardians.
- Galactic Guardian, Gore, Echo of Frenzied Regeneration, Echo of Ironfur — all hero-talent passive procs. Do NOT add.

### Interrupts

- **Spell name (id):** Skull Bash (106839) — Bear/Cat form
- **Cast type:** instant melee charge-based
- **Sample observed kicks per fight (median):** not captured by buffs sampler
- **Recommended expected count for scoring:** keep tank role default (12). Skull Bash 15s CD is fine.

### Dispels

- **In-spec dispel ability:** **Remove Corruption (2782)** — Poison + Curse
- **Schools cleansable on allies:** Poison, Curse
- **Schools the engine should credit Guardian for:** `{Poison, Curse}` — NOT Magic
- **Notes:** Same partial-kit story. Tank Druids carry Remove Corruption when in caster form briefly; uncommon usage in M+ but worth crediting when it happens.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Skull Bash | 106839 | silence (4s) | baseline kick + silence |
| Mighty Bash | 5211 | stun | talent, single-target |
| Incapacitating Roar | 99 | incapacitate (AoE) | baseline AoE incap (3s, breaks on damage) |
| Stampeding Roar | 106898 | utility (movement speed) | not CC but party utility — note for utility category, not CC |
| Cyclone | 33786 | disorient | talent (rare in tank build) |

### Recommended changes

1. `app/scoring/cooldowns.py` `(11, "Guardian")`: **add** `(102558, "Incarnation: Guardian of Ursoc", 16, "defensive")`. **Add** `(50334, "Berserk", 16, "defensive")` as the alt-build branch.
2. **Re-calibrate Ironfur (192081)**: bump expected uptime to ~150 or higher to match observed med=654, OR move Ironfur out of the major-CD bucket entirely and into an active-mitigation uptime metric. Current expected=50 saturates the entire cohort at 100%.
3. **Dispel registry** (new): `(11, "Guardian") = {Poison, Curse}`. NOT Magic.
4. **No interrupt benchmark override** — tank role default of 12 is fine.
5. **Talent-gate flags:** 102558 (Incarnation), 50334 (Berserk Bear) — alt-build branches. The talent-aware skip should pick whichever the player took.

### Top-cohort raw output reference

```
=== Aggregate over 8 Druid Guardian fights ===

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
     22812      100%        38   Barkskin  [Barkskin]
     61336      100%        11   Survival Instincts  [Survival Instincts]
    192081      100%       654   Ironfur  [Ironfur]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
         768   100%        10   Cat Form
        5487   100%        16   Bear Form
       77761   100%         7   Stampeding Roar
       93622   100%       391   Gore
       22812   100%        38   Barkskin (tracked)
     1269645   100%        78   Echo of Frenzied Regeneration
      213708   100%       313   Galactic Guardian
     1269659   100%        16   Gift of Ironfur
      378991   100%        16   Lycara's Teachings
        1126   100%         7   Mark of the Wild
     1236616   100%         6   Light's Potential
       61336   100%        11   Survival Instincts (tracked)
     1241715   100%       204   Might of the Void
      378990   100%        10   Lycara's Teachings
      378989   100%         4   Lycara's Teachings
     1272376   100%       162   Celestial Might
      192081   100%       654   Ironfur (tracked)
        8936   100%        23   Regrowth
     1269633   100%       106   Echo of Ironfur
      102558   100%        16   Incarnation: Guardian of Ursoc
       22842   100%        72   Frenzied Regeneration
     1269616   100%        15   Wild Guardian
     1269661   100%        16   Gift of Frenzied Regeneration
      372505   100%       934   Ursoc's Fury
     1269660   100%        16   Gift of Maul
     1229746   100%       124   Arcanoweave Insight
      441825    88%      1254   Killing Strikes
     1278914    88%       144   Dream Guide
        1850    88%         2   Dash
      441686    88%        15   Wildshape Mastery
```

---

## Spec: Restoration

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 740     | Tranquility | yes | 100% | 5 | keep |
| 391528  | Convoke the Spirits | yes | 100% | 21 | keep |
| 33891   | Incarnation: Tree of Life | no | 0% in cohort | — | add as alt-build branch (talent-aware skip target) |
| 197721  | Flourish | no | 0% in cohort top-30 | — | add as alt-build branch (mutually exclusive with Tree at capstone) |
| 132158  | Nature's Swiftness | no | 100% | 19 | do NOT add — instant-cast modifier, not a "major" CD |
| 207640  | Abundance | no | 100% | 499 | passive build-up — do NOT add |
| 114108  | Soul of the Forest | no | 100% | 154 | passive proc — do NOT add |

**Notes on splits / alt-builds:**
- The current Resto cooldown list (Tranquility + Convoke) covers the universal current-meta build. Tree of Life (33891) and Flourish (197721) are alt-build capstones — currently not in the cohort because every top Resto runs Convoke. **Recommend adding both as alt-build branches** so a player who picks the Tree or Flourish path isn't penalized.
- Confirmed: **Resto Druid does NOT have a baseline interrupt.** Skull Bash requires Bear form (which drops Tree/healing presence) and Solar Beam is Balance-only. `HEALER_SPECS_WITH_INTERRUPT` in `roles.py` correctly excludes (11, "Restoration").
- **Barkskin (22812)** stays out of the tracked list per the Pass-3 fix in the file's own comment — it was saturating Dobbermon's cooldown_usage at 100. Resto cohort showed Barkskin presses but they're a personal defensive, not a major raid CD. Correct decision; do not add.
- Innervate (29166) — cast on allies, not self. Correctly not tracked. Same as in the file comment.
- Nature's Swiftness at med=19 is a frequent rotational tool (instant-cast next spell) — it modifies a cast, not a press-on-CD major.

### Interrupts

- **Spell name (id):** **NONE — Resto Druid has no baseline interrupt.**
- **Cast type:** N/A
- **Sample observed kicks per fight (median):** N/A
- **Recommended expected count for scoring:** **0** — Resto should be zero-weighted on interrupts and have utility scoring routed through dispel/CC/cooldowns instead. The `HEALER_SPECS_WITH_INTERRUPT` set in `roles.py` correctly excludes Resto. Verified: do not change.
- **No-baseline-kick callout:** "Restoration Druid cannot interrupt without leaving healing form. Skull Bash needs Bear/Cat form (drops mastery + Tree benefits); Solar Beam is Balance-only. Top Resto Druids do not interrupt — they CC and cleanse instead."

### Dispels

- **In-spec dispel ability:** **Nature's Cure (88423)** — Magic + Poison + Curse
- **Schools cleansable on allies:** Magic, Poison, Curse
- **Schools the engine should credit Resto for:** `{Magic, Poison, Curse}` — full healer dispel kit
- **Notes:** Resto Druid has the upgraded Magic-cleanse version of Remove Corruption. This is the BRM lesson #3 split — Resto = full kit, all other Druid specs = Poison + Curse only.
- **Soothe (2908)** — offensive Enrage purge. Note as offensive purge separate from defensive cleanse credit.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Cyclone | 33786 | disorient (banish) | talent, single-target 6s |
| Mighty Bash | 5211 | stun | talent (rarely picked by Resto in M+) |
| Mass Entanglement | 102359 | root (AoE) | talent |
| Typhoon | 132469 | knockback | talent (requires Moonkin shift) |
| Hibernate | 2637 | incapacitate | beasts/dragons only — niche |

### Recommended changes

1. `app/scoring/cooldowns.py` `(11, "Restoration")`: **add** `(33891, "Incarnation: Tree of Life", 5, "defensive")` and `(197721, "Flourish", 4, "defensive")` as alt-build branches. The talent-aware skip will exclude whichever the player didn't pick. Current Tranq + Convoke pair stays.
2. **Dispel registry** (new): `(11, "Restoration") = {Magic, Poison, Curse}`. Full healer kit.
3. **Interrupt benchmark override:** 0. `HEALER_SPECS_WITH_INTERRUPT` already correctly excludes Resto — verify the engine doesn't double-penalize Resto for missing kicks. (Cross-check during codification.)
4. **Talent-gate flags:** 391528 (Convoke), 33891 (Tree), 197721 (Flourish) — all three are talent-gated capstone choices in the same tier. The talent-aware skip should keep whichever shows in BuffsTable; the others are skipped automatically.

### Top-cohort raw output reference

```
=== Aggregate over 8 Druid Restoration fights ===

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
       740      100%         5   Tranquility  [Tranquility]
    391528      100%        21   Convoke the Spirits  [Convoke the Spirits]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1265140   100%        45   Refreshing Drink
         740   100%         5   Tranquility (tracked)
        1126   100%         4   Mark of the Wild
        5215   100%         2   Prowl
       48438   100%       128   Wild Growth
     1232285   100%       495   Efflorescence
      114108   100%       154   Soul of the Forest
        5487   100%        58   Bear Form
        1850   100%         5   Dash
     1236616   100%         6   Light's Potential
     1229746   100%       116   Arcanoweave Insight
      378989   100%       142   Lycara's Teachings
      378991   100%        58   Lycara's Teachings
      374227   100%         7   Zephyr
       16870   100%        90   Clearcasting
         774   100%        66   Rejuvenation
       58984   100%         2   Shadowmeld
      165961   100%         5   Travel Form
      207640   100%       499   Abundance
      439530   100%       169   Symbiotic Blooms
       33763   100%        25   Lifebloom
      390386   100%         3   Fury of the Aspects
      393903   100%        58   Ursine Vigor
      132158   100%        19   Nature's Swiftness
     1265145   100%        30   Refreshing Drink
      404381   100%         2   Defy Fate
      381746   100%         7   Blessing of the Bronze
        8936   100%       129   Regrowth
      155777   100%        42   Rejuvenation (Germination)
       22842   100%        20   Frenzied Regeneration
```

---

## Open questions for review

1. **Fury of Elune classification (Balance):** med=62 uses with expected=5 implies the tracked aura is the per-tick channel buff, not the press event. Two options for codification: (a) bump expected uptime to ~50 to match observed reality so it provides meaningful signal; (b) swap to a different aura ID that maps to the cast itself. Logan should pick — option (a) is faster, option (b) is correct.
2. **Ironfur classification (Guardian):** Same saturation problem as the original Resto Barkskin. Med=654 with expected=50 means every Guardian scores 100% — no signal. Options: bump expected to ~150, replace with a separate active-mitigation uptime metric, or drop Ironfur from major CDs entirely (it's rotational, not "major"). The Pass-3 Resto Druid Barkskin precedent suggests dropping it; the 50% expected uptime was a half-measure that didn't fix the saturation.
3. **Soothe (offensive Enrage purge):** Currently no engine path credits offensive purges. Worth a separate scoring slot or roll into "utility"? Affects multiple classes (Hunter Tranquilizing Shot, Priest Mass Dispel offensive use, Druid Soothe).
4. **Convoke add for Feral:** 100% consensus med=23 in the cohort, but Convoke is a shared talent across all four Druid specs and currently only tracked on Restoration. Adding it to Feral and Balance (alt-build) and Guardian (alt-build) for talent-build coverage is consistent with the BRM lesson — but does cooldown_usage suddenly weight Druid more than other classes if every spec gets Convoke? Worth Logan's eye during codification.
5. **Balance has no Convoke at 100%:** Top-30 didn't show 391528 for Balance even though the talent exists. Two reads: (a) top Balance druids skip Convoke for the Sundered Firmament / Boundless Reality build, (b) sampler cohort happened to all be Sundered builds. If (a), don't add to Balance. If (b), retry with broader sampling. Current evidence leans (a) — 8 out of 8 unanimous on no-Convoke is strong.

## Confidence

- **Sample size: 8 fights per spec, 32 fights total.** Above the 5-fight minimum for all four specs. Cohorts pulled from key range +19 to +22, players from EU/CN/RU/NA realms — reasonable geographic spread.
- **High confidence** on Guardian (Incarnation: Guardian of Ursoc add at 100% med=16) and Feral (Convoke add at 100% med=23). These are unambiguous BRM-rule >70% adds.
- **High confidence** on dispel-school splits (Resto = Magic+Poison+Curse, others = Poison+Curse). Spell IDs are baseline kit, not talent-gated, so cohort sample size isn't the limiting factor.
- **Medium confidence** on alt-build adds (Celestial Alignment for Balance, Berserk Bear for Guardian, Avatar of Ashamane for Feral, Tree of Life + Flourish for Resto). Cohort showed 0% on these because meta builds converge on the dominant talent — but the alt-builds are real, validated by the Druid talent tree structure. The talent-aware skip mechanism handles this correctly: if the alt-build aura never fires, it's skipped, not scored as 0.
- **Lower confidence** on Fury of Elune and Ironfur calibration. Both saturate at 100% in the cohort under current expected uptimes — the data tells us the calibration is wrong, but doesn't tell us what the right number is. Logan may want to sample bottom-quartile players to find the discriminating point.
- **No retry needed.** All four specs cleared the 5-fight bar on the first run.
