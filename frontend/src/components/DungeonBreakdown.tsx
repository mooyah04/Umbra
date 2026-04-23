import Link from "next/link";
import { getGradeColor } from "@/lib/grades";
import type { PerDungeonGrade } from "@/lib/types";

/**
 * Per-dungeon grade grid for the player page. Shows 8 tiles (one per
 * active-season dungeon); dungeons the player hasn't run yet render
 * dimmed as coverage-gap markers. Tiles with runs link to the dungeon
 * detail page so users can drill into per-dungeon aggregates.
 *
 * Server component — just renders props from PlayerProfileResponse.
 */
export default function DungeonBreakdown({
  tiles,
  playerPath,
}: {
  tiles: PerDungeonGrade[];
  /** Base path for building dungeon links, e.g. "/player/eu/realm/name". */
  playerPath: string;
}) {
  if (!tiles || tiles.length === 0) return null;

  return (
    <section className="mb-10">
      <div className="flex items-end justify-between mb-6">
        <div>
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            Where Your Grade Comes From
          </p>
          <h3 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-4xl tracking-tighter text-on-surface">
            PERFORMANCE BY DUNGEON
          </h3>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {tiles.map((t) => (
          <DungeonTile
            key={t.encounter_id}
            tile={t}
            playerPath={playerPath}
          />
        ))}
      </div>
    </section>
  );
}

function DungeonTile({
  tile,
  playerPath,
}: {
  tile: PerDungeonGrade;
  playerPath: string;
}) {
  const hasRuns = tile.runs_count > 0 && tile.grade;
  const gradeColor = hasRuns && tile.grade ? getGradeColor(tile.grade) : "#6b6b6b";

  const body = (
    <div
      className={`rounded-xl p-4 border transition-colors h-full ${
        hasRuns
          ? "bg-surface-container-high border-outline-variant/20 hover:bg-surface-bright"
          : "bg-surface-container-low border-outline-variant/10 opacity-60"
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <h4
          className="font-[family-name:var(--font-body)] font-bold text-sm text-on-surface leading-tight"
          title={tile.dungeon_name}
        >
          {tile.dungeon_name}
        </h4>
        {hasRuns && tile.grade && (
          <span
            className="font-[family-name:var(--font-headline)] font-black text-3xl leading-none shrink-0"
            style={{
              color: gradeColor,
              textShadow: `0 0 8px ${gradeColor}60`,
            }}
          >
            {tile.grade}
          </span>
        )}
      </div>
      {hasRuns ? (
        <div className="flex items-center justify-between text-[10px] font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant">
          <span>
            {tile.runs_count} {tile.runs_count === 1 ? "run" : "runs"}
            {tile.runs_count === 1 && (
              <span className="ml-1 text-primary/70">(prelim)</span>
            )}
          </span>
          {tile.best_keystone_timed != null && (
            <span>+{tile.best_keystone_timed} timed</span>
          )}
          {tile.best_keystone_timed == null &&
            tile.best_keystone_attempted != null && (
              <span>+{tile.best_keystone_attempted} untimed</span>
            )}
        </div>
      ) : (
        <p className="text-[10px] font-[family-name:var(--font-label)] uppercase tracking-widest text-on-surface-variant/70">
          No runs yet
        </p>
      )}
    </div>
  );

  // Only tiles with runs link through — empty tiles have nothing to show
  // on the dungeon page.
  if (!hasRuns) return body;
  return (
    <Link href={`${playerPath}/dungeon/${tile.encounter_id}`} className="block">
      {body}
    </Link>
  );
}
