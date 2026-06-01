import type { ReportVersionItem } from "@/lib/cortex-api";

/**
 * Single source of truth for "is this the live report version?".
 *
 * Only the `current` boolean decides this. `ReportVersionItem.status` is the
 * raw report-generation status (`generating` | `ready` | `failed`) — it is
 * never literally `"current"`, so do NOT branch on `status === "current"`.
 */
export function isCurrent(v: ReportVersionItem): boolean {
  return v.current;
}
