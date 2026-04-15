import type {
  HistoryResponse,
  PlayerProfileResponse,
  PlayerSearchResult,
  RunListResponse,
  RunResponse,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchApi<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { next: { revalidate: 60 } });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
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
