"use client";

import { useEffect, useState } from "react";

/**
 * Rotating headline for the sign-in hero.
 *
 * The big "Your investment ___" line cycles between three brand-flavoured
 * promises every 3.5s. Per design handoff §03, the variable span is teal-700
 * weight 600 — _not_ a serif (the prototype's serif was rejected in favour
 * of Noto Sans across the board).
 *
 * The pagination dots sync to the current index — first dot at 32px wide,
 * the other two at 18px (the one-active-of-three pattern from the spec).
 */

const PHRASES = [
  "building your brand.",
  "growing your audience.",
  "driving more revenue.",
] as const;

const ROTATE_MS = 3500;

export function RotatingHeadline() {
  const [idx, setIdx] = useState(0);

  useEffect(() => {
    const t = setInterval(
      () => setIdx((i) => (i + 1) % PHRASES.length),
      ROTATE_MS,
    );
    return () => clearInterval(t);
  }, []);

  return (
    <>
      <h1
        className="m-0 max-w-[820px] text-balance"
        style={{
          font: "700 72px/1.05 var(--font-sans)",
          letterSpacing: "-0.025em",
          color: "var(--fg-strong)",
        }}
      >
        Your investment
        <br />
        <span
          key={idx}
          style={{
            color: "var(--mly-teal-700)",
            fontWeight: 600,
            transition:
              "opacity var(--dur-panel) var(--ease-std), transform var(--dur-panel) var(--ease-std)",
          }}
        >
          {PHRASES[idx]}
        </span>
      </h1>

      <div className="mt-6 flex gap-2" aria-hidden>
        {PHRASES.map((_, i) => (
          <span
            key={i}
            className="block h-[5px] rounded-[3px] transition-[width,background-color] duration-panel ease-std"
            style={{
              width: i === idx ? 32 : 18,
              background:
                i === idx ? "var(--mly-ink-700)" : "var(--mly-ink-300)",
            }}
          />
        ))}
      </div>
    </>
  );
}
