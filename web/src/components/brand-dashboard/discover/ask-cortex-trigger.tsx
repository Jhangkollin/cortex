"use client";

/**
 * AskCortexTrigger — the fixed bottom-right pill that opens the docked
 * Cortex drawer.
 *
 * Mirrors cortex-composer.jsx 224–231 (DrawerTrigger). The `⌘K` keycap is
 * rendered by the F1 `.cmp-drawer-trigger::after` rule (so the label here
 * is just the brand mark + "Ask Cortex"), and the same F1 recipe hides the
 * trigger entirely when `.geo-app[data-drawer-open]` is set — no duplicate
 * affordance while the drawer is docked.
 */

import { CortexMark } from "./cortex-mark";
import { useCortexDrawer } from "./drawer-context";

export function AskCortexTrigger() {
  const { openDrawer } = useCortexDrawer();
  return (
    <button
      type="button"
      className="cmp-drawer-trigger"
      aria-label="Ask Cortex"
      onClick={openDrawer}
    >
      <CortexMark size={24} />
      <span>Ask Cortex</span>
    </button>
  );
}
