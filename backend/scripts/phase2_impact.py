"""Phase 2 run-selection impact report.

For every graded player, scores their role runs both ways:
  - select_runs=False (legacy: weighted avg over all runs)
  - select_runs=True  (Phase 2: best timed run per dungeon)

Reports composite delta, grade delta, and aggregates so we can see
inflation, deflation, and selection-coverage drop-offs before deciding
whether Phase 2 needs threshold recalibration.

Read-only. Never writes.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import DungeonRun, Player, PlayerScore
from app.scoring.engine import composite_to_grade, score_player_runs


def main() -> None:
    session = SessionLocal()
    try:
        scores = list(session.execute(select(PlayerScore)).scalars())
        print(f"Scoring {len(scores)} PlayerScores both ways...")

        deltas = []
        grade_changes = Counter()  # (old, new) -> count
        runs_dropped = []
        ungrade_candidates = []  # selected count < min_runs_for_grade

        for ps in scores:
            player = session.get(Player, ps.player_id)
            if player is None:
                continue
            role_runs = list(session.execute(
                select(DungeonRun).where(
                    DungeonRun.player_id == ps.player_id,
                    DungeonRun.role == ps.role,
                )
            ).scalars())
            if len(role_runs) < settings.min_runs_for_grade:
                continue

            legacy = score_player_runs(
                role_runs, ps.role, class_id=player.class_id,
                select_runs=False,
            )
            new = score_player_runs(
                role_runs, ps.role, class_id=player.class_id,
                select_runs=True,
            )

            delta = new.composite_score - legacy.composite_score
            deltas.append(delta)
            grade_changes[(legacy.overall_grade, new.overall_grade)] += 1
            runs_dropped.append(len(role_runs) - new.runs_analyzed)
            if new.runs_analyzed < settings.min_runs_for_grade:
                ungrade_candidates.append({
                    "name": f"{player.name}-{player.realm}",
                    "role": ps.role.value,
                    "in_runs": len(role_runs),
                    "selected": new.runs_analyzed,
                    "old_grade": legacy.overall_grade,
                    "new_grade": new.overall_grade,
                    "delta": round(delta, 1),
                })

        if not deltas:
            print("No graded players to score.")
            return

        deltas.sort()
        n = len(deltas)
        print(f"\nComposite deltas (Phase 2 - legacy) across {n} graded players:")
        print(f"  min:  {deltas[0]:+.1f}")
        print(f"  p10:  {deltas[n//10]:+.1f}")
        print(f"  p25:  {deltas[n//4]:+.1f}")
        print(f"  p50:  {deltas[n//2]:+.1f}")
        print(f"  p75:  {deltas[(3*n)//4]:+.1f}")
        print(f"  p90:  {deltas[(9*n)//10]:+.1f}")
        print(f"  max:  {deltas[-1]:+.1f}")
        print(f"  mean: {sum(deltas)/n:+.2f}")

        runs_dropped.sort()
        print(f"\nRuns dropped per player (input - selected):")
        print(f"  min:  {runs_dropped[0]}")
        print(f"  p50:  {runs_dropped[n//2]}")
        print(f"  p90:  {runs_dropped[(9*n)//10]}")
        print(f"  max:  {runs_dropped[-1]}")
        print(f"  mean: {sum(runs_dropped)/n:.1f}")

        moved = sum(1 for (o, n_) in grade_changes if o != n_ for _ in range(grade_changes[(o, n_)]))
        # Recount cleanly
        moved = sum(c for (o, n_), c in grade_changes.items() if o != n_)
        print(f"\nGrade changes: {moved} of {n} ({moved*100/n:.1f}%) players moved letters.")

        # Top transitions
        print("\nTop grade transitions (old -> new : count):")
        for (old, new_g), count in sorted(
            grade_changes.items(), key=lambda kv: -kv[1]
        )[:15]:
            marker = "" if old == new_g else "  *"
            print(f"  {old:>3} -> {new_g:<3} : {count}{marker}")

        if ungrade_candidates:
            print(
                f"\n{len(ungrade_candidates)} players would have <"
                f"{settings.min_runs_for_grade} selected runs (no-coverage candidates):"
            )
            for c in ungrade_candidates[:20]:
                print(
                    f"  {c['name']:<32} {c['role']:>6}  "
                    f"in={c['in_runs']:>2} sel={c['selected']:>1}  "
                    f"{c['old_grade']:>3} -> {c['new_grade']:<3}  "
                    f"({c['delta']:+.1f})"
                )
            if len(ungrade_candidates) > 20:
                print(f"  ... and {len(ungrade_candidates)-20} more")
    finally:
        session.close()


if __name__ == "__main__":
    main()
