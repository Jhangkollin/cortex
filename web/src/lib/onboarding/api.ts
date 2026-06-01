/**
 * OnboardingApi — typed async seam between the wizard UI and its data source.
 *
 * The interface is intentionally thin: each method maps to a discrete wizard
 * step or a data-set the page needs at initialisation time.  Return types
 * re-export the domain types from the existing `data.ts` module so no new
 * type definitions are introduced — callers import from here or from data.ts
 * interchangeably.
 *
 * zh-TW adopts the same OnboardingApi — follow-up.
 *
 * Contract note (SP-3): the mock returns the `data.ts` shapes directly, but the
 * backend `cortex-brand-extract` `BrandProfile` is NOT a 1:1 passthrough — it
 * is snake_case, omits UI-only fields (`id`, `picked`, `icon`) and derived
 * counts (`productMoreCount`), and has nullable strings. `HttpOnboardingApi`
 * (the real adapter) is the projection layer that MUST translate
 * `BrandProfile` → `ExtractedBrand`: snake→camel casing, null-coalescing,
 * UI-field synthesis, and `productMoreCount` derivation. Do not assume
 * passthrough when wiring the real client.
 *
 * Swap point: `getOnboardingApi()` in this file currently returns
 * MockOnboardingApi.  When the cortex-api client is ready, instantiate
 * HttpOnboardingApi there instead (see SEAM comment below).
 */

export type {
  CrawlTask,
  ExtractedBrand,
  Media,
  LiveQuestion,
  VoiceTone,
  DeployAgent,
  DeployLogLine,
} from "@/components/onboarding-v2/data";

import type {
  CrawlTask,
  ExtractedBrand,
  Media,
  LiveQuestion,
  VoiceTone,
  DeployAgent,
  DeployLogLine,
} from "@/components/onboarding-v2/data";

import { HttpOnboardingApi } from "./http-api";
import { MockOnboardingApi } from "./mock-api";

export interface OnboardingApi {
  /**
   * Analyse a brand URL and return the extracted brand profile.
   * In the mock adapter this resolves immediately with the seed data.
   * In production this will call the cortex-api crawl endpoint and poll.
   */
  analyzeBrand(url: string): Promise<ExtractedBrand>;

  /**
   * Fetch the crawl-animation task list shown during step 1 (the crawl screen).
   * Each task has a `delay` field that drives the animation timing — the mock
   * returns the original CRAWL_TASKS array unchanged.
   */
  getCrawlTasks(): Promise<CrawlTask[]>;

  /**
   * Return the full media network for this brand context.
   * Used during step 3 (media selection), step 5 (launch summary), step 6
   * (deploy overlay), and step 7 (complete screen).
   */
  getMediaNetwork(): Promise<Media[]>;

  /**
   * Return the live reader questions sampled for this week.
   * Used during step 4 (weekly questions).
   */
  getLiveQuestions(): Promise<LiveQuestion[]>;

  /**
   * Return the available brand voice tone presets.
   * Used during step 5 (launch settings — voice tone picker).
   */
  getVoiceTones(): Promise<VoiceTone[]>;

  /**
   * Return the agent manifest used during the deploy overlay animation (step 6).
   */
  getDeployAgents(): Promise<DeployAgent[]>;

  /**
   * Return the deploy log lines streamed during the deploy overlay (step 6).
   */
  getDeployLog(): Promise<DeployLogLine[]>;
}

/**
 * Factory — the single drop-in point for the concrete implementation.
 * Import and call this anywhere data is needed; do NOT import the concrete
 * class directly from wizard components.
 *
 * SEAM: swap `new MockOnboardingApi()` for `new HttpOnboardingApi(baseUrl)`
 *       when SP-3 (cortex-api brand_profile / agent-deploy endpoints) lands.
 */
export function getOnboardingApi(): OnboardingApi {
  // SEAM (SP-3a): real adapter behind a flag; default stays mock.
  if (process.env.NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP === "1") {
    return new HttpOnboardingApi();
  }
  return new MockOnboardingApi();
}
