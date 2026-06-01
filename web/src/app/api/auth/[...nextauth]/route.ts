/**
 * NextAuth route handlers (App Router).
 *
 * Exports GET and POST exactly as NextAuth v5 expects. All config lives in
 * `@/lib/auth.ts` so server actions and middleware can share it.
 */
export { GET, POST } from "@/lib/auth";
