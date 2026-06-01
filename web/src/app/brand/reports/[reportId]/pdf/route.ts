/**
 * Brand IQ Report PDF proxy — COR-81.
 *
 * The Download-PDF button can't hit cortex-api directly: the api `/pdf`
 * endpoint requires a Bearer token a browser <a href> can't carry, and the
 * api base URL is an in-cluster address not reachable from the browser. This
 * route handler runs server-side, authenticates the session, signs a cortex
 * token, fetches the upstream PDF and streams the binary body back with the
 * upstream Content-Type / Content-Disposition.
 *
 * The Bearer token never reaches the browser. Until COR-80 ships the api
 * `/pdf` endpoint, this relays the upstream 404/501 verbatim — acceptable.
 */

import { auth } from "@/lib/auth";
import { fetchBrandReportPdf } from "@/lib/cortex-api";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ reportId: string }> },
): Promise<Response> {
  const { reportId } = await params;
  const session = await auth();

  const activeContext = session?.user?.activeContext;
  if (!activeContext || activeContext.kind !== "brand") {
    return new Response("Unauthorized", { status: 401 });
  }

  const brandId = activeContext.id;
  const claims = {
    cortexUserId: session.user.cortexUserId ?? "",
    email: session.user.email ?? "",
    displayName: session.user.name ?? null,
    activeContext,
  };

  let upstream: Response;
  try {
    upstream = await fetchBrandReportPdf(claims, brandId, reportId);
  } catch (err) {
    // Network/signing failure — log detail server-side, return generic error.
    console.error(
      `[brand-report-pdf] fetch failed brandId=${brandId} reportId=${reportId}:`,
      err,
    );
    return new Response("Failed to fetch report PDF", { status: 502 });
  }

  // Relay the upstream body + relevant headers (incl. non-2xx like 404/501).
  const headers = new Headers();
  const contentType = upstream.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const disposition = upstream.headers.get("content-disposition");
  if (disposition) {
    headers.set("content-disposition", disposition);
  } else if (upstream.ok) {
    headers.set(
      "content-disposition",
      `inline; filename="brand-iq-${reportId}.pdf"`,
    );
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers,
  });
}
