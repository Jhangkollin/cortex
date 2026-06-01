"use client";

/**
 * StepPreparingReport (zh-TW) — thin localized wrapper over the shared
 * <StepPreparingReport/> in `onboarding-v2/`.
 *
 * Every other zh step has a localized sibling in this folder; the post-
 * onboarding interstitial was the one place the zh wizard fell back to English
 * copy. Rather than fork the component, the shared one exposes a `labels` prop
 * (default `EN_PREPARING_LABELS`); this wrapper simply supplies the Traditional
 * Chinese copy and forwards every other prop unchanged.
 */

import { type ReactElement } from "react";

import {
  StepPreparingReport as StepPreparingReportBase,
  type PreparingReportLabels,
  type StepPreparingReportProps,
} from "@/components/onboarding-v2/step-preparing-report";

export const ZH_PREPARING_LABELS: PreparingReportLabels = {
  working: "Brand Agent · 工作中",
  title: "正在準備你的第一份報告…",
  subtitle:
    "Cortex 正在用你在 onboarding 設定的所有資料，組成你的 Brand IQ 報告。通常只需要一點時間 — 請稍候。",
  skip: "先進入儀表板",
};

/**
 * Forwards all <StepPreparingReport/> props (onDone, optional loadState,
 * pollMs, timeoutMs) and pins the Traditional Chinese labels. A caller may
 * still override `labels` if it ever needs to.
 */
export function StepPreparingReport({
  labels = ZH_PREPARING_LABELS,
  ...props
}: StepPreparingReportProps): ReactElement {
  return <StepPreparingReportBase labels={labels} {...props} />;
}
