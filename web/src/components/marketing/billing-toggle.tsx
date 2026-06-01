"use client";

import { cn } from "@/lib/utils";

export type BillingPeriod = "monthly" | "annual";

export interface BillingToggleProps {
  value: BillingPeriod;
  onChange: (next: BillingPeriod) => void;
  className?: string;
}

/**
 * Pill-shaped Monthly / Annual toggle for the pricing hero.
 *
 * Visual spec — handoff §V1: ink-100 pill bg, 3px inner padding, active option
 * lifts to white + elev-1; SAVE 20% chip inline with Annual label, teal-700
 * on teal-050 at 10/700/.06em tracking.
 *
 * Accessibility: pair of toggle buttons in a group with aria-pressed for
 * selected state.
 */
export function BillingToggle({
  value,
  onChange,
  className,
}: BillingToggleProps) {
  const select = (next: BillingPeriod) => {
    if (next !== value) onChange(next);
  };

  return (
    <div
      role="group"
      aria-label="Billing period"
      className={cn(
        "inline-flex items-center gap-0.5 rounded-full bg-ink-100 p-[3px]",
        className,
      )}
    >
      <ToggleButton
        active={value === "monthly"}
        onClick={() => select("monthly")}
      >
        Monthly
      </ToggleButton>
      <ToggleButton
        active={value === "annual"}
        onClick={() => select("annual")}
      >
        Annual
        <span
          className={cn(
            "ml-1.5 inline-flex items-center rounded-full bg-brand-50 px-1.5 py-[2px]",
            "text-[10px] font-bold tracking-[0.06em] text-brand-700",
          )}
        >
          SAVE 20%
        </span>
      </ToggleButton>
    </div>
  );
}

function ToggleButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "inline-flex items-center rounded-full px-[18px] py-2",
        "text-sm font-medium",
        "transition-[background-color,color,box-shadow] duration-state ease-std",
        active
          ? "bg-white text-ink-900 shadow-elev-1"
          : "bg-transparent text-ink-500 hover:text-ink-800",
      )}
    >
      {children}
    </button>
  );
}
