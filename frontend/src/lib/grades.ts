/** Grade display helpers — colors match the WoW addon exactly. */

export type Grade =
  | "S+" | "S"
  | "A+" | "A" | "A-"
  | "B+" | "B" | "B-"
  | "C+" | "C" | "C-"
  | "D+" | "D" | "D-"
  | "F" | "F-";

/** Grade colors matching WoW item quality tiers. */
export const GRADE_COLORS: Record<string, string> = {
  "S+": "#ff8000", "S": "#ff8000",           // orange (legendary)
  "A+": "#a335ee", "A": "#a335ee", "A-": "#a335ee", // purple (epic)
  "B+": "#0070dd", "B": "#0070dd", "B-": "#0070dd", // blue (rare)
  "C+": "#1eff00", "C": "#1eff00", "C-": "#1eff00", // green (uncommon)
  "D+": "#ffffff", "D": "#ffffff", "D-": "#ffffff", // white (common)
  "F": "#9d9d9d", "F-": "#9d9d9d",           // grey (poor)
};

/** Tailwind-friendly background classes for grade tiers. */
export const GRADE_BG_CLASSES: Record<string, string> = {
  "S+": "bg-orange-500/20", "S": "bg-orange-500/20",
  "A+": "bg-purple-500/20", "A": "bg-purple-500/20", "A-": "bg-purple-500/20",
  "B+": "bg-blue-500/20", "B": "bg-blue-500/20", "B-": "bg-blue-500/20",
  "C+": "bg-green-500/20", "C": "bg-green-500/20", "C-": "bg-green-500/20",
  "D+": "bg-white/10", "D": "bg-white/10", "D-": "bg-white/10",
  "F": "bg-gray-500/20", "F-": "bg-gray-500/20",
};

export function getGradeColor(grade: string): string {
  return GRADE_COLORS[grade] ?? "#9d9d9d";
}

export function getStatColor(value: number): string {
  if (value >= 80) return "#00e600";  // green
  if (value >= 60) return "#ffdd00";  // yellow
  if (value >= 40) return "#ff8000";  // orange
  return "#ff3333";                    // red
}

/** Friendly category label for display. */
export const CATEGORY_LABELS: Record<string, string> = {
  damage_output: "DPS Performance",
  damage_output_ilvl: "DPS vs iLvl Bracket",
  healing_throughput: "Healing Throughput",
  utility: "Utility (Kicks/Dispels)",
  survivability: "Survivability",
  cooldown_usage: "Cooldown Usage",
  casts_per_minute: "Casts Per Minute",
  timing_modifier: "Key Timing",
};

/** Category labels for specific roles. */
export function getCategoryLabel(key: string, role: string, spec?: string): string {
  if (key === "damage_output" && role === "healer") return "Healer DPS";
  if (key === "damage_output") return `Overall vs ${spec ?? "Spec"}`;
  if (key === "damage_output_ilvl") return `iLvl vs ${spec ?? "Spec"}`;
  if (key === "healing_throughput") return `HPS vs ${spec ?? "Spec"}`;
  if (key === "utility" && role === "healer") return "Utility/Dispels";
  return CATEGORY_LABELS[key] ?? key;
}
