/**
 * Global vitest setup — runs once per test file before user code.
 *
 * Responsibilities:
 *   1. Register `@testing-library/jest-dom` matchers (`toBeInTheDocument`,
 *      `toHaveTextContent`, etc.) on vitest's `expect`.
 *   2. Hoist module-level mocks for `next-auth/react` and `next/navigation`
 *      so every test file sees them. The mock implementations read from
 *      mutable holders exported by `tests/helpers/session-mock-state.ts`,
 *      which tests drive via `setMockSession()` / `router`.
 *   3. Tear down DOM and localStorage between tests so MockSessionProvider's
 *      `useSyncExternalStore` reads a clean baseSession in each test —
 *      otherwise a write in test N would bleed into test N+1.
 */
import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

import {
  resetMockSession,
  resetRouter,
} from "@tests/helpers/session-mock-state";

// `vi.mock` is hoisted to the top of the file. Because this setup file is
// listed in `vitest.config.ts` setupFiles, these mocks apply to every test
// file that imports `next-auth/react` or `next/navigation` (directly or via
// the component-under-test). The factories below dynamically import the
// state holder so they can read the latest test-controlled values on every
// call without breaking hoisting.
vi.mock("next-auth/react", async () => {
  const state = await import("./helpers/session-mock-state");
  return {
    useSession: () => ({ ...state.getMockSession(), update: vi.fn() }),
    SessionProvider: ({ children }: { children: React.ReactNode }) => children,
    signIn: vi.fn(),
    signOut: vi.fn(),
  };
});

vi.mock("next/navigation", async () => {
  const state = await import("./helpers/session-mock-state");
  return {
    useRouter: () => state.router,
    usePathname: () => "/",
    useSearchParams: () => new URLSearchParams(),
  };
});

afterEach(() => {
  cleanup();
  if (typeof window !== "undefined") {
    window.localStorage.clear();
  }
  // Reset mutable singletons so a test that DOESN'T call `renderWithSession`
  // (or asserts on `router` without `beforeEach(resetRouter)`) still starts
  // from a clean baseline. `renderWithSession` overwrites `currentSession`
  // anyway, but defence-in-depth is cheap.
  resetMockSession();
  resetRouter();
});
