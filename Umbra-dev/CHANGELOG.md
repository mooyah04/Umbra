# Changelog

All notable changes to the WoWUmbra.gg addon are recorded here.

## [0.3.18] - 2026-04-29

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.17] - 2026-04-28

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.16] - 2026-04-27

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.15] - 2026-04-26

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.14] - 2026-04-25

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.13] - 2026-04-24

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.12] - 2026-04-23

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.11] - 2026-04-23

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.10] - 2026-04-22

### Changed
- Interface version bumped to 120005 for the WoW 12.0.5 client patch.
  Addon now loads without the out-of-date warning on updated clients.

## [0.3.9] - 2026-04-22

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.8] - 2026-04-21

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.7] - 2026-04-20

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.6] - 2026-04-19

### Fixed
- Addon being marked "Incompatible" on current live clients. The
  .toc's Interface was bumped to 120005 in anticipation of a WoW 12.0.5
  client update that hasn't shipped yet; live clients still report
  120001, so the higher value made WoW treat the addon as targeting
  a future version and refuse to load it. Rolled back to 120001.

## [0.3.5] - 2026-04-19

### Changed
- Bundled grade data refreshed (automated daily release).

## [0.3.4] - 2026-04-18

### Changed
- Bundled grade data refreshed against the live database. CurseForge
  and Wago installs now carry the same freshness the direct download
  has had since 0.3.3 shipped (the direct zip rebuilds every hour;
  store installs only pick up data when we cut a new version).
- `X-Curse-Project-ID` now wired into the .toc so the CurseForge app
  matches installed copies to the listing and auto-updates correctly.

## [0.3.3] - 2026-04-17

### Fixed
- World-hover tooltip flickering in 0.3.2. Deferring the `AddLine` by
  one frame meant each of Blizzard's continuous tooltip refreshes would
  clear our deferred line before it could re-fire, causing visible
  appear/disappear cycles. Replaced the per-hover defer with a delayed
  post-call registration at login (1s after load) so we naturally
  register *after* Raider.IO. Post-calls run in registration order, so
  we still append below Raider.IO without any per-frame deferral.
  LFG tooltip keeps its defer (no continuous refresh there).

## [0.3.2] - 2026-04-17

### Fixed
- LFG applicant tooltip was silently not appending the Umbra section.
  Three-layer bug: our OnEnter attach relied on a scroll callback that
  doesn't fire on initial render; `self:GetID()` returns 0 on member
  frames in current retail (we now find the member by identity in
  `parent.Members`); and the LFG API returns just "Name" for same-realm
  applicants while our DB keys are "Name-Realm" (normalized at the call
  site). Same fix applies to the search-result (group leader) tooltip.

### Changed
- LFG hover tooltip now renders *below* Raider.IO (deferred via
  `C_Timer.After(0)`) in a compact 3-row layout: primary output
  (Damage vs spec / Healing vs spec), Casts/min, Cooldown Usage. The
  world-hover tooltip still shows the full breakdown.
- World hover tooltip also deferred so Umbra renders below Raider.IO
  there too. Good-neighbour policy: Umbra is the newcomer and shouldn't
  steal the top-of-tooltip slot.

## [0.3.1] - 2026-04-17

### Added
- "Open full profile on wowumbra.gg" button at the bottom of the `/umbra`
  panel. Click it to get a popup with your profile URL pre-selected.
  Copy, alt-tab to your browser, paste. WoW sandboxes browser opens, so
  this is as frictionless as the client allows.

### Changed
- D and F grade colors now readable. D is amber, F is red. Previously
  both rendered close to white/grey and were easy to miss at a glance.
  Colors now match the site (wowumbra.gg).

### Fixed
- README now points at Archon (the official WCL uploader app) with its
  Live Logging setup recipe, instead of the old generic uploader link.

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
