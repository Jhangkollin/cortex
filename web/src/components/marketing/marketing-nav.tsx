"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

export interface MarketingNavProps {
  /** Optional explicit active key — overrides pathname-based detection. */
  active?: "pricing" | "partnership" | null;
  className?: string;
}

// Only Pricing is a live route in this slice. Partnership is a stub that
// renders as a non-routed anchor so Next.js typed-routes doesn't fail the
// build. Add it to LIVE_LINKS once /partnership/page.tsx exists.
const LIVE_LINKS = [
  { key: "pricing" as const, label: "Pricing", href: "/pricing" as const },
];

const STUB_LINKS = [{ key: "partnership" as const, label: "Partnership" }];

/**
 * Public marketing chrome — used by routes inside the (marketing) route group.
 *
 * Minimal first cut: brand mark + persona dropdown stub + the live page links
 * + a Sign in button. The "Who you are" persona switcher is non-interactive
 * for v1 (the persona-led marketing surface lands with V2 Pricing).
 */
export function MarketingNav({ active, className }: MarketingNavProps) {
  const pathname = usePathname();
  const resolvedActive =
    active ??
    (LIVE_LINKS.find(
      (l) => pathname === l.href || pathname?.startsWith(`${l.href}/`),
    )?.key ?? null);

  return (
    <header
      className={cn(
        "flex items-center justify-between border-b border-ink-150 bg-white px-8 py-4",
        className,
      )}
    >
      <Link href="/" className="flex items-center">
        <Image
          src="/brand/mlytics-logo.png"
          alt="mlytics"
          width={140}
          height={25}
          priority
          data-mly-mark="marketing-nav-logo"
          style={{ height: "auto" }}
        />
      </Link>
      <nav className="flex items-center gap-6 text-sm text-ink-500">
        <button
          type="button"
          className="inline-flex items-center gap-1 text-ink-500 hover:text-ink-800"
          aria-haspopup="menu"
          aria-expanded="false"
        >
          Who you are
          <span aria-hidden className="material-icons-outlined text-sm">
            expand_more
          </span>
        </button>
        {LIVE_LINKS.map((link) => (
          <Link
            key={link.key}
            href={link.href}
            className={cn(
              "transition-colors duration-state ease-std",
              resolvedActive === link.key
                ? "font-semibold text-ink-900"
                : "text-ink-500 hover:text-ink-800",
            )}
            aria-current={resolvedActive === link.key ? "page" : undefined}
          >
            {link.label}
          </Link>
        ))}
        {STUB_LINKS.map((link) => (
          <span
            key={link.key}
            className="text-ink-500 cursor-default"
            aria-disabled="true"
          >
            {link.label}
          </span>
        ))}
        <Button asChild variant="dark" size="sm">
          <Link href="/signin">Sign in</Link>
        </Button>
      </nav>
    </header>
  );
}
