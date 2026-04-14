import GradeBadge from "./GradeBadge";
import { CLASS_NAMES, CLASS_COLORS, ROLE_NAMES } from "@/lib/utils";

interface PlayerHeaderProps {
  name: string;
  realm: string;
  region: string;
  classId: number;
  grade: string;
  role: string;
  spec?: string;
  timedPct: number;
  totalRuns: number;
}

export default function PlayerHeader({
  name,
  realm,
  region,
  classId,
  grade,
  role,
  spec,
  timedPct,
  totalRuns,
}: PlayerHeaderProps) {
  const className = CLASS_NAMES[classId] ?? "Unknown";
  const classColor = CLASS_COLORS[classId] ?? "#ffffff";
  const roleName = ROLE_NAMES[role] ?? "DPS";

  return (
    <div className="flex items-center gap-6">
      <GradeBadge grade={grade} size="xl" />
      <div>
        <h1 className="text-3xl font-bold text-white">{name}</h1>
        <p className="text-gray-400">
          {realm}-{region.toUpperCase()}
        </p>
        <p className="mt-1">
          <span style={{ color: classColor }} className="font-medium">
            {spec ?? className}
          </span>
          <span className="text-gray-500 mx-2">&middot;</span>
          <span className="text-gray-400">{roleName}</span>
        </p>
        <div className="flex gap-4 mt-2 text-sm text-gray-500">
          <span>{totalRuns} runs</span>
          <span>{timedPct}% timed</span>
        </div>
      </div>
    </div>
  );
}
