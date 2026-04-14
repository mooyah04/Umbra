"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getPlayerHistory } from "@/lib/api";
import type { HistoryResponse } from "@/lib/types";

type Period = "week" | "month" | "season";

export default function ProgressPage() {
  const params = useParams<{ region: string; realm: string; name: string }>();
  const [period, setPeriod] = useState<Period>("season");
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const { region, realm, name } = params;
  const playerPath = `/player/${region}/${realm}/${name}`;

  useEffect(() => {
    setLoading(true);
    getPlayerHistory(region, realm, name, period)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [region, realm, name, period]);

  const totalRuns = data?.points.reduce((s, p) => s + p.runs_count, 0) ?? 0;
  const totalTimed = data?.points.reduce((s, p) => s + p.timed_count, 0) ?? 0;
  const avgKey = totalRuns > 0
    ? (data!.points.reduce((s, p) => s + p.avg_keystone_level * p.runs_count, 0) / totalRuns)
    : 0;
  const avgDeaths = totalRuns > 0
    ? (data!.points.reduce((s, p) => s + p.avg_deaths * p.runs_count, 0) / totalRuns)
    : 0;
  const successRate = totalRuns > 0 ? Math.round((totalTimed / totalRuns) * 100) : 0;

  return (
    <main className="pt-24 pb-32 px-6 max-w-7xl mx-auto space-y-8">
      {/* Hero Section */}
      <section className="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-outline-variant/10 pb-8">
        <div className="space-y-1">
          <Link href={playerPath} className="font-[family-name:var(--font-label)] text-primary uppercase tracking-[0.3em] text-xs font-bold hover:underline">
            &larr; {decodeURIComponent(name)}
          </Link>
          <p className="font-[family-name:var(--font-label)] text-primary uppercase tracking-[0.3em] text-xs font-bold">
            Season 02 // Performance Monitor
          </p>
          <h2 className="font-[family-name:var(--font-headline)] text-5xl md:text-7xl font-extrabold tracking-tighter text-on-surface">
            TRENDS
          </h2>
        </div>
        {!loading && data && totalRuns > 0 && (
          <div className="flex flex-col items-start md:items-end gap-2">
            <div className="font-[family-name:var(--font-label)] text-4xl font-bold text-primary">
              {totalRuns}
              <span className="text-xs uppercase text-on-surface-variant tracking-widest ml-2">Runs</span>
            </div>
            <div className="px-3 py-1 bg-primary-container text-on-primary-container font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest rounded-sm">
              {successRate}% Success Rate
            </div>
          </div>
        )}
      </section>

      {loading ? (
        <div className="text-on-surface-variant py-20 text-center font-[family-name:var(--font-label)] text-xs uppercase tracking-widest">
          Loading analytics...
        </div>
      ) : !data || data.points.length === 0 ? (
        <div className="text-on-surface-variant py-20 text-center font-[family-name:var(--font-label)] text-xs uppercase tracking-widest">
          No data for this period.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Main Chart Area */}
          <div className="md:col-span-8 bg-surface-container-high rounded-lg p-6 relative overflow-hidden">
            <div className="flex justify-between items-center mb-12">
              <div>
                <h3 className="font-[family-name:var(--font-headline)] font-bold text-lg text-on-surface">Activity Progression</h3>
                <p className="font-[family-name:var(--font-label)] text-xs text-on-surface-variant uppercase tracking-widest">
                  Runs per day
                </p>
              </div>
              <div className="flex gap-2">
                {(["week", "month", "season"] as Period[]).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPeriod(p)}
                    className={`px-4 py-2 font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest transition-all ${
                      period === p
                        ? "bg-primary text-on-primary"
                        : "bg-surface-container-highest text-on-surface-variant hover:bg-surface-bright"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            {/* Bar chart */}
            <div className="h-48 flex items-end gap-[2px]">
              {data.points.map((point, i) => {
                const maxRuns = Math.max(...data.points.map((p) => p.runs_count), 1);
                const height = (point.runs_count / maxRuns) * 100;
                const opacity = 0.3 + (height / 100) * 0.7;
                return (
                  <div
                    key={point.date}
                    className="flex-1 rounded-t-sm transition-all hover:opacity-100 cursor-pointer group relative"
                    style={{
                      height: `${Math.max(4, height)}%`,
                      backgroundColor: `rgba(138, 43, 226, ${opacity})`,
                    }}
                    title={`${point.date}: ${point.runs_count} runs`}
                  />
                );
              })}
            </div>
            <div className="flex justify-between mt-4 font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-tighter">
              <span>{data.points[0]?.date}</span>
              <span>{data.points[data.points.length - 1]?.date}</span>
            </div>
          </div>

          {/* Growth Index */}
          <div className="md:col-span-4 bg-surface-container-high rounded-lg p-6 flex flex-col justify-between">
            <div>
              <h3 className="font-[family-name:var(--font-headline)] font-bold text-lg text-on-surface mb-1">Key Level</h3>
              <p className="font-[family-name:var(--font-label)] text-xs text-on-surface-variant uppercase tracking-widest">Average Keystone</p>
            </div>
            <div className="py-8 text-center">
              <div className="text-7xl font-[family-name:var(--font-headline)] font-black text-on-surface tracking-tighter">
                +{Math.floor(avgKey)}
                <span className="text-xl text-primary">.{Math.round((avgKey % 1) * 10)}</span>
              </div>
              <div className="mt-2 flex items-center justify-center gap-2 text-primary">
                <span className="material-symbols-outlined text-sm">trending_up</span>
                <span className="font-[family-name:var(--font-label)] text-sm font-bold">
                  {totalTimed}/{totalRuns} Timed
                </span>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest">
                <span className="text-on-surface-variant">Avg Deaths/Run</span>
                <span className={avgDeaths <= 1 ? "text-primary" : "text-error"}>{avgDeaths.toFixed(1)}</span>
              </div>
              <div className="w-full h-1 bg-surface-container-highest rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.max(0, 100 - avgDeaths * 20)}%`,
                    backgroundColor: avgDeaths <= 1 ? "var(--color-primary)" : "var(--color-error)",
                  }}
                />
              </div>
            </div>
          </div>

          {/* Stat Cards Row */}
          <div className="md:col-span-12 grid grid-cols-1 md:grid-cols-4 gap-6">
            <StatCard label="Run Success Rate" value={`${successRate}%`} badge={successRate >= 80 ? "+Good" : "Low"} badgeColor={successRate >= 80 ? "text-primary bg-primary-container/20" : "text-error bg-error-container/20"} borderClass="border-l-2 border-primary" />
            <StatCard label="Total Timed" value={totalTimed.toString()} badge={`of ${totalRuns}`} badgeColor="text-secondary bg-secondary-container/20" />
            <StatCard label="Avg Deaths" value={avgDeaths.toFixed(1)} badge={avgDeaths <= 1 ? "Clean" : "High"} badgeColor={avgDeaths <= 1 ? "text-primary bg-primary-container/20" : "text-error bg-error-container/20"} />
            <StatCard
              label="Avg Interrupts"
              value={(data.points.reduce((s, p) => s + p.avg_interrupts * p.runs_count, 0) / Math.max(1, totalRuns)).toFixed(1)}
              badge="Per Run"
              badgeColor="text-secondary bg-secondary-container/20"
            />
          </div>

          {/* Performance Log */}
          <div className="md:col-span-12 bg-surface-container-high rounded-lg overflow-hidden">
            <div className="p-6 border-b border-outline-variant/10 flex justify-between items-center">
              <h3 className="font-[family-name:var(--font-headline)] font-bold text-lg uppercase tracking-tight">
                Performance Log
              </h3>
              <span className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase tracking-widest">
                Daily Recaps
              </span>
            </div>
            <div className="divide-y divide-outline-variant/5">
              {data.points.map((point, i) => (
                <div
                  key={point.date}
                  className={`grid grid-cols-2 md:grid-cols-5 p-6 hover:bg-surface-container-highest transition-colors items-center gap-4 ${
                    i % 2 === 1 ? "bg-surface-container-low/50" : ""
                  }`}
                >
                  <div>
                    <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">Date</p>
                    <p className="font-[family-name:var(--font-label)] text-sm text-on-surface">{point.date}</p>
                  </div>
                  <div>
                    <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">Runs</p>
                    <p className="font-[family-name:var(--font-body)] text-sm font-bold text-primary">
                      {point.timed_count}/{point.runs_count} Timed
                    </p>
                  </div>
                  <div className="hidden md:block">
                    <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">Avg Key</p>
                    <p className="font-[family-name:var(--font-label)] text-sm">+{point.avg_keystone_level}</p>
                  </div>
                  <div className="hidden md:block">
                    <p className="font-[family-name:var(--font-label)] text-[10px] text-on-surface-variant uppercase">Deaths</p>
                    <p className={`font-[family-name:var(--font-label)] text-sm ${point.avg_deaths > 2 ? "text-error" : ""}`}>
                      {point.avg_deaths} avg
                    </p>
                  </div>
                  <div className="col-span-2 md:col-span-1 flex justify-end">
                    <span className="font-[family-name:var(--font-label)] text-sm text-on-surface-variant">
                      {point.avg_interrupts} kicks/run
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function StatCard({
  label,
  value,
  badge,
  badgeColor,
  borderClass,
}: {
  label: string;
  value: string;
  badge: string;
  badgeColor: string;
  borderClass?: string;
}) {
  return (
    <div className={`bg-surface-container-low p-6 rounded-lg ${borderClass ?? ""}`}>
      <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mb-4">{label}</p>
      <div className="flex items-end justify-between">
        <span className="font-[family-name:var(--font-headline)] text-4xl font-bold text-on-surface">{value}</span>
        <span className={`font-[family-name:var(--font-label)] text-xs px-2 py-0.5 rounded-sm ${badgeColor}`}>{badge}</span>
      </div>
    </div>
  );
}
