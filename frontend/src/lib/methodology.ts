/**
 * Centralized scoring methodology copy. Keeping this in one place so
 * the About page, the player breakdown, and any future tooltips all
 * speak the same language about what we measure and why.
 */

export interface CategoryExplanation {
  key: string;
  label: string;
  /** One-line summary for tight UI. */
  summary: string;
  /** Full paragraph for the explainer/methodology page. */
  description: string;
  /** What the player can do to improve it. */
  howToImprove: string;
  /** Roles this category applies to. */
  roles: Array<"dps" | "healer" | "tank">;
  icon: string; // Material Symbols name
}

export const CATEGORY_EXPLANATIONS: CategoryExplanation[] = [
  {
    key: "damage_output",
    label: "Damage Output",
    summary:
      "Where your damage ranks against other players of your spec this season.",
    description:
      "We pull Warcraft Logs' percentile rank for your spec in the current M+ zone. A 90 means you out-dps'd 90% of players playing your exact spec. Key levels and gear are factored into WCL's own normalization, so this is a fair spec-vs-spec comparison.",
    howToImprove:
      "Review top-parse logs for your spec to see their opener, cooldown alignment, and target priority. Most sub-50 percentiles are fixable by tightening rotation, not by pushing gear.",
    roles: ["dps", "healer", "tank"],
    icon: "swords",
  },
  {
    key: "healing_throughput",
    label: "Healing Throughput",
    summary: "How much you healed relative to other healers of your spec.",
    description:
      "WCL percentile for HPS against same-spec healers in this M+ zone. A high score here reflects actually healing — throughput — separate from your utility and damage.",
    howToImprove:
      "Low throughput on high keys usually means either the tank is taking unnecessary damage (addressable via CC/kicks) or you're not using your group heals on CD.",
    roles: ["healer"],
    icon: "healing",
  },
  {
    key: "utility",
    label: "Utility",
    summary: "Interrupts + dispels + crowd control per run.",
    description:
      "We count every interrupt, dispel, and CC cast across your tracked runs. Classes without a dispel aren't penalized for not having one. Critical-priority interrupts (boss heals, mass CC) count 1.5× when we have the data. Healers are weighted toward dispels; DPS and tanks toward interrupts and CC.",
    howToImprove:
      "The single biggest single-player improvement in M+ is kicking the right casts. Install a kick-announcer, learn which casts matter per dungeon, and rotate with your team.",
    roles: ["dps", "healer", "tank"],
    icon: "bolt",
  },
  {
    key: "survivability",
    label: "Survivability",
    summary: "Deaths, avoidable damage taken, and healing burden.",
    description:
      "Three signals: how often you died, how much of your damage taken came from ability IDs we know are avoidable, and how much healing you consumed relative to the group. Tanks aren't penalized for healing received (they're supposed to tank). Deaths caused by avoidable abilities cost extra.",
    howToImprove:
      "Audit your Details damage-taken log after a wipe — if one ability hit you for >15% of your total intake, look up the mechanic on Wowhead and you'll usually find the out.",
    roles: ["dps", "healer", "tank"],
    icon: "shield",
  },
  {
    key: "cooldown_usage",
    label: "Cooldown Usage",
    summary: "Did you press your major cooldowns on schedule?",
    description:
      "For each of your spec's major CDs we compute expected uses based on fight duration, then compare against actual casts. Talent-optional CDs are excluded — we don't penalize you for not taking a specific talent. Missing only one CD drops your score; hoarding defensives or offensives is a common sub-grade cause.",
    howToImprove:
      "Bind your majors prominently. If you're sitting a 2-minute CD through a 30-minute key, that's 10+ minutes of wasted throughput.",
    roles: ["dps", "healer", "tank"],
    icon: "timer",
  },
  {
    key: "casts_per_minute",
    label: "Casts Per Minute",
    summary: "Activity level — are you pressing buttons?",
    description:
      "Total casts divided by fight duration, scored against role and spec benchmarks. We use spec-specific thresholds — a 25 CPM Marksmanship Hunter is doing great, a 25 CPM Fury Warrior is struggling. Low CPM usually means rotation gaps, bad positioning, or AFK on a mechanic.",
    howToImprove:
      "Check your Details timeline for long gaps between casts. Often these map to movement, mechanics, or a dead target (precast before the pull ends).",
    roles: ["dps", "healer", "tank"],
    icon: "speed",
  },
  {
    key: "timing_modifier",
    label: "Key Timing",
    summary: "A ±8 bonus based on whether your keys actually timed.",
    description:
      "M+ is a team activity. We apply a ±8-point modifier to the composite based on your weighted timing rate — higher keys count more. Timing everything adds 8; 50% timed is neutral; 0% timed subtracts 8. It's not per-player, it's the group's result, and that's intentional: you can't be a great M+ player while your runs deplete.",
    howToImprove:
      "Route quality and group cohesion matter as much as personal play. Practice dungeons in lower keys, study route creators like MDT/Quazii, and communicate pulls.",
    roles: ["dps", "healer", "tank"],
    icon: "schedule",
  },
];

export function getCategoryExplanation(
  key: string,
): CategoryExplanation | undefined {
  return CATEGORY_EXPLANATIONS.find((c) => c.key === key);
}

export function getCategoriesForRole(
  role: string,
): CategoryExplanation[] {
  const r = role as "dps" | "healer" | "tank";
  return CATEGORY_EXPLANATIONS.filter((c) => c.roles.includes(r));
}

/** Role weight breakdown — must match backend ROLE_WEIGHTS. Kept in sync manually. */
export const ROLE_WEIGHT_PROFILES: Record<
  "dps" | "healer" | "tank",
  Array<{ key: string; weight: number }>
> = {
  dps: [
    { key: "damage_output", weight: 0.3 },
    { key: "utility", weight: 0.2 },
    { key: "survivability", weight: 0.25 },
    { key: "cooldown_usage", weight: 0.15 },
    { key: "casts_per_minute", weight: 0.1 },
  ],
  healer: [
    { key: "healing_throughput", weight: 0.2 },
    { key: "damage_output", weight: 0.2 },
    { key: "utility", weight: 0.2 },
    { key: "survivability", weight: 0.2 },
    { key: "cooldown_usage", weight: 0.1 },
    { key: "casts_per_minute", weight: 0.1 },
  ],
  tank: [
    { key: "damage_output", weight: 0.25 },
    { key: "utility", weight: 0.15 },
    { key: "survivability", weight: 0.25 },
    { key: "cooldown_usage", weight: 0.2 },
    { key: "casts_per_minute", weight: 0.15 },
  ],
};

/**
 * The four principles we lead with on the About page.
 */
export const DESIGN_PRINCIPLES = [
  {
    title: "Role-aware weighting",
    icon: "tune",
    body:
      "Tanks, healers, and DPS are scored on different categories at different weights. A tank isn't dragged down by DPS; a healer isn't penalized for not kicking a spell only Resto Shaman and Holy Paladin can interrupt.",
  },
  {
    title: "Spec-aware benchmarks",
    icon: "insights",
    body:
      "Fury Warrior and Marksmanship Hunter have very different natural cast rates. We use spec-specific benchmarks instead of one universal curve, so a clean MM Hunter isn't flagged as lazy and a slacking Fury isn't given a free pass.",
  },
  {
    title: "Talent-honest cooldown tracking",
    icon: "rule",
    body:
      "We only score CDs every player of the spec has access to. If you didn't pick a talent-gated ability (Tree of Life, Flourish, etc.), we don't score you on something you couldn't press.",
  },
  {
    title: "Evidence-backed categories",
    icon: "verified",
    body:
      "Every score is tied to events in the combat log: specific cast IDs, specific damage breakdowns, specific deaths. When you disagree with a grade, you can inspect the raw per-run numbers and see exactly what drove it.",
  },
];

/**
 * How Umbra differs from the existing addon/site landscape.
 * Used on the About page.
 */
export const DIFFERENTIATORS = [
  {
    title: "Receipts, not rankings",
    body:
      "Gear score shows what you brought. IO shows what you completed. Umbra shows how you actually played: the kicks you hit, the avoidable damage you ate, the cooldowns you held. Every grade drills down to the specific events that drove it.",
  },
  {
    title: "Fair across roles",
    body:
      "Most rating systems quietly weight toward DPS output. Our tank and healer grades reflect tanking and healing — survivability and utility carry real weight, not the ceremonial 5% other tools give them.",
  },
  {
    title: "Per-dungeon + pull-by-pull",
    body:
      "You don't just get an overall letter. You get a grade per dungeon (see where you actually struggle) and a pull-by-pull breakdown per run (scan the whole dungeon in 30 seconds). Nobody else does this.",
  },
  {
    title: "Built for M+, not raids",
    body:
      "Raid parsing tools are mature. M+ evaluation isn't. We start from M+-native assumptions: key-level weighting in every category, timed rate as context not penalty, per-dungeon avoidable-ability lists sourced from live top logs.",
  },
];
