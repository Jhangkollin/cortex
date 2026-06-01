"use client";

/**
 * ComposerCard — the shared chat-input card body.
 *
 * Mirrors cortex-composer.jsx 96–151: a `.cmp` shell with a single-line
 * `.cmp-input` and a `.cmp-foot` action row (ModelPill, attach, optional
 * version tag, mic, optional send). The model picker is owned here so the
 * pill anchor rect can be measured on toggle. All wiring is mock — no LLM
 * call; `onSend` is the integration seam.
 */

import { useRef, useState } from "react";

import { ModelPicker, ModelPill, type ModelId } from "./model-picker";

interface ComposerCardProps {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  model: ModelId;
  setModel: (id: ModelId) => void;
  openUp?: boolean;
  sendLabel?: string;
  showVersion?: boolean;
  onSend?: (value: string) => void;
}

export function ComposerCard({
  value,
  onChange,
  placeholder,
  model,
  setModel,
  openUp,
  sendLabel,
  showVersion,
  onSend,
}: ComposerCardProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [anchor, setAnchor] = useState<DOMRect | null>(null);
  const pillRef = useRef<HTMLButtonElement>(null);

  const togglePicker = () => {
    if (pickerOpen) {
      setPickerOpen(false);
      return;
    }
    if (pillRef.current) setAnchor(pillRef.current.getBoundingClientRect());
    setPickerOpen(true);
  };

  const handleSend = () => onSend?.(value);
  const handleKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="cmp">
      <input
        className="cmp-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKey}
        placeholder={placeholder}
      />
      <div className="cmp-foot">
        <ModelPill model={model} onClick={togglePicker} pillRef={pillRef} />
        <button type="button" className="cmp-plus" aria-label="Add attachment">
          <span className="material-icons-outlined">add</span>
        </button>
        <div className="grow" />
        {showVersion ? <span className="cmp-version">Cortex v3.2</span> : null}
        <button type="button" className="cmp-mic" aria-label="Voice input">
          <span className="material-icons-outlined">mic</span>
        </button>
        {sendLabel ? (
          <button type="button" className="cmp-send" onClick={handleSend}>
            <span className="material-icons-outlined">arrow_upward</span>
            {sendLabel}
          </button>
        ) : null}
      </div>
      {pickerOpen ? (
        <ModelPicker
          model={model}
          onChange={setModel}
          anchorRect={anchor}
          openUp={openUp}
          onClose={() => setPickerOpen(false)}
        />
      ) : null}
    </div>
  );
}
