"use client";

/**
 * Step 1A — Welcome / URL paste.
 *
 * Hero on the left, deep-teal radar visualisation on the right. The deal is
 * "give us your URL and we'll do the rest", so the input is hero-sized and
 * the trust strip below it pre-empts the obvious objections (privacy,
 * latency, editability).
 */

import { useEffect, useRef, useState } from "react";

import { URL_SUGGESTIONS } from "./data";
import { Badge, Icon, OnbButton } from "./primitives";

const EXTRACTION_LABELS: Array<{ x: string; y: string; label: string; icon: string }> = [
  { x: "20%", y: "22%", label: "品牌名稱", icon: "badge" },
  { x: "76%", y: "20%", label: "品牌標誌", icon: "interests" },
  { x: "84%", y: "52%", label: "產品 × 12", icon: "category" },
  { x: "72%", y: "82%", label: "品牌語氣", icon: "campaign" },
  { x: "20%", y: "82%", label: "競品 × 4", icon: "groups" },
  { x: "12%", y: "52%", label: "品類", icon: "psychology" },
];

const TRUST_STRIP = [
  { i: "shield", l: "資料不離開你的工作區", s: "全部僅供 Cortex 內部使用" },
  // Light Edition (handoff Appendix D): 90s → 60s to match the StepCrawl
  // receipt's "用時 74s" timing.
  { i: "schedule", l: "平均 60 秒完成爬取", s: "你可以邊看邊修改" },
  { i: "fact_check", l: "所有結果都可編輯", s: "Cortex 只是先寫好初稿" },
];

export function StepWelcome({
  url,
  setUrl,
  onAnalyze,
  onManual,
}: {
  url: string;
  setUrl: (v: string) => void;
  onAnalyze: () => void;
  onManual: () => void;
}) {
  const [focused, setFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const isValid = url.trim().length >= 3 && url.includes(".");
  const submit = () => {
    if (isValid) onAnalyze();
  };

  const ringActive = focused || url.length > 0;

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1.05fr 1fr",
        gap: 56,
        alignItems: "center",
        minHeight: 580,
      }}
    >
      {/* LEFT */}
      <div>
        <Badge color="amber" style={{ marginBottom: 16 }}>
          第 1 步 · 連結你的網站
        </Badge>
        <h1
          style={{
            fontSize: 46,
            fontWeight: 700,
            color: "var(--mly-ink-900)",
            letterSpacing: "-0.02em",
            lineHeight: 1.1,
            marginBottom: 18,
            margin: 0,
          }}
        >
          只要給我們
          <br />
          <span
            style={{
              background: "linear-gradient(90deg, var(--mly-teal-700), var(--mly-teal-400))",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            一個網址
          </span>
          ，
          <br />
          剩下我們做。
        </h1>
        <p
          style={{
            fontSize: 16,
            color: "var(--mly-ink-600)",
            lineHeight: 1.65,
            maxWidth: 540,
            margin: "18px 0 28px",
          }}
        >
          告訴 Cortex 你的官網在哪裡，我們會自動讀取品牌名稱、產品、Brand Voice 與競品，
          兩分鐘內整理成可編輯的草稿——你只要檢查、按確認。
        </p>

        {/* URL field */}
        <div
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
          style={{
            display: "flex",
            alignItems: "stretch",
            border: `1.5px solid ${ringActive ? "var(--mly-teal-600)" : "var(--mly-ink-200)"}`,
            borderRadius: 10,
            background: "#fff",
            padding: 4,
            boxShadow: ringActive
              ? "0 0 0 4px rgba(34,93,89,0.10), 0 4px 14px rgba(var(--brand-teal-rgb), 0.10)"
              : "0 1px 2px rgba(0,0,0,0.04)",
            transition: "all 160ms",
            marginBottom: 14,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "0 14px 0 18px",
              color: "var(--mly-ink-500)",
              fontFamily: "var(--font-mono)",
              fontSize: 14,
              borderRight: "1px dashed var(--mly-ink-150)",
            }}
          >
            <Icon name="language" size={18} />
            https://
          </div>
          <input
            ref={inputRef}
            value={url}
            onChange={(e) => setUrl(e.target.value.replace(/^https?:\/\//, ""))}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="your-website.com"
            style={{
              flex: 1,
              border: "none",
              outline: "none",
              fontSize: 18,
              fontFamily: "var(--font-mono)",
              color: "var(--mly-ink-900)",
              padding: "16px 12px",
              minWidth: 0,
              background: "transparent",
            }}
            aria-label="您的網站網址"
          />
          <OnbButton
            variant="dark"
            size="lg"
            iconRight="arrow_forward"
            disabled={!isValid}
            onClick={submit}
            style={{ borderRadius: 7 }}
          >
            分析我的品牌
          </OnbButton>
        </div>

        {/* Suggestions + manual fallback */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            alignItems: "center",
            gap: 8,
            marginBottom: 36,
          }}
        >
          <span style={{ fontSize: 12, color: "var(--mly-ink-500)" }}>試試：</span>
          {URL_SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setUrl(s)}
              style={{
                padding: "4px 10px",
                borderRadius: 999,
                background: "#fff",
                border: "1px solid var(--mly-ink-200)",
                color: "var(--mly-ink-600)",
                fontSize: 12,
                fontFamily: "var(--font-mono)",
                cursor: "pointer",
                transition: "all 120ms",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--mly-teal-400)";
                e.currentTarget.style.color = "var(--mly-teal-700)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--mly-ink-200)";
                e.currentTarget.style.color = "var(--mly-ink-600)";
              }}
            >
              {s}
            </button>
          ))}
          <span style={{ color: "var(--mly-ink-300)", margin: "0 4px" }}>·</span>
          <button
            type="button"
            onClick={onManual}
            style={{
              background: "transparent",
              border: "none",
              padding: 0,
              color: "var(--brand-teal)",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 600,
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
              fontFamily: "inherit",
            }}
          >
            {/* Light Edition (handoff Appendix D): edit_note icon dropped —
                plain text link reads lighter as a fallback affordance. */}
            沒有官網？手動填寫
          </button>
        </div>

        {/* Trust strip */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 18,
            paddingTop: 24,
            borderTop: "1px solid var(--mly-ink-100)",
          }}
        >
          {TRUST_STRIP.map((t) => (
            <div key={t.l} style={{ display: "flex", gap: 10 }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 6,
                  background: "var(--mly-teal-050)",
                  display: "grid",
                  placeItems: "center",
                  flexShrink: 0,
                }}
              >
                <Icon name={t.i} size={16} color="var(--mly-teal-700)" />
              </div>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: "var(--mly-ink-900)" }}>
                  {t.l}
                </div>
                <div style={{ fontSize: 11, color: "var(--mly-ink-500)", marginTop: 1 }}>{t.s}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* RIGHT — radar visualisation (Light Edition). See en sibling for
          the full rationale: cream radial + fixed 480×480 stage + gold
          sweep clipped to the outermost ring (handoff Appendix B). */}
      <div style={{ position: "relative", height: 560 }}>
        <div
          style={{
            position: "absolute",
            inset: 0,
            borderRadius: 14,
            overflow: "hidden",
            background:
              "radial-gradient(circle at 50% 40%, var(--paper-highlight) 0%, var(--paper) 55%, var(--paper-warm) 100%)",
            border: "1px solid var(--paper-border)",
            boxShadow:
              "0 20px 40px -16px rgba(var(--paper-ink-rgb), 0.18), 0 4px 12px -4px rgba(var(--paper-ink-rgb), 0.06)",
          }}
        >
          {/* Fixed-size square radar stage. */}
          <div
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              transform: "translate(-50%, -50%)",
              width: 480,
              height: 480,
            }}
          >
            {/* concentric warm-gray dashed rings */}
            {[0.92, 0.7, 0.5, 0.32, 0.16].map((s, i) => (
              <div
                key={i}
                aria-hidden
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "50%",
                  width: `${s * 100}%`,
                  height: `${s * 100}%`,
                  transform: "translate(-50%,-50%)",
                  borderRadius: "50%",
                  border: "1px dashed rgba(110,96,69,0.30)",
                }}
              />
            ))}
            {/* Gold radar sweep clipped to outermost ring. */}
            <div
              aria-hidden
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                width: "92%",
                height: "92%",
                transform: "translate(-50%, -50%)",
                borderRadius: "50%",
                overflow: "hidden",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  borderRadius: "50%",
                  background:
                    "conic-gradient(from 0deg, rgba(var(--gold-rgb), 0.55) 0deg, rgba(var(--gold-rgb), 0.30) 20deg, rgba(var(--gold-rgb), 0.12) 50deg, transparent 90deg)",
                  maskImage: "radial-gradient(circle, transparent 24%, black 42%)",
                  WebkitMaskImage:
                    "radial-gradient(circle, transparent 24%, black 42%)",
                  animation: "mly-radar-sweep 5s linear infinite",
                }}
              />
            </div>
            {/* Centre URL globe — brand-teal disc + white earth + gold ring. */}
            <div
              style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                transform: "translate(-50%,-50%)",
                width: 96,
                height: 96,
                borderRadius: "50%",
                background: "var(--brand-teal)",
                display: "grid",
                placeItems: "center",
                color: "#fff",
                boxShadow:
                  "0 8px 26px rgba(var(--brand-teal-rgb), 0.30), inset 0 -4px 10px rgba(0,0,0,0.15)",
                border: "2px solid #fff",
              }}
            >
              <div
                aria-hidden
                style={{
                  position: "absolute",
                  inset: -8,
                  borderRadius: "50%",
                  border: "1.5px dashed var(--gold)",
                  opacity: 0.7,
                }}
              />
              <div style={{ textAlign: "center", position: "relative" }}>
                <Icon name="language" size={24} color="#fff" />
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 10,
                    fontWeight: 700,
                    marginTop: 2,
                    letterSpacing: "0.04em",
                    color: "#fff",
                  }}
                >
                  {url || "您的網站"}
                </div>
              </div>
            </div>
          </div>

          {/* Extraction pill labels — white cards with paper-border. */}
          {EXTRACTION_LABELS.map((p, i) => (
            <div
              key={p.label}
              style={{
                position: "absolute",
                left: p.x,
                top: p.y,
                transform: "translate(-50%,-50%)",
                display: "flex",
                alignItems: "center",
                gap: 6,
                padding: "6px 12px",
                borderRadius: 999,
                background: "#fff",
                border: "1px solid var(--paper-border)",
                boxShadow: "0 2px 8px -2px rgba(var(--paper-ink-rgb), 0.10)",
                fontSize: 12,
                color: "var(--paper-ink)",
                whiteSpace: "nowrap",
                fontWeight: 600,
                animation: `mly-fade-up 600ms ${i * 120}ms backwards`,
              }}
            >
              <Icon name={p.icon} size={13} color="var(--brand-teal)" />
              {p.label}
            </div>
          ))}
          {/* Corner stats */}
          <div
            style={{
              position: "absolute",
              left: 18,
              top: 18,
              color: "var(--paper-ink-3)",
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              letterSpacing: "0.06em",
              fontWeight: 700,
            }}
          >
            <div>CORTEX · CRAWLER v3.2</div>
            <div
              style={{
                marginTop: 2,
                color: "var(--lime-deep)",
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              <span
                style={{
                  width: 6,
                  height: 6,
                  borderRadius: "50%",
                  background: "var(--lime-deep)",
                  boxShadow: "0 0 6px rgba(var(--lime-deep-rgb), 0.6)",
                }}
              />
              就緒
            </div>
          </div>
          <div
            style={{
              position: "absolute",
              right: 18,
              bottom: 18,
              color: "var(--paper-ink-3)",
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              textAlign: "right",
            }}
          >
            <div
              style={{
                fontSize: 18,
                fontWeight: 700,
                color: "var(--paper-ink)",
                fontFamily: "var(--font-numeric)",
                letterSpacing: "-0.02em",
              }}
            >
              240+
            </div>
            <div style={{ marginTop: 2 }}>家品牌已上線</div>
          </div>
        </div>
      </div>
    </div>
  );
}
