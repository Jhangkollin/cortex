/**
 * Sign-in page — marketing-grade entry per design handoff §03.
 *
 * Layout: thin top header (logo · persona pivot · Pricing · Partnership · Sign in)
 *         → centered hero with LIVE pill, rotating headline, dot indicator,
 *           Continue-with-Google CTA, work-email pill input, SSO note.
 *
 * The persona dropdown / nav links are visual-only here. They route into
 * Persona-picker / Pricing / Partnership pages once those exist.
 */

import Image from "next/image";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { RotatingHeadline } from "@/components/auth/rotating-headline";
import { SignInButton } from "@/components/auth/sign-in-button";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      {/* Top header */}
      <header className="flex items-center justify-between border-b border-ink-150 px-8 py-[18px]">
        <div className="flex items-center">
          <Image
            src="/brand/mlytics-logo.png"
            alt="mlytics"
            width={140}
            height={25}
            priority
            data-mly-mark="signin-logo"
            style={{ height: "auto" }}
          />
        </div>
        <nav className="flex items-center gap-6 text-sm text-ink-500">
          <span className="flex cursor-pointer items-center gap-1 hover:text-ink-800">
            Who you are
            <span
              className="material-icons-outlined"
              style={{ fontSize: 16 }}
              aria-hidden
            >
              expand_more
            </span>
          </span>
          <Link href="/pricing" className="cursor-pointer hover:text-ink-800">
            Pricing
          </Link>
          <span className="cursor-pointer hover:text-ink-800">Partnership</span>
          <Button variant="dark" size="sm">
            Sign in
          </Button>
        </nav>
      </header>

      {/* Hero */}
      <main className="flex flex-1 flex-col items-center justify-center px-8 py-12 text-center">
        <Badge variant="live" className="text-[11px]">
          <span
            className="material-icons-outlined"
            style={{ fontSize: 11 }}
            aria-hidden
          >
            bolt
          </span>
          MLYTICS CORTEX · LIVE
        </Badge>

        <div className="mt-8">
          <RotatingHeadline />
        </div>

        <p className="mt-2 text-lg text-ink-500">
          Intelligent reach. Measurable outcomes.
        </p>

        <div className="mt-12 flex w-full max-w-[380px] flex-col gap-3">
          <SignInButton />
          <Input
            type="email"
            placeholder="Enter your work email"
            className="h-12 rounded-full text-center"
          />
          <p className="m-0 text-xs text-ink-500">
            Single sign-on (SSO) for enterprise customers
          </p>
        </div>
      </main>
    </div>
  );
}
