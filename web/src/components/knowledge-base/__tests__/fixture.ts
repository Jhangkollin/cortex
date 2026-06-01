/**
 * Fixtures for knowledge-base component tests.
 */
import type { ReportVersionItem } from "@/lib/cortex-api";

// NOTE: `status` is the raw report-generation status (generating|ready|failed)
// — it is NEVER literally "current". The `current` boolean alone decides which
// version is live. Fixtures use realistic `status` values so the test would
// catch any regression that branched on `status === "current"`.
export const CURRENT_VERSION: ReportVersionItem = {
  reportId: "BIQ-2026-05-22-TESTBRAND",
  version: "v1.0",
  createdAt: "2026-05-22T08:00:00Z",
  status: "ready",
  current: true,
  costUsd: 1.23,
};

export const ARCHIVED_VERSION: ReportVersionItem = {
  reportId: "BIQ-2026-05-19-TESTBRAND",
  version: "v0.9",
  createdAt: "2026-05-19T10:30:00Z",
  status: "ready",
  current: false,
  costUsd: 0.98,
};

export const VERSIONS_FIXTURE: ReportVersionItem[] = [CURRENT_VERSION, ARCHIVED_VERSION];
