"use client";

import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useState } from "react";

import { createAnotherBrandAction } from "@/app/(auth)/onboarding/v2/add-brand-actions";

const ONBOARDING_STORAGE_KEY = "cortex.onboarding.v2";

export function OnboardingChooserAddAnother() {
  const { update } = useSession();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const { activeContext } = await createAnotherBrandAction();
      await update({ activeContext });
      // The wizard's local progress is single-keyed; clear so a brand-new
      // brand starts at step 0 instead of inheriting a stale "complete" flag.
      try {
        localStorage.removeItem(ONBOARDING_STORAGE_KEY);
      } catch {
        // ignore
      }
      router.push("/onboarding/v2");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not add a new brand.");
      setBusy(false);
    }
  }

  return (
    <div className="mb-4">
      <button
        type="button"
        onClick={onClick}
        disabled={busy}
        className="flex w-full items-center gap-3 rounded-md border border-brand-700 bg-brand-700 px-5 py-4 text-left text-white shadow-elev-2 transition-transform hover:translate-y-[-1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-700/40 focus-visible:ring-offset-2 disabled:opacity-60"
      >
        <span className="material-icons-outlined">library_add</span>
        <span>
          <div className="text-base font-bold">Add another brand</div>
          <div className="text-sm text-brand-100">
            {busy ? "Preparing a fresh workspace…" : "Start a new onboarding without touching your existing brand."}
          </div>
        </span>
      </button>
      {error ? <div className="mt-2 text-sm text-red-700">{error}</div> : null}
    </div>
  );
}
