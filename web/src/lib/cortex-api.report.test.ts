import { afterEach, describe, expect, it, vi } from "vitest";

import { CortexApiError, fetchBrandReport } from "./cortex-api";

const CLAIMS = {
  cortexUserId: "u1",
  email: "a@b.c",
  activeContext: {
    kind: "brand",
    id: "b1",
    role: "admin",
    capabilities: ["view_brand_dashboard"],
  },
};

afterEach(() => vi.unstubAllGlobals());

describe("fetchBrandReport", () => {
  it("returns the envelope on 200", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        async (): Promise<Response> =>
          new Response(
            JSON.stringify({ reportId: "r1", status: "ready", report: { meta: {} } }),
            { status: 200 },
          ),
      ),
    );
    const env = await fetchBrandReport(CLAIMS as never, "b1", "r1");
    expect(env.status).toBe("ready");
    expect(env.reportId).toBe("r1");
  });

  it("throws a typed CortexApiError carrying the HTTP status on 404", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (): Promise<Response> => new Response("not found", { status: 404 })),
    );
    await expect(
      fetchBrandReport(CLAIMS as never, "b1", "missing"),
    ).rejects.toMatchObject({ status: 404 });
  });

  it("CortexApiError.status reflects non-404 failures too (e.g. 500)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (): Promise<Response> => new Response("boom", { status: 500 })),
    );
    try {
      await fetchBrandReport(CLAIMS as never, "b1", "r1");
      throw new Error("expected fetchBrandReport to throw");
    } catch (err) {
      expect(err).toBeInstanceOf(CortexApiError);
      expect((err as CortexApiError).status).toBe(500);
    }
  });
});
