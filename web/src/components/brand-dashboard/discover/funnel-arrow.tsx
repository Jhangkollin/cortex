"use client";

import { useId } from "react";

// markerId still needed for the SVG <marker> element uniqueness
export function FunnelArrow({
  kind,
}: {
  rate?: string;
  label?: unknown;
  kind?: "bottleneck" | "leverage";
}) {
  const markerId = `funnel-arrow-${useId()}`;
  return (
    <div className={`conn${kind ? " is-" + kind : ""}`}>
      <svg width="48" height="12" viewBox="0 0 48 12">
        <defs>
          <marker
            id={markerId}
            markerWidth="6"
            markerHeight="6"
            refX="5"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L0,6 L6,3 z" fill="#9E9E9E" />
          </marker>
        </defs>
        <line
          x1="0"
          y1="6"
          x2="44"
          y2="6"
          stroke="#9E9E9E"
          strokeWidth="1.2"
          markerEnd={`url(#${markerId})`}
        />
      </svg>
    </div>
  );
}
