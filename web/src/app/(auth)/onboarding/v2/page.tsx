"use client";

import { useMemo } from "react";

import { completeV2Onboarding } from "@/app/(auth)/onboarding/v2/complete-actions";
import { OnboardingV2Wizard } from "@/components/onboarding-v2/wizard";
import { getOnboardingApi } from "@/lib/onboarding/api";

export default function OnboardingV2Page() {
  // useMemo so the api instance is stable across re-renders. The factory
  // returns a fresh class instance each call; the wizard's deps arrays
  // expect a stable reference.
  const api = useMemo(() => getOnboardingApi(), []);
  return (
    <OnboardingV2Wizard
      mode="live"
      api={api}
      onComplete={completeV2Onboarding}
    />
  );
}
