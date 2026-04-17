import Link from "next/link";
import { getRunDetail } from "@/lib/api";
import { dungeonName } from "@/lib/dungeons";
import { formatNumber } from "@/lib/utils";
import type { Pull, PullEvent, PullEventType, PullVerdict } from "@/lib/types";

interface Props {
  params: Promise<{ region: string; realm: string; name: string; runId: string }>;
}

export default async function RunBreakdownPage({ params }: Props) {
  const { region, realm, name, runId } = await params;
  const playerPath = `/player/${region}/${realm}/${name}`;
  const runPath = `${playerPath}/run/${runId}`;

  let run;
  try {
    run = await getRunDetail(region, realm, name, parseInt(runId, 10));
  } catch {
    return (
      <main className="mt-24 px-6 max-w-4xl mx-auto pb-32 text-center">
        <h2 className="font-[family-name:var(--font-headline)] text-5xl font-extrabold tracking-tighter text-on-surface mb-4">
          RUN NOT FOUND
        </h2>
        <Link
          href={playerPath}
          className="text-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest hover:underline"
        >
          Return to profile
        </Link>
      </main>
    );
  }

  const wclUrl = `https://www.warcraftlogs.com/reports/${run.wcl_report_id}?fight=${run.fight_id}`;
  const pulls = run.pulls ?? null;

  return (
    <main className="mt-24 px-6 max-w-4xl mx-auto pb-32 space-y-10">
      <header className="space-y-3">
        <Link
          href={runPath}
          className="text-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest hover:underline inline-flex items-center gap-1"
        >
          <span className="material-symbols-outlined text-sm">arrow_back</span>
          Back to run recap
        </Link>
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary">
          Full Breakdown
        </p>
        <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-4xl md:text-6xl tracking-tighter text-on-surface">
          {dungeonName(run.encounter_id)} +{run.keystone_level}
        </h1>
        <p className="text-on-surface-variant">
          Deeper per-run analysis. What&apos;s built and what&apos;s coming.
        </p>
      </header>

      {/* Today: direct WCL link */}
      <section className="bg-surface-container-low rounded-xl p-6 md:p-8 border-l-4 border-primary/60">
        <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary mb-2">
          Available now
        </p>
        <h2 className="font-[family-name:var(--font-headline)] font-bold text-2xl tracking-tighter text-on-surface mb-3">
          Open the raw log on Warcraft Logs
        </h2>
        <p className="text-on-surface-variant mb-5 text-sm">
          Until our own event timeline is built, the most complete view of
          this run is the source report on WCL. Opens in a new tab.
        </p>
        <a
          href={wclUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 bg-primary text-on-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest px-5 py-3 rounded-md hover:brightness-110 transition"
        >
          View on warcraftlogs.com
          <span className="material-symbols-outlined text-sm">open_in_new</span>
        </a>
        <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant/70 mt-4">
          Report {run.wcl_report_id} &middot; fight {run.fight_id}
        </p>
      </section>

      {/* Pull-by-pull breakdown — the whole point of this page */}
      {pulls && pulls.length > 0 && (
        <section className="space-y-4">
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary">
            Pull-by-Pull Breakdown
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-2xl md:text-3xl tracking-tighter text-on-surface">
            What happened, pull by pull
          </h2>
          <p className="text-on-surface-variant text-sm">
            {pulls.length} pulls tracked. Each one shows your kicks,
            the damage you took, and whether you died, aggregated so
            you can scan the whole dungeon in under a minute.
          </p>
          <ol className="space-y-3 pt-2">
            {pulls.map((p) => (
              <PullCard key={p.i} pull={p} />
            ))}
          </ol>
        </section>
      )}

      {/* Roadmap — shown as a fallback when Level B data isn't populated
          (low keystone, old run, or ingest hadn't stored pulls yet) */}
      {(!pulls || pulls.length === 0) && (
        <section className="space-y-4">
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-on-surface-variant">
            Coming soon
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-2xl md:text-3xl tracking-tighter text-on-surface">
            What we&apos;re building here
          </h2>
          <p className="text-on-surface-variant text-sm">
            No event timeline available for this run yet. Either it&apos;s
            below the +8 threshold we track, or it was ingested before this
            feature went live. Newer runs will populate automatically.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <RoadmapCard
              tier="Level B"
              title="Event Timeline"
              description="Top 10-15 events ordered by time — when you ate big damage, when you kicked critical casts, when you died. Read-it-in-30-seconds format for the moments that actually mattered."
              status="Populates on next re-ingest"
            />
            <RoadmapCard
              tier="Level C"
              title="AI Coach"
              description="Spec-aware, dungeon-aware prose that tells you exactly what to work on for your next key. Not a score — a conversation."
              status="After scoring is rock-solid"
            />
          </div>
        </section>
      )}
    </main>
  );
}

/**
 * One pull → one self-contained card with a header, verdict pill, and
 * aggregated per-ability event summaries. Rendering is dense so players
 * can scan the whole dungeon in ~30 seconds.
 */
function PullCard({ pull }: { pull: Pull }) {
  const duration = pull.end_t - pull.start_t;
  const verdict = VERDICT_CONFIG[pull.verdict];

  // Group events by (type, ability_id) so the card reads like prose
  // summaries instead of a raw log. One line per unique ability per type.
  const grouped = groupEvents(pull.events);

  return (
    <li
      className="bg-surface-container-low rounded-xl overflow-hidden border-l-4"
      style={{ borderLeftColor: verdict.color }}
    >
      {/* Header */}
      <div className="px-5 py-3 flex items-center justify-between gap-4 flex-wrap border-b border-outline-variant/10">
        <div className="flex items-baseline gap-3 min-w-0">
          <span className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-widest text-on-surface-variant tabular-nums">
            Pull {String(pull.i).padStart(2, "0")}
          </span>
          <span className="font-[family-name:var(--font-body)] font-semibold text-on-surface truncate">
            {pull.label}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs font-[family-name:var(--font-label)] uppercase tracking-widest">
          <span className="text-on-surface-variant/70 tabular-nums">
            {formatTime(pull.start_t)}–{formatTime(pull.end_t)}
            {" "}
            <span className="opacity-60">({Math.round(duration)}s)</span>
          </span>
          <span
            className="px-2.5 py-1 rounded font-bold"
            style={{ backgroundColor: `${verdict.color}20`, color: verdict.color }}
          >
            {verdict.label}
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="px-5 py-3 space-y-1">
        {grouped.length === 0 ? (
          <p className="text-xs text-on-surface-variant/60 italic">
            Nothing notable happened here.
          </p>
        ) : (
          grouped.map((g, i) => <EventSummaryLine key={i} summary={g} />)
        )}
      </div>
    </li>
  );
}

interface EventSummary {
  type: PullEventType;
  label: string;      // e.g. "Shadow Bolt", "Runic Glaive"
  count: number;
  total: number | null;  // total damage (sum); null for interrupts
}

/**
 * Group a pull's events by (type, ability). Deaths stay as individual
 * rows (rare enough to list each, and losing the timestamp would lose
 * too much). Damage and interrupts collapse into per-ability summaries.
 */
function groupEvents(events: PullEvent[]): EventSummary[] {
  const out: EventSummary[] = [];

  // Damage: one row per unique ability, sorted by total damage desc
  const dmgMap = new Map<number, EventSummary>();
  for (const ev of events) {
    if (ev.type !== "avoidable_damage") continue;
    const existing = dmgMap.get(ev.ability_id);
    if (existing) {
      existing.count += 1;
      existing.total = (existing.total ?? 0) + (ev.amount ?? 0);
    } else {
      dmgMap.set(ev.ability_id, {
        type: "avoidable_damage",
        label: ev.ability_name,
        count: 1,
        total: ev.amount ?? 0,
      });
    }
  }
  const dmgSorted = [...dmgMap.values()].sort(
    (a, b) => (b.total ?? 0) - (a.total ?? 0),
  );

  // Interrupts: one row per unique kicked ability
  const kickMap = new Map<number, EventSummary>();
  for (const ev of events) {
    if (ev.type !== "critical_interrupt") continue;
    const existing = kickMap.get(ev.ability_id);
    if (existing) existing.count += 1;
    else kickMap.set(ev.ability_id, {
      type: "critical_interrupt",
      label: ev.ability_name,
      count: 1,
      total: null,
    });
  }
  const kickSorted = [...kickMap.values()].sort((a, b) => b.count - a.count);

  // Deaths: one row per death (keep each separate)
  const deaths: EventSummary[] = events
    .filter((e) => e.type === "death")
    .map((ev) => ({
      type: "death" as const,
      label: ev.ability_name,
      count: 1,
      total: ev.amount,
    }));

  // Priority order: deaths first (most important), then damage (usually
  // larger impact than misses), then kicks (positive moments).
  out.push(...deaths, ...dmgSorted, ...kickSorted);
  return out;
}

function EventSummaryLine({ summary }: { summary: EventSummary }) {
  const color = EVENT_COLOR[summary.type];
  const sentence = buildSentence(summary);

  return (
    <p className="text-sm font-[family-name:var(--font-body)] text-on-surface/90 leading-relaxed flex gap-2.5 items-start">
      <span
        className="mt-1.5 w-1.5 h-1.5 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
      {sentence}
    </p>
  );
}

function buildSentence(s: EventSummary): string {
  switch (s.type) {
    case "death":
      return s.total
        ? `Died to ${s.label} — ${formatNumber(s.total)} damage.`
        : `Died to ${s.label}.`;
    case "avoidable_damage":
      return s.count === 1
        ? `Took ${formatNumber(s.total ?? 0)} from ${s.label}.`
        : `Took ${s.count} hits from ${s.label} (${formatNumber(s.total ?? 0)} total).`;
    case "critical_interrupt":
      return s.count === 1
        ? `Kicked ${s.label}.`
        : `Kicked ${s.label} ×${s.count}.`;
  }
}

const EVENT_COLOR: Record<PullEventType, string> = {
  avoidable_damage: "#fbbf24",
  critical_interrupt: "#22d3ee",
  death: "#f87171",
};

const VERDICT_CONFIG: Record<PullVerdict, { color: string; label: string }> = {
  clean: { color: "#34d399", label: "Clean" },
  took_hits: { color: "#fbbf24", label: "Took Hits" },
  wipe: { color: "#f87171", label: "Wipe" },
};

function formatTime(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function RoadmapCard({
  tier,
  title,
  description,
  status,
}: {
  tier: string;
  title: string;
  description: string;
  status: string;
}) {
  return (
    <div className="bg-surface-container-high rounded-xl p-5 border border-outline-variant/20">
      <div className="flex items-center justify-between mb-3">
        <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary bg-primary/10 px-2 py-1 rounded">
          {tier}
        </span>
        <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
          {status}
        </span>
      </div>
      <h3 className="font-[family-name:var(--font-headline)] font-bold text-xl text-on-surface mb-2 tracking-tight">
        {title}
      </h3>
      <p className="text-on-surface-variant text-sm leading-relaxed">
        {description}
      </p>
    </div>
  );
}
