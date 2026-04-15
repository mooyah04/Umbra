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

async function fetchApi<T>(path: string): Promise<T> {
  // Auto-ingest paths can take 20-40s (WCL calls + scoring) so the
  // player-profile fetch needs a relaxed revalidate window + generous
  // timeout. Other paths are cheap and benefit from the 60s cache.
  const res = await fetch(`${API_URL}${path}`, { next: { revalidate: 60 } });
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
  return fetchApi(`/api/players/top?${params}`);
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
  return fetchApi(`/api/players/leaderboard?${params}`);
}

export interface StatsSummary {
  total_players: number;
  total_runs: number;
  graded_players: number;
  role_counts: Record<string, number>;
}

export async function getStatsSummary(): Promise<StatsSummary> {
  return fetchApi<StatsSummary>(`/api/stats/summary`);
}

export async function getPlayerProfile(
  region: string,
  realm: string,
  name: string,
): Promise<PlayerProfileResponse> {
  return fetchApi(`/api/player/${region}/${realm}/${name}/all`);
}

export async function getPlayerRuns(
  region: string,
  realm: string,
  name: string,
  page = 1,
  perPage = 20,
): Promise<RunListResponse> {
  return fetchApi(
    `/api/player/${region}/${realm}/${name}/runs?page=${page}&per_page=${perPage}`,
  );
}

export async function getRunDetail(
  region: string,
  realm: string,
  name: string,
  runId: number,
): Promise<RunResponse> {
  return fetchApi(`/api/player/${region}/${realm}/${name}/runs/${runId}`);
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
  const res = await fetch(`${API_URL}/api/player/claim`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name,
      realm,
      region,
      report_url_or_code: reportUrlOrCode,
    }),
  });
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
