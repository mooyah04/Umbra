import Link from "next/link";
import type { RunResponse } from "@/lib/types";
import { formatDuration } from "@/lib/utils";

interface RunCardProps {
  run: RunResponse;
  playerPath: string;
}

export default function RunCard({ run, playerPath }: RunCardProps) {
  const timedColor = run.timed ? "text-green-400" : "text-red-400";
  const timedLabel = run.timed ? "Timed" : "Depleted";
  const date = new Date(run.logged_at).toLocaleDateString();

  return (
    <Link
      href={`${playerPath}/run/${run.id}`}
      className="block bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/8 hover:border-[#8a2be2]/50 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-white font-bold text-lg">+{run.keystone_level}</span>
          <span className="text-gray-400 text-sm">{run.spec_name}</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className={timedColor}>{timedLabel}</span>
          <span className="text-gray-500">{formatDuration(run.duration)}</span>
          <span className="text-gray-500">{date}</span>
        </div>
      </div>
      <div className="flex gap-4 mt-2 text-xs text-gray-400">
        <span>Deaths: <span className={run.deaths === 0 ? "text-green-400" : "text-red-400"}>{run.deaths}</span></span>
        <span>Kicks: <span className="text-blue-400">{run.interrupts}</span></span>
        <span>Dispels: <span className="text-blue-400">{run.dispels}</span></span>
        {run.cc_casts !== null && <span>CC: <span className="text-purple-400">{run.cc_casts}</span></span>}
      </div>
    </Link>
  );
}
