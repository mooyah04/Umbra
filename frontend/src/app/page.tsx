import Link from "next/link";
import SearchBar from "@/components/SearchBar";
import { getStatsSummary, getTopPlayers, getLeaderboard } from "@/lib/api";
import { getGradeColor } from "@/lib/grades";
import { classIconUrl, specIconUrl } from "@/lib/wow-assets";
import { CLASS_COLORS, CLASS_NAMES } from "@/lib/utils";
import type { PlayerSearchResult } from "@/lib/types";

export const revalidate = 60;

export default async function Home() {
  // Parallel fetch so homepage renders in a single RTT to the API.
  const [stats, recent, topRanked] = await Promise.all([
    getStatsSummary().catch(() => null),
    getTopPlayers(8).catch(() => [] as PlayerSearchResult[]),
    getLeaderboard({ limit: 5 }).catch(() => [] as PlayerSearchResult[]),
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

      {/* ── Stats strip ── */}
      {stats && (
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16">
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
        </section>
      )}

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
            body="Drop the Umbra/ folder into Interface/AddOns. It auto-enables Advanced Combat Logging and toggles /combatlog on when your M+ key starts."
          />
          <StepCard
            num="02"
            title="Upload to Warcraft Logs"
            icon="cloud_upload"
            body="The official Warcraft Logs Uploader picks up your log file automatically. No extra steps — your logs are already feeding our data pipeline."
          />
          <StepCard
            num="03"
            title="Get your grade"
            icon="insights"
            body="Search any character on the homepage. We parse every run, score each category, and show you the raw numbers behind the grade — no black box."
          />
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
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {recent.map((p) => (
              <PlayerCard key={`${p.name}-${p.realm}`} player={p} />
            ))}
          </div>
        </section>
      )}

      {/* ── Top-ranked strip ── */}
      {topRanked.length > 0 && (
        <section className="mb-16">
          <div className="flex items-end justify-between mb-6 flex-wrap gap-4">
            <div>
              <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
                Top Performers
              </p>
              <h3 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
                LEADERBOARD
              </h3>
            </div>
            <Link
              href="/leaderboard"
              className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary hover:underline inline-flex items-center gap-1"
            >
              View full board
              <span className="material-symbols-outlined text-sm">arrow_forward</span>
            </Link>
          </div>
          <ul className="bg-surface-container-high rounded-xl divide-y divide-outline-variant/10 overflow-hidden">
            {topRanked.map((p) => (
              <LeaderboardRow key={`${p.region}-${p.realm}-${p.name}`} player={p} />
            ))}
          </ul>
        </section>
      )}

      {/* ── CTA row: about + addon ── */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
        <Link
          href="/about"
          className="bg-surface-container-high rounded-xl p-8 group hover:bg-surface-bright transition-colors relative overflow-hidden"
        >
          <span className="material-symbols-outlined absolute top-6 right-6 text-primary text-5xl opacity-20 group-hover:opacity-40 transition-opacity">
            verified
          </span>
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary mb-3">
            About Umbra
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
          href="/Umbra.zip"
          download="Umbra.zip"
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
            href="/Umbra.zip"
            download="Umbra.zip"
            className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors"
          >
            Download Addon
          </a>
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

function LeaderboardRow({ player }: { player: PlayerSearchResult }) {
  const classColor = CLASS_COLORS[player.class_id] ?? "#ffffff";
  const className = CLASS_NAMES[player.class_id] ?? "Unknown";
  const gradeColor = player.grade ? getGradeColor(player.grade) : "#9d9d9d";
  const href = `/player/${player.region.toLowerCase()}/${encodeURIComponent(
    player.realm,
  )}/${player.name}`;
  const composite =
    player.composite_score != null ? player.composite_score.toFixed(1) : null;

  return (
    <li>
      <Link
        href={href}
        className="flex items-center gap-4 px-5 py-3 hover:bg-surface-bright transition-colors"
      >
        <span className="font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-on-surface-variant w-8 text-right">
          #{player.rank ?? "—"}
        </span>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={player.avatar_url ?? classIconUrl(player.class_id)}
          alt={className}
          className="w-9 h-9 rounded-full object-cover"
        />
        <div className="flex-1 min-w-0">
          <p className="font-bold truncate" style={{ color: classColor }}>
            {player.name}
          </p>
          <p className="text-xs text-on-surface-variant truncate">
            {player.spec ? `${player.spec} ${className}` : className} ·{" "}
            {player.realm}-{player.region.toUpperCase()}
          </p>
        </div>
        {player.role && (
          <span className="hidden md:inline-block font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant bg-surface-container-lowest px-2 py-1 rounded">
            {player.role}
          </span>
        )}
        <div className="text-right flex items-baseline gap-3">
          {composite && (
            <span className="text-sm text-on-surface-variant hidden sm:inline">
              {composite}
            </span>
          )}
          <span
            className="font-[family-name:var(--font-headline)] font-extrabold text-2xl tracking-tighter w-12 text-right"
            style={{ color: gradeColor }}
          >
            {player.grade ?? "—"}
          </span>
        </div>
      </Link>
    </li>
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
