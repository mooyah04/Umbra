# Rogue Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 report per dungeon, top-8 per dungeon scan, 8 active-season Midnight S1 dungeons (Windrunner Spire, Maisara Caverns, Magister's Terrace, Algeth'ar Academy, Nexus-Point Xenas, Skyreach, Pit of Saron, Seat of the Triumvirate)
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Rogue" --spec "{Assassination|Outlaw|Subtlety}" --samples-per-dungeon 1 --top-n 8`
**Fights sampled:** Assassination 8 / Outlaw 8 / Subtlety 8 (24 distinct top players in +19 to +21 range)

> Class IDs verified from `app/scoring/roles.py`: Rogue is class_id `4`. All three specs (Assassination, Outlaw, Subtlety) are DPS. Kick (1766) is the universal Rogue interrupt across all three specs. Rogue has no defensive cleanse on allies in any spec.

---

## Spec: Assassination

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| (none)  | (no current entries) | — | — | — | Sin currently has zero tracked CDs because Deathmark/Vendetta were debuffs (BuffsTable can't see them) |
| 385627  | Kingsbane (self-aura) | no | 100% | 24 | **add candidate** — talented major CD, ~1min CD with a 14s self-aura. Median 24 uses is roughly on-CD across a M+ key. The 394095 "Kingsbane" buff at 1153 uses is the per-tick stack/proc, not the press. |
| 392401  | Improved Garrote | no | 100% | 23 | skip (talent-passive aura applied during Stealth/Vanish openers; rotational, not a major CD) |
| 1264297 | Cold Blood    | no            | 100%        | 601         | skip (rotational ~30s CD passive proc / finisher buff; sampler's 601 median uses is per-Envenom-empower, not a press-on-CD button) |
| 1265787 | Implacable Strikes | no       | 100%        | 24          | watch (talent proc tracker; could be a Deathstalker hero-talent stack, not a player-pressed CD) |
| 5277    | Evasion           | no        | 100%        | 8           | consider add as defensive (10s personal dodge buff, ~2min CD; signature Rogue defensive used on-CD for tank-busters) |
| 31224   | Cloak of Shadows  | no        | 100%        | 6           | consider add as defensive (5s magic-immunity, ~2min CD; staple Rogue magic-mitigation press) |
| 1966    | Feint             | no        | 100%        | 60          | skip (rotational AoE damage reduction, ~6s CD on energy spend, not a major CD) |
| 360194  | Deathmark         | no        | (n/a)       | (n/a)       | not visible — Deathmark applies a debuff to the *target*, not a self-buff. BuffsTable can't see it; same reason it was dropped 2026-04-16. |

**Notes on splits / alt-builds:**
- **Sin currently has zero tracked CDs.** Deathmark (360194) and Vendetta (79140) were both pulled in 2026-04-16 because they're target debuffs, not self-auras. The sampler confirms Deathmark still doesn't surface in the Rogue's BuffsTable — so the "needs a different detection path" note in `cooldowns.py` still holds.
- **Kingsbane at 100% with 24 median uses** is the cleanest BuffsTable-visible candidate. Aura ID 385627 is the cast-time self-aura on the Rogue (the 14s "I have Kingsbane active" buff that empowers Envenom). The 394095 "Kingsbane" entry at 1153 uses is the per-tick stack on the target, which is a different aura ID. Tracking 385627 with `(385627, "Kingsbane", 24, "offensive")` would give Sin its first BuffsTable-visible major CD. **Caveat:** Kingsbane is talent-gated (Deathstalker tree node). Top-8 cohort is 100% Deathstalker; if Fatebound becomes the meta hero tree for Sin, Kingsbane drops out. Mark as talent-aware-skip eligible.
- **No Indiscriminate Carnage / Crimson Tempest** appears as a press-able major CD aura in the top 30 — they're rotational AoE finishers without a persistent self-buff aura distinct from Slice and Dice / Envenom buffs.
- **No Hero-talent capstone aura is press-able.** Deathstalker's signature is the Deathstalker's Mark debuff on the target; Fatebound's signature is the coin-flip passive. Neither is a "press-on-CD" major CD.
- **Evasion + Cloak of Shadows as defensives:** both at 100% consensus with med-uses near their cooldown counts (Evasion=8 with ~2min CD ~6-8 presses per key; Cloak=6 with ~2min CD same). Adding both would give Sin a defensive pair similar to other specs. They're baseline (not talented), so no skip flag needed.

### Interrupts

- **Spell name (id):** `Kick` (1766)
- **Cast type:** instant (off-GCD melee kick, 15s CD)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable. Kick is a single-school silence on the target; doesn't surface as a self-buff. Needs CastsTable spot-check for verification.
- **Recommended expected count for scoring:** 15 (DPS role default). Kick at 15s CD with melee uptime should comfortably hit 12-18 kicks in a M+ key.
- **No-baseline-kick callout:** N/A — Sin has Kick.

### Dispels

- **In-spec dispel ability:** **none in baseline kit** (no defensive cleanse on allies)
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Rogues universally lack a friendly cleanse. Shroud of Concealment (114018), Shadowstep (36554), and Tricks of the Trade (57934/59628) are utility tools but NOT dispels. Cloak of Shadows removes harmful magic effects from the *Rogue herself* only — that's a personal mitigation, not an ally cleanse, and shouldn't count as utility-dispel coverage. Sin should have an explicit empty-set entry in the new dispel-school registry.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Kidney Shot | 408 | stun | baseline single-target stun (combo-point finisher, 6s max, ~30s CD via Cheap Shot tree) |
| Cheap Shot  | 1833 | stun | baseline opener stun (4s, requires Stealth — limited M+ utility outside Vanish opener) |
| Blind       | 2094 | disorient | baseline 1min ranged disorient, breaks on damage |
| Sap         | 6770 | incapacitate | baseline out-of-combat opener; rarely useful in M+ pull-pacing context |
| Gouge       | 1776 | incapacitate | baseline single-target 4s incap, breaks on damage |
| Smoke Bomb  | 359053 | utility (AoE absorbed-stealth) | talent-gated; group-wide threat-drop / re-stealth field, 3min CD |
| Distract    | 1725 | utility (forced facing) | baseline non-CC tool |

(Sin has the broad Rogue CC kit, with Kidney Shot as the primary M+ stun and Blind as the panic disorient.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(4, "Assassination")`: **add** `(385627, "Kingsbane", 24, "offensive")` to give Sin its first BuffsTable-visible major CD. **Mark as talent-gated** so the talent-aware skip catches non-Deathstalker (Fatebound) builds where Kingsbane isn't pressed. Optionally add `(5277, "Evasion", 8, "defensive")` and `(31224, "Cloak of Shadows", 6, "defensive")` as baseline defensives — both are at 100% consensus with on-CD median uses and would round Sin out from "zero tracked CDs" to a sensible kit-coverage list.
2. **Dispel registry** (new): `(4, "Assassination") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** none. Kick at 15s CD + 15 expected kicks default is fine.
4. Talent-gate flags: Kingsbane is tied to the Deathstalker hero tree. Top-8 cohort is 100% Deathstalker, but Fatebound is the live alt-build path — flag Kingsbane so the talent-aware skip catches Fatebound builds where the aura is absent.
5. Deathmark/Vendetta detection: still blocked on a debuff-on-target detection path. Out of scope for this audit. The empty-list status quo for Sin's cooldown_usage is at least honest (skip-and-zero-out via the talent-aware path) but unsatisfying — Sin currently scores nothing in the cooldown category. Adding Kingsbane fixes that.

### Top-cohort raw output reference

```
No currently-tracked cooldowns for (4, Assassination).

Top 30 most-common buffs across the cohort (spot anything we should add):
   aura_id    pct  med_uses  name
      315496   100%         1   Slice and Dice
      394080   100%       351   Scent of Blood
       59628   100%        14   Tricks of the Trade
      452923   100%       521   Fatebound Coin (Heads)
     1249093   100%       343   Fatebound Coin Flips
      392401   100%        23   Improved Garrote
      385627   100%        24   Kingsbane
     1236616   100%         6   Light's Potential
      457333   100%        14   Death's Arrival
      452917   100%       314   Fatebound Coin (Tails)
     1265787   100%        24   Implacable Strikes
        5277   100%         8   Evasion
     1249810   100%        12   Finish the Job
     1229746   100%        94   Arcanoweave Insight
     1252488   100%        57   Masterful Hunt
        1966   100%        60   Feint
      185311   100%        13   Crimson Vial
     1265389   100%       262   Implacable
      394095   100%      1153   Kingsbane
       11327   100%        13   Vanish
       32645   100%       386   Envenom
     1265391   100%        71   Implacable
       31224   100%         6   Cloak of Shadows
      383781   100%        12   Algeth'ar Puzzle
       36554   100%        14   Shadowstep
     1248971   100%        53   Lucky Coin
        1784   100%        13   Stealth
        2983   100%        12   Sprint
       57934   100%        14   Tricks of the Trade
     1264297   100%       601   Cold Blood
```

> **Note on Fatebound coin flips:** "Fatebound Coin (Heads)" 452923 and "Fatebound Coin (Tails)" 452917 both surfacing at 100% suggests the entire top-8 cohort is running Fatebound — but Kingsbane (Deathstalker) at 100% contradicts that. Most likely both hero-trees surface as auras because the coin flips fire as procs even when the player chose Deathstalker for finishers. Worth a follow-up when there's bandwidth for Rogue hero-tree-aura mapping.

---

## Spec: Outlaw

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 13750   | Adrenaline Rush | yes               | 100%        | 45          | keep |
| 271896  | Blade Rush      | yes               | 100%        | 135         | keep (note: 135 median uses is high — see "alt-build splits" below) |
| 13877   | Blade Flurry    | no                | 100%        | 125         | skip (rotational ~12s CD AoE-cleave-toggle; not a "major" CD, more like Slice and Dice — frequent reapply) |
| 256171  | Loaded Dice     | no                | 100%        | 46          | skip (passive proc tied to Roll the Bones, not a player-pressed CD) |
| 1214909 | Roll the Bones  | no                | 100%        | 45          | watch — could be a candidate. RtB is the rotational ~30s buff cycle. 45 median is roughly the press count per key; but it's rotational not "major", same shape as Slice and Dice for Sin. Hold. |
| 315341  | Between the Eyes | no               | 100%        | 426         | skip (rotational finisher buff; 426 uses is the per-finisher empower, not a press) |
| 5277    | Evasion         | no                | 100%        | 9           | consider add as defensive (signature Rogue defensive ~2min CD) |
| 31224   | Cloak of Shadows | no               | 100%        | 6           | consider add as defensive |
| 195457  | Grappling Hook  | no                | (n/a)       | (n/a)       | not surfaced — utility, not a CD candidate anyway |
| 51690   | Killing Spree   | no                | (n/a)       | (n/a)       | not surfaced in top 30 — would be the major CD if talented, but appears non-meta this season |

**Notes on splits / alt-builds:**
- **Adrenaline Rush + Blade Rush both confirmed at 100%.** No changes needed to the existing tracked list.
- **Blade Rush at 135 median uses is suspicious.** Aura 271896 was set to expected_uptime=5% in `cooldowns.py`, but 135 actual uses against the 5% target would saturate cooldown_usage at 100% — same Pass-3 saturation pattern as Resto Druid Barkskin or Guardian Ironfur. Looking at the aura name, "Blade Rush" might be the tick-aura on the player while charging through enemies (per-target-hit) rather than the press. **Recommend either dropping Blade Rush from the tracked list OR raising expected_uptime to a number that matches the rotational cadence (the press is ~5min CD per Wowhead, but the 135 median strongly suggests this aura ID is per-charge-tick, not per-press).** Either is preferable to silently saturating the score.
- **Killing Spree (51690)** does not appear in the top 30. Outlaw historically had Killing Spree as a major CD; current Midnight S1 builds either dropped the talent or the 4s channel doesn't register a persistent self-aura. Same pattern as Bladestorm for Warrior — channel-with-no-persistent-aura. If Killing Spree returns to meta, expect to revisit.
- **Ghostly Strike (196937)** does not appear — confirms it's no longer talented in current builds.
- **Smokescreen (441640) at 88% med=243** — surfaced in two of three Rogue specs. Likely a hero-talent capstone aura but not a press-on-CD button (hundreds of uses suggests passive proc).
- **No clean alt-build split.** Top cohort is uniform on Adrenaline Rush + Blade Rush; whether they're Trickster or Fatebound hero tree doesn't change the visible major CDs.

### Interrupts

- **Spell name (id):** `Kick` (1766)
- **Cast type:** instant (off-GCD melee kick, 15s CD)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable. Same caveat as Sin.
- **Recommended expected count for scoring:** 15 (DPS role default).
- **No-baseline-kick callout:** N/A — Outlaw has Kick.

### Dispels

- **In-spec dispel ability:** **none in baseline kit**
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Same as Sin. Cloak of Shadows is self-only magic mitigation, not an ally cleanse. Outlaw has Sap-then-Tricks utility but no defensive cleanse.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Kidney Shot | 408 | stun | baseline combo-finisher single-target stun |
| Cheap Shot  | 1833 | stun | opener-only baseline stun |
| Blind       | 2094 | disorient | baseline 1min ranged disorient |
| Sap         | 6770 | incapacitate | out-of-combat opener |
| Gouge       | 1776 | incapacitate | baseline 4s incap; less common in Outlaw rotation |
| Between the Eyes (stun-on-3CP) | 315341 | stun | rotational stun on a Roll the Bones finisher; baseline AoE-style 3-target stun on 4-6CP |
| Smoke Bomb  | 359053 | utility | talent-gated, AoE re-stealth field |
| Distract    | 1725 | utility | baseline non-CC |

(Outlaw's notable Sin-vs-Outlaw difference: Between the Eyes is a finisher-stun with low cost — gives Outlaw arguably better stun uptime than Sin in extended pulls. Not currently a scoring category.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(4, "Outlaw")`: keep Adrenaline Rush as-is. **Investigate Blade Rush.** Either drop it (treating 135 median uses as a per-tick saturation) or recalibrate `expected_uptime_pct` to align with the actual press count. Recommend a one-pass spot-check via `/api/debug/wcl-buffs` to confirm whether 271896 is the press-aura or the tick-aura. If we keep it, raise expected to ~120-140 uses to avoid saturation. If we drop it, the spec is left with Adrenaline Rush only and we should consider adding Evasion + Cloak as defensive companions.
2. **Dispel registry** (new): `(4, "Outlaw") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** none. DPS default 15 expected kicks is fine.
4. Talent-gate flags: Adrenaline Rush is baseline; Blade Rush is technically talented but at 100% consensus is effectively baseline. No skip flag needed.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
     13750      100%        45   Adrenaline Rush  [Adrenaline Rush]
    271896      100%       135   Blade Rush  [Blade Rush]

Top 30 most-common buffs across the cohort (spot anything we should add):
   aura_id    pct  med_uses  name
      271896   100%       135   Blade Rush (tracked)
     1275176   100%      1208   Whirl of Blades
      256171   100%        46   Loaded Dice
     1214909   100%        45   Roll the Bones
     1235110   100%         1   Flask of the Blood Knights
     1214937   100%         8   Jackpot
        1784   100%        12   Stealth
     1214935   100%        13   Triple Threat
     1214933   100%         4   One of a Kind
     1265935   100%        46   Gravedigger
     1259486   100%      1538   Zero In
       13750   100%        45   Adrenaline Rush (tracked)
        1966   100%        59   Feint
     1214934   100%        19   Double Trouble
     1229746   100%       103   Arcanoweave Insight
       11327   100%         5   Vanish
      315341   100%       426   Between the Eyes
      315496   100%         5   Slice and Dice
       59628   100%        12   Tricks of the Trade
       31224   100%         6   Cloak of Shadows
      195627   100%       828   Opportunity
     1265931   100%       310   Palmed Bullets
     1236616   100%         6   Light's Potential
        2983   100%        50   Sprint
       13877   100%       125   Blade Flurry
        5277   100%         9   Evasion
        6673    88%        10   Battle Shout
     1266686    88%        57   Alnsight
     1264426    88%         1   Void-Touched
      441640    88%       243   Smokescreen
```

---

## Spec: Subtlety

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 121471  | Shadow Blades | yes               | 100%        | 18          | keep |
| 185422  | Shadow Dance  | no                | 100%        | 85          | watch — could be a candidate but high uses suggests rotational. SD is a 60s-CD with ~6s window in current builds; 85 median is per-Vanish/Stealth-aura tick. Hold. |
| 1264297 | Cold Blood    | no                | 100%        | 508         | skip (rotational finisher empower; 508 median is per-Eviscerate-empower, not a press) |
| 196911  | Shadow Techniques | no            | 100%        | 2563        | skip (passive proc resource generator; not a CD) |
| 1269163 | Ancient Arts  | no                | 100%        | 1193        | skip (passive Trickster hero-talent stack tracker) |
| 393969  | Danse Macabre | no                | 100%        | 85          | watch — Danse Macabre is the Sub talent that empowers Shadow Dance. 85 median = ~1 per Shadow Dance entry. Track-as-major-CD candidate IF we want to capture the Shadow Dance windows. |
| 441786  | Escalating Blade | no             | 100%        | 324         | skip (Trickster hero-talent stack on the Rogue) |
| 1264521 | Find Weakness | no                | 100%        | 1542        | skip (rotational debuff-tracker / proc) |
| 5277    | Evasion       | no                | 100%        | 6           | consider add as defensive |
| 31224   | Cloak of Shadows | no             | 100%        | 8           | consider add as defensive |
| 207736  | Shadowy Duel  | no                | (n/a)       | (n/a)       | not surfaced — talent that would be a major CD candidate but appears non-meta |
| 277925  | Shuriken Tornado | no             | (n/a)       | (n/a)       | not surfaced — confirms 2026-04-15 Pass-1 removal still holds |
| 212283  | Symbols of Death | no             | (n/a)       | (n/a)       | not surfaced — Symbols was historically a Sub major CD; either non-meta in Midnight S1 or rolled into a different aura ID |

**Notes on splits / alt-builds:**
- **Shadow Blades confirmed at 100% with 18 median uses** — keep. Tracked uptime of 15% maps reasonably to 18 actual uses.
- **Shuriken Tornado (277925) confirmed absent** from the top-30 cohort. The 2026-04-15 Pass-1 removal note still holds: Sub doesn't take it in current builds.
- **Symbols of Death (212283) absent** from the top-30. Historical Sub major CD; current Midnight S1 cohort either dropped it or its self-aura ID has changed. Worth a future check if it comes back to meta.
- **Shadow Dance + Danse Macabre as a paired window.** Both at 100% with med=85. Shadow Dance's actual press is ~60s CD with 2 charges (~7-10 presses per key); 85 median uses = per-tick of the 6s Shadow Dance window (~10 ticks per use × 8 uses). Like Blade Rush for Outlaw, this is per-tick not per-press. Tracking either as a "major CD" with the wrong expected_uptime would saturate the score. NOT recommending add until a per-press aura ID is identified.
- **No clean alt-build split.** The top-8 Sub cohort is uniform on Trickster (Ancient Arts, Escalating Blade visible) over Deathstalker. Shadow Blades is the one universal trackable major.
- **Smokescreen (441640) at 88% med=92** — same hero-talent passive seen in Outlaw cohort.

### Interrupts

- **Spell name (id):** `Kick` (1766)
- **Cast type:** instant (off-GCD melee kick, 15s CD)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable.
- **Recommended expected count for scoring:** 15 (DPS role default).
- **No-baseline-kick callout:** N/A — Sub has Kick.

### Dispels

- **In-spec dispel ability:** **none in baseline kit**
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Same as Sin and Outlaw. Sub has Shroud of Concealment (group stealth-field) which is utility, not a dispel.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Kidney Shot | 408 | stun | baseline combo-finisher stun |
| Cheap Shot  | 1833 | stun | opener stun, also castable inside Shadow Dance / Vanish |
| Blind       | 2094 | disorient | baseline ranged disorient |
| Sap         | 6770 | incapacitate | baseline opener |
| Gouge       | 1776 | incapacitate | baseline; less common in Sub rotation |
| Smoke Bomb  | 359053 | utility | talent-gated; group-wide threat-drop / re-stealth field |
| Shadowy Duel | 207736 | banish-style | talent-gated 1v1 isolation; rarely picked in M+ |
| Distract    | 1725 | utility | baseline |

(Sub uniquely benefits from Shadow Dance / Vanish enabling repeat Cheap Shot stuns; in extended pulls Sub has the highest CC throughput of the three Rogue specs.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(4, "Subtlety")`: keep Shadow Blades as-is. No high-confidence add at the major-CD layer until we identify the per-press aura ID for Shadow Dance or Symbols of Death. Optionally add `(5277, "Evasion", 6, "defensive")` and `(31224, "Cloak of Shadows", 8, "defensive")` as defensive companions, mirroring the Sin recommendation.
2. **Dispel registry** (new): `(4, "Subtlety") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** none. DPS default 15 expected kicks is fine.
4. Talent-gate flags: Shadow Blades is baseline. No skip flag needed for Sub's current single tracked CD.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    121471      100%        18   Shadow Blades  [Shadow Blades]

Top 30 most-common buffs across the cohort (spot anything we should add):
   aura_id    pct  med_uses  name
        1966   100%        65   Feint
      185422   100%        85   Shadow Dance
      196911   100%      2563   Shadow Techniques
     1264297   100%       508   Cold Blood
        2983   100%        17   Sprint
     1269163   100%      1193   Ancient Arts
      386237   100%       103   Fade to Nothing
        8936   100%         9   Regrowth
      441786   100%       324   Escalating Blade
     1264521   100%      1542   Find Weakness
        5277   100%         6   Evasion
     1229746   100%        99   Arcanoweave Insight
     1224098   100%        11   Tricks of the Trade
        1784   100%        13   Stealth
       31224   100%         8   Cloak of Shadows
      428488   100%       492   Exhilarating Execution
      315496   100%         4   Slice and Dice
       11327   100%         7   Vanish
      196980   100%       103   Master of Shadows
       59628   100%        11   Tricks of the Trade
      185311   100%        16   Crimson Vial
      393969   100%        85   Danse Macabre
       36554   100%        12   Shadowstep
      441326   100%       802   Flawless Form
      385727   100%       149   Silent Storm
      112942   100%       271   Shadow Focus
      121471   100%        18   Shadow Blades (tracked)
      441640    88%        92   Smokescreen
     1236616    88%         5   Light's Potential
        1126    88%         6   Mark of the Wild
```

---

## Open questions for review

- **Sin's "no tracked CDs" status quo.** Pre-this-audit, Sin scored zero in cooldown_usage because Deathmark/Vendetta were both unobservable via BuffsTable. The talent-aware skip in `_get_cooldown_usage` masks this for Sin (empty list = nothing to skip = no penalty), but Sin players still get a flat-zero contribution where other DPS specs get a real number. Adding Kingsbane (385627) gives Sin its first real CD signal. Logan: do we want to also pursue the debuff-on-target detection path for Deathmark, or live with Kingsbane-only for the season? The detection-path work is non-trivial (separate API path: events/Debuffs query) but would unlock Vendetta + Deathmark + similar (e.g. Hunter Wailing Arrow, Mage Touch of the Magi).
- **Blade Rush expected_uptime calibration.** The current `expected_uptime_pct=5` for Blade Rush against a sampler median of 135 uses is almost certainly miscalibrated — the math saturates the cooldown_usage category for every Outlaw player. Either:
  1. Drop Blade Rush and leave Outlaw with Adrenaline Rush as the sole tracked CD, OR
  2. Spot-check 271896 to verify it's the press-aura (not per-tick), and if it is the press, raise expected to ~120-140.
- **Defensive-CD slots for melee leather DPS.** Same question as the Warrior audit raised for plate melee: Rogue's Evasion (5277) and Cloak of Shadows (31224) appear at 100% on every spec with on-CD median uses. Adding them as defensives would make Rogue's tracked-CD list more representative of how the spec actually plays, and bring it in line with tank/healer specs that have multiple defensives tracked. Logan: do we want melee-leather DPS to track defensives as part of cooldown_usage?
- **Hero-tree aura mapping.** All three Rogue specs surface a mix of Deathstalker (Light's Potential, Implacable, Implacable Strikes), Fatebound (Coin Heads/Tails, Coin Flips), and Trickster (Ancient Arts, Escalating Blade, Smokescreen, Flawless Form) auras at 100% in their respective cohorts. None of these hero-tree auras read as "press-on-CD major CDs" — they're passive procs, stacks, or rotational stack-trackers. The Brewmaster precedent (alt-build branch tracking) doesn't apply directly here because Rogue hero trees don't gate a separate press-able major CD the way Brewmaster Keg vs Black Ox Brew does. Recording this for completeness; no action needed.
- **Pummel/Kick verification.** All three Rogue specs use Kick (1766). None of the BuffsTable samples surfaced kick aura/debuff data directly. Same caveat as the Warrior audit — recommend a one-time CastsTable spot-check to confirm Kick's spell ID hasn't shifted in Midnight S1.

## Confidence

- **Sample size:** 8 distinct top players per spec across 8 dungeons, all at +19 to +21. Standard sample depth for this audit. All three specs cleared the >=5 fights bar; no retries needed.
- **Confidence on Outlaw tracked-list status quo (Adrenaline Rush + Blade Rush):** very high on Adrenaline Rush; medium on Blade Rush due to the saturated-uses concern flagged above.
- **Confidence on Subtlety tracked-list status quo (Shadow Blades only):** high. Sampler confirms Shadow Blades is the sole press-able BuffsTable-visible major CD for Sub in current builds. Shuriken Tornado removal still holds.
- **Confidence on Sin Kingsbane add:** medium-high. 100% consensus and the median uses (24) line up with the on-CD press count for a ~1min CD over a M+ key. Caveat: tied to Deathstalker hero tree. If Fatebound becomes meta, we'd see Kingsbane drop and the talent-aware skip would zero out Sin again.
- **Confidence on dispel registry empty-set entries (all 3 specs):** very high. Rogue has no defensive cleanse on allies in any spec; this is a static class fact across every WoW expansion.
- **Confidence on interrupt benchmark (Kick, 1766, 15 expected for DPS):** medium. Kick ID is well-known but observed kick counts couldn't be validated from BuffsTable.
- **Lower-confidence items:** the optional defensive-CD adds (Evasion + Cloak of Shadows on every spec). Same observation-driven-not-must-add caveat as the Warrior audit. Logan should weigh in on the broader policy question (are defensives tracked as CDs for melee DPS or not?) before codification.
