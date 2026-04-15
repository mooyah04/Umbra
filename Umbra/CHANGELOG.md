# Changelog

All notable changes to the WoWUmbra.gg addon are recorded here.

## [0.3.0] - 2026-04-16

### Added
- Two-column `/umbra` panel: profile card on the left (3D character model, role icon, spec, class, item level, big tier-colored grade chip), settings sidebar on the right.
- Minimap button — left-click toggles the panel; shift-drag repositions it around the minimap edge. Position persists across sessions.
- In-panel settings: tooltip grades on/off, LFG grades on/off, auto `/combatlog` on/off, panel scale/alpha sliders, reset-to-defaults.
- "Casts per minute" stat row — was scored on the backend but never displayed before.
- Role-aware stat ordering: healers see HPS-vs-spec first, DPS/Tank lead with DPS-vs-spec.

### Changed
- Stat-bar color palette aligned with wowumbra.gg branding (lilac / cyan / amber / coral instead of stoplight).
- Stat-row labels rewritten so only spec-ranked WCL percentiles carry "vs <spec>" suffixes — utility/survivability/cooldowns are absolute benchmarks and now read that way.

### Fixed
- `Core.lua: UpdateResults is not a function` crash on clients where Blizzard renamed/removed the LFG ApplicationViewer method (ScrollBox rework). Hook is now guarded.
- 100+ "Secret values are only allowed during untainted execution" errors per minute on cursor hover. Tooltip unit-resolution now uses the sanctioned `TooltipUtil.GetDisplayedUnit` and wraps `UnitIsPlayer` / `UnitFullName` in `pcall`.
- Combat log being cut off the moment an M+ key started. The CHALLENGE_MODE_RESET event fires both on manual mid-run resets and on the instance pre-reset that happens at key insertion — we no longer listen to it. Only CHALLENGE_MODE_COMPLETED triggers the (delayed) shutdown.
- PLAYER_LEAVING_WORLD no longer disables the log if a challenge-mode key is still active (covers internal world-reset transitions during the countdown).

## [0.2.1] - 2026-04-14

### Added
- Auto-toggle `/combatlog` on M+ key start; auto-disable 8s after key end (8s flush gives WCL the CHALLENGE_MODE_END line it needs to record `kill=true` and `keystoneTime`).
- `/umbralog` slash command for status + opt-out.
- Forces Advanced Combat Logging on at login (WCL can't parse logs without it).
- Tooltip grade displayed on hovered players in the world.
- LFG applicant grade badges + tooltips in the Group Finder. Yields the badge spot to Raider.IO when it's installed.
- `/umbra` slash command opens the stats panel.

## [0.1.0] - 2026-04-12

- Initial release.
