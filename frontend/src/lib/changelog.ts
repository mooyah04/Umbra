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
    date: "2026-04-23",
    title: "See exactly which abilities moved your utility score",
    category: "new",
    body:
      "The Utility tile on every run page now lists the specific abilities you cast during that fight with counts. Instead of \"Total interrupts: 8\" you see \"Solar Beam x3, Mass Entanglement x1, Mighty Bash x2, Nature's Cure x4\". You can scan the list and tell immediately whether a low score came from missing dispels, sparse CC, or an untouched kick. Every class's kit is covered: Warrior Pummel, Priest Silence, Evoker Quell, Druid's spec-specific kicks, the full CC toolkit, and every dispel spell across paladin/priest/shaman/druid/mage/monk/hunter/warlock/evoker. First view on a run pulls the data from Warcraft Logs; every view after that is instant.",
  },
  {
    date: "2026-04-23",
    title: "Dedicated overall-dungeon page, plus clearer run pages",
    category: "new",
    body:
      "Clicking a dungeon tile on your profile now takes you to a dedicated page for that dungeon: aggregate grade, category breakdown across every run you have there, and a list of individual runs you can drill into. Before, the run page mixed two things: your specific fight plus the dungeon-wide aggregate in the same breakdown tiles. The run page now shows just this fight's numbers and score. Three pages, three questions: \"how am I graded overall?\" (profile), \"how do I do at this dungeon?\" (dungeon overall), \"how did this one run go?\" (run). Every tile links the right direction so you can jump between them in one click.",
  },
  {
    date: "2026-04-23",
    title: "How your grade breaks down, now explained for your spec",
    category: "improved",
    body:
      "When you open \"How this is measured\" on any breakdown tile, it reads for your actual class and spec instead of the generic role-level blurb. A Resto Druid sees their dispel toolkit (Nature's Cure, Remove Corruption) and CC kit (Hibernate, Mighty Bash, Mass Entanglement) named directly, with a note that Resto Druid doesn't have a baseline interrupt so kicks don't count toward utility. Holy Paladin sees Rebuke called out as their kick. Assassination Rogue sees \"no dispel in your kit, so that weight shifts to CC instead.\" The Cooldown Usage tile names the specific cooldowns we're tracking for your spec (Tranquility, Convoke the Spirits, etc.) with their expected uptime. The Casts Per Minute tile shows the actual thresholds for your spec instead of a universal curve. If you're a hybrid who has runs in multiple specs of the same role (Sin+Outlaw+Sub Rogue, Ret+Prot Paladin, Feral+Balance Druid), the profile breakdown gets a tab strip to flip between \"All\" and each individual spec.",
  },
  {
    date: "2026-04-23",
    title: "Healers in dispel-poor dungeons graded fairly",
    category: "fixed",
    body:
      "Healer utility used a single flat benchmark of \"about 8 dispels per run is a perfect score\" across every dungeon. That punished healers in dungeons where few debuffs exist to dispel (Skyreach averages 6 dispellable events per run) and gave a free pass in dispel-heavy dungeons (Pit of Saron runs 65+). We sampled the top logs of every Midnight Season 1 dungeon for the debuffs real healers actually cleanse off allies, separated them from offensive purges (Tranquilizing Shot, Mage Spellsteal) that were wrongly bucketed with them, and scaled each dungeon's benchmark to its real volume. Skyreach healers who cleanse the few debuffs that are there can now hit 100; Pit of Saron healers who miss half the debuffs score in the 50s. Same execution, consistent grading across the dungeon pool. This fixed a meaningful bias against healers who played dispel-poor dungeons most often.",
  },
  {
    date: "2026-04-23",
    title: "Duplicate runs cleaned from profiles",
    category: "fixed",
    body:
      "Some profiles showed the same run listed twice. Root cause was a race condition during refresh: if two of your party members triggered a refresh on your profile at the same moment, the ingest pipeline could insert the same fight twice before the dedup check caught it. We cleaned up every duplicate row in the database and added a database-level uniqueness constraint so it can't happen again. Flagged by a user who spotted seven duplicates on a single profile (Luminès on Ysondre); same fix applied across every player on the site.",
  },
  {
    date: "2026-04-22",
    title: "Join the Umbra Discord",
    category: "new",
    body:
      "The community server is live at https://discord.gg/Vc6vjJ2N9R. Release announcements, scoring debates, bug reports, and role-based discussion channels (tanks, healers, DPS). New members walk through a short onboarding flow to pick their role and get matched to the right channels automatically. There's also an Umbra bot you can install in your own Discord server. Type `/umbra name-realm region` (e.g. `/umbra elonmunk-tarrenmill eu`) and you'll get an embed with that player's grade, role, spec, and category breakdown. The bot reads directly from our database, so lookups are instant.",
  },
  {
    date: "2026-04-22",
    title: "Addon updated for WoW 12.0.5",
    category: "improved",
    body:
      "The 12.0.5 client patch just went live. We bumped Umbra's compatibility marker to match so the addon loads without the out-of-date warning on updated clients. No behavior changes. Grab the latest from CurseForge, Wago, or the direct download.",
  },
  {
    date: "2026-04-21",
    title: "Augmentation Evokers finally graded fairly",
    category: "fixed",
    body:
      "Aug's whole job is buffing teammates via Ebon Might and Prescience, and Warcraft Logs attributes that amplified damage to the teammates' bars, not to the Aug. Our old scoring only saw the Aug's personal damage (which is lower by design) and graded them accordingly. Now we measure each Aug's group uplift directly (summing teammate damage during their buff windows) and blend it into the damage category. A top Aug adding 80k+ DPS of uplift gets the credit the pure-DPS scorer was missing. We also added an Aug-specific casts-per-minute benchmark and shifted their category weights toward cooldowns and utility, where their real contribution lives. Top Augs should see their grades move up on their next refresh.",
  },
  {
    date: "2026-04-21",
    title: "Rotation tab on every run",
    category: "new",
    body:
      "Click into any run and there's a new Rotation tab next to Pull-by-Pull. It shows the first 15 casts of your opener with timestamps, a cast-frequency table grouped into Rotation / Cooldowns / Utility, and a per-pull timeline of every button you pressed. Every spec has its own classification data so the frequency table actually reads as your rotation, not a dump of every combat-log event. First time you open the tab on a run it fetches from Warcraft Logs and caches it; every view after that is instant. Full coverage: all 39 WoW specs including Midnight's Devourer DH.",
  },
  {
    date: "2026-04-21",
    title: "Dungeon timing write-up removed from methodology page",
    category: "improved",
    body:
      "The methodology page used to carry a dedicated section explaining that timing keys is shown on your profile but doesn't feed into the composite. That was accurate but muddy. It gave timing more airtime than it deserved in the scoring explanation, so we cut the section to keep the page focused on what actually drives the grade. The timed-rate stat still shows on your profile; we just don't over-explain a non-factor.",
  },
  {
    date: "2026-04-20",
    title: "See exactly when you pressed your cooldowns",
    category: "new",
    body:
      "Every pull on the run page now shows which of your major cooldowns fired during it. Offensive cooldowns (burst windows like Avenging Wrath, Combustion, Bestial Wrath) show a red sword. Defensive cooldowns (Shield Block, Ironfur, Touch of Karma, Tranquility) show a blue shield. A pull where you took avoidable damage but also popped a defensive reads as 'Mitigated' in softer blue instead of alarm yellow, because you made the save attempt. New runs capture this automatically; older runs will pick it up the next time you refresh your profile.",
  },
  {
    date: "2026-04-19",
    title: "Disconnect runs no longer drag your grade down",
    category: "fixed",
    body:
      "If a dungeon ended with you disconnected or AFK, that fight used to flow into your grade as a zero-cast, zero-cooldown-use entry and could crater an otherwise clean composite from B into D. We now skip those phantom runs entirely. Cleaned 54 of them out of the database today, so 33 players will see their grade shift on their next refresh.",
  },
  {
    date: "2026-04-19",
    title: "Per-dungeon grades no longer collapse on reintroduced legacy dungeons",
    category: "fixed",
    body:
      "Pit of Saron is back in rotation this season but Warcraft Logs hasn't indexed it for percentile rankings yet. Until today that meant our per-dungeon PoS tile had to treat damage and healing as zero, which pushed players with clean timed +20 runs down to D+ on that dungeon alone. Now we redistribute those categories' weight across the categories we can actually measure, so the per-dungeon grade reflects how the runs played instead of how much of the data Warcraft Logs has filled in.",
  },
  {
    date: "2026-04-19",
    title: "Two grades on every run page",
    category: "new",
    body:
      "Click into any specific run and you'll now see both a grade for that single pull and your overall grade for that dungeon across however many runs you have of it. The single-run grade answers 'how did this one go?' and the aggregate answers 'where does this sit in my history here?'. They're right next to each other at the top of the page.",
  },
  {
    date: "2026-04-19",
    title: "Per-dungeon breakdown on the run page",
    category: "new",
    body:
      "The same category blocks the profile uses for your overall grade now appear on the run page too, scoped to the dungeon you're viewing. See exactly where your B+ Skyreach or your A- Magister's Terrace came from, category by category, without leaving the run.",
  },
  {
    date: "2026-04-19",
    title: "Upload a log straight from the run page",
    category: "new",
    body:
      "The run hero now has a 'Got another log?' slot in the top corner. Paste a Warcraft Logs URL or its 16-character code and we'll re-sync your profile directly from that report. Handy right after you finish a key and want the log in your profile without jumping back to your main page.",
  },
  {
    date: "2026-04-19",
    title: "Fixed profiles flickering between Not Rated and your real grade",
    category: "fixed",
    body:
      "Some characters had duplicate records in our database from different ingest paths using different realm name formats (TwistingNether vs twisting-nether). Profile pages would sometimes load the empty duplicate instead of the populated one, showing 'Not Rated' even on graded players. Consolidated 61 duplicate characters into their real entries, made the lookup deterministic so the populated row wins every time, and closed the path that was creating the stubs so new ones can't appear.",
  },
  {
    date: "2026-04-18",
    title: "Interrupts now name the spell you kicked with",
    category: "improved",
    body:
      "Pull-by-pull lines read like prose: \"Kicked Shadow Bolt with Mind Freeze\" instead of just \"Kicked Shadow Bolt.\" We're now also capturing every interrupt, not only the priority casts. The priority ones keep full color and the trash ones render dimmer so the important kicks still dominate the eye. Scoring is unchanged: grade still only moves on priority interrupts.",
  },
  {
    date: "2026-04-18",
    title: "Pull-by-pull breakdown on every M+ run",
    category: "improved",
    body:
      "Used to be gated behind +8 keys. Lowered the floor to +2 so the per-pull timeline (interrupts, avoidable damage, deaths) shows up on every Mythic+ run you've had. Low-key learners get the same depth as +20 pushers. New ingests populate automatically; older runs backfill next time you hit Refresh.",
  },
  {
    date: "2026-04-18",
    title: "Run breakdown lives on the run page, not a click away",
    category: "improved",
    body:
      "Merged the pull-by-pull breakdown into the main run page. One scroll, everything: hero, stats, per-pull timeline, and the raw WCL link at the bottom. Also bumped the brightness of the verdict pills and event text so it's actually readable on dark.",
  },
  {
    date: "2026-04-18",
    title: "Local download dropped, CurseForge + Wago become the default",
    category: "improved",
    body:
      "Every 'Download Addon' button on the site now points at CurseForge or Wago instead of the raw zip. Managers handle auto-updates, which means fewer 'why does my friend have a newer version' moments. Direct zip is still there if you type the URL in. We just stopped pushing it.",
  },
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
      "Install Umbra from Wago now and it'll auto-update through any supported addon manager (CurseForge app, WowUp, etc.). Direct download from wowumbra.gg still works too. Listing: https://addons.wago.io/addons/umbra. CurseForge submission is also in review.",
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
