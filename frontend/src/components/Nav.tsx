import Link from "next/link";

export default function Nav() {
  return (
    <>
      {/* Desktop TopAppBar */}
      <header className="fixed top-0 w-full z-50 flex items-center justify-between px-6 h-16 bg-[#0e0e0e]">
        <Link href="/" className="flex items-center gap-3">
          <span className="material-symbols-outlined text-primary">analytics</span>
          <h1 className="text-2xl font-black text-primary tracking-tighter italic font-[family-name:var(--font-headline)] uppercase">
            WoWUmbra<span className="text-on-surface">.gg</span>
          </h1>
        </Link>
        <div className="flex items-center gap-6">
          <nav className="hidden md:flex gap-8">
            <Link
              href="/"
              className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-primary"
            >
              Search
            </Link>
            <Link
              href="#"
              className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface hover:text-primary transition-colors"
            >
              Trends
            </Link>
            <Link
              href="#"
              className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface hover:text-primary transition-colors"
            >
              History
            </Link>
          </nav>
          <span className="material-symbols-outlined text-primary cursor-pointer scale-95 duration-100">
            search
          </span>
        </div>
      </header>

      {/* Mobile BottomNavBar */}
      <nav className="md:hidden fixed bottom-0 w-full z-50 flex justify-around items-center h-20 px-4 bg-[#0e0e0e]/90 backdrop-blur-xl">
        <Link
          href="/"
          className="flex flex-col items-center justify-center text-primary border-t-2 border-primary pt-1"
        >
          <span className="material-symbols-outlined">search</span>
          <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest">
            Search
          </span>
        </Link>
        <Link
          href="#"
          className="flex flex-col items-center justify-center text-on-surface/50 pt-1 hover:text-primary"
        >
          <span className="material-symbols-outlined">query_stats</span>
          <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest">
            Trends
          </span>
        </Link>
        <Link
          href="#"
          className="flex flex-col items-center justify-center text-on-surface/50 pt-1 hover:text-primary"
        >
          <span className="material-symbols-outlined">history</span>
          <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest">
            History
          </span>
        </Link>
        <Link
          href="#"
          className="flex flex-col items-center justify-center text-on-surface/50 pt-1 hover:text-primary"
        >
          <span className="material-symbols-outlined">account_circle</span>
          <span className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest">
            Profile
          </span>
        </Link>
      </nav>
    </>
  );
}
