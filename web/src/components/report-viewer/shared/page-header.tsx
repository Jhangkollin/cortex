import { sectionFor } from "../sections";

interface PageHeaderProps {
  /** Page number — running-header section/en strings come from the catalog. */
  page: number;
  subject: string;
}

/**
 * Running header on every interior page. Light Edition: warm-gray mono
 * eyebrow over a paper-border underline. The eyebrow is intentionally muted
 * (paper-ink-3) so it sits behind the section title without competing.
 */
export function PageHeader({ page, subject }: PageHeaderProps) {
  const { sectionLabel, headerEn } = sectionFor(page);
  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 26,
          left: 36,
          right: 36,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: "var(--font-mono)",
          fontSize: 9,
          letterSpacing: "0.2em",
          textTransform: "uppercase",
          color: "var(--paper-ink-3)",
        }}
      >
        <span>
          {sectionLabel} · {headerEn}
        </span>
        <span>
          {subject} · p.{String(page).padStart(2, "0")}
        </span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 36,
          right: 36,
          top: 50,
          height: 1,
          background: "#d5dee0",
        }}
      />
    </>
  );
}
