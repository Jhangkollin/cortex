"use client";

/**
 * Client-side providers wrapper.
 *
 * `SessionProvider` (from `next-auth/react`) is required so that
 * `useSession()` works in Client Components anywhere in the tree —
 * the persona picker, the mock-session bridge, etc. Root layout stays
 * a Server Component; this is the boundary that flips to client.
 *
 * `MockSessionProvider` wraps the localStorage-backed mock session.
 * Its internal `useSession()` bridge seeds mock state from the real
 * NextAuth session when one exists, so existing components that read
 * `useMockSession()` keep working after real OAuth lands.
 */

import { SessionProvider } from "next-auth/react";

import { MockSessionProvider } from "@/components/auth/mock-session-provider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <MockSessionProvider>{children}</MockSessionProvider>
    </SessionProvider>
  );
}
