"use client";

import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

import { OnboardingV2Wizard } from "@/components/onboarding-v2/wizard";
import { MockOnboardingApi } from "@/lib/onboarding/mock-api";

export function DemoOnboardingClient() {
  // Force the mock adapter regardless of the build-time NEXT_PUBLIC_CORTEX_ONBOARDING_HTTP
  // flag. The demo flow is auth-free; it must never hit real cortex-api.
  const api = useMemo(() => new MockOnboardingApi(), []);
  // Kiosk auto-play flags. `?auto=1` advances the wizard through every step
  // without clicks; `?loop=1` (only with auto=1) restarts at step 7 so the
  // URL can be left running on a TV / demo screen.
  const searchParams = useSearchParams();
  const autoPlay = searchParams.get("auto") === "1";
  const loop = searchParams.get("loop") === "1";
  return (
    <OnboardingV2Wizard mode="demo" api={api} autoPlay={autoPlay} loop={loop} />
  );
}
