"use client";

/**
 * BrandReportSurfaceView — pure presentational view for the Brand IQ report
 * surface (hero + one-time celebration).
 *
 * This component holds ZERO data-fetching and ZERO effects. It is driven
 * entirely by props: the owning component decides what to show and supplies the
 * report envelope plus the interaction callbacks. Splitting presentation out
 * this way lets the hero + celebration be rendered with a fixture and no
 * backend (see `report-surface-fixture.ts`).
 *
 * Render rules (mirrors the legacy `brand-report-surface.tsx` JSX):
 *   - nothing to show → return null (no markup)
 *   - hero  → `<BrandReportHero/>` when `showHero && report`
 *   - modal → `<BrandReportCelebration/>` when `showCelebration && report`
 */

import type { ReactElement } from "react";

import type { ReportEnvelope } from "@/app/brand/dashboard/report-types";

import { BrandReportHero } from "./discover/brand-report-hero";
import { BrandReportCelebration } from "./discover/brand-report-celebration";

export interface BrandReportSurfaceViewProps {
  showHero: boolean;
  showCelebration: boolean;
  report: ReportEnvelope | null;
  heroDismissed: boolean;
  onDismissHero: () => void;
  onRetry: () => void;
  onCloseCelebration: () => void;
}

export function BrandReportSurfaceView({
  showHero,
  showCelebration,
  report,
  heroDismissed,
  onDismissHero,
  onRetry,
  onCloseCelebration,
}: BrandReportSurfaceViewProps): ReactElement | null {
  if (!showHero && !showCelebration) return null;

  return (
    <>
      {/* Hero — sits above the stage, collapses when dismissed */}
      {showHero && report && (
        <BrandReportHero
          report={report}
          heroDismissed={heroDismissed}
          onDismiss={onDismissHero}
          onRetry={onRetry}
        />
      )}

      {/* Celebration modal — portal-free; position:fixed handles layering */}
      {showCelebration && report && (
        <BrandReportCelebration report={report} onClose={onCloseCelebration} />
      )}
    </>
  );
}
