"use client";

/**
 * App sidebar — Aurora Mist v1.2 light surface, Discover v2 §04 IA,
 * collapsible.
 *
 * §04 section structure (per Discover v2 design bundle / spec §9 —
 * cortex/dashboard.jsx `MistSidebar`):
 *   - Logo block
 *   - Discover (top-level, default/active on /brand/dashboard)
 *   - History  (top-level)
 *   - Media Network  · under "Network" overline
 *   - Knowledge Base · Brand Voice · Connectors · under "Agent" overline
 *   - User footer = popover menu trigger (avatar + name/org + chevron),
 *     opens a menu with [Account settings · Reset demo · Sign out (danger)]
 *
 * v2.1 footer redesign: the previous v1.2 footer (avatar + name + bare gear
 * button + sibling sign-out row) was replaced with a single trigger button
 * + popover, matching the latest designer output (handoff-v2 dashboard.jsx
 * MistSidebar). Click-outside and Escape close the menu.
 *
 * Aurora Mist composition (mist base + 3 blurred radials + 14% SVG grain)
 * lives in globals.css `.sb`; per-element tokens live in tokens.css
 * `--sidebar-*`. Stacking is sensitive — every real child sets `relative
 * z-[2]` so it sits above the `.sb::before/::after` layers.
 */

import type { Route } from "next";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { signOut as nextAuthSignOut } from "next-auth/react";
import { useEffect, useRef, useState } from "react";

import { useMockSession } from "@/components/auth/mock-session-provider";
import {
  type ActiveContextKind,
  hasCapability,
  type OrgTier,
  type UserRole,
} from "@/lib/permissions";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: Route;
  icon: string;
  requires?: Parameters<typeof hasCapability>[2];
  isDefault?: boolean;
  soon?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Discover",
    href: "/brand/dashboard",
    icon: "explore",
    requires: "view_brand_dashboard",
    isDefault: true,
  },
  {
    label: "Ask Cortex",
    href: "/brand/ask-cortex",
    icon: "auto_awesome",
    requires: "view_brand_dashboard",
  },
  {
    label: "Knowledge Base",
    href: "/brand/knowledge",
    icon: "menu_book",
    soon: true,
  },
];

interface UserShell {
  displayName: string;
  orgName: string;
  initial: string;
}

export interface SidebarProps {
  activeContextKind: ActiveContextKind;
  role: UserRole;
  tier?: OrgTier;
  user: UserShell;
  /**
   * Retained for consumer stability (v2 §04 removed the status pod that
   * consumed it). Kept optional so the prop surface stays compatible.
   */
  health?: {
    label: string;
    metrics: string;
  };
  /** When provided, renders a collapse chevron at the top-right. */
  onCollapse?: () => void;
}

function NavRow({
  item,
  active,
}: {
  item: NavItem;
  active: boolean;
}) {
  if (item.soon) {
    return (
      <div
        className="relative z-[2] flex cursor-default items-center gap-2.5 rounded-md px-3 py-[9px] text-[13.5px] font-medium"
        aria-disabled="true"
      >
        <span
          className="material-icons-outlined"
          style={{ fontSize: 18, color: "var(--mly-ink-300)" }}
          aria-hidden
        >
          {item.icon}
        </span>
        <span className="flex-1 text-[var(--mly-ink-300)]">{item.label}</span>
        <span className="sb-soon">soon</span>
      </div>
    );
  }

  return (
    <Link
      href={item.href}
      className={cn(
        "group relative z-[2] flex items-center gap-2.5 rounded-md px-3 py-[9px]",
        "text-[13.5px] font-medium",
        "transition-[background-color,color,box-shadow] duration-state ease-std",
        active
          ? "font-semibold text-[var(--sidebar-fg-on-active)] bg-[#ebebea]"
          : "text-ink-700 hover:bg-[rgba(20,73,72,0.05)] hover:text-ink-900",
      )}
      aria-current={active ? "page" : undefined}
    >
      <span
        className="material-icons-outlined"
        style={{
          fontSize: 18,
          color: active ? "var(--mly-teal-700)" : "var(--mly-ink-500)",
        }}
        aria-hidden
      >
        {item.icon}
      </span>
      <span className="flex-1">{item.label}</span>
    </Link>
  );
}

interface UserMenuProps {
  user: UserShell;
}

/**
 * Sidebar footer = user-menu popover trigger.
 *
 * The trigger button shows avatar (`user.initial`) + display name + org +
 * a chevron. Clicking it toggles a menu rendered ABOVE the trigger via
 * `position:absolute; bottom: calc(100% + 6px)` (the `.sb .user-menu`
 * recipe in globals.css). Click-outside and Escape close the menu.
 *
 * Menu actions:
 *   - Account settings — placeholder (no onClick, matching the designer's
 *     literal prototype; will be wired to a real route in a follow-up).
 *   - Reset demo       — `router.push("/demo/onboarding")` (demo-mode
 *     entry point being built separately).
 *   - Sign out (danger) — clears the mock session via `useMockSession`
 *     then calls NextAuth signOut with `callbackUrl: "/signin"`.
 */
function UserMenu({ user }: UserMenuProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { signOut: clearMockSession } = useMockSession();

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    const onEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  const handleResetDemo = () => {
    setOpen(false);
    // The /demo/onboarding route is being built separately (no page.tsx yet),
    // so Next.js typedRoutes won't have it in `RouteImpl`. The `as Route` cast
    // is the documented typedRoutes escape hatch for routes that exist
    // (or will exist) but aren't statically discoverable yet.
    router.push("/demo/onboarding" as Route);
  };

  const handleSignOut = () => {
    setOpen(false);
    clearMockSession();
    void nextAuthSignOut({ callbackUrl: "/signin" });
  };

  return (
    <div className="user" ref={ref}>
      <button
        type="button"
        className="user-trigger"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Account menu"
      >
        <div className="av" aria-hidden>
          {user.initial}
        </div>
        <div className="who min-w-0">
          <div className="truncate">{user.displayName}</div>
          <small className="truncate">{user.orgName}</small>
        </div>
        <span className="material-icons-outlined chev" aria-hidden>
          {open ? "expand_less" : "expand_more"}
        </span>
      </button>

      {open ? (
        <div className="user-menu" role="menu">
          {/* Account settings — placeholder (design has no onClick yet) */}
          <button
            type="button"
            className="user-menu-item"
            role="menuitem"
          >
            <span className="material-icons-outlined" aria-hidden>
              person
            </span>
            <span>Account settings</span>
          </button>
          <button
            type="button"
            className="user-menu-item"
            role="menuitem"
            onClick={handleResetDemo}
          >
            <span className="material-icons-outlined" aria-hidden>
              restart_alt
            </span>
            <span>Reset demo</span>
          </button>
          <div className="user-menu-sep" />
          <button
            type="button"
            className="user-menu-item is-danger"
            role="menuitem"
            onClick={handleSignOut}
          >
            <span className="material-icons-outlined" aria-hidden>
              logout
            </span>
            <span>Sign out</span>
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function Sidebar({
  activeContextKind,
  role,
  tier = "free",
  user,
  onCollapse,
}: SidebarProps) {
  const pathname = usePathname();

  // Only one nav row at a time should highlight. Stub items that point at
  // /brand/dashboard (placeholder routes until their real pages ship) must
  // not claim active state when the isDefault row already owns that pathname.
  const isItemActive = (item: NavItem) => {
    if (item.isDefault) return pathname === "/brand/dashboard";
    if (item.href === "/brand/dashboard") return false;
    return pathname?.startsWith(item.href) ?? false;
  };

  return (
    <aside
      className="sb flex h-screen flex-col gap-1.5 px-3.5 py-4 text-ink-700"
      aria-label="Primary navigation"
    >
      {/* Collapse chevron — only renders when the parent layout owns
          the collapse state and wants to expose the handle. */}
      {onCollapse ? (
        <button
          type="button"
          className="sb-collapse"
          aria-label="Hide sidebar"
          onClick={onCollapse}
        >
          <span className="material-icons-outlined" aria-hidden>
            chevron_left
          </span>
        </button>
      ) : null}

      {/* Logo — real mlytics brand PNG shipped from design handoff
          (web/public/brand/mlytics-logo.png, 500×90, ≈5.56:1 aspect). The
          PNG already contains the mark + wordmark, so the previous gradient
          "M" glyph span and trailing "mlytics" text are gone. */}
      <Link
        href="/brand/dashboard"
        className="relative z-[2] mb-3 flex items-center px-2 py-2"
      >
        <Image
          src="/brand/mlytics-logo.png"
          alt="mlytics"
          width={108}
          height={20}
          priority
          data-mly-mark="sidebar-logo"
          style={{ height: "auto" }}
        />
      </Link>

      {/* Scrollable nav region. `.sb` is pinned at height:100vh with
          overflow:hidden (the aurora ::before/::after recipe needs the clip),
          so the nav owns its own scroll — otherwise items would silently clip
          on short viewports. `min-h-0` lets this flex child shrink below its
          content size so overflow-y actually engages. */}
      <div className="relative z-[2] flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto">
        {NAV_ITEMS.filter((item) =>
          item.requires
            ? hasCapability(activeContextKind, role, item.requires, tier)
            : true,
        ).map((item) => (
          <NavRow key={item.label} item={item} active={isItemActive(item)} />
        ))}
      </div>

      {/* User footer popover */}
      <UserMenu user={user} />
    </aside>
  );
}
