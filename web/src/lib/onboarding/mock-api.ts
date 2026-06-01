/**
 * MockOnboardingApi — returns the existing seed constants from data.ts.
 *
 * All methods resolve synchronously (via Promise.resolve) with exactly the
 * same data as the original hardcoded imports, so the wizard UI sees no
 * behavioural change.  This class is the only place that imports the seed
 * constants; wizard components reach them through getOnboardingApi() instead.
 *
 * Do NOT delete data.ts — this adapter sources from it.
 */

import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  EXTRACTED_BRAND,
  LIVE_QUESTIONS,
  MEDIA_NETWORK,
  VOICE_TONES,
} from "@/components/onboarding-v2/data";
import type {
  CrawlTask,
  DeployAgent,
  DeployLogLine,
  ExtractedBrand,
  LiveQuestion,
  Media,
  VoiceTone,
} from "@/components/onboarding-v2/data";

import type { OnboardingApi } from "./api";

export class MockOnboardingApi implements OnboardingApi {
  analyzeBrand(_url: string): Promise<ExtractedBrand> {
    // In production, _url drives the crawl request.
    // Mock ignores it and returns the seed brand data unchanged.
    return Promise.resolve(EXTRACTED_BRAND);
  }

  getCrawlTasks(): Promise<CrawlTask[]> {
    return Promise.resolve(CRAWL_TASKS);
  }

  getMediaNetwork(): Promise<Media[]> {
    return Promise.resolve(MEDIA_NETWORK);
  }

  getLiveQuestions(): Promise<LiveQuestion[]> {
    return Promise.resolve(LIVE_QUESTIONS);
  }

  getVoiceTones(): Promise<VoiceTone[]> {
    return Promise.resolve(VOICE_TONES);
  }

  getDeployAgents(): Promise<DeployAgent[]> {
    return Promise.resolve(DEPLOY_AGENTS);
  }

  getDeployLog(): Promise<DeployLogLine[]> {
    return Promise.resolve(DEPLOY_LOG);
  }
}
