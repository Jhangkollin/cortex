import type { CSSProperties, ReactNode } from "react";

interface A4PageProps {
  children: ReactNode;
  bg?: string;
  style?: CSSProperties;
}

/**
 * A4 portrait page wrapper (794×1123 px at 96 dpi).
 * All 8 report pages are absolutely positioned inside this container.
 *
 * Defaults to cream paper (`var(--paper)`) for the Light Edition; the cover
 * page-1 overrides via the `bg` prop to layer in its hero gradient. Shadow is
 * tinted toward paper-deep ink, not pure black, so the page reads as a sheet
 * floating over the warm-paper stage rather than a dark slab.
 */
export function A4Page({ children, bg = "#fff", style = {} }: A4PageProps) {
  return (
    <div
      style={{
        width: 794,
        height: 1123,
        background: bg,
        position: "relative",
        overflow: "hidden",
        boxShadow:
          "0 1px 0 rgba(100, 120, 130, 0.06), 0 30px 60px -20px rgba(80, 100, 110, 0.16)",
        borderRadius: 2,
        ...style,
      }}
    >
      {children}
    </div>
  );
}
