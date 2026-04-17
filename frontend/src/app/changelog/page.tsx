import Link from "next/link";
import { CHANGELOG, type ChangelogCategory } from "@/lib/changelog";

export const metadata = {
  title: "Changelog | WoWUmbra.gg",
  description:
    "What's changed on WoWUmbra.gg: new features, improvements, fixes. Newest first.",
};

// 6 hour ISR — changelog is edited by hand and doesn't need to be live.
export const revalidate = 21600;

const CATEGORY_CONFIG: Record<
  ChangelogCategory,
  { label: string; color: string }
> = {
  new: { label: "New", color: "#8a2be2" },
  improved: { label: "Improved", color: "#3fc7eb" },
  fixed: { label: "Fixed", color: "#ffaa00" },
};

export default function ChangelogPage() {
  // Group entries by date so a single date shows as one block with
  // multiple items under it — reads more naturally than repeating dates.
  const byDate = new Map<string, typeof CHANGELOG>();
  for (const entry of CHANGELOG) {
    const arr = byDate.get(entry.date) ?? [];
    arr.push(entry);
    byDate.set(entry.date, arr);
  }
  const dates = [...byDate.keys()].sort().reverse();

  return (
    <main className="pt-28 pb-32 px-6 md:px-12 max-w-4xl mx-auto">
      <section className="mb-12">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-3">
          What&apos;s changed
        </p>
        <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-5xl md:text-7xl tracking-tighter mb-4 text-on-surface">
          CHANGELOG
        </h1>
        <p className="text-on-surface-variant max-w-2xl leading-relaxed">
          Every user-visible change to the site, the scoring engine, and
          the addon. Newest first. If you spot a regression or want to
          understand why a grade moved, start here.
        </p>
      </section>

      <ol className="space-y-12">
        {dates.map((date) => (
          <li key={date}>
            <header className="flex items-baseline gap-3 mb-4 pb-2 border-b border-outline-variant/15">
              <span className="font-[family-name:var(--font-label)] text-[11px] uppercase tracking-[0.3em] text-primary">
                {formatDate(date)}
              </span>
              <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant/60 tabular-nums">
                {date}
              </span>
            </header>
            <ul className="space-y-5">
              {(byDate.get(date) ?? []).map((entry, i) => {
                const cfg = CATEGORY_CONFIG[entry.category];
                return (
                  <li key={i} className="flex gap-4">
                    <span
                      className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest font-bold shrink-0 w-20 pt-1"
                      style={{ color: cfg.color }}
                    >
                      {cfg.label}
                    </span>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-[family-name:var(--font-body)] font-semibold text-on-surface mb-1">
                        {entry.title}
                      </h3>
                      <p className="text-sm text-on-surface-variant leading-relaxed">
                        {entry.body}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </li>
        ))}
      </ol>

      <section className="mt-16 pt-8 border-t border-outline-variant/10 text-center">
        <p className="text-sm text-on-surface-variant">
          Found a regression? Think something should be here that isn&apos;t?{" "}
          <Link
            href="/bug-report"
            className="text-primary hover:underline font-semibold"
          >
            Let us know
          </Link>
          .
        </p>
      </section>
    </main>
  );
}

function formatDate(iso: string): string {
  // "2026-04-16" → "April 16, 2026"
  const d = new Date(iso + "T00:00:00Z");
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
}
