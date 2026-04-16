import Link from "next/link";
import { getRunDetail } from "@/lib/api";
import { dungeonName } from "@/lib/dungeons";
import { formatNumber } from "@/lib/utils";
import type { TimelineEvent } from "@/lib/types";

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
  const timeline = run.timeline_events ?? null;

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
          Deeper per-run analysis — what&apos;s built and what&apos;s coming.
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

      {/* Event timeline — shown when Level B data is populated */}
      {timeline && timeline.length > 0 && (
        <section className="space-y-4">
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary">
            Event Timeline
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-2xl md:text-3xl tracking-tighter text-on-surface">
            The moments that mattered
          </h2>
          <p className="text-on-surface-variant text-sm">
            Chronological recap of the {timeline.length} most-impactful
            moments in this run.
          </p>
          <ol className="space-y-1 pt-2 bg-surface-container-low rounded-xl p-5 md:p-6">
            {timeline.map((ev, i) => (
              <TimelineSentence key={i} event={ev} />
            ))}
          </ol>
        </section>
      )}

      {/* Roadmap — shown as a fallback when Level B data isn't populated
          (low keystone, old run, or ingest hadn't stored timeline yet) */}
      {(!timeline || timeline.length === 0) && (
        <section className="space-y-4">
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-on-surface-variant">
            Coming soon
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-2xl md:text-3xl tracking-tighter text-on-surface">
            What we&apos;re building here
          </h2>
          <p className="text-on-surface-variant text-sm">
            No event timeline available for this run yet — either it&apos;s
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
 * One event → one plain-English sentence with a timestamp prefix.
 * Rendered as a flowing list of lines, not data rows, so the page
 * reads as a recap rather than a spreadsheet.
 */
function TimelineSentence({ event }: { event: TimelineEvent }) {
  const time = formatTime(event.t);
  const color = TYPE_COLOR[event.type];
  const ability = event.ability_name || "an unknown ability";
  const amount = event.amount && event.amount > 0 ? formatNumber(event.amount) : null;

  let sentence: string;
  switch (event.type) {
    case "death":
      sentence = amount
        ? `Died to ${ability} — ${amount} damage.`
        : `Died to ${ability}.`;
      break;
    case "avoidable_damage":
      sentence = amount
        ? `Took ${amount} from ${ability} — avoidable.`
        : `Took avoidable damage from ${ability}.`;
      break;
    case "critical_interrupt":
      sentence = `Kicked ${ability}.`;
      break;
    default:
      sentence = ability;
  }

  return (
    <li className="flex gap-4 py-1.5 leading-relaxed">
      <span
        className="font-[family-name:var(--font-label)] text-xs text-on-surface-variant/70 tabular-nums shrink-0 w-14 pt-0.5"
      >
        {time}
      </span>
      <span
        className="font-[family-name:var(--font-body)] text-on-surface"
        style={{ borderLeft: `2px solid ${color}`, paddingLeft: "0.75rem" }}
      >
        {sentence}
      </span>
    </li>
  );
}

const TYPE_COLOR: Record<TimelineEvent["type"], string> = {
  avoidable_damage: "#fbbf24",
  critical_interrupt: "#22d3ee",
  death: "#f87171",
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
