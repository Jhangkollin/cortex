import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/app/(auth)/onboarding/v2/analyze-actions", () => ({
  startAnalyzeAction: vi.fn(),
  pollAnalyzeAction: vi.fn(),
}));

vi.mock("@/app/(auth)/onboarding/v2/media-actions", () => ({
  startMediaNetworkAction: vi.fn(),
  pollMediaNetworkAction: vi.fn(),
}));

vi.mock("@/app/(auth)/onboarding/v2/weekly-questions-actions", () => ({
  startWeeklyQuestionsAction: vi.fn(),
  pollWeeklyQuestionsAction: vi.fn(),
}));

// brand-voice-actions is a "use server" file importing @/lib/auth → next-auth.
// Same Next.js 16 / `package.json#exports` issue as the other actions:
// without this stub, `import "./http-api"` below transitively loads
// brand-voice-actions, which loads next-auth, which fails to resolve
// `next/server`.
vi.mock("@/app/(auth)/onboarding/v2/brand-voice-actions", () => ({
  startBrandVoiceAction: vi.fn(),
  pollBrandVoiceAction: vi.fn(),
}));

import {
  pollAnalyzeAction,
  startAnalyzeAction,
} from "@/app/(auth)/onboarding/v2/analyze-actions";
import {
  pollMediaNetworkAction,
  startMediaNetworkAction,
} from "@/app/(auth)/onboarding/v2/media-actions";
import {
  pollWeeklyQuestionsAction,
  startWeeklyQuestionsAction,
} from "@/app/(auth)/onboarding/v2/weekly-questions-actions";

import { HttpOnboardingApi } from "./http-api";

const SUCCEEDED = {
  job_id: "j1",
  status: "succeeded" as const,
  profile: {
    brand_id: "b1", name: "Acme", legal_name: null, tagline: null, monogram: null,
    brand_color: null, founded: null, about: null, source_url: "acme.test",
    industry_vertical: null, primary_jurisdiction: null, category_value: "Bank",
    category_confidence: 9, category_alternatives: [], region: [],
    voice_samples: [], products: [], competitors: [], media_matches: [],
    extraction_meta: null, created_at: "x", updated_at: "x",
  },
};

describe("HttpOnboardingApi", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("analyzeBrand polls to success and projects", async () => {
    vi.mocked(startAnalyzeAction).mockResolvedValue({
      job_id: "j1",
      status: "pending",
    });
    vi.mocked(pollAnalyzeAction)
      .mockResolvedValueOnce({ job_id: "j1", status: "running" })
      .mockResolvedValueOnce(SUCCEEDED);
    const api = new HttpOnboardingApi({ pollMs: 1, maxPolls: 10 });
    const eb = await api.analyzeBrand("acme.test");
    expect(eb.name).toBe("Acme");
    expect(eb.category.value).toBe("Bank");
  });

  it("analyzeBrand throws on failed job", async () => {
    vi.mocked(startAnalyzeAction).mockResolvedValue({
      job_id: "j1",
      status: "pending",
    });
    vi.mocked(pollAnalyzeAction).mockResolvedValue({
      job_id: "j1",
      status: "failed",
      error: "boom",
    });
    const api = new HttpOnboardingApi({ pollMs: 1, maxPolls: 5 });
    await expect(api.analyzeBrand("x")).rejects.toThrow();
  });

  it("non-analyze methods still return modeled data", async () => {
    vi.mocked(startAnalyzeAction).mockResolvedValue({
      job_id: "j1",
      status: "pending",
    });
    const api = new HttpOnboardingApi();
    expect(await api.getCrawlTasks()).toBeInstanceOf(Array);
    expect(await api.getDeployLog()).toBeInstanceOf(Array);
  });

  it("getMediaNetwork polls to success and projects outlets", async () => {
    const OUTLET = {
      hostname: "aigc.cmoney.tw", member_name: "CMoney", wau: 117260, relevance: 91,
      why: "fit", topics: ["ETF"], context_agent_label: "Wealth Context", audience_descriptor: "Investors",
    };
    vi.mocked(startMediaNetworkAction).mockResolvedValue({ brand_id: "b", status: "pending", outlets: [] });
    vi.mocked(pollMediaNetworkAction).mockResolvedValue({ brand_id: "b", status: "succeeded", outlets: [OUTLET] });
    const api = new HttpOnboardingApi({ pollMs: 1, maxPolls: 10 });
    const media = await api.getMediaNetwork();
    expect(media[0].id).toBe("aigc.cmoney.tw");
    expect(media[0].weeklyReaders).toBe(117260);
  });

  it("getLiveQuestions polls to success and projects questions", async () => {
    const Q = {
      id: "q1", text: "Best ETF?", media: "CMoney", asks: 300, when: "2026-05-15",
      intent: "Evaluate", score: 91, competitorMentions: ["Cathay"],
    };
    vi.mocked(startWeeklyQuestionsAction).mockResolvedValue({ brand_id: "b", status: "pending", questions: [] });
    vi.mocked(pollWeeklyQuestionsAction).mockResolvedValue({ brand_id: "b", status: "succeeded", questions: [Q] });
    const api = new HttpOnboardingApi({ pollMs: 1, maxPolls: 10 });
    const lq = await api.getLiveQuestions();
    expect(lq[0].id).toBe("q1");
    expect(lq[0].text).toBe("Best ETF?");
    expect(lq[0].intent).toBe("Evaluate");
  });
});
