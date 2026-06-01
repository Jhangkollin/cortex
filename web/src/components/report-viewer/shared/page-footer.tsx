import { sectionFor } from "../sections";

interface PageFooterProps {
  /** Page number — footer left string comes from the catalog. */
  page: number;
  pageCount: number;
}

/**
 * Running footer on every interior page. Light Edition: warm-gray mono
 * baseline separated from page content by a paper-border rule.
 */
export function PageFooter({ page, pageCount }: PageFooterProps) {
  const { footerLeft } = sectionFor(page);
  return (
    <div
      style={{
        position: "absolute",
        left: 36,
        right: 36,
        bottom: 30,
        display: "flex",
        justifyContent: "space-between",
        fontFamily: "var(--font-mono)",
        fontSize: 9,
        letterSpacing: "0.22em",
        textTransform: "uppercase",
        color: "var(--paper-ink-3)",
        paddingTop: 12,
        borderTop: "1px solid #d5dee0",
      }}
    >
      <span>{footerLeft}</span>
      <span>Cortex · Brand Intelligence</span>
      <span>
        p.{String(page).padStart(2, "0")} / {pageCount}
      </span>
    </div>
  );
}
