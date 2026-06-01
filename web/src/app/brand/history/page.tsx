/**
 * Decision history — design handoff §08.
 *
 * Sits OUTSIDE the brand layout (the sidebar's History link routes to /history,
 * which uses its own minimal chrome). For the skeleton, render the empty state
 * the spec calls out: "You haven't asked Cortex anything yet."
 *
 * Real history rows wire up later via GET /v1/decisions with cursor pagination.
 */

import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function HistoryPage() {
  return (
    <div className="min-h-screen bg-ink-25 px-8 py-12">
      <div className="text-[11px] font-bold uppercase tracking-[0.1em] text-ink-500">
        DECISION HISTORY
      </div>
      <h1
        className="mt-3.5 mb-6 text-ink-900"
        style={{
          font: "700 42px/1.1 var(--font-sans)",
          letterSpacing: "-0.02em",
        }}
      >
        Everything you&apos;ve{" "}
        <span style={{ color: "var(--mly-teal-700)" }}>asked Cortex.</span>
      </h1>

      <div className="rounded-md border border-ink-150 bg-white p-12 text-center shadow-elev-1">
        <span
          className="material-icons-outlined text-ink-300"
          style={{ fontSize: 36 }}
          aria-hidden
        >
          history
        </span>
        <p className="mt-4 mb-6 text-base text-ink-500">
          You haven&apos;t asked Cortex anything yet.
        </p>
        <Link href="/brand/dashboard">
          <Button>Back to Discover</Button>
        </Link>
      </div>
    </div>
  );
}
