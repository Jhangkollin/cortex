"use client";

/**
 * Persona picker — design handoff §03.
 *
 * Three persona cards. Only Brand Customer is live in v1 — the other two
 * are visually present (so the demo conveys product breadth) but disabled
 * with a "Coming soon" pill.
 *
 * Selecting "Brand Customer" calls the `createMyBrand` Server Action, which
 * hits cortex-api `POST /v1/brand` (atomically creates brand + ADMIN
 * membership). On success, triggers `session.update()` so NextAuth's jwt
 * callback re-resolves and bakes `activeContext` into the next session
 * token. Then routes to the `/onboarding` chooser where the user picks
 * Quick AI setup or Manual form entry to complete brand onboarding.
 */

import Image from "next/image";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { createMyBrand } from "@/app/(auth)/persona/actions";
import { Badge } from "@/components/ui/badge";

interface PersonaCardSpec {
  title: string;
  pitch: string;
  bullets: readonly string[];
  footer: string;
  icon: string;
  status: "live" | "soon";
}

const CARDS: readonly PersonaCardSpec[] = [
  {
    title: "Content Business Owner",
    pitch: "I run a publication, media site, or content business.",
    bullets: [
      "Deploy AI Q&A widgets",
      "Monetize your content",
      "AI agents to engage your audience",
    ],
    footer: "PUBLISHERS · MEDIA",
    icon: "article",
    status: "soon",
  },
  {
    title: "Brand Customer",
    pitch: "I want to be the chosen answer when my buyers are deciding.",
    bullets: [
      "Find your target customers",
      "Track confirmed conversions",
      "AI agents to promote and convert",
    ],
    footer: "FINANCE · INSURANCE · WEALTH · DTC",
    icon: "storefront",
    status: "live",
  },
  {
    title: "Developer",
    pitch: "I'm integrating Mlytics Cortex into a product or platform.",
    bullets: [
      "Unified API for top models",
      "Global delivery",
      "Agent integrations",
    ],
    footer: "API · SDK",
    icon: "code",
    status: "soon",
  },
] as const;

export default function PersonaPickerPage() {
  const router = useRouter();
  const { update } = useSession();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSelectBrand() {
    setBusy(true);
    setError(null);
    try {
      const { brandId } = await createMyBrand();
      // Trigger NextAuth jwt callback (trigger: "update") so it re-resolves
      // active_context via cortex-api and bakes it into the next session token.
      await update({ activeContext: { kind: "brand", id: brandId } });
      router.push("/onboarding");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create brand workspace.",
      );
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-ink-25 p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center">
          <Image
            src="/brand/mlytics-logo.png"
            alt="mlytics"
            width={132}
            height={24}
            priority
            data-mly-mark="persona-logo"
            style={{ height: "auto" }}
          />
        </div>
        <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-brand-700">
          PICK YOUR VIEW
        </div>
      </div>

      <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-brand-700">
        WELCOME TO MLYTICS CORTEX
      </div>
      <h1
        className="mt-3.5 mb-2.5"
        style={{
          font: "700 48px/1.1 var(--font-sans)",
          letterSpacing: "-0.02em",
        }}
      >
        Where do you sit in the
        <br />
        Agent Economy?
      </h1>
      <p className="mb-9 max-w-[560px] text-base text-ink-500">
        We&apos;ll tune Cortex to your view — the metrics, surfaces, and actions
        you care about most.
      </p>

      {error ? (
        <div className="mb-4 rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {CARDS.map((card) => (
          <PersonaCard
            key={card.title}
            card={card}
            disabled={busy}
            onSelect={() => {
              if (card.status !== "live" || busy) return;
              void handleSelectBrand();
            }}
          />
        ))}
      </div>
    </div>
  );
}

function PersonaCard({
  card,
  onSelect,
  disabled,
}: {
  card: PersonaCardSpec;
  onSelect: () => void;
  disabled?: boolean;
}) {
  const isLive = card.status === "live";

  if (isLive) {
    return (
      <button
        type="button"
        onClick={onSelect}
        disabled={disabled}
        className="relative flex min-h-[340px] flex-col gap-3 rounded-md border border-brand-700 bg-brand-700 p-6 text-left text-white shadow-elev-2 transition-transform duration-state ease-std hover:translate-y-[-1px] disabled:cursor-wait disabled:opacity-70"
      >
        <Badge
          variant="live"
          className="absolute right-[18px] top-[18px] bg-white"
        >
          Live
        </Badge>
        <div
          aria-hidden
          className="grid h-11 w-11 place-items-center rounded-md bg-white/10"
        >
          <span className="material-icons-outlined">{card.icon}</span>
        </div>
        <h3 className="m-0 text-xl font-bold leading-snug">{card.title}</h3>
        <p className="m-0 text-sm text-brand-100">{card.pitch}</p>
        <ul className="m-0 flex list-none flex-col gap-1 p-0 text-[13px] text-brand-100">
          {card.bullets.map((b) => (
            <li key={b}>· {b}</li>
          ))}
        </ul>
        <div className="mt-auto border-t border-white/10 pt-3.5 text-[11px] font-bold uppercase tracking-[0.05em] text-brand-200">
          <span className="font-mono">{card.footer}</span>
        </div>
      </button>
    );
  }

  return (
    <div
      aria-disabled
      className="relative flex min-h-[340px] cursor-not-allowed flex-col gap-3 rounded-md border border-ink-200 bg-white p-6 opacity-70"
    >
      <Badge
        variant="soon"
        className="absolute right-[18px] top-[18px]"
      >
        Coming soon
      </Badge>
      <div
        aria-hidden
        className="grid h-11 w-11 place-items-center rounded-md bg-ink-100"
      >
        <span className="material-icons-outlined text-ink-700">
          {card.icon}
        </span>
      </div>
      <h3 className="m-0 text-xl font-bold leading-snug text-ink-900">
        {card.title}
      </h3>
      <p className="m-0 text-sm text-ink-500">{card.pitch}</p>
      <ul className="m-0 flex list-none flex-col gap-1 p-0 text-[13px] text-ink-500">
        {card.bullets.map((b) => (
          <li key={b}>· {b}</li>
        ))}
      </ul>
      <div className="mt-auto border-t border-ink-100 pt-3.5 text-[11px] font-bold uppercase tracking-[0.05em] text-ink-400">
        <span className="font-mono">{card.footer}</span>
      </div>
    </div>
  );
}
