import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Mlytics primary button.
 *
 * Variants — primary | ghost | soft | dark, exactly per design handoff.
 * Sizes   — default (40h) | sm (32h) | xs (28h).
 *
 * Press animation is a 1px translate-y, no bounce, 120ms standard ease —
 * matching the design system's "no bouncy interactions" rule.
 */
const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2",
    "rounded-sm font-medium whitespace-nowrap",
    "border border-transparent",
    "transition-[background-color,color,border-color,transform] duration-state ease-std",
    "active:translate-y-px",
    "disabled:pointer-events-none disabled:opacity-50",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-700/40",
  ].join(" "),
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--primary)] text-[var(--on-primary)] border-[var(--primary)] hover:bg-[var(--primary-hover)] hover:border-[var(--primary-hover)]",
        ghost:
          "bg-transparent text-brand-700 hover:bg-[rgba(20,73,72,0.06)]",
        soft:
          "bg-white text-ink-800 border-ink-200 hover:bg-ink-50 hover:border-ink-300",
        dark: "bg-ink-900 text-white border-ink-900 hover:bg-ink-800",
      },
      size: {
        default: "h-10 px-[18px] text-sm",
        sm: "h-8 px-[14px] text-[13px]",
        xs: "h-7 px-[10px] text-xs",
        icon: "h-10 w-10 px-0",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        ref={ref}
        className={cn(buttonVariants({ variant, size }), className)}
        {...props}
      />
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
