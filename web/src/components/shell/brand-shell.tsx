"use client";

/**
 * Brand customer shell layout (Aurora Mist v1.2 + GEO Monitor stage).
 *
 * The grid + seam treatment + sidebar-visibility transform are all owned
 * by the `.geo-app` class in globals.css. This layout sets the
 * `data-seam="bridge"` and `data-sidebar={open|closed}` attributes the
 * recipe uses, manages the open/closed state, and renders the reveal pill
 * when the sidebar is hidden.
 *
 * Session-aware: feeds the sidebar the live mock user/org.
 *
 * The TopBar + DemoDataBanner sat at the top of the content column in
 * the v1.1 layout. v1.2 moves the topbar into each page's stage so it
 * can pin sticky right above the section content (see
 * `app/brand/dashboard/page.tsx`'s StageTopBar). Layout-level chrome is
 * therefore minimal here — children own their own top row.
 */

import { useState } from "react";

import { useMockSession } from "@/components/auth/mock-session-provider";
import { AskCortexTrigger } from "@/components/brand-dashboard/discover/ask-cortex-trigger";
import { CortexDrawer } from "@/components/brand-dashboard/discover/cortex-drawer";
import {
  DrawerProvider,
  useCortexDrawer,
} from "@/components/brand-dashboard/discover/drawer-context";
import { Sidebar } from "@/components/shell/sidebar";

const FALLBACK_USER = {
  displayName: "Marketing Manager",
  orgName: "Brand Account",
  initial: "M",
};

/**
 * Inner shell that owns the `.geo-app` element. It must read
 * `useCortexDrawer()` so it lives *inside* `<DrawerProvider>`; the drawer's
 * open state is reflected onto `data-drawer-open` so the F1 `.geo-app`
 * recipe can switch to the 3-column grid when Cortex is open.
 */
function GeoApp({ children }: { children: React.ReactNode }) {
  const { session } = useMockSession();
  // Sidebar visibility lives at the layout level so children don't remount
  // when it toggles. `.geo-app[data-sidebar="closed"]` collapses the grid
  // template to 0 + minmax(0, 1fr) and translates the sidebar off-screen.
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { drawerOpen } = useCortexDrawer();

  const user = session.user
    ? {
        displayName: session.user.displayName,
        orgName: session.org?.name ?? FALLBACK_USER.orgName,
        initial: session.user.initial,
      }
    : FALLBACK_USER;

  const tier = session.org?.tier ?? "enterprise";

  return (
    <div
      className="geo-app"
      data-seam="bridge"
      data-sidebar={sidebarOpen ? "open" : "closed"}
      data-drawer-open={drawerOpen ? "true" : undefined}
    >
      <Sidebar
        activeContextKind="brand"
        role="admin"
        tier={tier}
        user={user}
        onCollapse={() => setSidebarOpen(false)}
      />
      {!sidebarOpen ? (
        <button
          type="button"
          className="sb-reveal"
          aria-label="Show sidebar"
          onClick={() => setSidebarOpen(true)}
        >
          <span className="material-icons-outlined" aria-hidden>
            chevron_right
          </span>
        </button>
      ) : null}
      {children}
      <AskCortexTrigger />
      <CortexDrawer />
    </div>
  );
}

export function BrandShell({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DrawerProvider>
      <GeoApp>{children}</GeoApp>
    </DrawerProvider>
  );
}
