import type {
  HistoryResponse,
  PlayerProfileResponse,
  PlayerSearchResult,
  RunListResponse,
  RunResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Full URL of the tracked addon-download endpoint. Used in <a href>
 *  elements so every click gets logged via a 302 through the backend. */
export const ADDON_DOWNLOAD_URL = `${API_URL}/api/addon/download`;

/** Public Wago listing. Auto-updates via addon managers that sync Wago. */
export const WAGO_ADDON_URL = "https://addons.wago.io/addons/umbra-1Mo9iQjb";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Shape of the structured detail object the backend returns on 404s
 *  that the frontend can act on (e.g. a player-not-found with reason). */
export interface ApiErrorDetail {
  code?: string;
  reason?: string;
  message?: string;
}

async function fetchApi<T>(
  path: string,
  freshness: number | "no-store" = 60,
): Promise<T> {
  // Per-endpoint cache freshness. Server components use Next's ISR:
  // responses are served from cache for `freshness` seconds, then
  // stale-served once while the background regen runs.
  //
  // Pass "no-store" for routes where the first-visit stale window
  // is unacceptable (player profiles after a force re-ingest, etc.).
  // Makes every request hit the backend; still fast because the
  // backend caches scored data in PlayerScore.
  const init: RequestInit =
    freshness === "no-store"
      ? { cache: "no-store" }
      : { next: { revalidate: freshness } };
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    let detail: ApiErrorDetail | string | undefined;
    let message = `API error ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? body;
      if (
        detail &&
        typeof detail === "object" &&
        "message" in detail &&
        typeof detail.message === "string"
      ) {
        message = detail.message;
      }
    } catch {
      // Body wasn't JSON; keep the generic message.
    }
    throw new ApiError(res.status, message, detail);
  }
  return res.json();
}

export async function searchPlayers(
  query: string,
  region?: string,
): Promise<PlayerSearchResult[]> {
  const params = new URLSearchParams({ q: query });
  if (region) params.set("region", region);
  return fetchApi(`/api/players/search?${params}`);
}

export async function getTopPlayers(
  limit = 10,
  role?: "tank" | "healer" | "dps",
  region?: string,
): Promise<PlayerSearchResult[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (role) params.set("role", role);
  if (region) params.set("region", region);
  // 30s — homepage's "Recently Graded" should feel live without
  // re-fetching on every page view.
  return fetchApi(`/api/players/top?${params}`, 30);
}

export async function getLeaderboard(opts: {
  role?: "tank" | "healer" | "dps";
  region?: string;
  classId?: number;
  limit?: number;
} = {}): Promise<PlayerSearchResult[]> {
  const params = new URLSearchParams({ limit: String(opts.limit ?? 50) });
  if (opts.role) params.set("role", opts.role);
  if (opts.region) params.set("region", opts.region);
  if (opts.classId) params.set("class_id", String(opts.classId));
  // 20s — leaderboard shifts as scores recompute during sweep ticks.
  return fetchApi(`/api/players/leaderboard?${params}`, 20);
}

export interface StatsSummary {
  total_players: number;
  total_runs: number;
  graded_players: number;
  role_counts: Record<string, number>;
}

export async function getStatsSummary(): Promise<StatsSummary> {
  // 15s — homepage banner numbers. Short freshness is cheap (endpoint
  // is a few counts) and makes the site feel alive.
  return fetchApi<StatsSummary>(`/api/stats/summary`, 15);
}

export async function getPlayerProfile(
  region: string,
  realm: string,
  name: string,
): Promise<PlayerProfileResponse> {
  // No-store: after a force re-ingest, users expect the player page
  // to reflect fresh data without a hard refresh. Server-side scoring
  // is already cached in PlayerScore so the per-request cost is cheap.
  return fetchApi(`/api/player/${region}/${realm}/${name}/all`, "no-store");
}

export async function getPlayerRuns(
  region: string,
  realm: string,
  name: string,
  page = 1,
  perPage = 20,
): Promise<RunListResponse> {
  // Same rationale as getPlayerProfile — run list needs to reflect
  // fresh ingests immediately (the recent-runs section is the first
  // thing users check).
  return fetchApi(
    `/api/player/${region}/${realm}/${name}/runs?page=${page}&per_page=${perPage}`,
    "no-store",
  );
}

export async function getRunDetail(
  region: string,
  realm: string,
  name: string,
  runId: number,
): Promise<RunResponse> {
  // Run detail pages include the Level B timeline which populates on
  // re-ingest — caching masks timeline appearances for the freshness
  // window. Always fresh.
  return fetchApi(
    `/api/player/${region}/${realm}/${name}/runs/${runId}`,
    "no-store",
  );
}

export interface ClaimResponse {
  ok: boolean;
  report_code: string;
  class_name: string | null;
  class_id: number | null;
  runs_ingested: number;
  reason: string | null;
}

export async function claimPlayer(
  name: string,
  realm: string,
  region: string,
  reportUrlOrCode: string,
): Promise<ClaimResponse> {
  // Hard cap the claim wait so a stuck backend (WCL 429 + slow retry)
  // surfaces as a clear error to the user instead of the "Verifying…"
  // button spinning forever. Comfortably below Railway's edge timeout.
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 25_000);
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/player/claim`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        realm,
        region,
        report_url_or_code: reportUrlOrCode,
      }),
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(
        408,
        "The request timed out. Warcraft Logs may be rate-limiting us. Try again in a minute.",
      );
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
  if (!res.ok) {
    let detail: ApiErrorDetail | string | undefined;
    let message = `API error ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? body;
      if (
        detail &&
        typeof detail === "object" &&
        "message" in detail &&
        typeof detail.message === "string"
      ) {
        message = detail.message;
      }
    } catch {
      /* fall through */
    }
    throw new ApiError(res.status, message, detail);
  }
  return res.json();
}

export async function getPlayerHistory(
  region: string,
  realm: string,
  name: string,
  period: "week" | "month" | "season" = "month",
): Promise<HistoryResponse> {
  return fetchApi(
    `/api/player/${region}/${realm}/${name}/history?period=${period}`,
  );
}

export interface BugReportPayload {
  summary: string;
  details?: string;
  source?: "website" | "addon";
  submitter_name?: string;
  submitter_email?: string;
  page_url?: string;
}

export async function submitBugReport(payload: BugReportPayload): Promise<{ id: number; ok: boolean }> {
  const res = await fetch(`${API_URL}/api/bug-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let message = `Bug report submit failed (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* fall through */
    }
    throw new ApiError(res.status, message);
  }
  return res.json();
}
