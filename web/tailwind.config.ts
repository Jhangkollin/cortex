import type { Config } from "tailwindcss";

/**
 * Mlytics Cortex Tailwind config — token-aliased.
 *
 * The single source of truth for design tokens is `src/app/tokens.css`.
 * Tailwind utilities here just point at those CSS variables, so a token
 * change flows everywhere without touching component code.
 *
 * Usage examples (see handoff/Mlytics Cortex - Design Handoff.html):
 *   bg-brand-700 text-white       → primary brand teal
 *   bg-brand-800                  → sidebar dark surface
 *   text-ink-500                  → muted body copy
 *   border-ink-200                → default control border
 *   font-numeric                  → Roboto for KPI numbers
 *   rounded-md                    → 8px card radius
 */
const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "var(--mly-teal-050)",
          100: "var(--mly-teal-100)",
          200: "var(--mly-teal-200)",
          400: "var(--mly-teal-400)",
          500: "var(--mly-teal-500)",
          600: "var(--mly-teal-600)",
          700: "var(--mly-teal-700)",
          800: "var(--mly-teal-800)",
          900: "var(--mly-teal-900)",
        },
        ink: {
          25: "var(--mly-ink-025)",
          50: "var(--mly-ink-050)",
          100: "var(--mly-ink-100)",
          150: "var(--mly-ink-150)",
          200: "var(--mly-ink-200)",
          300: "var(--mly-ink-300)",
          400: "var(--mly-ink-400)",
          500: "var(--mly-ink-500)",
          600: "var(--mly-ink-600)",
          700: "var(--mly-ink-700)",
          800: "var(--mly-ink-800)",
          900: "var(--mly-ink-900)",
        },
        lime: {
          100: "var(--mly-lime-100)",
          200: "var(--mly-lime-200)",
          500: "var(--mly-lime-500)",
        },
        amber: {
          50: "var(--cortex-amber-50)",
          200: "var(--cortex-amber-200)",
          500: "var(--cortex-amber-500)",
          600: "var(--cortex-amber-600)",
        },
        purple: {
          fg: "var(--cortex-purple-fg)",
          bg: "var(--cortex-purple-bg)",
          bd: "var(--cortex-purple-bd)",
        },
        info: "var(--mly-info)",
        warn: "var(--mly-warn)",
        success: "var(--mly-success)",
        danger: "var(--mly-danger)",
      },
      fontFamily: {
        sans: ["Noto Sans", "system-ui", "-apple-system", "sans-serif"],
        numeric: ["Roboto", "Noto Sans", "system-ui", "sans-serif"],
        mono: ["Roboto Mono", "Roboto", "ui-monospace", "Menlo", "monospace"],
      },
      borderRadius: {
        xs: "2px",
        sm: "4px",
        md: "8px",
        lg: "12px",
      },
      boxShadow: {
        "elev-1": "0 1px 2px rgba(0,0,0,0.06), 0 1px 1px rgba(0,0,0,0.04)",
        "elev-2": "0 2px 6px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04)",
        "elev-3": "0 6px 16px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.05)",
      },
      transitionTimingFunction: {
        std: "cubic-bezier(0.4, 0, 0.2, 1)",
      },
      transitionDuration: {
        state: "120ms",
        panel: "200ms",
        route: "320ms",
      },
    },
  },
  plugins: [],
};

export default config;
