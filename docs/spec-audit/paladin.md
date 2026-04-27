# Paladin Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 distinct top player per active dungeon (8 dungeons), Holy / Protection / Retribution
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Paladin" --spec "{Spec}" --samples-per-dungeon 1 --top-n 8`

Cohort key range observed: **+18 to +21** (consistent with the Midnight S1 top-tier band). Eight distinct fights collected per spec — confidence threshold met for all three specs.

---

## Spec: Holy

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 31884   | Avenging Wrath | yes        | 100%        | 13          | keep |
| 200025  | Beacon of Virtue (talent) | no | 0% (not seen) | — | leave (channel/talent — see notes) |
| 633     | Lay on Hands | no            | not seen in top-30 | — | leave (emergency cd, not "performance" major) |

**Notes on splits / alt-builds:**
- Avenging Wrath is universally taken on Holy in this cohort (8/8 logs). No Crusade aura (231895) appeared in any top-30 list, so there's no observed alt-build path here. If/when Crusade gains Holy traction in a later patch, both aura IDs will need tracking with the talent-aware skip catching the absent one.
- High-value passive auras dominate the top-30 (Beacon of the Savior, Sun's Avatar, Will of the Dawn, Dawnlight, Sun Sear, Litany of Lightblind Wrath). These are hero-talent procs / DoT trackers, **not** performance cooldowns the player is choosing to press; they should NOT be added to `SPEC_MAJOR_COOLDOWNS`. Tracking them would saturate the category at 100 (same trap that `Barkskin` caused on Resto Druid in Pass 3).
- **Apotheosis (200183)** appears tracked for Priest Holy but is the wrong class — confirmed not present in Paladin Holy data. Already correctly absent.
- Avenging Wrath median uses on Holy (13) is comfortably below Ret's (26). Current 20% expected uptime is a reasonable single-CD bench; consider whether this should be lowered slightly given Holy AW windows are shorter than Ret's. **No change recommended** until cooldown_usage distribution is reviewed for Holy specifically.

### Interrupts

- **Spell name (id):** `Rebuke` (96231)
- **Cast type:** instant
- **Sample observed kicks per fight (median):** Cannot derive from BuffsTable sampler — Rebuke leaves no aura on the paladin. **Needs cast-event sample** to validate the engine's `interrupts / 10` denominator for Holy.
- **Recommended expected count for scoring:** 10 (current healer-with-interrupt denom in `_score_utility_healer`). Holy Paladins do kick in M+ but at lower volume than Resto Shaman because Wind Shear is a 12s CD vs Rebuke's 15s; flag for cast-event audit.
- **Healer-baseline-kick callout:** Holy is correctly listed in `HEALER_SPECS_WITH_INTERRUPT` in `roles.py`. Confirmed.

### Dispels

- **In-spec dispel ability:** `Cleanse` (4987). Removes Magic + Poison + Disease from allies.
- **Schools cleansable on allies:** `{Magic, Poison, Disease}`
- **Schools the engine should credit this spec for:** `{Magic, Poison, Disease}`
- **Notes:** Holy is the **only** Paladin spec that cleanses Magic. Prot/Ret use `Cleanse Toxins` (Poison/Disease only). The dispel-school registry the audit is producing must encode this distinction precisely or Holy's Magic-cleanse contribution gets credited to Prot/Ret as well — the BRM lesson #3 fix.
- No offensive dispel in the kit (Paladin lacks a Tranquilizing Shot / Purge / Mass Dispel offensive analog).

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Hammer of Justice | 853 | stun | baseline 6s stun, ~60s CD |
| Repentance | 20066 | incapacitate (Humanoid/Beast/Dragonkin/Giant) | talent-gated, 1min CD |
| Blinding Light | 115750 | disorient (AoE) | talent-gated |
| Turn Evil | 10326 | fear (Undead/Demon) | situational utility |

### Recommended changes

1. `app/scoring/cooldowns.py` `(2, "Holy")`: **No changes.** Avenging Wrath at 100% med=13 is correctly tracked and uptime=20 is a fair bench.
2. **Dispel registry** (new): `(2, "Holy") = {Magic, Poison, Disease}`.
3. **Interrupt benchmark override:** keep healer default of 10. Flag for follow-up cast-event sampler to verify Holy actually achieves ~10 kicks/fight (current concern is the median may be lower than Resto Shaman, which would warrant a Holy-specific override).
4. **No talent-gate flags needed** — only one aura tracked, and it's at 100% consensus.

### Top-cohort raw output reference

```
Aggregate over 8 Paladin Holy fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
     31884      100%        13   Avenging Wrath  [Avenging Wrath]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
       31821   100%         6   Aura Mastery
         465   100%         1   Devotion Aura
     1265145   100%        35   Refreshing Drink
      463073   100%        10   Sun's Avatar
      431752   100%         8   Will of the Dawn
     1245369   100%       109   Beacon of the Savior
      431462   100%         1   Will of the Dawn
     1229746   100%       108   Arcanoweave Insight
      223819   100%       123   Divine Purpose
      156322   100%        66   Eternal Flame
       54149   100%       111   Infusion of Light
      431415   100%        93   Sun Sear
      431381   100%        10   Dawnlight
     1241715   100%       188   Might of the Void
      400745   100%       300   Afterimage
     1264050   100%        13   Born in Sunlight
      414273   100%        13   Hand of Divinity
      431907   100%        62   Sun's Avatar
      431522   100%        37   Dawnlight
         498   100%        23   Divine Protection
        6940   100%         8   Blessing of Sacrifice
     1244893   100%       141   Beacon of the Savior
         642   100%         5   Divine Shield
     1265140   100%        45   Refreshing Drink
       31884   100%        13   Avenging Wrath (tracked)
     1236616    88%         4   Light's Potential
     1264426    88%         1   Void-Touched
     1263727    75%        99   Litany of Lightblind Wrath
     1241410    75%        13   Hammer of Wrath
     1277389    75%         1   Vantus Rune: Radiant
```

---

## Spec: Protection

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 31850   | Ardent Defender | yes           | 100%        | 20          | keep |
| 393108  | Guardian of Ancient Kings | yes | 100%        | 12          | keep |
| 132403  | Shield of the Righteous | yes   | 100%        | 14          | keep |
| 86659   | Guardian of Ancient Kings (legacy ID) | no | 100% | 27   | **investigate — see notes** |
| 432502  | Sacred Weapon (hero talent) | no  | 100%        | 57          | leave (passive trinket-like aura, not active CD) |
| 432607  | Holy Bulwark (hero talent) | no   | 100%        | 230         | leave (passive proc/stack tracker) |
| 386652  | Bulwark of Righteous Fury | no    | 100%        | 1337        | leave (rotational mastery stack) |

**Notes on splits / alt-builds:**
- All three currently-tracked Prot CDs appear at 100% consensus across 8/8 logs. No drops, no additions needed for the active-cooldown story.
- **`86659` (legacy GoAK aura) showing at 100% med=27 alongside `393108` (current GoAK aura) at 100% med=12** is the most actionable finding. Two possibilities:
  1. They're complementary auras applied during the same cast — `393108` is the active damage-reduction window (12 uses, ~1 per AD-reset), `86659` is a sub-aura or stack tracker that ticks more often (27).
  2. `86659` is a tracking aura applied per-mob or per-stack while GoAK is up.

  Either way, current tracking on `393108` matches the "active window" semantics correctly. Recommend **leaving `393108` tracked and not adding `86659`** — but flag for a post-audit sampler dive to confirm the relationship before the codification PR locks it in.
- **Sentinel vs Templar hero-talent split:** the sampler shows `Sacred Weapon` and `Holy Bulwark` at 100% — these are Templar staples. Sentinel-tree auras (Eye of Tyr, Truth's Wake) didn't surface at 100%, suggesting the top-cohort is uniformly Templar in this season. If Sentinel becomes meta later, no change needed because neither tree's signature ability is currently tracked as a "major CD."
- **Divine Toll** would be the obvious other Prot CD candidate but it casts only and leaves no self-aura — same pattern as Wake of Ashes. Cannot be added via BuffsTable; flag for cast-event path.
- **Eye of Tyr (387174)** — same: enemy debuff, not self-buff. Not visible in BuffsTable.

### Interrupts

- **Spell name (id):** `Rebuke` (96231)
- **Cast type:** instant
- **Sample observed kicks per fight (median):** not derivable from this sampler.
- **Recommended expected count for scoring:** 12 (engine's tank denom in `_score_utility_dps_tank`). Tank-route variance argument applies normally.
- No special override needed.

### Dispels

- **In-spec dispel ability:** `Cleanse Toxins` (213644). Removes Poison + Disease from allies. **No Magic dispel.**
- **Schools cleansable on allies:** `{Poison, Disease}`
- **Schools the engine should credit this spec for:** `{Poison, Disease}`
- **Notes:** This is the BRM-lesson-3 fix in action. The current `dispel_capability.py` flags Paladin (class_id=2) as having a dispel — true — but the new per-spec registry must NOT credit Prot for Magic dispels. Prot's contribution to a healer's offloaded magic-dispel work is zero.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Hammer of Justice | 853 | stun | baseline |
| Avenger's Shield silence | 31935 | silence (auto-applied on cast hit) | baseline rotational tool — counts as silence/interrupt-adjacent |
| Blessing of Spellwarding | 204018 | magic immunity (single target) | talent-gated, defensive utility — appeared at 100% med=2 |
| Repentance | 20066 | incapacitate | rare on Prot but available |

Note: Avenger's Shield's silence component is the standout Prot M+ tool — it's why Prot Paladin is one of the strongest "second kicker" tanks.

### Recommended changes

1. `app/scoring/cooldowns.py` `(2, "Protection")`: **No drops, no adds.** All three tracked auras at 100% consensus.
2. **Dispel registry** (new): `(2, "Protection") = {Poison, Disease}`. Critical: do NOT include Magic.
3. **Interrupt benchmark override:** none. Tank default of 12 stands.
4. **Open question (low priority):** the `86659` vs `393108` GoAK aura pairing — confirm before codification but don't block on it.

### Top-cohort raw output reference

```
Aggregate over 8 Paladin Protection fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
     31850      100%        20   Ardent Defender  [Ardent Defender]
    393108      100%        12   Guardian of Ancient Kings  [Guardian of Ancient Kings]
    132403      100%        14   Shield of the Righteous  [Shield of the Righteous]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      432502   100%        57   Sacred Weapon
     1269179   100%       241   Valor
       31850   100%        20   Ardent Defender (tracked)
      386652   100%      1337   Bulwark of Righteous Fury
      378412   100%       137   Light of the Titans
       86659   100%        27   Guardian of Ancient Kings
         465   100%         1   Devotion Aura
      432607   100%       230   Holy Bulwark
      223819   100%       129   Divine Purpose
         642   100%         5   Divine Shield
      379017   100%      3079   Faith's Armor
      182104   100%       436   Shining Light
        1044   100%        12   Blessing of Freedom
     1277026   100%        27   Hammer of Wrath
     1229746   100%       110   Arcanoweave Insight
      432496   100%        31   Holy Bulwark
     1239002   100%         2   Lesser Bulwark
      204018   100%         2   Blessing of Spellwarding
     1271383   100%        19   Masterwork: Bulwark
      469703   100%        15   Tempered in Battle
      378457   100%         1   Soaring Shield
     1236616   100%         6   Light's Potential
      209388   100%       344   Bulwark of Order
     1268810   100%        77   Vanguard
      327510   100%       334   Shining Light
      378279   100%         1   Gift of the Golden Val'kyr
     1272298   100%       648   Light-Blessed Shield
      386730   100%        25   Divine Resonance
      393108   100%        12   Guardian of Ancient Kings (tracked)
      132403   100%        14   Shield of the Righteous (tracked)
```

---

## Spec: Retribution

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 31884   | Avenging Wrath | yes        | 100%        | 26          | keep |
| 1234189 | Execution Sentence | yes    | 100%        | 25          | keep |
| 231895  | Crusade (alt-build) | no     | 0% (not seen) | —         | leave for now — see notes |
| 184662  | Shield of Vengeance | no     | 100%        | 17          | leave (rotational personal defensive — not "major performance" CD) |
| 403876  | Divine Protection | no       | 100%        | 17          | leave (1min defensive — same case as Resto Druid Barkskin: would saturate category) |
| 198034  | Divine Hammer | no           | 100%        | 52          | leave (rotational ability proc/aura, not pressed CD) |

**Notes on splits / alt-builds:**
- Both currently-tracked CDs at 100% — Pass-2 fixes (replacing Wake of Ashes with Execution Sentence) held up perfectly across 8/8 logs.
- **Avenging Wrath vs Crusade alt-build path:** Crusade did not appear in any top-30 list. The Midnight S1 top cohort is **uniformly running Avenging Wrath** for Ret. Two possibilities to verify:
  1. Crusade is genuinely off-meta in current S1 (Templar/Herald hero-talent picks favor AW).
  2. Crusade's aura ID has changed and the sampler missed it.

  Recommend **deferring the Crusade alt-build registration** until either (a) we see a non-trivial cohort actually running it, or (b) someone surfaces the correct Midnight aura ID. Until then, AW alone covers the meta.
- **Shield of Vengeance / Divine Protection** are personal defensives that EVERY Ret presses every minute. Adding them would saturate `cooldown_usage` at 100 across the entire spec — exactly the failure mode that prompted the Pass-3 Barkskin removal on Resto Druid. **Do not add.**
- **The Hunt** (370965) is tracked for Havoc DH but is hero-talent-specific; for Ret, the Hunt-equivalent is folded into Templar's offerings and didn't surface as a clean major aura.

### Interrupts

- **Spell name (id):** `Rebuke` (96231)
- **Cast type:** instant
- **Sample observed kicks per fight (median):** not derivable from this sampler.
- **Recommended expected count for scoring:** 15 (DPS denom in `_score_utility_dps_tank`). Standard.
- No override needed.

### Dispels

- **In-spec dispel ability:** `Cleanse Toxins` (213644). Removes Poison + Disease from allies.
- **Schools cleansable on allies:** `{Poison, Disease}`
- **Schools the engine should credit this spec for:** `{Poison, Disease}`
- **Notes:** Same as Prot — NOT a magic dispel. Same registry shape.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Hammer of Justice | 853 | stun | baseline |
| Repentance | 20066 | incapacitate | talent-gated, mostly seen on multi-target rebreak pulls |
| Blinding Light | 115750 | disorient (AoE) | talent-gated |
| Turn Evil | 10326 | fear | situational |

### Recommended changes

1. `app/scoring/cooldowns.py` `(2, "Retribution")`: **No drops, no adds.** AW + Execution Sentence both at 100%, no alt-build need.
2. **Dispel registry** (new): `(2, "Retribution") = {Poison, Disease}`. Match Prot.
3. **Interrupt benchmark override:** none. DPS default of 15 stands.
4. Talent-gate flags: none currently needed. If/when a Crusade-running cohort emerges, register `(231895, "Crusade", 20, "offensive")` alongside AW with the talent-aware skip handling whichever the player didn't take.

### Top-cohort raw output reference

```
Aggregate over 8 Paladin Retribution fights

Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
     31884      100%        26   Avenging Wrath  [Avenging Wrath]
   1234189      100%        25   Execution Sentence  [Execution Sentence]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1236616   100%         6   Light's Potential
      198034   100%        52   Divine Hammer
      432629   100%       107   Undisputed Ruling
      431536   100%       107   Shake the Heavens
     1229746   100%        85   Arcanoweave Insight
         642   100%         5   Divine Shield
      184662   100%        17   Shield of Vengeance
     1241715   100%       196   Might of the Void
      265140   100%        53   Refreshing Drink
      433732   100%        54   Light's Deliverance
        6940   100%         7   Blessing of Sacrifice
     1234189   100%        25   Execution Sentence (tracked)
     1265145   100%        38   Refreshing Drink
      407065   100%       472   Rush of Light
      408458   100%        69   Divine Purpose
      387178   100%        26   Empyrean Legacy
      433674   100%      2732   Light's Deliverance
      403876   100%        17   Divine Protection
      433671   100%       767   Sanctification
     1241410   100%        26   Hammer of Wrath
      461867   100%       118   Sacrosanct Crusade
       31884   100%        26   Avenging Wrath (tracked)
      406086   100%       132   Art of War
      406064    88%         1   Art of War
         465    88%         1   Devotion Aura
        1044    88%        10   Blessing of Freedom
      383781    88%        12   Algeth'ar Puzzle
     1242775    88%        12   Farstrider's Step
     1264426    75%         2   Void-Touched
      462854    75%         6   Skyfury
```

---

## Open questions for review

1. **GoAK dual-aura on Prot Paladin:** `393108` (currently tracked, med=12) and `86659` (currently NOT tracked, med=27) both appeared at 100% consensus. Is `86659` a per-stack/per-mob sub-aura applied during a GoAK window, or is it a separate longer-lived companion buff? The current tracking on `393108` appears correct (it's the active mitigation aura), but a confirmation pass would let us close the question definitively.
2. **Holy interrupt volume baseline:** Holy Paladins are credited for kicks via `interrupts / 10` in the engine. The BuffsTable sampler can't validate this — needs a cast-event sample of `96231 Rebuke` for the same top-cohort to confirm Holy actually averages ~10 kicks/run. If the real number is 5-7, a Holy-specific denom override (similar to the tank's softer 12 vs DPS 15) is warranted.
3. **Crusade aura ID in Midnight:** verified zero appearance at top of Ret rankings. Confirm whether Crusade is currently underpicked vs the aura ID has shifted — a quick WoWHead lookup for "Crusade aura" Midnight S1 would settle it. If the meta later drifts, both aura IDs need to be tracked.
4. **Sacrosanct Crusade (461867)** at 100% med=118 on Ret is a hero-talent passive proc, NOT a hint that Crusade is being talented — confirmed, ignore for cooldown tracking purposes.

## Confidence

- **Holy:** 8 distinct fights, +19 to +21 keys. **High confidence** on the cooldown story (single-CD spec). Lower confidence on interrupt benchmark — flagged for cast-event follow-up.
- **Protection:** 8 distinct fights, +18 to +20 keys. **High confidence** — all three tracked CDs at 100% consensus, no edits needed. One open question on the dual-aura GoAK mystery, but it doesn't block recommendations.
- **Retribution:** 8 distinct fights, +20 to +21 keys. **High confidence** on AW + Execution Sentence (Pass-2 fixes validated). Crusade alt-build path defer-until-observed is the right call.

All three specs cleared the 5-fight minimum without needing the retry pass.
