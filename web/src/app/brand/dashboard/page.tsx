"use client";

/**
 * Brand dashboard — Cortex Discover v2.0 (default landing for Brand Customer).
 *
 * The Brand IQ report hero + one-time celebration (`<BrandReportSurface/>`)
 * render ABOVE the empty/populated split so a freshly-onboarded brand — which
 * has 0 connected sources and shows <EmptyDiscover/> — still sees its first
 * report and the celebration. (Previously the report surface lived inside
 * <DiscoverDashboard/> and never showed for empty brands.)
 *
 * Stage below the surface, switched on `connectedSourceCount` (spec §2,
 * decision 6):
 *   - 0 sources & not demo → EmptyDiscover ("—" everywhere + connect CTA)
 *   - otherwise            → DiscoverDashboard (v2 stage tree, mock data)
 *
 * The `.geo-app` shell + color-bridge seam are owned by `BrandShell`
 * (`@/components/shell/brand-shell.tsx`), rendered by the parent
 * `/brand/layout.tsx`, so the sidebar can collapse without remounting this
 * page. The ⌘K trigger + docked Cortex drawer are also mounted at that shell
 * level (plan F3/R6) — this page only mounts the report surface + chooses the
 * empty vs. populated stage.
 */

import { Suspense } from "react";

import { useSearchParams } from "next/navigation";

import { useMockSession } from "@/components/auth/mock-session-provider";
import { BrandReportSurface } from "@/components/brand-dashboard/brand-report-surface";
import { DiscoverDashboard } from "@/components/brand-dashboard/discover/discover-dashboard";
import { EmptyDiscover } from "@/components/brand-dashboard/empty-discover";

function BrandDashboardContent() {
  const { session } = useMockSession();

  // Deterministic local/QA trigger for the Brand IQ celebration:
  // `?celebrate=preview` renders the celebration from a fixture (no cortex-api).
  const preview = useSearchParams().get("celebrate") === "preview";

  const isEmpty = !session.demo && session.connectedSourceCount === 0;

  return (
    <div className="pg sp">
      {/* Brand IQ report hero + one-time celebration — renders for both empty
          and populated brands (a just-onboarded brand has 0 sources). */}
      <BrandReportSurface preview={preview} />
      {isEmpty ? <EmptyDiscover /> : <DiscoverDashboard />}
    </div>
  );
}

export default function BrandDashboardPage() {
  // useSearchParams() requires a Suspense boundary to satisfy Next.js 16's
  // static-prerender bailout for client-side query-param reads.
  return (
    <Suspense fallback={null}>
      <BrandDashboardContent />
    </Suspense>
  );
}
