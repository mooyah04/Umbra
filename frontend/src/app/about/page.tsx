import Link from "next/link";
import {
  CATEGORY_EXPLANATIONS,
  DESIGN_PRINCIPLES,
  DIFFERENTIATORS,
} from "@/lib/methodology";

export const metadata = {
  title: "About — WoWUmbra.gg",
  description:
    "How Umbra grades M+ performance: the categories, the weights, and why we think this approach is fairer than what's out there.",
};

export default function AboutPage() {
  return (
    <div className="pt-28 pb-32 px-6 md:px-12 max-w-7xl mx-auto">
      {/* Hero */}
      <section className="text-center mb-20">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-4">
          What Umbra is
        </p>
        <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-5xl md:text-7xl lg:text-8xl tracking-tighter mb-8 text-on-surface">
          GRADES WITH{" "}
          <span className="text-primary italic">RECEIPTS.</span>
        </h1>
        <p className="max-w-3xl mx-auto text-lg text-on-surface-variant leading-relaxed">
          Umbra is a Mythic+ performance grading system for World of Warcraft.
          Every grade we show is backed by combat-log evidence from Warcraft
          Logs, weighted against role-appropriate benchmarks, and reduced to a
          single letter from <span className="text-primary font-bold">S+</span>{" "}
          to <span className="text-on-surface-variant font-bold">F-</span> that
          reflects how a player actually performed.
        </p>
      </section>

      {/* Principles */}
      <section className="mb-20">
        <div className="mb-10">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            Principles
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            HOW WE BUILD A FAIR GRADE
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {DESIGN_PRINCIPLES.map((p) => (
            <div
              key={p.title}
              className="bg-surface-container-high rounded-xl p-8 relative overflow-hidden"
            >
              <span className="material-symbols-outlined absolute top-6 right-6 text-primary text-4xl opacity-20">
                {p.icon}
              </span>
              <h3 className="font-[family-name:var(--font-headline)] font-bold text-xl text-on-surface mb-3 pr-12">
                {p.title}
              </h3>
              <p className="text-on-surface-variant leading-relaxed">
                {p.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* How we differ */}
      <section className="mb-20">
        <div className="mb-10">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            Why Umbra
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            WHAT MAKES US DIFFERENT
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {DIFFERENTIATORS.map((d, idx) => (
            <div
              key={d.title}
              className="bg-surface-container rounded-xl p-6 border-t-2"
              style={{
                borderColor: ["#8a2be2", "#00e600", "#ffaa00", "#3fc7eb"][idx],
              }}
            >
              <h3 className="font-[family-name:var(--font-headline)] font-bold text-lg text-on-surface mb-3">
                {d.title}
              </h3>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                {d.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Categories methodology */}
      <section className="mb-20">
        <div className="mb-10">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            Methodology
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            WHAT WE MEASURE
          </h2>
          <p className="mt-4 text-on-surface-variant max-w-3xl">
            Seven categories feed a composite score. Role weights are listed
            on each player&apos;s page so you can see exactly how their grade
            was computed.
          </p>
        </div>
        <div className="space-y-4">
          {CATEGORY_EXPLANATIONS.map((cat) => (
            <div
              key={cat.key}
              className="bg-surface-container-high rounded-xl p-6 md:p-8 flex flex-col md:flex-row md:items-start gap-6"
            >
              <div className="flex items-center gap-4 md:w-64 flex-shrink-0">
                <div className="w-14 h-14 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="material-symbols-outlined text-primary text-3xl">
                    {cat.icon}
                  </span>
                </div>
                <div>
                  <h3 className="font-[family-name:var(--font-headline)] font-bold text-xl text-on-surface tracking-tight">
                    {cat.label}
                  </h3>
                  <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant mt-1">
                    {cat.roles.join(" • ")}
                  </p>
                </div>
              </div>
              <div className="flex-1 space-y-3">
                <p className="text-on-surface leading-relaxed">
                  {cat.description}
                </p>
                <div className="bg-surface-container-low rounded p-4 border-l-2 border-primary/40">
                  <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary mb-1">
                    Improve
                  </p>
                  <p className="text-sm text-on-surface-variant">
                    {cat.howToImprove}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* What's next */}
      <section className="mb-20">
        <div className="bg-gradient-to-br from-primary-container to-surface-container-highest rounded-xl p-10 md:p-14 relative overflow-hidden">
          <span className="material-symbols-outlined absolute -bottom-6 -right-6 text-primary opacity-5 text-[12rem]">
            query_stats
          </span>
          <div className="relative z-10 max-w-3xl">
            <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-3">
              Roadmap
            </p>
            <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-primary-container mb-6">
              HONEST GRADES, THEN COACHING.
            </h2>
            <p className="text-on-primary-container/90 leading-relaxed mb-6">
              The grade is the beginning, not the end. Our next phase adds an
              AI coach that reads your per-run breakdown and gives
              spec-specific, dungeon-specific advice: which kicks you missed,
              which defensives you hoarded, which mechanics killed you. We
              won&apos;t ship the coach until the grades it&apos;s built on
              are rock solid — because a confident wrong answer is worse than
              no answer.
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 bg-primary text-on-primary font-[family-name:var(--font-label)] text-xs px-5 py-3 uppercase tracking-widest font-bold rounded hover:brightness-110 transition-all"
            >
              Look up a player
              <span className="material-symbols-outlined text-sm">
                arrow_forward
              </span>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
