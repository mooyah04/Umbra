from dataclasses import dataclass, field


@dataclass(frozen=True)
class DungeonData:
    encounter_id: int
    name: str
    avoidable_abilities: tuple[tuple[int, str], ...] = field(default_factory=tuple)
    # Appearances in M+ seasons, newest first. Informational.
    appearances: tuple[str, ...] = field(default_factory=tuple)
    # Date this writeup was last reviewed against live game data (YYYY-MM-DD).
    last_reviewed: str | None = None
    # True when avoidable_abilities has been sourced from logs, not stubbed.
    verified: bool = False
