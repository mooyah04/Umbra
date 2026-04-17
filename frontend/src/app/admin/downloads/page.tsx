import DownloadsAdmin from "./DownloadsAdmin";
import AdminNav from "@/components/AdminNav";

export const metadata = {
  title: "Download Stats Admin | WoWUmbra",
  description: "Internal view of addon download counts.",
  robots: { index: false, follow: false },
};

export default function DownloadsAdminPage() {
  return (
    <main className="min-h-screen pt-32 pb-24 px-6 md:px-12 max-w-6xl mx-auto">
      <AdminNav />
      <header className="mb-8">
        <p className="font-[family-name:var(--font-label)] text-xs uppercase tracking-[0.3em] text-primary mb-2">
          Admin : Downloads
        </p>
        <h1 className="font-[family-name:var(--font-headline)] font-extrabold text-4xl md:text-5xl tracking-tighter text-on-surface">
          ADDON DOWNLOADS
        </h1>
        <p className="text-on-surface-variant text-sm mt-3">
          Total downloads over time, plus recent windows and unique-IP sanity
          checks against bot reload loops.
        </p>
      </header>
      <DownloadsAdmin />
    </main>
  );
}
