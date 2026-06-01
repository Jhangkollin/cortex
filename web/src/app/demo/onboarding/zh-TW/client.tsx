"use client";

import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { OnboardingV2WizardZh } from "@/components/onboarding-v2-zh/wizard";
import { MockOnboardingApiZh } from "@/lib/onboarding/mock-api-zh";

export function DemoOnboardingZhClient() {
  // Force the zh-aware mock adapter so the wizard renders Traditional
  // Chinese mock data (brand, products, media, questions, voice tones,
  // deploy log). The demo flow is auth-free and must never hit real
  // cortex-api regardless of the build-time NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP
  // flag.
  const api = useMemo(() => new MockOnboardingApiZh(), []);
  // Kiosk auto-play flags. `?auto=1` advances the wizard through every step
  // without clicks; `?loop=1` (only with auto=1) restarts at step 7 so the
  // URL can be left running on a TV / demo screen.
  const searchParams = useSearchParams();
  const autoPlay = searchParams.get("auto") === "1";
  const loop = searchParams.get("loop") === "1";
  return (
    <OnboardingV2WizardZh mode="demo" api={api} autoPlay={autoPlay} loop={loop} />
  );
}
