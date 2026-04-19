import BugReportForm from "@/components/BugReportForm";

interface Props {
  searchParams: Promise<{ type?: string }>;
}

export const metadata = {
  title: "Report a Bug or Suggest a Feature | WoWUmbra",
  description:
    "Send us a bug report, or suggest a feature for the site or the addon.",
};

// Shared intake page for bugs and suggestions. The nav link sends
// suggestions here with ?type=suggestion so the page copy and the
// form's placeholders reframe around ideas instead of breakage —
// submissions still land in the same admin queue, prefixed in the
// summary so the two are visually separable.
export default async function BugReportPage({ searchParams }: Props) {
  const { type } = await searchParams;
  const mode = type === "suggestion" ? "suggestion" : "bug";

  if (mode === "suggestion") {
    return (
      <main className="min-h-screen pt-32 pb-24 px-6 md:px-12 max-w-3xl mx-auto">
        <header className="mb-10">
          <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
            Share An Idea
          </p>
          <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-4xl md:text-6xl tracking-tighter text-on-surface mb-4">
            SUGGEST A FEATURE
          </h1>
          <p className="text-on-surface-variant">
            Missing a stat you want to see? A tooltip layout that would
            help? A grading category that doesn&apos;t sit right? Tell us
            what you&apos;d build.
          </p>
          <p className="text-on-surface-variant text-sm mt-3">
            Found an actual bug instead? Head to the{" "}
            <a
              href="/bug-report"
              className="text-primary hover:underline"
            >
              bug report page
            </a>
            .
          </p>
        </header>
        <BugReportForm mode="suggestion" />
      </main>
    );
  }

  return (
    <main className="min-h-screen pt-32 pb-24 px-6 md:px-12 max-w-3xl mx-auto">
      <header className="mb-10">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
          Tell Us What Broke
        </p>
        <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-4xl md:text-6xl tracking-tighter text-on-surface mb-4">
          REPORT A BUG
        </h1>
        <p className="text-on-surface-variant">
          Seen something wrong? Bad grade, busted tooltip, something looks off
          on a player page? Tell us below. The more detail the faster we can
          fix it.
        </p>
        <p className="text-on-surface-variant text-sm mt-3">
          <span className="text-primary">Reporting an addon bug?</span> Run{" "}
          <code className="bg-surface-container-high px-2 py-0.5 rounded">/umbra bug</code>{" "}
          in-game, copy the output WoW gives you, paste it into the{" "}
          <span className="italic">Details</span> box below, and select
          &quot;Addon&quot; as the source.
        </p>
      </header>
      <BugReportForm mode="bug" />
    </main>
  );
}
