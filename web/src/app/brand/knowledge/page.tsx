/**
 * Knowledge Base — COR-83
 *
 * Server Component under the brand shell. `brand/layout.tsx` wraps every
 * brand route in `OnboardingGate` (no session → /signin, no brand ctx →
 * /persona, not onboarded → /onboarding) and `BrandShell` (sidebar). So by
 * the time this renders we are guaranteed an onboarded brand session — this
 * page only owns the KB-specific fetch / error / empty handling.
 *
 * Capability: the cortex-api enforces the capability on `listBrandReports`;
 * the report KB is a VIEW_BRAND_DASHBOARD feature, so there is no extra
 * page-level capability check here.
 *
 * States:
 *   - Empty list (no reports) → clean empty-state via KnowledgeBasePage
 *   - Reports present         → featured card + version history + pending stubs
 *   - Fetch error             → KB load-error panel
 */

import { auth } from "@/lib/auth";
import { listBrandReports } from "@/lib/cortex-api";
import { KnowledgeBasePage } from "@/components/knowledge-base/knowledge-base-page";

export default async function BrandKnowledgePage() {
  // OnboardingGate (brand/layout.tsx) guarantees an onboarded brand session
  // by the time this renders. We still read the session here to derive the
  // brand-scoped claims for the cortex-api call.
  const session = await auth();
  const activeContext = session?.user?.activeContext;
  if (!activeContext || activeContext.kind !== "brand") {
    // Unreachable in practice (the gate redirects first); a defensive
    // empty-state keeps the type narrowing honest without a non-null cast.
    return <KnowledgeBasePage versions={[]} />;
  }

  const brandId = activeContext.id;
  const claims = {
    cortexUserId: session?.user?.cortexUserId ?? "",
    email: session?.user?.email ?? "",
    displayName: session?.user?.name ?? null,
    activeContext,
  };

  let versions;
  try {
    versions = await listBrandReports(claims, brandId);
  } catch (err: unknown) {
    // Log server-side only — never leak internal details to the browser.
    console.error(`[knowledge] listBrandReports failed brandId=${brandId}:`, err);
    return <KnowledgeLoadError />;
  }

  return <KnowledgeBasePage versions={versions} />;
}

// ─── Error state ─────────────────────────────────────────────────────────────

function KnowledgeLoadError() {
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
          color: "var(--mly-danger)",
        }}
      >
        載入失敗
      </div>
      <div
        style={{
          fontSize: 13,
          color: "var(--fg-muted)",
          maxWidth: 480,
          textAlign: "center",
          fontFamily: "var(--font-sans)",
        }}
      >
        無法載入知識庫，請稍後再試。若問題持續，請聯絡支援團隊。
      </div>
      <a
        href="/brand/dashboard"
        style={{ color: "var(--mly-teal-600)", fontSize: 13 }}
      >
        返回 Dashboard
      </a>
    </div>
  );
}
