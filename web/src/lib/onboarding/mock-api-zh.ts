/**
 * MockOnboardingApiZh — zh-Hant sibling of MockOnboardingApi.
 *
 * Sources from the zh-Hant data tree (components/onboarding-v2-zh/data.ts)
 * so the zh demo route renders Traditional Chinese mock brand, products,
 * media, questions, voice tones, and deploy log entries instead of the EN
 * defaults.
 *
 * The OnboardingApi type signature is the same as the EN sibling — the zh
 * data file exports structurally identical types, just with localised
 * string values. Wizard components don't need to know which adapter is in
 * use.
 */

import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  EXTRACTED_BRAND,
  LIVE_QUESTIONS,
  MEDIA_NETWORK,
  VOICE_TONES,
} from "@/components/onboarding-v2-zh/data";
import type {
  CrawlTask,
  DeployAgent,
  DeployLogLine,
  ExtractedBrand,
  LiveQuestion,
  Media,
  VoiceTone,
} from "@/components/onboarding-v2-zh/data";

import type { OnboardingApi } from "./api";

export class MockOnboardingApiZh implements OnboardingApi {
  analyzeBrand(_url: string): Promise<ExtractedBrand> {
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
