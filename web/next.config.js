/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  turbopack: {
    root: __dirname,
  },
  reactStrictMode: true,
  // Re-enabled now that /history, /brand/dashboard/{cortex,nexus} exist.
  // If you add a new route referenced by Link/router.push, that route must
  // exist (or be added to staticRoutes/dynamicRoutes) or build will fail.
  typedRoutes: true,
  // GTM citation-network demo. The file lives at public/demo.html (a
  // self-contained, auth-free static asset — there is no edge middleware,
  // so public/ is reachable without sign-in, which is the point for
  // prospect engagement). This rewrite serves it at the clean /demo path
  // while keeping the browser URL as /demo (rewrite, not redirect). Not a
  // typedRoutes route — nothing links to it via <Link>; it's a shared URL.
  async rewrites() {
    return [{ source: "/demo", destination: "/demo.html" }];
  },
};

module.exports = nextConfig;
