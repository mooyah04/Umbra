import BugReportsAdmin from "./BugReportsAdmin";

export const metadata = {
  title: "Bug Reports Admin — WoWUmbra",
  description: "Internal triage view for incoming bug reports.",
  robots: { index: false, follow: false },
};

export default function BugReportsAdminPage() {
  return (
    <main className="min-h-screen pt-32 pb-24 px-6 md:px-12 max-w-6xl mx-auto">
      <header className="mb-8">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
          Admin · Triage
        </p>
        <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-4xl md:text-5xl tracking-tighter text-on-surface">
          BUG REPORTS
        </h1>
        <p className="text-on-surface-variant text-sm mt-3">
          Requires the admin API key. Key is stored in{" "}
          <code className="bg-surface-container-high px-2 py-0.5 rounded">
            localStorage
          </code>{" "}
          on this device only.
        </p>
      </header>
      <BugReportsAdmin />
    </main>
  );
}
