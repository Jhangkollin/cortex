/**
 * Augment NextAuth's Session and JWT types with cortex-specific fields.
 *
 * NextAuth v5 re-exports JWT from `@auth/core/jwt`, so augmentation must
 * target both the consumer path (`next-auth/jwt`) and the source path
 * (`@auth/core/jwt`) for TS to pick it up reliably.
 *
 * Fields:
 * - `cortexUserId` — AppUser UUID returned by cortex-api on first /me call.
 * - `activeContext` — currently active brand/publisher context, baked in
 *                     by the `jwt` callback after `/v1/auth/resolve-context`.
 *
 * Pattern B JWT (see `project_cortex_mvp.md` § Onboarding flow design):
 * NextAuth signs all session tokens; cortex-api enriches via callbacks.
 */

import type { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: {
      cortexUserId?: string;
      activeContext?: {
        kind: "brand" | "publisher";
        id: string;
        role: string;
        capabilities: string[];
      };
    } & DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    cortexUserId?: string;
    activeContext?: {
      kind: "brand" | "publisher";
      id: string;
      role: string;
      capabilities: string[];
    };
  }
}

declare module "@auth/core/jwt" {
  interface JWT {
    cortexUserId?: string;
    activeContext?: {
      kind: "brand" | "publisher";
      id: string;
      role: string;
      capabilities: string[];
    };
  }
}
