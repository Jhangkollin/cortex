import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Mlytics input.
 *
 * 1px ink-200 border at rest. On focus, the border thickens to 2px teal-800
 * AND a 3px focus ring is drawn — to compensate for the +1px border the
 * horizontal padding drops to 13px so the inner content doesn't shift.
 */
const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, type = "text", ...props }, ref) => {
  return (
    <input
      ref={ref}
      type={type}
      className={cn(
        "h-10 w-full rounded-sm border border-ink-200 bg-white px-[14px]",
        "text-sm text-ink-800 placeholder:text-ink-400",
        "transition-[border-color,box-shadow] duration-state ease-std",
        "focus:outline-none focus:border-2 focus:border-brand-800 focus:px-[13px]",
        "focus:shadow-[var(--focus-ring)]",
        "disabled:cursor-not-allowed disabled:opacity-60",
        className,
      )}
      {...props}
    />
  );
});
Input.displayName = "Input";

export { Input };
