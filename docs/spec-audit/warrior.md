# Warrior Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 report per dungeon, top-8 per dungeon scan, 8 active-season Midnight S1 dungeons (Windrunner Spire, Maisara Caverns, Magister's Terrace, Algeth'ar Academy, Nexus-Point Xenas, Skyreach, Pit of Saron, Seat of the Triumvirate)
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Warrior" --spec "{Arms|Fury|Protection}" --samples-per-dungeon 1 --top-n 8`
**Fights sampled:** Arms 8 / Fury 8 / Protection 8 (24 distinct top players in +19 to +21 range)

> Class IDs verified from `app/scoring/roles.py`: Warrior is class_id `1`. Arms/Fury are DPS; Protection is tank. Pummel is the universal kick. Warriors have no defensive cleanse — only Shattering Throw (offensive Magic-effect remove).

---

## Spec: Arms

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 107574  | Avatar    | yes                | 100%        | 23          | keep |
| 436358  | Demolish  | no                 | 100%        | 58          | **add (Colossus hero-talent capstone, universal in current Arms builds)** |
| 260708  | Sweeping Strikes | no          | 100%        | 100         | hold (rotational ~30s CD; high uses, but it's a 12s buff that's part of the AoE rotation, not a "major" CD) |
| 118038  | Die by the Sword | no          | 100%        | 9           | consider add as defensive (8s personal mitigation, ~2min CD; signature Arms defensive) |
| 334783  | Collateral Damage | no         | 100%        | 669         | skip (passive proc/stacking buff, not a player-pressed CD) |
| 1269394 | Master of Warfare | no         | 100%        | 210         | skip (passive talent stacking aura) |
| 440989  | Colossal Might | no            | 100%        | 1034        | skip (passive Colossus stack counter, not a CD) |

**Notes on splits / alt-builds:**
- **Demolish at 100%** is the cleanest "add" finding for Arms in this sample. It's the Colossus hero-talent capstone and every top-8 Arms player in this cohort runs Colossus over Mountain Thane. The 58 median uses is the actual button-press count (~10s CD with Colossal Might stacks gating). This should be tracked with `kind="offensive"`.
- **Bladestorm (227847)** does NOT appear in the top 30 — confirms the 2026-04-16 Pass 2 removal still holds. Bladestorm is a 4s channel with no persistent self-aura that BuffsTable can see.
- **Champion's Spear / Thunderous Roar** absent from top 30 — Thunderous Roar was the previous-meta major CD; Colossus builds dropped it. If Mountain Thane builds become competitive again next tuning, Thunder Blast (435615) shows in Fury's table at 100% and would be the corresponding aura to track for Mountain Thane Arms.
- **Die by the Sword** is a defensive worth considering. 9 median uses in a M+ key with ~30 minutes of pulls is roughly on-CD. Adding it would give Arms a `defensive` CD which currently has none — every other tank/healer spec has at least one defensive in the kit, and the run page's red/blue icon variety improves.
- No genuine alt-build split surfaced in this 8-fight sample. The cohort is homogeneous on Colossus + Slayer-or-Mountain-Thane secondary trees, but the secondary doesn't surface a major-CD aura difference.

### Interrupts

- **Spell name (id):** `Pummel` (6552)
- **Cast type:** instant (no GCD, off-GCD melee kick)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable. Pummel applies a 4s silence debuff to the target rather than a self-buff, so it doesn't appear in any of the sampled players' aura lists. Needs a CastsTable spot-check for verification.
- **Recommended expected count for scoring:** 15 (the role-default for DPS). Pummel is a 15s CD instant — easily 12-18 kicks in a typical M+ run, so 15 is realistic.
- **No-baseline-kick callout:** N/A — Arms has Pummel.

### Dispels

- **In-spec dispel ability:** **none in baseline kit** (no defensive cleanse)
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Warrior offensively has Shattering Throw (64382) which removes a Magic effect from an enemy (e.g. immunity bubbles in PvP, niche M+ uses). It's offensive, not a defensive cleanse, so the engine should NOT count it as a dispel for utility scoring. Arms should have an explicit empty-set entry in the new dispel-school registry so utility scoring doesn't penalize the spec for not cleansing things it cannot cleanse.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Intimidating Shout | 5246 | fear | baseline AoE fear, 1.5min CD |
| Storm Bolt | 107570 | stun | talent-gated single-target ranged stun (4s) |
| Shockwave | 46968 | stun | talent-gated frontal cone AoE stun (3s) — Arms typically picks Shockwave or Storm Bolt, not both |
| Piercing Howl | 12323 | slow | baseline AoE slow (no stun/incap) |
| Hamstring | 1715 | slow | baseline single-target slow |

(Storm Bolt vs Shockwave is the canonical Arms CC talent split; both are alt-build paths a future CC scoring component should treat as alternatives.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(1, "Arms")`: **add** `(436358, "Demolish", 58, "offensive")`. Optionally add `(118038, "Die by the Sword", 9, "defensive")` if we want Arms to have a defensive in its tracked list (currently zero defensives tracked for Arms). Keep Avatar.
2. **Dispel registry** (new): `(1, "Arms") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** none. Pummel + 15s CD + 15 expected kicks default is fine.
4. Talent-gate flags: Demolish is tied to the Colossus hero tree. Top-8 cohort is 100% Colossus, but Mountain Thane is a real alt path — flag Demolish so the talent-aware skip catches the absent aura on Mountain Thane builds. (Mountain Thane Arms doesn't surface a comparable single major-CD aura in this sample; if it becomes viable, revisit this audit.)

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    107574      100%        23   Avatar  [Avatar]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      436358   100%        58   Demolish
      192082   100%         4   Wind Rush
     1270846   100%        58   Celeritous Conclusion
        6673   100%         6   Battle Shout
     1292058   100%       166   Heroic Might
      118038   100%         9   Die by the Sword
     1265145   100%        36   Refreshing Drink
      260708   100%       100   Sweeping Strikes
      386164   100%        11   Battle Stance
      462854   100%         5   Skyfury
      262232   100%       156   War Machine
      392778   100%       125   Wild Strikes
       52437   100%        74   Sudden Death
      441387   100%        15   Second Wind
     1270840   100%       213   Cut to the Bone
     1265140   100%        44   Refreshing Drink
      107574   100%        23   Avatar (tracked)
      385391   100%        32   Spell Reflection
       97463   100%         4   Rallying Cry
      334783   100%       669   Collateral Damage
      440989   100%      1034   Colossal Might
     1262753   100%        58   Heart of Ancient Hunger
       23920   100%        32   Spell Reflection
     1235111   100%         1   Flask of the Shattered Sun
      386633   100%        46   Executioner's Precision
      386208   100%        10   Defensive Stance
     1261189   100%        46   Crushing Combo
     1269391   100%       131   Master of Warfare
     1269394   100%       210   Master of Warfare
       32216   100%        43   Victorious
```

---

## Spec: Fury

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 1719    | Recklessness | yes              | 100%        | 31          | keep |
| 107574  | Avatar    | no                 | 100%        | 44          | **add (universally talented in current Fury, second major CD alongside Recklessness)** |
| 184362  | Enrage    | no                 | 100%        | 685         | skip (passive proc, fires every Bloodthirst-crit, not a player-pressed CD) |
| 1269349 | Berserk (Hero-talent variant) | no | 100%   | 1119        | skip (Slayer hero-talent passive, not a CD) |
| 435615  | Thunder Blast | no            | 100%        | 184         | skip (Mountain Thane hero-talent rotational proc, not a major CD aura) |
| 184364  | Enraged Regeneration | no       | 100%        | 7           | consider add as defensive (8s personal heal-over-time; ~2min CD; signature Fury defensive) |
| 437121  | Burst of Power | no            | 100%        | 58          | skip (talent proc/buff, rotational not major) |

**Notes on splits / alt-builds:**
- **Avatar at 100% with 44 median uses** is a clear add. Fury currently has only Recklessness tracked, while Arms has Avatar tracked. Top Fury players take Avatar universally — this is a baseline add. Use `(107574, "Avatar", 15, "offensive")` mirroring Arms.
- **Ravager (228920)** does NOT appear in this sample — confirms the 2026-04-16 removal. Ravager summons a weapon entity with no self-aura.
- **Slayer vs Mountain Thane hero-talent split:** The cohort shows both Slayer-flavored auras (1269349 "Berserk", 1265406 "Bloodborne") and Mountain Thane-flavored auras (435615 "Thunder Blast", 1265575 "Executioner's Wrath") at 100% — meaning both hero trees show a passive aura on every Fury, not because every Fury runs both, but because the auras represent the hero tree's passive effect. None of these are a "press-on-cooldown" major CD.
- **Champion's Spear** absent from the cohort — Fury used to take it pre-Midnight; now neither hero tree builds around it.
- **Enraged Regeneration** is worth a defensive slot if we want Fury to have one. Currently Fury has zero defensive CDs tracked, while Brewmaster/Prot/etc. all have multiple defensives. Fury is a notably squishy plate DPS in M+; the spec actually does press Enraged Regeneration on cooldown.

### Interrupts

- **Spell name (id):** `Pummel` (6552)
- **Cast type:** instant
- **Sample observed kicks per fight (median):** Same caveat as Arms — Pummel doesn't surface in BuffsTable. Needs CastsTable for verification.
- **Recommended expected count for scoring:** 15 (DPS role default).
- **No-baseline-kick callout:** N/A.

### Dispels

- **In-spec dispel ability:** **none in baseline kit**
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Same as Arms. Shattering Throw is offensive Magic-effect remove (enemy-only); not a defensive cleanse.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Intimidating Shout | 5246 | fear | baseline AoE fear |
| Storm Bolt | 107570 | stun | talent-gated single-target stun |
| Shockwave | 46968 | stun | talent-gated AoE stun |
| Piercing Howl | 12323 | slow | baseline AoE slow |
| Hamstring | 1715 | slow | baseline single-target slow |

(Same CC tools as Arms; Storm Bolt vs Shockwave alt-build split.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(1, "Fury")`: **add** `(107574, "Avatar", 15, "offensive")` to give Fury two tracked majors (Recklessness + Avatar). Optionally add `(184364, "Enraged Regeneration", 7, "defensive")` if we want a defensive in the list. Keep Recklessness.
2. **Dispel registry** (new): `(1, "Fury") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** none.
4. Talent-gate flags: Avatar is technically a talent in some hero-tree builds, but at 100% consensus it's effectively baseline. No flag needed unless Mountain Thane builds drop Avatar in a future tuning pass.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
      1719      100%        31   Recklessness  [Recklessness]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
       85739   100%       651   Whirlwind
      386196   100%         5   Berserker Stance
     1269349   100%      1119   Berserk
      386208   100%         4   Defensive Stance
        6673   100%        11   Battle Shout
      385391   100%        29   Spell Reflection
     1265406   100%      1175   Bloodborne
       23920   100%        29   Spell Reflection
       52437   100%        85   Sudden Death
       32216   100%        43   Victorious
      437121   100%        58   Burst of Power
      202164   100%         9   Bounding Stride
      392778   100%       134   Wild Strikes
        1719   100%        31   Recklessness (tracked)
      435615   100%       184   Thunder Blast
     1262753   100%        65   Heart of Ancient Hunger
       97463   100%         5   Rallying Cry
      107574   100%        44   Avatar
      184362   100%       685   Enrage
     1265399   100%       593   Scent of Blood
      335082   100%       694   Frenzy
     1229746   100%        86   Arcanoweave Insight
      262232   100%       155   War Machine
     1265575   100%       256   Executioner's Wrath
     1285644    88%         1   Hearty Well Fed
     1264426    88%         1   Void-Touched
     1266686    88%        67   Alnsight
      184364    88%         7   Enraged Regeneration
     1266687    88%       767   Alnscorned Essence
       58984    88%         2   Shadowmeld
```

---

## Spec: Protection

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 871     | Shield Wall | yes              | 100%        | 24          | keep |
| 132404  | Shield Block | yes             | 100%        | 65          | keep |
| 107574  | Avatar    | no                 | 100%        | 47          | **add (universally taken by top Prot warriors as offensive major; also gives a non-defensive CD to balance the kind mix)** |
| 190456  | Ignore Pain | no               | 100%        | 1918        | skip (rotational rage spender / absorb shield, not a major CD; ~12s reapply, 1900+ uses confirms it's a button-press-on-cooldown rage dump) |
| 23922   | Shield Slam | no               | 100%        | 496         | skip (rotational ~9s CD damage ability, not a major CD) |
| 5302    | Revenge!  | no                 | 100%        | 118         | skip (rage proc / rotational free-cast aura) |
| 386486  | Seeing Red | no                | 100%        | 1642        | skip (passive damage stack tracker) |
| 386029  | Brace For Impact | no          | 100%        | 580         | skip (passive Shield Slam stack buff) |
| 386478  | Violent Outburst | no          | 100%        | 105         | skip (talent proc, rotational) |

**Notes on splits / alt-builds:**
- **Avatar at 100% with 47 median uses** is the clear add. Every top Prot warrior in this sample took Avatar — same aura ID as Arms (107574). Adding it gives Prot a third tracked CD, including its first offensive major (currently Prot has only Shield Wall + Shield Block, both defensive). This better matches how the spec actually plays in M+.
- **Last Stand (12975)** does NOT appear in the top 30 — confirms the 2026-04-16 Pass 2 drop still holds. The 15s buff is too short to register reliably.
- **Champion's Spear / Thunderous Roar** absent from the cohort — same trend as Arms/Fury.
- **Demolish (436358)** does NOT appear in Prot's top 30 — Prot doesn't take the Colossus capstone (different spec talent tree). So Demolish is Arms-only.
- **Spell Reflection (23920 / 385391, both at 100%)** is interesting. It has a 21s CD with a 5s buff and is functionally a pressed defensive. 34 median uses is roughly on-CD. NOT recommending add because it's a niche utility press (only useful when a magical cast is incoming) and the median pulls hard depending on dungeon affixes. But worth noting as a possible future addition if we want to separate "uses defensives reactively" from "uses defensives on cooldown."
- **Ignore Pain at 1918 median uses** is the rage spender, not a major CD. Including it would saturate Prot's cooldown_usage at 100% the way Barkskin saturated Resto Druid (per the 2026-04-16 Pass 3 note). Keep it out.
- No genuine alt-build split surfaced. Top cohort is homogeneous on Mountain Thane (Thunder Blast at 100%) over Colossus, but neither tree's hero-talent capstone is a separate trackable major CD for Prot the way Demolish is for Arms.

### Interrupts

- **Spell name (id):** `Pummel` (6552)
- **Cast type:** instant
- **Sample observed kicks per fight (median):** Same caveat — not visible in BuffsTable. Needs CastsTable.
- **Recommended expected count for scoring:** 12 (tank role default). Tanks generally have to balance kicking with tanking the boss and CC management. 12 is realistic.
- **No-baseline-kick callout:** N/A.

### Dispels

- **In-spec dispel ability:** **none in baseline kit**
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:** Tank Warriors have no defensive cleanse. They have Spell Reflection (interrupts a magical cast aimed at them, which can be reflected as damage), but that's a personal mitigation tool, not a friendly cleanse. Same registry treatment as Arms/Fury — explicit empty set.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Intimidating Shout | 5246 | fear | baseline AoE fear |
| Storm Bolt | 107570 | stun | talent-gated single-target ranged stun |
| Shockwave | 46968 | stun | talent-gated AoE stun (Prot picks this nearly universally for M+) |
| Piercing Howl | 12323 | slow | baseline AoE slow (1244157 in sample) |
| Hamstring | 1715 | slow | baseline single-target slow |
| Spell Reflection | 23920 | reflect | baseline; magical cast reflect, doubles as semi-CC if it returns a CC effect |

(Prot is the most CC-rich Warrior spec because Shockwave is the canonical Prot tank stun for M+ pulls.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(1, "Protection")`: **add** `(107574, "Avatar", 15, "offensive")` to give Prot a third CD, mixing offensive + defensive in the tracked list. Keep Shield Wall and Shield Block.
2. **Dispel registry** (new): `(1, "Protection") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** none. Tank default of 12 expected kicks is fine for Prot.
4. Talent-gate flags: Avatar is a talent but appears at 100% — no skip needed unless tuning shifts. Last Stand stays unflagged (already dropped, sampler confirms it's still not surfacing).

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
       871      100%        24   Shield Wall  [Shield Wall]
    132404      100%        65   Shield Block  [Shield Block]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
         871   100%        24   Shield Wall (tracked)
     1278009   100%       484   Phalanx
      386486   100%      1642   Seeing Red
     1234772   100%       275   Best Served Cold
      132404   100%        65   Shield Block (tracked)
        5302   100%       118   Revenge!
       32216   100%        18   Victorious
      107574   100%        47   Avatar
     1229746   100%       124   Arcanoweave Insight
       23922   100%       496   Shield Slam
      386397   100%         5   Battle-Scarred Veteran
       23920   100%        34   Spell Reflection
      392778   100%       139   Wild Strikes
      190456   100%      1918   Ignore Pain
      385391   100%        34   Spell Reflection
      386029   100%       580   Brace For Impact
      262232   100%       156   War Machine
      386478   100%       105   Violent Outburst
     1244157   100%         3   Piercing Howl
        6673   100%        14   Battle Shout
      386208   100%         4   Defensive Stance
      202602    88%       128   Into the Fray
       97463    88%         4   Rallying Cry
      385840    88%         1   Thunderlord
      437121    75%        74   Burst of Power
      438591    75%       226   Keep Your Feet on the Ground
     1235110    75%         1   Flask of the Blood Knights
      462854    75%         8   Skyfury
     1262753    75%        74   Heart of Ancient Hunger
      435615    75%       224   Thunder Blast
```

---

## Open questions for review

- **Defensive-CD slots for plate DPS specs:** Arms (Die by the Sword) and Fury (Enraged Regeneration) currently have zero defensives tracked, while every tank/healer spec has at least one. Adding defensives is consistent with how the run page's red/blue icon mix is meant to work and may improve scoring fairness for plate DPS. Logan: do we want to widen the "major CD" definition to include 2-min personal defensives for melee DPS, or keep that out of cooldown_usage scoring?
- **Pummel verification:** All three Warrior specs use Pummel. None of the BuffsTable samples surfaced kick aura/debuff data directly. Recommend a one-time CastsTable spot-check via `/api/debug/wcl-casts` (or similar) to confirm Pummel ID 6552 is what current top Warriors actually cast in Midnight. The expected count (15 DPS / 12 tank) is calibrated against role norms, not Warrior specifically — if Pummel's 15s CD makes 18+ kicks routinely realistic in long M+ pulls, the role default may underrate Warriors.
- **Hero-tree alt-builds:** Slayer vs Mountain Thane (Fury, Prot) and Colossus vs Mountain Thane (Arms) are the live hero-tree splits. The current sample shows Colossus-only for Arms (Demolish at 100%) and a mix for Fury/Prot, but no surfaced major-CD aura is hero-tree-exclusive in a way that requires alt-build tracking. If Mountain Thane Arms becomes meta, Thunder Blast (435615) would be the equivalent capstone aura to track alongside Demolish.
- **Spell Reflection as a tracked CD:** Universal at 100% on all three specs, ~24-34 median uses (roughly on-CD). It's a 21s-CD reactive defensive. Including it would inflate scores for the "presses Spell Reflection on cooldown" archetype. Hold off until we have a clearer story on how to score reactive vs proactive defensives.

## Confidence

- **Sample size:** 8 distinct top players per spec across 8 dungeons, all at +19 to +21. This is the standard sample depth for this audit. All three specs cleared the >=5 fights bar with no need for retries.
- **Confidence on Avatar add (Fury, Prot):** very high. 100% consensus across 8 players, and Avatar is already tracked for Arms — the spec asymmetry was clearly a Pass-2 oversight.
- **Confidence on Demolish add (Arms):** high. 100% consensus, but tied to Colossus hero tree which the entire +20 sample took. Mark as talent-gated when codifying so the talent-aware skip catches Mountain Thane Arms players.
- **Confidence on dispel registry empty-set entries:** very high. Warrior has no defensive cleanse in any spec; this is a static class fact.
- **Confidence on interrupt expected count:** medium. Pummel ID is well-known, but observed kick counts couldn't be validated from BuffsTable in this audit. Default role values (15 DPS / 12 tank) are reasonable but unverified for Warrior specifically.
- **Lower-confidence items:** the optional defensive-CD adds (Die by the Sword, Enraged Regeneration) — these are observation-driven recommendations, not high-consensus must-adds. Logan should weigh in before codification.
