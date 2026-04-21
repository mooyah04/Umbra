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
  wcl_report_id: string;
  fight_id: number;
  rating: number | null;
  average_item_level: number | null;
  keystone_affixes: number[] | null;
  healing_received: number | null;
  cc_casts: number | null;
  critical_interrupts: number | null;
  avoidable_deaths: number | null;
  party_comp?: PartyMember[] | null;
  pulls?: Pull[] | null;
  /** Blizzard media URLs carried off the Player for the run page hero
   *  backdrop. Only populated by the single-run detail endpoint. */
  avatar_url?: string | null;
  inset_url?: string | null;
  render_url?: string | null;
  /** Grade for THIS specific run, scored in isolation. Only populated
   *  by the single-run detail endpoint — the run list uses a
   *  lighter response shape. */
  run_grade?: string | null;
  run_composite_score?: number | null;
  /** Player's aggregate grade across every run they have at this
   *  encounter+role. Only populated by the single-run detail endpoint.
   *  Null when the run's role has no scored runs at all. */
  dungeon_grade?: string | null;
  dungeon_composite_score?: number | null;
  dungeon_runs_count?: number | null;
  /** Per-category breakdown for the dungeon aggregate — same shape as
   *  the profile's overall category_scores but scoped to this dungeon's
   *  runs. Drives the per-dungeon "THE BREAKDOWN" view. */
  dungeon_category_scores?: Record<string, number> | null;
  /** Categories the scorer dropped (no data). Currently this is how
   *  `damage_output` lands when WCL hasn't ranked the character yet —
   *  the per-fight DPS percentile lookup came back empty, so the score
   *  would otherwise render as a misleading 0. Frontend hides these. */
  dungeon_excluded_categories?: string[] | null;
}

export type PullEventType =
  | "avoidable_damage"
  | "critical_interrupt"
  | "death"
  | "cooldown";
export type PullVerdict = "clean" | "took_hits" | "wipe";
export type CooldownKind = "offensive" | "defensive";

export interface PullEvent {
  t: number;                    // seconds into fight
  type: PullEventType;
  ability_id: number;
  ability_name: string;
  amount: number | null;        // damage amount; null for interrupts and cooldowns
  /** For critical_interrupt events: the player's interrupter spell
   *  (Mind Freeze, Kick, Counter Shot, etc.). Optional because legacy
   *  runs ingested before this field was added won't have it. */
  interrupter_id?: number | null;
  interrupter_name?: string | null;
  /** True when the kicked enemy cast is on our priority list for this
   *  dungeon (i.e. the ones that count toward scoring). False for
   *  'informational' interrupts that don't move the grade. Missing on
   *  legacy runs — treat undefined as true to preserve their behavior. */
  critical?: boolean;
  /** For cooldown events: whether the tracked CD was used to boost
   *  damage/throughput ("offensive") or reduce damage taken / emergency
   *  heal ("defensive"). Drives the per-pull icon (red sword vs blue
   *  shield). Missing on legacy runs ingested before CD tracking landed. */
  kind?: CooldownKind;
}

export interface Pull {
  i: number;                    // 1-based pull index
  start_t: number;              // seconds into fight
  end_t: number;
  label: string;                // "Selin Fireheart" or "Trash (4 mobs)"
  verdict: PullVerdict;
  events: PullEvent[];
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

export interface PerDungeonGrade {
  encounter_id: number;
  dungeon_name: string;
  runs_count: number;
  grade: string | null;
  composite_score: number | null;
  best_keystone_timed: number | null;
  best_keystone_attempted: number | null;
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
  per_dungeon?: PerDungeonGrade[];
  is_indexing?: boolean;
  /** Player isn't in our DB yet. Frontend renders a "Parse WCL" button
   *  that hits POST /api/player/.../parse to trigger the cold ingest
   *  explicitly. Replaces the old auto-ingest-on-GET behavior. */
  not_indexed?: boolean;
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

/** One cast in the rotation timeline: `t` seconds from fight start, `s`
 *  WoW spell ID. Names and icons live in the abilities lookup so the
 *  payload stays small on runs with hundreds of casts. */
export interface RotationCast {
  t: number;
  s: number;
}

export interface RotationAbility {
  name: string | null;
  icon: string | null;
}

export interface RunRotationResponse {
  run_id: number;
  encounter_id: number;
  keystone_level: number;
  role: string;
  spec_name: string;
  duration_ms: number;
  wcl_report_id: string;
  fight_id: number;
  /** Keyed by stringified spell ID — JSON objects can't have numeric keys. */
  abilities: Record<string, RotationAbility>;
  casts: RotationCast[];
  cached: boolean;
}
