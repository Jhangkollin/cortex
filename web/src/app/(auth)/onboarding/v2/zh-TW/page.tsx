"use client";

import { useMemo } from "react";

import { completeV2Onboarding } from "@/app/(auth)/onboarding/v2/complete-actions";
import { OnboardingV2WizardZh } from "@/components/onboarding-v2-zh/wizard";
import { getOnboardingApi } from "@/lib/onboarding/api";

export default function OnboardingV2ZhPage() {
  const api = useMemo(() => getOnboardingApi(), []);
  return (
    <OnboardingV2WizardZh
      mode="live"
      api={api}
      onComplete={completeV2Onboarding}
    />
  );
}
