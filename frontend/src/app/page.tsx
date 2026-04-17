import Link from "next/link";
import SearchBar from "@/components/SearchBar";
import RecentlyGradedCarousel from "@/components/RecentlyGradedCarousel";
import { ADDON_DOWNLOAD_URL, getStatsSummary, getTopPlayers } from "@/lib/api";
import { getGradeColor } from "@/lib/grades";
import { specIconUrl } from "@/lib/wow-assets";
import { CLASS_COLORS, CLASS_NAMES } from "@/lib/utils";
import type { PlayerSearchResult } from "@/lib/types";

// Short page-level ISR so the homepage's stats + carousel + testimonials
// don't serve multi-minute-old content on the first visit after a
// cache-miss. Individual `getTopPlayers` / `getStatsSummary` calls also
// have their own revalidate windows in lib/api.ts.
export const revalidate = 15;

export default async function Home() {
  const [stats, recent] = await Promise.all([
    getStatsSummary().catch(() => null),
    getTopPlayers(12).catch(() => [] as PlayerSearchResult[]),
  ]);

  return (
    <div className="min-h-screen pt-32 pb-24 px-6 md:px-12 max-w-7xl mx-auto">
      {/* ── Hero ── */}
      <section className="flex flex-col items-center justify-center text-center mb-12">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-6">
          Mythic+ Performance Grading
        </p>
        <h2 className="font-[family-name:var(--font-headline)] font-extrabold text-5xl md:text-7xl lg:text-8xl tracking-tighter mb-8 text-on-surface">
          LOOK UP <span className="text-primary italic">ANY PLAYER.</span>
        </h2>
        <p className="max-w-2xl text-on-surface-variant text-lg mb-8">
          One composite grade per character — built from your combat-log
          evidence, tuned for the current season, and explained piece by piece.
        </p>
        <SearchBar />
        <a
          href={ADDON_DOWNLOAD_URL}
          className="md:hidden mt-5 inline-flex items-center gap-2 bg-primary text-on-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest px-5 py-3 rounded hover:brightness-110 transition-all"
        >
          <span className="material-symbols-outlined text-sm">download</span>
          Download Addon
        </a>
        <p className="mt-6 font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.2em] text-on-surface-variant">
          Indexed:{" "}
          <span className="text-primary">
            {stats?.total_players.toLocaleString() ?? "—"}
          </span>{" "}
          characters
          {" • "}
          <span className="text-secondary">
            {stats?.total_runs.toLocaleString() ?? "—"}
          </span>{" "}
          runs
          {" • "}
          <span className="text-tertiary">
            {stats?.graded_players.toLocaleString() ?? "—"}
          </span>{" "}
          graded
        </p>
      </section>

      {/* ── Stats strip ─ 3 role counts on row 1, 2 totals centered on
           row 2. Shape picked so the three roles read as one unit and
           the totals sit underneath as context rather than competing. */}
      {stats && (
        <section className="mb-16 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatTile
              label="Tanks Graded"
              value={(stats.role_counts.tank ?? 0).toString()}
              icon="shield"
              color="tertiary"
            />
            <StatTile
              label="Healers Graded"
              value={(stats.role_counts.healer ?? 0).toString()}
              icon="healing"
              color="primary"
            />
            <StatTile
              label="DPS Graded"
              value={(stats.role_counts.dps ?? 0).toString()}
              icon="swords"
              color="secondary"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl mx-auto">
            <StatTile
              label="Total Characters"
              value={stats.total_players.toLocaleString()}
              icon="group"
              color="primary"
            />
            <StatTile
              label="Runs Parsed"
              value={stats.total_runs.toLocaleString()}
              icon="fort"
              color="secondary"
            />
          </div>
        </section>
      )}

      {/* ── Tester call-to-action ────────────────────────────────────────
           Scoring calibrates from real-log diversity, so the fastest way to
           make grades accurate for every class/spec is simply to have more
           people running keys with the addon installed. */}
      <section className="mb-16">
        <div className="relative bg-gradient-to-br from-primary-container/60 via-surface-container-high to-surface-container-high border border-primary/30 rounded-xl p-8 md:p-10 overflow-hidden">
          <span className="material-symbols-outlined absolute top-6 right-6 text-primary text-6xl opacity-15 pointer-events-none">
            rocket_launch
          </span>
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-3">
            Early Access
          </p>
          <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-3xl md:text-5xl tracking-tighter text-on-surface mb-4">
            WE NEED <span className="text-primary italic">TESTERS</span>
          </h3>
          <p className="text-on-surface-variant leading-relaxed max-w-3xl mb-6">
            WoWUmbra.gg is brand new. The grading system learns from the logs
            our community feeds it — the more diverse the keys, specs, and
            compositions we see, the sharper every category gets. If you run
            Mythic+, drop the addon in and play normally. That&apos;s it. Your
            logs help tune benchmarks that will grade every player who comes
            after you.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <a
              href={ADDON_DOWNLOAD_URL}
              className="bg-primary text-on-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest px-5 py-3 rounded hover:brightness-110 transition-all inline-flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">download</span>
              Download Addon
            </a>
            <Link
              href="/methodology"
              className="font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-primary hover:underline inline-flex items-center gap-1"
            >
              How the grading works
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="mb-16">
        <div className="mb-8">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            Getting Started
          </p>
          <h3 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            HOW IT WORKS
          </h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StepCard
            num="01"
            title="Install the addon"
            icon="extension"
            body="Drop the Umbra/ folder into Interface/AddOns. It auto-enables Advanced Combat Logging and toggles /combatlog on when your M+ key starts — you don't have to remember."
          />
          <StepCard
            num="02"
            title="Upload to Warcraft Logs"
            icon="cloud_upload"
            body="Run the official Warcraft Logs Uploader alongside WoW. It watches your combatlog folder and uploads every M+ key automatically — that's what we read from."
          />
          <StepCard
            num="03"
            title="Search yourself here"
            icon="insights"
            body="Search your character on the homepage. We pull your logs from Warcraft Logs, score every category, and show the raw numbers behind the grade. First look-up takes a few seconds — after that it's cached."
          />
        </div>
        <div className="mt-6 bg-surface-container-high rounded-xl p-5 border-l-2 border-primary/40">
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.2em] text-primary mb-2">
            Player-driven scoring
          </p>
          <p className="text-on-surface-variant text-sm leading-relaxed">
            We grade characters on demand — not by scraping Warcraft Logs at
            scale. If you want your grade to appear,{" "}
            <span className="text-on-surface">install the addon and run your keys</span>{" "}
            (your logs will be there already, via the standard WCL Uploader),
            then search yourself. That&apos;s the whole flow.
          </p>
        </div>
      </section>

      {/* ── Recently graded showcase ── */}
      {recent.length > 0 && (
        <section className="mb-16">
          <div className="flex items-end justify-between mb-6">
            <div>
              <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
                Fresh Data
              </p>
              <h3 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
                RECENTLY GRADED
              </h3>
            </div>
            <span className="font-[family-name:var(--font-label)] text-[10px] text-primary bg-primary/10 border border-primary/20 px-3 py-1 rounded uppercase tracking-widest">
              Live
            </span>
          </div>
          <RecentlyGradedCarousel>
            {recent.map((p) => (
              <PlayerCard key={`${p.name}-${p.realm}`} player={p} />
            ))}
          </RecentlyGradedCarousel>
        </section>
      )}

      {/* ── Testimonial / "grades speak for themselves" ──
           Anonymized real-data examples. Players are not named. The goal
           is to show that the grade and the underlying stats tell the
           same story — low grades come with low numbers, high grades
           come with high numbers. The addon is the product; this
           section exists to make people feel comfortable trying it. */}
      <section className="mb-16">
        <div className="mb-8">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            The Data Speaks For Itself
          </p>
          <h3 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            GRADES MATCH <span className="text-primary italic">REALITY</span>
          </h3>
          <p className="text-on-surface-variant mt-3 max-w-3xl leading-relaxed">
            Every grade is a summary of the log evidence — nothing more, nothing
            less. Three anonymized examples from our live dataset. Names and
            realms stripped; the numbers are real.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <TestimonialCard
            grade="F"
            role="DPS"
            roleDescriptor="A Hunter"
            summary="Low damage output, barely any utility, dying repeatedly to mechanics they should've sidestepped."
            stats={[
              { label: "DPS percentile", value: "8th" },
              { label: "Interrupts / dungeon", value: "1.2" },
              { label: "Deaths across 18 runs", value: "41" },
              { label: "Avoidable damage taken", value: "97th pct (worst)" },
            ]}
          />
          <TestimonialCard
            grade="D"
            role="Healer"
            roleDescriptor="A Resto Shaman"
            summary="Throughput OK, but dispels missed, CDs unused, and survivability below the average for their key level."
            stats={[
              { label: "HPS percentile", value: "52nd" },
              { label: "Dispels / dungeon", value: "3.1" },
              { label: "Major CD usage", value: "38%" },
              { label: "Deaths / run", value: "2.4" },
            ]}
          />
          <TestimonialCard
            grade="S"
            role="Tank"
            roleDescriptor="A Prot Paladin"
            summary="High survivability, generous utility, and crucially — pushes high keys in time. Every category lights up."
            stats={[
              { label: "Key level range", value: "+11 to +14" },
              { label: "Interrupts / dungeon", value: "11.7" },
              { label: "Timing rate", value: "88% in time" },
              { label: "Avoidable damage", value: "9th pct (best)" },
            ]}
          />
        </div>
        <p className="text-on-surface-variant/70 text-xs mt-6 max-w-3xl italic">
          No cherry-picking, no shaming. Pulled from the real distribution of
          graded players. Install the addon, run your keys, and find out what
          the data says about you.
        </p>
      </section>

      {/* ── CTA row: about + addon ── */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
        <Link
          href="/methodology"
          className="bg-surface-container-high rounded-xl p-8 group hover:bg-surface-bright transition-colors relative overflow-hidden"
        >
          <span className="material-symbols-outlined absolute top-6 right-6 text-primary text-5xl opacity-20 group-hover:opacity-40 transition-opacity">
            verified
          </span>
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary mb-3">
            Methodology
          </p>
          <h4 className="font-[family-name:var(--font-headline)] font-bold text-3xl tracking-tighter text-on-surface mb-3">
            FAIR GRADES,{" "}
            <span className="text-primary italic">FULL TRANSPARENCY</span>
          </h4>
          <p className="text-on-surface-variant leading-relaxed mb-4">
            Why we weight tanks differently from DPS. Why talent-gated CDs
            aren&apos;t scored. How the composite actually gets computed.
          </p>
          <span className="inline-flex items-center gap-2 font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary">
            Read the methodology
            <span className="material-symbols-outlined text-sm">
              arrow_forward
            </span>
          </span>
        </Link>

        <a
          href={ADDON_DOWNLOAD_URL}
          className="bg-gradient-to-br from-primary-container to-surface-container-highest rounded-xl p-8 group relative overflow-hidden"
        >
          <span className="material-symbols-outlined absolute top-6 right-6 text-primary text-5xl opacity-20 group-hover:opacity-40 transition-opacity">
            extension
          </span>
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary mb-3">
            WoW Addon
          </p>
          <h4 className="font-[family-name:var(--font-headline)] font-bold text-3xl tracking-tighter text-on-primary-container mb-3">
            IN-GAME GRADE{" "}
            <span className="text-primary italic">TOOLTIPS</span>
          </h4>
          <p className="text-on-primary-container/80 leading-relaxed mb-4">
            Hover any player in-game or in the Group Finder to see their
            Umbra grade, role, and category breakdown. Auto combat-logs
            your M+ keys. Plays nicely with Raider.IO.
          </p>
          <span className="inline-flex items-center gap-2 font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary">
            Download Umbra.zip
            <span className="material-symbols-outlined text-sm">
              download
            </span>
          </span>
          <p className="font-[family-name:var(--font-label)] text-[10px] text-on-primary-container/60 mt-3">
            Unzip into World of Warcraft/_retail_/Interface/AddOns/
          </p>
        </a>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-outline-variant/10 pt-8 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_#8a2be2]" />
            <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
              Midnight Season 1
            </span>
          </div>
          <Link
            href="/about"
            className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors"
          >
            About
          </Link>
          <a
            href={ADDON_DOWNLOAD_URL}
            className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors"
          >
            Download Addon
          </a>
          <Link
            href="/changelog"
            className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors"
          >
            Changelog
          </Link>
          <Link
            href="/bug-report"
            className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors"
          >
            Report a Bug
          </Link>
        </div>
        <div className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-[0.3em]">
          WoWUmbra.gg © 2026
        </div>
      </footer>
    </div>
  );
}

function StatTile({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string;
  icon: string;
  color: "primary" | "secondary" | "tertiary";
}) {
  const tint = {
    primary: "text-primary border-primary/30",
    secondary: "text-secondary border-secondary/30",
    tertiary: "text-tertiary border-tertiary/30",
  }[color];
  return (
    <div className={`bg-surface-container rounded-xl p-5 border-l-2 ${tint}`}>
      <div className="flex items-center gap-3 mb-2">
        <span className={`material-symbols-outlined ${tint.split(" ")[0]}`}>
          {icon}
        </span>
        <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
          {label}
        </p>
      </div>
      <p className="font-[family-name:var(--font-headline)] font-black text-3xl text-on-surface tracking-tighter">
        {value}
      </p>
    </div>
  );
}

function StepCard({
  num,
  title,
  icon,
  body,
}: {
  num: string;
  title: string;
  icon: string;
  body: string;
}) {
  return (
    <div className="bg-surface-container-high rounded-xl p-6 relative overflow-hidden">
      <span className="font-[family-name:var(--font-headline)] font-black text-[5rem] leading-none text-primary/10 absolute -top-2 -right-2">
        {num}
      </span>
      <span className="material-symbols-outlined text-primary text-3xl mb-4 relative">
        {icon}
      </span>
      <h4 className="font-[family-name:var(--font-headline)] font-bold text-xl text-on-surface mb-2 tracking-tight relative">
        {title}
      </h4>
      <p className="text-on-surface-variant leading-relaxed relative">{body}</p>
    </div>
  );
}

function TestimonialCard({
  grade,
  role,
  roleDescriptor,
  summary,
  stats,
}: {
  grade: string;
  role: string;
  roleDescriptor: string;
  summary: string;
  stats: Array<{ label: string; value: string }>;
}) {
  const gradeColor = getGradeColor(grade);
  return (
    <div className="bg-surface-container-high rounded-xl p-6 relative overflow-hidden flex flex-col">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">
            {role}
          </p>
          <h4 className="font-[family-name:var(--font-headline)] font-bold text-xl text-on-surface tracking-tight mt-1">
            {roleDescriptor}
          </h4>
        </div>
        <span
          className="font-[family-name:var(--font-headline)] font-black text-5xl leading-none tracking-tighter"
          style={{
            color: gradeColor,
            textShadow: `0 0 14px ${gradeColor}55`,
          }}
        >
          {grade}
        </span>
      </div>
      <p className="text-on-surface-variant text-sm leading-relaxed mb-4">
        {summary}
      </p>
      <ul className="space-y-2 mt-auto">
        {stats.map((s) => (
          <li
            key={s.label}
            className="flex items-center justify-between text-xs border-t border-outline-variant/10 pt-2"
          >
            <span className="font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant">
              {s.label}
            </span>
            <span className="font-mono text-on-surface">{s.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function PlayerCard({ player }: { player: PlayerSearchResult }) {
  const classColor = CLASS_COLORS[player.class_id] ?? "#ffffff";
  const className = CLASS_NAMES[player.class_id] ?? "Unknown";
  const gradeColor = player.grade
    ? getGradeColor(player.grade)
    : "#9d9d9d";
  const href = `/player/${player.region.toLowerCase()}/${encodeURIComponent(
    player.realm,
  )}/${player.name}`;

  return (
    <Link
      href={href}
      className="bg-surface-container-high rounded-xl overflow-hidden group hover:bg-surface-bright transition-colors relative"
    >
      <div
        className="h-1"
        style={{ backgroundColor: classColor }}
      />
      <div className="p-5">
        <div className="flex items-start gap-3 mb-4">
          {/* Real avatar if Blizzard has one, else spec icon */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={player.avatar_url ?? specIconUrl(player.spec, player.class_id)}
            alt={player.spec ?? className}
            width={44}
            height={44}
            className="rounded-md border-2"
            style={{ borderColor: `${classColor}60` }}
          />
          <div className="flex-1 min-w-0">
            <h4 className="font-[family-name:var(--font-body)] font-bold text-on-surface truncate">
              {player.name}
            </h4>
            <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-widest truncate">
              {player.realm} • {player.region}
            </p>
          </div>
          {player.grade && (
            <span
              className="font-[family-name:var(--font-headline)] font-black text-2xl leading-none"
              style={{
                color: gradeColor,
                textShadow: `0 0 8px ${gradeColor}60`,
              }}
            >
              {player.grade}
            </span>
          )}
        </div>
        <div className="flex items-center justify-between text-[10px] font-[family-name:var(--font-label)] uppercase tracking-widest">
          <span style={{ color: classColor }}>
            {player.spec ?? "—"} {className}
          </span>
          <span className="text-on-surface-variant">
            {player.role ?? ""}
            {player.runs_analyzed ? ` • ${player.runs_analyzed}r` : ""}
          </span>
        </div>
      </div>
    </Link>
  );
}
