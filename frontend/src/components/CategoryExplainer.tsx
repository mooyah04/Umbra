import type { CategoryExplanation } from "@/lib/methodology";
import { getStatColor } from "@/lib/grades";

interface DataPoint {
  label: string;
  value: string;
}

interface Props {
  explanation: CategoryExplanation;
  score: number;
  /**
   * Raw numbers that contributed to the score, rendered below the bar.
   * e.g., for Utility: "Total interrupts: 67", "Total dispels: 12"
   */
  dataPoints?: DataPoint[];
  /** Weight (0-1) this category carries in the composite for this role. */
  weight?: number;
}

/**
 * Expanded category card: score bar + what it measures + the raw numbers
 * beneath it + how to improve. Goal is zero surprise — a player should
 * be able to see exactly why their grade is what it is.
 */
export default function CategoryExplainer({
  explanation,
  score,
  dataPoints,
  weight,
}: Props) {
  const color = getStatColor(score);
  const rounded = Math.round(score);

  return (
    <div className="bg-surface-container rounded-xl overflow-hidden">
      {/* Colored top edge tied to the score, so green/yellow/red reads at a glance */}
      <div className="h-0.5" style={{ backgroundColor: color }} />
      <div className="p-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-primary text-2xl">
              {explanation.icon}
            </span>
            <div>
              <h4 className="font-[family-name:var(--font-headline)] font-bold text-lg tracking-tight text-on-surface">
                {explanation.label}
              </h4>
              {weight !== undefined && (
                <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mt-0.5">
                  {(weight * 100).toFixed(0)}% of composite
                </p>
              )}
            </div>
          </div>
          <div className="text-right">
            <span
              className="font-[family-name:var(--font-headline)] font-black text-3xl"
              style={{ color }}
            >
              {rounded}
            </span>
            <span className="text-on-surface-variant text-sm">/100</span>
          </div>
        </div>

        {/* Score bar */}
        <div className="h-1.5 bg-surface-container-highest rounded-full mb-5 overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${Math.min(100, Math.max(0, score))}%`,
              backgroundColor: color,
              boxShadow: `0 0 8px ${color}40`,
            }}
          />
        </div>

        <p className="text-sm text-on-surface-variant leading-relaxed mb-4">
          {explanation.summary}
        </p>

        {dataPoints && dataPoints.length > 0 && (
          <div className="grid grid-cols-2 gap-2 mb-4">
            {dataPoints.map((dp) => (
              <div
                key={dp.label}
                className="bg-surface-container-highest rounded px-3 py-2"
              >
                <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
                  {dp.label}
                </p>
                <p className="font-[family-name:var(--font-body)] font-semibold text-on-surface">
                  {dp.value}
                </p>
              </div>
            ))}
          </div>
        )}

        <details className="group">
          <summary className="cursor-pointer font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary hover:text-primary-container transition-colors list-none flex items-center gap-1">
            <span className="material-symbols-outlined text-sm transition-transform group-open:rotate-90">
              chevron_right
            </span>
            How this is measured
          </summary>
          <div className="mt-3 pl-6 space-y-3 text-sm text-on-surface-variant leading-relaxed">
            <p>{explanation.description}</p>
            <div className="bg-surface-container-low rounded p-3 border-l-2 border-primary/40">
              <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary mb-1">
                How to improve
              </p>
              <p>{explanation.howToImprove}</p>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
}
