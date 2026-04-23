"use client";

import { useState } from "react";
import CategoryExplainer from "@/components/CategoryExplainer";
import { getMethodology } from "@/lib/api";
import type { CategoryExplanation } from "@/lib/methodology";
import type { MethodologyResponse, RoleScore, RoleSpecScore } from "@/lib/types";

interface CategoryBlock {
  explanation: CategoryExplanation;
  dataPoints?: Array<{ label: string; value: string }>;
  weight?: number;
}

interface Props {
  /** The role-aggregate score. Drives the default "All" tab — its
   *  category_scores populate the grid when no spec tab is active. */
  primaryScore: RoleScore;
  /** Class id for the methodology fetch on first spec tab click. */
  classId: number;
  /** Category metadata (explanations + dataPoints + weights) prebuilt on
   *  the server. On the "All" tab we render scores from primaryScore; on
   *  a spec tab we keep the same category order but pull scores from the
   *  selected spec and drop dataPoints (aggregate numbers mislead when
   *  scoped to a spec subset). */
  blocks: CategoryBlock[];
}

type TabValue = "all" | string; // spec_name for spec tabs

/**
 * Tab strip over a role's breakdown. Only renders tabs when the role
 * has >=2 specs with >=2 runs each — single-spec roles (the common
 * case) get the tab strip skipped and look identical to the previous
 * version. Methodology copy for a spec is lazy-fetched on first click
 * and cached client-side.
 */
export default function RoleBreakdownTabs({
  primaryScore,
  classId,
  blocks,
}: Props) {
  const specs = primaryScore.specs ?? [];
  const hasTabs = specs.length >= 2;

  const [active, setActive] = useState<TabValue>("all");
  // Keyed by spec_name so re-clicking a previously-opened tab is free.
  const [methodologyBySpec, setMethodologyBySpec] = useState<
    Record<string, MethodologyResponse>
  >({});
  const [loadingSpec, setLoadingSpec] = useState<string | null>(null);

  const activeSpec: RoleSpecScore | undefined =
    active === "all" ? undefined : specs.find((s) => s.spec_name === active);

  const activeMethodology: MethodologyResponse | undefined =
    active === "all" ? undefined : methodologyBySpec[active];

  async function onTabClick(value: TabValue) {
    setActive(value);
    if (value === "all") return;
    if (methodologyBySpec[value]) return; // cached
    setLoadingSpec(value);
    try {
      const m = await getMethodology(classId, value);
      setMethodologyBySpec((prev) => ({ ...prev, [value]: m }));
    } catch {
      // Silent — tab still renders the scores, just without spec copy.
    } finally {
      setLoadingSpec(null);
    }
  }

  // Excluded categories (no data): hide from the grid, just like the
  // server-side rendering did via run.dungeon_excluded_categories.
  const excluded = new Set(activeSpec?.excluded_categories ?? []);

  const rendered = blocks
    .filter((b) => !excluded.has(b.explanation.key))
    .map((b) => {
      const score = activeSpec
        ? activeSpec.category_scores[b.explanation.key] ??
          primaryScore.category_scores[b.explanation.key] ??
          0
        : primaryScore.category_scores[b.explanation.key] ?? 0;
      const specCopy =
        activeMethodology?.categories?.[b.explanation.key];
      return {
        key: b.explanation.key,
        explanation: b.explanation,
        score,
        // Drop dataPoints when a spec tab is active: the raw totals are
        // computed off the last 20 recent runs (role aggregate), so
        // showing them under a spec tab would be misleading.
        dataPoints: activeSpec ? undefined : b.dataPoints,
        weight: b.weight,
        specDescription: specCopy?.description,
        specHowToImprove: specCopy?.howToImprove,
      };
    });

  return (
    <>
      {hasTabs && (
        <div
          role="tablist"
          aria-label="Breakdown by spec"
          className="flex items-center gap-2 mb-5 flex-wrap"
        >
          <TabButton
            label={`All (${primaryScore.runs_analyzed})`}
            active={active === "all"}
            onClick={() => onTabClick("all")}
          />
          {specs.map((s) => (
            <TabButton
              key={s.spec_name}
              label={`${s.spec_name} (${s.runs_analyzed})`}
              active={active === s.spec_name}
              loading={loadingSpec === s.spec_name}
              onClick={() => onTabClick(s.spec_name)}
            />
          ))}
        </div>
      )}

      {activeSpec && activeSpec.grade === null && (
        <p className="text-on-surface-variant text-xs mb-4 italic">
          Only {activeSpec.runs_analyzed} runs logged as {activeSpec.spec_name}.
          Shown without a letter grade until there&apos;s enough data.
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rendered.map((c) => (
          <CategoryExplainer
            key={c.key}
            explanation={c.explanation}
            score={c.score}
            dataPoints={c.dataPoints}
            weight={c.weight}
            specDescription={c.specDescription}
            specHowToImprove={c.specHowToImprove}
          />
        ))}
      </div>
    </>
  );
}

function TabButton({
  label,
  active,
  loading,
  onClick,
}: {
  label: string;
  active: boolean;
  loading?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={
        "font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest " +
        "px-3 py-1.5 rounded transition-colors " +
        (active
          ? "bg-primary text-on-primary"
          : "bg-surface-container-high text-on-surface-variant hover:bg-surface-bright")
      }
    >
      {label}
      {loading && <span className="ml-2 animate-pulse">...</span>}
    </button>
  );
}
