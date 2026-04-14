/** Format milliseconds as "MM:SS" */
export function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/** Format a number with commas: 1234567 -> "1,234,567" */
export function formatNumber(n: number): string {
  return Math.round(n).toLocaleString();
}

/** Capitalize first letter */
export function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** WoW class names by ID */
export const CLASS_NAMES: Record<number, string> = {
  1: "Warrior",
  2: "Paladin",
  3: "Hunter",
  4: "Rogue",
  5: "Priest",
  6: "Death Knight",
  7: "Shaman",
  8: "Mage",
  9: "Warlock",
  10: "Monk",
  11: "Druid",
  12: "Demon Hunter",
  13: "Evoker",
};

/** WoW class colors (hex) */
export const CLASS_COLORS: Record<number, string> = {
  1: "#C69B6D",  // Warrior
  2: "#F48CBA",  // Paladin
  3: "#AAD372",  // Hunter
  4: "#FFF468",  // Rogue
  5: "#FFFFFF",  // Priest
  6: "#C41E3A",  // Death Knight
  7: "#0070DD",  // Shaman
  8: "#3FC7EB",  // Mage
  9: "#8788EE",  // Warlock
  10: "#00FF98", // Monk
  11: "#FF7C0A", // Druid
  12: "#A330C9", // Demon Hunter
  13: "#33937F", // Evoker
};

/** Role display names */
export const ROLE_NAMES: Record<string, string> = {
  tank: "Tank",
  healer: "Healer",
  dps: "DPS",
};
