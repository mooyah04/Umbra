"""Major cooldown buff IDs per spec for tracking usage via WCL Buffs table.

These are the "big" cooldowns that good players use on cooldown during M+.
A player who never uses their major CDs is leaving significant performance on the table.

IMPORTANT: These are WCL *buff* IDs (the aura that appears on the player),
not cast/spell IDs. WCL's Buffs table reports auras by their buff ID.

Organized by (class_id, spec_name).
Each entry is (buff_id, ability_name, expected_uptime_pct, kind) where kind
is "offensive" (damage/throughput boost) or "defensive" (damage reduction /
mitigation / emergency heal). The run page uses kind to pick the per-pull
icon (red sword vs blue shield); scoring doesn't care about it.
"""

from typing import Literal

CooldownKind = Literal["offensive", "defensive"]

# (class_id, spec_name) -> [(buff_id, name, expected_uptime_pct, kind), ...]
SPEC_MAJOR_COOLDOWNS: dict[tuple[int, str], list[tuple[int, str, float, CooldownKind]]] = {
    # ── DPS Specs ────────────────────────────────────────────────────────

    # Warrior
    (1, "Arms"): [
        # Bladestorm (227847) removed 2026-04-16 (Pass 2): channel with no
        # persistent self-aura — sampler didn't see it at 50% consensus.
        (107574, "Avatar", 15, "offensive"),
        # Demolish (436358) added 2026-04-27 (Batch 1 audit): Colossus
        # hero-talent capstone, 100% consensus on top-cohort Arms players
        # with med=58 uses. Talent-aware skip catches Mountain Thane
        # builds where the aura is absent.
        (436358, "Demolish", 20, "offensive"),
    ],
    (1, "Fury"): [
        (1719, "Recklessness", 15, "offensive"),
        # Avatar (107574) added 2026-04-27 (Batch 1 audit): Pass-2 spec
        # asymmetry — Avatar was tracked for Arms only despite 100%
        # consensus on top Fury too (med=44).
        (107574, "Avatar", 15, "offensive"),
        # Ravager (228920) removed 2026-04-16: summons a weapon (pet-like
        # entity), no self-buff aura on the player. Sampler confirmed 0
        # Fury logs had it in their BuffsTable.
    ],

    # Paladin
    (2, "Retribution"): [
        (31884, "Avenging Wrath", 20, "offensive"),
        # Wake of Ashes (255937) replaced 2026-04-16 (Pass 2): WoA is a
        # hard cast with no self-aura. Execution Sentence is the
        # trackable major CD per sampler (90% consensus, med=24).
        (1234189, "Execution Sentence", 24, "offensive"),
    ],

    # Hunter
    (3, "Beast Mastery"): [
        (19574, "Bestial Wrath", 25, "offensive"),
        # Call of the Wild (359844) removed 2026-04-27 (Batch 3 audit):
        # 0% consensus across 8 top-cohort BMs in extended top-60 scan.
        # Pet-summon pattern that BuffsTable can't see; current Pack
        # Leader meta replaced it with passive procs (Howl/Wyvern's
        # Cry/Hogstrider) that aren't press-on-cooldown CDs.
    ],
    (3, "Marksmanship"): [
        (288613, "Trueshot", 13, "offensive"),  # Pass 2: observed at 70% consensus, med=13 (uptime was 15, now realistic)
    ],
    (3, "Survival"): [
        # Aspect of the Eagle (186289) added 2026-04-27 (Batch 3 audit):
        # 100% consensus across 8 top-cohort Survivals with med=13 uses
        # on a ~90s CD. Baseline (no talent gate). First trackable major
        # for Survival after the Spearhead removal.
        (186289, "Aspect of the Eagle", 13, "offensive"),
        # Spearhead (360966) removed 2026-04-16 (Pass 2): 3s buff too
        # short to register reliably in BuffsTable.
        # Kill Command removed 2026-04-15: rotational spam, not a major
        # cooldown.
    ],

    # Rogue
    (4, "Assassination"): [
        # Kingsbane (385627) added 2026-04-27 (Batch 3 audit): 100%
        # consensus across 8 top-cohort Sins with med=24. First
        # BuffsTable-visible major for Sin since Deathmark/Vendetta
        # were dropped (both debuff-on-target). Talent-gated for the
        # Deathstalker vs Fatebound hero-tree split.
        (385627, "Kingsbane", 24, "offensive"),
        # Deathmark (360194) and Vendetta (79140) removed 2026-04-16:
        # both apply debuffs to enemies, BuffsTable can't see them.
    ],
    (4, "Outlaw"): [
        (13750, "Adrenaline Rush", 20, "offensive"),
        # Blade Rush (271896) removed 2026-04-27 (Batch 3 audit):
        # observed median 135 uses against expected_uptime=5 saturated
        # cooldown_usage to 100% on every Outlaw run — same Pass-3
        # Barkskin pattern. Adrenaline Rush is the legitimate signature
        # CD; tracking Blade Rush as a "major" inflates the score.
    ],
    (4, "Subtlety"): [
        (121471, "Shadow Blades", 15, "offensive"),
        # Shuriken Tornado removed 2026-04-15: talent-gated and rarely
        # picked in current M+ builds — Sub typically takes alternatives.
        # Audit showed 0 uses across observed Sub Rogue logs.
    ],

    # Priest
    (5, "Shadow"): [
        # Void Eruption (228260) replaced 2026-04-16 (Pass 2): VE is the
        # cast, Voidform (194249) is the resulting self-aura — that's
        # what BuffsTable reports. Sampler confirmed at 80% med=12.
        (194249, "Voidform", 12, "offensive"),
        # Power Infusion (10060) added 2026-04-27 (Batch 2 audit):
        # 100% consensus on top Shadow cohort with med=13. Tracked
        # only on Shadow, not the healer specs, to avoid the Twins
        # of the Sun glyph self-vs-received ambiguity.
        (10060, "Power Infusion", 13, "offensive"),
        # Dark Ascension (391109) removed: alternative talent to Void
        # Eruption, not universally taken. Sampler didn't see it at 50%.
    ],

    # Death Knight
    (6, "Frost"): [
        (51271, "Pillar of Frost", 20, "offensive"),
        # Frostwyrm's Fury (279302) removed 2026-04-16 (Pass 2): cast
        # with no self-aura. Sampler didn't see it at 50% consensus.
    ],
    (6, "Unholy"): [
        # Apocalypse (275699) removed 2026-04-15: ~45s-90s CD (too short
        # for "major"), not a self-buff aura. Army of the Dead is the
        # real major CD for Unholy.
        (42650, "Army of the Dead", 3, "offensive"),
    ],

    # Shaman
    (7, "Elemental"): [
        (191634, "Stormkeeper", 10, "offensive"),
        # Ascendance (1219480) added 2026-04-27 (Batch 2 audit): 100%
        # consensus on top Elemental cohort with med=13. Tracked
        # alongside Stormkeeper as the major-CD pair; talent-aware
        # skip handles builds that drop one or the other.
        (1219480, "Ascendance", 13, "offensive"),
        # Fire Elemental (198067) removed 2026-04-16: summons a pet — the
        # elemental has its own buffs, the shaman does not. No self-aura
        # detectable via BuffsTable.
    ],
    (7, "Enhancement"): [
        # Feral Spirit (51533) removed 2026-04-16: summons wolves, no
        # self-buff on the shaman. Same pet-summon pattern as Fire Elemental.
        # Ascendance (114051) replaced 2026-04-16 (Pass 2): Ascendance is
        # the alternate-form DPS CD but didn't show in the sampler;
        # Doom Winds is the current-meta major CD (90% consensus, med=25).
        (466772, "Doom Winds", 25, "offensive"),
    ],

    # Mage
    (8, "Arcane"): [
        (365362, "Arcane Surge", 10, "offensive"),  # was 365350 — sampler showed 365362 as the aura ID (2026-04-16)
        # Touch of the Magi (321507) removed 2026-04-16 (Pass 2): applies
        # a debuff to target, not a buff on the mage — BuffsTable can't
        # see it. Needs a debuff-on-target detection path if we add one.
    ],
    (8, "Fire"): [
        (190319, "Combustion", 12, "offensive"),
    ],
    (8, "Frost"): [
        # Icy Veins (12472) removed 2026-04-16 (Pass 2): sampler didn't
        # see any Icy Veins aura at 50% consensus across 10 top Frost
        # Mages. The aura ID must have changed in Midnight — until we
        # identify the correct one, track Mirror Image instead (90%
        # consensus, med=6). Mirror Image is an 80s-CD DPS decoy that
        # every Frost Mage talents.
        (55342, "Mirror Image", 6, "offensive"),
        # Frozen Orb (84714) removed 2026-04-16: cast-only spell with no
        # self-buff aura — same pattern as Kill Command.
    ],

    # Warlock
    (9, "Affliction"): [
        # Summon Darkglare (205180) re-added 2026-04-27 (Batch 3 audit):
        # the 2026-04-16 removal note was wrong. Sampler shows 100%
        # consensus across 8 top Aff logs with med=13. Cleanest re-add
        # of the audit project — the demon now applies an aura to the
        # warlock as well, which BuffsTable surfaces.
        (205180, "Summon Darkglare", 13, "offensive"),
    ],
    (9, "Demonology"): [
        (265187, "Summon Demonic Tyrant", 10, "offensive"),
        # Grimoire: Felguard (111898) removed 2026-04-15: creates a pet,
        # not a self-buff aura — BuffsTable never surfaces it. Demo has
        # comparatively few self-buff majors; Tyrant is the primary.
    ],
    (9, "Destruction"): [
        (111685, "Summon Infernal", 10, "offensive"),  # was 1122 — 111685 is the player-side aura (2026-04-16)
    ],

    # Monk
    (10, "Windwalker"): [
        # Storm, Earth, and Fire (137639) replaced 2026-04-16 (Pass 2):
        # no SEF aura showed at 50% consensus. Aura ID must have
        # changed in Midnight. Touch of Karma (122470) is a universally-
        # taken WW defensive that sampler confirmed at 90% med=10.
        # Karma is classified defensive: it's an absorb-then-reflect
        # CD. Damage is a side effect; the primary use is survival.
        (122470, "Touch of Karma", 10, "defensive"),
        # Invoke Xuen (123904) removed 2026-04-16: summons a pet.
    ],

    # Druid
    (11, "Balance"): [
        # Celestial Alignment (194223) and Incarnation (102560) are
        # alt-build branches (talent upgrade to CA). Both tracked so
        # the talent-aware skip catches whichever branch the player
        # didn't pick. Top Midnight S1 cohort runs Incarnation; CA
        # rebrought 2026-04-27 (Batch 1 audit) for fairness.
        (102560, "Incarnation: Chosen of Elune", 15, "offensive"),
        (194223, "Celestial Alignment", 15, "offensive"),
        # Fury of Elune (202770) removed 2026-04-27 (Batch 1 audit):
        # observed median uses 62 (per-tick channel aura, not the
        # press) saturated cooldown_usage to 100% on every Balance run
        # — same Pass-3 Barkskin removal pattern. Without a cast-event
        # detection path, FoE can't be tracked honestly.
    ],
    (11, "Feral"): [
        # Berserk (106951) and Incarnation: Avatar of Ashamane (102543)
        # tracked as alt-build branches 2026-04-27 (Batch 1 audit).
        # Top cohort universally runs Berserk; Incarnation is the
        # alt-talent. Talent-aware skip catches whichever the player
        # didn't pick. Pass 2 had dropped Incarnation; re-added so
        # Avatar-of-Ashamane builds aren't punished.
        (106951, "Berserk", 15, "offensive"),
        (102543, "Incarnation: Avatar of Ashamane", 13, "offensive"),
        # Convoke the Spirits (391528) added 2026-04-27 (Batch 1 audit):
        # 100% consensus on top Feral cohort with med=23 uses. Universal
        # in current Midnight S1 builds.
        (391528, "Convoke the Spirits", 23, "offensive"),
    ],

    # Demon Hunter
    (12, "Havoc"): [
        (162264, "Metamorphosis", 15, "offensive"),  # was 191427 — sampler showed 162264 as the DH Meta aura (2026-04-16)
        # Essence Break (258860) removed 2026-04-16 (Pass 2): target
        # debuff, not self-buff — BuffsTable can't see it.
        (370965, "The Hunt", 22, "offensive"),  # Pass 2 add: 80% consensus, med=22 — Havoc's reliable hero-talent CD
    ],
    # Midnight-added 4th DH spec (ranged DPS). Void Metamorphosis is the
    # high-confidence major CD identified from Mvpewe's audit (659 buff
    # uses, name pattern matches Havoc/Vengeance Metamorphosis CDs).
    # Other observed buffs (Soul Fragments, Feast of Souls, Emptiness)
    # read as passive resources/procs and are intentionally excluded.
    (12, "Devourer"): [
        (1225789, "Void Metamorphosis", 15, "offensive"),
    ],

    # Evoker
    (13, "Devastation"): [
        (375087, "Dragonrage", 15, "offensive"),
    ],
    (13, "Augmentation"): [
        (395296, "Ebon Might", 30, "offensive"),  # was 395152 — sampler showed 395296 as the self-aura ID (2026-04-16)
        # Time Skip (404977) removed 2026-04-16 (Pass 2): talented, not
        # universal. Breath of Eons is the Aug signature major CD the
        # sampler confirmed at 100% med=22.
        (442204, "Breath of Eons", 22, "offensive"),
    ],

    # ── Tank Specs (active mitigation cooldowns) ─────────────────────────
    # Every tank CD below is defensive — they're mitigation or emergency
    # damage-reduction auras. The big cooldown story for a tank in M+ is
    # "did you survive the incoming burst", not "did you press a DPS CD".

    (1, "Protection"): [
        (871, "Shield Wall", 3, "defensive"),
        # Last Stand (12975) removed 2026-04-16 (Pass 2): 15s aura too
        # short to register reliably via BuffsTable snapshots — sampler
        # didn't see it at 50% consensus.
        (132404, "Shield Block", 40, "defensive"),  # was 2565 — sampler showed 132404 as the buff-on-warrior (2026-04-16)
        # Avatar (107574) added 2026-04-27 (Batch 1 audit): 100% consensus
        # across top Prot cohort with med=47. Gives Prot its first
        # tracked offensive CD alongside the two defensives, matching how
        # the spec actually plays in M+.
        (107574, "Avatar", 15, "offensive"),
    ],
    (2, "Protection"): [
        (31850, "Ardent Defender", 5, "defensive"),
        (393108, "Guardian of Ancient Kings", 5, "defensive"),  # was 86659 — sampler showed 393108 as the active aura (2026-04-16)
        (132403, "Shield of the Righteous", 40, "defensive"),  # was 53600 — sampler showed 132403 as the stacking buff (2026-04-16)
    ],
    (6, "Blood"): [
        (55233, "Vampiric Blood", 8, "defensive"),
        (81256, "Dancing Rune Weapon", 10, "defensive"),  # was 49028 — sampler showed 81256 as the DK self-buff (2026-04-16)
        # Icebound Fortitude (48792) and Anti-Magic Zone (145629) added
        # 2026-04-27 (Batch 1 audit). Both at 100% consensus on top
        # Blood DKs (med=6 and med=3 respectively). IBF is the major
        # personal defensive (~3min CD); AMZ is the group-wide magic
        # absorb Blood places on M+ pulls.
        (48792, "Icebound Fortitude", 6, "defensive"),
        (145629, "Anti-Magic Zone", 3, "defensive"),
    ],
    (10, "Brewmaster"): [
        (120954, "Fortifying Brew", 8, "defensive"),
        (132578, "Invoke Niuzao, the Black Ox", 12, "defensive"),
        # Exploding Keg and Strength of the Black Ox are mutually-
        # exclusive talent paths in the current Brewmaster tree. Both
        # are tracked here; the talent-aware skip in _get_cooldown_usage
        # excludes the one a given player didn't take, so we don't
        # punish either build. Sampler 2026-04-26: 88% of top BRMs ran
        # Keg, the rest ran Black Ox Brew (e.g. Kirabrew testing the
        # no-Keg defensive build).
        (325153, "Exploding Keg", 5, "defensive"),
        (443113, "Strength of the Black Ox", 13, "defensive"),
    ],
    (11, "Guardian"): [
        (22812, "Barkskin", 10, "defensive"),
        (61336, "Survival Instincts", 5, "defensive"),
        # Incarnation: Guardian of Ursoc (102558) added 2026-04-27 (Batch
        # 1 audit): 100% consensus on top Guardian cohort with med=16.
        # The major active CD that pairs with the two existing personal
        # defensives.
        (102558, "Incarnation: Guardian of Ursoc", 16, "defensive"),
        # Ironfur (192081) removed 2026-04-27 (Batch 1 audit): observed
        # median 654 uses against expected 50 — a rotational rage
        # spender, not a major CD. Saturated cooldown_usage to 100% the
        # same way Resto Druid Barkskin did before its Pass-3 removal.
    ],
    (12, "Vengeance"): [
        (187827, "Metamorphosis", 10, "defensive"),
        # Fiery Brand (204021) removed 2026-04-15: applies a debuff to the
        # target (207771), not a self-buff — won't appear in the player's
        # BuffsTable regardless of use. Metamorphosis is the one reliable
        # self-buff major for Vengeance.
    ],

    # ── Healer Specs (major healing cooldowns) ───────────────────────────
    # Kind tagging for healers is intent-driven: a CD whose primary job is
    # "keep the group alive" (channeled raid heals, damage-reduction
    # totems, rewinds) is defensive; a CD whose primary job is "boost my
    # damage/throughput window" (Wings, Conduit, Convoke, Stasis) is
    # offensive. Most healer CDs technically do both, but the visual
    # signal on the run page follows the primary intent.

    (2, "Holy"): [
        (31884, "Avenging Wrath", 20, "offensive"),
        # Holy Avenger (105809) removed 2026-04-16 (Pass 2): not taken in
        # current-meta M+ Holy Paladin builds — sampler didn't see it at
        # 50% consensus.
    ],
    (5, "Discipline"): [
        # Rapture (47536) replaced 2026-04-16 (Pass 2): Rapture empowers
        # PW:Shield but isn't a persistent self-buff. Ultimate Penitence
        # (421453) is Disc's big hero-talent CD that does show reliably
        # (80% consensus, med=4).
        (421453, "Ultimate Penitence", 4, "offensive"),
        # Evangelism (472433) added 2026-04-27 (Batch 2 audit): 100%
        # consensus on top Disc cohort with med=15. Self-aura central
        # to every Disc rotation, longer than the original 2018-era
        # Evangelism. Highest-signal Priest add in this audit.
        (472433, "Evangelism", 15, "offensive"),
        # PW: Barrier (62618) removed 2026-04-16: ground effect.
    ],
    (5, "Holy"): [
        (200183, "Apotheosis", 10, "offensive"),
        (64843, "Divine Hymn", 3, "defensive"),
    ],
    (7, "Restoration"): [
        # Healing Tide Totem (108280) and original Spirit Link Totem (98008)
        # removed 2026-04-16: both drop totems, not self-buffs. Sampler showed
        # 325174 "Spirit Link Totem" as the actual self-aura on the shaman
        # while the totem is active — using that instead.
        (325174, "Spirit Link Totem", 5, "defensive"),
        # Healing Tide Totem (108280) re-added 2026-04-27 (Batch 2
        # audit): the original Pass-2 removal noted "totems aren't
        # self-auras", but the sampler showed 88% consensus med=9 on
        # this aura ID for top Resto cohort. The totem's group-heal
        # buff is now showing as a self-aura on the caster while the
        # totem is up — same shape as Spirit Link Totem (325174).
        (108280, "Healing Tide Totem", 9, "defensive"),
    ],
    (10, "Mistweaver"): [
        # Yu'lon (322118) removed 2026-04-16: summons a pet serpent.
        # Revival (115310) replaced 2026-04-16 (Pass 2): self-cast heal
        # burst with no aura on caster. Celestial Conduit (443028) is
        # the current-meta MW major CD (90% consensus, med=11).
        (443028, "Celestial Conduit", 11, "offensive"),
        # Strength of the Black Ox (443113) and Unity Within (443592)
        # added 2026-04-27 (Batch 2 audit): the Master of Harmony and
        # Conduit of the Celestials hero-talent capstones, both at
        # 100% consensus on top-cohort MWs. Treat as alt-build pair
        # via talent-aware skip — players take one hero tree or the
        # other.
        (443113, "Strength of the Black Ox", 58, "offensive"),
        (443592, "Unity Within", 12, "offensive"),
    ],
    # Core CDs every Resto Druid has regardless of talent build.
    # Tree of Life, Nature's Swiftness, and Flourish are talent choices
    # (mutually exclusive with other capstones) — scoring a player on
    # talents they didn't pick is unfair. Convoke sits between talent
    # and near-universal, but kept because it's the baseline assumption
    # in current Midnight S1 builds.
    (11, "Restoration"): [
        (740, "Tranquility", 4, "defensive"),                 # baseline, ~3min CD
        (391528, "Convoke the Spirits", 3, "offensive"),      # commonly talented, ~2min CD
        # Barkskin (22812) removed 2026-04-16 (Pass 3): 1-min rotational
        # personal defensive, not a "major" CD. Its inclusion saturated
        # Dobbermon's cooldown_usage at flat 100 across every run — the
        # category lost all signal. Tranq + Convoke are the true signature
        # CDs for a Resto Druid; score on those alone.
        # Innervate removed in Pass 2 (cast on allies, not self).
        # Ironbark removed 2026-04-15 (external, lands on target).
    ],
    (13, "Preservation"): [
        (363534, "Rewind", 3, "defensive"),
        # Emerald Communion (370960) replaced 2026-04-16 (Pass 2): mana-
        # recovery channel, not a performance major. Stasis (370562) is
        # the signature Pres cooldown the sampler caught at 100% med=17.
        (370562, "Stasis", 17, "offensive"),
    ],
}


def get_cooldowns_for_spec(
    class_id: int, spec_name: str
) -> list[tuple[int, str, float, CooldownKind]]:
    """Get the major cooldown abilities for a spec.

    Returns list of (ability_id, ability_name, expected_uptime_pct, kind).
    """
    return SPEC_MAJOR_COOLDOWNS.get((class_id, spec_name), [])
