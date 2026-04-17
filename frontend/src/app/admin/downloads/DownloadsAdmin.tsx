"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const STORAGE_KEY = "umbra-admin-api-key";

interface DailyPoint {
  day: string;
  count: number;
}

interface DownloadStats {
  total: number;
  last_24h: number;
  last_7d: number;
  last_30d: number;
  unique_ips_last_30d: number;
  daily_series: DailyPoint[];
}

export default function DownloadsAdmin() {
  const [apiKey, setApiKey] = useState("");
  const [keyInput, setKeyInput] = useState("");
  const [stats, setStats] = useState<DownloadStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setApiKey(saved);
  }, []);

  const fetchStats = useCallback(async (key: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/admin/download-stats`, {
        headers: { "X-API-Key": key },
        cache: "no-store",
      });
      if (res.status === 401) {
        setError("Invalid API key. Clear and re-enter.");
        setStats(null);
        return;
      }
      if (!res.ok) {
        setError(`Fetch failed (${res.status}): ${res.statusText}`);
        setStats(null);
        return;
      }
      const data = (await res.json()) as DownloadStats;
      setStats(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (apiKey) fetchStats(apiKey);
  }, [apiKey, fetchStats]);

  const handleSaveKey = () => {
    const trimmed = keyInput.trim();
    if (!trimmed) return;
    localStorage.setItem(STORAGE_KEY, trimmed);
    setApiKey(trimmed);
    setKeyInput("");
  };

  const handleClearKey = () => {
    localStorage.removeItem(STORAGE_KEY);
    setApiKey("");
    setStats(null);
    setError(null);
  };

  const peakDay = useMemo(() => {
    if (!stats || !stats.daily_series.length) return null;
    return stats.daily_series.reduce((best, p) =>
      p.count > best.count ? p : best,
    );
  }, [stats]);

  const chartMax = useMemo(() => {
    if (!stats) return 0;
    return Math.max(1, ...stats.daily_series.map((p) => p.count));
  }, [stats]);

  if (!apiKey) {
    return (
      <div className="bg-surface-container-high rounded-xl p-6">
        <label
          htmlFor="api-key"
          className="block font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-on-surface-variant mb-2"
        >
          Admin API Key
        </label>
        <div className="flex gap-2 flex-wrap">
          <input
            id="api-key"
            type="password"
            autoComplete="off"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSaveKey();
            }}
            placeholder="X-API-Key value"
            className="flex-1 min-w-0 bg-surface-container rounded px-3 py-2 text-sm text-on-surface border border-outline-variant/20 focus:border-primary focus:outline-none"
          />
          <button
            onClick={handleSaveKey}
            className="bg-primary text-on-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest px-5 py-2 rounded hover:brightness-110 transition-all"
          >
            Save
          </button>
        </div>
        <p className="text-on-surface-variant/70 text-xs mt-3">
          Stored only in this browser&apos;s localStorage.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-3 flex-wrap mb-6">
        <button
          onClick={() => fetchStats(apiKey)}
          className="bg-surface-container-highest text-on-surface font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest px-4 py-2 rounded hover:brightness-110 transition-all"
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
        <button
          onClick={handleClearKey}
          className="ml-auto text-on-surface-variant font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest hover:text-primary transition-colors"
        >
          Clear API key
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 text-sm text-red-300">
          {error}
        </div>
      )}

      {stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
            <StatTile label="Total" value={stats.total.toLocaleString()} />
            <StatTile
              label="Last 24h"
              value={stats.last_24h.toLocaleString()}
            />
            <StatTile label="Last 7d" value={stats.last_7d.toLocaleString()} />
            <StatTile
              label="Last 30d"
              value={stats.last_30d.toLocaleString()}
            />
            <StatTile
              label="Unique IPs (30d)"
              value={stats.unique_ips_last_30d.toLocaleString()}
              hint={
                stats.last_30d > 0
                  ? `${((stats.unique_ips_last_30d / stats.last_30d) * 100).toFixed(0)}% unique`
                  : undefined
              }
            />
          </div>

          <div className="bg-surface-container-high rounded-xl p-6">
            <div className="flex items-end justify-between mb-4 flex-wrap gap-2">
              <div>
                <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mb-1">
                  Daily Downloads (last 30 days)
                </p>
                <h3 className="font-[family-name:var(--font-headline)] font-bold text-xl text-on-surface tracking-tight">
                  Timeline
                </h3>
              </div>
              {peakDay && (
                <div className="text-right">
                  <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
                    Peak day
                  </p>
                  <p className="text-on-surface text-sm">
                    {peakDay.day} ({peakDay.count.toLocaleString()})
                  </p>
                </div>
              )}
            </div>
            {stats.daily_series.length === 0 ? (
              <p className="text-on-surface-variant text-sm italic">
                No downloads recorded yet.
              </p>
            ) : (
              <div className="flex items-end gap-1 h-40">
                {stats.daily_series.map((p) => {
                  const height = (p.count / chartMax) * 100;
                  return (
                    <div
                      key={p.day}
                      className="flex-1 min-w-0 group relative"
                      title={`${p.day} : ${p.count} download${p.count === 1 ? "" : "s"}`}
                    >
                      <div
                        className="w-full bg-primary/60 group-hover:bg-primary rounded-t transition-colors"
                        style={{ height: `${height}%`, minHeight: "2px" }}
                      />
                    </div>
                  );
                })}
              </div>
            )}
            {stats.daily_series.length > 0 && (
              <div className="flex justify-between text-[10px] font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant mt-2">
                <span>{stats.daily_series[0].day}</span>
                <span>
                  {stats.daily_series[stats.daily_series.length - 1].day}
                </span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function StatTile({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="bg-surface-container-high rounded-xl p-4">
      <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mb-1">
        {label}
      </p>
      <p className="font-[family-name:var(--font-headline)] font-black text-2xl text-on-surface tracking-tighter">
        {value}
      </p>
      {hint && (
        <p className="text-on-surface-variant text-[10px] mt-1">{hint}</p>
      )}
    </div>
  );
}
