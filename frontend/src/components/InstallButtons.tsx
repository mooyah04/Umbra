import { CURSEFORGE_ADDON_URL, WAGO_ADDON_URL } from "@/lib/api";

type Size = "sm" | "md" | "lg";

interface Props {
  /** Visual scale. `sm` for nav-bar and footer, `md` for hero, `lg` for
   *  the prominent install card. */
  size?: Size;
  /** Render on its own centered line instead of inline with siblings. */
  centered?: boolean;
  /** Optional extra className on the container. */
  className?: string;
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: "text-[10px] px-3 py-2",
  md: "text-xs px-5 py-3",
  lg: "text-[11px] px-4 py-3",
};

/**
 * Side-by-side "Install via CurseForge" / "Install via Wago" buttons.
 * Used everywhere we previously surfaced a single "Download Addon" CTA.
 * Both links open in new tabs — managers launch externally.
 */
export default function InstallButtons({
  size = "md",
  centered = false,
  className = "",
}: Props) {
  const sizing = SIZE_CLASSES[size];
  return (
    <div
      className={`flex flex-wrap gap-2 ${centered ? "justify-center" : ""} ${className}`}
    >
      <a
        href={CURSEFORGE_ADDON_URL}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-flex items-center justify-center gap-2 bg-primary text-on-primary font-[family-name:var(--font-label)] uppercase tracking-widest rounded hover:brightness-110 transition-all ${sizing}`}
      >
        <span className="material-symbols-outlined text-sm">open_in_new</span>
        CurseForge
      </a>
      <a
        href={WAGO_ADDON_URL}
        target="_blank"
        rel="noopener noreferrer"
        className={`inline-flex items-center justify-center gap-2 border border-primary/40 text-primary font-[family-name:var(--font-label)] uppercase tracking-widest rounded hover:bg-primary/10 transition-all ${sizing}`}
      >
        <span className="material-symbols-outlined text-sm">open_in_new</span>
        Wago
      </a>
    </div>
  );
}
