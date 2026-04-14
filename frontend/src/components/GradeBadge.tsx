import { getGradeColor, GRADE_BG_CLASSES } from "@/lib/grades";

interface GradeBadgeProps {
  grade: string;
  size?: "sm" | "md" | "lg" | "xl";
}

const sizeClasses = {
  sm: "text-lg w-10 h-10",
  md: "text-2xl w-14 h-14",
  lg: "text-4xl w-20 h-20",
  xl: "text-6xl w-28 h-28",
};

export default function GradeBadge({ grade, size = "md" }: GradeBadgeProps) {
  const color = getGradeColor(grade);
  const bgClass = GRADE_BG_CLASSES[grade] ?? "bg-gray-500/20";

  return (
    <div
      className={`${sizeClasses[size]} ${bgClass} rounded-full flex items-center justify-center font-bold border border-white/10`}
      style={{ color }}
    >
      {grade}
    </div>
  );
}
