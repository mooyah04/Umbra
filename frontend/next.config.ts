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
      // Next requires static >= 30. Combined with loading.tsx boundaries
      // on dynamic routes, this is effectively a no-op for profile pages.
      static: 30,
    },
  },

  async redirects() {
    return [
      {
        // Short branded URL users can share when telling others to
        // install the Umbra bot in their own Discord server. Points
        // at the OAuth2 Guild-Install authorize page with the exact
        // scopes + permissions the bot needs (Send Messages,
        // Embed Links, Use Slash Commands — nothing else).
        //
        // permanent: false (307) so we can change the destination
        // without the redirect being cached forever by browsers.
        source: "/bot",
        destination:
          "https://discord.com/oauth2/authorize?client_id=1496568641540325508&permissions=2147502080&integration_type=0&scope=bot+applications.commands",
        permanent: false,
      },
    ];
  },
};

export default nextConfig;
