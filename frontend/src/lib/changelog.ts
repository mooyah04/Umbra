/**
 * Public changelog — user-visible changes to the site, the scoring
 * engine, and the addon. Keep entries concise and written for players,
 * not engineers: say what changed from their perspective, skip internal
 * refactors. Newest first.
 */

export type ChangelogCategory = "new" | "improved" | "fixed";

export interface ChangelogEntry {
  date: string;               // ISO yyyy-mm-dd
  title: string;
  category: ChangelogCategory;
  body: string;
}

export const CHANGELOG: ChangelogEntry[] = [
  {
    date: "2026-04-16",
    title: "Pull-by-pull run breakdowns",
    category: "new",
    body:
      "Click any run on a player page → Full Breakdown. See what happened pull by pull — the kicks you hit, the avoidable damage you ate, the pulls you died in — aggregated per ability so the whole dungeon reads in 30 seconds.",
  },
  {
    date: "2026-04-16",
    title: "Per-dungeon grade breakdown",
    category: "new",
    body:
      "Every player page now shows a separate grade per active-season dungeon, so you can see exactly which dungeons are dragging your composite down.",
  },
  {
    date: "2026-04-16",
    title: "Leaderboard class picker + page-size selector",
    category: "new",
    body:
      "Filter the leaderboard by class with an icon row (click a class icon to narrow to it). Also pick 50 / 100 / 200 rows per page. All filters compose and are URL-shareable.",
  },
  {
    date: "2026-04-16",
    title: "Homepage 'Recently Graded' carousel",
    category: "improved",
    body:
      "Horizontal scroll-snap carousel instead of the old grid — shows more players in less vertical space, feels more alive.",
  },
  {
    date: "2026-04-16",
    title: "Bug report form",
    category: "new",
    body:
      "New /bug-report page. Use it for website bugs or addon bugs (run /umbra bug in-game and paste the output here).",
  },
  {
    date: "2026-04-16",
    title: "Scoring Pass 3 — correctness + calibration",
    category: "fixed",
    body:
      "Fixed a percentile-handling bug where unranked runs were silently counting as 100 for damage/healing output. Rebalanced CPM benchmarks (they were pegging at 100 for many specs), bumped healer survivability weight, and softened the tank interrupt denominator to be fair to route-dependent pulls.",
  },
  {
    date: "2026-04-16",
    title: "Auto-discovery of EU players",
    category: "new",
    body:
      "We now pull Blizzard's Mythic Keystone leaderboards for EU realms and auto-queue discovered players for ingest. You don't have to search yourself first to show up — running keys is enough.",
  },
  {
    date: "2026-04-16",
    title: "Addon 0.3.0 — two-column /umbra panel",
    category: "new",
    body:
      "Redesigned stats panel: 3D character model + big tier-colored grade on the left, live settings sidebar on the right. Minimap button (shift-drag to reposition). In-panel toggles for tooltip grades, LFG grades, auto /combatlog, panel scale + alpha.",
  },
  {
    date: "2026-04-16",
    title: "All 8 Midnight S1 dungeons have verified data",
    category: "improved",
    body:
      "Avoidable-damage ability lists and critical-kick lists for every dungeon now sourced from a cross-log sampler that reads top speed runs — not hand-curated. Scoring for survivability and utility categories finally reflects real dungeon mechanics.",
  },
  {
    date: "2026-04-15",
    title: "Background re-ingest scheduler",
    category: "new",
    body:
      "We now re-score your character on a regular cadence without anyone having to look you up. Your grade stays fresh as you run keys.",
  },
  {
    date: "2026-04-15",
    title: "Addon log auto-toggle fixed",
    category: "fixed",
    body:
      "Addon 0.2.1 — auto `/combatlog` correctly starts when a key inserts (no more cutting out at the countdown), and the 8-second end-flush guarantees WCL records the keystone time.",
  },
  {
    date: "2026-04-15",
    title: "Claim flow for name-colliding realms",
    category: "new",
    body:
      "If WCL's character lookup returns the wrong character (name collision on a busy realm), paste a report URL on your player page and we'll re-ingest from the correct log.",
  },
  {
    date: "2026-04-12",
    title: "Initial release",
    category: "new",
    body:
      "WoWUmbra.gg goes public. S+ to F- Mythic+ grades with receipts, a free addon that shows grades in tooltips and in Group Finder, and a website with full per-category breakdowns.",
  },
];
