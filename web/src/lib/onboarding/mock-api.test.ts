/**
 * MockOnboardingApi — unit tests.
 *
 * Assert that each method resolves to the exact same data as the corresponding
 * seed constant in data.ts.  These tests act as a regression guard: if the
 * constants change shape or value, the tests will catch divergence between the
 * mock adapter and the source of truth.
 */

import { describe, expect, it } from "vitest";

import {
  CRAWL_TASKS,
  DEPLOY_AGENTS,
  DEPLOY_LOG,
  EXTRACTED_BRAND,
  LIVE_QUESTIONS,
  MEDIA_NETWORK,
  VOICE_TONES,
} from "@/components/onboarding-v2/data";

import { MockOnboardingApi } from "./mock-api";

describe("MockOnboardingApi", () => {
  const api = new MockOnboardingApi();

  it("analyzeBrand() resolves to EXTRACTED_BRAND regardless of url argument", async () => {
    const result = await api.analyzeBrand("acmebank.asia");
    expect(result).toEqual(EXTRACTED_BRAND);
  });

  it("analyzeBrand() resolves to EXTRACTED_BRAND for any url", async () => {
    const result = await api.analyzeBrand("some-other-url.com");
    expect(result).toEqual(EXTRACTED_BRAND);
  });

  it("getCrawlTasks() resolves to CRAWL_TASKS", async () => {
    const result = await api.getCrawlTasks();
    expect(result).toEqual(CRAWL_TASKS);
  });

  it("getMediaNetwork() resolves to MEDIA_NETWORK", async () => {
    const result = await api.getMediaNetwork();
    expect(result).toEqual(MEDIA_NETWORK);
  });

  it("getLiveQuestions() resolves to LIVE_QUESTIONS", async () => {
    const result = await api.getLiveQuestions();
    expect(result).toEqual(LIVE_QUESTIONS);
  });

  it("getVoiceTones() resolves to VOICE_TONES", async () => {
    const result = await api.getVoiceTones();
    expect(result).toEqual(VOICE_TONES);
  });

  it("getDeployAgents() resolves to DEPLOY_AGENTS", async () => {
    const result = await api.getDeployAgents();
    expect(result).toEqual(DEPLOY_AGENTS);
  });

  it("getDeployLog() resolves to DEPLOY_LOG", async () => {
    const result = await api.getDeployLog();
    expect(result).toEqual(DEPLOY_LOG);
  });

  it("all methods return Promises", () => {
    expect(api.analyzeBrand("x.com")).toBeInstanceOf(Promise);
    expect(api.getCrawlTasks()).toBeInstanceOf(Promise);
    expect(api.getMediaNetwork()).toBeInstanceOf(Promise);
    expect(api.getLiveQuestions()).toBeInstanceOf(Promise);
    expect(api.getVoiceTones()).toBeInstanceOf(Promise);
    expect(api.getDeployAgents()).toBeInstanceOf(Promise);
    expect(api.getDeployLog()).toBeInstanceOf(Promise);
  });
});
