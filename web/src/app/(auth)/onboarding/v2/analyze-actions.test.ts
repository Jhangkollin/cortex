import { describe, expect, it, vi } from "vitest";

import type { Session } from "next-auth";

vi.mock("@/lib/cortex-api", () => ({
  startAnalyze: vi.fn(
    async (): Promise<{ job_id: string; status: string }> => ({
      job_id: "j1",
      status: "pending",
    }),
  ),
  pollAnalyze: vi.fn(
    async (): Promise<{
      job_id: string;
      status: string;
      profile: { name: string };
    }> => ({
      job_id: "j1",
      status: "succeeded",
      profile: { name: "Acme" },
    }),
  ),
}));

// Real session helper is `auth()` from `@/lib/auth` (NextAuth v5). The
// session shape mirrors `web/src/types/next-auth.d.ts`: `session.user`
// carries `cortexUserId`, `activeContext`, plus the NextAuth default
// `name`/`email`. Server Actions derive `brandId` from
// `session.user.activeContext.id` (see existing `completeBrandOnboarding`).
const SESSION: Session = {
  user: {
    name: "Founder",
    email: "a@b.c",
    cortexUserId: "u1",
    activeContext: {
      kind: "brand",
      id: "b1",
      role: "admin",
      capabilities: ["edit_brand_settings"],
    },
  },
  expires: "2099-01-01T00:00:00.000Z",
};

vi.mock("@/lib/auth", () => ({
  auth: vi.fn(async (): Promise<Session> => SESSION),
}));

import { pollAnalyzeAction, startAnalyzeAction } from "./analyze-actions";

describe("analyze server actions", () => {
  it("startAnalyzeAction returns the dto using session brandId", async () => {
    expect((await startAnalyzeAction("acme.test")).job_id).toBe("j1");
  });
  it("pollAnalyzeAction returns the terminal dto", async () => {
    expect((await pollAnalyzeAction("j1")).status).toBe("succeeded");
  });
});
