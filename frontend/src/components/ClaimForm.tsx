"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, claimPlayer } from "@/lib/api";

interface Props {
  name: string;
  realm: string;
  region: string;
  /** Header above the form. Defaults to the disambiguation framing. */
  title?: string;
  /** Paragraph under the header. Defaults to the disambiguation framing. */
  description?: string;
  /** Tighter paddings + smaller type for use below the fold on a graded
   *  profile. Default is the full-size prominent treatment. */
  compact?: boolean;
}

const DEFAULT_TITLE = "Not you? Claim with a log.";
const DEFAULT_DESCRIPTION =
  "Warcraft Logs sometimes returns the wrong character when multiple " +
  "players share a name. Paste a WCL report URL (or the 16-character " +
  "code) from any M+ run that included your character. We'll identify " +
  "you from that log directly.";

/**
 * Submit-a-log form. Dual purpose: disambiguation when WCL returned the
 * wrong character (name collisions across realms) AND re-sync from a
 * specific known-good log when a graded profile shows stale data. The
 * backend's claim_by_log path reads playerDetails from the report and
 * ingests via report_codes mode — authoritative regardless of name
 * collision state.
 */
export default function ClaimForm({
  name,
  realm,
  region,
  title = DEFAULT_TITLE,
  description = DEFAULT_DESCRIPTION,
  compact = false,
}: Props) {
  const [value, setValue] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [playersInLog, setPlayersInLog] = useState<string[] | null>(null);
  const router = useRouter();

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    setPlayersInLog(null);
    try {
      await claimPlayer(name, realm, region, value.trim());
      router.refresh();
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : null;
      const detail =
        apiErr?.detail && typeof apiErr.detail === "object"
          ? (apiErr.detail as {
              code?: string;
              message?: string;
              players_in_log?: string[];
            })
          : null;
      setError(detail?.message ?? apiErr?.message ?? "Something went wrong.");
      if (detail?.players_in_log?.length) {
        setPlayersInLog(detail.players_in_log);
      }
      setSubmitting(false);
    }
  }

  return (
    <div
      className={`bg-surface-container-high rounded-xl ${compact ? "p-4" : "p-6"} max-w-2xl mx-auto text-left`}
    >
      <h3
        className={`font-[family-name:var(--font-headline)] font-bold text-on-surface mb-2 ${compact ? "text-base" : "text-xl"}`}
      >
        {title}
      </h3>
      <p
        className={`text-on-surface-variant mb-4 leading-relaxed ${compact ? "text-xs" : "text-sm"}`}
      >
        {description}
      </p>
      <form onSubmit={onSubmit} className="flex flex-col gap-3">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="https://www.warcraftlogs.com/reports/ABC123xyz789DEF0"
          className="w-full bg-surface-bright text-on-surface rounded px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-primary"
          disabled={submitting}
        />
        <button
          type="submit"
          disabled={submitting || !value.trim()}
          className="bg-primary text-on-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest px-5 py-3 rounded hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? "Verifying log…" : "This Is Me"}
        </button>
      </form>
      {error && (
        <div className="mt-4 text-sm text-red-400">
          <p>{error}</p>
          {playersInLog && playersInLog.length > 0 && (
            <p className="mt-2 text-on-surface-variant">
              Players in that log: {playersInLog.join(", ")}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
