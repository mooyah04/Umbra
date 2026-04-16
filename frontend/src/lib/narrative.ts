/**
 * Run narrative — turns a stored RunResponse into 3-5 sentences of plain
 * English that explain what stood out. No new data fetched; entirely
 * derived from stats we already have. Later levels (B: event timeline,
 * C: AI coach) will slot in below or replace this.
 */
import { formatNumber } from "@/lib/utils";
import { dungeonName } from "@/lib/dungeons";
import type { RunResponse } from "@/lib/types";

function formatDuration(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function generateRunNarrative(run: RunResponse): string[] {
  const out: string[] = [];
  const dungeon = dungeonName(run.encounter_id);
  const duration = formatDuration(run.duration);

  // ── Opening: set the scene ──────────────────────────────────────────
  if (run.timed) {
    out.push(`You timed ${dungeon} +${run.keystone_level} in ${duration}.`);
  } else {
    out.push(
      `You ran ${dungeon} +${run.keystone_level} in ${duration} — the key depleted.`,
    );
  }

  // ── Avoidable damage ────────────────────────────────────────────────
  if (run.damage_taken_total > 0 && run.avoidable_damage_taken > 0) {
    const pct = (run.avoidable_damage_taken / run.damage_taken_total) * 100;
    if (pct < 3) {
      out.push(
        `Clean on mechanics — only ${pct.toFixed(1)}% of damage taken was avoidable.`,
      );
    } else if (pct >= 12) {
      out.push(
        `Took ${formatNumber(run.avoidable_damage_taken)} avoidable damage — that's ${pct.toFixed(0)}% of total damage received, which is a lot of "stuff you could have sidestepped".`,
      );
    } else {
      out.push(
        `Took ${formatNumber(run.avoidable_damage_taken)} avoidable damage (${pct.toFixed(0)}% of total) — manageable but leaves room to tighten up.`,
      );
    }
  }

  // ── Interrupts (DPS + tanks only; healers have their own utility path) ─
  if (run.role !== "healer") {
    const crit = run.critical_interrupts;
    if (run.interrupts >= 15) {
      const critNote = crit && crit > 0 ? ` (${crit} of them on critical casts)` : "";
      out.push(`Strong kick discipline: ${run.interrupts} interrupts${critNote}.`);
    } else if (run.interrupts >= 8) {
      out.push(
        `${run.interrupts} interrupts — solid, but top players in this key range push 15+ per run.`,
      );
    } else if (run.interrupts < 5) {
      out.push(
        `Only ${run.interrupts} interrupt${run.interrupts === 1 ? "" : "s"} — worth auditing kick rotations or covering casters yourself.`,
      );
    }
  } else {
    // Healer utility — dispels + CC
    if (run.dispels >= 10) {
      out.push(`Heavy dispel load: ${run.dispels} cleanses carried the group.`);
    } else if (run.dispels === 0) {
      out.push(
        `No dispels recorded — if this dungeon had magic/poison/disease on players, something got missed.`,
      );
    }
  }

  // ── Cooldown utilization ────────────────────────────────────────────
  if (run.cooldown_usage_pct >= 90) {
    out.push(
      `Cooldowns pressed on time (${Math.round(run.cooldown_usage_pct)}% utilization).`,
    );
  } else if (run.cooldown_usage_pct > 0 && run.cooldown_usage_pct < 50) {
    out.push(
      `Only ${Math.round(run.cooldown_usage_pct)}% cooldown usage — sitting on majors is the fastest way to lose a grade tier.`,
    );
  }

  // ── Deaths: the closing beat ────────────────────────────────────────
  if (run.deaths === 0) {
    out.push(`Zero deaths — clean run all the way.`);
  } else if (run.deaths === 1) {
    if (run.avoidable_deaths && run.avoidable_deaths > 0) {
      out.push(`One death, to an avoidable ability.`);
    } else {
      out.push(`One death — most timed keys survive a single slip.`);
    }
  } else {
    const avoidable = run.avoidable_deaths ?? null;
    if (avoidable !== null && avoidable > 0) {
      out.push(
        `${run.deaths} deaths, ${avoidable} of them to avoidable mechanics — staying alive is the #1 thing that would lift this grade.`,
      );
    } else {
      out.push(`${run.deaths} deaths in a key this level adds up fast on the timer.`);
    }
  }

  return out;
}
