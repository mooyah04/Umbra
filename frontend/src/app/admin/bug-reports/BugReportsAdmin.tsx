"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const STORAGE_KEY = "umbra-admin-api-key";

interface BugReport {
  id: number;
  created_at: string;
  source: "website" | "addon" | string;
  status: "new" | "triaged" | "resolved" | "wontfix" | string;
  submitter_name: string | null;
  submitter_email: string | null;
  summary: string;
  details: string;
  page_url: string | null;
  user_agent: string | null;
}

type StatusFilter = "" | "new" | "triaged" | "resolved" | "wontfix";
type SourceFilter = "" | "website" | "addon";

export default function BugReportsAdmin() {
  const [apiKey, setApiKey] = useState("");
  const [keyInput, setKeyInput] = useState("");
  const [reports, setReports] = useState<BugReport[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("");
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>("");

  // Rehydrate the stored key on mount. Runs client-only (no SSR mismatch
  // risk because the page renders the "enter key" state on first paint).
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) setApiKey(saved);
  }, []);

  const fetchReports = useCallback(
    async (key: string, status: StatusFilter, source: SourceFilter) => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams();
        if (status) params.set("status_filter", status);
        if (source) params.set("source", source);
        params.set("limit", "200");
        const res = await fetch(
          `${API_URL}/api/admin/bug-reports?${params.toString()}`,
          { headers: { "X-API-Key": key }, cache: "no-store" },
        );
        if (res.status === 401) {
          setError("Invalid API key. Clear and re-enter.");
          setReports(null);
          return;
        }
        if (!res.ok) {
          setError(`Fetch failed (${res.status}): ${res.statusText}`);
          setReports(null);
          return;
        }
        const data = (await res.json()) as { reports: BugReport[] };
        setReports(data.reports ?? []);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
        setReports(null);
      } finally {
        setLoading(false);
      }
    },
    [],
  );

  // Auto-fetch whenever we have a key or filter changes.
  useEffect(() => {
    if (apiKey) fetchReports(apiKey, statusFilter, sourceFilter);
  }, [apiKey, statusFilter, sourceFilter, fetchReports]);

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
    setReports(null);
    setError(null);
  };

  const counts = useMemo(() => {
    if (!reports) return null;
    const byStatus: Record<string, number> = {};
    for (const r of reports) byStatus[r.status] = (byStatus[r.status] ?? 0) + 1;
    return byStatus;
  }, [reports]);

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
          Stored only in this browser&apos;s localStorage. Not sent to any
          third party.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-3 flex-wrap mb-6">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          className="bg-surface-container rounded px-3 py-2 text-sm text-on-surface border border-outline-variant/20"
        >
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="triaged">Triaged</option>
          <option value="resolved">Resolved</option>
          <option value="wontfix">Won&apos;t fix</option>
        </select>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value as SourceFilter)}
          className="bg-surface-container rounded px-3 py-2 text-sm text-on-surface border border-outline-variant/20"
        >
          <option value="">All sources</option>
          <option value="website">Website</option>
          <option value="addon">Addon</option>
        </select>
        <button
          onClick={() => fetchReports(apiKey, statusFilter, sourceFilter)}
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

      {counts && (
        <div className="flex gap-4 mb-6 text-xs font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant">
          <span>Total: {reports?.length ?? 0}</span>
          {Object.entries(counts).map(([k, v]) => (
            <span key={k}>
              {k}: <span className="text-on-surface">{v}</span>
            </span>
          ))}
        </div>
      )}

      {reports && reports.length === 0 && !loading && (
        <p className="text-on-surface-variant text-sm italic">
          No reports matching the current filters.
        </p>
      )}

      {reports && reports.length > 0 && (
        <ul className="space-y-3">
          {reports.map((r) => (
            <ReportRow key={r.id} r={r} />
          ))}
        </ul>
      )}
    </div>
  );
}

function ReportRow({ r }: { r: BugReport }) {
  const [expanded, setExpanded] = useState(false);
  const statusColor =
    {
      new: "text-primary bg-primary/10 border-primary/30",
      triaged: "text-yellow-300 bg-yellow-500/10 border-yellow-500/30",
      resolved: "text-green-300 bg-green-500/10 border-green-500/30",
      wontfix: "text-on-surface-variant bg-surface-container border-outline-variant/20",
    }[r.status] ?? "text-on-surface-variant";
  const sourceColor =
    r.source === "addon"
      ? "text-secondary bg-secondary/10"
      : "text-tertiary bg-tertiary/10";

  const created = new Date(r.created_at).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <li className="bg-surface-container-high rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full text-left px-5 py-3 hover:bg-surface-bright transition-colors flex items-center gap-3"
      >
        <span
          className={`font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest px-2 py-1 rounded border ${statusColor}`}
        >
          {r.status}
        </span>
        <span
          className={`font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest px-2 py-1 rounded ${sourceColor}`}
        >
          {r.source}
        </span>
        <span className="text-on-surface font-medium truncate flex-1">
          {r.summary}
        </span>
        <span className="text-on-surface-variant text-xs whitespace-nowrap">
          {created}
        </span>
        <span className="material-symbols-outlined text-on-surface-variant">
          {expanded ? "expand_less" : "expand_more"}
        </span>
      </button>
      {expanded && (
        <div className="px-5 pb-5 pt-2 border-t border-outline-variant/10 space-y-3">
          {(r.submitter_name || r.submitter_email) && (
            <Field
              label="Submitter"
              value={[r.submitter_name, r.submitter_email]
                .filter(Boolean)
                .join(" · ") || "—"}
            />
          )}
          {r.page_url && <Field label="Page" value={r.page_url} link />}
          {r.user_agent && (
            <Field label="User Agent" value={r.user_agent} mono />
          )}
          <Field label="ID" value={`#${r.id}`} mono />
          <div>
            <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mb-1">
              Details
            </p>
            <pre className="bg-surface-container rounded p-3 text-xs text-on-surface whitespace-pre-wrap break-words font-mono">
              {r.details}
            </pre>
          </div>
        </div>
      )}
    </li>
  );
}

function Field({
  label,
  value,
  link,
  mono,
}: {
  label: string;
  value: string;
  link?: boolean;
  mono?: boolean;
}) {
  return (
    <div className="flex gap-3 items-start text-sm">
      <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant w-24 flex-shrink-0 pt-0.5">
        {label}
      </span>
      {link ? (
        <a
          href={value}
          target="_blank"
          rel="noreferrer"
          className={`text-primary hover:underline break-all ${mono ? "font-mono text-xs" : ""}`}
        >
          {value}
        </a>
      ) : (
        <span
          className={`text-on-surface break-all ${mono ? "font-mono text-xs" : ""}`}
        >
          {value}
        </span>
      )}
    </div>
  );
}
