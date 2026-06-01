import { afterEach, describe, expect, it, vi } from "vitest";

import { pollAnalyze, startAnalyze } from "./cortex-api";

const CLAIMS = {
  cortexUserId: "u1",
  email: "a@b.c",
  activeContext: { kind: "brand", id: "b1", role: "admin", capabilities: ["edit_brand_settings"] },
};

afterEach(() => vi.unstubAllGlobals());

describe("cortex-api analyze", () => {
  it("startAnalyze POSTs and returns the job dto", async () => {
    let capturedUrl: string | undefined;
    let capturedInit: RequestInit | undefined;
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        capturedUrl = String(input);
        capturedInit = init;
        return new Response(JSON.stringify({ job_id: "j1", status: "pending" }), { status: 202 });
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const dto = await startAnalyze(CLAIMS as never, "b1", "acme.test");
    expect(dto.job_id).toBe("j1");
    expect(capturedUrl).toMatch(/\/v1\/brand\/b1\/profile\/analyze$/);
    expect(capturedInit?.method).toBe("POST");
  });

  it("pollAnalyze throws on !ok", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (): Promise<Response> => new Response("nope", { status: 500 })),
    );
    await expect(pollAnalyze(CLAIMS as never, "b1", "j1")).rejects.toThrow();
  });
});
