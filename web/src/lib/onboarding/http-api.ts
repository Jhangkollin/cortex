/**
 * HttpOnboardingApi — the real adapter behind the #29 OnboardingApi seam.
 *
 * `analyzeBrand` calls the Task-12 Server Actions (`startAnalyzeAction` /
 * `pollAnalyzeAction`), polls to a terminal state, and projects the
 * snake_case `BrandProfileResponse` → the camelCase UI `ExtractedBrand`
 * via SP-3's owned `toExtractedBrand` projection.
 *
 * The other 6 methods return the existing modeled constants — a conscious
 * hybrid: no backend exists for crawl tasks / media network / live questions
 * / voice tones / deploy agents / deploy log yet, so the modeled data keeps
 * the wizard whole until SP-3b (or later) wires those surfaces.
 */

import {
  pollAnalyzeAction,
  startAnalyzeAction,
} from "@/app/(auth)/onboarding/v2/analyze-actions";
import {
  pollBrandVoiceAction,
  startBrandVoiceAction,
} from "@/app/(auth)/onboarding/v2/brand-voice-actions";
import {
  pollMediaNetworkAction,
  startMediaNetworkAction,
} from "@/app/(auth)/onboarding/v2/media-actions";
import {
  pollWeeklyQuestionsAction,
  startWeeklyQuestionsAction,
} from "@/app/(auth)/onboarding/v2/weekly-questions-actions";
import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  type CrawlTask,
  type DeployAgent,
  type DeployLogLine,
  type ExtractedBrand,
  type LiveQuestion,
  type Media,
  type VoiceTone,
} from "@/components/onboarding-v2/data";

import type { OnboardingApi } from "./api";
import {
  projectMediaNetwork,
  projectVoiceTones,
  projectWeeklyQuestions,
  toExtractedBrand,
} from "./projection";

const sleep = (ms: number): Promise<void> =>
  new Promise((r) => setTimeout(r, ms));

export class HttpOnboardingApi implements OnboardingApi {
  private readonly pollMs: number;
  private readonly maxPolls: number;

  constructor(opts: { pollMs?: number; maxPolls?: number } = {}) {
    this.pollMs = opts.pollMs ?? 2000;
    this.maxPolls = opts.maxPolls ?? 90;
  }

  async analyzeBrand(url: string): Promise<ExtractedBrand> {
    const started = await startAnalyzeAction(url);
    let job = started;
    for (let i = 0; i < this.maxPolls; i++) {
      if (job.status === "succeeded") {
        if (!job.profile) {
          throw new Error("analyze succeeded without a profile");
        }
        return toExtractedBrand(job.profile);
      }
      if (job.status === "failed") {
        throw new Error(`brand analysis failed: ${job.error ?? "unknown"}`);
      }
      await sleep(this.pollMs);
      job = await pollAnalyzeAction(started.job_id);
    }
    throw new Error("brand analysis timed out");
  }

  // SP-3b / later: no backend yet — modeled data keeps the wizard whole.
  getCrawlTasks(): Promise<CrawlTask[]> {
    return Promise.resolve(CRAWL_TASKS);
  }

  async getMediaNetwork(): Promise<Media[]> {
    const started = await startMediaNetworkAction();
    let dto = started;
    for (let i = 0; i < this.maxPolls; i++) {
      if (dto.status === "succeeded") {
        return projectMediaNetwork(dto);
      }
      if (dto.status === "failed") {
        throw new Error(`media-network failed: ${dto.error ?? "unknown"}`);
      }
      await sleep(this.pollMs);
      dto = await pollMediaNetworkAction();
    }
    throw new Error("media-network timed out");
  }

  async getLiveQuestions(): Promise<LiveQuestion[]> {
    const started = await startWeeklyQuestionsAction();
    let dto = started;
    for (let i = 0; i < this.maxPolls; i++) {
      if (dto.status === "succeeded") {
        return projectWeeklyQuestions(dto);
      }
      if (dto.status === "failed") {
        throw new Error(`weekly-questions failed: ${dto.error ?? "unknown"}`);
      }
      await sleep(this.pollMs);
      dto = await pollWeeklyQuestionsAction();
    }
    throw new Error("weekly-questions timed out");
  }

  async getVoiceTones(): Promise<VoiceTone[]> {
    const started = await startBrandVoiceAction();
    let dto = started;
    for (let i = 0; i < this.maxPolls; i++) {
      if (dto.status === "succeeded") {
        return projectVoiceTones(dto);
      }
      if (dto.status === "failed") {
        throw new Error(`brand-voice failed: ${dto.error ?? "unknown"}`);
      }
      await sleep(this.pollMs);
      dto = await pollBrandVoiceAction();
    }
    throw new Error("brand-voice timed out");
  }

  getDeployAgents(): Promise<DeployAgent[]> {
    return Promise.resolve(DEPLOY_AGENTS);
  }

  getDeployLog(): Promise<DeployLogLine[]> {
    return Promise.resolve(DEPLOY_LOG);
  }
}
