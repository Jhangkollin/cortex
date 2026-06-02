"use client";

import { type ReactElement } from "react";

import { BASE_DATA } from "@/lib/discover/mock";

import { GeoFunnel } from "./geo-funnel";
import { GeoOpportunity } from "./geo-opportunity";
import { KpiRow } from "./kpi-row";
import { MediaCompetitorGrid } from "./media-competitor-grid";
import { PriorityAlerts } from "./priority-alerts";
import { QuestionTop10 } from "./question-top10";
import { Topbar } from "./topbar";

export function DiscoverDashboard(): ReactElement {
  const data = BASE_DATA;

  return (
    <>
      <Topbar />
      <PriorityAlerts alerts={data.alerts} />
      <KpiRow kpis={data.kpis} />
      <GeoFunnel funnel={data.funnel} />
      <MediaCompetitorGrid media={data.media} intent={data.intent} />
      <QuestionTop10 questions={data.questions} />
      <GeoOpportunity geo={data.geo} />
    </>
  );
}
