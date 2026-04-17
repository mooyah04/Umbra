# Umbra — WoW Addon

Mythic+ performance grading on tooltips and the Group Finder.
Backed by combat-log data ingested at https://wowumbra.gg.

## Install

1. Close World of Warcraft completely.
2. Copy this entire **`Umbra/`** folder into:
   ```
   World of Warcraft/_retail_/Interface/AddOns/
   ```
   The final path should look like
   `World of Warcraft/_retail_/Interface/AddOns/Umbra/Umbra.toc`.
3. Install **Archon**, the official Warcraft Logs uploader (free):
   https://www.archon.gg/download?utm_source=header-cta-warcraftlogs
   In Archon, turn on "Live Logging", point it at your WoW log folder,
   hit Go. Your M+ keys upload automatically and feed Umbra's grading.
4. Launch WoW. The addon loads automatically — no configuration.

## What it does

- **Tooltips** — hover any player to see their grade, role, and
  category breakdown (DPS percentile, utility, survivability, etc.).
- **Group Finder** — applicants and group leaders show their grade
  inline so you can vet pugs at a glance.
- **/umbra** — open the personal stats panel for your own character.
- **/umbralog** — auto combat logging for Mythic+ keys.
  - Logs start when a key begins, stop when it ends.
  - `/umbralog status` to check, `/umbralog off` to disable.
  - Doesn't touch logs you started manually for raids.

## Refreshing your data

Grades come from `UmbraData.lua`. Re-download from
https://api.wowumbra.gg/api/export/lua and replace the file in this
folder, then `/reload` in-game.

## Sharing with a friend

Just zip this `Umbra/` folder and send it. They unzip into their
`AddOns/` directory exactly the same way. No accounts, no setup.

## File layout (for the curious)

| File | Role |
|---|---|
| `Umbra.toc` | WoW addon manifest |
| `UmbraData.lua` | Generated grade database — replace to refresh |
| `Core.lua` | Tooltip and Group Finder hooks |
| `UmbraUI.lua` | `/umbra` stats panel |
| `UmbraLogger.lua` | Auto combat-log toggle for M+ |
| `textures/` | Custom UI textures |
