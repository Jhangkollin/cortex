/**
 * Step rail — vertical list of all 5 onboarding steps with status pips.
 *
 * Per design handoff §04:
 *   - done     · brand-600 filled circle with check
 *   - current  · ink-900 filled circle with the step number
 *   - future   · ink-150 muted circle with the step number
 *
 * The rail is sticky-ish (lives in a 280px column inside a 2-col grid)
 * but doesn't actually use position:sticky — the page is short enough
 * that scrolling never makes the rail leave the viewport.
 */

import { STEP_INDICES, STEPS, type StepIndex } from "@/lib/onboarding";
import { cn } from "@/lib/utils";

export interface StepRailProps {
  current: StepIndex;
}

export function StepRail({ current }: StepRailProps) {
  return (
    <nav aria-label="Onboarding progress" className="flex flex-col gap-1.5">
      <div className="mb-3.5 text-[11px] font-bold uppercase tracking-[0.08em] text-brand-700">
        BRAND ONBOARDING
      </div>
      {STEP_INDICES.map((idx) => {
        const meta = STEPS[idx];
        const status =
          idx < current ? "done" : idx === current ? "current" : "future";
        return (
          <div
            key={idx}
            className={cn(
              "flex items-start gap-3.5 py-2.5",
              status === "future" && "text-ink-500",
            )}
          >
            <span
              aria-hidden
              className={cn(
                "grid h-6 w-6 place-items-center rounded-full text-xs font-bold",
                status === "done" && "bg-brand-600 text-white",
                status === "current" && "bg-ink-900 text-white",
                status === "future" && "bg-ink-150 text-ink-500",
              )}
            >
              {status === "done" ? "✓" : idx}
            </span>
            <span
              className={cn(
                "pt-[3px]",
                status !== "future"
                  ? "font-medium text-ink-900"
                  : "text-ink-500",
              )}
            >
              {meta.title}
            </span>
          </div>
        );
      })}
    </nav>
  );
}
