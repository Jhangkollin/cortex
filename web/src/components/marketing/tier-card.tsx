import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import type { BillingPeriod } from "./billing-toggle";
import type { Tier } from "@/lib/pricing/tiers";

export interface TierCardProps {
  tier: Tier;
  billing: BillingPeriod;
  className?: string;
}

/**
 * One pricing tier card — renders a Tier from `lib/pricing/tiers.ts`.
 *
 * Featured variant is driven by `tier.popular`: 2px brand-700 border,
 * elev-2 shadow, "MOST POPULAR" amber ribbon notched 12px above the card.
 * Padding stays at 27px on featured (vs 28px default) to maintain optical
 * size — see handoff §V1 spec.
 *
 * CTA visual variant maps to friction level, NOT to cta.kind alone:
 *   dev (low-stakes Stripe) → soft   — "try it"
 *   pro (conversion target) → primary — the natural pick
 *   ent (high-touch sales)  → dark    — committed motion
 */
export function TierCard({ tier, billing, className }: TierCardProps) {
  const featured = tier.popular;
  const price = billing === "annual" ? tier.price.annual : tier.price.monthly;
  const ctaVariant = pickCtaVariant(tier);

  return (
    <article
      aria-label={`${tier.name} plan`}
      className={cn(
        "relative flex flex-col gap-3.5 rounded-md bg-white",
        featured
          ? "border-2 border-brand-700 p-[27px] shadow-elev-2"
          : "border border-ink-200 p-7",
        className,
      )}
    >
      {featured ? (
        <Badge
          variant="beta"
          className="absolute -top-3 left-1/2 -translate-x-1/2"
        >
          Most popular
        </Badge>
      ) : null}

      <h3 className="m-0 flex items-center gap-2 text-xl font-bold text-ink-900">
        {tier.name}
        <TierPill tierId={tier.id} />
      </h3>
      <p className="m-0 text-sm text-ink-500">{tier.who}</p>

      <div className="mt-2 flex items-end gap-1.5">
        <span className="font-numeric text-5xl font-bold leading-none tracking-[-0.02em] text-ink-900">
          ${price}
        </span>
        <span className="pb-2 text-sm text-ink-500">
          / {tier.unit} / {billing === "annual" ? "month, billed yearly" : "month"}
        </span>
      </div>
      <p className="m-0 font-mono text-xs text-ink-500">{tier.priceHelp}</p>

      <ul className="mt-1.5 flex flex-col gap-2 border-t border-ink-100 pt-4">
        {tier.features.map((feature) => (
          <li
            key={feature.label}
            className={cn(
              "grid grid-cols-[18px_1fr] items-start gap-2 text-sm leading-snug",
              feature.included ? "text-ink-800" : "text-ink-500",
            )}
          >
            <span
              aria-hidden
              className={cn(
                "material-icons-outlined mt-px text-lg",
                feature.included ? "text-brand-600" : "text-ink-400",
              )}
            >
              {feature.included ? "check" : "close"}
            </span>
            <span>{feature.label}</span>
          </li>
        ))}
      </ul>

      <div className="mt-auto pt-4">
        <Button variant={ctaVariant} className="w-full">
          {tier.cta.label}
        </Button>
        <p className="mt-1.5 text-center font-mono text-[11px] text-ink-400">
          {tier.ctaHelp}
        </p>
      </div>
    </article>
  );
}

function TierPill({ tierId }: { tierId: Tier["id"] }) {
  if (tierId === "ent") return <Badge variant="ent">Ent</Badge>;
  return <Badge variant="live">Live</Badge>;
}

function pickCtaVariant(tier: Tier): "soft" | "primary" | "dark" {
  if (tier.cta.kind === "sales") return "dark";
  return tier.popular ? "primary" : "soft";
}
