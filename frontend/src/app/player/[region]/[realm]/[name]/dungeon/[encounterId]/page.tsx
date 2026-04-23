import Link from "next/link";
import { getDungeonSummary, getMethodology } from "@/lib/api";
import { getGradeColor, getStatColor } from "@/lib/grades";
import {
  getCategoriesForRole,
  ROLE_WEIGHT_PROFILES,
} from "@/lib/methodology";
import { dungeonName } from "@/lib/dungeons";
import { formatNumber } from "@/lib/utils";
import CategoryExplainer from "@/components/CategoryExplainer";
import type {
  DungeonAggregateStats,
  MethodologyResponse,
} from "@/lib/types";

interface Props {
  params: Promise<{
    region: string;
    realm: string;
    name: string;
    encounterId: string;
  }>;
  searchParams: Promise<{ role?: string }>;
}

/**
 * Dungeon-overview page. Reached by clicking a per-dungeon tile on the
 * profile. Shows the dungeon-aggregate breakdown (category scores,
 * totals, grade) scoped to a (player, encounter_id, role) triple, plus
 * a list of individual runs that link into their per-run detail page.
 *
 * Scoping rationale — the profile's per-dungeon tile is per-primary-
 * role by default, so this page follows the same default. `?role=X`
 * lets a user view the same dungeon through a different role's lens
 * when they have runs in more than one role.
 */
export default async function DungeonDetailPage({ params, searchParams }: Props) {
  const { region, realm, name, encounterId } = await params;
  const { role } = await searchParams;
  const playerPath = `/player/${region}/${realm}/${name}`;
  const encounterIdNum = parseInt(encounterId, 10);

  let summary;
  try {
    summary = await getDungeonSummary(region, realm, name, encounterIdNum, role);
  } catch {
    return (
      <div className="pt-24 pb-32 px-6 max-w-7xl mx-auto text-center">
        <h2 className="font-[family-name:var(--font-headline)] text-5xl font-extrabold tracking-tighter text-on-surface mb-4">
          DUNGEON NOT FOUND
        </h2>
        <Link
          href={playerPath}
          className="text-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest hover:underline"
        >
          Return to Profile
        </Link>
      </div>
    );
  }

  // No runs in this (player, dungeon, role) combo — show an empty state
  // rather than a broken breakdown.
  if (summary.runs_count === 0) {
    return (
      <div className="pt-24 pb-32 px-6 max-w-7xl mx-auto text-center">
        <h2 className="font-[family-name:var(--font-headline)] text-4xl font-extrabold tracking-tighter text-on-surface mb-4">
          NO {summary.dungeon_name.toUpperCase()} RUNS YET
        </h2>
        <p className="text-on-surface-variant mb-6">
          This profile has no logged runs of {summary.dungeon_name} in the{" "}
          <span className="uppercase">{summary.role}</span> role.
        </p>
        <Link
          href={playerPath}
          className="text-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest hover:underline"
        >
          Return to Profile
        </Link>
      </div>
    );
  }

  // Try to enrich the breakdown with spec-aware methodology copy.
  // Pick the most-played spec across the runs as the canonical spec
  // for this dungeon — matches the spec the player's actual data is
  // dominated by, and keeps the copy accurate for the common case.
  const specCounts = new Map<string, number>();
  for (const r of summary.runs) {
    specCounts.set(r.spec_name, (specCounts.get(r.spec_name) ?? 0) + 1);
  }
  const dominantSpec = [...specCounts.entries()].sort(
    (a, b) => b[1] - a[1],
  )[0]?.[0];
  const classId = summary.runs[0]?.class_id ?? null;

  let methodology: MethodologyResponse | null = null;
  if (classId && dominantSpec) {
    try {
      methodology = await getMethodology(classId, dominantSpec);
    } catch {
      methodology = null;
    }
  }

  const roleKey = summary.role.toLowerCase() as "dps" | "healer" | "tank";
  const weightMap: Record<string, number> = Object.fromEntries(
    (ROLE_WEIGHT_PROFILES[roleKey] ?? []).map((w) => [w.key, w.weight]),
  );
  const excluded = new Set(summary.excluded_categories);

  const categoryBlocks = getCategoriesForRole(roleKey)
    .filter(
      (c) =>
        c.key !== "timing_modifier" &&
        c.key in summary.category_scores &&
        !excluded.has(c.key),
    )
    .map((c) => ({
      explanation: c,
      score: summary.category_scores[c.key] ?? 0,
      weight: weightMap[c.key],
      dataPoints: dataPointsForAggregate(c.key, summary.stats),
    }));

  const grade = summary.grade ?? "—";
  const gradeColor = summary.grade ? getGradeColor(summary.grade) : "#9d9d9d";

  return (
    <main className="mt-24 px-6 max-w-7xl mx-auto space-y-10 pb-32">
      {/* Header */}
      <section className="bg-surface-container-high rounded-xl p-8">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <Link
              href={playerPath}
              className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary hover:underline inline-flex items-center gap-1 mb-3"
            >
              <span className="material-symbols-outlined text-sm">
                arrow_back
              </span>
              Back to profile
            </Link>
            <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
              Dungeon Overall
            </p>
            <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-4xl md:text-5xl tracking-tighter uppercase text-on-surface italic">
              {summary.dungeon_name}
            </h1>
            <p className="text-on-surface-variant text-sm mt-2">
              <span className="uppercase tracking-widest font-[family-name:var(--font-label)] text-[11px]">
                {summary.role}
              </span>
              {" · "}
              {summary.runs_count}{" "}
              {summary.runs_count === 1 ? "run" : "runs"}
              {dominantSpec && ` · mostly ${dominantSpec}`}
            </p>
          </div>
          <div className="text-right">
            <span
              className="font-[family-name:var(--font-headline)] font-black text-7xl leading-none"
              style={{
                color: gradeColor,
                textShadow: `0 0 20px ${gradeColor}60`,
              }}
            >
              {grade}
            </span>
            {summary.composite_score != null && (
              <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mt-1">
                {summary.composite_score.toFixed(0)} / 100
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Breakdown tiles */}
      {categoryBlocks.length > 0 && (
        <section className="bg-surface-container-high rounded-lg p-8">
          <div className="flex items-end justify-between mb-6 flex-wrap gap-4">
            <div>
              <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
                How Your {dungeonName(encounterIdNum)} Grade Breaks Down
              </p>
              <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-2xl tracking-tighter uppercase text-on-surface italic">
                The Breakdown
              </h3>
              <p className="text-on-surface-variant text-sm mt-2 max-w-xl">
                Aggregated across your {summary.runs_count}{" "}
                {summary.runs_count === 1 ? "run" : "runs"} of this dungeon.
                Numbers below each score come from the same run set.
              </p>
            </div>
            <Link
              href="/about"
              className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary hover:underline flex items-center gap-1"
            >
              Full methodology
              <span className="material-symbols-outlined text-sm">
                arrow_forward
              </span>
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {categoryBlocks.map((c) => {
              const specCopy = methodology?.categories?.[c.explanation.key];
              return (
                <CategoryExplainer
                  key={c.explanation.key}
                  explanation={c.explanation}
                  score={c.score}
                  weight={c.weight}
                  dataPoints={c.dataPoints}
                  specDescription={specCopy?.description}
                  specHowToImprove={specCopy?.howToImprove}
                />
              );
            })}
          </div>
        </section>
      )}

      {/* Run list */}
      <section className="bg-surface-container-high rounded-lg p-8">
        <div className="flex items-end justify-between mb-6">
          <div>
            <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
              Drill Into A Run
            </p>
            <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-2xl tracking-tighter uppercase text-on-surface italic">
              Runs Logged
            </h3>
          </div>
        </div>
        <div className="space-y-2">
          {summary.runs.map((r) => {
            const loggedAt = new Date(r.logged_at).toLocaleDateString();
            const dur = `${Math.floor(r.duration / 60000)}:${String(
              Math.floor((r.duration % 60000) / 1000),
            ).padStart(2, "0")}`;
            const runColor = r.run_composite_score != null
              ? getStatColor(r.run_composite_score)
              : "#6b6b6b";
            return (
              <Link
                key={r.id}
                href={`${playerPath}/run/${r.id}`}
                className="flex items-center justify-between gap-4 px-4 py-3 rounded-lg bg-surface-container border border-outline-variant/10 hover:bg-surface-bright transition-colors"
              >
                <div className="flex items-center gap-4 min-w-0">
                  <span
                    className="font-[family-name:var(--font-headline)] font-black text-2xl w-12 text-center shrink-0"
                    style={{ color: runColor }}
                  >
                    {r.run_grade ?? "—"}
                  </span>
                  <div className="min-w-0">
                    <p className="font-[family-name:var(--font-body)] font-bold text-on-surface text-sm truncate">
                      +{r.keystone_level} {r.timed ? "timed" : "depleted"}
                      {" · "}
                      {r.spec_name}
                    </p>
                    <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mt-0.5">
                      {loggedAt} · {dur} · {r.deaths}{" "}
                      {r.deaths === 1 ? "death" : "deaths"} ·{" "}
                      {formatNumber(r.avoidable_damage_taken)} avoidable
                    </p>
                  </div>
                </div>
                <span className="material-symbols-outlined text-on-surface-variant">
                  chevron_right
                </span>
              </Link>
            );
          })}
        </div>
      </section>
    </main>
  );
}

function dataPointsForAggregate(
  key: string,
  stats: DungeonAggregateStats | null,
): Array<{ label: string; value: string }> | undefined {
  if (!stats) return undefined;
  switch (key) {
    case "utility":
      return [
        { label: "Total interrupts", value: String(stats.total_interrupts) },
        { label: "Total dispels", value: String(stats.total_dispels) },
        { label: "Total CC casts", value: String(stats.total_cc_casts) },
        { label: "Critical kicks", value: String(stats.total_critical_interrupts) },
      ];
    case "survivability":
      return [
        { label: "Total deaths", value: String(stats.total_deaths) },
        { label: "Avoidable deaths", value: String(stats.total_avoidable_deaths) },
        { label: "Avoidable dmg taken", value: formatNumber(stats.total_avoidable_damage) },
        { label: "Total dmg taken", value: formatNumber(stats.total_damage_taken) },
      ];
    case "casts_per_minute": {
      const minutes = stats.total_duration_ms / 60000;
      const avgCpm =
        minutes > 0 ? (stats.total_casts / minutes).toFixed(1) : "0";
      return [
        { label: "Total casts", value: stats.total_casts.toLocaleString() },
        { label: "Avg CPM", value: avgCpm },
        { label: "Runs analyzed", value: String(stats.runs_count) },
      ];
    }
    case "cooldown_usage":
      return [
        { label: "Runs analyzed", value: String(stats.runs_count) },
      ];
    default:
      return undefined;
  }
}
