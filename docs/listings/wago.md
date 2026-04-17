# Wago listing — Umbra

Wago's addon page format is lighter than CurseForge. Same feature
story, tightened for Wago's readership (which skews more
power-user / WeakAura crowd who like the technical detail).

## Project name

`Umbra`

## Tagline (shown under the name)

`M+ performance grades on tooltips, in the LFG, and in a stats panel.`

## Category

`Addons > Mythic+ Tools` (closest fit)

## Tags

```
mythic-plus, tooltip, lfg, warcraftlogs, performance, grading
```

## License

MIT.

## Description (main body, markdown)

```markdown
Mythic+ performance grading backed by Warcraft Logs. Hover a player
in the world, in the LFG, or anywhere else a unit tooltip fires, and
you see their Umbra grade alongside their role. Full category
breakdown (DPS percentile, utility, survivability, cooldowns, CPM)
lives in the `/umbra` panel and on [wowumbra.gg](https://wowumbra.gg).

## The short version

- **Tooltips everywhere.** World, LFG list, applicant popup. Umbra's
  grade appears inline and renders below Raider.IO when RIO is
  installed. For LFG hovers the layout is compact: primary output,
  casts/min, cooldown usage.
- **`/umbra` stats panel.** 3D model, role + spec + ilvl, big
  color-coded grade, per-category bars.
- **`/combatlog` handled for you.** Flips on at key start, off 8s
  after the key ends. Plays nicely with Archon (the WCL uploader).
- **No network.** The addon doesn't phone home. Grade data is baked
  into a static Lua file rebuilt hourly on the server.
- **Open on web.** Button on the panel that shows your full profile
  URL for a one-step copy-paste to the browser (WoW sandboxes
  browser opens).

## Why another rating addon?

Raider.IO measures completion. Umbra measures performance inside
those completions. They complement each other: when both are
installed the LFG surfaces RIO's data up top, and Umbra extends the
tooltip below it.

Tanks and healers carry full weight in the composite, not the
ceremonial 5% other rating systems hand them. Tanks are scored on
survivability + utility. Healers on throughput + dispels. DPS on
damage percentile + kicks + deaths. Full methodology is public:
[wowumbra.gg/methodology](https://wowumbra.gg/methodology).

## Setup

1. Install the addon normally. Advanced Combat Logging auto-enables
   at first login.
2. Install [Archon](https://www.archon.gg/download?utm_source=header-cta-warcraftlogs),
   the official WCL uploader. Turn on Live Logging. Point it at your
   WoW Logs folder. Hit Go.
3. Run keys. Archon uploads automatically.
4. Look yourself up on [wowumbra.gg](https://wowumbra.gg). That
   triggers the first ingest. After that you're in the database and
   refresh hourly.

Your grade appears in tooltips the next time the addon data rebuilds
(hourly).

## Commands

- `/umbra`: open the panel
- `/umbralog status`: check logging state
- `/umbralog on` / `/umbralog off`: toggle auto combat logging

## Links

- Source: [github.com/mooyah04/Umbra](https://github.com/mooyah04/Umbra)
- Methodology: [wowumbra.gg/methodology](https://wowumbra.gg/methodology)
- Report a bug: [wowumbra.gg/bug-report](https://wowumbra.gg/bug-report)
```
