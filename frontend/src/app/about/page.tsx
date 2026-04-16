import Link from "next/link";
import { DESIGN_PRINCIPLES, DIFFERENTIATORS } from "@/lib/methodology";

export const metadata = {
  title: "About · WoWUmbra.gg",
  description:
    "A Mythic+ performance grading tool for players who take the game seriously. Transparent, receipts-backed, built to help you improve. Not to replace your judgment.",
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
          A Mythic+ performance grading tool built for two things: helping
          you see exactly where your play needs work, and helping you find
          groupmates who take the game as seriously as you do.
          Every grade drills down to the specific events that produced it:
          kicks, avoidable damage, cooldown presses.
        </p>
      </section>

      {/* Mission */}
      <section className="mb-20">
        <div className="bg-surface-container-high rounded-xl p-8 md:p-12">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-4">
            Why we built it
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-4xl tracking-tighter text-on-surface mb-6">
            EVERYONE&apos;S TIME IS PRECIOUS.
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-on-surface-variant leading-relaxed">
            <p>
              If you&apos;re a player who wants to push keys, you already know
              the wall: you run a dungeon with people who are gearing up to
              parse, not to time, and three hours later you&apos;ve learned
              nothing about your own play. The tools that exist tell you{" "}
              <span className="text-on-surface">what</span> people achieved,
              not <span className="text-on-surface">how</span> they play.
              Umbra tells you the second.
            </p>
            <p>
              We built this to be a self-improvement mirror first, and a
              vetting tool second. Look yourself up, read the breakdown, and
              you&apos;ll know exactly which habits are holding your keys
              back. Look up someone you&apos;re inviting, and you&apos;ll
              know if their grade matches their promises.
            </p>
          </div>
        </div>
      </section>

      {/* What we provide */}
      <section className="mb-20">
        <div className="mb-10">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            What we provide
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            EVERYTHING LINKS TO EVIDENCE
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {WHAT_WE_PROVIDE.map((f) => (
            <div
              key={f.title}
              className="bg-surface-container rounded-xl p-6 border-l-2 border-primary/40"
            >
              <div className="flex items-start gap-4">
                <span className="material-symbols-outlined text-primary text-2xl mt-1">
                  {f.icon}
                </span>
                <div>
                  <h3 className="font-[family-name:var(--font-headline)] font-bold text-lg text-on-surface mb-2 tracking-tight">
                    {f.title}
                  </h3>
                  <p className="text-sm text-on-surface-variant leading-relaxed">
                    {f.body}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Use alongside IO + Gearscore */}
      <section className="mb-20">
        <div className="bg-gradient-to-br from-surface-container-high to-surface-container rounded-xl p-8 md:p-12">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-4">
            How to use it
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-4xl tracking-tighter text-on-surface mb-6">
            USE IT ALONGSIDE <span className="text-primary italic">EVERYTHING ELSE.</span>
          </h2>
          <p className="text-on-surface-variant leading-relaxed mb-8 max-w-3xl">
            Umbra doesn&apos;t replace IO. It doesn&apos;t replace item level.
            Each tool answers a different question, and the three together
            give you a signal no single one can:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ToolCard
              title="Item level"
              question="What did they gear up to?"
              role="How much pressure their kit can apply. Necessary but not sufficient."
            />
            <ToolCard
              title="IO score"
              question="What have they actually completed?"
              role="Proven ceiling and consistency at key levels. Doesn't show how they got there."
            />
            <ToolCard
              title="Umbra grade"
              question="How do they play under the hood?"
              role="Kicks, positioning, cooldown usage, survivability. The difference between a timed and a depleted key."
            />
          </div>
          <p className="text-sm text-on-surface-variant mt-8 max-w-3xl leading-relaxed">
            A player with high IO + low Umbra grade is a carry-passenger.
            A player with low IO + high Umbra grade is someone ready to
            push, they just haven&apos;t been given the keys. A player with
            both is the groupmate you want. That&apos;s the information
            asymmetry we&apos;re trying to close.
          </p>
        </div>
      </section>

      {/* Anti-toxicity / our commitments */}
      <section className="mb-20">
        <div className="mb-10">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            On the gatekeeping question
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface">
            A RATING CAN&apos;T STAY HONEST BY BEING HIDDEN.
          </h2>
        </div>
        <div className="bg-surface-container-high rounded-xl p-8 md:p-10">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-on-surface-variant leading-relaxed mb-8">
            <div>
              <p className="mb-4">
                Raider.IO was called toxic when it launched. Players argued
                it would turn every LFG into a gated meritocracy. By 2022 it
                was the default way to vet groups, because transparent data
                is less toxic than rumor, reputation, and guess.
              </p>
              <p>
                Any rating system can be misused. We can&apos;t stop that.
                What we can do is make the system itself as honest and as
                transparent as possible, so the misuse is obvious when it
                happens and the data actually helps more than it hurts.
              </p>
            </div>
            <div>
              <p className="mb-4">
                The right stance isn&apos;t &quot;no ratings.&quot; It&apos;s
                &quot;ratings you can argue with.&quot; If you disagree with
                your Umbra grade, you can open your run breakdown, see every
                event that drove it, cross-check against the source WCL log,
                and tell us what&apos;s wrong. Rumors don&apos;t let you do
                that. Pugs don&apos;t let you do that.
              </p>
              <p>
                We&apos;d rather ship a grade you can disprove than a vibe
                you can&apos;t.
              </p>
            </div>
          </div>

          <div className="border-t border-outline-variant/20 pt-6">
            <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-4">
              Our commitments, in code, not words
            </p>
            <ul className="space-y-3">
              {COMMITMENTS.map((c) => (
                <li
                  key={c.title}
                  className="flex gap-3 text-on-surface-variant text-sm leading-relaxed"
                >
                  <span className="material-symbols-outlined text-primary text-sm mt-0.5 shrink-0">
                    check_circle
                  </span>
                  <span>
                    <span className="text-on-surface font-semibold">
                      {c.title}.
                    </span>{" "}
                    {c.body}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
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

      {/* Methodology teaser */}
      <section className="mb-20">
        <Link
          href="/methodology"
          className="block bg-surface-container-high rounded-xl p-8 md:p-10 group hover:bg-surface-bright transition-colors relative overflow-hidden"
        >
          <span className="material-symbols-outlined absolute top-6 right-6 text-primary text-5xl opacity-20 group-hover:opacity-40 transition-opacity">
            rule
          </span>
          <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary mb-3">
            Deeper reading
          </p>
          <h2 className="font-[family-name:var(--font-headline)] font-bold text-3xl md:text-5xl tracking-tighter text-on-surface mb-3">
            FULL METHODOLOGY{" "}
            <span className="text-primary italic">→</span>
          </h2>
          <p className="text-on-surface-variant leading-relaxed max-w-3xl mb-4">
            Role weights, category-by-category explanations, the keystone
            weighting curve, and the universal timing stat. Every input
            that produces a composite grade, written up end-to-end.
          </p>
          <span className="inline-flex items-center gap-2 font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary">
            Read the methodology
            <span className="material-symbols-outlined text-sm">
              arrow_forward
            </span>
          </span>
        </Link>
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
              The grade is the beginning, not the end. Our next phase adds
              an AI coach that reads your per-run pull breakdown and gives
              spec-specific, dungeon-specific advice: which kicks you missed,
              which defensives you hoarded, which mechanics killed you. We
              won&apos;t ship the coach until the grades it&apos;s built on
              are rock solid, because a confident wrong answer is worse
              than no answer.
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

function ToolCard({
  title,
  question,
  role,
}: {
  title: string;
  question: string;
  role: string;
}) {
  return (
    <div className="bg-surface-container-high rounded-lg p-5">
      <p className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-[0.3em] text-primary mb-1">
        {title}
      </p>
      <p className="font-[family-name:var(--font-headline)] font-bold text-on-surface text-lg mb-3 tracking-tight">
        {question}
      </p>
      <p className="text-sm text-on-surface-variant leading-relaxed">{role}</p>
    </div>
  );
}

/** What we ship today. Every item is a live feature, not a promise. */
const WHAT_WE_PROVIDE = [
  {
    icon: "grade",
    title: "A role-aware letter grade, S+ to F-",
    body: "One composite number per character, computed from six weighted categories tailored to how tanks, healers, and DPS actually contribute. Updates automatically as you run keys.",
  },
  {
    icon: "quiz",
    title: "A category breakdown you can argue with",
    body: "See exactly how much of your grade came from interrupts vs. survivability vs. damage. Every category links back to the specific numbers it's scored against. No opaque composites.",
  },
  {
    icon: "dataset",
    title: "A per-dungeon breakdown",
    body: "Your overall grade hides which dungeons you're actually struggling with. We compute a separate grade per dungeon from just that dungeon's runs, so weaknesses are obvious at a glance.",
  },
  {
    icon: "account_tree",
    title: "A pull-by-pull recap of every run",
    body: "Click any run and see what happened, pull by pull: the kicks you hit, the avoidable damage you ate, the pulls you died in. The whole dungeon in a 30-second read.",
  },
  {
    icon: "extension",
    title: "A free addon that surfaces grades in-game",
    body: "Tooltips in the world and in Group Finder show grades inline: yours and everyone else's. No signup, no account, no payment. Download, install, it just works.",
  },
  {
    icon: "refresh",
    title: "Fresh data without a manual refresh",
    body: "Run a key, upload to Warcraft Logs (the addon can auto-toggle combat logging), and we re-ingest your character on the next scheduled sweep, usually within a few hours of upload. Looking yourself up on the site triggers an immediate ingest if you want it sooner.",
  },
];

/** Concrete commitments. Every line describes a mechanism, not a promise. */
const COMMITMENTS = [
  {
    title: "Your grade is never hidden from you",
    body: "Every player page shows the composite, the category breakdown, the per-dungeon grades, and the per-run pull events. You can always see what produced your number.",
  },
  {
    title: "No pay-to-upgrade tiers",
    body: "The addon is free. The website is free. There will not be a Pro plan that shows you extra digits of your score.",
  },
  {
    title: "No selling user data",
    body: "The only thing we ingest is combat logs you already publish to Warcraft Logs. We don't collect anything else, and we don't sell what we do have.",
  },
  {
    title: "Dungeon ability data is sourced from live logs, not guesses",
    body: "Every 'avoidable damage' ability in our scoring comes from a cross-log sampler that reads the top 20 speed-runs per dungeon each week. No curated list, no editorial favoritism. If top players take damage from it and good players avoid it, we track it.",
  },
  {
    title: "Open roadmap, open tradeoffs",
    body: "We ship changelogs and we write up the scoring changes we make, including the ones that hurt our own characters. Category weights and benchmarks change when the data proves the old ones wrong.",
  },
];
