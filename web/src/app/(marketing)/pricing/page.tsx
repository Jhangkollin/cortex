import type { Metadata } from "next";

import {
  DEFAULT_FAQ_ITEMS,
  FaqBlock,
} from "@/components/marketing/faq-block";

import { PricingCards } from "./pricing-cards";

export const metadata: Metadata = {
  title: "Pricing · Mlytics Cortex",
  description:
    "Per seat. Per outcome. Per dollar. Start with a seat, add usage as your traffic, leads, and routed requests grow. Cancel anytime.",
};

/**
 * Public pricing page — handoff §V1 (Classic 3-up).
 *
 * Server component for crawlability and fast first paint. Interactive bits
 * (BillingToggle + the price column it controls) are lifted into the
 * `<PricingCards />` client island — see ./pricing-cards.tsx.
 *
 * Stripe checkout is intentionally not wired in this slice — the CTAs are
 * inert until X2's checkout flow lands.
 */
export default function PricingPage() {
  return (
    <main>
      <section className="bg-white px-8 pt-16 pb-6 text-center">
        <p className="font-bold uppercase tracking-[0.1em] text-xs text-brand-700">
          Mlytics Cortex · Pricing
        </p>
        <h1 className="mx-auto mt-3.5 mb-3.5 max-w-3xl text-5xl font-bold leading-[1.05] tracking-[-0.02em] text-ink-900">
          Per seat. <span className="text-brand-700">Per outcome.</span> Per
          dollar.
        </h1>
        <p className="mx-auto max-w-xl text-lg text-ink-500">
          Start with a seat. Add usage as your traffic, leads, and routed
          requests grow. Cancel anytime.
        </p>
        <div className="mt-7 flex justify-center">{/* toggle below */}</div>
      </section>

      <PricingCards />

      <section className="bg-white px-8 pb-14 pt-2 text-center text-sm text-ink-500">
        Need to see every difference side by side?{" "}
        <a
          href="#compare"
          className="font-semibold text-brand-700 hover:text-brand-800"
        >
          Compare all plans
        </a>{" "}
        · Procurement docs (SOC 2, DPA, MSA) on the Enterprise plan
      </section>

      <FaqBlock items={DEFAULT_FAQ_ITEMS} />
    </main>
  );
}
