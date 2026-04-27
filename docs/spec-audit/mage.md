# Mage Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 report per dungeon, top-8 per dungeon scan, 8 active-season Midnight S1 dungeons (Windrunner Spire, Maisara Caverns, Magister's Terrace, Algeth'ar Academy, Nexus-Point Xenas, Skyreach, Pit of Saron, Seat of the Triumvirate)
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Mage" --spec "{Arcane|Fire|Frost}" --samples-per-dungeon 1 --top-n 8`
**Fights sampled:** Arcane 8 / Fire 8 / Frost 8 (24 distinct top players in +18 to +21 range)

> Class IDs verified from `app/scoring/roles.py`: Mage is class_id `8`. All three specs (Arcane, Fire, Frost) are DPS. Counterspell (2139) is the universal kick — ranged, instant, 24s CD with a 6s school lockout. Remove Curse (475) is the Curse-only defensive cleanse, baseline for all three specs. Spellsteal (30449) is an offensive Magic purge from enemies (steals one buff to the mage); it is NOT a defensive cleanse and should not be credited as one.

---

## Spec: Arcane

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 365362  | Arcane Surge | yes             | 100%        | 16          | keep |
| 110960  | Greater Invisibility | no       | 100%        | 3           | consider add as defensive (signature Arcane personal CD; 90s/2min CD reset talented) |
| 55342   | Mirror Image | no              | 100%        | 10          | hold (rotational decoy ~80s CD with 100% consensus; if added would mirror the Frost slot — see Open questions) |
| 235450  | Prismatic Barrier | no          | 100%        | 43          | skip (rotational absorb shield, not a "major" CD; high reapply count saturates the way Ignore Pain did for Prot) |
| 263725  | Clearcasting | no              | 100%        | 193         | skip (passive proc, fires off rotational mana spends) |
| 394195  | Overflowing Energy | no         | 100%        | 389         | skip (passive crit-stack proc) |
| 384452  | Arcane Salvo | no              | 100%        | 1           | skip (1 use median — looks like a Sunfury hero-talent cap proc, not a press) |
| 1242974 | Arcane Salvo (variant) | no    | 100%        | 2498        | skip (passive stacking aura, 2.5k uses confirms it's a proc tracker) |
| 384858  | Orb Barrage | no               | 100%        | 1           | skip (talent proc) |
| 384651  | Charged Orb | no               | 100%        | 1           | skip (talent proc) |
| 342246  | Alter Time | no                | 100%        | 10          | skip (utility CD — rewinds health/position; not a damage/defensive major in the cooldown_usage sense) |
| 321526  | Mana Adept | no                | 100%        | 1           | skip (passive scaling buff) |
| 210126  | Arcane Familiar | no           | 100%        | 10          | skip (permanent pet aura) |

**Notes on splits / alt-builds:**
- **Arcane Surge stays as the only major CD.** 100% consensus med=16 is healthy, and the aura ID (365362) was already corrected in the 2026-04-16 Pass 2 from the cast ID (365350). No change needed.
- **Touch of the Magi (321507) confirmed absent from BuffsTable.** It applies a debuff to the enemy, not a buff on the mage. The 2026-04-16 Pass 2 removal still holds. Detection would require a debuff-on-target path that we don't currently have.
- **Evocation (12051)** does NOT appear in the top-30. It's a 6s channel (mana recovery in current builds) with no persistent self-aura that BuffsTable surfaces. Holds as untracked.
- **Time Anomaly** is a passive talent that triggers random procs on cooldown — not a player-pressed CD.
- **Mirror Image at 100% med=10 is interesting.** It's tracked for Frost as the only Frost CD (post Icy-Veins removal), but Arcane has Arcane Surge as a real CD already. Adding Mirror Image to Arcane would give the spec two CDs which better matches actual play. Logan's call on whether to mirror Frost's setup. See Open questions.
- **Greater Invisibility at 100% med=3** is the signature Arcane defensive — a 90s CD (reduced to ~60s with talents) that drops aggro and grants 25% damage reduction for 3s. If we want Arcane to have a defensive in the tracked list (Arcane currently has zero), this is the universal pick. Same shape as the Die-by-the-Sword/Enraged-Regeneration suggestion in the Warrior audit; Logan to weigh in.
- **No genuine alt-build split surfaced** in this 8-fight sample. Sunfury vs Spellslinger hero trees both show similar passive auras; neither produces a distinct major-CD aura the engine could track separately.

### Interrupts

- **Spell name (id):** `Counterspell` (2139)
- **Cast type:** instant, ranged (40 yd)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable. Counterspell applies a 6s silence debuff to the target rather than a self-buff, so it doesn't appear in any of the sampled players' aura lists. Needs a CastsTable spot-check for verification.
- **Recommended expected count for scoring:** 12-13 (slightly below the DPS role default of 15). Counterspell is on a 24s CD vs the typical 15s melee kick — that's a 60% longer cooldown, which mathematically caps Mage kicks per fight lower. In a 30-min M+ run with continuous combat, the theoretical max is ~75 kicks at 24s vs ~120 at 15s — but realistic mob-cast-window opportunity counts trim both. 12 is a defensible per-spec override.
- **No-baseline-kick callout:** N/A — all three Mage specs share Counterspell.

### Dispels

- **In-spec dispel ability:** `Remove Curse` (475)
- **Schools cleansable on allies:** `{Curse}` only — Mage's Remove Curse cannot cleanse Magic, Poison, Disease, or Enrage from allies. Curse-only.
- **Schools the engine should credit this spec for:** `{Curse}`
- **Notes:** All three Mage specs have Remove Curse baseline — it's class-wide, not spec-specific. Spellsteal (30449) is the offensive counterpart that purges one Magic buff from an enemy and copies it to the mage; this is offensive (target = enemy) and should NOT count as a defensive cleanse for utility scoring. The new dispel-school registry should encode `(8, "Arcane") = {Curse}` and similarly for Fire/Frost. Note that Curse is one of the rarer dungeon affix/mob schools — Mages cleansing Curses get less per-key opportunity than e.g. a Druid cleansing both Curse and Magic; the engine's per-class dispel benchmark in `_score_utility_*` should reflect that.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Polymorph (Sheep) | 118 | incapacitate | baseline 60s incap, beasts/humanoids/critters; universal Mage CC |
| Frost Nova | 122 | root + small AoE | baseline AoE root, ~30s CD |
| Ring of Frost | 113724 | root (AoE on cross) | talent-gated, AoE root with placement |
| Ice Nova | 157997 | root + damage | talent-gated (Frost), AoE root with damage |
| Mass Polymorph | 383121 | AoE incapacitate | talent-gated |
| Blast Wave | 157981 | AoE knockback + slow | talent-gated |
| Slow | 31589 | slow | Arcane baseline single-target slow |
| Cone of Cold | 120 | slow | baseline AoE slow |
| Dragon's Breath | 31661 | AoE disorient | Fire talent (not Arcane) |
| Counterspell | 2139 | silence (interrupt) | listed under Interrupts; the silence is part of the kick |

(All Mage specs share Polymorph + Frost Nova + Slow/Cone of Cold + Counterspell as baseline. Hero-tree and class-tree talents add Ring of Frost / Mass Poly / Blast Wave depending on build.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(8, "Arcane")`: **keep Arcane Surge.** Optionally add `(110960, "Greater Invisibility", 3, "defensive")` if we want Arcane to have a defensive in the tracked list — it's currently the only DPS spec with neither a defensive nor a second offensive tracked, so the run-page icon mix is single-CD. Optionally add `(55342, "Mirror Image", 10, "offensive")` to mirror Frost's tracked Mirror Image and give Arcane two CDs.
2. **Dispel registry** (new): `(8, "Arcane") = {Curse}` — Curse-only via Remove Curse.
3. **Interrupt benchmark override:** consider `(8, "Arcane") = 12` if we add a per-spec expected-count override path. Counterspell's 24s CD makes the 15-DPS-default optimistic for all Mages.
4. Talent-gate flags: Greater Invisibility is talented in some builds (the 90s -> 60s CD reset is a talent), but the aura itself is universal once the spec has the talent. Mirror Image is universally taken in current Arcane builds; no flag needed unless tuning shifts.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    365362      100%        16   Arcane Surge  [Arcane Surge]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      110960   100%         3   Greater Invisibility
      263725   100%       193   Clearcasting
      365362   100%        16   Arcane Surge (tracked)
      384452   100%         1   Arcane Salvo
      444754   100%        10   Slippery Slinging
      394195   100%       389   Overflowing Energy
     1236616   100%         5   Light's Potential
      414658   100%         6   Ice Cold
     1229746   100%       103   Arcanoweave Insight
      235450   100%        43   Prismatic Barrier
     1242775   100%        13   Farstrider's Step
      384858   100%         1   Orb Barrage
     1242974   100%      2498   Arcane Salvo
      384612   100%         1   Prodigious Savant
        1459   100%        10   Arcane Intellect
       55342   100%        10   Mirror Image
      321526   100%         1   Mana Adept
      342246   100%        10   Alter Time
     1223797   100%       188   Intuition
      210126   100%        10   Arcane Familiar
      384651   100%         1   Charged Orb
     1265145    88%        15   Refreshing Drink
      212653    88%        38   Shimmer
      461531    88%       191   Brainstorm
     1265140    88%        23   Refreshing Drink
     1260459    88%        15   Nullsight
     1241715    88%       158   Might of the Void
     1264426    88%         2   Void-Touched
     1217242    88%         3   Enlightened
     1266686    75%        55   Alnsight
```

---

## Spec: Fire

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 190319  | Combustion | yes               | 100%        | 25          | keep |
| 110960  | Greater Invisibility | no       | 100%        | 5           | consider add as defensive (signature Mage defensive; same case as Arcane) |
| 1242220 | Hyperthermia | no              | 100%        | 100         | skip (proc/passive aura that fires during/after Combustion windows; 100 uses confirms it's not a press) |
| 383874  | Hyperthermia (variant) | no    | 100%        | 25          | skip (the talent's secondary aura — same passive proc system) |
| 48107   | Heating Up | no                | 100%        | 729         | skip (Hot Streak precursor, rotational proc) |
| 48108   | Hot Streak! | no               | 100%        | 700         | skip (proc trigger for instant Pyroblasts, rotational not major) |
| 461531  | Brainstorm | no                | 100%        | 705         | skip (passive proc, very high count) |
| 235313  | Blazing Barrier | no            | 100%        | 45          | skip (rotational absorb shield like Prismatic Barrier on Arcane — not a major CD) |
| 1257350 | Fired Up | no                  | 100%        | 259         | skip (passive stack tracker) |
| 451073  | Glorious Incandescence | no    | 100%        | 176         | skip (passive proc, Sunfury hero-talent flavor) |
| 383637  | Fiery Rush | no                | 100%        | 75          | skip (Combustion-extender passive aura while inside the window) |
| 55342   | Mirror Image | no              | 88%         | 5           | hold (taken by most but not all top Fire builds; if Arcane/Frost adopt Mirror Image as a tracked CD, consider for Fire too — see Open questions) |
| 342246  | Alter Time | no                | 100%        | 16          | skip (utility CD — rewinds health/position; not a damage/defensive major) |
| 1242220 | Hyperthermia | (dup row above)   | -           | -           | - |

**Notes on splits / alt-builds:**
- **Combustion is solid.** Aura ID 190319, 100% consensus, med=25 uses (likely the per-tick aura count rather than press count, but consistent across all 8 samples). Keep as-is.
- **Phoenix Flames / Pyroblast / Fireball** are rotational casts, not major CDs. None surface as cooldown auras worth tracking.
- **Mirror Image consensus drops from 100% (Arcane/Frost) to 88% (Fire).** Slight build divergence — Fire builds vary on whether Mirror Image is taken vs other talent options. Below the >90% bar to add as universal but above the <50% drop bar; flag as alt-build if added.
- **Fire's Hyperthermia aura (1242220 at 100% med=100)** is the talent that turns Pyroblast/Flamestrike into instant casts during Combustion windows. The 100 median uses are per-buff-application ticks, not a player-pressed CD — same trap as Resto Druid's Barkskin or Prot's Ignore Pain. Do NOT add.
- **Greater Invisibility at 100% med=5** is the same defensive case as Arcane. Universal across all three Mage specs.
- **No genuine alt-build split for Combustion-class CDs** surfaced. Sunfury (Glorious Incandescence) vs Frostfire (TWW Frostfire bolt — though not seen here) hero-tree split is real but doesn't surface as separate trackable major-CD auras.

### Interrupts

- **Spell name (id):** `Counterspell` (2139)
- **Cast type:** instant, ranged
- **Sample observed kicks per fight (median):** Not BuffsTable-visible. Same 24s CD as Arcane/Frost.
- **Recommended expected count for scoring:** 12-13 (same case as Arcane). Fire is the most-played M+ Mage spec in current builds, but Counterspell mechanics are class-wide, so the override should apply uniformly.
- **No-baseline-kick callout:** N/A.

### Dispels

- **In-spec dispel ability:** `Remove Curse` (475)
- **Schools cleansable on allies:** `{Curse}` only
- **Schools the engine should credit this spec for:** `{Curse}`
- **Notes:** Identical to Arcane — Remove Curse is class-baseline. Spellsteal is offensive. No defensive cleanse outside Curse for any Mage spec.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Polymorph | 118 | incapacitate | baseline |
| Frost Nova | 122 | root + small AoE | baseline |
| Dragon's Breath | 31661 | AoE disorient | **Fire baseline (signature Fire CC; 8s disorient on cone)** |
| Ring of Frost | 113724 | AoE root on cross | talent-gated |
| Mass Polymorph | 383121 | AoE incapacitate | talent-gated |
| Blast Wave | 157981 | AoE knockback + slow | talent-gated |
| Cone of Cold | 120 | slow | baseline |
| Polymorph variants | various | incap | (Pig, Black Cat, etc — same mechanics as base Polymorph) |

(Dragon's Breath is the canonical Fire CC differentiator vs Arcane/Frost. 8s disorient on a 45s CD makes it a real M+ pull-control tool.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(8, "Fire")`: **keep Combustion.** Optionally add `(110960, "Greater Invisibility", 5, "defensive")` to give Fire a defensive in the tracked list (same recommendation as Arcane).
2. **Dispel registry** (new): `(8, "Fire") = {Curse}` — Curse-only via Remove Curse.
3. **Interrupt benchmark override:** consider `(8, "Fire") = 12` (same as Arcane).
4. Talent-gate flags: Greater Invisibility same as Arcane — talented uptime, aura is universal once the talent is taken. Mirror Image at 88% would need a talent-aware skip if added.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    190319      100%        25   Combustion  [Combustion]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
        1459   100%         7   Arcane Intellect
      449314   100%      1193   Mana Cascade
      414658   100%         6   Ice Cold
     1242220   100%       100   Hyperthermia
       48107   100%       729   Heating Up
      394195   100%       107   Overflowing Energy
      461531   100%       705   Brainstorm
     1229746   100%       103   Arcanoweave Insight
      342246   100%        16   Alter Time
       48108   100%       700   Hot Streak!
      458964   100%        61   Heat Shimmer
     1241715   100%       170   Might of the Void
     1260277   100%        25   Lesser Time Warp
      448604   100%       178   Spellfire Sphere
      235313   100%        45   Blazing Barrier
      190319   100%        25   Combustion (tracked)
     1236616   100%         5   Light's Potential
      383811   100%      4470   Fevered Incantation
     1257350   100%       259   Fired Up
      383874   100%        25   Hyperthermia
      383395   100%       803   Feel the Burn
      383637   100%        75   Fiery Rush
      451073   100%       176   Glorious Incandescence
      110960   100%         5   Greater Invisibility
      416714    88%         1   Intensifying Flame
     1265145    88%        15   Refreshing Drink
     1250508    88%        12   Emberwing Heatwave
       55342    88%         5   Mirror Image
      212653    88%        27   Shimmer
      108843    88%         2   Blazing Speed
```

---

## Spec: Frost

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 55342   | Mirror Image | yes               | 100%        | 6           | keep |
| 110960  | Greater Invisibility | no       | 100%        | 5           | consider add as defensive (signature Mage defensive; same case as Arcane/Fire) |
| 1247908 | Splinterstorm | no             | 100%        | 39          | hold (Frostfire / Spellslinger hero-talent rotational proc; 39 med uses suggests rotational, not a major press; verify before adding) |
| 11426   | Ice Barrier | no               | 100%        | 53          | skip (rotational absorb shield like Blazing/Prismatic Barrier; not a major CD) |
| 190446  | Brain Freeze | no              | 100%        | 99          | skip (rotational proc for instant Flurry) |
| 44544   | Fingers of Frost | no           | 100%        | 340         | skip (rotational proc) |
| 1222865 | Glacial Spike! | no            | 100%        | 62          | skip (rotational proc) |
| 205473  | Icicles | no                   | 100%        | 311         | skip (passive icicle stack tracker) |
| 1263263 | Hand of Frost | no             | 100%        | 362         | skip (passive Frostfire hero-talent stack tracker) |
| 455122  | Permafrost Lances | no         | 100%        | 45          | skip (rotational proc) |
| 1247730 | Thermal Void | no             | 100%        | 96          | skip (passive Icy-Veins-extender talent aura — note name implies it would only register *when Icy Veins is active*, see below) |
| 342246  | Alter Time | no                | 100%        | 10          | skip (utility CD) |
| 12472   | Icy Veins | no                | **0%**      | 0           | confirms 2026-04-16 Pass 2 finding — **NOT visible in any of the 8 sampled top Frost Mages' BuffsTables** |

**Notes on splits / alt-builds:**
- **Mirror Image stays as the only Frost major CD.** 100% consensus med=6 confirms the 2026-04-16 substitution still holds. The current placement is correct.
- **Icy Veins (12472) confirmed absent again.** Not in the top 30 of any Frost cohort. The 2026-04-16 Pass 2 note hypothesized "the aura ID must have changed in Midnight." This second sample reinforces that, but does NOT pin down what the correct ID is. Two candidates worth investigating in a follow-up:
  - **1247730 "Thermal Void"** at 100% med=96 — this is the talent that *extends* Icy Veins, so its aura presence implies Icy Veins is active. But it's a passive talent flag, not the IV self-buff itself.
  - **1263263 "Hand of Frost"** at 100% med=362 — likely a Frostfire hero-talent stack proc, not Icy Veins.
  - Neither is the "press Icy Veins" aura. The actual Icy Veins aura ID in Midnight may have been renamed (the cast spell ID 12472 might still trigger but produce a differently-IDed aura). A direct query with `name LIKE '%Icy Veins%'` against a Frost log's BuffsTable would identify it. Flag for Logan.
- **Frostfire vs Spellslinger hero-tree split:** This 8-fight cohort shows Frostfire-flavored auras (Hand of Frost, Splinterstorm) at 100% — meaning every sampled top Frost Mage runs Frostfire. Spellslinger builds may not be represented here. If Spellslinger becomes meta-competitive, a re-sample is worth doing. No current major-CD aura is hero-tree-exclusive in a way that needs alt-build tracking.
- **Cold Snap (235219)** does NOT appear — confirms it's a CD-reset spell with no self-buff aura.
- **No Splinterstorm-as-CD recommendation:** despite 100% med=39, Splinterstorm reads as a rotational proc (39 uses in a M+ run is roughly every 45s on a 30-min key, which is procky). It would need separate verification before adding as a major CD.

### Interrupts

- **Spell name (id):** `Counterspell` (2139)
- **Cast type:** instant, ranged
- **Sample observed kicks per fight (median):** Not BuffsTable-visible. Same 24s CD as Arcane/Fire.
- **Recommended expected count for scoring:** 12-13 (same per-class case as Arcane/Fire).
- **No-baseline-kick callout:** N/A.

### Dispels

- **In-spec dispel ability:** `Remove Curse` (475)
- **Schools cleansable on allies:** `{Curse}` only
- **Schools the engine should credit this spec for:** `{Curse}`
- **Notes:** Same as Arcane and Fire. Class-baseline Remove Curse, no Magic/Poison/Disease/Enrage cleanse.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Polymorph | 118 | incapacitate | baseline |
| Frost Nova | 122 | root + small AoE | baseline |
| Ice Nova | 157997 | root + damage | **Frost talent (signature Frost AoE root with damage)** |
| Ring of Frost | 113724 | AoE root on cross | talent-gated |
| Mass Polymorph | 383121 | AoE incapacitate | talent-gated |
| Cone of Cold | 120 | slow | baseline |
| Freeze (Water Elemental) | 33395 | freeze (root) | talent-gated, requires Water Elemental pet variant |

(Frost's CC strength is layered roots — Frost Nova + Ice Nova + Ring of Frost can chain-control AoE pulls.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(8, "Frost")`: **keep Mirror Image.** Optionally add `(110960, "Greater Invisibility", 5, "defensive")` for parity with Arcane/Fire. **Open: re-investigate Icy Veins aura ID** — if it's recoverable, Mirror Image becomes a partial proxy and the real Icy Veins aura should be the primary tracked CD.
2. **Dispel registry** (new): `(8, "Frost") = {Curse}` — Curse-only via Remove Curse.
3. **Interrupt benchmark override:** consider `(8, "Frost") = 12` (same as Arcane/Fire).
4. Talent-gate flags: Mirror Image is universally taken in current Frost builds (100%), no flag needed. Greater Invisibility same as other specs.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
     55342      100%         6   Mirror Image  [Mirror Image]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      190446   100%        99   Brain Freeze
      444754   100%        10   Slippery Slinging
     1242775   100%        13   Farstrider's Step
      110960   100%         5   Greater Invisibility
     1247908   100%        39   Splinterstorm
     1236994   100%         6   Potion of Recklessness
     1222865   100%        62   Glacial Spike!
     1229746   100%       106   Arcanoweave Insight
       44544   100%       340   Fingers of Frost
      212653   100%        36   Shimmer
      342246   100%        10   Alter Time
      461531   100%        99   Brainstorm
       55342   100%         6   Mirror Image (tracked)
     1266687   100%       881   Alnscorned Essence
        1459   100%         4   Arcane Intellect
      455122   100%        45   Permafrost Lances
       11426   100%        53   Ice Barrier
     1266686   100%        60   Alnsight
      394195   100%       189   Overflowing Energy
     1260459   100%        17   Nullsight
      205473   100%       311   Icicles
     1263263   100%       362   Hand of Frost
      414658   100%         9   Ice Cold
     1247730   100%        96   Thermal Void
      413984    88%        58   Shifting Sands
      410089    88%        64   Prescience
      395152    88%        49   Ebon Might
      374227    88%         6   Zephyr
      381750    88%         3   Blessing of the Bronze
     1265145    88%        14   Refreshing Drink
```

---

## Open questions for review

- **Greater Invisibility as a defensive across all three Mage specs.** 100% consensus on every spec at med=3-5 uses. Same case as the Arms/Fury/Prot defensive question in the Warrior audit — Logan to decide whether 2-min-class personal defensives belong in `cooldown_usage` scoring. If yes, this is the cleanest universal Mage add. If no, all three Mage specs continue with a single tracked CD (Surge/Combustion/Mirror Image).
- **Icy Veins aura ID for Frost — second confirmation that 12472 is wrong but the actual Midnight ID is unknown.** The 2026-04-16 Pass 2 note hypothesized the ID changed; this audit confirms it but doesn't recover the new ID. Recommend a one-time targeted query: pull a known top Frost Mage's BuffsTable and grep aura names for "Icy Veins" / "Glacial Tomb" / "Frigid Empowerment" — anything matching the pattern of an 8s active-cast self-buff at the right press count (~6-8 per key). If recovered, Mirror Image stays as a secondary CD and Icy Veins becomes the primary.
- **Mirror Image asymmetry across Mage specs.** Currently tracked only on Frost (as the post-Icy-Veins fallback), but it appears at 100% on Arcane and 88% on Fire. If we adopt Mirror Image as a universal Mage CD (one slot per spec), the spec asymmetry resolves cleanly. If we keep it Frost-only, we should document why.
- **Counterspell expected-count override.** Counterspell is on a 24s CD vs the 15s melee-kick standard the DPS role default (15) is calibrated against. All three Mage specs share this. Should `_score_utility_dps_tank` be augmented with a per-spec expected-kick override path, or do we leave the 15-default and accept that Mages will register slightly lower utility scores on the kicks axis? The Warrior audit raised the same question for Pummel; this is the second class where it's relevant.
- **Touch of the Magi / Counterspell visibility:** both are debuffs/silences applied to enemies, not self-buffs. Neither surfaces in BuffsTable. A future debuff-on-target detection path would unlock Counterspell kick-counting (debuff 2139 on enemy actors) and Touch of the Magi tracking (debuff 321507 on enemy actors). Flagging for the broader audit roadmap, not this codification pass.
- **Spellsteal as offensive purge.** All three Mage specs have Spellsteal (30449), which is an offensive Magic purge from enemies. It should be tracked separately from defensive cleanses. The current dispel scoring path treats `class_has_dispel(Mage)=True` as a cleanse, which is technically correct only for Remove Curse (Curse-only). The new dispel-school registry fixes this; flag Spellsteal as offensive-only for any future "purge usage" scoring path.

## Confidence

- **Sample size:** 8 distinct top players per spec across 8 dungeons, all at +18 to +21. All three specs cleared the >=5 fights bar with no need for retries. Cohort is geographically diverse (CN, EU, NA, RU all represented across the three specs).
- **Confidence on Arcane/Fire/Frost current tracked CDs (Arcane Surge, Combustion, Mirror Image):** very high. All three at 100% consensus with realistic median use counts. No changes needed to existing tracked CDs.
- **Confidence on dispel registry empty-set-except-Curse entries:** very high. Remove Curse is class-baseline and Curse-only; this is a static class fact.
- **Confidence on Icy Veins absence:** very high (second confirmation), but **the recovery path for the correct aura ID is open.** Without it, Frost's tracked CD list stays at Mirror Image-only.
- **Confidence on Greater Invisibility add (defensive, all 3 specs):** high observation-quality (100% across 24 samples) but **medium policy confidence** — Logan's call on whether 2-min personal defensives belong in `cooldown_usage`. Same shape as the Warrior defensive question.
- **Confidence on Counterspell override (12-13 expected kicks vs 15):** medium. The 24s vs 15s CD ratio is a real mechanical difference, but the per-spec override path doesn't exist in the engine today and adding it has scope-spread risk. The existing role default is tolerable; the override is a quality-of-grading improvement, not a correctness fix.
- **Lower-confidence items:** the optional Mirror Image symmetry across all three specs, and Splinterstorm as a possible Frost CD. Both are observation-driven recommendations needing Logan's input before codification.
