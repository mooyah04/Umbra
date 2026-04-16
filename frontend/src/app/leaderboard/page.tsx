import Link from "next/link";
import { getLeaderboard } from "@/lib/api";
import { getGradeColor } from "@/lib/grades";
import { CLASS_COLORS, CLASS_NAMES } from "@/lib/utils";
import { classIconUrl } from "@/lib/wow-assets";
import type { PlayerSearchResult } from "@/lib/types";

/**
 * Leaderboard page — top-N players ordered by composite score.
 *
 * Filters (role / class / region) are passed via query params rather than
 * client-side state so the URL is shareable and SSR can pre-render the
 * requested slice. A tab row at the top swaps role; a compact selector
 * row handles class + region.
 */

// Short ISR window — scores shift as the ingest sweep re-scores players,
// and seeing stale placements after visible backfill activity is
// confusing. The underlying getLeaderboard fetch also uses 20s.
export const revalidate = 20;

const ROLE_TABS: Array<{ key: string; label: string }> = [
  { key: "all", label: "All Roles" },
  { key: "tank", label: "Tank" },
  { key: "healer", label: "Healer" },
  { key: "dps", label: "DPS" },
];

const REGIONS = ["all", "eu", "us", "kr", "tw", "cn"] as const;

interface PageProps {
  searchParams: Promise<{
    role?: string;
    region?: string;
    class?: string;
  }>;
}

function buildHref(
  current: { role?: string; region?: string; class?: string },
  patch: Partial<{ role?: string; region?: string; class?: string }>,
): string {
  // Null/undefined in a patch value = clear the param.
  const merged = { ...current, ...patch };
  const params = new URLSearchParams();
  if (merged.role && merged.role !== "all") params.set("role", merged.role);
  if (merged.region && merged.region !== "all") params.set("region", merged.region);
  if (merged.class) params.set("class", merged.class);
  const qs = params.toString();
  return qs ? `/leaderboard?${qs}` : "/leaderboard";
}

export default async function LeaderboardPage({ searchParams }: PageProps) {
  const sp = await searchParams;
  const role = sp.role && ROLE_TABS.some((t) => t.key === sp.role) ? sp.role : "all";
  const region = sp.region && REGIONS.includes(sp.region.toLowerCase() as typeof REGIONS[number])
    ? sp.region.toLowerCase()
    : "all";
  const classId = sp.class ? Number(sp.class) : undefined;

  let rows: PlayerSearchResult[];
  try {
    rows = await getLeaderboard({
      role: role === "all" ? undefined : (role as "tank" | "healer" | "dps"),
      region: region === "all" ? undefined : region.toUpperCase(),
      classId: classId && classId >= 1 && classId <= 13 ? classId : undefined,
      limit: 100,
    });
  } catch {
    rows = [];
  }

  return (
    <main className="pt-24 pb-32 px-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
          Top Performers
        </p>
        <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-4xl md:text-5xl tracking-tighter text-on-surface">
          LEADERBOARD
        </h1>
        <p className="text-on-surface-variant mt-2 text-sm leading-relaxed max-w-2xl">
          Ranked by composite score across every graded M+ run in our database.
          Filter by role, class, or region.
        </p>
      </div>

      {/* Role tabs */}
      <div className="flex flex-wrap gap-2 mb-4">
        {ROLE_TABS.map((t) => (
          <Link
            key={t.key}
            href={buildHref({ role, region, class: sp.class }, { role: t.key })}
            className={
              "font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest px-4 py-2 rounded " +
              (role === t.key
                ? "bg-primary text-on-primary"
                : "bg-surface-container-high text-on-surface hover:bg-surface-bright transition-colors")
            }
          >
            {t.label}
          </Link>
        ))}
      </div>

      {/* Secondary filters */}
      <div className="flex flex-wrap items-center gap-3 mb-8 text-sm">
        <span className="text-on-surface-variant text-xs uppercase tracking-widest">Region:</span>
        {REGIONS.map((r) => (
          <Link
            key={r}
            href={buildHref({ role, region, class: sp.class }, { region: r })}
            className={
              "px-3 py-1 rounded text-xs " +
              (region === r
                ? "bg-primary/30 text-on-primary-container"
                : "text-on-surface-variant hover:text-primary")
            }
          >
            {r === "all" ? "All" : r.toUpperCase()}
          </Link>
        ))}
        {classId && (
          <Link
            href={buildHref({ role, region, class: sp.class }, { class: undefined })}
            className="ml-auto bg-surface-container-high px-3 py-1 rounded text-xs text-on-surface-variant hover:text-primary"
          >
            × Clear class filter ({CLASS_NAMES[classId] ?? classId})
          </Link>
        )}
      </div>

      {/* Rows */}
      {rows.length === 0 ? (
        <div className="bg-surface-container-high rounded-xl p-10 text-center text-on-surface-variant">
          No players match the current filters yet.
        </div>
      ) : (
        <ul className="space-y-1">
          {rows.map((p) => {
            const className = CLASS_NAMES[p.class_id] ?? "Unknown";
            const classColor = CLASS_COLORS[p.class_id] ?? "#ffffff";
            const gradeColor = p.grade ? getGradeColor(p.grade) : "#9d9d9d";
            const href = `/player/${p.region.toLowerCase()}/${p.realm}/${encodeURIComponent(p.name)}`;
            const composite = p.composite_score != null ? p.composite_score.toFixed(1) : null;

            return (
              <li key={`${p.region}-${p.realm}-${p.name}`}>
                <Link
                  href={href}
                  className="flex items-center gap-4 bg-surface-container-high hover:bg-surface-bright transition-colors rounded-lg px-4 py-3"
                >
                  {/* Rank */}
                  <span className="font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-on-surface-variant w-8 text-right">
                    #{p.rank}
                  </span>

                  {/* Class icon */}
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={p.avatar_url ?? classIconUrl(p.class_id)}
                    alt={className}
                    className="w-10 h-10 rounded-full object-cover"
                  />

                  {/* Name + class/realm */}
                  <div className="flex-1 min-w-0">
                    <p className="font-bold truncate" style={{ color: classColor }}>
                      {p.name}
                    </p>
                    <p className="text-xs text-on-surface-variant truncate">
                      {p.spec ? `${p.spec} ${className}` : className} · {p.realm}-{p.region.toUpperCase()}
                    </p>
                  </div>

                  {/* Role chip */}
                  {p.role && (
                    <span className="hidden md:inline-block font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant bg-surface-container-lowest px-2 py-1 rounded">
                      {p.role}
                    </span>
                  )}

                  {/* Runs count */}
                  <span className="hidden sm:inline text-xs text-on-surface-variant w-16 text-right">
                    {p.runs_analyzed ?? 0} runs
                  </span>

                  {/* Composite + Grade */}
                  <div className="text-right flex items-baseline gap-3">
                    {composite && (
                      <span className="text-sm text-on-surface-variant">{composite}</span>
                    )}
                    <span
                      className="font-[family-name:var(--font-headline)] font-extrabold text-2xl tracking-tighter w-14 text-right"
                      style={{ color: gradeColor }}
                    >
                      {p.grade ?? "—"}
                    </span>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
