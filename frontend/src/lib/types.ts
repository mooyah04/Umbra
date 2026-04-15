export interface PlayerScoreResponse {
  name: string;
  realm: string;
  region: string;
  role: string;
  grade: string;
  category_scores: Record<string, number>;
  runs_analyzed: number;
}

export interface PlayerSearchResult {
  name: string;
  realm: string;
  region: string;
  class_id: number;
  grade: string | null;
  role: string | null;
  spec: string | null;
  runs_analyzed: number | null;
  avatar_url?: string | null;
  inset_url?: string | null;
  composite_score?: number | null;
  rank?: number | null;
}

export interface RunResponse {
  id: number;
  encounter_id: number;
  keystone_level: number;
  role: string;
  spec_name: string;
  dps: number;
  hps: number;
  ilvl: number;
  duration: number;
  deaths: number;
  interrupts: number;
  dispels: number;
  avoidable_damage_taken: number;
  damage_taken_total: number;
  casts_total: number;
  cooldown_usage_pct: number;
  timed: boolean;
  logged_at: string;
  rating: number | null;
  average_item_level: number | null;
  keystone_affixes: number[] | null;
  healing_received: number | null;
  cc_casts: number | null;
  critical_interrupts: number | null;
  avoidable_deaths: number | null;
  party_comp?: PartyMember[] | null;
}

export interface PartyMember {
  name: string;
  realm: string;
  class: string;
  role: string;
  spec: string | null;
}

export interface RunListResponse {
  runs: RunResponse[];
  total: number;
  page: number;
  per_page: number;
}

export interface RoleScore {
  role: string;
  grade: string;
  category_scores: Record<string, number>;
  runs_analyzed: number;
  primary_role: boolean;
}

export interface PlayerProfileResponse {
  name: string;
  realm: string;
  region: string;
  class_id: number;
  scores: RoleScore[];
  recent_runs: RunResponse[];
  timed_pct: number;
  total_runs: number;
  avatar_url?: string | null;
  inset_url?: string | null;
  render_url?: string | null;
}

export interface HistoryPoint {
  date: string;
  runs_count: number;
  avg_keystone_level: number;
  timed_count: number;
  avg_deaths: number;
  avg_interrupts: number;
  avg_dps: number;
}

export interface HistoryResponse {
  points: HistoryPoint[];
  period: string;
}
