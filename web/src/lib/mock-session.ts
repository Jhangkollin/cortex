/**
 * Mock session — pure client-side stand-in for NextAuth + cortex-api identity.
 *
 * Lives until the real backend is wired (slice X1). Source of truth for:
 *   - whether the user is "signed in"
 *   - which persona they picked on the persona screen
 *   - their org context (name, tier)
 *   - their onboarding draft + completion flag
 *
 * Persisted to localStorage so the demo survives a browser refresh.
 *
 * IMPORTANT: this is the only auth path right now. When real NextAuth is
 * reconnected (X1 ship), this module switches to a thin adapter — every
 * consumer keeps reading `useSession()`, the source flips behind the hook.
 */

import type { OrgTier } from "@/lib/permissions";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type Persona = "brand" | "publisher" | "developer";

export interface MockUser {
  /** First-and-last or role-style label, e.g. "CMO / Wang". */
  displayName: string;
  email: string;
  /** Single grapheme used in the avatar circle. */
  initial: string;
}

export interface MockOrg {
  name: string;
  tier: OrgTier;
}

export interface OnboardingDraft {
  companyName?: string;
  shortName?: string;
  primaryDomain?: string;
  altDomains?: string;
  industry?: string;
  contactName?: string;
  contactTitle?: string;
  contactEmail?: string;
  placementTopicsIn?: string;
  placementTopicsOut?: string;
}

export interface MockSession {
  user: MockUser | null;
  org: MockOrg | null;
  persona: Persona | null;
  onboardingComplete: boolean;
  onboardingDraft: OnboardingDraft;
  /**
   * Number of real data sources the org has connected. 0 = empty Discover.
   * >0 flips Discover to the populated view. Real connections drop the
   * `demo` flag automatically (see provider) — demo and real are mutually
   * exclusive per v1.1 §06b "Not allowed: Demo mode cannot mix with real
   * data."
   */
  connectedSourceCount: number;
  /**
   * Demo data mode (v1.1 §06b). True after the user clicks "Use demo data"
   * on the empty Discover hero — Cortex serves a fixed acmebank fixture
   * and shows a persistent strip below the topbar. Cleared when the user
   * connects a real source.
   */
  demo: boolean;
}

export const EMPTY_SESSION: MockSession = {
  user: null,
  org: null,
  persona: null,
  onboardingComplete: false,
  onboardingDraft: {},
  connectedSourceCount: 0,
  demo: false,
};

// ---------------------------------------------------------------------------
// Persistence
// ---------------------------------------------------------------------------

const STORAGE_KEY = "cortex.mock-session.v1";

// Snapshot cache for useSyncExternalStore. Without this, every readSession()
// returns a fresh object → React detects "new snapshot" → re-renders → calls
// readSession() again → infinite loop. We key the cache on the raw localStorage
// string and return the same parsed object until the raw payload changes.
let cachedRaw: string | null | undefined = undefined;
let cachedSnapshot: MockSession = EMPTY_SESSION;

/**
 * Read session from localStorage. Returns EMPTY_SESSION on any failure
 * (missing key, corrupt JSON, schema drift) so a bad write can't brick
 * the demo — the user just lands at /signin again.
 *
 * The result is referentially stable across calls when the underlying
 * localStorage string hasn't changed — required by useSyncExternalStore.
 */
export function readSession(): MockSession {
  if (typeof window === "undefined") return EMPTY_SESSION;

  let raw: string | null;
  try {
    raw = window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return EMPTY_SESSION;
  }

  // Hit: same payload as last call, return the cached object.
  if (raw === cachedRaw) return cachedSnapshot;

  // Miss: reparse, recache.
  cachedRaw = raw;
  if (!raw) {
    cachedSnapshot = EMPTY_SESSION;
    return cachedSnapshot;
  }
  try {
    const parsed = JSON.parse(raw) as MockSession;
    cachedSnapshot = { ...EMPTY_SESSION, ...parsed };
  } catch {
    cachedSnapshot = EMPTY_SESSION;
  }
  return cachedSnapshot;
}

export function writeSession(s: MockSession): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  } catch {
    // localStorage quota or privacy mode — silently swallow; user can still
    // navigate during their session, but state won't survive a reload.
  }
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
}

// ---------------------------------------------------------------------------
// Demo fixture — used when "Continue with Google" is clicked
// ---------------------------------------------------------------------------

/**
 * Pre-canned brand customer for demos. Mirrors the persona shown in the
 * design handoff Discover frame ("CMO / Wang" at "Acme Bank Asia").
 * Once a real OAuth callback lands, this is replaced by the verified
 * Google profile.
 */
export const DEMO_BRAND_USER: MockUser = {
  displayName: "CMO / Wang",
  email: "wang@acmebank.asia",
  initial: "王",
};

/**
 * Fixture org paired with DEMO_BRAND_USER. Consumed by the dev-auth-bypass
 * seed in mock-session-provider; not used by the real OAuth flow.
 */
export const DEMO_BRAND_ORG: MockOrg = {
  name: "Acme Bank Asia",
  tier: "enterprise",
};
