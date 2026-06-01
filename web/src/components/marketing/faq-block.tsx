import { cn } from "@/lib/utils";

export interface FaqItem {
  q: string;
  a: string;
}

export interface FaqBlockProps {
  items: readonly FaqItem[];
  className?: string;
}

/**
 * Pricing FAQ block — native details/summary so the surface is keyboard-
 * accessible without JS. Spec §FAQ: first card is `open` by default so the
 * surface doesn't look closed; +/− glyph is Noto Sans (kept optically square).
 */
export function FaqBlock({ items, className }: FaqBlockProps) {
  return (
    <section className={cn("bg-white px-8 py-12", className)}>
      <h2 className="m-0 mb-6 text-2xl font-bold tracking-[-0.01em] text-ink-900">
        Questions, before you buy.
      </h2>
      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2">
        {items.map((item, i) => (
          <details
            key={item.q}
            open={i === 0}
            className="group rounded-md border border-ink-200 bg-white px-5 py-4.5"
          >
            <summary
              className={cn(
                "flex cursor-pointer items-center justify-between gap-3.5",
                "text-base font-bold text-ink-900",
                "list-none [&::-webkit-details-marker]:hidden",
              )}
            >
              <span>{item.q}</span>
              <span
                aria-hidden
                className="text-xl font-bold leading-none text-brand-700"
              >
                <span className="group-open:hidden">+</span>
                <span className="hidden group-open:inline">−</span>
              </span>
            </summary>
            <p className="mt-3 text-sm leading-relaxed text-ink-500">
              {item.a}
            </p>
          </details>
        ))}
      </div>
    </section>
  );
}

/**
 * Default FAQ content — 8 questions from handoff §FAQ. Exported so the page
 * composes the block without re-declaring strings; product / marketing can
 * mutate this list independently of the layout.
 */
export const DEFAULT_FAQ_ITEMS: readonly FaqItem[] = [
  {
    q: "What's a 'seat' in Cortex?",
    a: "One human login. Seats are billed by the named user, not by login session. Teammates invited from the Org admin page each consume one seat regardless of role.",
  },
  {
    q: "How do usage meters work?",
    a: "Two meters on the Brand plan: AI-surface scrapes (drives the KPI cards) and qualified leads (drives Lead Pilot). Each plan includes a baseline; overage bills monthly at the listed rate.",
  },
  {
    q: "Can I mix tiers in one org?",
    a: "No. All seats in an org are on the same plan. Mix-and-match would mean the same team sees different parts of the app, which we found in user testing felt broken, not flexible.",
  },
  {
    q: "Is there a free tier?",
    a: "No free production tier. Developer ($20/seat) ships with a 14-day no-card trial. Pro ships with a 14-day card-required trial that auto-converts to monthly. Enterprise pilots are arranged through sales.",
  },
  {
    q: "What happens at the end of a Pro trial?",
    a: "Auto-converts to monthly Pro at $50/seat starting on day 15. You can cancel from Org admin at any time during the trial with no charge.",
  },
  {
    q: "How do I get a DPA / SOC 2 report?",
    a: "DPA is available on request for Pro customers. SOC 2 Type II, ISO 27001, and the full security pack are bundled with Enterprise. Book a sales call for procurement requests.",
  },
  {
    q: "What's 'Coming soon' for Content Owners and Developers?",
    a: "Brand is the live tier in 2026 Q2. Content Owner pricing ships when Media GEO publisher monetization is live (target Q3). Developer pricing ships alongside the unified LLM gateway (target Q3–Q4).",
  },
  {
    q: "Annual discount?",
    a: "20% off list price when billed annually on Developer and Pro. Enterprise pricing already includes annual commit; volume tiers stack on top.",
  },
];
