"use client";

/**
 * CortexDrawer — the docked Cortex assistant panel.
 *
 * Mirrors cortex-composer.jsx 233–277 (DrawerComposer). Reads the lifted
 * drawer state from `useCortexDrawer()` (F3 context) so the in-stage query
 * strip, the ⌘K trigger, and this panel share one source of truth.
 *
 * State preservation ("don't unmount on close"): the conversation state —
 * input `value` and selected `model` — lives in `useCortexDrawer()`, not in
 * this component. The `.cmp-drawer` aside is only rendered while
 * `drawerOpen`, but because the state is owned by the provider it survives
 * close→reopen with no loss (spec §6.8 / §2.2 / §7.2.2).
 *
 * This is a *docked* drawer, not a modal: the `.cmp-drawer-backdrop`
 * element is present in the tree but the F1 `.geo-app[data-drawer-open]`
 * recipe hides it (no scrim) and reserves a 3rd grid column so content
 * never overlaps. Visibility/dock are CSS-driven; this file owns markup +
 * wiring only.
 */

import { useCortexDrawer } from "./drawer-context";
import { ComposerCard } from "./composer-card";

// Verbatim from cortex-composer.jsx 22–27.
const DRAWER_QUICK = [
  "本週品牌曝光走勢",
  "未覆蓋話題清單",
  "競品差距分析",
  "派工給 Answer Pilot",
];

export function CortexDrawer() {
  const { drawerOpen, closeDrawer, value, setValue, model, setModel } =
    useCortexDrawer();

  if (!drawerOpen) return null;

  return (
    <>
      <div className="cmp-drawer-backdrop" onClick={closeDrawer} />
      <aside className="cmp-drawer" role="dialog" aria-label="Cortex Assistant">
        <div className="head">
          <span className="title">Cortex Assistant</span>
          <div className="grow" />
          <button
            type="button"
            className="close"
            onClick={closeDrawer}
            aria-label="Close"
          >
            <span className="material-icons-outlined">close</span>
          </button>
        </div>

        <div className="empty">
          <div className="hero-ic">
            <span className="material-icons-outlined">auto_awesome</span>
          </div>
          <div className="hero-title">Explore your content network</div>
          <div className="hero-sub">
            Ask questions about brand visibility, competitors, or content
            opportunities. Cortex pulls from your live media network data.
          </div>
          <div className="quick">
            {DRAWER_QUICK.map((q) => (
              <button key={q} type="button" onClick={() => setValue(q)}>
                {q}
              </button>
            ))}
          </div>
        </div>

        <div className="foot">
          <ComposerCard
            value={value}
            onChange={setValue}
            placeholder="@ for objects, / for commands"
            model={model}
            setModel={setModel}
            openUp
            showVersion={false}
          />
          <div className="disclaimer">
            Always review the accuracy of responses.
          </div>
        </div>
      </aside>
    </>
  );
}
