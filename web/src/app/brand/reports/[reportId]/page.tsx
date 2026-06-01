/**
 * Brand IQ Report Viewer — COR-81
 *
 * Server Component: fetches the report from cortex-api using the current
 * session's activeContext.id as the brand_id. Delegates rendering to the
 * client-side <ReportViewer />.
 *
 * States:
 *   - No session / wrong context → redirect to /signin (handled by OnboardingGate)
 *   - Report pending/running    → shows a polling-intent status page
 *   - Report not found (404)    → shows a not-found state
 *   - Report ready              → full viewer
 */

import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { CortexApiError, fetchBrandReport } from "@/lib/cortex-api";
import { ReportViewer } from "@/components/report-viewer/report-viewer";

const DEV_BYPASS_AUTH = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true";

interface PageProps {
  params: Promise<{ reportId: string }>;
}

export default async function BrandReportPage({ params }: PageProps) {
  const { reportId } = await params;

  if (DEV_BYPASS_AUTH) {
    const { READY_FIXTURE } = await import(
      "@/components/brand-dashboard/report-surface-fixture"
    );
    if (READY_FIXTURE.report) {
      return <ReportViewer report={READY_FIXTURE.report} reportId={reportId} />;
    }
  }

  const session = await auth();

  // Not authenticated
  if (!session?.user?.activeContext) {
    redirect("/signin");
  }

  const { activeContext } = session.user;
  if (activeContext.kind !== "brand") {
    redirect("/signin");
  }

  const brandId = activeContext.id;
  const claims = {
    cortexUserId: session.user.cortexUserId ?? "",
    email: session.user.email ?? "",
    displayName: session.user.name ?? null,
    activeContext,
  };

  let envelope;
  try {
    envelope = await fetchBrandReport(claims, brandId, reportId);
  } catch (err: unknown) {
    if (err instanceof CortexApiError && err.status === 404) {
      return <ReportNotFound reportId={reportId} />;
    }
    // Log the real error (incl. cortex-api URL + body) server-side only —
    // never leak internal infrastructure detail to the browser.
    console.error(
      `[brand-report] fetch failed brandId=${brandId} reportId=${reportId}:`,
      err,
    );
    return <ReportError />;
  }

  if (envelope.status === "ready" && envelope.report) {
    return <ReportViewer report={envelope.report} reportId={reportId} />;
  }

  // Pending or running
  return <ReportPending status={envelope.status} reportId={reportId} />;
}

// ─── Sub-states ──────────────────────────────────────────────────────────────

function ReportPending({ status, reportId }: { status: string; reportId: string }) {
  return (
    <div
      style={{
        minHeight: "60vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        padding: "48px 24px",
        color: "var(--fg-muted)",
        fontFamily: "var(--font-mono)",
      }}
    >
      <div
        style={{
          fontSize: 13,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          color: "var(--mly-lime-500)",
          fontWeight: 700,
        }}
      >
        {status === "running" ? "◈ 報告生成中" : "◇ 等待中"}
      </div>
      <div style={{ fontSize: 14, color: "var(--fg)", fontFamily: "var(--font-sans)" }}>
        Brand IQ 報告 ({reportId}) 尚未就緒，請稍後重整頁面。
      </div>
      <div style={{ fontSize: 11, color: "var(--fg-muted)" }}>
        狀態 · {status}
      </div>
    </div>
  );
}

function ReportNotFound({ reportId }: { reportId: string }) {
  return (
    <div
      style={{
        minHeight: "60vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        padding: "48px 24px",
        color: "var(--fg-muted)",
        fontFamily: "var(--font-mono)",
      }}
    >
      <div style={{ fontSize: 13, letterSpacing: "0.2em", textTransform: "uppercase" }}>
        404
      </div>
      <div style={{ fontSize: 14, color: "var(--fg)", fontFamily: "var(--font-sans)" }}>
        找不到報告 {reportId}
      </div>
      <a href="/brand/dashboard" style={{ color: "var(--mly-teal-600)", fontSize: 13 }}>
        返回 Dashboard
      </a>
    </div>
  );
}

function ReportError() {
  return (
    <div
      style={{
        minHeight: "60vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 16,
        padding: "48px 24px",
        color: "var(--fg-muted)",
        fontFamily: "var(--font-mono)",
      }}
    >
      <div style={{ fontSize: 13, letterSpacing: "0.2em", textTransform: "uppercase", color: "var(--mly-danger)" }}>
        載入失敗
      </div>
      <div style={{ fontSize: 13, color: "var(--fg-muted)", maxWidth: 480, textAlign: "center", fontFamily: "var(--font-sans)" }}>
        無法載入報告，請稍後再試。若問題持續，請聯絡支援團隊。
      </div>
      <a href="/brand/dashboard" style={{ color: "var(--mly-teal-600)", fontSize: 13 }}>
        返回 Dashboard
      </a>
    </div>
  );
}
