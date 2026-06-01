"use client";

/**
 * Cortex Discover v2.1 — populated stage.
 *
 * Renders the canonical `BASE_DATA` view. The Cortex query strip (and its
 * per-preset re-shape behavior) was retired in v2.1; reach Cortex through the
 * shell-level ⌘K trigger + docked drawer (`BrandShell`, plan F3/R6).
 *
 * The Brand IQ report hero + one-time celebration were hoisted to the dashboard
 * page (`<BrandReportSurface/>`) so they also render for freshly-onboarded
 * brands (which show <EmptyDiscover/> instead of this stage). This component is
 * now purely the populated discover stage and is rendered inside the page's
 * `.pg sp` wrapper.
 *
 * Region order mirrors the reference `GeoMonitorStage`
 * (Topbar → PriorityAlerts → KpiRow → GeoFunnel → MediaCompetitorGrid).
 */

import { type ReactElement } from "react";

import { BASE_DATA } from "@/lib/discover/mock";

import { GeoFunnel } from "./geo-funnel";
import { KpiRow } from "./kpi-row";
import { MediaCompetitorGrid } from "./media-competitor-grid";
import { PriorityAlerts } from "./priority-alerts";
import { Topbar } from "./topbar";

export function DiscoverDashboard(): ReactElement {
  const data = BASE_DATA;

  return (
    <>
      <Topbar />
      <PriorityAlerts alerts={data.alerts} />
      <KpiRow hero={data.hero} minis={data.minis} />
      <GeoFunnel funnel={data.funnel} />
      <MediaCompetitorGrid media={data.media} comp={data.comp} />
    </>
  );
}
