import type { Metadata } from "next";
import { Suspense } from "react";

import { DemoOnboardingZhClient } from "./client";

export const metadata: Metadata = {
  title: "Cortex · 體驗版",
};

export default function DemoOnboardingZhPage() {
  // <Suspense> is required by Next when a descendant calls
  // useSearchParams() — the prerender phase has no URL params and would
  // bail out without a fallback boundary. The wizard mounts immediately
  // when the client takes over, so the empty fallback is never visible.
  return (
    <Suspense fallback={null}>
      <DemoOnboardingZhClient />
    </Suspense>
  );
}
