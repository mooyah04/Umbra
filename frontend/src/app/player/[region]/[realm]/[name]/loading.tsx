/*
 * Exists primarily as a prefetch boundary, not for the visual skeleton.
 * Without a loading.tsx on this dynamic route, Next.js prefetches the
 * entire rendered page and keeps it in the client cache "until app
 * reload" (see docs/01-app/02-guides/prefetching.md). That made navigating
 * back to a profile after a background rescore serve the stale "Not
 * Rated" snapshot from the first visit.
 *
 * With this file present, prefetch only covers the layout above, the
 * page body refetches on every navigation, and the experimental
 * staleTimes config in next.config.ts brings the TTL to zero.
 *
 * The actual fallback is minimal — the real page renders fast enough
 * that a heavy skeleton would flash and hurt perceived performance.
 */
export default function Loading() {
  return (
    <main className="mt-24 px-6 max-w-7xl mx-auto pb-32">
      <div className="h-8" aria-hidden />
    </main>
  );
}
