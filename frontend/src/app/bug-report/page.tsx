import BugReportForm from "@/components/BugReportForm";

export const metadata = {
  title: "Report a Bug | WoWUmbra",
  description: "Send us a bug report from the website or the addon.",
};

export default function BugReportPage() {
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
      <BugReportForm />
    </main>
  );
}
