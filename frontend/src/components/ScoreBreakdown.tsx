import CategoryBar from "./CategoryBar";
import { getCategoryLabel } from "@/lib/grades";

interface ScoreBreakdownProps {
  categoryScores: Record<string, number>;
  role: string;
  spec?: string;
}

/** Categories to display per role (in order). */
const ROLE_CATEGORIES: Record<string, string[]> = {
  dps: ["damage_output", "damage_output_ilvl", "utility", "survivability", "cooldown_usage", "casts_per_minute"],
  healer: ["healing_throughput", "damage_output", "damage_output_ilvl", "utility", "survivability", "cooldown_usage"],
  tank: ["damage_output", "damage_output_ilvl", "utility", "survivability", "cooldown_usage", "casts_per_minute"],
};

export default function ScoreBreakdown({ categoryScores, role, spec }: ScoreBreakdownProps) {
  const categories = ROLE_CATEGORIES[role] ?? ROLE_CATEGORIES.dps;

  return (
    <div className="space-y-3">
      {categories.map((key) => {
        const value = categoryScores[key];
        if (value === undefined || value === null) return null;
        return (
          <CategoryBar
            key={key}
            label={getCategoryLabel(key, role, spec)}
            value={value}
          />
        );
      })}
      {categoryScores.timing_modifier !== undefined && (
        <div className="text-sm text-gray-400 pt-1">
          Key Timing Modifier:{" "}
          <span className={categoryScores.timing_modifier >= 0 ? "text-green-400" : "text-red-400"}>
            {categoryScores.timing_modifier > 0 ? "+" : ""}
            {categoryScores.timing_modifier.toFixed(1)}
          </span>
        </div>
      )}
    </div>
  );
}
