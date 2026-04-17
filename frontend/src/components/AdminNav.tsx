import Link from "next/link";

/**
 * Shared top-of-page nav for /admin/* routes. Shows which admin section
 * you're on and links to the other ones. Admin pages aren't linked from
 * the public nav, so this is the primary navigation between them.
 */
export default function AdminNav() {
  const items: Array<{ href: string; label: string }> = [
    { href: "/admin/bug-reports", label: "Bug Reports" },
    { href: "/admin/downloads", label: "Downloads" },
  ];
  return (
    <nav className="flex gap-4 mb-6">
      {items.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="font-[family-name:var(--font-label)] text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-primary transition-colors"
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
