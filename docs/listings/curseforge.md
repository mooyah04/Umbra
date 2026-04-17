# CurseForge listing — Umbra

## Project name

`Umbra` (slug `umbra`)

## Category

`Addons > Plugins > Combat > Mythic Plus` (closest fit). Secondary if
allowed: `Tooltips`.

## Short description (card view)

Under CurseForge's ~150 char cap. Use this as the "summary" field.

> Mythic+ performance grades on tooltips and the Group Finder. Backed by Warcraft Logs data. No network calls from the addon.

## License

MIT.

## Tags

```
mythic-plus, m+, tooltip, group-finder, lfg, raider.io-alternative,
performance, grading, warcraftlogs, wcl
```

## Long description (description field, markdown)

```markdown
# Umbra

Mythic+ performance grades on tooltips, in the Group Finder, and in a
personal stats panel. Hover any player in the world and you see what
their Warcraft Logs history says about how they actually play. Not
just their item level or a completion score, but damage percentile,
kicks landed, deaths taken, cooldowns pressed.

## What it does

- **Tooltips.** Hover any player in-game and a line appears on the
  tooltip: "WoWUmbra.gg: B+ Tank" or similar. Color-coded by grade.
- **Group Finder tooltips.** Hover an applicant (or a group leader in
  the search list) and a compact Umbra section appears below
  Raider.IO's. Primary output, casts/min, cooldown usage. Vet at a
  glance. If Raider.IO isn't installed, each applicant also gets an
  inline grade badge next to their name.
- **/umbra panel.** Type `/umbra` in chat to open a stats panel for
  your own character. 3D model, role, spec, item level, the big tier
  color-coded grade, plus per-category breakdown (DPS percentile,
  utility, survivability, cooldowns, CPM).
- **Auto combat logging.** `/combatlog` toggles on at key start,
  off 8s after the key ends. You don't have to remember. Hands the
  log cleanly to Archon (the official WCL uploader) so your runs
  end up on Warcraft Logs automatically.
- **Open on web.** Button on the panel shows your full wowumbra.gg
  profile URL. Copy, paste in your browser, see every run graded
  pull by pull.

## Privacy

**No network calls. The addon never connects to the internet.** Grade
data ships inside the addon itself (a static `UmbraData.lua` file
regenerated every hour on our server). It doesn't phone home, doesn't
track you, doesn't read anything sensitive. Source is on GitHub.

## How it works

1. Install the addon. It auto-enables Advanced Combat Logging on
   first login.
2. Install [Archon](https://www.archon.gg/download?utm_source=header-cta-warcraftlogs),
   the official WCL uploader. Turn on Live Logging and point it at
   your WoW log folder. Your M+ keys upload automatically.
3. Search your character at [wowumbra.gg](https://wowumbra.gg). The
   first lookup triggers ingest (takes a few seconds). After that
   your grade lives in the system and refreshes on the hour.
4. Your grade shows up in Umbra tooltips in-game the next time the
   addon data file rebuilds (hourly).

## Frequently asked

**Does this replace Raider.IO?** No. RIO shows completion + key level,
Umbra shows performance inside those runs. They're complementary.
When both are installed, the Group Finder surfaces RIO on the badge
slot and Umbra extends the tooltip.

**Why's my grade N/R?** You need at least three Mythic+ runs in a
given role on Warcraft Logs for us to publish a grade. Run a few
keys with Archon uploading and your grade appears.

**Does it work for healers and tanks?** Yes, and those roles carry
real weight in the composite, not the token 5% other rating systems
give them. Tanks are scored on survivability and utility; healers
on throughput and dispels.

**I'm on the wrong character on warcraftlogs.com.** Go to your profile
on wowumbra.gg and use the "Claim with a log" flow. Paste a WCL report
link for any run that included your actual character. One click fixes
the mismatch.

## Commands

- `/umbra`: open the stats panel
- `/umbralog status`: check combat log state
- `/umbralog off`: disable auto combat logging
- `/umbralog on`: re-enable it

## Links

- Website and full profile view: [wowumbra.gg](https://wowumbra.gg)
- Methodology (how the grades are computed):
  [wowumbra.gg/methodology](https://wowumbra.gg/methodology)
- Bug reports: [wowumbra.gg/bug-report](https://wowumbra.gg/bug-report)
- Source: [github.com/mooyah04/Umbra](https://github.com/mooyah04/Umbra)

## Changelog

Latest changes in `CHANGELOG.md`. Highlights:

- 0.3.3: LFG applicant tooltip fixed (was silently blank on current
  retail frame structure). World and LFG tooltips now render below
  Raider.IO when it's installed, in a compact 3-row format for LFG.
- 0.3.1: "Open full profile on wowumbra.gg" button on the panel.
  Readable D/F grade colors.
- 0.3.0: Redesigned `/umbra` panel with 3D character model, minimap
  button, in-panel settings.
- 0.2.1: Auto combat-logging toggle; tooltip + LFG grade badges;
  Advanced Combat Logging forced on at login.
```
