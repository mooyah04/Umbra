import Link from "next/link";
import { getRunDetail } from "@/lib/api";
import { dungeonName } from "@/lib/dungeons";

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

      {/* Roadmap */}
      <section className="space-y-4">
        <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-on-surface-variant">
          Coming soon
        </p>
        <h2 className="font-[family-name:var(--font-headline)] font-bold text-2xl md:text-3xl tracking-tighter text-on-surface">
          What we&apos;re building here
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <RoadmapCard
            tier="Level B"
            title="Event Timeline"
            description="Top 10-15 events ordered by time — when you ate big damage, when you kicked critical casts, when you died. Read-it-in-30-seconds format for the moments that actually mattered."
            status="In design"
          />
          <RoadmapCard
            tier="Level C"
            title="AI Coach"
            description="Spec-aware, dungeon-aware prose that tells you exactly what to work on for your next key. Not a score — a conversation."
            status="After scoring is rock-solid"
          />
        </div>
      </section>
    </main>
  );
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
