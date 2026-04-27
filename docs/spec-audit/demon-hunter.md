# Demon Hunter Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 report per dungeon, top-8 per dungeon scan, 8 active-season Midnight S1 dungeons (Windrunner Spire, Maisara Caverns, Magister's Terrace, Algeth'ar Academy, Nexus-Point Xenas, Skyreach, Pit of Saron, Seat of the Triumvirate)
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Demon Hunter" --spec "{Havoc|Vengeance|Devourer}" --samples-per-dungeon 1 --top-n 8`
**Fights sampled:** Havoc 8 / Vengeance 8 / Devourer 8 (24 distinct top players in +19 to +22 range)

> Class IDs verified from `app/scoring/roles.py`: Demon Hunter is class_id `12`. Havoc and Devourer are DPS, Vengeance is tank. **Devourer** is a Midnight-added ranged DPS spec — older training data may not surface it; live WCL responses are the source of truth. Disrupt (183752) is the universal kick across all three specs. DH has **no defensive cleanse** in any spec; Consume Magic (278326) is an offensive purge (steals enemy buff), not a friendly cleanse.

---

## Spec: Havoc

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 162264  | Metamorphosis | yes            | 100%        | 66          | keep |
| 370965  | The Hunt  | yes                | 100%        | 26          | keep |
| 198013  | Eye Beam  | no                 | 100%        | 107         | hold (rotational ~30s CD AoE damage; 107 uses is the rotational cast counter, not a "major" press) |
| 188499  | Blade Dance | no               | 100%        | 59          | skip (rotational ~9s CD AoE attack) |
| 1271144 | Empowered Eye Beam | no          | 100%        | 26          | consider as alt-build major (Demon Hunter Aldrachi Reaver / Fel-Scarred buff modifying Eye Beam — cadence matches The Hunt at 26 median; verify hero-tree gating) |
| 452416  | Demonsurge | no                | 100%        | 280         | skip (Fel-Scarred hero-talent passive proc/stacker) |
| 343312  | Furious Gaze | no               | 100%        | 78          | skip (rotational haste buff post-Eye Beam, not a pressed CD) |
| 389890  | Tactical Retreat | no           | 100%        | 63          | skip (passive movement-buff after Vengeful Retreat) |
| 391215  | Initiative | no                | 100%        | 478         | skip (passive opener buff, fires every pull) |
| 212800  | Blur      | no                 | 100%        | 23          | consider add as defensive (10s 20% damage reduction, ~1min CD; signature Havoc personal defensive — 23 median uses is roughly on-CD across a 25-30min run) |
| 258920  | Immolation Aura | no            | 100%        | 74          | skip (rotational AoE pulse, ~30s CD) |
| 1271092 | Eternal Hunt | no               | 100%        | 78          | skip (Aldrachi Reaver hero-talent passive proc) |
| 1241715 | Might of the Void | no          | 100%        | 188         | skip (Midnight raidbuff/passive, not a personal CD) |
| 1266619 | First In, Last Out | no         | 100%        | 84          | skip (Midnight passive trinket/aura proc) |

**Notes on splits / alt-builds:**
- Both currently-tracked CDs (Metamorphosis 162264, The Hunt 370965) hit 100% consensus and behave like proper press-on-CD majors. **No drops needed** for Havoc.
- **No clear baseline >70%-untracked addition** beyond the tracked pair. Eye Beam (198013) is rotational (107 median uses confirms this), and Empowered Eye Beam (1271144) at 26 median matches The Hunt's cadence — likely a hero-tree-modified version. Until we can split Aldrachi Reaver vs Fel-Scarred sub-cohorts, treat Empowered Eye Beam as a candidate alt-build flag rather than a hard add.
- **Blur (212800)** is the signature Havoc personal defensive (10s 20% damage reduction, ~1min CD). 23 median uses across the cohort is roughly on-cooldown for a 25-30min M+ run. Adding it would give Havoc a `defensive` CD (currently the spec has only offensives tracked), consistent with Brewmaster/Prot's defensive-CD coverage. Open-question item — same conversation as Arms's Die by the Sword.
- **Essence Break (258860)** does NOT appear in the top 30 — confirms the 2026-04-16 Pass 2 removal. It's a target debuff, not a self-buff aura.
- **Hero-talent split:** Cohort shows both Aldrachi Reaver (Eternal Hunt 1271092 at 100%) and Fel-Scarred (Demonsurge 452416 at 100%) auras simultaneously. This is the same pattern Warrior Fury showed — both hero trees produce passive auras that surface on every player regardless of which they took, because the auras are class-wide framework signals rather than tree-exclusive abilities. None of the hero-tree-specific surfaces a new press-on-CD major beyond what's already tracked.

### Interrupts

- **Spell name (id):** `Disrupt` (183752)
- **Cast type:** instant (off-GCD melee kick, 15s CD)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable. Disrupt applies a 3s silence debuff to the target rather than producing a self-buff, so no aura appears in any sampled player's table. Needs a CastsTable spot-check to verify.
- **Recommended expected count for scoring:** 15 (DPS role default). Disrupt is a 15s CD instant — easily 12-18 kicks in a typical M+ key, so 15 is realistic.
- **No-baseline-kick callout:** N/A — Havoc has Disrupt.

### Dispels

- **In-spec dispel ability:** **none in baseline kit** (Consume Magic 278326 is an OFFENSIVE purge that steals one beneficial effect from an enemy, not a defensive cleanse on allies)
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Demon Hunter has zero defensive cleanse capability across all three specs. Consume Magic is offensive purge only — analogous to Hunter's Tranquilizing Shot or a Mage's offensive Spellsteal use. The new dispel-school registry should record `(12, "Havoc") = set()` so utility scoring doesn't penalize the spec for not cleansing things it cannot cleanse, and offensive purges should be credited (if at all) via a separate purge-tracking lane rather than via the cleanse registry.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Imprison  | 217832 | incapacitate | baseline single-target incap (60s, breaks on damage) |
| Chaos Nova | 179057 | stun         | baseline AoE stun (5s, ~1min CD) |
| Sigil of Misery | 207684 | disorient | talent-gated AoE disorient (~1min CD) |
| Fel Eruption | 211881 | stun       | talent-gated single-target stun (Havoc-only) |

(Havoc has the richest CC kit of the three DH specs — Imprison + Chaos Nova baseline plus two talent stun/disorient options. Storm-bolt-tier stun on Fel Eruption is a Havoc-exclusive talent.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(12, "Havoc")`: **no edits required** — Metamorphosis (162264) and The Hunt (370965) both at 100% consensus with realistic median use counts. Optional: add `(212800, "Blur", 23, "defensive")` if we want Havoc to have a defensive in its tracked list (currently zero). Pending Open-question item.
2. **Dispel registry** (new): `(12, "Havoc") = set()` — no defensive cleanses. Note Consume Magic separately as offensive purge if/when we add a purge-tracking lane.
3. **Interrupt benchmark override:** none. Disrupt + 15s CD + 15 expected kicks default is fine.
4. Talent-gate flags: no current additions. If Empowered Eye Beam (1271144) gets added in a future pass as a hero-tree-specific major, it should be flagged for talent-aware skip on Fel-Scarred builds.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    162264      100%        66   Metamorphosis  [Metamorphosis]
    370965      100%        26   The Hunt  [The Hunt]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1214887   100%         4   Cycle of Hatred
     1266619   100%        84   First In, Last Out
      258920   100%        74   Immolation Aura
      370965   100%        26   The Hunt (tracked)
     1241715   100%       188   Might of the Void
      427914   100%         5   Immolation Aura
     1271092   100%        78   Eternal Hunt
      427913   100%        22   Immolation Aura
      343312   100%        78   Furious Gaze
      428361   100%        52   Ragefire
     1229746   100%        90   Arcanoweave Insight
      428362   100%        22   Ragefire
      390192   100%        72   Ragefire
      452497   100%        21   Abyssal Gaze
      453314   100%        56   Enduring Torment
      452416   100%       280   Demonsurge
      391215   100%       478   Initiative
      188499   100%        59   Blade Dance
     1235111   100%         1   Flask of the Shattered Sun
     1271144   100%        26   Empowered Eye Beam
      428363   100%         5   Ragefire
      427912   100%        52   Immolation Aura
      162264   100%        66   Metamorphosis (tracked)
      427901   100%       249   Deflecting Dance
      383781   100%        13   Algeth'ar Puzzle
      212800   100%        23   Blur
      198013   100%       107   Eye Beam
      389890   100%        63   Tactical Retreat
     1265145    88%        44   Refreshing Drink
     1266616    88%        21   Demon Muzzle
```

---

## Spec: Vengeance

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 187827  | Metamorphosis | yes            | 100%        | 63          | keep |
| 207771  | Fiery Brand | no               | 100%        | 193         | **add (defensive) — see notes; 2026-04-15 removal needs revisiting** |
| 203819  | Demon Spikes | no              | 100%        | 30          | hold (rotational ~6s recharge active mitigation; 30 median is on-CD but it's the same saturation hazard as Brewmaster's Ironfur — see notes) |
| 263648  | Soul Barrier | no              | 100%        | 109         | skip (rotational soul-fragment-consumer absorb shield, not a "major" CD) |
| 212084  | Fel Devastation | no            | 100%        | 31          | consider add as defensive (heal/damage AoE, ~40s CD, 31 median is on-CD for a 25min run) |
| 203981  | Soul Fragments | no            | 100%        | 1744        | skip (passive resource counter, not a CD) |
| 1256322 | Voidfall  | no                 | 100%        | 381         | skip (Midnight passive/proc) |
| 1256308 | Dark Matter | no               | 100%        | 63          | skip (Midnight raid-buff or hero-talent passive) |
| 258920  | Immolation Aura | no            | 100%        | 137         | skip (rotational AoE pulse) |
| 393009  | Fel Flame Fortification | no    | 100%        | 137         | skip (passive scaling buff) |
| 1270476 | Untethered Rage | no            | 100%        | 42          | skip (passive proc/buff) |
| 1270547 | Seething Anger | no             | 100%        | 382         | skip (passive stacker) |

**Notes on splits / alt-builds:**
- **Fiery Brand (207771) showing at 100% with 193 median uses is the headline finding for Vengeance.** This contradicts the 2026-04-15 removal note in `cooldowns.py` ("applies a debuff to the target (207771), not a self-buff"). The current sampler shows Fiery Brand IS surfacing in BuffsTable across all 8 top Vengeance players, with extremely high use counts (193 median). The 193 count is suspicious for a ~1min CD — it suggests this is either (a) the debuff-on-target applied to multiple targets being recorded under the player's source ID, or (b) a hero-tree variant that pulses repeatedly. **Recommend adding back as `(207771, "Fiery Brand", 8, "defensive")` with the expected uptime tuned conservatively, OR investigating whether 193 median is multi-target debuff-spam rather than self-buff presses before codifying.** This is an Open-question item.
- **Metamorphosis (187827) at 100% with 63 median uses** is healthy — confirms the existing tracker. 63 median is unusually high for a ~3min CD; likely the buff procs/refreshes mid-fight or the count includes Demonic-talent extensions per Soul Fragment consumption. Not a concern for tracking, just noteworthy.
- **Demon Spikes (203819)** is the rotational active mitigation (Brewmaster Ironfur analog). 30 median uses across the cohort is on-CD and would saturate cooldown_usage scoring at flat 100% if added — same saturation hazard the Pass 3 Resto Druid Barkskin removal flagged. **Skip, do not add.**
- **Fel Devastation (212084)** at 100%, 31 median uses, ~40s CD damage-and-self-heal channel. This is a more legitimate "press-on-cooldown major" for Vengeance than Demon Spikes. Worth considering as a defensive add alongside Metamorphosis if we want Vengeance to have multiple tracked CDs (it currently has only one, fewer than other tanks: Prot Warrior has 3, Brewmaster has 4, Guardian has 3, Blood DK has 2).
- **Sigil of Flame / Sigil of Chains** absent from top 30 — those are placed-ground sigils, not self-auras.
- No clear hero-tree alt-build split surfaced — both Aldrachi Reaver and Fel-Scarred Vengeance builds appear in the cohort with overlapping passive auras, but no major-CD aura is hero-tree-exclusive in a way that requires alt-build branching.

### Interrupts

- **Spell name (id):** `Disrupt` (183752)
- **Cast type:** instant (off-GCD, 15s CD)
- **Sample observed kicks per fight (median):** Not visible in BuffsTable. Same caveat as Havoc.
- **Recommended expected count for scoring:** 12 (tank role default). DH tanks have fewer kick opportunities per pull because of their weave/dodge-based active mitigation pattern, but 12 is realistic.
- **No-baseline-kick callout:** N/A.

### Dispels

- **In-spec dispel ability:** **none in baseline kit**
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Vengeance has Consume Magic (278326) like the other DH specs, but it's offensive purge (enemy-only), not a friendly cleanse. The new dispel-school registry should record `(12, "Vengeance") = set()`.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Imprison  | 217832 | incapacitate | baseline single-target incap |
| Chaos Nova | 179057 | stun         | baseline AoE stun (~1min CD) |
| Sigil of Misery | 207684 | disorient | talent-gated AoE disorient (Vengeance frequently picks this for trash CC) |
| Sigil of Silence | 202137 | silence  | talent-gated AoE silence — Vengeance-favored M+ pick |

(Vengeance trades Havoc's Fel Eruption stun for Sigil of Silence, which is the canonical Vengeance M+ talented CC for caster-heavy pulls.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(12, "Vengeance")`: **investigate Fiery Brand (207771) re-add** (see Open-questions). If we keep the 2026-04-15 removal, Vengeance retains only Metamorphosis — undertracked relative to other tank specs. Optionally add `(212084, "Fel Devastation", 8, "defensive")` to give Vengeance a second tracked CD; 31 median uses is on-CD for the ~40s recharge.
2. **Dispel registry** (new): `(12, "Vengeance") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** none. Tank default of 12 expected kicks is fine.
4. Talent-gate flags: none required at current data — both surfaces are universal.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    187827      100%        63   Metamorphosis  [Metamorphosis]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1229746   100%       112   Arcanoweave Insight
     1266619   100%       239   First In, Last Out
      207771   100%       193   Fiery Brand
      203981   100%      1744   Soul Fragments
      187827   100%        63   Metamorphosis (tracked)
     1256322   100%       381   Voidfall
      263648   100%       109   Soul Barrier
     1256308   100%        63   Dark Matter
     1270476   100%        42   Untethered Rage
      258920   100%       137   Immolation Aura
      393009   100%       137   Fel Flame Fortification
      203819   100%        30   Demon Spikes
      212084   100%        31   Fel Devastation
     1256302   100%        89   Voidfall
     1256301   100%       110   Voidfall
     1270547   100%       382   Seething Anger
     1236616   100%         5   Light's Potential
     1266616   100%        26   Demon Muzzle
     1241715    88%       174   Might of the Void
      404381    75%         2   Defy Fate
     1263318    75%        88   The Wind Awoken
     1235110    75%         1   Flask of the Blood Knights
      374227    75%         5   Zephyr
      381741    75%         3   Blessing of the Bronze
     1252488    75%        28   Masterful Hunt
     1252486    75%        24   Hasty Hunt
      212988    75%      1766   Painbringer
     1252487    62%        35   Focused Hunt
      410089    62%         5   Prescience
     1252489    62%        31   Versatile Hunt
```

---

## Spec: Devourer

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 1225789 | Void Metamorphosis | yes           | 100%        | 1077        | **revisit** — 1077 median uses suggests this is a stack/proc aura, not a press-on-CD major (see notes) |
| 473728  | Void Ray  | no                 | 100%        | 189         | skip (rotational ranged spender; the Devourer "Aimed Shot" analog) |
| 1256301 | Voidfall  | no                 | 100%        | 250         | skip (Midnight passive/proc) |
| 1242504 | Emptiness | no                 | 100%        | 2130        | skip (passive resource counter) |
| 1245577 | Soul Fragments | no            | 100%        | 2935        | skip (passive resource counter; Devourer-flavor of Vengeance's Soul Fragments) |
| 212800  | Blur      | no                 | 100%        | 23          | consider add as defensive (same Havoc Blur aura — ~1min CD personal damage reduction) |
| 1244235 | Rolling Torment | no            | 100%        | 21          | candidate add (21 median uses is press-on-CD cadence for a ~1.5-2min major; could be Devourer's signature offensive press) |
| 1266686 | Alnsight  | no                 | 100%        | 63          | skip (Midnight passive raid-wide proc, also seen on non-DH specs) |
| 1266687 | Alnscorned Essence | no         | 100%        | 981         | skip (passive Midnight stacker) |
| 1260459 | Nullsight | no                 | 100%        | 18          | candidate add (18 median uses is press-on-CD cadence for a ~2min major; possible signature Devourer offensive) |
| 1260013 | Grim Focus | no                | 100%        | 3           | skip (3 median is too few to be a primary major; could be a 3-charge talent or end-of-run-only) |
| 1265145 | Refreshing Drink | no           | 100%        | 21          | skip (consumable food buff, not a class CD) |

**Notes on splits / alt-builds:**
- **Void Metamorphosis (1225789) at 1077 median uses is the audit's most important finding for Devourer.** That use count is wildly inconsistent with a press-on-CD major. The Vengeance/Havoc Metamorphosis variants (187827, 162264) sit at 63 and 66 median uses respectively — that's the "real" press-on-CD cadence. 1077 strongly suggests **Void Metamorphosis is a stacking/refreshing proc aura rather than a single-press major CD**. The earlier comment in `cooldowns.py` (line 197) noted "Void Metamorphosis is the high-confidence major CD identified from Mvpewe's audit (659 buff uses)" — at the time 659 was unusual; now we're seeing 1077, reinforcing that this is NOT behaving like Havoc/Vengeance Meta. **Recommend investigating** whether 1225789 is the press-aura for Devourer's "go-into-form" CD or a passive resource/stack signal. If it's the latter, drop it and search for a different aura.
- **Rolling Torment (1244235) at 21 median uses** and **Nullsight (1260459) at 18 median uses** both look like genuine press-on-CD majors — their cadence is similar to Havoc's The Hunt (26 median). One of these is likely the "true" Devourer signature CD that the original Mvpewe audit may have missed. Without per-talent build data we can't yet say which is universal vs talent-gated.
- **Devourer is a NEW spec in Midnight S1.** This audit is essentially a first-pass identification. Several ID candidates above need a follow-up sampler run with cast-event tracking (not just BuffsTable) to confirm the actual press-on-CD majors. The current `(12, "Devourer") = [(1225789, "Void Metamorphosis", ...)]` entry should be considered tentative until a second pass investigates the 1077-median anomaly.
- **Hero-tree split:** Same Aldrachi vs Fel-Scarred fork as Havoc — passive auras from both surface in the cohort but no hero-tree-exclusive press-on-CD major was identified.

### Interrupts

- **Spell name (id):** `Disrupt` (183752)
- **Cast type:** instant (off-GCD, 15s CD)
- **Sample observed kicks per fight (median):** Not visible in BuffsTable; needs CastsTable verification. **Special verification recommended for Devourer specifically** — as a ranged DPS, Disrupt's melee range may make it less practical to land than it is for Havoc/Vengeance, and Devourer may rely more on Sigil-based CC. If verified that Devourer kicks less often than melee DPS, the expected-kick count may need a downward override (e.g. 10 instead of 15).
- **Recommended expected count for scoring:** 15 (DPS role default) — provisional. Pending the ranged-vs-melee verification noted above.
- **No-baseline-kick callout:** N/A — Devourer has Disrupt baseline (DH class kick, not spec-gated).

### Dispels

- **In-spec dispel ability:** **none in baseline kit**
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Same as Havoc/Vengeance — Consume Magic is offensive purge only. The dispel registry should record `(12, "Devourer") = set()`.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Imprison  | 217832 | incapacitate | baseline DH incap |
| Chaos Nova | 179057 | stun         | baseline AoE stun |
| Sigil of Misery | 207684 | disorient | talent-gated AoE disorient |

(Devourer is ranged but shares the DH baseline CC kit. Lacks Havoc's Fel Eruption talent and likely lacks Vengeance's Sigil of Silence — exact ranged-DPS CC tree should be verified against in-game talent data, but the baseline kit above is the universal subset.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(12, "Devourer")`: **investigate Void Metamorphosis (1225789) — 1077 median uses is anomalous for a press-on-CD major.** Possible actions: (a) drop and replace with Rolling Torment (1244235) or Nullsight (1260459); (b) verify via cast-event sampler whether 1225789 is a stacking proc; (c) keep tentatively but flag for re-sample next tuning pass. **Open-question item.**
2. **Dispel registry** (new): `(12, "Devourer") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** verify ranged-spec kick cadence; provisional default 15. May need downward override to ~10 if Devourer plays at range and uses Disrupt sparingly.
4. Talent-gate flags: defer until cast-event-based sampler clarifies which of {Void Metamorphosis, Rolling Torment, Nullsight} is the universal vs alt-build major.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
   1225789      100%      1077   Void Metamorphosis  [Void Metamorphosis]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1256308   100%        22   Dark Matter
     1244235   100%        21   Rolling Torment
     1266686   100%        63   Alnsight
      155777   100%        38   Rejuvenation (Germination)
     1225789   100%      1077   Void Metamorphosis (tracked)
     1256301   100%       250   Voidfall
      413984   100%        61   Shifting Sands
     1265145   100%        21   Refreshing Drink
      410089   100%        63   Prescience
     1266687   100%       981   Alnscorned Essence
      381741   100%         4   Blessing of the Bronze
      390386   100%         3   Fury of the Aspects
       58984   100%         3   Shadowmeld
         774   100%        51   Rejuvenation
        8936   100%       100   Regrowth
      374227   100%         5   Zephyr
     1265140   100%        30   Refreshing Drink
      395152   100%        53   Ebon Might
      403295   100%        11   Black Attunement
     1266619   100%        40   First In, Last Out
     1266616   100%        24   Demon Muzzle
     1260459   100%        18   Nullsight
     1242504   100%      2130   Emptiness
      410263   100%        25   Inferno's Blessing
      404381   100%         2   Defy Fate
      473728   100%       189   Void Ray
       33763   100%        24   Lifebloom
      212800   100%        23   Blur
     1260013   100%         3   Grim Focus
     1245577   100%      2935   Soul Fragments
```

> Note on Devourer's top-30 composition: many of the highest-consensus auras (Rejuvenation, Lifebloom, Regrowth, Prescience, Shifting Sands, Ebon Might, Inferno's Blessing) are external buffs from group members (Resto Druid HoTs, Augvoker buffs, Aug raid-buff procs) rather than self-cast auras. This is expected behavior because the BuffsTable reports any buff present on the player, not just self-cast ones. The top-cohort cohort skewed toward groups running Aug-stacked compositions, which is normal for +21/+22 keys.

---

## Open questions for review

- **Vengeance Fiery Brand (207771) — RE-ADD or keep out?** Sampler shows 100% consensus, 193 median uses. The 2026-04-15 removal note said it was a target debuff invisible to BuffsTable. The current sampler clearly surfaces it. Is the 193 count (a) the player's buff-count of the debuff applied to the targets they hit (so it scales with mob count), or (b) a hero-talent-modified self-buff variant added in Midnight? **Without resolving this, the codification step should not blindly re-add Fiery Brand.** Suggest a CastsTable cross-check for Vengeance's actual Fiery Brand cast count (~2-4 per minute is the design intent).
- **Devourer Void Metamorphosis (1225789) — what is the actual press-on-CD aura?** 1077 median uses doesn't match any known major-CD cadence pattern. Either (a) the aura is a passive proc that surfaces in BuffsTable but isn't really pressed, (b) it's a refreshing buff that re-applies on every Void Ray cast, or (c) the Void Devourer kit doesn't have a single-press major CD and the engine should consider Rolling Torment (1244235, 21 median) or Nullsight (1260459, 18 median) instead. Logan: do we want a follow-up cast-event sampler pass for Devourer specifically before codifying?
- **Defensive-CD slot for Havoc?** Same question as Warrior Arms/Fury. Blur (212800) is a 23-median-uses-on-CD personal defensive that would give Havoc its first tracked defensive. Worth adding for cooldown_usage scoring fairness if we widen the "major CD" definition for melee DPS to include 1-min personal defensives. Pending Logan's call.
- **Devourer interrupt expected count:** As a ranged DPS, Devourer may use Disrupt less often than Havoc due to range positioning. Need cast-event verification before deciding whether to override the DPS-default of 15 expected kicks.
- **Hero-tree split tracking:** Aldrachi Reaver vs Fel-Scarred — every spec shows passive auras from both trees. The "Empowered Eye Beam" (1271144) on Havoc is a candidate hero-tree-modified press but couldn't be sub-cohorted with this 8-fight sample. Future audits with larger cohorts (16+ fights) could split players by talent build and identify hero-tree-exclusive majors.

## Confidence

- **Sample size:** 8 distinct top players per spec across 8 dungeons. Havoc and Vengeance both at +19 to +20 (standard sample depth), Devourer at +21 to +22 (Devourer's top cohort actually keys higher than the other DH specs in this snapshot, possibly because the spec is currently strong / pushed by minmaxing players). **All three specs cleared the >=5 fights bar; no retries needed.**
- **Confidence on Havoc keep-as-is:** very high. Both tracked CDs at 100% with realistic median use counts. The optional Blur defensive add is observation-driven, not a high-consensus must-add.
- **Confidence on Vengeance Fiery Brand finding:** medium. 100% consensus is unambiguous; 193-median-uses interpretation is not. Needs CastsTable follow-up before codification.
- **Confidence on Devourer audit:** **low**. Void Metamorphosis is currently the only tracked CD and its 1077-median-uses signal is anomalous. Devourer is a new Midnight-added spec with limited prior audit history (only Mvpewe's earlier 659-uses entry to compare against). Strongly recommend a follow-up cast-event sampler run before the codification PR lands. The dispel-registry entry, interrupt baseline (Disrupt), and CC catalog are high-confidence regardless of which press-on-CD aura ends up being the "real" one.
- **Confidence on dispel registry empty-set entries:** very high. Demon Hunter has no defensive cleanse in any spec; this is a static class fact. Consume Magic 278326 is offensive purge.
- **Confidence on interrupt expected count:** medium for Havoc/Vengeance (Disrupt ID 183752 is well-known, but kick counts couldn't be validated from BuffsTable in this audit), low for Devourer (ranged-spec usage pattern unknown).
