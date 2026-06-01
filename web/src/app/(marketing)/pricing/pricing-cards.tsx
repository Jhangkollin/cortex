"use client";

import { useState } from "react";

import {
  BillingToggle,
  type BillingPeriod,
} from "@/components/marketing/billing-toggle";
import { TierCard } from "@/components/marketing/tier-card";
import { TIERS } from "@/lib/pricing/tiers";

/**
 * Client island that owns the BillingPeriod state and renders the 3-up tier
 * grid. The surrounding hero + FAQ stay on the server. Lifting the toggle
 * into this single island avoids re-rendering the entire page on each click
 * and keeps the static parts crawlable as plain HTML.
 */
export function PricingCards() {
  const [billing, setBilling] = useState<BillingPeriod>("monthly");

  return (
    <>
      <div className="flex justify-center pb-8">
        <BillingToggle value={billing} onChange={setBilling} />
      </div>
      <div className="grid grid-cols-1 gap-4 px-8 pb-12 lg:grid-cols-3">
        {TIERS.map((tier) => (
          <TierCard key={tier.id} tier={tier} billing={billing} />
        ))}
      </div>
    </>
  );
}
