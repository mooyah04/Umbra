# Death Knight Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 report per dungeon, top 8 per dungeon, +18 to +22 keys, 8 active-season Midnight S1 dungeons
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Death Knight" --spec "{Spec}" --samples-per-dungeon 1 --top-n 8`

Class ID: 6. Three specs sampled: Blood (tank), Frost (DPS), Unholy (DPS). 8 distinct top-cohort fights captured per spec — comfortably above the 5-fight confidence floor.

DK has Mind Freeze (47528) as the universal interrupt across all three specs. No defensive cleanse exists in the baseline kit for any DK spec — they are a "no dispel" class entirely, which the new dispel registry must record explicitly.

---

## Spec: Blood

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 55233   | Vampiric Blood       | yes | 100% | 45  | keep |
| 81256   | Dancing Rune Weapon  | yes | 100% | 93  | keep |
| 48792   | Icebound Fortitude   | no  | 100% | 6   | **add** — major personal defensive (~3min CD), 6 uses/key consistent with a real "press on cooldown" pattern |
| 145629  | Anti-Magic Zone      | no  | 100% | 3   | **add** — group-wide magic absorb, ~2min CD; 3 uses/key indicates Blood is using AMZ as a positional party CD, not a personal proc |
| 194844  | Bonestorm            | n/a | 0%   | 0   | not seen — alternate talent path; do not track unless build divergence appears in a wider sample |

**Notes on splits / alt-builds:**
- All 8 sampled Blood DKs ran the same major-CD shape: Vampiric Blood + DRW + Icebound Fortitude + AMZ. No alt-build divergence detected at this sample depth — the kit is stable.
- DRW median 93 uses is the **buff-tick count**, not casts — DRW is a maintained 8s self-buff with periodic ticks while active. The CD itself is ~2min. Treat consensus, not raw count, as the signal.
- Bonestorm (194844) and Blood Tap variants did not surface; current top-cohort builds skip both. If we add them speculatively they would fail the talent-aware skip and dock players unfairly.
- Sanguine Ground (391459) and Boiling Point (1265982/1265968) are San'layn hero-talent passive auras, not pressable CDs. Skip.
- Blood Shield (77535) and Bone Shield (195181) are passive maintenance auras driven by Death Strike / Marrowrend — exclude.

### Interrupts

- **Spell name (id):** `Mind Freeze` (47528)
- **Cast type:** instant, 15s CD, 15yd range
- **Sample observed kicks per fight (median):** Not surfaced in this sampler (sampler only reads BuffsTable). No revision to expected kicks proposed without a separate cast-event sample.
- **Recommended expected count for scoring:** 12 (role default for tank). Blood has a baseline kick like every melee tank, and at the 12-kick floor Blood is in line with Prot Warrior / Vengeance DH expectations.

### Dispels

- **In-spec dispel ability:** **none in baseline kit.** Death Knight has zero defensive cleanse on allies across all three specs.
- **Schools cleansable on allies:** none.
- **Schools the engine should credit this spec for:** none — register `(6, "Blood") = set()` in the dispel registry so the healer-utility-of-cleanses path skips Blood entirely instead of awarding 0 (which would penalize the player for a kit gap).
- **Notes:** Anti-Magic Shell (48707) and Anti-Magic Zone (145629) are **personal/raid-wide magic absorbs**, not purges. They eat magic damage; they do not remove debuffs. Do not register them as dispels. Death Pact / Death Strike are not dispels either.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Asphyxiate | 108194 | stun | baseline Blood CC, 5s stun, 1min CD |
| Death Grip | 49576 | displacement (not stun) | universal DK utility; pulls a target. Classify as displacement/forced-movement, not a stun. Useful for grading "did the tank pull the priority add" but not a generic stun count. |
| Chains of Ice | 45524 | slow | hard slow, do **not** count as CC for grading — applying it is part of normal target maintenance, not an active-mitigation choice |
| Gorefiend's Grasp | 108199 | mass-pull | utility, talent-gated; Blood's signature M+ tool. Could matter for a future "AoE setup" metric but not for generic CC scoring. |

### Recommended changes

1. `app/scoring/cooldowns.py` `(6, "Blood")`: keep both currently tracked entries. **Add Icebound Fortitude (48792, expected uptime ~6, defensive)** and **Anti-Magic Zone (145629, expected uptime ~3, defensive)**. Both are universal across the cohort with no talent gating observed.
2. **Dispel registry** (new): `(6, "Blood") = set()` (empty) — DK has no ally cleanse.
3. **Interrupt benchmark override:** none. 12 kicks/fight is realistic.
4. **Talent-gate flags:** none required for current entries — all four proposed CDs sit at 100% consensus. If a future sample shows AMZ or IBF dropping below 90%, flag at that time.

### Top-cohort raw output reference

```
   aura_id    pct  med_uses  name
      463730   100%      2312   Coagulating Blood
      145629   100%         3   Anti-Magic Zone
     1229746   100%        67   Arcanoweave Insight
     1265982   100%       123   Boiling Point
      391459   100%       222   Sanguine Ground
       55233   100%        45   Vampiric Blood (tracked)
     1236616   100%         4   Light's Potential
     1265968   100%       138   Boiling Point
      460500   100%        33   Bloodied Blade
       48707   100%        22   Anti-Magic Shell
      274009   100%       399   Voracious
     1264568   100%        92   Dance of Midnight
      391527   100%        44   Umbilicus Eternus
      391519   100%        45   Umbilicus Eternus
      219788   100%        11   Ossuary
      273947   100%      1363   Hemostasis
       81141   100%        78   Crimson Scourge
       81256   100%        93   Dancing Rune Weapon (tracked)
      391481   100%       873   Coagulopathy
      195181   100%       763   Bone Shield
      374585   100%        95   Rune Mastery
      454871   100%        11   Blood Draw
       48265   100%        29   Death's Advance
     1264407   100%        97   Dance of Midnight
       77535   100%       399   Blood Shield
      188290   100%       412   Death and Decay
      180612   100%       441   Recently Used Death Strike
      194879   100%       485   Icy Talons
       48792   100%         6   Icebound Fortitude
      460499   100%       324   Bloodied Blade
```

---

## Spec: Frost

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 51271   | Pillar of Frost      | yes | 100% | 34  | keep |
| 152279  | Breath of Sindragosa | n/a | 0%   | 0   | not seen — channel buff and/or non-meta talent in current Midnight S1 builds. Do not add. |
| 47568   | Empower Rune Weapon  | n/a | 0%   | 0   | not in top 30. Cast that may not produce a self-aura, or simply skipped in current builds. Skip. |
| 377195  | Enduring Strength    | no  | 100% | 34  | **possible add** — Rider of the Apocalypse / Frostreaver hero-talent buff that procs alongside PoF (median exactly matches PoF's 34). However, it is a passive proc keyed off PoF rather than a separately-pressed CD; scoring on it would double-count PoF. Recommend **skip** for cooldown scoring; could surface as a "rotation health" indicator on the run page. |
| 1233152 | Remorseless Winter   | no  | 100% | 34  | **possible add** — RW is a 20s-CD ground effect. Median 34 across an M+ key is consistent with rotational use (every ~30s pull-time). Per BRM lessons, ~30+ uses signals "rotational, not major CD" — **skip** for major-CD tracking. |
| 1230916 | Killing Streak       | no  | 100% | 686 | proc, exclude |
| 456370  | Cryogenic Chamber    | no  | 100% | 477 | proc / hero talent shield, exclude |
| 469169  | Swift and Painful    | no  | 100% | 12  | hero talent passive proc, exclude |

**Notes on splits / alt-builds:**
- Frost's major-CD story is genuinely thin. Pillar of Frost is the only true "press-on-cooldown self-buff" in the modern Frost kit. Breath of Sindragosa builds exist in raid but did **not** show in any of the 8 top-cohort M+ logs — Midnight S1 M+ Frost is converged on the PoF / Frost Strike build.
- Empower Rune Weapon (47568) is a 1-min rune-regen CD that good Frost DKs press regularly. The fact that it didn't appear in any top-30 BuffsTable strongly suggests the cast doesn't leave a trackable self-aura (similar to the Frostwyrm's Fury / Wake of Ashes pattern). If we wanted to credit ERW we'd need a cast-event detection path.
- Enduring Strength (377195) at exactly the same median count as PoF (34) is a tell that it's the PoF-extension hero buff. Tracking it would inflate Frost's CD score by re-counting the same press.
- **Verdict for Frost: keep PoF as the only tracked major CD.** Frost is one of those specs where we accept that BuffsTable can only see one CD, and the engine's per-spec list reflects the kit honestly. This is preferable to adding rotational buffs (~30+ uses) that would saturate the score.

### Interrupts

- **Spell name (id):** `Mind Freeze` (47528)
- **Cast type:** instant, 15s CD, 15yd range
- **Sample observed kicks per fight (median):** Not measured in this sampler.
- **Recommended expected count for scoring:** 15 (role default for DPS). Frost is a melee DPS with an instant kick on a tight CD; 15 is realistic.

### Dispels

- **In-spec dispel ability:** **none in baseline kit.**
- **Schools cleansable on allies:** none.
- **Schools the engine should credit this spec for:** none — register `(6, "Frost") = set()`.
- **Notes:** Same as Blood. AMS / AMZ are absorbs, not dispels. Frost has no purge-style ability.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Chains of Ice | 45524 | slow | maintenance slow, **don't** count for CC scoring |
| Death Grip | 49576 | displacement | universal DK pull, useful but not a stun |
| Asphyxiate | 108194 | stun | **talent-gated for Frost** (baseline only on Blood). Many Frost builds skip it for Strangulate or Blinding Sleet. |
| Blinding Sleet | 207167 | disorient | talent-gated AoE disorient, ~12s window |

(Bullet form: Frost's CC is largely talent-driven. The grader should not assume Asphyxiate is present; check the player's talents before scoring CC use. If the engine doesn't yet do per-spec CC scoring, this is an "open question" item below.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(6, "Frost")`: **no change.** PoF stays as the sole tracked entry. Do not add Enduring Strength (double-counts PoF), Remorseless Winter (rotational not major), or any hero-talent procs. Honest "1 major CD" list is correct.
2. **Dispel registry** (new): `(6, "Frost") = set()` (empty).
3. **Interrupt benchmark override:** none. 15 kicks/fight is realistic.
4. **Talent-gate flags:** none on the cooldown list (only one entry, universal). Note: Asphyxiate is talented for Frost, not baseline, so a future per-spec CC tracker should be talent-aware here.

### Top-cohort raw output reference

```
   aura_id    pct  med_uses  name
       59052   100%       293   Rime
       48792   100%         6   Icebound Fortitude
      377103   100%        69   Bonegrinder
        8936   100%        74   Regrowth
       51271   100%        34   Pillar of Frost (tracked)
     1230916   100%       686   Killing Streak
     1269300   100%       171   Empowered Strikes
      443532   100%       293   Bind in Darkness
      377101   100%       255   Bonegrinder
      207203   100%       282   Frost Shield
      101568   100%        34   Dark Succor
     1233152   100%        34   Remorseless Winter
     1229746   100%        83   Arcanoweave Insight
      440290   100%       788   Rune Carved Plates
      456370   100%       477   Cryogenic Chamber
      145629   100%         6   Anti-Magic Zone
      377195   100%        34   Enduring Strength
      469169   100%        12   Swift and Painful
       48265   100%        28   Death's Advance
     1265145   100%        40   Refreshing Drink
         774   100%        58   Rejuvenation
      377192   100%       295   Enduring Strength
       53365   100%       115   Unholy Strength
     1230306   100%        78   Frostreaper
       48707   100%        22   Anti-Magic Shell
     1265639   100%        17   Chosen of Frostbrood
       48438   100%       111   Wild Growth
     1265140   100%        59   Refreshing Drink
        1126   100%         6   Mark of the Wild
       33763   100%        11   Lifebloom
```

---

## Spec: Unholy

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 42650   | Army of the Dead          | yes | 100% | 17 | keep |
| 275699  | Apocalypse                | n/a | 0%   | 0  | applies a debuff to target, not self-buff. BuffsTable can't see it. **Skip.** |
| 207289  | Unholy Assault            | n/a | 0%   | 0  | did not appear in top 30. Either non-meta talent in current builds or aura ID changed. Skip. |
| 63560   | Dark Transformation       | n/a | 0%   | 0  | buffs the ghoul (pet), not the DK. Pet-pattern same as Frostwyrm's Fury. **Skip** for BuffsTable tracking. |
| 444763  | Apocalyptic Conquest      | no  | 100% | 39 | **possible add** — Rider of the Apocalypse hero-talent self-buff that fires after Apocalypse. Median 39 is high (rotational-ish), but it's the cleanest "press signal" for the Apoc rotation since Apoc itself is invisible to BuffsTable. **Recommend skip** at 39 uses — too rotational for "major" tier, and the talent-aware skip for non-Rider builds adds complexity. |
| 390260  | Commander of the Dead     | no  | 100% | 34 | **possible add** — buffs the ghoul/pet during AotD windows. Median 34 across an M+ aligns with AotD + Dark Transformation cycles. Like Apocalyptic Conquest, this is keyed off other CDs and would double-count. **Skip.** |
| 1242654 | Reaping                   | no  | 100% | 34 | hero-talent passive aura, exclude |
| 444742  | Defile                    | n/a | 0%   | 0  | talent-gated AoE damage zone; not seen in top 30 — current builds run Death and Decay. Skip. |
| 1268917 | Unholy Aura               | no  | 100% | 412 | passive party buff, exclude |
| 51460   | Runic Corruption          | no  | 100% | 192 | passive proc, exclude |

**Notes on splits / alt-builds:**
- Unholy's CD story is similarly thin once you exclude debuffs (Apocalypse, Festering Strike applications), pet-buffs (Dark Transformation, Commander of the Dead), and proc/passive auras. AotD is the only true self-buff "press the big button" CD.
- Apocalyptic Conquest (444763) is interesting: it's the Rider of the Apocalypse hero capstone payoff and every top Unholy ran Rider in this sample. Median 39 puts it in a gray zone — high enough to be rotational, but it does track a real meaningful press cycle (Apoc / Festering Wound burst). I lean **skip** because:
  1. It double-counts Apocalypse pulls (which we can't track directly anyway).
  2. The Deathbringer hero talent is an alt-build path; if a Deathbringer Unholy emerges, Conquest would be 0% for them and the talent-aware skip would need to know the rule.
  3. With AotD already tracked, Unholy's CD score has signal. Adding Conquest would push it toward saturation similar to the BRM Barkskin issue Logan flagged.
- **Verdict for Unholy: keep AotD as the only tracked major CD.** Same kit-honest stance as Frost.
- Notable: Apocalypse (275699) is a debuff-on-target ability. If we ever add a debuff-on-target detection path (mentioned for Assassination's Deathmark and Mage's Touch of the Magi), Apocalypse should be on that list — it's the real Unholy major CD, ~90s, applies a marker debuff and summons ghouls.

### Interrupts

- **Spell name (id):** `Mind Freeze` (47528)
- **Cast type:** instant, 15s CD, 15yd range
- **Sample observed kicks per fight (median):** Not measured in this sampler.
- **Recommended expected count for scoring:** 15 (role default for DPS). Unholy is a melee DPS — 15 kicks/key is realistic, same as Frost.

### Dispels

- **In-spec dispel ability:** **none in baseline kit.**
- **Schools cleansable on allies:** none.
- **Schools the engine should credit this spec for:** none — register `(6, "Unholy") = set()`.
- **Notes:** Same as Blood and Frost. DK is a class-wide "no dispel" entry across all three specs.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Death Grip | 49576 | displacement | universal DK utility |
| Strangulate | 47476 | silence | **talent-gated** for all DK specs (PvP-talent in some seasons; PvE talent capstone in others). Common in M+ for silencable casters. |
| Chains of Ice | 45524 | slow | maintenance slow, don't count |
| Asphyxiate | 108194 | stun | talent-gated for Unholy (baseline only on Blood) |

### Recommended changes

1. `app/scoring/cooldowns.py` `(6, "Unholy")`: **no change.** AotD stays as the sole tracked entry. Do not add Apocalyptic Conquest or Commander of the Dead — both are dependent procs that double-count Apoc/AotD windows.
2. **Dispel registry** (new): `(6, "Unholy") = set()` (empty).
3. **Interrupt benchmark override:** none. 15 kicks/fight is realistic.
4. **Talent-gate flags:** none on the cooldown list (single entry, universal). Future debuff-on-target detection should target **Apocalypse (275699)** — the real signature Unholy CD that BuffsTable can't see.

### Top-cohort raw output reference

```
   aura_id    pct  med_uses  name
      188290   100%       349   Death and Decay
     1242654   100%        34   Reaping
     1241077   100%        67   Festering Scythe
      410089   100%        69   Prescience
     1242223   100%        17   Forbidden Knowledge
       48792   100%         7   Icebound Fortitude
       42650   100%        17   Army of the Dead (tracked)
      444763   100%        39   Apocalyptic Conquest
      403295   100%         5   Black Attunement
     1271199   100%       304   Blighted
       51460   100%       192   Runic Corruption
      458123   100%        67   Festering Scythe
      390260   100%        34   Commander of the Dead
        8936   100%        94   Regrowth
     1282570   100%       412   Forbidden Ritual
     1242998   100%      1239   Lesser Ghoul
     1262496   100%        17   Light Company Guidon
     1241569   100%       388   Clawing Shadows
      155777   100%        45   Rejuvenation (Germination)
     1254252   100%       731   Lesser Ghoul
     1265140   100%        62   Refreshing Drink
      194879   100%       501   Icy Talons
     1266686   100%        65   Alnsight
       49039   100%         7   Lichborne
     1268917   100%       412   Unholy Aura
         774   100%        53   Rejuvenation
      374227   100%         5   Zephyr
      395152   100%        49   Ebon Might
      374585   100%       117   Rune Mastery
       48438   100%       121   Wild Growth
```

---

## Open questions for review

1. **Should Frost and Unholy stay at one tracked CD each?** Both specs converge on a single self-buff major in BuffsTable terms. Adding rotational/proc auras would inflate the score artificially (BRM Barkskin saturation pattern). My recommendation is "yes, kit-honest single-entry list" — but Logan should sign off because it means Frost/Unholy CD scoring will have less granularity than (e.g.) Brewmaster which has 4 tracked entries.
2. **Debuff-on-target detection path.** Apocalypse (275699) is Unholy's real signature CD and we can't see it. This is the same gap that affects Assassination Rogue (Deathmark), Arcane Mage (Touch of the Magi), and Vengeance DH (Fiery Brand). The DK audit reinforces that this gap is broad enough to warrant a dedicated detection path eventually.
3. **Anti-Magic Zone classification.** AMZ is a *raid-wide* magic absorb, not a personal one. For Blood, it's a tank-pressed party CD. The "tank tracks personal mitigation" framing in cooldowns.py says all tank CDs are defensive — AMZ fits that, but it's worth noting it benefits the whole party. Defensive kind tag is correct; just flagging the semantic.
4. **CC scoring for talent-gated stuns.** Asphyxiate is baseline only for Blood. If the engine ever scores "did the DPS use their stun on the priority cast", that scorer must check the player's talents before assuming Asphyxiate is on Frost/Unholy. Today the engine doesn't do CC scoring per spec; flagging for whenever it does.

## Confidence

- **Blood: high.** 8 distinct top-cohort fights at +18 to +20. Both tracked CDs at 100%, two clear add candidates (IBF, AMZ) at 100% with realistic-major medians. No alt-build divergence detected.
- **Frost: high.** 8 distinct top-cohort fights at +18 to +20. Single tracked CD (PoF) at 100%. No false-positive add candidates — every other 100%-consensus aura is either rotational (>30 uses), a proc, or a hero-talent passive that double-counts PoF.
- **Unholy: high.** 8 distinct top-cohort fights at +21 to +22 (highest-key cohort of the three). Single tracked CD (AotD) at 100%. The interesting "almost candidate" Apocalyptic Conquest is consistent across all 8 fights but the analysis above explains why it should still be skipped.

All three specs comfortably exceeded the 5-fight floor on the first sampler pass; no retry was needed.
