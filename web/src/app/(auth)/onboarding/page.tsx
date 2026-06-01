import Image from "next/image";
import Link from "next/link";

import { auth } from "@/lib/auth";
import { listMyBrands } from "@/lib/cortex-api";
import type { CortexTokenClaims } from "@/lib/cortex-token";
import { OnboardingChooserAddAnother } from "@/components/onboarding-chooser-add-another";

/**
 * Onboarding setup chooser (server component).
 *
 * If the caller already has any onboarded brand, we surface "Add another
 * brand" as the primary CTA above the Quick/Manual choices — that CTA runs
 * createAnotherBrandAction + session.update + redirect, so the wizard
 * restarts against a NEW brand instead of overwriting the existing one.
 *
 * For first-timers (no onboarded brand yet), the chooser keeps its original
 * two destinations exactly.
 */
export default async function OnboardingChooser() {
  let hasOnboardedBrand = false;
  const session = await auth();
  if (
    session?.user?.email &&
    session.user.cortexUserId &&
    session.user.activeContext?.kind === "brand" &&
    session.user.activeContext.id
  ) {
    const claims: CortexTokenClaims = {
      cortexUserId: session.user.cortexUserId,
      email: session.user.email,
      displayName: session.user.name ?? null,
      activeContext: session.user.activeContext,
    };
    try {
      const brands = await listMyBrands(claims);
      hasOnboardedBrand = brands.some((b) => b.onboarded_at);
    } catch {
      // Fail-open: render the chooser without the add-another CTA.
    }
  }

  return (
    <div className="min-h-screen bg-ink-25 p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center">
          <Image
            src="/brand/mlytics-logo.png"
            alt="mlytics"
            width={132}
            height={24}
            priority
            data-mly-mark="onboarding-chooser-logo"
            style={{ height: "auto" }}
          />
        </div>
        <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-brand-700">
          SET UP YOUR BRAND
        </div>
      </div>

      <h1
        className="mb-2.5"
        style={{ font: "700 40px/1.1 var(--font-sans)", letterSpacing: "-0.02em" }}
      >
        How do you want to set up?
      </h1>
      <p className="mb-9 max-w-[560px] text-base text-ink-500">
        Let Cortex extract your brand from your website, or fill the details in
        yourself. You can edit everything later in Brand settings.
      </p>

      {hasOnboardedBrand ? <OnboardingChooserAddAnother /> : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Link
          href="/onboarding/v2"
          className="flex min-h-[220px] flex-col gap-3 rounded-md border border-brand-700 bg-brand-700 p-6 text-white shadow-elev-2 transition-transform hover:translate-y-[-1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-700/40 focus-visible:ring-offset-2"
        >
          <h3 className="m-0 text-xl font-bold">Quick · AI setup</h3>
          <p className="m-0 text-sm text-brand-100">
            Enter your website. Cortex crawls it and pre-fills your brand
            profile in ~30 seconds.
          </p>
        </Link>
        <Link
          href="/onboarding/manual?step=1"
          className="flex min-h-[220px] flex-col gap-3 rounded-md border border-ink-200 bg-white p-6 transition-transform hover:translate-y-[-1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-700/40 focus-visible:ring-offset-2"
        >
          <h3 className="m-0 text-xl font-bold text-ink-900">Manual · fill a form</h3>
          <p className="m-0 text-sm text-ink-500">
            Prefer to type it yourself? Walk through a short 5-step form.
          </p>
        </Link>
      </div>
    </div>
  );
}
