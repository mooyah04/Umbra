import Link from "next/link";
import { getPlayerProfile } from "@/lib/api";
import { getGradeColor, getStatColor } from "@/lib/grades";
import { formatDuration, CLASS_COLORS, CLASS_NAMES } from "@/lib/utils";

interface Props {
  params: Promise<{ region: string; realm: string; name: string }>;
}

export default async function PlayerProfilePage({ params }: Props) {
  const { region, realm, name } = await params;

  let profile;
  try {
    profile = await getPlayerProfile(region, realm, name);
  } catch {
    return (
      <div className="pt-24 pb-32 px-6 max-w-7xl mx-auto text-center">
        <h2 className="font-[family-name:var(--font-headline)] text-5xl font-extrabold tracking-tighter text-on-surface mb-4">
          PLAYER NOT FOUND
        </h2>
        <p className="text-on-surface-variant mb-8">
          Could not find {decodeURIComponent(name)} on {decodeURIComponent(realm)}-{region.toUpperCase()}
        </p>
        <Link href="/" className="text-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest hover:underline">
          Return to Search
        </Link>
      </div>
    );
  }

  const primary = profile.scores.find((s) => s.primary_role) ?? profile.scores[0];
  const playerPath = `/player/${region}/${realm}/${name}`;
  const spec = profile.recent_runs[0]?.spec_name ?? "Unknown";
  const className = CLASS_NAMES[profile.class_id] ?? "Unknown";
  const classColor = CLASS_COLORS[profile.class_id] ?? "#ffffff";
  const gradeColor = primary ? getGradeColor(primary.grade) : "#9d9d9d";

  return (
    <main className="pt-24 pb-32 px-6 max-w-7xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Main Identifier Hero */}
        <div className="md:col-span-8 bg-surface-container-high rounded-xl p-8 relative overflow-hidden flex flex-col justify-end min-h-[320px]">
          <div className="absolute inset-0 opacity-10 pointer-events-none bg-gradient-to-br from-primary/30 via-transparent to-secondary/20" />
          <div className="absolute inset-0 bg-gradient-to-t from-surface-container-high via-surface-container-high/60 to-transparent" />
          <div className="relative z-10">
            <div className="flex items-center gap-4 mb-2">
              <span className="bg-primary text-on-primary font-[family-name:var(--font-label)] text-[10px] px-2 py-0.5 rounded-sm uppercase font-bold tracking-widest">
                {primary?.role?.toUpperCase() ?? "DPS"} MAIN
              </span>
              <span className="text-[10px] font-[family-name:var(--font-label)] px-1 border border-primary/20 text-primary uppercase">
                {region.toUpperCase()}
              </span>
            </div>
            <h2 className="font-[family-name:var(--font-headline)] font-extrabold text-6xl md:text-8xl tracking-tighter text-on-surface uppercase">
              {profile.name}
            </h2>
            <p className="font-[family-name:var(--font-body)] text-on-surface-variant text-lg tracking-wide">
              {profile.realm} &middot;{" "}
              <span style={{ color: classColor }}>{spec} {className}</span>
            </p>
          </div>
        </div>

        {/* Overall Grade */}
        <div className="md:col-span-4 bg-surface-container-high rounded-xl p-8 flex flex-col items-center justify-center text-center border-b-4 border-primary/20">
          <span className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-on-surface-variant mb-4">
            Overall Performance
          </span>
          <div className="relative">
            <span
              className="font-[family-name:var(--font-headline)] font-black text-9xl"
              style={{ color: gradeColor, textShadow: `0 0 20px ${gradeColor}40` }}
            >
              {primary?.grade ?? "N/R"}
            </span>
            {primary && (
              <div className="absolute -top-2 -right-4 bg-tertiary text-white font-[family-name:var(--font-label)] text-xs font-bold px-2 py-1 rounded-sm rotate-12">
                {profile.total_runs} RUNS
              </div>
            )}
          </div>
          <div className="mt-6 w-full h-1 bg-surface-container-highest rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${profile.timed_pct}%`,
                backgroundColor: gradeColor,
                boxShadow: `0 0 8px ${gradeColor}80`,
              }}
            />
          </div>
          <p className="mt-4 font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-widest italic">
            {profile.timed_pct}% Keys Timed
          </p>
        </div>

        {/* Category Breakdown */}
        <div className="md:col-span-4 bg-surface-container-low rounded-xl p-6">
          <h3 className="font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-on-surface-variant mb-6 flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">bar_chart</span>
            Category Breakdown
          </h3>
          {primary ? (
            <div className="space-y-6">
              {Object.entries(primary.category_scores)
                .filter(([key]) => !["timing_modifier", "damage_output_ilvl"].includes(key))
                .map(([key, value]) => {
                  const color = getStatColor(value);
                  const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
                  return (
                    <div key={key} className="space-y-2">
                      <div className="flex justify-between items-end">
                        <span className="font-[family-name:var(--font-body)] text-sm font-semibold">{label}</span>
                        <span className="font-[family-name:var(--font-label)] font-bold" style={{ color }}>
                          {Math.round(value)}/100
                        </span>
                      </div>
                      <div className="h-2 bg-surface-container-highest rounded-sm">
                        <div
                          className="h-full rounded-sm transition-all duration-500"
                          style={{
                            width: `${value}%`,
                            backgroundColor: color,
                            boxShadow: `0 0 8px ${color}30`,
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          ) : (
            <p className="text-on-surface-variant text-sm">No score data available.</p>
          )}
        </div>

        {/* Run History */}
        <div className="md:col-span-8 bg-surface-container-low rounded-xl p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-on-surface-variant flex items-center gap-2">
              <span className="material-symbols-outlined text-sm">history</span>
              Recent Run History
            </h3>
            <Link
              href={`${playerPath}/progress`}
              className="text-primary font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest hover:underline"
            >
              View All Activity
            </Link>
          </div>
          <div className="space-y-3 overflow-y-auto max-h-[400px]" style={{ scrollbarWidth: "none" }}>
            {profile.recent_runs.length > 0 ? (
              profile.recent_runs.map((run) => (
                <Link
                  key={run.id}
                  href={`${playerPath}/run/${run.id}`}
                  className="bg-surface-container-high rounded-lg p-4 flex items-center justify-between group hover:bg-surface-bright transition-colors block"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-surface-container-highest rounded-md flex items-center justify-center">
                      <span className="material-symbols-outlined text-on-surface">fort</span>
                    </div>
                    <div>
                      <h4 className="font-[family-name:var(--font-body)] font-bold text-on-surface">
                        +{run.keystone_level} &middot; {run.spec_name}
                      </h4>
                      <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-tighter">
                        {formatDuration(run.duration)} &middot; {new Date(run.logged_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-8">
                    <div className="text-right hidden md:block">
                      <p className="font-[family-name:var(--font-label)] text-sm font-bold text-on-surface">
                        {run.deaths}d / {run.interrupts}k / {run.dispels}disp
                      </p>
                    </div>
                    <div className="flex flex-col items-center">
                      {run.timed ? (
                        <>
                          <span className="material-symbols-outlined text-primary text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                            check_circle
                          </span>
                          <span className="font-[family-name:var(--font-label)] text-[8px] text-primary uppercase mt-1">Timed</span>
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined text-error text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                            cancel
                          </span>
                          <span className="font-[family-name:var(--font-label)] text-[8px] text-error uppercase mt-1">Depleted</span>
                        </>
                      )}
                    </div>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-on-surface-variant text-sm text-center py-8">No runs recorded yet.</p>
            )}
          </div>
        </div>
      </div>

      {/* Floating Detail Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        <div className="bg-surface-container p-6 rounded-xl border-l-2 border-primary">
          <span className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase block mb-1">Current Spec</span>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-primary text-2xl">flare</span>
            <div>
              <p className="font-[family-name:var(--font-body)] font-bold leading-tight">{spec}</p>
              <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">
                {className} &middot; {primary?.role?.toUpperCase() ?? "DPS"}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-surface-container p-6 rounded-xl border-l-2 border-secondary">
          <span className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase block mb-1">Item Level</span>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-secondary text-2xl">shield_with_heart</span>
            <div>
              <p className="font-[family-name:var(--font-body)] font-bold leading-tight">
                {profile.recent_runs[0]?.ilvl?.toFixed(0) ?? "—"}
              </p>
              <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">Latest Run</p>
            </div>
          </div>
        </div>
        <div className="bg-surface-container p-6 rounded-xl border-l-2 border-tertiary">
          <span className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase block mb-1">M+ Score</span>
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-tertiary text-2xl">stars</span>
            <div>
              <p className="font-[family-name:var(--font-body)] font-bold leading-tight">
                {profile.recent_runs[0]?.rating ?? "—"}
              </p>
              <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">Blizzard Rating</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
