/**
 * Plain (non-"use server") home for the brand-report DTO/state types.
 * Types must NOT be exported from report-actions.ts ("use server"): in the
 * Turbopack build that makes the type get referenced at SSR module-eval time
 * and throws "ReferenceError: <Type> is not defined". Import report types from
 * HERE; import the server ACTIONS from report-actions.ts.
 */
import type { ReportEnvelope, ReportUiStateResponse } from "@/lib/cortex-api";

export type {
  ReportUiStateResponse,
  ReportVersionItem,
  ReportEnvelope,
} from "@/lib/cortex-api";

export interface ReportState {
  uiState: ReportUiStateResponse;
  /** The newest report version, or null if no reports have been generated. */
  latestReport: ReportEnvelope | null;
  brandId: string | null;
}
