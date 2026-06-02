"use client";

import { useEffect, useRef, useState } from "react";

const MOCK_TURNS = [
  {
    user: "達摩本草產品線與哪些問題類別最匹配？",
    reply:
      "Based on the 47 knowledge cards from your connected sources, here is what I can see relevant to that. (Wireframe — wire this turn to your Decisive Engine + RAG stack for a live, grounded answer.)",
    sources: [
      { label: "acmebank.asia", icon: "link" },
      { label: "Publisher A", icon: "article" },
    ],
  },
];

const MODELS = [
  {
    id: "adaptive",
    label: "Cortex Adaptive",
    sub: "Decisive Engine picks the best model per question",
    recommended: true,
  },
  {
    id: "frontier",
    label: "Frontier · highest quality",
    sub: "force-direct to a top-tier model",
    recommended: false,
  },
  {
    id: "fast",
    label: "Fast · lowest latency",
    sub: "force-direct to a lightweight model",
    recommended: false,
  },
  {
    id: "private",
    label: "Private · in-region",
    sub: "self-hosted, data never leaves region",
    recommended: false,
  },
];

function ModelPicker() {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState("adaptive");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onEsc = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  const current = MODELS.find((m) => m.id === selected) ?? MODELS[0];

  return (
    <div className="ac-model-wrap" ref={ref}>
      {open && (
        <div className="ac-model-popover" role="listbox" aria-label="Choose model">
          <div className="ac-model-hd">ANSWER WITH</div>
          {MODELS.map((m) => (
            <button
              key={m.id}
              type="button"
              role="option"
              aria-selected={selected === m.id}
              className={`ac-model-opt${selected === m.id ? " is-sel" : ""}`}
              onClick={() => { setSelected(m.id); setOpen(false); }}
            >
              <span className="material-icons-outlined ac-model-opt-ic">developer_board</span>
              <div className="ac-model-opt-body">
                <div className="ac-model-opt-nm">
                  {m.label}
                  {m.recommended && <span className="ac-model-rec">RECOMMENDED</span>}
                </div>
                <div className="ac-model-opt-sub">{m.sub}</div>
              </div>
              {selected === m.id && (
                <span className="material-icons-outlined ac-model-check">check</span>
              )}
            </button>
          ))}
          <div className="ac-model-note">
            Adaptive lets the Decisive Engine route each question to the best model. Override only if you need to.
          </div>
        </div>
      )}

      <button
        type="button"
        className={`ac-model-pill${open ? " is-open" : ""}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="material-icons-outlined">developer_board</span>
        {current.label}
        {current.recommended && <span className="ac-model-rec">RECOMMENDED</span>}
        <span className="material-icons-outlined ac-model-chev">
          {open ? "expand_less" : "expand_more"}
        </span>
      </button>
    </div>
  );
}

export function AskCortexPage() {
  return (
    <div className="pg ac">
      {/* Scrollable chat area */}
      <div className="ac-chat">
        <div className="ac-thread">
          {MOCK_TURNS.map((turn, i) => (
            <div className="ac-turn" key={i}>
              <div className="ac-user">
                <div className="ac-user-bubble">{turn.user}</div>
              </div>
              <div className="ac-ai">
                <div className="ac-ai-icon" aria-hidden>
                  <span className="material-icons-outlined">auto_awesome</span>
                </div>
                <div className="ac-ai-body">
                  <div className="ac-ai-card">{turn.reply}</div>
                  <div className="ac-sources">
                    <span className="ac-sources-label">GROUNDED ON</span>
                    {turn.sources.map((s, j) => (
                      <span className="ac-source-pill" key={j}>
                        <span className="material-icons-outlined">{s.icon}</span>
                        {s.label}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pinned input bar */}
      <div className="ac-bar">
        <div className="ac-bar-inner">
          <ModelPicker />
          <div className="ac-input-row">
            <span className="material-icons-outlined ac-input-icon">auto_awesome</span>
            <input
              className="ac-input"
              placeholder="Ask about your brand site..."
              aria-label="Ask Cortex"
            />
            <button type="button" className="ac-send" aria-label="Send">
              <span className="material-icons-outlined">arrow_upward</span>
            </button>
          </div>
          <div className="ac-disclaimer">
            Wireframe · responses are simulated. Charts render from the agent's structured answer spec.
          </div>
        </div>
      </div>
    </div>
  );
}
