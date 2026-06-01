"use client";

/**
 * Demo data banner — persistent reminder strip below the topbar when
 * `session.demo === true`.
 *
 * Per design handoff v1.1 §06b "Demo data mode":
 *   - Background: cortex-amber-50
 *   - Left rule: 3px cortex-amber-500
 *   - Copy: "Demo data" + "Replace with real sources" link → /connectors
 *   - Visible to everyone in the org (a session flag, not a per-user toggle)
 *   - On first real source connection, banner vanishes automatically
 *     (handled in mock-session-provider.tsx — connectFirstSource clears
 *     the demo flag)
 *
 * Renders nothing when demo mode is off, so the layout can mount it
 * unconditionally without leaking blank space into the document flow.
 */

import Link from "next/link";

import { useMockSession } from "@/components/auth/mock-session-provider";

export function DemoDataBanner() {
  const { session } = useMockSession();

  if (!session.demo) return null;

  return (
    <div
      role="status"
      className="flex items-center justify-between gap-4 bg-amber-50 px-7 py-2.5 text-sm text-ink-800"
      style={{ borderLeft: "3px solid var(--cortex-amber-500)" }}
    >
      <div className="flex items-center gap-2">
        <span
          className="material-icons-outlined text-amber-600"
          style={{ fontSize: 18 }}
          aria-hidden
        >
          dataset
        </span>
        <strong className="text-ink-900">Demo data</strong>
        <span className="text-ink-500">
          — Cortex is showing a fixed Acme Bank fixture, not your data.
        </span>
      </div>
      <Link
        href="/connectors"
        className="font-medium text-brand-700 hover:text-brand-600"
      >
        Replace with real sources →
      </Link>
    </div>
  );
}
