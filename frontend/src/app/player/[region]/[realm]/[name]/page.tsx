import Link from "next/link";
import { getPlayerProfile } from "@/lib/api";
import { getGradeColor, getStatColor } from "@/lib/grades";
import {
  getCategoriesForRole,
  getCategoryExplanation,
  ROLE_WEIGHT_PROFILES,
} from "@/lib/methodology";
import { formatDuration, CLASS_COLORS, CLASS_NAMES } from "@/lib/utils";
import { specIconUrl, classIdFromName, classifyDpsSpec } from "@/lib/wow-assets";
import { dungeonName } from "@/lib/dungeons";
import CategoryExplainer from "@/components/CategoryExplainer";
import type { RunResponse, RoleScore, PartyMember } from "@/lib/types";

interface Props {
  params: Promise<{ region: string; realm: string; name: string }>;
}

/**
 * Average a numeric field across runs, rounded to the specified decimals.
 * Safely handles null/undefined fields (returns 0 for those entries).
 */
function avg(runs: RunResponse[], field: keyof RunResponse, decimals = 1): string {
  if (!runs.length) return "0";
  const sum = runs.reduce((acc, r) => acc + (Number(r[field]) || 0), 0);
  return (sum / runs.length).toFixed(decimals);
}

function total(runs: RunResponse[], field: keyof RunResponse): number {
  return runs.reduce((acc, r) => acc + (Number(r[field]) || 0), 0);
}

/**
 * For each category, produce the raw per-run numbers that drove the score.
 * Kept close to the scoring engine's inputs so players can reason about
 * what changed their grade.
 */
function getDataPointsForCategory(
  key: string,
  role: string,
  runs: RunResponse[],
): Array<{ label: string; value: string }> {
  if (!runs.length) return [];
  switch (key) {
    case "utility":
      return [
        { label: "Total interrupts", value: String(total(runs, "interrupts")) },
        { label: "Total dispels", value: String(total(runs, "dispels")) },
        { label: "Total CC casts", value: String(total(runs, "cc_casts")) },
        {
          label: "Critical kicks",
          value: String(total(runs, "critical_interrupts")),
        },
      ];
    case "survivability":
      return [
        { label: "Total deaths", value: String(total(runs, "deaths")) },
        {
          label: "Avoidable deaths",
          value: String(total(runs, "avoidable_deaths")),
        },
        { label: "Avg deaths / run", value: avg(runs, "deaths") },
        {
          label: "Avoidable dmg taken",
          value: total(runs, "avoidable_damage_taken").toLocaleString(),
        },
      ];
    case "cooldown_usage":
      return [
        { label: "Avg CD usage %", value: `${avg(runs, "cooldown_usage_pct")}%` },
        { label: "Runs analyzed", value: String(runs.length) },
      ];
    case "casts_per_minute": {
      const totalCasts = total(runs, "casts_total");
      const totalDurationMin = total(runs, "duration") / 60000;
      const cpm = totalDurationMin > 0 ? totalCasts / totalDurationMin : 0;
      return [
        { label: "Total casts", value: totalCasts.toLocaleString() },
        { label: "Avg CPM", value: cpm.toFixed(1) },
        {
          label: "Fight duration",
          value: `${totalDurationMin.toFixed(0)} min`,
        },
      ];
    }
    case "damage_output":
      return [
        { label: "Runs analyzed", value: String(runs.length) },
        { label: "Best key", value: `+${Math.max(...runs.map((r) => r.keystone_level))}` },
      ];
    case "healing_throughput":
      if (role !== "healer") return [];
      return [
        { label: "Runs analyzed", value: String(runs.length) },
      ];
    case "timing_modifier": {
      const timedCount = runs.filter((r) => r.timed).length;
      const pct = runs.length ? (timedCount / runs.length) * 100 : 0;
      return [
        { label: "Keys timed", value: `${timedCount} / ${runs.length}` },
        { label: "Timing rate", value: `${pct.toFixed(0)}%` },
      ];
    }
    default:
      return [];
  }
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
          Could not find {decodeURIComponent(name)} on{" "}
          {decodeURIComponent(realm)}-{region.toUpperCase()}
        </p>
        <Link
          href="/"
          className="text-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest hover:underline"
        >
          Return to Search
        </Link>
      </div>
    );
  }

  const primary: RoleScore | undefined =
    profile.scores.find((s) => s.primary_role) ?? profile.scores[0];
  const playerPath = `/player/${region}/${realm}/${name}`;
  const spec = profile.recent_runs[0]?.spec_name ?? "Unknown";
  const className = CLASS_NAMES[profile.class_id] ?? "Unknown";
  const classColor = CLASS_COLORS[profile.class_id] ?? "#ffffff";
  const gradeColor = primary ? getGradeColor(primary.grade) : "#9d9d9d";
  const role = primary?.role ?? "dps";
  const roleWeights =
    ROLE_WEIGHT_PROFILES[role as "dps" | "healer" | "tank"] ?? [];
  const weightMap: Record<string, number> = Object.fromEntries(
    roleWeights.map((w) => [w.key, w.weight]),
  );

  const categoryScoresForRole = primary
    ? getCategoriesForRole(role)
        .filter((c) => c.key in primary.category_scores || c.key === "timing_modifier")
        .map((c) => ({
          explanation: c,
          score: primary.category_scores[c.key] ?? 0,
          dataPoints: getDataPointsForCategory(c.key, role, profile.recent_runs),
          weight: weightMap[c.key],
        }))
    : [];

  return (
    <main className="pt-24 pb-32 px-6 max-w-7xl mx-auto">
      {/* ── Hero row ── */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-8">
        <div className="md:col-span-8 bg-surface-container-high rounded-xl p-8 relative overflow-hidden flex flex-col justify-end min-h-[320px]">
          {/* Blizzard main-raw render as a subtle backdrop when available */}
          {profile.render_url && (
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={profile.render_url}
                alt=""
                aria-hidden
                className="absolute inset-0 w-full h-full object-cover object-right opacity-30 pointer-events-none"
              />
            </>
          )}
          <div
            className="absolute inset-0 opacity-30"
            style={{
              background: `radial-gradient(circle at 30% 50%, ${classColor}40, transparent 60%)`,
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-surface-container-high via-surface-container-high/70 to-transparent" />
          <div className="relative z-10 flex items-end gap-6">
            {/* Avatar if Blizzard has one, otherwise the spec icon */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={profile.avatar_url ?? specIconUrl(spec, profile.class_id)}
              alt={`${spec} ${className}`}
              width={112}
              height={112}
              className="rounded-lg border-2 shadow-xl flex-shrink-0 hidden md:block"
              style={{ borderColor: `${classColor}80` }}
            />
            <div className="min-w-0">
              <div className="flex items-center gap-2 md:gap-3 mb-2 flex-wrap">
                <span className="bg-primary text-on-primary font-[family-name:var(--font-label)] text-[10px] px-2 py-0.5 rounded-sm uppercase font-bold tracking-widest">
                  {role.toUpperCase()} MAIN
                </span>
                <span className="text-[10px] font-[family-name:var(--font-label)] px-2 py-0.5 border border-primary/20 text-primary uppercase">
                  {region.toUpperCase()}
                </span>
                <span
                  className="text-[10px] font-[family-name:var(--font-label)] px-2 py-0.5 border uppercase font-bold"
                  style={{
                    color: classColor,
                    borderColor: `${classColor}40`,
                  }}
                >
                  {className}
                </span>
              </div>
              <h2 className="font-[family-name:var(--font-headline)] font-extrabold text-5xl md:text-7xl lg:text-8xl tracking-tighter text-on-surface uppercase leading-[0.9]">
                {profile.name}
              </h2>
              <p className="font-[family-name:var(--font-body)] text-on-surface-variant text-lg tracking-wide mt-2">
                {profile.realm} &middot;{" "}
                <span style={{ color: classColor }}>
                  {spec} {className}
                </span>
              </p>
            </div>
          </div>
        </div>

        <div className="md:col-span-4 bg-surface-container-high rounded-xl p-8 flex flex-col items-center justify-center text-center border-b-4 border-primary/20">
          <span className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-on-surface-variant mb-4">
            Overall Performance
          </span>
          <div className="relative">
            <span
              className="font-[family-name:var(--font-headline)] font-black text-9xl"
              style={{
                color: gradeColor,
                textShadow: `0 0 20px ${gradeColor}40`,
              }}
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
      </div>

      {/* ── Quick-stat strip ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        <QuickStat
          label="Current Spec"
          value={spec}
          sub={className}
          icon="flare"
          color="primary"
        />
        <QuickStat
          label="Item Level"
          value={profile.recent_runs[0]?.ilvl?.toFixed(0) ?? "—"}
          sub="Latest run"
          icon="shield_with_heart"
          color="secondary"
        />
        <QuickStat
          label="Blizzard Rating"
          value={profile.recent_runs[0]?.rating?.toString() ?? "—"}
          sub="Last logged"
          icon="stars"
          color="tertiary"
        />
        <QuickStat
          label="Keys Timed"
          value={`${profile.timed_pct}%`}
          sub={`${profile.total_runs} runs`}
          icon="check_circle"
          color="primary"
        />
      </div>

      {/* ── How we graded you ── */}
      {primary && (
        <section className="mb-10">
          <div className="flex items-end justify-between mb-6 flex-wrap gap-4">
            <div>
              <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
                How We Graded You
              </p>
              <h3 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-4xl tracking-tighter text-on-surface">
                THE BREAKDOWN
              </h3>
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
            {categoryScoresForRole.map((c) => (
              <CategoryExplainer
                key={c.explanation.key}
                explanation={c.explanation}
                score={c.score}
                dataPoints={c.dataPoints}
                weight={c.weight}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── Run history ── */}
      <section className="mb-10">
        <div className="flex items-end justify-between mb-6">
          <div>
            <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
              Activity
            </p>
            <h3 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-4xl tracking-tighter text-on-surface">
              RECENT RUNS
            </h3>
          </div>
          <Link
            href={`${playerPath}/progress`}
            className="text-primary font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest hover:underline"
          >
            View All Activity
          </Link>
        </div>
        <div className="bg-surface-container-low rounded-xl p-4">
          {profile.recent_runs.length > 0 ? (
            <div className="space-y-2">
              {profile.recent_runs.map((run) => (
                <RunRow
                  key={run.id}
                  run={run}
                  href={`${playerPath}/run/${run.id}`}
                />
              ))}
            </div>
          ) : (
            <p className="text-on-surface-variant text-center py-16">
              No runs recorded yet. Run an M+ key with Advanced Combat Logging
              enabled, upload to Warcraft Logs, and re-ingest.
            </p>
          )}
        </div>
      </section>
    </main>
  );
}

function QuickStat({
  label,
  value,
  sub,
  icon,
  color,
}: {
  label: string;
  value: string;
  sub: string;
  icon: string;
  color: "primary" | "secondary" | "tertiary";
}) {
  const border = {
    primary: "border-primary",
    secondary: "border-secondary",
    tertiary: "border-tertiary",
  }[color];
  const text = {
    primary: "text-primary",
    secondary: "text-secondary",
    tertiary: "text-tertiary",
  }[color];
  return (
    <div className={`bg-surface-container rounded-xl p-5 border-l-2 ${border}`}>
      <span className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase block mb-2 tracking-widest">
        {label}
      </span>
      <div className="flex items-center gap-3">
        <span className={`material-symbols-outlined text-2xl ${text}`}>
          {icon}
        </span>
        <div>
          <p className="font-[family-name:var(--font-body)] font-bold leading-tight text-on-surface">
            {value}
          </p>
          <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">
            {sub}
          </p>
        </div>
      </div>
    </div>
  );
}

function RunRow({ run, href }: { run: RunResponse; href: string }) {
  const when = new Date(run.logged_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
  const ccExplainer = getCategoryExplanation("utility");
  void ccExplainer; // avoid unused warning in release builds

  const party = (run.party_comp ?? []) as PartyMember[];

  return (
    <Link
      href={href}
      className="bg-surface-container-high rounded-lg p-4 flex flex-col lg:flex-row lg:items-center gap-4 group hover:bg-surface-bright transition-colors"
    >
      {/* Left — key badge + dungeon meta */}
      <div className="flex items-center gap-4 lg:min-w-0 lg:w-64 flex-shrink-0">
        <div className="w-14 h-14 bg-surface-container-highest rounded-md flex flex-col items-center justify-center relative overflow-hidden flex-shrink-0">
          {run.timed && (
            <span className="absolute inset-0 bg-primary/10" />
          )}
          <span
            className={`relative font-[family-name:var(--font-headline)] font-black text-xl ${
              run.timed ? "text-primary" : "text-on-surface-variant"
            }`}
          >
            +{run.keystone_level}
          </span>
        </div>
        <div className="min-w-0">
          <h4 className="font-[family-name:var(--font-body)] font-bold text-on-surface truncate">
            {dungeonName(run.encounter_id)}
          </h4>
          <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-widest mt-0.5 truncate">
            {run.spec_name} &middot; {formatDuration(run.duration)}
          </p>
          <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-widest truncate">
            {when} &middot; ilvl {run.ilvl.toFixed(0)}
          </p>
        </div>
      </div>

      {/* Middle — party composition grouped by role */}
      {party.length > 0 && (
        <div className="flex-1 min-w-0">
          <PartyGrid party={party} />
        </div>
      )}

      {/* Right — stats */}
      <div className="flex items-center gap-3 lg:gap-5 text-[11px] font-[family-name:var(--font-label)] uppercase tracking-widest flex-shrink-0">
        <Stat label="Kicks" value={run.interrupts} color="text-primary" />
        <Stat label="Dispels" value={run.dispels} color="text-tertiary" />
        <Stat
          label="CC"
          value={run.cc_casts ?? 0}
          color="text-secondary"
        />
        <Stat
          label="Deaths"
          value={run.deaths}
          color={run.deaths === 0 ? "text-primary" : "text-error"}
        />
        <span
          className={`flex flex-col items-center ${
            run.timed ? "text-primary" : "text-error"
          }`}
        >
          <span
            className="material-symbols-outlined text-xl"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            {run.timed ? "check_circle" : "cancel"}
          </span>
          <span className="text-[9px] mt-0.5">
            {run.timed ? "Timed" : "Depleted"}
          </span>
        </span>
      </div>
    </Link>
  );
}

function PartyGrid({ party }: { party: PartyMember[] }) {
  // Bucket party members into the four M+ role columns. DPS specs get
  // classified as melee or ranged via classifyDpsSpec().
  const buckets: Record<"tank" | "healer" | "melee" | "ranged", PartyMember[]> = {
    tank: [],
    healer: [],
    melee: [],
    ranged: [],
  };
  for (const m of party) {
    if (m.role === "tank") buckets.tank.push(m);
    else if (m.role === "healer") buckets.healer.push(m);
    else {
      const classId = classIdFromName(m.class);
      const kind = classifyDpsSpec(m.spec, classId);
      buckets[kind].push(m);
    }
  }

  const columns: Array<{ key: "tank" | "healer" | "melee" | "ranged"; label: string }> = [
    { key: "tank", label: "Tank" },
    { key: "healer", label: "Healer" },
    { key: "melee", label: "Melee DPS" },
    { key: "ranged", label: "Ranged DPS" },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-2">
      {columns.map((col) => {
        const members = buckets[col.key];
        if (members.length === 0) return null;
        return (
          <div key={col.key} className="min-w-0">
            <p className="font-[family-name:var(--font-label)] text-[9px] uppercase tracking-widest text-on-surface-variant mb-1.5 truncate">
              {col.label}
            </p>
            <div className="space-y-1.5">
              {members.map((m, i) => (
                <PartyMemberChip key={`${m.name}-${m.realm}-${i}`} member={m} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PartyMemberChip({ member }: { member: PartyMember }) {
  const classId = classIdFromName(member.class);
  const color = classId ? CLASS_COLORS[classId] ?? "#9d9d9d" : "#9d9d9d";
  const icon = classId ? specIconUrl(member.spec, classId) : null;
  return (
    <div
      className="flex items-center gap-2 min-w-0"
      title={`${member.name} — ${member.spec ?? ""} ${member.class}`}
    >
      {icon ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={icon}
          alt={member.class}
          width={22}
          height={22}
          className="rounded flex-shrink-0"
          style={{ boxShadow: `0 0 0 1px ${color}` }}
        />
      ) : (
        <span
          className="inline-block w-[22px] h-[22px] rounded bg-surface-container-highest flex-shrink-0"
          style={{ boxShadow: `0 0 0 1px ${color}` }}
        />
      )}
      <div className="min-w-0">
        <p
          className="font-[family-name:var(--font-body)] text-xs font-semibold truncate leading-tight"
          style={{ color }}
        >
          {member.name}
        </p>
        <p className="font-[family-name:var(--font-label)] text-[9px] text-on-surface-variant uppercase truncate">
          {member.realm}
        </p>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="flex flex-col items-center min-w-[44px]">
      <span
        className={`font-[family-name:var(--font-headline)] font-bold text-base ${color}`}
        style={{ textShadow: `0 0 6px currentColor` }}
      >
        {value}
      </span>
      <span className="text-[9px] text-on-surface-variant">{label}</span>
    </div>
  );
}

export function getStatColorRef() {
  // Keeps getStatColor referenced for build — used elsewhere
  return getStatColor;
}
