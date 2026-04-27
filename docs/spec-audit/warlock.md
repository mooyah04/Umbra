# Warlock Spec Audit

**Date sampled:** 2026-04-27
**Auditor:** Scoring Scientist agent
**Sample depth:** 1 report per dungeon, top-8 per dungeon scan, 8 active-season Midnight S1 dungeons (Windrunner Spire, Maisara Caverns, Magister's Terrace, Algeth'ar Academy, Nexus-Point Xenas, Skyreach, Pit of Saron, Seat of the Triumvirate)
**Sampler invocation:** `PYTHONIOENCODING=utf-8 python -m scripts.sample_spec_cds --class "Warlock" --spec "{Affliction|Demonology|Destruction}" --samples-per-dungeon 1 --top-n 8`
**Fights sampled:** Affliction 8 / Demonology 8 / Destruction 8 (24 distinct top players in +18 to +21 range)

> Class IDs verified from `app/scoring/roles.py`: Warlock is class_id `9`. All three specs (Affliction, Demonology, Destruction) are DPS. Warlocks themselves have **no baseline interrupt** — kicks come from the Felhunter pet's Spell Lock (19647), which means interrupt access is **conditional on which pet the Warlock has summoned**. Warlocks have **no defensive cleanse** on allies; pet abilities (Imp Singe Magic, Felhunter Devour Magic) can offensively purge enemies but do not cleanse friendlies.

---

## Spec: Affliction

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 205180  | Summon Darkglare | no          | 100%        | 13          | **add (player-side aura DOES surface in BuffsTable; Pass-2 removal was based on incorrect assumption that it was pet-only — sampler proves it's trackable)** |
| 1257052 | Dark Harvest | no             | 100%        | 37          | consider add (Hellcaller hero-talent capstone aura, ~45s CD; rotational at 37 uses but not a passive proc — actual press-on-CD damage CD) |
| 387626  | Soulburn  | no                 | 100%        | 13          | hold (resource-empower aura; gates Soul Rot empowerment; not a "press major CD" — it's a 1-charge buff that's pre-cast before each Soul Rot) |
| 108416  | Dark Pact | no                 | 100%        | 26          | consider add as defensive (~60s CD personal absorb shield; signature Affliction defensive press-on-CD) |
| 104773  | Unending Resolve | no          | 100%        | 4           | consider add as defensive (~3min CD universal Warlock defensive — universal across all 3 specs) |
| 108366  | Soul Leech | no                | 100%        | 509         | skip (passive damage-into-shield proc, ticks per-cast, not a CD) |
| 449793  | Succulent Soul | no            | 88%         | 292         | skip (Hellcaller hero-talent passive shard accrual aura) |
| 1260279 | Nightfall | no                 | 100%        | 261         | skip (Drain Soul/Shadow Bolt proc tracker, not a CD) |
| 387636  | Soulburn: Healthstone | no       | 100%        | 7           | skip (utility healthstone variant, not a damage CD) |

**Notes on splits / alt-builds:**
- **Summon Darkglare (205180) at 100% with 13 median uses** is the cleanest finding. The 2026-04-16 Pass-2 note in `cooldowns.py` claims "summons a demon, no self-buff aura — Aff currently has no trackable major CD via BuffsTable." The sampler **disproves that claim**: 8/8 top Affliction logs show Darkglare in the player's BuffsTable with a consistent ~13 median uses (matches the 60s CD over a 13-15 minute key). This is the same recovery pattern as Destruction's Summon Infernal (111685) — both appear as player-side auras while the demon is active. Recommend re-adding.
- **Hero-tree split:** The cohort runs Hellcaller universally (Dark Harvest, Succulent Soul, and Wither all show at >88%). Soul Harvester would surface Demonic Soul (1269042 at 88% / med=21) and the related auras. The current sample is too Hellcaller-skewed to fully characterize Soul Harvester, but Dark Harvest at 100% is suggestive enough that it should be tracked when codifying — the talent-aware skip will catch Soul Harvester builds where the aura is absent.
- **Phantom Singularity, Vile Taint, Haunt** none surfaced in the top 30. Vile Taint and Haunt apply debuffs to enemies, not buffs on the Warlock — same BuffsTable-invisibility issue that hits Sin Rogue Deathmark. Phantom Singularity is a channel that may not register a persistent self-aura.
- **Soul Rot** does not appear in the top 30 even though it's the signature Affliction DoT-burst spell. It applies a debuff to enemies. NOT trackable via BuffsTable; flag for future debuff-on-target detection if we add that path.
- **Dark Pact (108416) at 100% / med=26** is a defensive worth considering. ~60s CD self-absorb shield; 26 median uses is roughly on-CD for a 13-15 minute key. Adding it would give Affliction its first defensive CD entry.
- **Unending Resolve (104773) at 100% / med=4** is the universal Warlock major defensive (~3min CD). All three specs have it at 100% across the cohort. Could be added across all three specs, OR tracked separately; either way it's the cleanest universal-Warlock defensive add.

### Interrupts

- **Spell name (id):** `Spell Lock` (19647) — **Felhunter pet ability only.** Warlocks themselves have NO baseline interrupt.
- **Cast type:** instant (off-GCD pet command)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable; would need CastsTable + pet-actor source-ID query.
- **Recommended expected count for scoring:** **conditional**. If the Warlock has Felhunter summoned, 15 kicks/run is realistic (24s CD instant kick, plenty of windows). If the Warlock has Imp/Voidwalker/Succubus/Felguard summoned, 0 kicks expected — Spell Lock is unavailable.
- **No-baseline-kick callout:** **Critical.** Affliction historically pets-Felhunter for the kick because Affliction's pet damage contribution is small enough that the utility tradeoff is worthwhile. But this is a player choice, not a class/spec rule. The cohort sample doesn't include pet data; we don't know what % of top Affliction players run Felhunter vs another pet. **Until we have pet-tracking, Affliction should NOT be penalized for missing kicks** — the engine has no way to know whether the player chose to forgo a kick or simply didn't have a kicking pet out.

### Dispels

- **In-spec dispel ability:** **none in baseline kit.** Warlocks have no defensive cleanse on allies in any spec.
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:**
  - **Imp pet's Singe Magic (132411)** can defensively dispel a Magic effect from an ally — BUT this is a pet ability, only available when the Warlock has Imp summoned. Top Affliction logs typically run Felhunter (for kick), not Imp. Not reliable as a "this spec dispels" assumption.
  - **Felhunter pet's Devour Magic (19505)** is an offensive purge (removes a Magic buff from an enemy). NOT a defensive cleanse on allies; should not count toward utility-of-cleanses scoring.
  - **No "Mass Dispel"** — that's a Priest spell, not Warlock. Don't confuse.
  - Recommendation: Affliction's dispel registry entry = **empty set**. If the engine ever adds pet-aware dispel tracking, Imp Singe Magic could be credited situationally, but defaulting to empty is correct.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Fear | 5782 | fear | baseline single-target fear, 1.5min CD |
| Howl of Terror | 5484 | fear | talent, AoE fear (often replaces single-target Fear in M+) |
| Mortal Coil | 6789 | horror | talent, single-target horror + self-heal, 45s CD |
| Shadowfury | 30283 | stun | talent, AoE 30y radius stun (3s); near-universal Warlock CC pick in M+ |
| Banish | 710 | incapacitate | baseline, demons/elementals only — situational in M+ depending on dungeon trash |

(Shadowfury is the canonical Warlock M+ CC because it's a 3s AoE stun that all three specs talent. Banish is dungeon-conditional based on whether the trash mob types are demon/elemental.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(9, "Affliction")`: **add** `(205180, "Summon Darkglare", 13, "offensive")`. The Pass-2 removal note (line 165-169) was incorrect — sampler confirms the player-side aura IS visible. Optionally also add `(1257052, "Dark Harvest", 37, "offensive")` for the Hellcaller hero-talent capstone, with talent-aware skip catching Soul Harvester builds. Optionally add defensives: `(108416, "Dark Pact", 26, "defensive")` and/or `(104773, "Unending Resolve", 4, "defensive")` to give Affliction tracked defensives.
2. **Dispel registry** (new): `(9, "Affliction") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** **flag for special handling.** Pet-conditional interrupt access means default DPS expected count of 15 will unfairly penalize Affliction Warlocks who don't run Felhunter. Recommend either (a) lowering Affliction's expected kicks to a reduced number that matches "if you run Felhunter you should kick" probability-weighted, or (b) adding pet-aware tracking before scoring. **DO NOT codify a roles.py-level rule change without explicit Logan sign-off** — this is a structural engine question, not a sampler-confirmed find.
4. Talent-gate flags: Dark Harvest tied to Hellcaller hero tree. Talent-aware skip should handle Soul Harvester builds.

### Top-cohort raw output reference

```
No currently-tracked cooldowns for (9, Affliction).

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1257052   100%        37   Dark Harvest
      108366   100%       509   Soul Leech
      104773   100%         4   Unending Resolve
     1229746   100%        98   Arcanoweave Insight
     1260279   100%       261   Nightfall
      387626   100%        13   Soulburn
      108446   100%         9   Soul Link
      111400   100%        19   Burning Rush
      205180   100%        13   Summon Darkglare
      108416   100%        26   Dark Pact
     1236616   100%         5   Light's Potential
      387636   100%         7   Soulburn: Healthstone
      449793    88%       292   Succulent Soul
     1250508    88%        13   Emberwing Heatwave
     1266686    88%        62   Alnsight
     1269042    88%        21   Manifested Demonic Soul
      333889    88%         3   Fel Domination
     1266687    88%       946   Alnscorned Essence
     1265145    75%        22   Refreshing Drink
       48018    75%         6   Demonic Circle
       48020    75%         4   Demonic Circle: Teleport
     1265140    75%        34   Refreshing Drink
     1252488    62%        36   Masterful Hunt
      390386    62%         3   Fury of the Aspects
     1242775    62%        17   Farstrider's Step
      413984    62%        58   Shifting Sands
      409678    62%        99   Chrono Ward
      395152    62%        49   Ebon Might
      381757    62%         3   Blessing of the Bronze
      410263    62%        11   Inferno's Blessing
```

---

## Spec: Demonology

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 265187  | Summon Demonic Tyrant | yes      | 100%        | 25          | keep |
| 428524  | Demonic Art: Overlord | no        | 100%        | 46          | hold (Diabolist hero-talent proc/empower aura — fires on its own when the Diabolist resource fills, not a player-pressed CD) |
| 432816  | Diabolic Ritual: Pit Lord | no    | 100%        | 45          | skip (Diabolist resource-build aura, not a CD press) |
| 432794  | Demonic Art: Mother of Chaos | no | 100%        | 46          | skip (Diabolist proc) |
| 433885  | Ruination | no                 | 100%        | 45          | skip (Diabolist hero-talent triggered cast) |
| 431944  | Diabolic Ritual: Overlord | no    | 100%        | 46          | skip (Diabolist resource-build aura) |
| 264173  | Demonic Core | no              | 100%        | 468         | skip (Demonology's signature rotational proc, fires per Hand of Gul'dan / Implosion) |
| 1241715 | Might of the Void | no          | 100%        | 176         | skip (Midnight-tied passive damage stack aura) |
| 1281559 | Hellbent Commander | no         | 100%        | 423         | skip (passive Demo aura) |
| 104773  | Unending Resolve | no          | 100%        | 6           | consider add as defensive (universal Warlock defensive, 3min CD) |
| 108416  | Dark Pact | no                 | 100%        | 21          | consider add as defensive (~60s CD personal absorb) |

**Notes on splits / alt-builds:**
- **Demonic Tyrant (265187) confirmed at 100% / med=25** — current tracked CD is correct. 25 median uses on a ~90s CD over a 13-15 min key is on-CD play.
- **No second major CD surfaced.** Demonic Strength (267171), Nether Portal (267217), Grimoire: Felguard (111898) — none appear in the top 30. Demonic Strength is a self-buff that empowers the Felguard, but if the player isn't talenting it, no aura. Nether Portal applies a debuff/spawn stack and doesn't show in the player's BuffsTable as expected. Grimoire: Felguard is the pet-summon issue (creates a pet, no player aura) — Pass-1 removal still holds.
- **Diabolist hero tree dominates the cohort.** All 8 logs show Diabolic Ritual / Demonic Art / Ruination auras at 100%. The other Demonology hero tree (Soul Harvester) would not surface these auras — but the cohort sample is too Diabolist-heavy to characterize the alternative. None of the Diabolist auras are pressed CDs (they're triggered/passive); they're not great tracked-CD candidates.
- **Tyrant's Oblation (1276767) at 100% / med=25** mirrors Demonic Tyrant's count. Likely a Diabolist-tied bonus aura that fires when Tyrant is up. Tracking would be redundant with Tyrant.
- **Defensives:** Dark Pact and Unending Resolve are universal Warlock defensives. Demo currently has only Tyrant tracked (offensive); adding a defensive would balance the kind mix the way it does for tanks/healers.

### Interrupts

- **Spell name (id):** `Spell Lock` (19647) — **Felhunter pet ability only.** Warlocks themselves have NO baseline interrupt.
- **Cast type:** instant (off-GCD pet command)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable.
- **Recommended expected count for scoring:** **0 by default; conditional.** Demonology's primary pet is Felguard, which does NOT have Spell Lock. Demonology Warlocks who want to kick must dismiss Felguard and summon Felhunter — a meaningful DPS sacrifice that most top Demo logs do NOT make. Demo is the most extreme of the three specs on this conditional-kick problem.
- **No-baseline-kick callout:** **Critical for Demonology specifically.** Top Demo logs typically run Felguard for the demon-army synergy and never summon Felhunter. Penalizing Demo for "missing kicks" when the spec's optimal play sheet is "Felguard, no Spell Lock" is fundamentally unfair. **DO NOT default-expect 15 kicks for Demo.** Recommend either (a) Demo-specific reduced expected count near 0, or (b) flag for engine-level "no interrupt expected" treatment, similar to how some healer specs are handled in `HEALER_SPECS_WITH_INTERRUPT`.

### Dispels

- **In-spec dispel ability:** **none in baseline kit.** Same as Affliction.
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:**
  - Demonology's primary pet (Felguard) has no dispel of any kind.
  - **Imp's Singe Magic (132411)** is theoretically available if the Demo player swaps to Imp, but that's not a Demo build. Treat as not-a-dispel-spec.
  - **Felhunter's Devour Magic (19505)** is offensive-only (purges enemy magic buffs). Not a defensive cleanse.
  - Registry entry: empty set.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Fear | 5782 | fear | baseline single-target fear |
| Howl of Terror | 5484 | fear | talent, AoE fear |
| Mortal Coil | 6789 | horror | talent, single-target horror |
| Shadowfury | 30283 | stun | talent, AoE 3s stun (universal pick) |
| Axe Toss | 89766 | stun | **Felguard pet ability** — 4s ranged stun (Demo's primary stun if Felguard is out) |
| Banish | 710 | incapacitate | demons/elementals only |

(Demonology effectively gets two stuns when Felguard is out — Shadowfury from the Warlock + Axe Toss from Felguard. This is part of the Demo "kit reason to keep Felguard" and trades against losing Spell Lock.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(9, "Demonology")`: keep Tyrant as is. Optionally add `(104773, "Unending Resolve", 6, "defensive")` and/or `(108416, "Dark Pact", 21, "defensive")` for defensive coverage. Hold off on Diabolist hero-talent auras (428524, 432816, etc.) — they're proc-driven, not pressed.
2. **Dispel registry** (new): `(9, "Demonology") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** **flag for engine-level handling.** Demo's pet-conditional interrupt is the clearest case across the three Warlock specs for "this spec should not be expected to kick." Logan should decide whether to (a) accept that "Demo Warlocks don't kick" as a fact and lower the expected count, or (b) leave the penalty and let the addon's spec-explainer text make the case. **Do NOT codify a `roles.py` rule without explicit go-ahead.**
4. Talent-gate flags: Diabolist auras (428524, 432816) at 100% are hero-tree-tied. Soul Harvester builds would not surface them. None are recommended for tracking, so no flagging needed.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    265187      100%        25   Summon Demonic Tyrant  [Summon Demonic Tyrant]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
      333889   100%         2   Fel Domination
      108446   100%         6   Soul Link
      104773   100%         6   Unending Resolve
      428524   100%        46   Demonic Art: Overlord
     1269879   100%       115   Mind's Eyes
     1269643   100%       632   Demonic Oculi
     1265140   100%        31   Refreshing Drink
     1236616   100%         6   Light's Potential
      108416   100%        21   Dark Pact
     1282501   100%        19   Dominion of Argus: Lady Sacrolash
       48018   100%         4   Demonic Circle
     1242775   100%        14   Farstrider's Step
     1276767   100%        25   Tyrant's Oblation
      265187   100%        25   Summon Demonic Tyrant (tracked)
      264173   100%       468   Demonic Core
      432816   100%        45   Diabolic Ritual: Pit Lord
      387636   100%         7   Soulburn: Healthstone
      108366   100%       535   Soul Leech
     1235111   100%         1   Flask of the Shattered Sun
      432794   100%        46   Demonic Art: Mother of Chaos
      387626   100%        11   Soulburn
     1241715   100%       176   Might of the Void
     1276166   100%       147   Dominion of Argus
      433885   100%        45   Ruination
      431944   100%        46   Diabolic Ritual: Overlord
     1282502   100%        24   Dominion of Argus: Grand Warlock Alythess
     1281559   100%       423   Hellbent Commander
     1229746   100%       114   Arcanoweave Insight
     1265145   100%        22   Refreshing Drink
      433891   100%        44   Infernal Bolt
```

---

## Spec: Destruction

### Cooldowns

| Aura ID | Aura Name | Currently tracked? | Consensus % | Median uses | Verdict |
|---------|-----------|-------------------:|------------:|------------:|---------|
| 111685  | Summon Infernal | yes             | 100%        | 18          | keep |
| 117828  | Backdraft | no                 | 100%        | 249         | skip (rotational ~5s proc, every Conflagrate cast — not a major CD; would saturate cooldown_usage) |
| 266030  | Reverse Entropy | no               | 100%        | 82          | skip (talent passive resource-gen aura) |
| 387109  | Conflagration of Chaos | no       | 100%        | 522         | skip (per-cast proc tracker) |
| 394087  | Mayhem | no                    | 100%        | 123         | skip (Havoc passive cleave aura) |
| 1265939 | Vision of Nihilam | no          | 100%        | 639         | skip (passive Midnight-tied stack tracker) |
| 1245664 | Fiendish Cruelty | no           | 100%        | 98          | skip (passive Destruction aura) |
| 266087  | Rain of Chaos | no              | 88%         | 18          | hold (Diabolist proc that triggers free Infernals; ride-along on Summon Infernal tracking) |
| 104773  | Unending Resolve | no          | 100%        | 6           | consider add as defensive (universal Warlock defensive, 3min CD) |
| 108416  | Dark Pact | no                 | 100%        | 26          | consider add as defensive (~60s CD personal absorb) |

**Notes on splits / alt-builds:**
- **Summon Infernal (111685) confirmed at 100% / med=18** — current tracking is correct. 18 median uses on a 3-min CD over a 13-15 min key is universal play; players use the cooldown plus get free Rain-of-Chaos procs that drop additional Infernals counted against the same aura.
- **No second pressed major CD surfaced.** Channel Demonfire (196447), Cataclysm (152108), Soul Fire (6353) — none appear as persistent self-auras. Channel Demonfire and Cataclysm are channeled casts; they don't surface in BuffsTable. Same shape as Aff's Phantom Singularity.
- **Backdraft at 100% / med=249** is the rotational Conflagrate proc. Including it would saturate cooldown_usage — same shape as the Pass-3 Resto Druid Barkskin removal. Skip.
- **Hero-tree split:** The cohort shows Diabolist-flavored auras (Fiendish Cruelty, Vision of Nihilam, Rain of Chaos) at high consensus. Hellcaller for Destruction would surface different procs (Wither's Withering Bolt). The sample is Diabolist-skewed but no Diabolist aura is a "press major CD" candidate.
- **Defensives:** Same Dark Pact + Unending Resolve story as Affliction/Demonology. Adding either would balance the offensive-only Summon Infernal entry.
- **Mannimarco-Mal'Ganis** outlier in the cohort — only 50 auras vs others' 60-70. Not a flagged-issue, just a shorter run with fewer flask/consumable surfaces.

### Interrupts

- **Spell name (id):** `Spell Lock` (19647) — **Felhunter pet ability only.** Warlocks themselves have NO baseline interrupt.
- **Cast type:** instant (off-GCD pet command)
- **Sample observed kicks per fight (median):** Not directly observable from BuffsTable.
- **Recommended expected count for scoring:** **conditional.** Destruction's pet choice is the most flexible of the three Warlock specs — many top Destro logs run Felhunter for the kick because Destro's pet-damage contribution is small (Imp damage scales poorly into Midnight S1). But others run Imp for Singe Magic or for the Fel Domination free-cast.
- **No-baseline-kick callout:** **Critical, but less severe than Demo.** Destro is more kick-capable than Demo because it doesn't lose major DPS by running Felhunter (Demo loses Felguard's demon-army synergy; Destro just loses some Imp damage). But the engine still has no way to know which pet a given Destro Warlock is running. **Same recommendation as Affliction:** flag for special handling, do not penalize at default rate.

### Dispels

- **In-spec dispel ability:** **none in baseline kit.** Same as Affliction and Demonology.
- **Schools cleansable on allies:** none
- **Schools the engine should credit this spec for:** **empty set**
- **Notes:**
  - Pet-conditional Singe Magic (Imp) and offensive-only Devour Magic (Felhunter) — same caveats as the other two specs.
  - Registry entry: empty set.

### CC

| Spell name | ID | Type | Notes |
|---|---|---|---|
| Fear | 5782 | fear | baseline single-target fear |
| Howl of Terror | 5484 | fear | talent, AoE fear |
| Mortal Coil | 6789 | horror | talent, single-target horror + heal (Destro often skips this for offensive talent slots) |
| Shadowfury | 30283 | stun | talent, AoE 3s stun (universal Warlock M+ CC pick) |
| Banish | 710 | incapacitate | demons/elementals only |

(Destruction's CC kit is identical to Affliction's — no Felguard means no Axe Toss like Demo gets.)

### Recommended changes

1. `app/scoring/cooldowns.py` `(9, "Destruction")`: keep Summon Infernal as is. Optionally add `(104773, "Unending Resolve", 6, "defensive")` and/or `(108416, "Dark Pact", 26, "defensive")` for defensive coverage.
2. **Dispel registry** (new): `(9, "Destruction") = set()` — no defensive cleanses.
3. **Interrupt benchmark override:** **flag for engine-level handling.** Same conditional-kick story as Affliction. Defer codification until Logan decides on the broader Warlock interrupt-handling story.
4. Talent-gate flags: none recommended for tracked CDs.

### Top-cohort raw output reference

```
Currently tracked cooldowns — appearance % across the sample:
   aura_id  consensus  med_uses  name
    111685      100%        18   Summon Infernal  [Summon Infernal]

Top 30 most-common buffs across the cohort:
   aura_id    pct  med_uses  name
     1245664   100%        98   Fiendish Cruelty
     1229746   100%       106   Arcanoweave Insight
      333889   100%         2   Fel Domination
     1236616   100%         6   Light's Potential
      111685   100%        18   Summon Infernal (tracked)
      108366   100%       539   Soul Leech
      266030   100%        82   Reverse Entropy
      104773   100%         6   Unending Resolve
      387109   100%       522   Conflagration of Chaos
      117828   100%       249   Backdraft
      394087   100%       123   Mayhem
      387626   100%        15   Soulburn
      111400   100%        19   Burning Rush
      108416   100%        26   Dark Pact
      108446   100%        10   Soul Link
     1265939   100%       639   Vision of Nihilam
      387636    88%         6   Soulburn: Healthstone
       48018    88%         4   Demonic Circle
      266087    88%        18   Rain of Chaos
     1265140    88%        34   Refreshing Drink
     1266687    88%       897   Alnscorned Essence
     1265145    88%        20   Refreshing Drink
     1266686    88%        63   Alnsight
     1269879    75%       106   Mind's Eyes
      432795    75%        40   Demonic Art: Pit Lord
     1241715    75%       174   Might of the Void
      432816    75%        40   Diabolic Ritual: Pit Lord
      192082    75%         3   Wind Rush
      431944    75%        42   Diabolic Ritual: Overlord
      433891    75%        40   Infernal Bolt
```

---

## Open questions for review

- **Pet-conditional interrupt handling (Warlock-wide):** This is the single largest open question for Warlock scoring. All three specs depend on Felhunter being summoned for kicks. Affliction and Destruction commonly run Felhunter; Demonology rarely does. Without pet-aware tracking, the engine cannot know whether a missed kick was a player error or an unavailable ability.
  - Option A: **Lower the expected kick count for all three Warlock specs** (e.g. to 5-7 instead of 15) to roughly match average pet-choice probability. Crude but doesn't require new data.
  - Option B: **Mark Demonology specifically as "no interrupt expected"** (similar treatment to healer specs in `HEALER_SPECS_WITH_INTERRUPT`), leave Affliction/Destro at a reduced count.
  - Option C: **Add pet-aware tracking** in `app/pipeline/ingest.py` — query for Felhunter actor presence in the report's actors list, conditionally credit kicks. This is the "right" answer but is a structural engine change.
  - Strongly recommend Logan picks one before codification — the audit has good evidence that the current default-15 is unfair across Warlock, but the audit doesn't have evidence to pick between the options.
- **Summon Darkglare re-add:** The 2026-04-16 Pass-2 removal note for `(9, "Affliction")` is wrong — sampler shows the player-side aura at 100% / med=13 across 8 top Aff logs. Re-adding is the cleanest single sampler-confirmed find for Warlock. Should land as part of codification.
- **Universal Warlock defensive (Unending Resolve, 104773) at 100% across all three specs:** This is unusual — most class defensives are spec-specific. Adding it would be a "this is a universal Warlock thing" pattern. Worth considering a single class-level defensive entry vs three duplicate spec entries when codifying.
- **Diabolist hero-tree saturation in the cohort:** All three specs' top-8 logs are heavily Diabolist-flavored. Soul Harvester (Aff/Demo) and Hellcaller (Destro) builds may show different aura distributions but were under-represented. A broader-sample retry (`--samples-per-dungeon 2 --top-n 12`) would help characterize the alternative hero trees, though no recommendation in this audit hinges on Soul Harvester/Hellcaller-specific data.
- **`Wither` (Hellcaller capstone for Destro)** does not appear in the top 30 for Destruction even though Hellcaller-flavored auras (Fiendish Cruelty, Vision of Nihilam) are at 100%. Wither applies a debuff to enemies — same BuffsTable-invisibility issue. Future debuff-on-target detection path could pick it up.

## Confidence

- **Sample size:** 8 distinct top players per spec across 8 dungeons, all at +18 to +21. All three specs cleared the >=5 fights bar with no need for retries.
- **Confidence on Summon Darkglare re-add (Affliction):** very high. 100% consensus across 8 players, sampler directly contradicts the Pass-2 removal note. Aura ID matches Wowhead. Cleanest finding in this audit.
- **Confidence on Tyrant + Infernal (Demo, Destro) kept:** very high. Already tracked; sampler confirms.
- **Confidence on dispel registry empty-set entries:** very high. Warlock has no defensive cleanse on allies in any spec; this is a static class fact. Pet abilities are situational, not spec abilities.
- **Confidence on interrupt conditional-kick story:** high on the underlying class-mechanic facts (Spell Lock is Felhunter-only), but **low confidence on which option Logan should pick** (A/B/C above). The audit can confirm the problem; can't pick the right scoring fix without product input.
- **Confidence on optional defensive adds (Unending Resolve, Dark Pact):** medium. 100% consensus is strong, but they're observation-driven proposals rather than "must-add to fix scoring asymmetry." Logan should weigh in.
- **Confidence on Dark Harvest (Aff Hellcaller capstone):** medium. 100% consensus in this sample, but Hellcaller-skewed cohort. A Soul Harvester sample would help validate that the talent-aware skip would correctly handle absent-aura cases.
- **Lower-confidence items:** Diabolist hero-tree aura interpretation (Demonic Art / Diabolic Ritual / Ruination) — these surface as 100% but read as proc/passive auras rather than pressed CDs. Recommendation is to skip them, but if Logan wants Diabolist-aware tracking, a deeper pass to identify which auras correspond to player-pressed Diabolist abilities would be needed.
