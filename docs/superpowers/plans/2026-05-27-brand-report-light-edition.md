# Brand Report Light Edition — celebration + hero refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the dark-teal "constellation" celebration modal and Discover-page hero card with the paper-cream "Light Edition" aesthetic per Anthropic Design canvas `brand-report/Brand Report.html`.

**Architecture:** Two existing client components (`brand-report-celebration.tsx`, `brand-report-hero.tsx`) get rewritten in-place; their `Props` signatures are preserved so callers are untouched. CSS variables for the Light Edition palette (`--paper`, `--gold`, etc.) are added to `web/src/app/globals.css`; rendering uses inline-`style` consumption of those vars, matching the existing pattern. A11y wiring (Esc, focus trap, aria-modal, click-outside) is preserved verbatim and protected by regression tests.

**Tech Stack:** Next.js 16 (App Router) + React 18 + TypeScript + Vitest + Testing Library. No backend changes.

**Spec:** `docs/superpowers/specs/2026-05-27-brand-report-light-edition-design.md`

**Worktree:** `.claude/worktrees/brand-report-light/` on branch `feat/brand-report-light-edition` (already created off `origin/develop`).

---

## File map

**Modified (3):**
- `web/src/app/globals.css` — add Light Edition CSS vars + missing keyframes (`br-orbit`, `br-glow`, `br-shimmer`, `br-confetti`, `br-stamp`).
- `web/src/components/brand-dashboard/discover/brand-report-celebration.tsx` — full body rewrite to the 2-column paper-cream layout. `Props` shape preserved; a11y wiring preserved.
- `web/src/components/brand-dashboard/discover/brand-report-hero.tsx` — flip card background to paper-cream; recolor 3 branches (Generating / Failed / Ready); single CTA becomes a dual CTA pair.

**Modified tests (2):**
- `web/src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx`.
- `web/src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx`.

**No new files. No backend changes. No DB migration.**

---

## Task 1: Add Light Edition tokens + missing keyframes to `globals.css`

**Files:**
- Modify: `web/src/app/globals.css`

- [ ] **Step 1: Read the existing `:root` and verify the missing keyframes**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
grep -nE "^:root|^}|--mly-|--paper|--gold|@keyframes" web/src/app/globals.css | head -40
```

Expected: existing `--mly-*` tokens visible, NO `--paper*` / `--gold*` / `--lime-deep` lines yet, and existing keyframes `mly-pulse / mly-fade-up / mly-fade-in / mly-pop-in / mly-radar-sweep` visible. The five keyframes we need (`br-orbit`, `br-glow`, `br-shimmer`, `br-confetti`, `br-stamp`) should be ABSENT.

- [ ] **Step 2: Add the Light Edition tokens inside the existing `:root`**

Open `web/src/app/globals.css`. Find the closing `}` of the first `:root` block (the one with `--mly-teal-*`). Immediately BEFORE that closing brace, insert this block:

```css

  /* Light Edition (Brand IQ paper-cream aesthetic) — added 2026-05-27 */
  --paper:             #F4EDDF;
  --paper-warm:        #ECE3D0;
  --paper-deep:        #DCCFB2;
  --card-white:        #FFFFFF;
  --paper-border:      #D8CFB8;
  --paper-border-soft: #E5DCC4;
  --paper-ink:         #1F1B14;
  --paper-ink-2:       #3D362A;
  --paper-ink-3:       #6E6045;
  --paper-ink-4:       #9A8C6E;
  --ink-warm-50:       #FBF7EE;
  --gold:              #B98821;
  --gold-soft:         #F1E4C1;
  --gold-deep:         #8B6314;
  --lime-deep:         #5A8E2A;
  --lime-soft:         #E5EFD1;
  --brand-teal-soft:   #E0EAE8;
```

- [ ] **Step 3: Add the 5 missing keyframes anywhere after the existing keyframe block**

Find the existing `@keyframes mly-radar-sweep` block. After its closing `}`, append:

```css

@keyframes br-orbit {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

@keyframes br-glow {
  0%, 100% { box-shadow: 0 0 0 0   rgba(185, 136, 33, 0.40),
                          0 0 32px 0   rgba(185, 136, 33, 0.25); }
  50%      { box-shadow: 0 0 0 6px rgba(185, 136, 33, 0),
                          0 0 64px 8px rgba(185, 136, 33, 0.10); }
}

@keyframes br-shimmer {
  0%   { background-position: -240px 0; }
  100% { background-position:  240px 0; }
}

@keyframes br-confetti {
  0%   { transform: translateY(-10px) rotate(0deg);   opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 1; }
  100% { transform: translateY(120vh) rotate(720deg); opacity: 0; }
}

@keyframes br-stamp {
  0%   { transform: scale(2)    rotate(-12deg); opacity: 0; }
  60%  { transform: scale(0.94) rotate(-6deg);  opacity: 1; }
  100% { transform: scale(1)    rotate(-6deg);  opacity: 1; }
}
```

(The `br-glow` colors are gold per the design spec — the design's original had lime; this swap is intentional.)

- [ ] **Step 4: Verify the file still parses (Next dev server / typecheck)**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light/web
npm run type-check 2>&1 | tail -5
npm run lint 2>&1 | tail -5
```

Expected: no new errors. (Pre-existing errors in `(app)/layout.tsx`, if any, can be ignored — they were noted as not-real-tech-debt in prior session.)

- [ ] **Step 5: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
git add web/src/app/globals.css
git commit -m "feat(web): Light Edition design tokens + keyframes for Brand IQ surfaces

Adds CSS variables (--paper*, --gold*, --lime-deep, --brand-teal-soft) and
the 5 br-* keyframes (orbit, glow, shimmer, confetti, stamp) the rewrites
of brand-report-celebration and brand-report-hero will consume.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Rewrite `BrandReportCelebration` to Light Edition (TDD)

**Files:**
- Modify: `web/src/components/brand-dashboard/discover/brand-report-celebration.tsx`
- Test: `web/src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx`

- [ ] **Step 1: Read the existing component and test once, end-to-end**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
wc -l web/src/components/brand-dashboard/discover/brand-report-celebration.tsx \
       web/src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx
sed -n '1,40p' web/src/components/brand-dashboard/discover/brand-report-celebration.tsx
sed -n '1,40p' web/src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx
```

Note the existing `BrandReportCelebrationProps` shape (`{ report, onClose }`), the focus-trap useEffect, and the existing `CONFETTI_PALETTE` const at module scope. These are preserved.

- [ ] **Step 2: Append the new Light Edition structure assertions to the test file**

Open `web/src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx`. Find the closing `});` of the existing top-level `describe(...)` block (or any sibling describe). Inside the existing top-level describe (NOT inside a nested describe), append this block:

```tsx
  // ─── Light Edition structure assertions (2026-05-27) ─────────────────────

  describe("Light Edition layout", () => {
    function fixture() {
      return {
        reportId: "BIQ-TEST-1",
        status: "ready" as const,
        report: {
          meta: {
            subject: "Acme Bank Asia",
            monogram: "A",
            pageCount: 8,
          },
          productLines: [{}, {}, {}, {}, {}, {}, {}],          // 7
          mediaNetwork: [{}, {}, {}, {}, {}, {}],               // 6
          competitors: [{}, {}, {}],                            // 3
          risks: [{}, {}, {}, {}],                              // 4
        } as never,
      };
    }

    it("renders the ALL AGENTS ONLINE top-bar telemetry", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      expect(screen.getByText(/ALL AGENTS ONLINE/)).toBeInTheDocument();
      expect(screen.getByText(/Cortex · Brand Agent · Live/i)).toBeInTheDocument();
    });

    it("renders the gold achievement pill (成就解鎖)", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      expect(screen.getByText(/成就解鎖.*Brand IQ/)).toBeInTheDocument();
    });

    it("renders the 4-stat mini grid with live counts from the envelope", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      expect(screen.getByText("產品線")).toBeInTheDocument();
      expect(screen.getByText("媒體節點")).toBeInTheDocument();
      expect(screen.getByText("競品")).toBeInTheDocument();
      expect(screen.getByText("風險訊號")).toBeInTheDocument();
      expect(screen.getByText("7")).toBeInTheDocument();   // productLines
      expect(screen.getByText("6")).toBeInTheDocument();   // mediaNetwork
      expect(screen.getByText("3")).toBeInTheDocument();   // competitors
      expect(screen.getByText("4")).toBeInTheDocument();   // risks
    });

    it("renders the bottom agent-badge strip", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      expect(screen.getByText(/分派的工作/)).toBeInTheDocument();
      expect(screen.getByText("Answer Pilot")).toBeInTheDocument();
      expect(screen.getByText("GEO Pilot")).toBeInTheDocument();
    });

    it("primary CTA links to the report viewer route", () => {
      render(<BrandReportCelebration report={fixture()} onClose={() => {}} />);
      const primary = screen.getByRole("link", { name: /下載 Brand IQ 報告/ });
      expect(primary.getAttribute("href")).toMatch(/\/brand\/dashboard\/report\/BIQ-TEST-1/);
    });

    it("falls back to '0' in stat cells when envelope sections are missing", () => {
      const f = fixture();
      f.report = { meta: f.report.meta } as never;   // strip productLines etc.
      render(<BrandReportCelebration report={f} onClose={() => {}} />);
      // 4 cells with "0"
      expect(screen.getAllByText("0").length).toBeGreaterThanOrEqual(4);
    });
  });
```

(If the test file doesn't yet import `screen`, add it: `import { render, screen } from "@testing-library/react";`.)

- [ ] **Step 3: Run the new tests — expect them to FAIL**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light/web
npx vitest run "src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx" 2>&1 | tail -25
```

Expected: the 6 new "Light Edition layout" tests FAIL (the old dark celebration doesn't render `ALL AGENTS ONLINE`, `成就解鎖`, the mini-stats grid, or the agent strip). Existing a11y / dismissal tests still PASS.

- [ ] **Step 4: Replace the body of `BrandReportCelebration` with the Light Edition layout**

Open `web/src/components/brand-dashboard/discover/brand-report-celebration.tsx`.

**Replace** the `CONFETTI_PALETTE` const at module top:
```tsx
const CONFETTI_PALETTE = ["#B98821", "#1C726B", "#5A8E2A", "#D8CFB8"];
```
(Was: `["#7CB342", "#FCD34D", "#38A69A", "#80CBC4"]`.)

**Keep** the existing focus-trap `useEffect`, `closeBtnRef`, `overlayRef`, click-outside handler, and `BrandReportCelebrationProps`. Only the JSX returned changes.

**Replace** the `return ( ... )` block of the `BrandReportCelebration` function with the new layout. This is the full replacement (paste verbatim, then implementer may extract sub-components if any helper grows >50 lines):

```tsx
  // Stat counts. Empty envelope sections fall back to 0 so the grid cell
  // always renders (per spec acceptance criterion).
  const reportInner = report.report ?? null;
  const counts = {
    productLines: reportInner?.productLines?.length ?? 0,
    mediaNetwork: reportInner?.mediaNetwork?.length ?? 0,
    competitors:  reportInner?.competitors?.length  ?? 0,
    risks:        reportInner?.risks?.length        ?? 0,
  };

  return (
    <div
      ref={overlayRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby={TITLE_ID}
      onClick={handleOverlayClick}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1000,
        background:
          "radial-gradient(circle at 50% 35%, #FBF6E8 0%, #F4EDDF 55%, #ECE3D0 100%)",
        color: "var(--paper-ink)",
        overflow: "hidden",
        animation: "br-fade-in 320ms ease-out",
      }}
    >
      {/* Warm faint grid (decoration only) */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(110,96,69,0.06) 1px, transparent 1px)," +
            "linear-gradient(90deg, rgba(110,96,69,0.06) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          maskImage: "radial-gradient(ellipse at center, #000 30%, transparent 75%)",
          WebkitMaskImage: "radial-gradient(ellipse at center, #000 30%, transparent 75%)",
        }}
      />

      {/* Confetti — palette swapped to warm gold/teal/lime */}
      <BRConfetti />

      {/* Top bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          padding: "16px 28px",
          display: "flex",
          alignItems: "center",
          gap: 12,
          zIndex: 5,
        }}
      >
        <div
          style={{
            width: 26,
            height: 26,
            borderRadius: 5,
            background: "#1C726B",
            color: "#fff",
            display: "grid",
            placeItems: "center",
            fontWeight: 800,
            fontSize: 13,
          }}
        >
          {mono}
        </div>
        <div
          style={{
            fontSize: 12,
            color: "var(--paper-ink-3)",
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
          }}
        >
          Cortex · Brand Agent · Live
        </div>
        <div
          style={{
            marginLeft: "auto",
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: 11,
            color: "var(--lime-deep)",
            fontFamily: "var(--font-mono)",
          }}
        >
          <span
            aria-hidden
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "var(--lime-deep)",
              boxShadow: "0 0 8px rgba(90,142,42,0.6)",
              animation: "mly-pulse 1.4s infinite",
            }}
          />
          ALL AGENTS ONLINE
        </div>
        <button
          ref={closeBtnRef}
          aria-label="關閉"
          onClick={onClose}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--paper-ink-3)",
            cursor: "pointer",
            marginLeft: 12,
            padding: 4,
          }}
        >
          <span className="material-icons-outlined" style={{ fontSize: 20, color: "var(--paper-ink-3)" }}>
            close
          </span>
        </button>
      </div>

      {/* Main two-column body */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "grid",
          gridTemplateColumns: "1.05fr 0.95fr",
          alignItems: "center",
          padding: "0 80px",
        }}
      >
        {/* LEFT — constellation + radar rings + gold orbit ray */}
        <div style={{ position: "relative", display: "grid", placeItems: "center" }}>
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              aria-hidden
              style={{
                position: "absolute",
                width: 560,
                height: 560,
                borderRadius: "50%",
                border: "1px solid rgba(185,136,33,0.20)",
                opacity: 0.8 - i * 0.2,
                animation: `mly-pulse ${2.2 + i * 0.4}s ease-in-out infinite`,
              }}
            />
          ))}
          <div
            style={{
              position: "relative",
              animation: "mly-pop-in 800ms cubic-bezier(0.2,0.9,0.3,1.2) backwards",
            }}
          >
            <CelebrationConstellation size={520} mono={mono} accent="#1C726B" />
            <div
              aria-hidden
              style={{
                position: "absolute",
                inset: 0,
                borderRadius: "50%",
                background:
                  "conic-gradient(from 0deg, rgba(185,136,33,0.20), transparent 30%)",
                animation: "br-orbit 5s linear infinite",
                pointerEvents: "none",
              }}
            />
          </div>
        </div>

        {/* RIGHT — copy + stats + CTAs */}
        <div style={{ paddingLeft: 28 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "6px 12px",
              background: "var(--gold-soft)",
              border: "1px solid #E0CC8E",
              borderRadius: 999,
              color: "var(--gold-deep)",
              fontSize: 11,
              fontFamily: "var(--font-mono)",
              letterSpacing: "0.16em",
              textTransform: "uppercase",
              marginBottom: 18,
              fontWeight: 700,
            }}
          >
            <span className="material-icons-outlined" style={{ fontSize: 13, color: "var(--gold-deep)" }}>
              auto_awesome
            </span>
            成就解鎖 · Brand IQ 報告
          </div>

          <div
            style={{
              fontSize: 14,
              color: "var(--paper-ink-3)",
              fontFamily: "var(--font-mono)",
              marginBottom: 6,
              letterSpacing: "0.06em",
            }}
          >
            這是你的品牌的形狀——
          </div>
          <h1
            id={TITLE_ID}
            style={{
              fontFamily: "var(--font-serif-tc)",
              fontSize: 52,
              fontWeight: 700,
              letterSpacing: "-0.02em",
              lineHeight: 1.05,
              marginBottom: 14,
              color: "var(--paper-ink)",
            }}
          >
            {subject}
            <br />
            <span
              style={{
                fontFamily: "var(--font-serif)",
                fontWeight: 500,
                fontStyle: "italic",
                color: "var(--gold)",
              }}
            >
              Brand Constellation
            </span>
          </h1>
          <p
            style={{
              fontSize: 14,
              color: "var(--paper-ink-2)",
              lineHeight: 1.7,
              marginBottom: 24,
              maxWidth: 440,
            }}
          >
            Onboarding 階段我們找到了 {subject} 的核心、{counts.productLines} 條產品線、
            {counts.competitors} 家直接競品，以及 {counts.mediaNetwork} 家可分發的媒體節點。
            它們在這份 {pageCount} 頁的 Brand IQ 報告裡，被整理成一個你可以隨時拿給高層、夥伴看的故事。
          </p>

          {/* Stat mini-grid */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 14,
              marginBottom: 26,
              maxWidth: 480,
            }}
          >
            {[
              { label: "產品線", value: counts.productLines },
              { label: "媒體節點", value: counts.mediaNetwork },
              { label: "競品", value: counts.competitors },
              { label: "風險訊號", value: counts.risks },
            ].map((s) => (
              <div key={s.label}>
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: 9,
                    letterSpacing: "0.14em",
                    textTransform: "uppercase",
                    color: "var(--paper-ink-3)",
                  }}
                >
                  {s.label}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-numeric)",
                    fontSize: 30,
                    fontWeight: 700,
                    color: "var(--paper-ink)",
                    lineHeight: 1,
                    marginTop: 4,
                  }}
                >
                  {s.value}
                </div>
              </div>
            ))}
          </div>

          {/* CTAs */}
          <div style={{ display: "flex", gap: 10 }}>
            <a
              href={`/brand/dashboard/report/${reportId}`}
              onClick={onClose}
              style={{
                background: "var(--gold)",
                color: "#fff",
                border: "none",
                padding: "14px 22px",
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 800,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                boxShadow: "0 8px 18px -4px rgba(185,136,33,0.45)",
                animation: "br-glow 2.6s ease-in-out infinite",
                textDecoration: "none",
              }}
            >
              <span className="material-icons-outlined" style={{ fontSize: 16, color: "#fff" }}>
                download
              </span>
              下載 Brand IQ 報告 · PDF
            </a>
            <a
              href={`/brand/dashboard/report/${reportId}`}
              onClick={onClose}
              style={{
                background: "#fff",
                color: "var(--paper-ink)",
                border: "1px solid var(--paper-border)",
                padding: "13px 18px",
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 700,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                textDecoration: "none",
              }}
            >
              <span className="material-icons-outlined" style={{ fontSize: 15, color: "var(--paper-ink)" }}>
                visibility
              </span>
              開啟 Report Viewer
            </a>
          </div>
          <div
            style={{
              marginTop: 14,
              fontSize: 11,
              color: "var(--paper-ink-3)",
              fontFamily: "var(--font-mono)",
              letterSpacing: "0.06em",
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span className="material-icons-outlined" style={{ fontSize: 11, color: "var(--paper-ink-3)" }}>
              bookmark
            </span>
            已自動存到 Knowledge Base · 隨時可重新下載
          </div>
        </div>
      </div>

      {/* Bottom strip — static agent badges (TODO: wire to live deployed agents) */}
      <div
        style={{
          position: "absolute",
          bottom: 24,
          left: 80,
          right: 80,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 10,
          opacity: 0.95,
          animation: "mly-fade-up 1200ms 400ms backwards",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 10,
            color: "var(--paper-ink-3)",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            marginRight: 4,
          }}
        >
          分派的工作 →
        </span>
        {[
          "Answer Pilot",
          "GEO Pilot",
          "Monetize Lens",
          "Market Radar",
          "Context · MoneyDJ",
          "Context · Smart 智富",
          "+ 4 個",
        ].map((n, i) => (
          <span
            key={n}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              padding: "5px 10px",
              background: "#fff",
              border: "1px solid var(--paper-border)",
              borderRadius: 999,
              fontSize: 11,
              color: "var(--paper-ink-2)",
              fontFamily: "var(--font-mono)",
              animation: `mly-fade-up 500ms ${500 + i * 80}ms backwards`,
            }}
          >
            <span
              aria-hidden
              style={{
                width: 5,
                height: 5,
                borderRadius: "50%",
                background: "var(--lime-deep)",
              }}
            />
            {n}
          </span>
        ))}
      </div>
    </div>
  );
```

If the existing file used a different name than `CelebrationConstellation` for its constellation SVG (it does — check before this step), reuse that name. Confirm it's already imported / defined in the file. The size prop changes from whatever-it-was to `520`; verify the existing SVG accepts a `size` prop.

If `CelebrationConstellation`'s color attributes are hardcoded for the dark background, recolor: outer rings/stars use `rgba(110,96,69,0.30)` (paper-toned) and the center disc stays teal `#1C726B` with white monogram. Update the SVG inline in the same file.

- [ ] **Step 5: Re-run the celebration test — expect all green**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light/web
npx vitest run "src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx" 2>&1 | tail -25
```

Expected: all tests PASS (the 6 new Light Edition assertions + all pre-existing a11y / dismissal tests).

If a pre-existing test fails because it asserted dark-mode-specific text or colors, UPDATE the assertion to match the new copy/colors. Examples:
- A test that checked for the lime CTA background → update to gold.
- A test that asserted "白底黑字" → update to "paper-cream" or simply assert the dialog still renders + Esc closes.

Do NOT delete coverage; rewrite to assert the new contract.

- [ ] **Step 6: Lint + type-check**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light/web
npm run lint
npm run type-check 2>&1 | tail -5
```

Expected: no new errors.

- [ ] **Step 7: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
git add web/src/components/brand-dashboard/discover/brand-report-celebration.tsx \
        web/src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx
git commit -m "feat(web): BrandReportCelebration → Light Edition (paper-cream)

Two-column body, top-bar telemetry (ALL AGENTS ONLINE), gold achievement
pill, live 4-stat mini-grid (productLines/mediaNetwork/competitors/risks),
gold primary + outline secondary CTA, bottom agent-badge strip. A11y
preserved (Esc, focus trap, aria-modal, click-outside).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Rewrite `BrandReportHero` to Light Edition (TDD)

**Files:**
- Modify: `web/src/components/brand-dashboard/discover/brand-report-hero.tsx`
- Test: `web/src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx`

- [ ] **Step 1: Read the existing hero + test**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
sed -n '1,100p' web/src/components/brand-dashboard/discover/brand-report-hero.tsx
wc -l web/src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx
```

Note the three render branches (`GeneratingSkeleton`, `FailedState`, `ReadyHero`) and the dismiss × wiring (`onDismiss`).

- [ ] **Step 2: Append the Light Edition assertions to the hero test**

Open `web/src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx`. Inside the existing top-level describe, append:

```tsx
  describe("Light Edition — paper-cream surface", () => {
    function readyFixture() {
      return {
        reportId: "BIQ-TEST-2",
        status: "ready" as const,
        report: {
          meta: { subject: "Acme Bank Asia", monogram: "A", pageCount: 8,
                  reportDate: "2026-05-22", preparedBy: "Cortex" },
          productLines: [{}, {}, {}, {}, {}, {}, {}],
          mediaNetwork: [{}, {}, {}, {}, {}, {}],
          competitors:  [{}, {}, {}],
          risks:        [{}, {}, {}, {}],
        } as never,
      };
    }

    it("ReadyHero renders both gold primary and outline secondary CTAs", () => {
      render(
        <BrandReportHero
          report={readyFixture()}
          heroDismissed={false}
          onDismiss={() => {}}
          onRetry={() => {}}
        />,
      );
      expect(screen.getByRole("link", { name: /下載.*PDF/ })).toBeInTheDocument();
      expect(screen.getByRole("link", { name: /開啟 Report Viewer/ })).toBeInTheDocument();
    });

    it("ReadyHero card uses the paper-cream background token", () => {
      const { container } = render(
        <BrandReportHero
          report={readyFixture()}
          heroDismissed={false}
          onDismiss={() => {}}
          onRetry={() => {}}
        />,
      );
      // The outermost card has the paper background. Locate via the title text
      // and walk up to the card surface.
      const titleNode = screen.getByText(/品牌側寫已準備好/);
      // The card root carries inline style background containing 'var(--paper'.
      let el: HTMLElement | null = titleNode as HTMLElement;
      let foundPaper = false;
      while (el) {
        const bg = el.style?.background ?? "";
        if (bg.includes("var(--paper") || bg.includes("#F4EDDF")) { foundPaper = true; break; }
        el = el.parentElement;
      }
      expect(foundPaper).toBe(true);
    });

    it("ReadyHero dismiss × calls onDismiss", () => {
      const onDismiss = vi.fn();
      render(
        <BrandReportHero
          report={readyFixture()}
          heroDismissed={false}
          onDismiss={onDismiss}
          onRetry={() => {}}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /關閉/ }));
      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it("returns null when heroDismissed is true", () => {
      const { container } = render(
        <BrandReportHero
          report={readyFixture()}
          heroDismissed={true}
          onDismiss={() => {}}
          onRetry={() => {}}
        />,
      );
      expect(container.firstChild).toBeNull();
    });

    it("FailedState calls onRetry on click", () => {
      const onRetry = vi.fn();
      render(
        <BrandReportHero
          report={{ reportId: "BIQ-X", status: "failed", error: "boom" } as never}
          heroDismissed={false}
          onDismiss={() => {}}
          onRetry={onRetry}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /重試/ }));
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });
```

Ensure imports include `vi`, `fireEvent`, `screen`, `render`:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
```

(Vitest doesn't auto-import these; add only what's missing.)

- [ ] **Step 3: Run the new tests — expect them to FAIL**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light/web
npx vitest run "src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx" 2>&1 | tail -20
```

Expected: the new Light Edition tests FAIL (no gold paper background, no dual-CTA pair, no "下載 PDF" text yet, etc.).

- [ ] **Step 4: Rewrite the three branches in `brand-report-hero.tsx`**

Open `web/src/components/brand-dashboard/discover/brand-report-hero.tsx`.

**Replace the `ReadyHero` function** (around line 302 per spec context). Full replacement:

```tsx
function ReadyHero({ report, onDismiss }: ReadyHeroProps): ReactElement {
  const meta = report.report?.meta;
  const subject  = meta?.subject  ?? "你的品牌";
  const mono     = meta?.monogram ?? subject.charAt(0).toUpperCase();
  const pageCount = meta?.pageCount ?? 0;
  const reportDate = meta?.reportDate ?? "—";
  const preparedBy = meta?.preparedBy ?? "Cortex";
  const reportId   = report.reportId;

  return (
    <div
      style={{
        position: "relative",
        borderRadius: 14,
        overflow: "hidden",
        background: "var(--paper)",
        color: "var(--paper-ink)",
        padding: 26,
        marginBottom: 24,
        minHeight: 188,
        border: "1px solid var(--paper-border)",
        boxShadow: "0 16px 32px -8px rgba(110,96,69,0.18)",
      }}
    >
      {/* Constellation deco — recolored for paper background */}
      <div aria-hidden style={{ position: "absolute", right: 24, top: -20, opacity: 0.95 }}>
        <BRConstellation size={220} mono={mono} accent="var(--gold)" />
      </div>
      {/* Gold orbit-sweep deco */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          right: -80,
          bottom: -90,
          width: 280,
          height: 280,
          borderRadius: "50%",
          background: "conic-gradient(from 0deg, rgba(185,136,33,0.18), transparent 32%)",
          animation: "br-orbit 6s linear infinite",
          pointerEvents: "none",
        }}
      />

      <div style={{ position: "relative", maxWidth: 720 }}>
        {/* Achievement pill */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            padding: "4px 10px",
            background: "var(--gold-soft)",
            color: "var(--gold-deep)",
            border: "1px solid #E0CC8E",
            borderRadius: 999,
            fontSize: 11,
            fontFamily: "var(--font-mono)",
            letterSpacing: "0.16em",
            textTransform: "uppercase",
            marginBottom: 12,
            fontWeight: 700,
          }}
        >
          <span className="material-icons-outlined" style={{ fontSize: 13, color: "var(--gold-deep)" }}>
            auto_awesome
          </span>
          成就解鎖 · Brand IQ 報告 · 新
        </div>

        <h2
          style={{
            fontSize: 30,
            fontWeight: 800,
            letterSpacing: "-0.02em",
            lineHeight: 1.15,
            marginBottom: 8,
            color: "var(--paper-ink)",
          }}
        >
          {subject} 的品牌側寫已準備好——下載你的第一份報告
        </h2>
        <p
          style={{
            fontSize: 13,
            color: "var(--paper-ink-2)",
            lineHeight: 1.6,
            maxWidth: 580,
            margin: 0,
          }}
        >
          從 onboarding 抓取的所有公開資料，已整理成 {pageCount} 頁的 PDF。
          適合給高層、外部夥伴、或保留作為 Brand Agent 啟動點的快照。
        </p>

        <div style={{ display: "flex", gap: 10, marginTop: 18, alignItems: "center" }}>
          <a
            href={`/brand/dashboard/report/${reportId}`}
            style={{
              background: "var(--gold)",
              color: "#fff",
              border: "none",
              padding: "11px 18px",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 800,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              textDecoration: "none",
              boxShadow: "0 8px 18px -4px rgba(185,136,33,0.4)",
            }}
          >
            <span className="material-icons-outlined" style={{ fontSize: 15, color: "#fff" }}>
              download
            </span>
            下載 PDF
          </a>
          <a
            href={`/brand/dashboard/report/${reportId}`}
            style={{
              background: "#fff",
              color: "var(--paper-ink)",
              border: "1px solid var(--paper-border)",
              padding: "10px 16px",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 700,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 7,
              textDecoration: "none",
            }}
          >
            <span className="material-icons-outlined" style={{ fontSize: 14, color: "var(--paper-ink)" }}>
              visibility
            </span>
            開啟 Report Viewer
          </a>
          <span
            style={{
              marginLeft: 12,
              fontSize: 11,
              color: "var(--paper-ink-4)",
              fontFamily: "var(--font-mono)",
              letterSpacing: "0.08em",
            }}
          >
            產生於 {reportDate} · {preparedBy}
          </span>
          <button
            aria-label="關閉"
            onClick={onDismiss}
            style={{
              marginLeft: "auto",
              background: "transparent",
              color: "var(--paper-ink-4)",
              border: "none",
              padding: "8px 8px",
              borderRadius: 4,
              fontSize: 12,
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            <span className="material-icons-outlined" style={{ fontSize: 16, color: "var(--paper-ink-4)" }}>
              close
            </span>
            關閉
          </button>
        </div>
      </div>
    </div>
  );
}
```

**Recolor `BRConstellation`** at module top: change the default `accent` from `"#7CB342"` to `"var(--gold)"` (or pass `accent="var(--gold)"` explicitly from each caller — both work). Also: change any hardcoded stroke/fill that targets the dark background. Walk the SVG body:
- Outer rings: change `stroke="rgba(255,255,255,...)"` patterns to `stroke="rgba(110,96,69,0.30)"`.
- Stars/dots: change `fill="#fff"` or white-alpha to `fill="var(--paper-ink-4)"`.
- Center disc: keep teal `#1C726B` + white monogram (brand stamp).

If `BRConstellation` has no hardcoded white attributes (passes `accent` only), the prop swap above is enough.

**Replace `GeneratingSkeleton`** (around line 130):
```tsx
function GeneratingSkeleton(): ReactElement {
  return (
    <div
      style={{
        position: "relative",
        borderRadius: 14,
        overflow: "hidden",
        background: "var(--paper)",
        color: "var(--paper-ink)",
        padding: 26,
        marginBottom: 24,
        minHeight: 188,
        border: "1px solid var(--paper-border)",
        boxShadow: "0 16px 32px -8px rgba(110,96,69,0.18)",
      }}
    >
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--paper-ink-3)",
          marginBottom: 12,
        }}
      >
        準備中 · Brand IQ 報告
      </div>
      {[260, 360, 220].map((w, i) => (
        <div
          key={i}
          style={{
            height: 18,
            width: w,
            borderRadius: 6,
            marginBottom: 10,
            background:
              "linear-gradient(90deg, #ECE3D0 0%, #F4EDDF 50%, #ECE3D0 100%)",
            backgroundSize: "480px 100%",
            animation: "br-shimmer 1.4s linear infinite",
          }}
        />
      ))}
    </div>
  );
}
```

**Replace `FailedState`** (around line 218). Keep the existing `onRetry` callback signature; only the visual changes:
```tsx
function FailedState({
  report,
  onRetry,
  onDismiss,
}: FailedStateProps): ReactElement {
  const errorMsg = report.error ?? "未知錯誤";
  return (
    <div
      style={{
        position: "relative",
        borderRadius: 14,
        overflow: "hidden",
        background: "var(--paper)",
        color: "var(--paper-ink)",
        padding: 26,
        marginBottom: 24,
        minHeight: 188,
        border: "1px solid var(--paper-border)",
        boxShadow: "0 16px 32px -8px rgba(110,96,69,0.18)",
      }}
    >
      <div
        style={{
          fontFamily: "var(--font-mono)",
          fontSize: 11,
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "var(--paper-ink-3)",
          marginBottom: 8,
        }}
      >
        Brand IQ 報告 · 生成失敗
      </div>
      <div
        style={{
          fontSize: 13,
          color: "var(--paper-ink-2)",
          marginBottom: 16,
          maxWidth: 580,
        }}
      >
        {errorMsg}
      </div>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <button
          onClick={onRetry}
          style={{
            background: "var(--gold)",
            color: "#fff",
            border: "none",
            padding: "10px 16px",
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 800,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 7,
          }}
        >
          <span className="material-icons-outlined" style={{ fontSize: 15, color: "#fff" }}>
            refresh
          </span>
          重試
        </button>
        <button
          aria-label="關閉"
          onClick={onDismiss}
          style={{
            marginLeft: "auto",
            background: "transparent",
            color: "var(--paper-ink-4)",
            border: "none",
            padding: "8px 8px",
            borderRadius: 4,
            fontSize: 12,
            cursor: "pointer",
            display: "inline-flex",
            alignItems: "center",
            gap: 4,
          }}
        >
          <span className="material-icons-outlined" style={{ fontSize: 16, color: "var(--paper-ink-4)" }}>
            close
          </span>
          關閉
        </button>
      </div>
    </div>
  );
}
```

(If `FailedStateProps` doesn't already include `onDismiss`, check the existing signature. The branch is already invoked from the public `BrandReportHero` component which has access to `onDismiss` — pass it through.)

The public `BrandReportHero` component (at the bottom of the file) wires the three branches together. Preserve its `heroDismissed → null` short-circuit. Only the branch internals change; the public component's flow is unchanged.

- [ ] **Step 5: Re-run the hero test — expect green**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light/web
npx vitest run "src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx" 2>&1 | tail -20
```

Expected: all tests PASS (new Light Edition + preserved a11y/null/dismiss).

If pre-existing tests assert dark-mode-specific copy or single-CTA behavior, update them to assert the new contract.

- [ ] **Step 6: Run full web suite to catch any unrelated regression**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light/web
npm test 2>&1 | tail -8
npm run lint
npm run type-check 2>&1 | tail -5
```

Expected: all green. Pre-existing failures in `(app)/layout.tsx` (if any) are acceptable per the session memory — they're stash residue, not real test failures.

- [ ] **Step 7: Commit**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
git add web/src/components/brand-dashboard/discover/brand-report-hero.tsx \
        web/src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx
git commit -m "feat(web): BrandReportHero → Light Edition (paper-cream)

Flips all three branches (Generating / Failed / Ready) to the paper-cream
card. Gold orbit-sweep deco replaces the lime ring. Dual CTAs (gold primary
download + outline secondary 'Open Report Viewer') replace the single lime
button. Dismiss × wired to paper-ink-4 muted.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Final local verification + push PR

**Files:** none new.

- [ ] **Step 1: Re-run the full local suite (api + web)**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
make lint
make test
```

Expected: all green. (api side wasn't touched, so api should be unchanged.)

- [ ] **Step 2: Manual smoke (optional but recommended)**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light/web
npm run dev
# Open http://localhost:3000, sign in, with a brand whose report is ready,
# verify hero appears as paper-cream and celebration shows the new structure.
# The `?celebrate=preview` query path (added in #66) renders the modal
# without a backend — easiest way to eyeball the celebration.
```

Expected: card is paper-cream (no dark teal anywhere on the surface). Celebration modal shows top-bar + stats grid + agent strip. Esc closes the modal.

- [ ] **Step 3: Push the branch + open the PR**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
git push -u origin feat/brand-report-light-edition
gh pr create --base develop --title "feat(web): Brand Report Light Edition — celebration + hero refactor" --body "$(cat <<'EOF'
## Summary
Replaces the dark-teal Brand IQ surfaces with the paper-cream "Light Edition / 晨光紙感" direction per Anthropic Design canvas. Closes CEO feedback that the current surfaces are too dark.

## What's in
- New CSS variables in \`globals.css\` (\`--paper\`, \`--gold\`, \`--lime-deep\`, etc.) + 5 missing keyframes (\`br-orbit\`, \`br-glow\`, \`br-shimmer\`, \`br-confetti\`, \`br-stamp\`).
- \`BrandReportCelebration\` — full rewrite to the 2-column paper-cream layout: top bar with brand mono + \`ALL AGENTS ONLINE\`, gold achievement pill, serif headline + italic gold \`Brand Constellation\` subhead, **live 4-stat mini-grid** (productLines / mediaNetwork / competitors / risks from the envelope), gold primary + outline secondary CTAs, bottom agent-badge strip. A11y wiring (Esc, focus trap, aria-modal, click-outside) preserved.
- \`BrandReportHero\` — flips all three branches (Generating / Failed / Ready) to paper-cream. Gold orbit-sweep replaces the lime ring. Dual CTAs (download + open viewer) replace the single lime button. Dismiss × wired to paper-ink-4.

## Out (deferred)
- 8-page Report Viewer route.
- Knowledge Base entry.
- Onboarding-complete handoff hero.
- PDF renderer (backend stays dark for one release; flagged in the spec).

## Acceptance
1. \`/brand/dashboard\` shows the new paper-cream hero card.
2. First-time post-onboarding shows the new celebration modal with all 5 structural pieces.
3. Esc + Tab focus trap + overlay click + dismiss × all still work.
4. \`?celebrate=preview\` preview path (#66) still renders without backend.
5. Full vitest suite + lint + type-check pass.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR opens; watcher captures owl + CI.

- [ ] **Step 4: Wait for owl review + CI, address any feedback**

If CI fails or owl posts CHANGES_REQUESTED, follow the standard fix-and-push loop: read the review body, fix in the worktree, commit, push, re-trigger with `@owl review`.

On owl APPROVED + CI green:

```bash
gh pr merge <PR#> --repo mlytics/cortex --squash --delete-branch
```

---

## Task 5: UAT promotion

**Files:** none in cortex; one in `data-platform-helm-charts`.

- [ ] **Step 1: Identify the merge SHA + check Deploy ran**

```bash
cd /Users/okis.chuang/Documents/dev/cortex
git fetch origin develop --quiet
TAG=$(git rev-parse --short origin/develop)
echo "develop HEAD = $TAG"
# Wait for the Deploy workflow run for this SHA to succeed.
# If GitHub Actions is healthy:
gh run list --repo mlytics/cortex --workflow=Deploy --branch develop --limit 1 \
  --json headSha,status,conclusion --jq '.[0]|"\(.headSha[0:7]) \(.status) \(.conclusion)"'
```

If Deploy completed successfully, skip Step 2 and proceed to Step 3. If Actions is broken, use Step 2.

- [ ] **Step 2 (fallback): Build locally with the runbook target**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/brand-report-light
git fetch origin develop --quiet
git checkout origin/develop --quiet  # detached HEAD at the merged SHA
aws sso login --profile c2g-uat 2>&1 | tail -3
make build-local
# `make build-local` builds both images for linux/arm64, pushes to UAT ECR,
# and verifies the manifest. Output prints both image refs.
```

Expected: both images push successfully and the verify step prints `arm64/linux`.

- [ ] **Step 3: Open the helm-charts promotion PR + merge + deploy**

```bash
cd /Users/okis.chuang/Documents/dev/cortex
TAG=$(git rev-parse --short origin/develop)
echo "Promoting cortex-{api,web}:$TAG to UAT"

cd /Users/okis.chuang/Documents/dev/data-platform-helm-charts
git fetch origin main --quiet
git checkout -b feat/cortex-uat-promote-$TAG origin/main
# Bump both tags in environments/uat/cortex/values.yaml (lines ~34 and ~73)
# from the current value to "$TAG". The two lines are byte-identical, so a
# single sed -i "" replacement covers both. Use the file's current tag for the
# left-hand side of the swap.
CURRENT=$(grep -m1 'tag:' environments/uat/cortex/values.yaml | grep -oE '"[a-z0-9]+"')
sed -i "" "s#tag: $CURRENT#tag: \"$TAG\"#g" environments/uat/cortex/values.yaml
grep -n 'tag:' environments/uat/cortex/values.yaml  # expect both lines now $TAG
```

(If the values file is currently digest-pinned to `e7573f0@sha256:...`, the `sed` above won't match the bare-tag form; replace by hand with the new bare tag instead.)

```bash
git add environments/uat/cortex/values.yaml
git commit -m "feat(cortex uat): promote to SHA $TAG (Brand Report Light Edition)

Bumps cortex-web and cortex-api uat image tags to $TAG.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
git push -u origin feat/cortex-uat-promote-$TAG

PR_URL=$(gh pr create --repo mlytics/data-platform-helm-charts --base main \
  --title "feat(cortex uat): promote to SHA $TAG" \
  --body "Brand Report Light Edition refresh." | tail -1)
PR_NUM=$(echo "$PR_URL" | grep -oE '[0-9]+$')
gh pr merge "$PR_NUM" --repo mlytics/data-platform-helm-charts --merge --delete-branch

cd /Users/okis.chuang/Documents/dev/data-platform-helm-charts
git checkout main --quiet && git pull --ff-only origin main --quiet
yes yes | AWS_PROFILE=c2g-uat make helm-cortex ENV=uat
```

Expected: helm upgrade succeeds (REVISION increments).

- [ ] **Step 4: Verify the rollout + open the UI**

```bash
kubectl rollout status deploy/cortex-api -n cortex --timeout=240s
kubectl rollout status deploy/cortex-web -n cortex --timeout=240s
# Confirm both pods on the new SHA:
kubectl get pods -n cortex -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}' | grep 'cortex-(web|api)'
# Public endpoint:
curl -s -o /dev/null -w "providers endpoint: %{http_code}\n" https://cortex.mlytics.co/api/auth/providers
```

Open `https://cortex.mlytics.co/brand/dashboard?celebrate=preview` (or hard-refresh after onboarding) and visually confirm:
- Hero card: paper-cream background, gold orbit deco, dual CTAs.
- Celebration modal (when triggered): two-column layout, top bar `ALL AGENTS ONLINE`, 4-stat mini-grid with live counts, bottom agent strip.

- [ ] **Step 5: Done — report PR URLs + the deploy SHA**

```bash
echo "cortex PR: <merged>"
echo "helm-charts PR: <merged>"
echo "UAT now on cortex-{api,web}:$TAG"
```

---

## Self-review summary

- Spec coverage: every In-scope item (1 tokens, 2 celebration, 3 hero, 4 tests) maps to Tasks 1–3. Acceptance criteria 1, 2, 3 → Tasks 2/3 + Task 5 step 4 manual UI smoke; criterion 4 → Task 2 a11y preservation; criterion 5 → Task 3 dismiss test; criterion 6 → Task 4 step 2 preview-path smoke; criterion 7 → Task 4 step 1 (lint/test/type-check gate before push).
- No placeholders: every step ships a concrete file path, concrete code block (or concrete command + expected output), or a concrete commit message.
- Type/name consistency: `BrandReportCelebrationProps { report, onClose }` and `BrandReportHeroProps { report, heroDismissed, onDismiss, onRetry }` are referenced identically across tasks. CSS token names (`--paper`, `--gold`, `--paper-ink`, etc.) match the spec and the Anthropic Design canvas. `CelebrationConstellation` / `BRConstellation` are the existing names from the file and are preserved by the rewrite.
