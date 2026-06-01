/**
 * Mutable holders for the next-auth + next/navigation mocks.
 *
 * The mocks themselves live in `tests/setup.ts` (must be at module-load
 * time for `vi.mock` hoisting). The mocks read from these holders on every
 * call, so tests can flip session state or assert on `router.replace` /
 * `router.push` calls without re-mocking.
 *
 * `currentSession` is reset to `DEFAULT` between tests by `tests/setup.ts`'s
 * `afterEach` (via `resetMockSession()`) — any test that doesn't call
 * `renderWithSession` (which writes via `setMockSession`) still starts from
 * a clean baseline.
 */
import { vi } from "vitest";
import type { Session } from "next-auth";

export interface SessionState {
  data: Session | null;
  status: "loading" | "authenticated" | "unauthenticated";
}

const DEFAULT: SessionState = { data: null, status: "loading" };
let currentSession: SessionState = { ...DEFAULT };

export function getMockSession(): SessionState {
  return currentSession;
}

export function setMockSession(next: SessionState): void {
  currentSession = next;
}

export function resetMockSession(): void {
  currentSession = { ...DEFAULT };
}

/**
 * Mutable router stub. Tests assert on `.mock.calls` directly:
 *
 *   expect(router.replace).toHaveBeenCalledWith("/signin");
 *
 * Cleared per-test in the test file's `beforeEach`.
 */
export const router = {
  replace: vi.fn(),
  push: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  refresh: vi.fn(),
  prefetch: vi.fn(),
};

export function resetRouter(): void {
  router.replace.mockClear();
  router.push.mockClear();
  router.back.mockClear();
  router.forward.mockClear();
  router.refresh.mockClear();
  router.prefetch.mockClear();
}
