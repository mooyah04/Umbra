import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/next";
import Nav from "@/components/Nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "WoWUmbra.gg | M+ Performance Grading",
  description:
    "Deep-audit performance grading for World of Warcraft Mythic+. Search players, analyze runs, and track improvement.",
  // Next.js auto-detects app/icon.png + app/apple-icon.png +
  // app/opengraph-image.png by filename; the openGraph block below just
  // fills in the social-preview fields that aren't derivable from file
  // conventions (site name, title, etc).
  openGraph: {
    type: "website",
    siteName: "WoWUmbra.gg",
    title: "WoWUmbra.gg | M+ Performance Grading",
    description:
      "Deep-audit performance grading for World of Warcraft Mythic+.",
    url: "https://wowumbra.gg",
  },
  twitter: {
    card: "summary_large_image",
    title: "WoWUmbra.gg | M+ Performance Grading",
    description:
      "Deep-audit performance grading for World of Warcraft Mythic+.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark h-full antialiased">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-surface text-on-surface font-[family-name:var(--font-body)] selection:bg-primary selection:text-on-primary overflow-x-hidden">
        <div className="bg-error-container text-on-surface text-sm text-center px-4 py-2 border-b border-error/40">
          Our hosting provider (Railway) is experiencing an outage — player lookups and data updates are temporarily unavailable. Track status at{" "}
          <a
            href="https://status.railway.com"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:text-error"
          >
            status.railway.com
          </a>
          .
        </div>
        <Nav />
        <main className="flex-1">{children}</main>
        <Analytics />
      </body>
    </html>
  );
}
