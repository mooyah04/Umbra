import { getStatColor } from "@/lib/grades";

interface CategoryBarProps {
  label: string;
  value: number;
}

export default function CategoryBar({ label, value }: CategoryBarProps) {
  const color = getStatColor(value);
  const width = `${Math.max(0, Math.min(100, value))}%`;

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-gray-300">{label}</span>
        <span className="font-medium" style={{ color }}>
          {Math.round(value)}%
        </span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width, backgroundColor: color }}
        />
      </div>
    </div>
  );
}
