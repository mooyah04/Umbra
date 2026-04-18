/**
 * Public changelog: user-visible changes to the site, the scoring
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
    date: "2026-04-18",
    title: "Searching a new character now prompts a 'Parse Warcraft Logs' button",
    category: "improved",
    body:
      "Before: searching a character we'd never seen before silently triggered a WCL fetch in the background while you stared at a spinner. Now: you see an empty-state page with a single button to confirm you actually want us to pull their logs. Rate-limited to once per character per IP per 24 hours so drive-by clicks can't burn through our Warcraft Logs budget. Separate from the 1-hour refresh cooldown on profiles that are already graded.",
  },
  {
    date: "2026-04-18",
    title: "Refresh-on-demand replaces the background refresher",
    category: "improved",
    body:
      "Your profile now has a 'Refresh my profile' button that pulls your recent logs from Warcraft Logs when you click it, capped at once per hour per character. We're retiring the background job that used to re-fetch every graded player on a schedule because it wasn't pulling its weight: most refreshed profiles were never viewed again. Click-to-refresh keeps fresh data one tap away while keeping our WCL call budget focused on people actually checking their grade.",
  },
  {
    date: "2026-04-18",
    title: "\"Stale Logs? Submit a log.\" on any profile",
    category: "new",
    body:
      "Every player page now has a compact 'Submit a log' form, even on already-graded profiles. If a recent run isn't showing up, paste the Warcraft Logs report URL or 16-character code and we'll re-sync your profile directly from that log. Handy when the normal character lookup missed a pull, or when WCL matched the wrong same-named character.",
  },
  {
    date: "2026-04-18",
    title: "Umbra is also on CurseForge",
    category: "new",
    body:
      "CurseForge listing is live. Install Umbra through the CurseForge app and it'll auto-update alongside the rest of your addons. Wago and direct download from wowumbra.gg still work too. Pick whichever manager you already use.",
  },
  {
    date: "2026-04-17",
    title: "Umbra is on Wago",
    category: "new",
    body:
      "Install Umbra from Wago now and it'll auto-update through any supported addon manager (CurseForge app, WowUp, etc.). Direct download from wowumbra.gg still works too. Listing: https://addons.wago.io/addons/umbra-1Mo9iQjb. CurseForge submission is also in review.",
  },
  {
    date: "2026-04-17",
    title: "Umbra grades now appear on LFG tooltips (below Raider.IO)",
    category: "fixed",
    body:
      "Hovering an applicant or a group leader in the Group Finder now shows the Umbra grade and a compact 3-row stat breakdown: primary output (Damage or Healing vs your spec), casts per minute, and cooldown usage. Sits below Raider.IO when it's installed, so both addons coexist instead of fighting for the same spot. Same treatment for the world-hover tooltip. Grab the latest Umbra.zip to pick up the fix.",
  },
  {
    date: "2026-04-17",
    title: "Addon: 'Open full profile on wowumbra.gg' button",
    category: "new",
    body:
      "New button at the bottom of the /umbra panel. Click it and we show a popup with your full profile URL pre-selected. Ctrl-C, alt-tab to your browser, paste. WoW sandboxes browser opens so we can't launch the page directly, but this is one keystroke away.",
  },
  {
    date: "2026-04-17",
    title: "In-game tooltip data refreshes every hour (was 6)",
    category: "improved",
    body:
      "The addon's bundled grade data now gets rebuilt every hour instead of every 6. If your friend just got graded and they're running keys with you, they'll show up in tooltips sooner: worst case 60 min, average 30. Same download URL; just grab a fresh Umbra.zip if you want the latest.",
  },
  {
    date: "2026-04-17",
    title: "Player-driven grading: scoring happens on demand",
    category: "improved",
    body:
      "We no longer auto-grade every character we can find. Instead, new grades appear when someone actually searches a character (or when logs come in from the addon via Warcraft Logs). Already-graded players still get their scores refreshed on the normal schedule. Keeps our data-fetch budget focused on people who want their grade, not on building a giant unused mirror of WCL.",
  },
  {
    date: "2026-04-17",
    title: "D and F grades now have their own colors",
    category: "fixed",
    body:
      "Before, D tier rendered as plain white and F blended into grey body text, so you could miss a bad grade at a glance. D is now amber, F is red. Everything else keeps its WoW-item-quality color (S orange, A purple, B blue, C green).",
  },
  {
    date: "2026-04-17",
    title: "'Grades match reality' homepage section",
    category: "new",
    body:
      "New section with three anonymized real-data examples showing what the stats look like behind an F, a D, and an S grade. No names, just numbers. Shows that the grade is a summary of the log evidence, not a black box.",
  },
  {
    date: "2026-04-17",
    title: "Leaderboard taken down for now",
    category: "improved",
    body:
      "Publicly ranking named players isn't consistent with Umbra's anti-toxicity stance, so we've removed the leaderboard from the nav and the homepage. Your player page still shows your own grade and breakdown. That's what the product is actually for.",
  },
  {
    date: "2026-04-17",
    title: "Timed runs no longer mislabeled as depleted",
    category: "fixed",
    body:
      "Some timed keys (especially +1 / +2 / +3 chest runs) were showing up as depleted on your run list. The underlying field we read had a different meaning than we thought, so we switched to the authoritative one. Existing affected runs get corrected on the next refresh.",
  },
  {
    date: "2026-04-17",
    title: "Death details now show on every run page",
    category: "new",
    body:
      "Risk Analysis panel on the run page now lists each death by the ability that killed you and the pull it happened in. Previously this info was there but hidden behind a fallback message.",
  },
  {
    date: "2026-04-17",
    title: "Avoidable death count fixed",
    category: "fixed",
    body:
      "A small number of avoidable deaths were being undercounted in your risk score due to a mismatch between two Warcraft Logs data sources. Backfilled 125 affected runs and made the live pipeline use the authoritative source.",
  },
  {
    date: "2026-04-17",
    title: "No more silent freezes on cold player lookups",
    category: "improved",
    body:
      "Clicking an uncached player on a run page used to sometimes hang quietly for a minute. Now you see an 'Analyzing this player' state immediately while the backend ingests in the background. You can come back to the page in a moment and it'll be graded.",
  },
  {
    date: "2026-04-17",
    title: "Windrunner Spire name fixed",
    category: "fixed",
    body:
      "One Windrunner Spire encounter ID was missing from the frontend dungeon map, so those runs showed up as 'Mythic+ Dungeon' instead. Now labeled correctly.",
  },
  {
    date: "2026-04-16",
    title: "Pull-by-pull run breakdowns",
    category: "new",
    body:
      "Click any run on a player page → Full Breakdown. See what happened pull by pull: the kicks you hit, the avoidable damage you ate, the pulls you died in, aggregated per ability so the whole dungeon reads in 30 seconds.",
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
      "Horizontal scroll-snap carousel instead of the old grid. Shows more players in less vertical space, feels more alive.",
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
    title: "Scoring Pass 3: correctness + calibration",
    category: "fixed",
    body:
      "Fixed a percentile-handling bug where unranked runs were silently counting as 100 for damage/healing output. Rebalanced CPM benchmarks (they were pegging at 100 for many specs), bumped healer survivability weight, and softened the tank interrupt denominator to be fair to route-dependent pulls.",
  },
  {
    date: "2026-04-16",
    title: "Auto-discovery of EU players",
    category: "new",
    body:
      "We now pull Blizzard's Mythic Keystone leaderboards for EU realms and auto-queue discovered players for ingest. You don't have to search yourself first to show up. Running keys is enough.",
  },
  {
    date: "2026-04-16",
    title: "Addon 0.3.0: two-column /umbra panel",
    category: "new",
    body:
      "Redesigned stats panel: 3D character model + big tier-colored grade on the left, live settings sidebar on the right. Minimap button (shift-drag to reposition). In-panel toggles for tooltip grades, LFG grades, auto /combatlog, panel scale + alpha.",
  },
  {
    date: "2026-04-16",
    title: "All 8 Midnight S1 dungeons have verified data",
    category: "improved",
    body:
      "Avoidable-damage ability lists and critical-kick lists for every dungeon now sourced from a cross-log sampler that reads top speed runs, not hand-curated. Scoring for survivability and utility categories finally reflects real dungeon mechanics.",
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
      "Addon 0.2.1: auto `/combatlog` correctly starts when a key inserts (no more cutting out at the countdown), and the 8-second end-flush guarantees WCL records the keystone time.",
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
