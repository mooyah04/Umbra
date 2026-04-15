import Link from "next/link";
import { getRunDetail } from "@/lib/api";
import { formatNumber, CLASS_COLORS, CLASS_NAMES } from "@/lib/utils";
import { classIdFromName, specIconUrl } from "@/lib/wow-assets";
import { dungeonName } from "@/lib/dungeons";
import type { PartyMember } from "@/lib/types";

interface Props {
  params: Promise<{ region: string; realm: string; name: string; runId: string }>;
}

export default async function RunDetailPage({ params }: Props) {
  const { region, realm, name, runId } = await params;
  const playerPath = `/player/${region}/${realm}/${name}`;

  let run;
  try {
    run = await getRunDetail(region, realm, name, parseInt(runId, 10));
  } catch {
    return (
      <div className="pt-24 pb-32 px-6 max-w-7xl mx-auto text-center">
        <h2 className="font-[family-name:var(--font-headline)] text-5xl font-extrabold tracking-tighter text-on-surface mb-4">
          RUN NOT FOUND
        </h2>
        <Link href={playerPath} className="text-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest hover:underline">
          Return to Profile
        </Link>
      </div>
    );
  }

  const date = new Date(run.logged_at).toLocaleString();
  const durationMin = Math.floor(run.duration / 60000);
  const durationSec = Math.floor((run.duration % 60000) / 1000);
  const cpm = run.duration > 0 ? ((run.casts_total / (run.duration / 60000))).toFixed(1) : "0";

  return (
    <main className="mt-24 px-6 max-w-7xl mx-auto space-y-12 pb-32">
      {/* Hero Banner */}
      <section className="relative w-full aspect-[21/9] md:aspect-[25/7] rounded-xl overflow-hidden bg-surface-container-high group">
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent z-10" />
        <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-secondary/10 opacity-50" />
        <div className="absolute bottom-8 left-8 z-20 space-y-2">
          <div className="flex items-center gap-3">
            <Link href={playerPath} className="text-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest hover:underline">
              &larr; {decodeURIComponent(name)}
            </Link>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="bg-primary text-on-primary font-black font-[family-name:var(--font-headline)] px-3 py-1 text-2xl italic tracking-tighter">
              +{run.keystone_level}
            </span>
            <h2 className="text-4xl md:text-6xl font-black font-[family-name:var(--font-headline)] tracking-tighter uppercase text-on-surface">
              {dungeonName(run.encounter_id)}
            </h2>
          </div>
          <p className="text-on-surface-variant font-[family-name:var(--font-label)] text-xs uppercase tracking-widest mt-1">
            {run.spec_name}
          </p>
          <div className="flex items-center gap-6 text-on-surface-variant font-[family-name:var(--font-label)] uppercase tracking-tighter text-sm">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-xs">timer</span>
              <span>
                {durationMin}:{durationSec.toString().padStart(2, "0")}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-xs">skull</span>
              <span className={run.deaths > 0 ? "text-error" : "text-primary"}>
                {run.deaths.toString().padStart(2, "0")} Deaths
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-xs">star</span>
              <span className={run.timed ? "text-primary" : "text-error"}>
                {run.timed ? "Timed" : "Depleted"}
              </span>
            </div>
            <span className="text-on-surface-variant/50">{date}</span>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* What Went Right */}
        <div className="md:col-span-7 bg-surface-container-high rounded-lg p-8 space-y-6">
          <div className="flex justify-between items-end">
            <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-2xl tracking-tighter uppercase text-primary italic">
              Performance Anchors
            </h3>
            <span className="font-[family-name:var(--font-label)] text-xs text-on-surface-variant tracking-widest opacity-50 uppercase">
              Strengths
            </span>
          </div>
          <div className="grid grid-cols-1 gap-4">
            <PerformanceRow
              icon="flash_on"
              iconColor="text-primary"
              iconBg="bg-primary/10"
              title="Interrupt Discipline"
              description={`${run.interrupts} total interrupts${run.critical_interrupts !== null ? `, ${run.critical_interrupts} critical kicks` : ""}`}
              value={run.interrupts >= 15 ? "Elite" : run.interrupts >= 8 ? "Good" : "Low"}
              valueColor={run.interrupts >= 15 ? "text-primary" : run.interrupts >= 8 ? "text-secondary" : "text-error"}
              subLabel="Kick Rate"
            />
            <PerformanceRow
              icon="security"
              iconColor="text-secondary"
              iconBg="bg-secondary/10"
              title="Survivability"
              description={`${run.deaths} deaths, ${formatNumber(run.avoidable_damage_taken)} avoidable damage taken`}
              value={run.deaths === 0 ? "Perfect" : run.deaths <= 1 ? "Clean" : "Risky"}
              valueColor={run.deaths === 0 ? "text-primary" : run.deaths <= 1 ? "text-secondary" : "text-error"}
              subLabel="Risk Index"
            />
            <PerformanceRow
              icon="local_fire_department"
              iconColor="text-on-primary-container"
              iconBg="bg-primary-container/30"
              title="Cooldown Management"
              description={`${Math.round(run.cooldown_usage_pct)}% of expected cooldowns used`}
              value={`${Math.round(run.cooldown_usage_pct)}%`}
              valueColor={run.cooldown_usage_pct >= 80 ? "text-primary" : "text-on-surface-variant"}
              subLabel="Usage Rate"
            />
            <PerformanceRow
              icon="speed"
              iconColor="text-secondary"
              iconBg="bg-secondary/10"
              title="Activity Level"
              description={`${cpm} casts per minute, ${formatNumber(run.casts_total)} total casts`}
              value={`${cpm} CPM`}
              valueColor="text-on-surface"
              subLabel="Rotation"
            />
          </div>
        </div>

        {/* What Went Wrong / Death Log */}
        <div className="md:col-span-5 bg-surface-container-high rounded-lg p-8 space-y-6">
          <div className="flex justify-between items-end">
            <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-2xl tracking-tighter uppercase text-error italic">
              Risk Analysis
            </h3>
            <div className="flex gap-1">
              {Array.from({ length: Math.min(run.deaths, 5) }).map((_, i) => (
                <span key={i} className="w-2 h-2 rounded-full bg-error" />
              ))}
              {Array.from({ length: Math.max(0, 3 - Math.min(run.deaths, 5)) }).map((_, i) => (
                <span key={`empty-${i}`} className="w-2 h-2 rounded-full bg-error/30" />
              ))}
            </div>
          </div>
          <div className="space-y-4">
            {run.deaths > 0 ? (
              <>
                <div className="flex gap-4 items-start p-4 bg-surface-container-low/50 rounded border-l-2 border-error">
                  <span className="font-[family-name:var(--font-label)] text-xs text-error font-bold mt-1">
                    {run.deaths}x
                  </span>
                  <div>
                    <p className="font-bold text-on-surface font-[family-name:var(--font-body)]">
                      Deaths Recorded
                    </p>
                    <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                      {run.avoidable_deaths !== null && run.avoidable_deaths > 0
                        ? `${run.avoidable_deaths} of ${run.deaths} deaths were from avoidable mechanics.`
                        : "Death details require avoidable ability data to classify."}
                    </p>
                  </div>
                </div>
                {run.avoidable_damage_taken > 0 && (
                  <div className="p-4 bg-error-container/20 rounded border border-error/20 flex gap-3">
                    <span className="material-symbols-outlined text-error text-xl">warning</span>
                    <p className="text-xs font-[family-name:var(--font-body)] text-on-surface-variant">
                      Took <span className="font-bold text-error">{formatNumber(run.avoidable_damage_taken)}</span> avoidable damage
                      ({run.damage_taken_total > 0
                        ? `${Math.round((run.avoidable_damage_taken / run.damage_taken_total) * 100)}% of total`
                        : "N/A"}).
                    </p>
                  </div>
                )}
              </>
            ) : (
              <div className="flex gap-4 items-start p-4 bg-primary/5 rounded border-l-2 border-primary">
                <span className="material-symbols-outlined text-primary">verified</span>
                <div>
                  <p className="font-bold text-on-surface font-[family-name:var(--font-body)]">Zero Deaths</p>
                  <p className="text-xs text-on-surface-variant mt-1">Clean run with no fatalities.</p>
                </div>
              </div>
            )}

            {/* Damage breakdown */}
            <div className="pt-4 space-y-3">
              <h4 className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
                Damage Profile
              </h4>
              <DetailRow label="Total Damage Taken" value={formatNumber(run.damage_taken_total)} />
              <DetailRow label="Avoidable Damage" value={formatNumber(run.avoidable_damage_taken)} />
              {run.healing_received !== null && (
                <DetailRow label="Healing Received" value={formatNumber(run.healing_received)} />
              )}
            </div>
          </div>
        </div>

        {/* Party Composition */}
        {run.party_comp && run.party_comp.length > 0 && (
          <div className="md:col-span-12 bg-surface-container-high rounded-lg p-8">
            <div className="flex items-end justify-between mb-6">
              <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-2xl tracking-tighter uppercase text-on-surface italic">
                Team Composition
              </h3>
              <span className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant tracking-widest uppercase">
                {run.party_comp.length} players
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              {run.party_comp.map((member) => (
                <PartyCard
                  key={`${member.name}-${member.realm}`}
                  member={member}
                  region={region}
                />
              ))}
            </div>
          </div>
        )}

        {/* Stats Bar */}
        <div className="md:col-span-12 bg-surface-container-high rounded-lg p-8">
          <h3 className="font-[family-name:var(--font-headline)] font-extrabold text-2xl tracking-tighter uppercase text-on-surface italic mb-6">
            Full Stat Sheet
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-6">
            <StatTile label="DPS %" value={`${run.dps.toFixed(1)}`} sub="Percentile" />
            {run.hps > 0 && <StatTile label="HPS %" value={`${run.hps.toFixed(1)}`} sub="Percentile" />}
            <StatTile label="iLvl" value={run.ilvl.toFixed(0)} sub="Item Level" />
            <StatTile label="Dispels" value={run.dispels.toString()} sub="Cleanses" />
            {run.cc_casts !== null && <StatTile label="CC" value={run.cc_casts.toString()} sub="Applications" />}
            {run.rating !== null && <StatTile label="Rating" value={run.rating.toString()} sub="Blizzard M+" />}
            {run.average_item_level !== null && <StatTile label="Group iLvl" value={run.average_item_level.toFixed(0)} sub="Average" />}
          </div>
        </div>
      </div>
    </main>
  );
}

function PerformanceRow({
  icon, iconColor, iconBg, title, description, value, valueColor, subLabel,
}: {
  icon: string; iconColor: string; iconBg: string;
  title: string; description: string;
  value: string; valueColor: string; subLabel: string;
}) {
  return (
    <div className="bg-surface-container-highest p-5 rounded-md flex justify-between items-center hover:bg-surface-bright transition-colors">
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 rounded ${iconBg} flex items-center justify-center ${iconColor}`}>
          <span className="material-symbols-outlined">{icon}</span>
        </div>
        <div>
          <p className="text-on-surface font-bold text-lg tracking-tight">{title}</p>
          <p className="text-on-surface-variant text-xs font-[family-name:var(--font-body)]">{description}</p>
        </div>
      </div>
      <div className="text-right">
        <p className={`font-[family-name:var(--font-label)] text-xl font-bold ${valueColor}`}>{value}</p>
        <p className="text-[10px] font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant">{subLabel}</p>
      </div>
    </div>
  );
}

function StatTile({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="text-center">
      <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mb-2">{label}</p>
      <p className="font-[family-name:var(--font-headline)] text-3xl font-bold text-on-surface">{value}</p>
      <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase mt-1">{sub}</p>
    </div>
  );
}

function PartyCard({
  member,
  region,
}: {
  member: PartyMember;
  region: string;
}) {
  const classId = classIdFromName(member.class);
  const classColor = classId ? CLASS_COLORS[classId] ?? "#ffffff" : "#9d9d9d";
  const className = classId ? CLASS_NAMES[classId] ?? member.class : member.class;
  const icon = classId ? specIconUrl(member.spec, classId) : null;
  const roleLabel = {
    tank: "Tank",
    healer: "Healer",
    dps: "DPS",
  }[member.role] ?? member.role.toUpperCase();

  // Link to the player page if their realm + name look sane. If realm is
  // unknown we just render a non-clickable card.
  const hasProfileLink = !!member.realm && !!member.name;
  const href = hasProfileLink
    ? `/player/${region.toLowerCase()}/${encodeURIComponent(
        member.realm,
      )}/${member.name}`
    : "#";

  const content = (
    <div
      className="bg-surface-container-highest rounded-lg p-3 border-l-2 flex items-center gap-3 hover:bg-surface-bright transition-colors"
      style={{ borderColor: classColor }}
    >
      {icon ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={icon}
          alt={`${member.spec ?? className}`}
          width={36}
          height={36}
          className="rounded flex-shrink-0"
          style={{ boxShadow: `0 0 0 1px ${classColor}60` }}
        />
      ) : (
        <div className="w-9 h-9 rounded bg-surface-container flex-shrink-0" />
      )}
      <div className="min-w-0">
        <p className="font-[family-name:var(--font-body)] font-semibold text-on-surface text-sm truncate">
          {member.name}
        </p>
        <p
          className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest truncate"
          style={{ color: classColor }}
        >
          {member.spec ?? ""} {className}
        </p>
        <p className="font-[family-name:var(--font-label)] text-[9px] uppercase tracking-widest text-on-surface-variant mt-0.5 truncate">
          {roleLabel} &middot; {member.realm}
        </p>
      </div>
    </div>
  );

  return hasProfileLink ? (
    <Link href={href} className="block">
      {content}
    </Link>
  ) : (
    content
  );
}


function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-on-surface-variant text-sm">{label}</span>
      <span className="text-on-surface text-sm font-medium">{value}</span>
    </div>
  );
}
