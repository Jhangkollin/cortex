/**
 * Certainty indicator chip — Light Edition palette per Engineering Handoff
 * §5 (consistency table):
 *   - 已確認  → --brand-teal-soft bg + --mly-teal-700 text + paper-border-soft
 *   - 高可能  → --gold-soft bg + --gold-deep text + --gold-border
 *   - 資料不足 → warm gray (paper-border-soft) bg + --paper-ink-3 text
 */
export type CertaintyValue = "已確認" | "高可能" | "資料不足";

interface CertaintyChipProps {
  value: CertaintyValue | string;
}

export function CertaintyChip({ value }: CertaintyChipProps) {
  const map: Record<string, { bg: string; fg: string; border: string }> = {
    已確認: {
      bg: "var(--brand-teal-soft)",
      fg: "var(--mly-teal-700)",
      border: "var(--brand-teal-soft-border)",
    },
    高可能: {
      bg: "rgb(244, 249, 250)",
      fg: "var(--mly-teal-700)",
      border: "var(--mly-teal-200)",
    },
    資料不足: {
      bg: "#d5dee0",
      fg: "var(--paper-ink-3)",
      border: "#d5dee0",
    },
  };
  const m = map[value] ?? map["資料不足"]!;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 3,
        padding: "2px 7px",
        background: m.bg,
        color: m.fg,
        borderRadius: 3,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: "0.04em",
        border: `1px solid ${m.border}`,
      }}
    >
      {value || "資料不足"}
    </span>
  );
}
