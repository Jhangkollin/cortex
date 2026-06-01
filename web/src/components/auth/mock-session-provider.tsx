"use client";

/**
 * MockSessionProvider — React context wrapping the localStorage-backed
 * mock session, projected synchronously over the real NextAuth session.
 *
 * Derivation model (the important bit):
 *
 *   baseSession   ← useSyncExternalStore(localStorage)
 *                   Holds the demo flag, onboarding draft, connected source
 *                   count, plus user/persona/onboardingComplete as a
 *                   fallback when realSession is still loading.
 *
 *   realSession   ← useSession() from next-auth/react
 *                   Authoritative source for who the user is once OAuth
 *                   completes.
 *
 *   session       ← useMemo(baseSession, realSession)
 *                   The value every consumer sees. Derived on the SAME
 *                   render that realSession flips to authenticated, so
 *                   there is no transient window where a downstream
 *                   redirect-driving consumer would see "mock empty but
 *                   real authenticated".
 *
 *   useEffect     ← persists the overlay back to localStorage. This is a
 *                   pure side-channel for cross-tab observability and
 *                   reload roundtrips — not load-bearing for any consumer
 *                   reading `useMockSession()`.
 *
 * The earlier implementation used a `useEffect` to bridge realSession into
 * the mock store. That introduced a one-render race because effects fire
 * child-first: a child component's effect would observe the empty mock
 * store before the parent's bridge effect ran, redirecting authenticated
 * users to /signin. Computing the projection synchronously here removes
 * the race by construction; consumers don't need any workaround.
 *
 * The localStorage hydration flag ("loading" → "ready") is kept private
 * to the provider — the persistence `useEffect` reads it to defer writes
 * until hydration completes — but it is no longer part of the public
 * context surface. Consumers that need to gate routing on "auth fully
 * resolved" use `isAuthReady`. `combinedStatus` remains exposed for
 * callers that want the explicit three-state enum.
 *
 * `isAuthReady` is true when both localStorage hydration and NextAuth
 * resolution have settled — gate routing decisions on this; never on
 * `combinedStatus === "loading"` directly, which couples to a specific
 * enum variant and silently flows through if the enum gains future
 * states (e.g. "refreshing", "error").
 *
 * History: the client-side `RequireOnboarded` guard once owned onboarding
 * gating and its "don't redirect before auth resolves" race was the
 * regression of record. That guard has since been retired — gating moved
 * server-side and its decision ladder (including dev-bypass and error
 * branches) is now covered by
 * `src/components/auth/__tests__/onboarding-gate.test.tsx`. The
 * `isAuthReady`-before-routing discipline above remains the contract for
 * any future client consumer that needs hydration-safe routing.
 */

import { useSession } from "next-auth/react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

import {
  clearSession,
  DEMO_BRAND_ORG,
  DEMO_BRAND_USER,
  EMPTY_SESSION,
  type MockOrg,
  type MockSession,
  type OnboardingDraft,
  type Persona,
  readSession,
  writeSession,
} from "@/lib/mock-session";

/**
 * Dev-only auth bypass. When `NEXT_PUBLIC_DEV_BYPASS_AUTH=true` is set in
 * `.env.local`, the provider seeds a fully-onboarded demo brand session on
 * first paint AND prefers the localStorage user over NextAuth's "unauth-
 * enticated" verdict in the projection. The combination lets the dev visit
 * /brand/dashboard without a real Google OAuth round-trip.
 *
 * Production builds NEVER set this flag, so the bypass branch is dead code
 * there. Read at module scope so the constant inlines and tree-shakes cleanly.
 */
const DEV_BYPASS_AUTH = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true";

type Status = "loading" | "ready";
type CombinedStatus = "loading" | "authenticated" | "unauthenticated";

interface MockSessionContextValue {
  /**
   * Folds the localStorage hydration flag together with real-auth state
   * into a single three-state enum:
   *   - "loading"         localStorage not yet hydrated, OR NextAuth loading
   *   - "authenticated"   realSession.user.email is present
   *   - "unauthenticated" NextAuth resolved with no user
   * Prefer `isAuthReady` for routing gates — it stays conservative if the
   * enum grows new variants. Use `combinedStatus` only when you need to
   * branch on the specific authenticated-vs-unauthenticated outcome.
   */
  combinedStatus: CombinedStatus;
  /**
   * True when both localStorage hydration and NextAuth resolution have
   * settled (i.e. `combinedStatus !== "loading"`). Routing decisions
   * should gate on `!isAuthReady` so future enum variants like
   * "refreshing" or "error" keep the placeholder shown instead of
   * silently flowing through.
   */
  isAuthReady: boolean;
  /** Derived session: localStorage base overlaid with realSession. */
  session: MockSession;
  /** Mock "Continue with Google" — fills user, leaves persona null. */
  signIn: () => void;
  /** Persona picker selection. Brand is the only live persona. */
  setPersona: (p: Persona) => void;
  /** Merge a patch into the onboarding draft. */
  updateDraft: (patch: Partial<OnboardingDraft>) => void;
  /** Finalize onboarding — sets org, marks complete, clears draft. */
  completeOnboarding: (org: MockOrg) => void;
  /** Connect the first real source (drops demo if it was on). */
  connectFirstSource: () => void;
  /** Flip into demo data mode (v1.1 §06b). */
  enableDemoData: () => void;
  /** Wipe everything and return to signed-out. */
  signOut: () => void;
}

const MockSessionContext = createContext<MockSessionContextValue | null>(null);

// ---------------------------------------------------------------------------
// External store — listens for "storage" so cross-tab writes are reflected,
// plus a manual notifier for same-tab writes.
// ---------------------------------------------------------------------------

const sameTabListeners = new Set<() => void>();

function subscribe(listener: () => void): () => void {
  sameTabListeners.add(listener);
  if (typeof window !== "undefined") {
    window.addEventListener("storage", listener);
  }
  return () => {
    sameTabListeners.delete(listener);
    if (typeof window !== "undefined") {
      window.removeEventListener("storage", listener);
    }
  };
}

function notifySameTab() {
  sameTabListeners.forEach((l) => l());
}

function getServerSnapshot(): MockSession {
  return EMPTY_SESSION;
}

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function MockSessionProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  // Base state lives in localStorage — demo flag, onboarding draft, and any
  // fallback identity fields. Read via useSyncExternalStore for SSR safety
  // and to dodge the "setState-in-effect" lint warning.
  const baseSession = useSyncExternalStore(
    subscribe,
    readSession,
    getServerSnapshot,
  );

  // Track whether the client has hydrated. Once true, redirect-driving
  // consumers know they're looking at real localStorage state, not the
  // SSR placeholder. The lint rule flags setState-in-effect as cascading
  // renders, but this is the hydration-detection pattern — without it,
  // RequireOnboarded would redirect on the first client paint before
  // useSyncExternalStore has read localStorage, sending onboarded users
  // back to /signin.
  const [status, setStatus] = useState<Status>("loading");
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setStatus("ready");
  }, []);

  const { data: realSession, status: realStatus } = useSession();

  // Synchronous projection: realSession + baseSession → derived session.
  // This is the bridge — but as a pure computation, NOT an effect. Every
  // render that sees realSession authenticated also sees session.user
  // populated. No "child effect runs before parent effect" race possible.
  const session = useMemo<MockSession>(() => {
    // NextAuth still resolving — fall back to the base. Once it resolves,
    // we re-derive on the same render.
    if (realStatus === "loading") {
      return baseSession;
    }
    const realEmail = realSession?.user?.email;
    if (!realEmail) {
      // Dev-only bypass: synthesise a fully-onboarded demo brand session
      // synchronously in the projection, so the very first render after
      // NextAuth resolves is already authenticated. Doing this in useMemo
      // (not useEffect) sidesteps the child-effects-first ordering trap —
      // see PR #16 / the header comment for the original incarnation of
      // this race. Without this, RequireOnboarded redirects to /signin
      // before the auto-seed effect can write to localStorage.
      //
      // Production builds NEVER set DEV_BYPASS_AUTH, so this branch is
      // dead-code eliminated.
      if (DEV_BYPASS_AUTH) {
        return {
          ...baseSession,
          user: baseSession.user ?? DEMO_BRAND_USER,
          org: baseSession.org ?? DEMO_BRAND_ORG,
          persona: baseSession.persona ?? "brand",
          onboardingComplete: true,
          // Seed demo mode so the populated DiscoverDashboard renders instead
          // of EmptyDiscover (which requires connectedSourceCount > 0 or demo).
          demo: true,
        };
      }
      // Definitely unauthenticated. Strip auth identity (drives RequireOnboarded
      // → /signin redirect) but keep client-only fields like draft / demo so
      // the user's pre-signin progress isn't yanked out from under them.
      return { ...baseSession, user: null };
    }
    const realName = realSession?.user?.name ?? realEmail;
    const hasBrandContext = realSession?.user?.activeContext?.kind === "brand";
    return {
      ...baseSession,
      user: {
        displayName: realName,
        email: realEmail,
        initial: realName.charAt(0).toUpperCase(),
      },
      // When the user has a brand active_context, treat them as past the
      // persona picker AND past the (deferred-for-MVP) wizard so the
      // dashboard renders cleanly.
      persona: hasBrandContext ? "brand" : baseSession.persona,
      onboardingComplete: hasBrandContext
        ? true
        : baseSession.onboardingComplete,
    };
  }, [baseSession, realSession, realStatus]);

  const combinedStatus = useMemo<CombinedStatus>(() => {
    if (status !== "ready" || realStatus === "loading") return "loading";
    return realSession?.user?.email ? "authenticated" : "unauthenticated";
  }, [status, realStatus, realSession]);

  const isAuthReady = combinedStatus !== "loading";

  // Dev-only auto-seed (persistence side-channel). The projection already
  // synthesised a demo session synchronously above, so this effect is NOT
  // load-bearing for the first paint — it just mirrors the demo back to
  // localStorage so devtools, cross-tab observers, and hard reloads all
  // see the same shape. Gated on the env flag — production never runs.
  useEffect(() => {
    if (!DEV_BYPASS_AUTH) return;
    if (status !== "ready") return;
    if (realStatus === "loading") return;
    if (realSession?.user?.email) return;
    if (baseSession.user) return;

    writeSession({
      ...EMPTY_SESSION,
      user: DEMO_BRAND_USER,
      org: DEMO_BRAND_ORG,
      persona: "brand",
      onboardingComplete: true,
    });
    notifySameTab();
  }, [status, realStatus, realSession, baseSession.user]);

  // Side-channel: persist the projected session back to localStorage so
  // other tabs see it and a hard reload picks up the same shape. Not
  // load-bearing — every consumer reads via the context, which already has
  // the synchronously-derived `session`. Early-return when nothing changed
  // to avoid notify-loops.
  const lastPersistedRaw = useRef<string | null>(null);
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (status !== "ready") return;
    if (realStatus === "loading") return;

    const realEmail = realSession?.user?.email;
    if (!realEmail) {
      // Real session resolved to unauthenticated. Wipe storage only if there
      // is something to wipe — first-load unauthenticated stays a no-op so
      // we don't fire a spurious storage event.
      const current = readSession();
      if (current.user !== null) {
        clearSession();
        lastPersistedRaw.current = null;
        notifySameTab();
      }
      return;
    }

    const nextRaw = JSON.stringify(session);
    if (lastPersistedRaw.current === nextRaw) return;
    lastPersistedRaw.current = nextRaw;
    writeSession(session);
    notifySameTab();
  }, [session, status, realStatus, realSession]);

  // Centralised mutator. Writes to localStorage and pings the same-tab
  // listeners so useSyncExternalStore re-reads.
  const update = useCallback(
    (patch: (prev: MockSession) => MockSession) => {
      const next = patch(readSession());
      writeSession(next);
      notifySameTab();
    },
    [],
  );

  const value = useMemo<MockSessionContextValue>(
    () => ({
      combinedStatus,
      isAuthReady,
      session,
      signIn: () =>
        update((prev) => ({ ...prev, user: DEMO_BRAND_USER })),
      setPersona: (persona) => update((prev) => ({ ...prev, persona })),
      updateDraft: (patch) =>
        update((prev) => ({
          ...prev,
          onboardingDraft: { ...prev.onboardingDraft, ...patch },
        })),
      completeOnboarding: (org) =>
        update((prev) => ({
          ...prev,
          org,
          onboardingComplete: true,
          onboardingDraft: {},
        })),
      connectFirstSource: () =>
        update((prev) => ({
          ...prev,
          connectedSourceCount: Math.max(1, prev.connectedSourceCount + 1),
          // Per v1.1 §06b: real connection drops demo automatically.
          demo: false,
        })),
      enableDemoData: () =>
        update((prev) => ({
          ...prev,
          demo: true,
        })),
      signOut: () => {
        clearSession();
        notifySameTab();
      },
    }),
    [combinedStatus, isAuthReady, session, update],
  );

  return (
    <MockSessionContext.Provider value={value}>
      {children}
    </MockSessionContext.Provider>
  );
}

export function useMockSession(): MockSessionContextValue {
  const ctx = useContext(MockSessionContext);
  if (!ctx) {
    throw new Error(
      "useMockSession must be used inside <MockSessionProvider>. Did you forget to mount it in app/layout.tsx?",
    );
  }
  return ctx;
}
