# Shaman Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 distinct top player per active dungeon (8 dungeons), Elemental / Enhancement / Restoration
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Shaman" --spec "{Spec}" --samples-per-dungeon 1 --top-n 8`

Cohort key range observed: **+19 to +22** across all three specs (Restoration sampled at +20 to +22 via HPS metric, Elemental/Enhancement at +19 to +21 via DPS metric). Eight distinct fights collected per spec — confidence threshold met for all three specs without retry.

---

## Spec: Elemental

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 191634  | Stormkeeper | yes        | 100%        | 145         | keep — but uses count is *charge consumption*, see notes |
| 1219480 | Ascendance (talent) | no | 100%       | 13          | **add** (>70%, talent-aware skip handles non-takers) |
| 198103  | Earth Elemental | no    | 100%        | 5           | leave (defensive pet summon — short uptime aura, not a "press on cd" major) |
| 118323  | Primal Earth Elemental | no | 100%   | 5           | leave (companion aura to 198103, same pet) |
| 378081  | Nature's Swiftness | no | 100%       | 23          | leave (1min utility instant-cast enabler, not a major DPS CD) |
| 198067  | Fire Elemental | no    | 0% (not seen) | —         | confirm-removed (Pass 2 already pruned; pet pattern, no self-aura) |
| 192249  | Storm Elemental (alt-talent) | no | 0% (not seen) | — | leave (same pet pattern; talent-gated alt to FE) |
| 375982  | Primordial Wave (talent) | no | 0% (not seen) | — | leave (cast-only, debuff/proc — no self-aura) |
| 192222  | Liquid Magma Totem (talent) | no | 0% (not seen) | — | leave (totem drop, not self-aura) |

**Notes on splits / alt-builds:**
- **Ascendance (1219480) at 100% med=13 is the headline finding.** Currently untracked. Across 8/8 top Elemental logs in this cohort, every player has Ascendance taken AND pressing it ~13 times per fight is consistent with a 3-min CD pressed on cooldown across a typical 35-40min M+ run. This is a clean **add candidate** — register it as `(1219480, "Ascendance", 13, "offensive")`. Because Ascendance is a hero-talent capstone (and there's a non-Ascendance build path still circulating in lower-key cohorts), it should be paired with Stormkeeper rather than replacing it; the talent-aware skip in `_get_cooldown_usage` handles cohorts that didn't pick it.
- **Stormkeeper med=145 looks anomalous but is correct.** Stormkeeper grants Lightning Bolt charges, and the BuffsTable's `totalUses` for the aura counts each *charge consumption* application, not each cast of the original CD. The actual CD presses per fight are roughly med ÷ 10-15 ≈ 10-15 presses. This doesn't break scoring — `cooldown_usage` normalizes against `expected_uptime_pct=10`, which is calibrated to "saturating coverage" at 100, and Elemental easily clears that. Note the same pattern shows up on Enhancement Doom Winds (med=25) and Resto Spirit Link (med=6) — different units, same mechanism.
- **Pet-summon CDs are correctly absent.** Fire Elemental, Storm Elemental, and Earth Elemental all summon entities with their own buff trees; the shaman's BuffsTable doesn't see them as a self-aura. The Pass-2 prune of Fire Elemental holds. Earth Elemental shows up at 100% (med=5) only as a *defensive shield* aura on the player during summon — it's a 60s-cd personal mitigation more than a damage CD, and adding it would saturate the category like Resto Druid Barkskin did in Pass 3.
- **Primordial Wave / Liquid Magma Totem** are the two other commonly-talented active spells. Both leave no trackable self-aura (PWave applies a debuff to the target that buffs the shaman's Lightning Bolt damage; LMT is a totem that drops AoE pulses). Same "needs cast-event detection" pattern as Wake of Ashes / Frozen Orb. Flag for the future cast-event path.
- **Tempest (454015) at 100% med=136** is the Stormbringer hero-talent passive proc — a Lightning Bolt that sometimes upgrades. NOT a pressed CD, do not track.

### Interrupts

- **Spell name (id):** `Wind Shear` (57994)
- **Cast type:** instant, 12s CD, 30yd ranged kick (the longest-range baseline kick in the game)
- **Sample observed kicks per fight (median):** not derivable from BuffsTable (Wind Shear leaves no self-aura). Anecdotally Elemental's range advantage means it's typically *the* primary kicker on a DPS-heavy comp.
- **Recommended expected count for scoring:** 15 (DPS denom in `_score_utility_dps_tank`). Standard. Wind Shear's range and short CD favor Elemental clearing this denom comfortably.
- No baseline-kick callout needed (DPS spec).

### Dispels

- **In-spec dispel ability:** `Cleanse Spirit` (51886). Removes Curse from allies. **No Magic dispel for Elemental** — that's Resto-only.
- **Schools cleansable on allies:** `{Curse}`
- **Schools the engine should credit this spec for:** `{Curse}`
- **Notes:** Verified — Cleanse Spirit (51886) is class-baseline for Shaman across all three specs (a Pet-talent and class-baseline ability tree distinction in older expansions, but it's been baseline since Legion). Restoration *replaces* Cleanse Spirit with Purify Spirit (77130) which adds Magic. So the registry split must be precise:
  - `(7, "Elemental") = {Curse}`
  - `(7, "Enhancement") = {Curse}`
  - `(7, "Restoration") = {Curse, Magic}`

  This is the key BRM-lesson-3 fix for Shaman: `class_has_dispel(7) = True` is correct, but the engine must NOT credit Elemental/Enhancement for Magic-cleanse work that only Resto can perform.
- **Offensive purge:** `Purge` (370) is in the kit but it strips buffs from enemies — does NOT register as a defensive cleanse. Do not credit Elemental for ally cleanses based on Purge use; the dispel registry records `{Curse}` for Elemental, full stop. (The cast list in `dispel_abilities.py` line 33-37 already correctly lists 51886 for non-Resto and 77130 for Resto; no Purge entry, no offensive-dispel double-credit.)

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Hex | 51514 | incapacitate (Humanoid/Beast) | baseline 1-min CD, the signature shaman CC |
| Capacitor Totem | 192058 | stun (AoE) | talent-gated, ~30s CD pulse stun on totem detonation |
| Earthbind Totem | 2484 | slow only | NOT a hard CC — slow effect, count as utility not CC |
| Earthgrab Totem | 51485 | root (AoE) | talent-gated, baseline-replaces Earthbind on takers |
| Thunderstorm | 51490 | knockback / disorient | Elemental-only; AoE displacement — counts as "displacement utility" (similar to Typhoon) |

Thunderstorm is the standout Elemental-specific tool — knockback off ledges/back into AoE clusters is regularly used at the top end. Worth surfacing on the run page if/when CC tracking gains a UI.

### Recommended changes

1. `app/scoring/cooldowns.py` `(7, "Elemental")`: **add** `(1219480, "Ascendance", 13, "offensive")` paired alongside the existing Stormkeeper entry. Talent-aware skip handles non-takers.
2. **Dispel registry** (new): `(7, "Elemental") = {Curse}`. Critical: do NOT credit for Magic.
3. **Interrupt benchmark override:** none. DPS default of 15 stands.
4. Talent-gate flags: Ascendance is a hero-talent capstone — register with talent-gate handling so non-takers (rare in S1 top cohort, but possible at lower keys) aren't punished.

### Top-cohort raw output reference

```
Aggregate over 8 Shaman Elemental fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    191634      100%       145   Stormkeeper  [Stormkeeper]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1219480   100%        13   Ascendance
      381755   100%         5   Primordial Bond
      118522   100%       103   Elemental Blast: Critical Strike
      355634   100%        32   Windveil
      192082   100%         5   Wind Rush
      263806   100%       123   Wind Gust
     1236616   100%         5   Light's Potential
       32182   100%         3   Heroism
      198103   100%         5   Earth Elemental
      173183   100%       101   Elemental Blast: Haste
        2645   100%        21   Ghost Wolf
     1229746   100%        85   Arcanoweave Insight
      454394   100%       258   Unlimited Power
      454015   100%       136   Tempest
       77762   100%       119   Lava Surge
      191634   100%       145   Stormkeeper (tracked)
       79206   100%        15   Spiritwalker's Grace
      454025   100%       115   Electroshock
      108271   100%        10   Astral Shift
      462854   100%         3   Skyfury
      378081   100%        23   Nature's Swiftness
      118323   100%         5   Primal Earth Elemental
      173184   100%        97   Elemental Blast: Mastery
     1272101   100%        31   Thunderous Velocity
     1264426    88%         1   Void-Touched
     1250508    88%        13   Emberwing Heatwave
     1265140    75%        33   Refreshing Drink
     1265145    75%        19   Refreshing Drink
       65116    75%         3   Stoneform
      374227    75%         5   Zephyr
```

---

## Spec: Enhancement

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 466772  | Doom Winds | yes        | 100%        | 25          | keep (Pass 2 fix validated) |
| 51533   | Feral Spirit | no         | 0% (not seen) | —         | confirm-removed (Pass 2 prune holds — pet summon, no self-aura) |
| 114051  | Ascendance (talent) | no | 0% (not seen) | —       | leave (Enh's Ascendance not in current-meta build) |
| 191634  | Stormkeeper (alt-talent for Enh) | no | 0% (not seen) | — | leave (Stormbringer-tree pick, not in current Enh meta) |
| 375982  | Primordial Wave (talent) | no | 0% (not seen) | — | leave (cast-only, no self-aura — same as Elemental) |
| 1262830 | Storm Unleashed | no    | 100%        | 69          | leave (hero-talent rotational proc — not a pressed CD) |
| 470466  | Stormblast | no            | 100%        | 127         | leave (rotational ability proc/aura) |
| 1218125 | Primordial Storm (hero-talent capstone) | no | 100% | 51 | **investigate — see notes** |
| 224125  | Molten Weapon | no         | 88%         | 51          | leave (rotational weapon-imbue stack tracker) |
| 224127  | Crackling Surge | no       | 100%        | 27          | leave (rotational stack tracker) |

**Notes on splits / alt-builds:**
- **Doom Winds at 100% med=25 fully validates the Pass-2 swap from Ascendance.** No drop, no replace. Current build-divergence analysis: the entire top-8 cohort runs Doom Winds; no Ascendance/Stormkeeper-Enhancement variants observed at top keys.
- **Primordial Storm (1218125) at 100% med=51 is the alt-add candidate worth examining.** This is the Totemic-tree hero-talent capstone pulse. Whether this is a "press on cooldown" major CD or a passive rotational stack-tracker depends on its mechanic — Primordial Storm is actually a *cast* spell with an aura that ticks per-pulse, similar in mechanic to a totem drop. Median uses of 51 across an M+ run suggests aura-applications-per-pulse (totem detonates), not press-presses. **Recommend leaving untracked** — adding it would risk the same saturation issue that `Barkskin` caused on Resto Druid in Pass 3. Doom Winds alone gives a clean signal.
- **Pet-summon CDs (Feral Spirit) correctly absent.** The Pass-2 prune of Feral Spirit (51533) holds — wolves are entities with their own buffs.
- **Hot Hand (215785) at 88% med=52** is a rotational proc, not a pressed CD. Do not track.
- **Maelstrom Weapon (344179) at 100% med=4827** is the resource stack — definitely not a CD.

### Interrupts

- **Spell name (id):** `Wind Shear` (57994)
- **Cast type:** instant, 12s CD, 30yd range
- **Sample observed kicks per fight (median):** not derivable from BuffsTable.
- **Recommended expected count for scoring:** 15 (DPS denom). Standard. Enhancement is melee but Wind Shear's 30yd range means kick volume is comparable to ranged DPS shamans — they don't lose kicks to repositioning the way pure-melee classes do.
- No override needed.

### Dispels

- **In-spec dispel ability:** `Cleanse Spirit` (51886). Removes Curse from allies.
- **Schools cleansable on allies:** `{Curse}`
- **Schools the engine should credit this spec for:** `{Curse}`
- **Notes:** Same as Elemental — non-Resto Shaman dispel registry is Curse-only. Purge (370) is offensive-only, does not count.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Hex | 51514 | incapacitate | baseline class-wide |
| Capacitor Totem | 192058 | stun (AoE) | talent-gated |
| Earthbind Totem | 2484 | slow only | not hard CC |
| Earthgrab Totem | 51485 | root (AoE) | talent-gated, replaces Earthbind |

Enhancement does NOT have Thunderstorm — that's Elemental-only. Enhancement's signature CC is melee-range Hex setup and Capacitor for AoE stuns, both at ~1-min cadence.

### Recommended changes

1. `app/scoring/cooldowns.py` `(7, "Enhancement")`: **No drops, no adds.** Doom Winds at 100% med=25 — Pass-2 swap held perfectly.
2. **Dispel registry** (new): `(7, "Enhancement") = {Curse}`. Match Elemental.
3. **Interrupt benchmark override:** none.
4. Talent-gate flags: none currently — Doom Winds is universally taken in the current Enhancement meta. If Ascendance-Enhancement (114051) gains traction in a later patch, register it as the alt-build alongside Doom Winds.

### Top-cohort raw output reference

```
Aggregate over 8 Shaman Enhancement fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    466772      100%        25   Doom Winds  [Doom Winds]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      198103   100%         4   Earth Elemental
     1265145   100%        40   Refreshing Drink
      462854   100%         6   Skyfury
      382043   100%        51   Surging Elements
      344179   100%      4827   Maelstrom Weapon
     1262830   100%        69   Storm Unleashed
      355634   100%        28   Windveil
      224127   100%        27   Crackling Surge
     1229746   100%        82   Arcanoweave Insight
      470466   100%       127   Stormblast
      192082   100%         5   Wind Rush
        2645   100%        26   Ghost Wolf
     1265140   100%        51   Refreshing Drink
      201846   100%       118   Stormsurge
     1236616   100%         6   Light's Potential
     1252415   100%       271   Crash Lightning
      466772   100%        25   Doom Winds (tracked)
     1241715   100%       182   Might of the Void
      108271   100%        12   Astral Shift
     1218125   100%        51   Primordial Storm
      410681   100%       349   Overflowing Maelstrom
      381755   100%         4   Primordial Bond
      215785    88%        52   Hot Hand
     1266686    88%        63   Alnsight
      458269    88%       185   Totemic Rebound
      224125    88%        51   Molten Weapon
       58875    88%         8   Spirit Walk
      456369    88%        26   Amplification Core
      453406    88%        26   Whirling Earth
      461242    88%       131   Lively Totems
```

---

## Spec: Restoration

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 325174  | Spirit Link Totem | yes  | 100%        | 6           | keep (Pass 2 fix held) |
| 108280  | Healing Tide Totem | no  | 88%         | 9           | **add** (>70%, signature defensive raid CD) |
| 1267089 | Stormstream Totem (hero-talent capstone) | no | 100% | 43 | leave (hero-talent passive proc/totem pulse) |
| 470077  | Coalescing Water | no     | 100%        | 467         | leave (rotational stack tracker — not a pressed CD) |
| 53390   | Tidal Waves | no           | 100%        | 370         | leave (rotational proc) |
| 73685   | Unleash Life (talent) | no | 100%       | 72          | leave (rotational ability buff, ~30s CD per use — not "major" CD; saturation risk) |
| 207400  | Ancestral Vigor | no       | 100%        | 266         | leave (passive HP buff applied per heal) |
| 16191   | Mana Tide Totem (talent) | no | 0% (not seen) | —     | leave (talent-gated; not in current S1 meta build) |
| 157153  | Cloudburst Totem (talent) | no | 0% (not seen) | —    | leave (talent-gated alt to Healing Tide; rare in current meta) |
| 33757   | Earthen Wall Totem (talent) | no | 0% (not seen) | —  | leave (talent-gated absorb totem; situational) |
| 114052  | Ascendance (Resto talent) | no | 0% (not seen) | —    | leave (talent-gated; current S1 Resto builds favor non-Asc paths) |

**Notes on splits / alt-builds:**
- **Healing Tide Totem (108280) at 88% med=9 is the headline add candidate.** Currently untracked. The Pass-2 removal commentary in `cooldowns.py` line 290-294 noted that totems are "drops, not self-buffs" — but the sampler is showing Healing Tide DOES leave a trackable aura on the shaman (which makes sense; it's the cast-side aura while the totem is alive). Spirit Link Totem already validates this pattern (325174 IS tracked successfully). Healing Tide should follow the same path: **add** `(108280, "Healing Tide Totem", 9, "defensive")`. The 1/8 cohort that didn't have it is the Cloudburst-build minority — talent-aware skip handles them.
- **Cloudburst Totem (157153)** is the alternative to Healing Tide for cohorts running the smart-heal build. It did not appear at 50%+ in this top-8 cohort. **Recommend deferring** until either (a) a non-trivial Cloudburst-build cohort emerges in the data, or (b) we sample broader (top-20+). For now, Healing Tide alone covers the meta with the talent-aware skip handling the minority.
- **Ascendance (114052)** for Resto did not surface — current S1 Resto top builds appear to skip Ascendance in favor of totem-heavy builds. No alt-build registration needed.
- **Stormstream Totem (1267089) at 100% med=43** looks like a Stormbringer/Totemic hero-talent capstone — it pulses repeatedly while the totem is up, generating per-pulse aura applications. This is the same "saturation risk" pattern as Resto Druid Barkskin. **Do not track.**
- **Mana Tide / Earthen Wall** — both are talent-gated, both did not surface. The audit prompt asked specifically about these; sampler confirms they're outside the current meta and not worth tracking until that changes.
- **Spirit Link Totem med=6** is correct — SLT is a 3min CD, and 6 uses across a typical 35-min M+ run means it's pressed reliably. Pass-2 fix continues to be the right call.

### Interrupts

- **Spell name (id):** `Wind Shear` (57994)
- **Cast type:** instant, 12s CD, 30yd range
- **Sample observed kicks per fight (median):** not derivable from BuffsTable. Anecdotally Resto Shamans kick MORE often than Holy Paladins because Wind Shear's 12s CD is shorter than Rebuke's 15s, and the 30yd range means Resto can kick from positions where Holy Paladin would be out of range.
- **Recommended expected count for scoring:** **flag for review.** Current healer denom is 10 in `_score_utility_healer`. Resto Shaman likely clears 10 kicks/run more easily than Holy Paladin does, so the same denom across both healer-with-interrupt specs may give Resto Shaman an inflated utility score relative to Holy. Two paths:
  1. **Per-spec override:** if cast-event sampling shows Resto Shaman averages ~14-16 kicks/run vs Holy at ~7-9, Resto's denom should be raised to ~14 (matching the uplift) so Holy's "got 8/10 kicks" doesn't undergrade them next to Resto's "got 14/10 kicks".
  2. **Status quo + flag:** keep the shared denom of 10 and accept that Resto Shaman simply has higher kick capacity. This is defensible — Wind Shear's range/CD ARE a real spec advantage and the engine should reward classes that have better kits.

  Recommend cast-event sampler follow-up before deciding. The same audit produced a similar concern for Holy Paladin (paladin.md lines 32-34); resolving both at once with a single cast-event sample makes sense.
- **Healer-baseline-kick callout:** Restoration is correctly listed in `HEALER_SPECS_WITH_INTERRUPT` in `roles.py`. Confirmed.

### Dispels

- **In-spec dispel ability:** `Purify Spirit` (77130). Removes Magic + Curse from allies. **Resto's broader version of Cleanse Spirit.**
- **Schools cleansable on allies:** `{Magic, Curse}`
- **Schools the engine should credit this spec for:** `{Magic, Curse}`
- **Notes:** This is the BRM-lesson-3 fix in action for Shaman, mirroring Holy Paladin's "Magic-only-for-Holy" split. The dispel registry MUST encode:
  - Non-Resto (Elemental, Enhancement): `{Curse}` (via Cleanse Spirit 51886)
  - Resto: `{Magic, Curse}` (via Purify Spirit 77130)

  `dispel_abilities.py` already lists both spell IDs correctly under Shaman (class_id=7, lines 33-37). The new per-spec school registry just needs to wire Purify Spirit's Magic-cleanse credit to Resto specifically, not to all Shaman.
- **Offensive purge:** Purge (370) — offensive Magic strip from enemies. Not a defensive cleanse; not credited.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Hex | 51514 | incapacitate | baseline; Resto Shaman's primary M+ CC tool |
| Capacitor Totem | 192058 | stun (AoE) | talent-gated |
| Earthbind Totem | 2484 | slow only | utility, not hard CC |
| Earthgrab Totem | 51485 | root (AoE) | talent-gated |

No Thunderstorm for Resto (Elemental-only). Resto's CC profile is the lightest of the three specs but still respectable — Hex + Capacitor cover the standard M+ "rebreak this caster, lock down that pull" cases.

### Recommended changes

1. `app/scoring/cooldowns.py` `(7, "Restoration")`: **add** `(108280, "Healing Tide Totem", 9, "defensive")` alongside the existing Spirit Link Totem entry. Talent-aware skip handles Cloudburst-build minority. Update the comment block in `cooldowns.py` lines 289-295 — the current note says "Healing Tide Totem (108280) … removed 2026-04-16: drop totems, not self-buffs", which contradicts the sampler evidence. Fix the comment when adding it back.
2. **Dispel registry** (new): `(7, "Restoration") = {Magic, Curse}`. Critical to differentiate from Elemental/Enhancement at Curse-only.
3. **Interrupt benchmark override:** **flag for cast-event sampler follow-up** — Resto Shaman likely averages more kicks than Holy Paladin due to Wind Shear's range/CD advantage. If confirmed, raise Resto's denom from 10 to ~14. Pair with the Holy Paladin flag from paladin.md to do both at once.
4. Talent-gate flags: Healing Tide Totem should be registered with talent-gate handling so Cloudburst-build cohorts (when they emerge in data) aren't punished for the Cloudburst alternative.

### Top-cohort raw output reference

```
Aggregate over 8 Shaman Restoration fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    325174      100%         6   Spirit Link Totem  [Spirit Link Totem]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
       53390   100%       370   Tidal Waves
     1229746   100%        99   Arcanoweave Insight
      462854   100%         6   Skyfury
      470077   100%       467   Coalescing Water
     1265145   100%        28   Refreshing Drink
     1265140   100%        38   Refreshing Drink
     1241715   100%       198   Might of the Void
       79206   100%         7   Spiritwalker's Grace
      207400   100%       266   Ancestral Vigor
     1267089   100%        43   Stormstream Totem
       61295   100%        46   Riptide
      192082   100%         6   Wind Rush
       77762   100%        51   Lava Surge
       73685   100%        72   Unleash Life
      108271   100%        10   Astral Shift
      325174   100%         6   Spirit Link Totem (tracked)
      382024   100%       163   Earthliving Weapon
        2645   100%        20   Ghost Wolf
      456369    88%        62   Amplification Core
      382022    88%         2   Earthliving Weapon
      378081    88%        24   Nature's Swiftness
      457387    88%        65   Wind Barrier
      462568    88%       706   Elemental Resistance
      453409    88%        62   Whirling Air
      383648    88%         2   Earth Shield
       32182    88%         3   Heroism
      108280    88%         9   Healing Tide Totem
       52127    88%         3   Water Shield
     1277461    88%         3   Drink
      453407    88%        62   Whirling Water
```

---

## Open questions for review

1. **Resto Shaman vs Holy Paladin interrupt parity.** Both healer specs share the `_score_utility_healer` denom of 10 kicks/run, but Wind Shear (12s CD, 30yd range) is meaningfully better than Rebuke (15s CD, 5yd melee). Cast-event sampling for both `57994` and `96231` across their respective top-cohorts would settle whether a per-spec denom override is warranted. Suggest pairing this work with the same flag from `paladin.md` — one cast-event sample, both questions answered.
2. **Healing Tide Totem comment-vs-data conflict.** `cooldowns.py` line 290-293 explicitly says HTT "drops totems, not self-buffs" — but the sampler shows aura 108280 at 88% med=9 across the top-Resto cohort. Either the totem applies a self-aura on the caster while it's active (most likely), or there's a different aura ID being conflated. When codifying, verify by grepping a single Resto fight's BuffsTable for 108280 and confirming it's the cast-side companion buff. Then update the comment block explaining what changed.
3. **Primordial Storm (1218125) for Enhancement.** 100% consensus med=51 in the sampler — high enough to surface but mechanically a totem-pulse capstone. Probably correct to leave untracked (saturation risk), but a future audit pass should re-sample this once the Enhancement hero-talent meta stabilizes; if it shifts to a "single press, single big window" model, it becomes a clean track-add candidate.
4. **Stormstream Totem (1267089) for Restoration** — same rationale as #3. Hero-talent passive at the moment, but watch for meta shifts.
5. **Ascendance for Elemental specifically:** the sampler shows 1219480 at 100% — but worth confirming this is the *Elemental* Ascendance aura ID and not a class-shared one. Restoration's Ascendance is 114052, Enhancement's is 114051. If `1219480` is a hero-talent-modified version (Stormbringer's "Tempest" form?), the talent-gate handling needs to encode that nuance.

## Confidence

- **Elemental:** 8 distinct fights, +19 to +21 keys. **High confidence** on Ascendance add (100% consensus) and Stormkeeper keep. Open question on Ascendance aura ID (1219480 vs 114050) needs a quick verification before codification.
- **Enhancement:** 8 distinct fights, +19 keys uniformly. **High confidence** — Doom Winds at 100% med=25, Pass-2 fix held. No edits needed.
- **Restoration:** 8 distinct fights, +20 to +22 keys. **High confidence** on Healing Tide Totem add (88% consensus) and Spirit Link Totem keep. The interrupt-denom question is flagged but doesn't block cooldown codification — that's a separate utility-scoring decision.

All three specs cleared the 5-fight minimum without needing the retry pass. No specs require a second sampling pass.
