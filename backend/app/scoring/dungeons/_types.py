from dataclasses import dataclass, field


@dataclass(frozen=True)
class DungeonData:
    encounter_id: int
    name: str
    avoidable_abilities: tuple[tuple[int, str], ...] = field(default_factory=tuple)
    # High-priority casts that should be kicked (heals, dangerous AoE, etc).
    # Kicking these counts 1.5× in the utility scoring category.
    critical_interrupts: tuple[tuple[int, str], ...] = field(default_factory=tuple)
    # Dispellable debuffs that enemies in this dungeon can put on the
    # party. Sourced from the dispel sampler (top N logs per dungeon,
    # aggregated by which debuff IDs actually got dispelled).
    #
    # Tri-state semantics — the scoring layer cares about the difference:
    #   - None:  not yet sampled. Scoring uses the legacy flat benchmark
    #            so back-compat is preserved for every dungeon we haven't
    #            populated yet.
    #   - ():    sampled AND confirmed empty. Rare but real — some
    #            dungeons legitimately have no dispellable debuffs. The
    #            scorer excludes the dispel component from utility
    #            scoring for runs in this dungeon so healers don't get
    #            punished for 0 dispels they couldn't have landed.
    #   - tuple: sampled with data. Current consumer uses only the count
    #            (non-empty -> opportunity exists); future tuning can use
    #            the specific IDs to build a per-dungeon benchmark.
    dispellable_debuffs: tuple[tuple[int, str], ...] | None = None
    # Average defensive dispels the party lands per run in top logs
    # (sum of total_dispels / logs_sampled from the dispel sampler,
    # filtered to defensive-only). Healer utility scoring uses this as
    # the per-run denominator instead of a flat 8 — otherwise healers
    # in dispel-poor dungeons (Skyreach ~6/run) can never hit 100 on
    # the dispel component, while healers in dispel-heavy dungeons
    # (Pit of Saron ~65/run) get credit for just a handful.
    # None = use the legacy flat-8 benchmark. 0 or None when
    # dispellable_debuffs is also (), since there's nothing to cast
    # against.
    expected_defensive_dispels_per_run: float | None = None
    # Appearances in M+ seasons, newest first. Informational.
    appearances: tuple[str, ...] = field(default_factory=tuple)
    # Date this writeup was last reviewed against live game data (YYYY-MM-DD).
    last_reviewed: str | None = None
    # True when avoidable_abilities has been sourced from logs, not stubbed.
    verified: bool = False
