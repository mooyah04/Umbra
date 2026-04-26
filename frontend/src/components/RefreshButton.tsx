"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, refreshPlayer } from "@/lib/api";

interface Props {
  name: string;
  realm: string;
  region: string;
}

/**
 * User-triggered profile refresh. Hits POST /api/player/.../refresh on
 * the backend, which re-ingests recent WCL reports for this character.
 *
 * Two layers of rate limit apply server-side (per-IP via slowapi, and
 * per-player 60-min cooldown via last_ingested_at). On 429 the component
 * flips into countdown mode so repeat clicks are blocked client-side
 * and the user sees exactly when they can try again.
 *
 * First-load state intentionally allows the click — the backend is the
 * source of truth for the cooldown, and plumbing last_ingested_at into
 * the profile GET just for this button would bloat the payload.
 */
export default function RefreshButton({ name, realm, region }: Props) {
  const router = useRouter();
  const [refreshing, setRefreshing] = useState(false);
  const [cooldownRemaining, setCooldownRemaining] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // Live countdown while cooldown is active.
  useEffect(() => {
    if (cooldownRemaining <= 0) return;
    const id = setInterval(() => {
      setCooldownRemaining((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [cooldownRemaining]);

  const disabled = refreshing || cooldownRemaining > 0;

  async function onClick() {
    if (disabled) return;
    setRefreshing(true);
    setError(null);
    setInfo(null);
    try {
      await refreshPlayer(name, realm, region);
      router.refresh();
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : null;
      const detail =
        apiErr?.detail && typeof apiErr.detail === "object"
          ? (apiErr.detail as {
              code?: string;
              retry_after_seconds?: number;
              retry_after?: number;
            })
          : null;

      if (detail?.code === "cooldown_active" && detail.retry_after_seconds) {
        setCooldownRemaining(detail.retry_after_seconds);
      } else if (detail?.code === "wcl_rate_limited" && detail.retry_after) {
        setCooldownRemaining(detail.retry_after);
      } else if (apiErr?.status === 408) {
        // Client aborted but the server-side ingest keeps running. Block
        // the button for a minute so users wait for it to finish instead
        // of stacking up duplicate work, and surface the message as info.
        setCooldownRemaining(60);
        setInfo(apiErr.message);
      } else {
        setError(apiErr?.message ?? "Something went wrong. Try again soon.");
      }
    } finally {
      setRefreshing(false);
    }
  }

  const label = refreshing
    ? "Refreshing…"
    : cooldownRemaining > 0
      ? `Refresh in ${formatCountdown(cooldownRemaining)}`
      : "Refresh Profile";

  return (
    <div className="w-full">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className="w-full bg-surface-container-highest hover:bg-surface-bright text-on-surface border border-primary/30 hover:border-primary/60 font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest px-4 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
      >
        {refreshing && (
          <span className="material-symbols-outlined text-sm animate-spin">
            progress_activity
          </span>
        )}
        {label}
      </button>
      {error && (
        <p className="mt-2 text-xs text-red-400 text-center">{error}</p>
      )}
      {info && (
        <p className="mt-2 text-xs text-on-surface-variant text-center">
          {info}
        </p>
      )}
    </div>
  );
}

function formatCountdown(seconds: number): string {
  if (seconds >= 60) {
    return `${Math.ceil(seconds / 60)}m`;
  }
  return `${seconds}s`;
}
