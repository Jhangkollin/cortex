interface SectionTitleProps {
  num: number;
  title: string;
  en: string;
  sub?: string;
}

/**
 * Section eyebrow + H2 used at the top of every interior page. Light Edition:
 * gold mono eyebrow (ceremony accent), paper-ink serif-display title, muted
 * subtitle in paper-ink-2. Underline rule is paper-border (NOT teal) so it
 * reads as quiet paper trim instead of a brand stripe.
 */
export function SectionTitle({ num, title, en, sub }: SectionTitleProps) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 10,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          color: "var(--mly-teal-400)",
          fontWeight: 700,
        }}
      >
        {String(num).padStart(2, "0")} · {en}
      </div>
      <div
        style={{
          fontSize: 30,
          fontWeight: 800,
          color: "var(--paper-ink)",
          letterSpacing: "-0.02em",
          marginTop: 4,
          lineHeight: 1.1,
        }}
      >
        {title}
      </div>
      {sub ? (
        <div
          style={{
            fontSize: 12,
            color: "var(--paper-ink-2)",
            marginTop: 6,
            maxWidth: 560,
          }}
        >
          {sub}
        </div>
      ) : null}
    </div>
  );
}
