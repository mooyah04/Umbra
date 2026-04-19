import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    // Zero out the client-side router cache. Player profiles and run
    // pages can change the moment a user clicks Refresh or an admin
    // script rescores them, and Next's default behavior (cache a
    // prefetched RSC payload for 5 minutes) was serving stale "Not
    // Rated" states on back-navigation. Every navigation now hits
    // the server; the backend is fast enough that this is invisible
    // to users and strictly more correct.
    staleTimes: {
      dynamic: 0,
      static: 0,
    },
  },
};

export default nextConfig;
