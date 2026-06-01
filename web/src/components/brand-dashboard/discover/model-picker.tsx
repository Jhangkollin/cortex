"use client";

/**
 * Model picker — the `.mdl-pill` trigger + a portaled `.mdl-pop` popover.
 *
 * Mirrors cortex-composer.jsx 30–93 (ModelPill / ModelPicker). The model
 * list is the F2 `COMPOSER_MODELS` contract plus an implicit "auto" entry
 * (Mlytics Cortex AUTO — adaptive routing). The popover portals to
 * `document.body` so it escapes the drawer's `overflow`/stacking context
 * and closes on outside `mousedown`.
 */

import { createPortal } from "react-dom";
import { type CSSProperties, type RefObject, useEffect, useRef } from "react";

import { COMPOSER_MODELS } from "@/lib/discover/mock";
import type { ComposerModel } from "@/lib/discover/types";

// "auto" is the synthetic adaptive-routing entry; any other id is a
// direct-model id from COMPOSER_MODELS.
export type ModelId = string;

export function ModelPill({
  model,
  onClick,
  pillRef,
}: {
  model: ModelId;
  onClick: () => void;
  pillRef: RefObject<HTMLButtonElement | null>;
}) {
  const isAuto = model === "auto";
  const m = isAuto ? null : COMPOSER_MODELS.find((x) => x.id === model);
  return (
    <button ref={pillRef} type="button" className="mdl-pill" onClick={onClick}>
      <span className="mdl-ic">
        <span className="material-icons-outlined">psychology</span>
      </span>
      <span>{isAuto ? "Mlytics Cortex" : (m?.name ?? "Mlytics Cortex")}</span>
      {isAuto ? <span className="mdl-tag">AUTO</span> : null}
      <span className="material-icons-outlined mdl-chev">expand_more</span>
    </button>
  );
}

export function ModelPicker({
  model,
  onChange,
  anchorRect,
  openUp,
  onClose,
}: {
  model: ModelId;
  onChange: (id: ModelId) => void;
  anchorRect: DOMRect | null;
  openUp?: boolean;
  onClose: () => void;
}) {
  const popRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (popRef.current && !popRef.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [onClose]);

  if (!anchorRect || typeof document === "undefined") return null;

  const popStyle: CSSProperties = openUp
    ? {
        left: anchorRect.left,
        bottom: window.innerHeight - anchorRect.top + 8,
      }
    : { left: anchorRect.left, top: anchorRect.bottom + 8 };

  return createPortal(
    <div ref={popRef} className="mdl-pop" style={popStyle}>
      <div className="mdl-header">
        Adaptive Routing
        <span style={{ opacity: 0.5, margin: "0 4px" }}>·</span>
        <b>Recommended</b>
      </div>

      <button
        type="button"
        className="mdl-auto"
        onClick={() => {
          onChange("auto");
          onClose();
        }}
      >
        <span className="mdl-ic">
          <span className="material-icons-outlined">psychology</span>
        </span>
        <div className="mdl-body">
          <div className="mdl-title">
            Mlytics Cortex <span className="mdl-tag">AUTO</span>
          </div>
          <div className="mdl-desc">
            Cortex routes to the optimal model per task
          </div>
        </div>
        {model === "auto" ? (
          <span className="material-icons-outlined mdl-check">check</span>
        ) : null}
      </button>

      <hr />

      <div className="mdl-section">Force direct model</div>
      {COMPOSER_MODELS.map((m: ComposerModel) => (
        <button
          key={m.id}
          type="button"
          className="mdl-row"
          data-selected={model === m.id}
          onClick={() => {
            onChange(m.id);
            onClose();
          }}
        >
          <span className="mdl-ic">
            <span className="material-icons-outlined">{m.icon}</span>
          </span>
          <div>
            <div className="mdl-title">{m.name}</div>
            <div className="mdl-desc">{m.desc}</div>
          </div>
          <span className="mdl-lat">{m.lat}</span>
        </button>
      ))}
    </div>,
    document.body,
  );
}
