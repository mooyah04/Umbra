"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, parsePlayerFromWcl } from "@/lib/api";

interface Props {
  name: string;
  realm: string;
  region: string;
}

/**
 * First-time cold ingest trigger. Shown on profiles where `not_indexed`
 * is true — i.e. the character isn't in our DB yet. Hits the new
 * POST /api/player/.../parse endpoint which rate-limits to once per
 * (IP, character) per 24h, a much stricter cap than the 60-minute
 * refresh cooldown on already-cached profiles.
 *
 * On 429 (cold_parse_cooldown_active) we flip into a countdown state so
 * users can see when they'll be allowed to retry.
 */
export default function ParseButton({ name, realm, region }: Props) {
  const router = useRouter();
  const [parsing, setParsing] = useState(false);
  const [cooldownRemaining, setCooldownRemaining] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cooldownRemaining <= 0) return;
    const id = setInterval(() => {
      setCooldownRemaining((s) => Math.max(0, s - 1));
    }, 1000);
    return () => clearInterval(id);
  }, [cooldownRemaining]);

  const disabled = parsing || cooldownRemaining > 0;

  async function onClick() {
    if (disabled) return;
    setParsing(true);
    setError(null);
    try {
      await parsePlayerFromWcl(name, realm, region);
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

      if (
        detail?.code === "cold_parse_cooldown_active" &&
        detail.retry_after_seconds
      ) {
        setCooldownRemaining(detail.retry_after_seconds);
      } else if (detail?.code === "wcl_rate_limited" && detail.retry_after) {
        setCooldownRemaining(detail.retry_after);
      } else {
        setError(apiErr?.message ?? "Something went wrong. Try again soon.");
      }
    } finally {
      setParsing(false);
    }
  }

  const label = parsing
    ? "Parsing logs…"
    : cooldownRemaining > 0
      ? `Try again in ${formatCountdown(cooldownRemaining)}`
      : "Parse Warcraft Logs";

  return (
    <div className="w-full max-w-md mx-auto">
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className="w-full bg-primary text-on-primary font-[family-name:var(--font-label)] text-xs uppercase tracking-widest px-5 py-3 rounded hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
      >
        {parsing && (
          <span className="material-symbols-outlined text-sm animate-spin">
            progress_activity
          </span>
        )}
        {label}
      </button>
      <p className="mt-3 text-[11px] text-on-surface-variant/70 text-center leading-relaxed">
        You can only use this feature once every 24 hours. This does not
        affect the 1 hour refresh cooldown.
      </p>
      {error && (
        <p className="mt-3 text-xs text-red-400 text-center">{error}</p>
      )}
    </div>
  );
}

function formatCountdown(seconds: number): string {
  if (seconds >= 3600) {
    return `${Math.ceil(seconds / 3600)}h`;
  }
  if (seconds >= 60) {
    return `${Math.ceil(seconds / 60)}m`;
  }
  return `${seconds}s`;
}
