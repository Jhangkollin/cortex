"use client";

/**
 * Step 2 — Review the extracted brand profile.
 *
 * Layout: a 5-up summary strip at the top, then a 2-column grid of cards
 * (brand identity, category, products full-width, voice samples, competitors)
 * with a teal "next step" callout pinned to the bottom. Every field is
 * editable in-place; toggling products/voice/competitors flows back into the
 * parent draft via `setBrand`.
 */

import { useState } from "react";

import type { ExtractedBrand } from "./data";
import { Badge, Card, Icon, OnbButton, StepHead, Toggle } from "./primitives";

function EditableField({
  label,
  value,
  onChange,
  multiline,
  fontSize = 14,
  fontWeight = 500,
  fontFamily,
}: {
  label?: string;
  value: string;
  onChange: (v: string) => void;
  multiline?: boolean;
  fontSize?: number;
  fontWeight?: number;
  fontFamily?: string;
}) {
  const [editing, setEditing] = useState(false);
  // `draft` is only meaningful while editing. We re-seed it from the latest
  // `value` every time the user opens the editor (not via useEffect, which
  // would chain a re-render). That means external value changes mid-edit
  // are intentionally ignored — the right behaviour for an inline editor.
  const [draft, setDraft] = useState(value);
  const startEdit = () => {
    setDraft(value);
    setEditing(true);
  };
  const commit = () => {
    onChange(draft);
    setEditing(false);
  };
  const cancel = () => {
    setEditing(false);
  };

  if (!editing) {
    return (
      <div style={{ display: "flex", alignItems: "flex-start", gap: 6 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          {label ? (
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "var(--mly-ink-500)",
                marginBottom: 3,
              }}
            >
              {label}
            </div>
          ) : null}
          <div
            style={{
              fontSize,
              fontWeight,
              color: "var(--mly-ink-900)",
              fontFamily,
              lineHeight: 1.45,
              wordBreak: "break-word",
            }}
          >
            {value || (
              <span style={{ color: "var(--mly-ink-400)", fontStyle: "italic" }}>— 未提供 —</span>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={startEdit}
          aria-label={`編輯 ${label ?? "欄位"}`}
          style={{
            background: "transparent",
            border: "none",
            padding: 4,
            marginTop: label ? 14 : 0,
            color: "var(--mly-ink-400)",
            cursor: "pointer",
            borderRadius: 4,
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "var(--mly-ink-050)";
            e.currentTarget.style.color = "var(--mly-teal-700)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent";
            e.currentTarget.style.color = "var(--mly-ink-400)";
          }}
        >
          <Icon name="edit" size={14} />
        </button>
      </div>
    );
  }

  const sharedInputStyle = {
    width: "100%",
    padding: "6px 10px",
    fontSize,
    fontWeight,
    border: "1.5px solid var(--mly-teal-600)",
    borderRadius: 6,
    outline: "none",
    color: "var(--mly-ink-900)",
    background: "#fff",
    lineHeight: 1.45,
    fontFamily: fontFamily ?? "inherit",
  } as const;

  return (
    <div style={{ flex: 1 }}>
      {label ? (
        <div
          style={{
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "var(--mly-ink-500)",
            marginBottom: 3,
          }}
        >
          {label}
        </div>
      ) : null}
      {multiline ? (
        <textarea
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Escape") cancel();
          }}
          rows={3}
          style={{ ...sharedInputStyle, resize: "vertical" }}
        />
      ) : (
        <input
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") commit();
            if (e.key === "Escape") cancel();
          }}
          style={{ ...sharedInputStyle, resize: "none" }}
        />
      )}
      <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
        <OnbButton variant="primary" size="xs" icon="check" onClick={commit}>
          儲存
        </OnbButton>
        <OnbButton variant="soft" size="xs" onClick={cancel}>
          取消
        </OnbButton>
      </div>
    </div>
  );
}

export function StepReview({
  brand,
  setBrand,
  onConfirm,
}: {
  brand: ExtractedBrand;
  setBrand: (b: ExtractedBrand) => void;
  onConfirm: () => void;
}) {
  const update = (patch: Partial<ExtractedBrand>) => setBrand({ ...brand, ...patch });

  const toggleProduct = (id: string) =>
    update({
      products: brand.products.map((p) => (p.id === id ? { ...p, picked: !p.picked } : p)),
    });
  const toggleVoice = (i: number) =>
    update({
      voiceSamples: brand.voiceSamples.map((s, idx) =>
        idx === i ? { ...s, picked: !s.picked } : s,
      ),
    });
  const toggleCompetitor = (id: string) =>
    update({
      competitors: brand.competitors.map((c) =>
        c.id === id ? { ...c, picked: !c.picked } : c,
      ),
    });

  const productsOn = brand.products.filter((p) => p.picked).length;
  const voiceOn = brand.voiceSamples.filter((v) => v.picked).length;
  const competitorsOn = brand.competitors.filter((c) => c.picked).length;

  const summary: Array<{
    l: string;
    v: number;
    t: number | null;
    suffix?: string;
    i: string;
  }> = [
    { l: "產品", v: productsOn, t: brand.products.length, i: "category" },
    { l: "Voice 樣本", v: voiceOn, t: brand.voiceSamples.length, i: "campaign" },
    { l: "競品", v: competitorsOn, t: brand.competitors.length, i: "groups" },
    { l: "區域", v: brand.region.length, t: null, i: "place" },
    {
      l: "品類信心度",
      v: brand.category.confidence,
      t: null,
      suffix: "%",
      i: "psychology",
    },
  ];

  return (
    <div>
      <StepHead
        eyebrow="第 2 步 · 確認資料"
        title="我們找到這些資訊——請快速看一遍"
        subtitle="所有欄位都可以直接修改。看到不對的地方點旁邊的鉛筆。確認後，我們會用這份資料分析你的媒體與本週問題。"
        accent={`從 ${brand.url} 抓取 · 25 秒前 · 47 筆原始資料`}
      />

      {/* Summary strip */}
      <Card
        style={{
          padding: 16,
          marginBottom: 16,
          background: "linear-gradient(135deg, var(--mly-teal-050), #fff 60%)",
          border: "1px solid var(--mly-teal-100)",
        }}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: 16,
            alignItems: "center",
          }}
        >
          {summary.map((s) => (
            <div key={s.l} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: 8,
                  background: "#fff",
                  border: "1px solid var(--mly-teal-100)",
                  display: "grid",
                  placeItems: "center",
                }}
              >
                <Icon name={s.i} size={16} color="var(--mly-teal-700)" />
              </div>
              <div>
                <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                  <span
                    style={{
                      fontFamily: "var(--font-numeric)",
                      fontWeight: 700,
                      fontSize: 22,
                      color: "var(--mly-ink-900)",
                      lineHeight: 1,
                    }}
                  >
                    {s.v}
                    {s.suffix ?? ""}
                  </span>
                  {s.t ? (
                    <span style={{ fontSize: 11, color: "var(--mly-ink-400)" }}>/ {s.t}</span>
                  ) : null}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: "var(--mly-ink-500)",
                    fontFamily: "var(--font-mono)",
                    letterSpacing: "0.04em",
                    marginTop: 2,
                    textTransform: "uppercase",
                    fontWeight: 600,
                  }}
                >
                  {s.l}
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        {/* Brand identity */}
        <Card style={{ padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <Icon name="badge" size={18} color="var(--mly-teal-700)" />
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--mly-ink-900)" }}>
              品牌識別
            </div>
            <Badge color="teal" style={{ marginLeft: "auto" }}>
              自動辨識
            </Badge>
          </div>
          <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
            <div style={{ position: "relative" }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: 12,
                  background: `linear-gradient(135deg, ${brand.brandColor}, var(--mly-teal-800))`,
                  color: "#fff",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 700,
                  fontSize: 26,
                  letterSpacing: "-0.02em",
                  boxShadow: "0 4px 14px rgba(var(--brand-teal-rgb), 0.25)",
                }}
              >
                {brand.monogram}
              </div>
              <button
                type="button"
                aria-label="上傳 Logo"
                style={{
                  position: "absolute",
                  bottom: -4,
                  right: -4,
                  width: 22,
                  height: 22,
                  borderRadius: "50%",
                  background: "#fff",
                  border: "1px solid var(--mly-ink-150)",
                  display: "grid",
                  placeItems: "center",
                  cursor: "pointer",
                  color: "var(--mly-ink-500)",
                }}
              >
                <Icon name="upload" size={12} />
              </button>
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 10 }}>
              <EditableField
                label="品牌名稱"
                value={brand.name}
                onChange={(v) => update({ name: v })}
                fontSize={16}
                fontWeight={700}
              />
              <EditableField
                label="標語"
                value={brand.tagline}
                onChange={(v) => update({ tagline: v })}
                fontSize={13}
                fontWeight={500}
              />
              <EditableField
                label="法人實體"
                value={brand.legalName}
                onChange={(v) => update({ legalName: v })}
                fontSize={12}
                fontWeight={400}
                fontFamily="var(--font-mono)"
              />
            </div>
          </div>
        </Card>

        {/* Category & region */}
        <Card style={{ padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
            <Icon name="psychology" size={18} color="var(--mly-teal-700)" />
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--mly-ink-900)" }}>
              品類與市場
            </div>
            <Badge color="amber" style={{ marginLeft: "auto" }}>
              {brand.category.confidence}% 信心
            </Badge>
          </div>
          <div style={{ marginBottom: 14 }}>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "var(--mly-ink-500)",
                marginBottom: 6,
              }}
            >
              主要品類
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  padding: "6px 14px",
                  borderRadius: 999,
                  background: "var(--mly-teal-700)",
                  color: "#fff",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {brand.category.value}
              </span>
              <button
                type="button"
                aria-label="切換主要品類"
                style={{
                  background: "transparent",
                  border: "none",
                  padding: 0,
                  color: "var(--mly-ink-400)",
                  cursor: "pointer",
                }}
              >
                <Icon name="swap_horiz" size={16} />
              </button>
            </div>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 6,
                marginTop: 10,
                fontSize: 11,
                color: "var(--mly-ink-500)",
              }}
            >
              <span>替代選項：</span>
              {brand.category.alternatives.map((a) => (
                <button
                  key={a}
                  type="button"
                  onClick={() =>
                    update({
                      category: {
                        ...brand.category,
                        value: a,
                        alternatives: [
                          brand.category.value,
                          ...brand.category.alternatives.filter((x) => x !== a),
                        ],
                      },
                    })
                  }
                  style={{
                    padding: "2px 9px",
                    borderRadius: 999,
                    background: "#fff",
                    border: "1px solid var(--mly-ink-200)",
                    color: "var(--mly-ink-600)",
                    fontSize: 11,
                    cursor: "pointer",
                  }}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div
              style={{
                fontSize: 10,
                fontWeight: 700,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "var(--mly-ink-500)",
                marginBottom: 6,
              }}
            >
              區域
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
              {brand.region.map((r) => (
                <span
                  key={r}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 4,
                    padding: "4px 10px",
                    borderRadius: 999,
                    background: "var(--mly-teal-050)",
                    color: "var(--mly-teal-700)",
                    fontSize: 12,
                    fontWeight: 500,
                  }}
                >
                  <Icon name="place" size={11} /> {r}
                  <button
                    type="button"
                    aria-label={`Remove ${r}`}
                    onClick={() =>
                      update({ region: brand.region.filter((x) => x !== r) })
                    }
                    style={{
                      background: "transparent",
                      border: "none",
                      padding: 0,
                      color: "currentColor",
                      cursor: "pointer",
                      marginLeft: 2,
                    }}
                  >
                    <Icon name="close" size={11} />
                  </button>
                </span>
              ))}
              <button
                type="button"
                style={{
                  padding: "4px 10px",
                  borderRadius: 999,
                  background: "#fff",
                  color: "var(--mly-ink-500)",
                  border: "1px dashed var(--mly-ink-300)",
                  fontSize: 12,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 4,
                }}
              >
                <Icon name="add" size={12} /> 新增
              </button>
            </div>
          </div>
        </Card>

        {/* Products */}
        <Card style={{ padding: 18, gridColumn: "1 / -1" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Icon name="category" size={18} color="var(--mly-teal-700)" />
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--mly-ink-900)" }}>
              產品（已勾選的會用來回答問題）
            </div>
            <span style={{ fontSize: 11, color: "var(--mly-ink-500)" }}>
              {productsOn} / {brand.products.length} 啟用
            </span>
            <OnbButton variant="ghost" size="xs" icon="add" style={{ marginLeft: "auto" }}>
              新增產品
            </OnbButton>
          </div>
          <div className="onb-grid-2-3" style={{ gap: 8 }}>
            {brand.products.map((p, idx) => (
              <div
                key={p.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto 1fr auto auto",
                  gap: 12,
                  alignItems: "center",
                  padding: "12px 14px",
                  background: p.picked ? "#fff" : "var(--mly-ink-025)",
                  border: `1px solid ${
                    p.picked ? "var(--mly-teal-100)" : "var(--mly-ink-150)"
                  }`,
                  borderRadius: 8,
                  opacity: p.picked ? 1 : 0.7,
                  animation: `mly-fade-up 280ms ${idx * 25}ms backwards`,
                  transition: "all 160ms",
                }}
              >
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 6,
                    background: p.picked ? "var(--mly-teal-050)" : "var(--mly-ink-050)",
                    color: p.picked ? "var(--mly-teal-700)" : "var(--mly-ink-400)",
                    display: "grid",
                    placeItems: "center",
                  }}
                >
                  <Icon name={p.icon} size={16} />
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span
                      style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: "var(--mly-ink-900)",
                      }}
                    >
                      {p.name}
                    </span>
                    <span
                      style={{
                        fontSize: 10,
                        padding: "1px 6px",
                        background: "var(--mly-ink-050)",
                        color: "var(--mly-ink-500)",
                        borderRadius: 3,
                        fontWeight: 500,
                      }}
                    >
                      {p.category}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: "var(--mly-ink-400)",
                      fontFamily: "var(--font-mono)",
                      marginTop: 2,
                    }}
                  >
                    {brand.url}
                    {p.url}
                  </div>
                </div>
                <div style={{ textAlign: "right", minWidth: 38 }}>
                  <div
                    style={{
                      fontFamily: "var(--font-numeric)",
                      fontWeight: 700,
                      fontSize: 13,
                      color: p.confidence >= 90 ? "var(--mly-success)" : "var(--cortex-amber-600)",
                      lineHeight: 1,
                    }}
                  >
                    {p.confidence}%
                  </div>
                  <div
                    style={{
                      fontSize: 9,
                      color: "var(--mly-ink-400)",
                      fontFamily: "var(--font-mono)",
                      letterSpacing: "0.04em",
                      marginTop: 1,
                    }}
                  >
                    信心
                  </div>
                </div>
                <Toggle on={p.picked} onChange={() => toggleProduct(p.id)} size="sm" />
              </div>
            ))}
          </div>
          {brand.productMoreCount > 0 ? (
            <button
              type="button"
              style={{
                marginTop: 10,
                padding: "8px 14px",
                background: "var(--mly-ink-025)",
                border: "1px dashed var(--mly-ink-200)",
                borderRadius: 6,
                width: "100%",
                cursor: "pointer",
                color: "var(--mly-ink-600)",
                fontSize: 12,
                fontWeight: 500,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
              }}
            >
              <Icon name="unfold_more" size={14} /> 顯示其餘 {brand.productMoreCount} 個產品
            </button>
          ) : null}
        </Card>

        {/* Brand voice */}
        <Card style={{ padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Icon name="campaign" size={18} color="var(--mly-teal-700)" />
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--mly-ink-900)" }}>
              Brand Voice 樣本
            </div>
            <Badge color="ink" style={{ marginLeft: "auto" }}>
              從你的官網擷取
            </Badge>
          </div>
          <div style={{ fontSize: 12, color: "var(--mly-ink-500)", marginBottom: 12 }}>
            勾選代表性最強的句子，Cortex 會用這些建立你的語調指紋。
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {brand.voiceSamples.map((s, i) => (
              <button
                key={`${s.src}-${i}`}
                type="button"
                onClick={() => toggleVoice(i)}
                style={{
                  textAlign: "left",
                  display: "grid",
                  gridTemplateColumns: "auto 1fr",
                  gap: 10,
                  alignItems: "flex-start",
                  padding: "10px 12px",
                  borderRadius: 6,
                  cursor: "pointer",
                  background: s.picked ? "var(--mly-teal-050)" : "#fff",
                  border: `1px solid ${
                    s.picked ? "var(--mly-teal-200)" : "var(--mly-ink-150)"
                  }`,
                  fontFamily: "inherit",
                }}
              >
                <div
                  style={{
                    width: 18,
                    height: 18,
                    borderRadius: 4,
                    marginTop: 2,
                    background: s.picked ? "var(--mly-teal-600)" : "transparent",
                    border: `1.5px solid ${
                      s.picked ? "var(--mly-teal-600)" : "var(--mly-ink-300)"
                    }`,
                    display: "grid",
                    placeItems: "center",
                    flexShrink: 0,
                  }}
                >
                  {s.picked ? <Icon name="check" size={12} color="#fff" /> : null}
                </div>
                <div>
                  <div
                    style={{
                      fontSize: 13,
                      color: "var(--mly-ink-900)",
                      lineHeight: 1.45,
                      fontWeight: s.picked ? 500 : 400,
                    }}
                  >
                    “{s.text}”
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: "var(--mly-ink-500)",
                      fontFamily: "var(--font-mono)",
                      marginTop: 3,
                    }}
                  >
                    來源 {brand.url}
                    {s.src}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </Card>

        {/* Competitors */}
        <Card style={{ padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <Icon name="groups" size={18} color="var(--mly-teal-700)" />
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--mly-ink-900)" }}>
              主要競品
            </div>
            <Badge color="ink" style={{ marginLeft: "auto" }}>
              同品類比對
            </Badge>
          </div>
          <div style={{ fontSize: 12, color: "var(--mly-ink-500)", marginBottom: 12 }}>
            Cortex 會追蹤這些品牌在媒體上的曝光，提醒你哪裡正在被搶走機會。
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {brand.competitors.map((c, i) => (
              <div
                key={c.id}
                style={{
                  display: "grid",
                  gridTemplateColumns: "auto 1fr auto auto",
                  gap: 10,
                  alignItems: "center",
                  padding: "10px 12px",
                  borderRadius: 6,
                  background: c.picked ? "#fff" : "var(--mly-ink-025)",
                  border: `1px solid ${
                    c.picked ? "var(--mly-teal-100)" : "var(--mly-ink-150)"
                  }`,
                  opacity: c.picked ? 1 : 0.7,
                  animation: `mly-fade-up 280ms ${i * 30}ms backwards`,
                }}
              >
                <div
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: 6,
                    flexShrink: 0,
                    background: `hsl(${(i * 137) % 360}, 25%, 90%)`,
                    color: `hsl(${(i * 137) % 360}, 40%, 30%)`,
                    display: "grid",
                    placeItems: "center",
                    fontWeight: 700,
                    fontSize: 13,
                  }}
                >
                  {c.name.charAt(0)}
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "var(--mly-ink-900)" }}>
                    {c.name}
                  </div>
                  <div
                    style={{
                      fontSize: 10,
                      color: "var(--mly-ink-400)",
                      fontFamily: "var(--font-mono)",
                      marginTop: 1,
                    }}
                  >
                    {c.domain}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div
                    style={{
                      fontFamily: "var(--font-numeric)",
                      fontWeight: 700,
                      fontSize: 13,
                      color: "var(--mly-ink-800)",
                      lineHeight: 1,
                    }}
                  >
                    {c.matchScore}
                  </div>
                  <div
                    style={{
                      fontSize: 9,
                      color: "var(--mly-ink-400)",
                      fontFamily: "var(--font-mono)",
                      marginTop: 1,
                    }}
                  >
                    相似
                  </div>
                </div>
                <Toggle on={c.picked} onChange={() => toggleCompetitor(c.id)} size="sm" />
              </div>
            ))}
            <button
              type="button"
              style={{
                padding: "8px 12px",
                background: "transparent",
                border: "1px dashed var(--mly-ink-300)",
                borderRadius: 6,
                cursor: "pointer",
                color: "var(--mly-ink-600)",
                fontSize: 12,
                fontWeight: 500,
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 6,
              }}
            >
              <Icon name="add" size={14} /> 新增競品
            </button>
          </div>
        </Card>
      </div>

      {/* Bottom callout */}
      <div
        style={{
          marginTop: 16,
          padding: 16,
          borderRadius: 10,
          background: "var(--mly-teal-050)",
          border: "1px solid var(--mly-teal-100)",
          display: "grid",
          gridTemplateColumns: "auto 1fr auto",
          gap: 16,
          alignItems: "center",
        }}
      >
        <Icon name="auto_awesome" size={22} color="var(--mly-teal-700)" />
        <div style={{ fontSize: 13, color: "var(--mly-ink-800)", lineHeight: 1.55 }}>
          <strong style={{ color: "var(--mly-ink-900)" }}>下一步：</strong>
          Cortex 用這份資料分析你的
          <strong style={{ color: "var(--mly-teal-700)" }}>媒體網絡</strong>與
          <strong style={{ color: "var(--mly-teal-700)" }}>本週讀者問題</strong>。
          之後仍可從設定隨時調整。
        </div>
        <OnbButton variant="primary" size="md" iconRight="arrow_forward" onClick={onConfirm}>
          確認並繼續
        </OnbButton>
      </div>
    </div>
  );
}
