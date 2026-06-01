import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Mlytics card primitive.
 *
 * 1px ink-150 border + elev-1 shadow + 8px radius. No colored left-border
 * accents (handoff note: that's a banned pattern). Default padding 24,
 * dense variant 16 — pass `data-density="dense"` if you want the tighter pad.
 */
function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-md border border-ink-150 bg-white shadow-elev-1",
        className,
      )}
      {...props}
    />
  );
}

function CardPad({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6", className)} {...props} />;
}

function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("mb-3.5 flex items-baseline justify-between", className)}
      {...props}
    />
  );
}

function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-base font-bold text-ink-900 leading-snug",
        className,
      )}
      {...props}
    />
  );
}

function CardHelp({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("mt-0.5 text-xs text-ink-500 leading-snug", className)}
      {...props}
    />
  );
}

export { Card, CardPad, CardHeader, CardTitle, CardHelp };
