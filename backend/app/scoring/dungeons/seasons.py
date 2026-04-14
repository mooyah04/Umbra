"""Season manifests — which dungeons are active in which M+ season.

Dungeon modules live independently under this package. A season entry
just lists which of them are in rotation. When Blizzard announces the
next season, add a new entry and flip ACTIVE_SEASON.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Season:
    key: str
    display_name: str
    wcl_zone_id: int
    dungeon_modules: tuple[str, ...]


MIDNIGHT_S1 = Season(
    key="midnight_s1",
    display_name="Midnight Season 1",
    wcl_zone_id=47,
    dungeon_modules=(
        "magisters_terrace",
        "maisara_caverns",
        "nexus_point_xenas",
        "windrunner_spire",
        "algethar_academy",
        "seat_of_triumvirate",
        "skyreach",
        "pit_of_saron",
    ),
)

SEASONS: dict[str, Season] = {
    MIDNIGHT_S1.key: MIDNIGHT_S1,
}

ACTIVE_SEASON: Season = MIDNIGHT_S1
