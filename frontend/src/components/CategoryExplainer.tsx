import type { CategoryExplanation } from "@/lib/methodology";
import { getStatColor } from "@/lib/grades";

interface DataPoint {
  label: string;
  value: string;
  /** Optional 0-100 score to render as a colored bar under the value.
   *  Used by damage_output to show "vs +2 keys: 21" and "vs all keys: 3"
   *  with bars matching their respective percentiles, so the player
   *  can read the comparison visually without doing the math. Other
   *  data points (utility ability counts, raw damage numbers) leave
   *  this undefined and skip the bar. */
  bar?: number;
}

interface Props {
  explanation: CategoryExplanation;
  score: number;
  /**
   * Raw numbers that contributed to the score, rendered below the bar.
   * e.g., for Utility: "Total interrupts: 67", "Total dispels: 12"
   */
  dataPoints?: DataPoint[];
  /** Optional footnote rendered directly below the dataPoints grid.
   *  Used by damage_output to clarify that the bracketed pill counts
   *  toward grading and the global pill is context only — without
   *  putting that disclaimer on every category card. */
  dataPointsFootnote?: string;
  /** Weight (0-1) this category carries in the composite for this role. */
  weight?: number;
  /** Spec-aware override for the "How this is measured" description.
   *  When provided, replaces `explanation.description` in the expander
   *  so Resto Druid sees their actual dispel/CC list instead of the
   *  generic role-level copy. */
  specDescription?: string;
  /** Spec-aware override for the "How to improve" box. */
  specHowToImprove?: string;
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
  dataPointsFootnote,
  weight,
  specDescription,
  specHowToImprove,
}: Props) {
  const color = getStatColor(score);
  const rounded = Math.round(score);
  const description = specDescription ?? explanation.description;
  const howToImprove = specHowToImprove ?? explanation.howToImprove;

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
            {dataPoints.map((dp) => {
              const barColor = dp.bar !== undefined ? getStatColor(dp.bar) : null;
              return (
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
                  {dp.bar !== undefined && barColor && (
                    <div className="mt-1.5 h-1 bg-surface-container-low rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(100, Math.max(0, dp.bar))}%`,
                          backgroundColor: barColor,
                          boxShadow: `0 0 6px ${barColor}50`,
                        }}
                      />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {dataPointsFootnote && (
          <p className="text-xs italic text-on-surface-variant/80 leading-relaxed mb-4 -mt-1">
            {dataPointsFootnote}
          </p>
        )}

        <details className="group">
          <summary className="cursor-pointer font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary hover:text-primary-container transition-colors list-none flex items-center gap-1">
            <span className="material-symbols-outlined text-sm transition-transform group-open:rotate-90">
              chevron_right
            </span>
            How this is measured
          </summary>
          <div className="mt-3 pl-6 space-y-3 text-sm text-on-surface-variant leading-relaxed">
            <p>{description}</p>
            <div className="bg-surface-container-low rounded p-3 border-l-2 border-primary/40">
              <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary mb-1">
                How to improve
              </p>
              <p>{howToImprove}</p>
            </div>
          </div>
        </details>
      </div>
    </div>
  );
}
