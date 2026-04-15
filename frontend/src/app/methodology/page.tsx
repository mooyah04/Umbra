import Link from "next/link";
import {
  CATEGORY_EXPLANATIONS,
  ROLE_WEIGHT_PROFILES,
} from "@/lib/methodology";

export const metadata = {
  title: "Methodology — WoWUmbra.gg",
  description:
    "How the Umbra grading system works: role-aware category weights, keystone-level weighting, timing modifier, and what each category actually measures.",
};

const ROLE_ORDER: Array<"dps" | "healer" | "tank"> = ["dps", "healer", "tank"];
const ROLE_LABEL: Record<string, string> = {
  dps: "DPS",
  healer: "Healer",
  tank: "Tank",
};

export default function MethodologyPage() {
  // Collect every category key referenced by at least one role — this
  // gives us the columns for the weights table without hardcoding them.
  const categoryKeys = Array.from(
    new Set(
      ROLE_ORDER.flatMap((r) =>
        ROLE_WEIGHT_PROFILES[r].map((w) => w.key),
      ),
    ),
  );

  const weightFor = (role: "dps" | "healer" | "tank", key: string) =>
    ROLE_WEIGHT_PROFILES[role].find((w) => w.key === key)?.weight;

  return (
    <div className="pt-28 pb-32 px-6 md:px-12 max-w-7xl mx-auto">
      {/* Hero */}
      <section className="text-center mb-16">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-4">
          How the grade is built
        </p>
        <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-5xl md:text-7xl tracking-tighter mb-6 text-on-surface">
          METHODOLOGY
        </h1>
        <p className="max-w-3xl mx-auto text-lg text-on-surface-variant leading-relaxed">
          Every Umbra grade is a composite of five or six weighted categories,
          adjusted by how many of your keys you timed. Weights change by role
          — a tank and a DPS player aren&apos;t graded on the same things. The
          whole engine is documented here so there&apos;s no black box.
        </p>
      </section>

      {/* Role weights table */}
      <section className="mb-20">
        <div className="mb-8">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            Role weights
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            WHAT COUNTS FOR WHOM
          </h2>
          <p className="mt-3 text-on-surface-variant max-w-3xl">
            Category scores are 0-100 and feed the composite at these weights.
            Rows that don&apos;t apply to a role (e.g. healing throughput for
            a tank) are simply absent — the remaining weights redistribute.
          </p>
        </div>
        <div className="overflow-x-auto bg-surface-container-high rounded-xl">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-outline-variant/20">
                <th className="text-left px-5 py-4 font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant">
                  Category
                </th>
                {ROLE_ORDER.map((r) => (
                  <th
                    key={r}
                    className="text-right px-5 py-4 font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary"
                  >
                    {ROLE_LABEL[r]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {categoryKeys.map((key) => {
                const cat = CATEGORY_EXPLANATIONS.find((c) => c.key === key);
                return (
                  <tr
                    key={key}
                    className="border-b border-outline-variant/10 last:border-b-0"
                  >
                    <td className="px-5 py-3 text-on-surface">
                      {cat?.label ?? key}
                    </td>
                    {ROLE_ORDER.map((r) => {
                      const w = weightFor(r, key);
                      return (
                        <td
                          key={r}
                          className={`text-right px-5 py-3 font-mono ${w ? "text-on-surface" : "text-on-surface-variant/30"}`}
                        >
                          {w ? `${Math.round(w * 100)}%` : "—"}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Category deep-dive */}
      <section className="mb-20">
        <div className="mb-8">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            Categories
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            WHAT EACH ONE MEASURES
          </h2>
        </div>
        <div className="space-y-4">
          {CATEGORY_EXPLANATIONS.map((cat) => (
            <div
              key={cat.key}
              id={cat.key}
              className="bg-surface-container-high rounded-xl p-6 md:p-8 flex flex-col md:flex-row md:items-start gap-6 scroll-mt-28"
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

      {/* Mechanics: key-level + timing */}
      <section className="mb-20 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-surface-container-high rounded-xl p-8">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-3">
            Key level weighting
          </p>
          <h3 className="font-[family-name:var(--font-headline)] font-bold text-2xl text-on-surface mb-3 tracking-tight">
            HIGHER KEYS COUNT MORE
          </h3>
          <p className="text-on-surface-variant leading-relaxed">
            Inside each category, per-run scores are weight-averaged by
            keystone level. A +15 carries about 3× the weight of a +5.
            That&apos;s because pushing higher keys is the actual measure of
            skill — the scoring engine rewards it directly instead of asking
            us to infer it after the fact.
          </p>
        </div>
        <div className="bg-surface-container-high rounded-xl p-8">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-3">
            Timing modifier
          </p>
          <h3 className="font-[family-name:var(--font-headline)] font-bold text-2xl text-on-surface mb-3 tracking-tight">
            ±8 POINTS, UNIVERSAL
          </h3>
          <p className="text-on-surface-variant leading-relaxed">
            After the weighted categories sum, a timing bonus of up to +8 (or
            penalty of up to -8) is applied based on how many of your recent
            keys you timed. This is the same adjustment for every role —
            finishing the key on time matters regardless of what you pressed
            during it.
          </p>
        </div>
      </section>

      {/* Back to About */}
      <section className="mb-16 text-center">
        <Link
          href="/about"
          className="inline-flex items-center gap-2 font-[family-name:var(--font-label)] text-xs uppercase tracking-widest text-primary hover:underline"
        >
          <span className="material-symbols-outlined text-sm">
            arrow_back
          </span>
          Back to About
        </Link>
      </section>
    </div>
  );
}
