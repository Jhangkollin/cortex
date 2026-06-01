/// <reference types="vitest" />
import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/**
 * Vitest harness for cortex-web.
 *
 * - jsdom environment so React components that touch `window` /
 *   `localStorage` / `document` work without a browser.
 * - Path alias `@/*` mirrors the `tsconfig.json` alias so test files can
 *   import production code via `@/components/...`.
 * - `globals: true` exposes `describe` / `it` / `expect` without explicit
 *   imports — matches the @testing-library docs and keeps tests terse.
 * - `setupFiles` runs once per test file before user code, registering
 *   jest-dom matchers and clearing localStorage between tests.
 *
 * Test discovery globs are intentionally broad:
 *   - Co-located: `src/**\/__tests__/*.test.tsx`
 *   - Cross-cutting: `tests/**\/*.test.tsx`
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
      "@tests": path.resolve(__dirname, "./tests"),
      // `cortex-api.ts` starts with `import "server-only"`. The real
      // `server-only` package's default export throws by design and is not
      // resolvable under vitest, so map it to an empty stub. Shared test
      // infra: SP-3a web tasks 12-14 transitively import cortex-api.ts too.
      "server-only": path.resolve(__dirname, "src/test/server-only-stub.ts"),
    },
  },
  test: {
    environment: "jsdom",
    // `src/lib/cortex-api*` is pure server-side code (no DOM). Run it under
    // `node` so cross-realm checks in `jose` (Uint8Array `instanceof`) pass —
    // jsdom's separate realm makes the encoded secret fail `jose`'s guard.
    // `src/lib/onboarding/onboarding-api-client*` imports cortex-api directly
    // and likewise must run under node for the same jose cross-realm reason.
    // Everything else stays jsdom for React component tests.
    environmentMatchGlobs: [
      ["src/lib/cortex-api*.{test,spec}.{ts,tsx}", "node"],
      ["src/lib/onboarding/onboarding-api-client.{test,spec}.{ts,tsx}", "node"],
    ],
    globals: true,
    // Dummy values so `cortex-api.ts`'s server-only helpers reach `fetch`
    // under test: `signCortexApiToken` requires `NEXTAUTH_SECRET` and
    // `apiBase()` requires `CORTEX_API_URL`. Test infra (no real network /
    // signing happens — `fetch` is stubbed), shared by SP-3a web tasks.
    env: {
      NEXTAUTH_SECRET: "test-secret-not-used-for-real-signing",
      CORTEX_API_URL: "http://cortex-api.test",
    },
    setupFiles: ["./tests/setup.ts"],
    include: [
      "src/**/*.{test,spec}.{ts,tsx}",
      "tests/**/*.{test,spec}.{ts,tsx}",
    ],
    css: false,
  },
});
