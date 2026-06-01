# Brand Report Light Edition — celebration + hero refactor

> Replaces the dark-teal "constellation" celebration modal and Discover-page hero card with the **"Light Edition / 晨光紙感"** paper-cream aesthetic per Anthropic Design canvas `brand-report/Brand Report.html`. Closes CEO feedback that the current Brand IQ surfaces are "too dark / too heavy". Scope is the two surfaces actually shipped on develop today; the 8-page Report Viewer, Knowledge Base entry, and onboarding-complete handoff are deferred.

## Why this exists

The existing Brand IQ surfaces (`web/src/components/brand-dashboard/discover/brand-report-{hero,celebration}.tsx`) render against a dark teal-to-black radial gradient (`#06181A → #0E2D2C → #144948`) with white text and a lime accent. CEO feedback: "太深太重." The design team's Anthropic Design canvas (`brand-report/Brand Report.html`) ships a chosen redirection — same constellation visual language, but on a warm cream "paper" background with darker warm ink and a gold ceremony accent. This spec ports that direction into cortex/web.

## In scope (this PR)

1. **Token additions** to `web/src/app/globals.css` (CSS variables only — matches the file's existing convention; no Tailwind theme changes).
2. **`BrandReportCelebration` full rewrite** — paper-cream background, two-column body (constellation left + copy right), new top bar, 4-stat mini-grid, two CTAs (gold primary + outline secondary), and a streaming agent-badge bottom strip.
3. **`BrandReportHero` rewrite** — flip card background from dark-teal gradient to paper-cream; recolor constellation deco; replace the single lime CTA with a gold primary + outline secondary pair; preserve Generating-skeleton, Failed-state, and Ready-state branches; recolor each.
4. **Tests** — keep the existing a11y / dismissal coverage green; extend with snapshot/structure assertions for the new pieces (top bar, stats grid, agent strip, gold primary CTA, paper background).

## Out of scope (deferred)

- 8-page Report Viewer route (`/brand/dashboard/report/{reportId}`) and its TOC/chrome.
- Knowledge Base entry route (permanent download surface).
- Onboarding-complete page's hero card (single, lives in `onboarding-v2/step-complete.tsx`).
- PDF renderer (backend `service/brand_report/pdf/*`) — keeps producing the current PDF; PDF visual refresh will be a follow-up.
- Tailwind theme additions (`bg-paper`, `text-gold`, etc.) — existing components consume tokens via inline `style={{ background: "var(--paper)" }}`, and this PR follows that convention; theme tokens can be added later if other dashboard surfaces need them.

## Architecture

### 1. Token additions (`web/src/app/globals.css`)

The Anthropic Design canvas defines a "Light Edition" palette in its `:root`. Mirror it under the existing `:root` block in `web/src/app/globals.css` (alongside `--mly-teal-*`). New variables:

```css
/* Light Edition (Brand IQ paper-cream aesthetic) — added 2026-05-27 */
--paper:           #F4EDDF;
--paper-warm:      #ECE3D0;
--paper-deep:      #DCCFB2;
--card-white:      #FFFFFF;
--paper-border:    #D8CFB8;
--paper-border-soft: #E5DCC4;
--paper-ink:       #1F1B14;
--paper-ink-2:     #3D362A;
--paper-ink-3:     #6E6045;
--paper-ink-4:     #9A8C6E;
--ink-warm-50:     #FBF7EE;
--gold:            #B98821;
--gold-soft:       #F1E4C1;
--gold-deep:       #8B6314;
--lime-deep:       #5A8E2A;
--lime-soft:       #E5EFD1;
--brand-teal-soft: #E0EAE8;
```

Animations needed by the new components: `br-orbit`, `br-glow`, `mly-pop-in`, `mly-pulse`, `mly-fade-up`, `br-shimmer`, `br-confetti`. The existing `globals.css` already defines most (verify during implementation); add only the missing ones. Keyframe definitions are listed verbatim in the design canvas HTML and can be copied.

### 2. `BrandReportCelebration` rewrite

File: `web/src/components/brand-dashboard/discover/brand-report-celebration.tsx`.

**Preserved (DO NOT regress):**
- `BrandReportCelebrationProps { report, onClose }` — unchanged signature.
- `role="dialog" aria-modal="true" aria-labelledby={TITLE_ID}` on the overlay.
- Focus management: `closeBtnRef.current?.focus()` on mount.
- Esc dismisses.
- Tab/Shift-Tab focus trap (loop within the dialog).
- Click on overlay (target === overlayRef.current) dismisses.
- `useEffect` cleanup for the keydown listener.

**Replaced:**

The overlay's `background` flips to a cream radial:
```ts
background: "radial-gradient(circle at 50% 35%, #FBF6E8 0%, #F4EDDF 55%, #ECE3D0 100%)",
color: "var(--paper-ink)",
```

Behind everything, a faint warm grid sits as decoration:
```tsx
<div aria-hidden style={{
  position: "absolute", inset: 0,
  backgroundImage:
    "linear-gradient(rgba(110,96,69,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(110,96,69,0.06) 1px, transparent 1px)",
  backgroundSize: "48px 48px",
  maskImage: "radial-gradient(ellipse at center, #000 30%, transparent 75%)",
}} />
```

The existing `BRConfetti` component is replaced (or recolored — implementer's choice) so its palette becomes `[#B98821, #1C726B, #5A8E2A, #D8CFB8]` (gold + brand-teal + lime-deep + paper-border) instead of lime-only. Density and timing stay the same.

The body is restructured into a top bar + two-column main + bottom strip.

**Top bar** (zIndex 5, absolute top 16/28):
```tsx
<div style={{ position: "absolute", top: 0, left: 0, right: 0, padding: "16px 28px",
              display: "flex", alignItems: "center", gap: 12, zIndex: 5 }}>
  <div style={{ width: 26, height: 26, borderRadius: 5, background: "#1C726B",
                color: "#fff", display: "grid", placeItems: "center",
                fontWeight: 800, fontSize: 13 }}>
    {mono}
  </div>
  <div style={{ fontSize: 12, color: "var(--paper-ink-3)", fontFamily: "var(--font-mono)",
                letterSpacing: "0.14em", textTransform: "uppercase" }}>
    Cortex · Brand Agent · Live
  </div>
  <div style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 6,
                fontSize: 11, color: "var(--lime-deep)", fontFamily: "var(--font-mono)" }}>
    <span style={{ width: 7, height: 7, borderRadius: "50%", background: "var(--lime-deep)",
                   boxShadow: "0 0 8px rgba(90,142,42,0.6)", animation: "mly-pulse 1.4s infinite" }} />
    ALL AGENTS ONLINE
  </div>
  <button ref={closeBtnRef} aria-label="關閉" onClick={onClose}
          style={{ background: "transparent", border: "none", color: "var(--paper-ink-3)",
                   cursor: "pointer", marginLeft: 12 }}>
    {/* Material Icons "close" 20px paper-ink-3 */}
  </button>
</div>
```

**Two-column body** (absolute inset, padding `0 80px`, grid `1.05fr 0.95fr`):
- **Left** — relative grid placeItems center. Three concentric `mly-pulse` radar rings at 560×560 with `1px solid rgba(185,136,33,0.20)` borders. Inside, the existing constellation SVG at size 520 (renamed/recolored: brand-mono center stays teal disc + white letter; outer rings/stars switch to gold/paper tones to read on cream). Wrap the constellation in a conic-gradient div that orbits via `br-orbit 5s linear infinite` to draw a sweeping gold ray.

- **Right** — padding-left 28px:
  - Gold-soft achievement pill:
    ```
    成就解鎖 · Brand IQ 報告
    ```
    (icon `auto_awesome`, gold-deep text, `var(--gold-soft)` bg, mono uppercase tracking 0.16em.)
  - Mono kicker line:
    ```
    這是你的品牌的形狀——
    ```
    (font-mono, paper-ink-3, letter-spacing 0.06em.)
  - Serif title block:
    ```tsx
    <div style={{ fontFamily: "var(--font-serif-tc)", fontSize: 52, fontWeight: 700,
                  letterSpacing: "-0.02em", lineHeight: 1.05, marginBottom: 14,
                  color: "var(--paper-ink)" }}>
      {subject}<br/>
      <span style={{ fontFamily: "var(--font-serif)", fontWeight: 500,
                     fontStyle: "italic", color: "var(--gold)" }}>
        Brand Constellation
      </span>
    </div>
    ```
  - Description paragraph (~440px max-width, font-size 14, paper-ink-2, line-height 1.7):
    ```
    Onboarding 階段我們找到了 {subject} 的核心、{productLines.length} 條產品線、{competitors.length} 家直接競品，以及 {mediaNetwork.length} 家可分發的媒體節點。它們在這份 {pageCount} 頁的 Brand IQ 報告裡，被整理成一個你可以隨時拿給高層、夥伴看的故事。
    ```
    (Cap each count behind a `?? 0`. The design's hard-coded "7 條產品線/3 家競品/6 家媒體" is replaced by live counts.)
  - **4-stat mini grid** (grid-cols-4, max-width 480px):
    ```
    產品線    媒體節點    競品    風險訊號
    {productLines.length} {mediaNetwork.length} {competitors.length} {risks.length}
    ```
    (mono caption uppercase 0.14em paper-ink-3; numbers font-numeric 30 weight-700 paper-ink line-height 1.)
  - **CTA pair** (flex gap 10):
    - Primary (gold, `br-glow` pulse):
      ```tsx
      <a href={`/brand/dashboard/report/${reportId}`} ...>
        <Icon name="download" /> 下載 Brand IQ 報告 · PDF
      </a>
      ```
    - Secondary (outline paper-border):
      ```tsx
      <a href={`/brand/dashboard/report/${reportId}`} ...>
        <Icon name="visibility" /> 開啟 Report Viewer
      </a>
      ```
    Both link to the existing report viewer route. The primary uses the existing PDF download endpoint or the same route — preserve current behavior.
  - Bookmark caption (mono, paper-ink-3, font-size 11):
    ```
    📑 已自動存到 Knowledge Base · 隨時可重新下載
    ```

**Bottom strip** (absolute bottom 24, left/right 80):
```tsx
<div style={{ ..., display: "flex", alignItems: "center", justifyContent: "center",
              gap: 10, animation: "mly-fade-up 1200ms 400ms backwards" }}>
  <span /* mono kicker */>分派的工作 →</span>
  {[
    "Answer Pilot", "GEO Pilot", "Monetize Lens", "Market Radar",
    "Context · MoneyDJ", "Context · Smart 智富", "+ 4 個",
  ].map((n, i) => (
    <span key={n} style={{
      display: "inline-flex", alignItems: "center", gap: 5, padding: "5px 10px",
      background: "#fff", border: "1px solid var(--paper-border)",
      borderRadius: 999, fontSize: 11, color: "var(--paper-ink-2)",
      fontFamily: "var(--font-mono)",
      animation: `mly-fade-up 500ms ${500 + i * 80}ms backwards`,
    }}>
      <span style={{ width: 5, height: 5, borderRadius: "50%", background: "var(--lime-deep)" }} />
      {n}
    </span>
  ))}
</div>
```
The agent list is **static cosmetic data** for this PR (no backend wiring) — it tells the same "your agents are now working" story regardless of brand. A `// TODO(chunk-X)` comment marks it for later replacement with the live deployed-agents list.

### 3. `BrandReportHero` rewrite

File: `web/src/components/brand-dashboard/discover/brand-report-hero.tsx`.

**Preserved:**
- `BrandReportHeroProps { report, heroDismissed, onDismiss, onRetry }` — unchanged signature.
- The three render branches: `GeneratingSkeleton`, `FailedState`, `ReadyHero`.
- `heroDismissed` collapses the card (rendered as `null`).

**Replaced — all three branches share the new paper-cream card:**
- Card background: `background: "var(--paper)"` (with a `var(--paper-warm)` fade in one corner via a low-opacity radial overlay if the implementer wants the same depth the design has); `border: 1px solid var(--paper-border)`; `border-radius: 14`; `box-shadow: 0 16px 32px -8px rgba(110,96,69,0.18)`.
- Text default: `var(--paper-ink)`.
- Constellation deco (upper-right): same SVG, recolored — outer rings/stars use `var(--paper-ink-4)` opacity 0.45 instead of white; center disc stays teal with white monogram (the "brand stamp" remains).
- Radar deco: corner conic-gradient orbit, now `rgba(185,136,33,0.18)` (gold) instead of lime.

**`ReadyHero` content:**
- Achievement pill: gold-soft, gold-deep text, `auto_awesome` icon, `成就解鎖 · Brand IQ 報告 · 新`.
- Title (paper-ink, weight 800, size 30): `{subject} 的品牌側寫已準備好——下載你的第一份報告`.
- Description (paper-ink-2): `從 onboarding 抓取的所有公開資料，已整理成 {pageCount} 頁的 PDF。適合給高層、外部夥伴、或保留作為 Brand Agent 啟動點的快照。`
- CTA pair (replace the single existing CTA): primary gold `下載 PDF` + outline `開啟 Report Viewer`.
- Right-side caption: mono paper-ink-4 `產生於 {reportDate} · {preparedBy}`.
- Dismiss × (top-right): `paper-ink-4` button, `aria-label="關閉"` → `onDismiss`.

**`GeneratingSkeleton`:**
- Paper background + paper-border. Skeleton bars use `linear-gradient(90deg, #ECE3D0 0%, #F4EDDF 50%, #ECE3D0 100%)` with `br-shimmer` 1.4s. Status caption: paper-ink-3 mono `準備中 · Brand IQ 報告`.

**`FailedState`:**
- Paper background. The error chip switches to `paper-ink-2` text + `var(--mly-danger)` border. Retry button: outline `paper-border`, label `重試`, calls `onRetry`. The current dismissive secondary action stays.

### 4. Tests

File: `web/src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx` (extend if existing; create if not).

```ts
describe("BrandReportCelebration — Light Edition", () => {
  it("renders the top bar with brand monogram + ALL AGENTS ONLINE telemetry");
  it("renders the gold achievement pill (成就解鎖)");
  it("renders the 4-stat mini grid from report.report counts");
  it("renders the bottom agent-badge strip");
  it("primary CTA links to the report viewer route");
  it("Esc still dismisses (regression on the existing a11y test)");
  it("Tab/Shift-Tab still wrap inside the dialog (regression on focus trap)");
  it("clicking the overlay (not the dialog) dismisses");
});
```

File: `web/src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx`.

```ts
describe("BrandReportHero — Light Edition", () => {
  it("ReadyHero renders on paper background (asserts the var(--paper) inline style)");
  it("ReadyHero renders both gold primary and outline secondary CTAs");
  it("GeneratingSkeleton paper variant — shimmer present, paper-toned");
  it("FailedState calls onRetry on click");
  it("dismiss × calls onDismiss; returns null when heroDismissed is true");
});
```

## Data flow

```
ReportEnvelope (already on develop)
  └── report?.meta?.{subject, monogram, pageCount, reportDate, preparedBy}
  └── report?.{productLines, mediaNetwork, competitors, risks}.length → mini-stats

BrandReportHero (Discover hero card)         BrandReportCelebration (modal)
├── ReadyHero uses meta + first 4 lengths    ├── Top bar uses meta.monogram
├── Generating uses no data (skeleton)       ├── Headline uses meta.subject
└── Failed uses report.error                 ├── Stats grid uses 4 lengths
                                             ├── CTAs link to /brand/dashboard/report/{reportId}
                                             └── Bottom strip is static cosmetic (TODO follow-up)
```

## Error handling

- `meta` absent → fall back to existing defaults (`subject = "你的品牌"`, `mono = subject.charAt(0).toUpperCase()`, `pageCount = 0`).
- Any of `productLines / mediaNetwork / competitors / risks` absent → render `0` in the stats cell (don't hide; the design wants to show the cell with a `0`).
- `reportId` absent → render the CTAs as `<button disabled>` with the caption "報告產生中" rather than a broken link.
- `onRetry` throwing in `FailedState` → swallow + log; the existing retry button stays clickable.

## Testing

- Existing tests pass (a11y, dismissal, focus trap).
- New snapshot/structure tests above pass.
- Manual smoke: `npm run dev`, sign in, with a brand whose report is ready, verify the celebration modal appears once (use the existing `?celebrate=preview` query param fixture path that #66 added — preserve that path).
- Visual diff against the design canvas: open the canvas HTML in one tab, the dev server in another, eyeball-match the layout.

## File summary

**Modified:**
- `web/src/app/globals.css` — adds the Light Edition tokens + any missing keyframes (`br-orbit`, `br-glow`, etc.).
- `web/src/components/brand-dashboard/discover/brand-report-celebration.tsx` — full rewrite of the body; preserves a11y wiring.
- `web/src/components/brand-dashboard/discover/brand-report-hero.tsx` — flip all three branches to paper-cream; replace single CTA with dual CTA pair.

**New / extended:**
- `web/src/components/brand-dashboard/discover/__tests__/brand-report-celebration.test.tsx` — extend with Light Edition structure assertions.
- `web/src/components/brand-dashboard/discover/__tests__/brand-report-hero.test.tsx` — extend or create.

## Risks and migrations

- **No DB / backend migration.** All data the new design needs already exists in `ReportEnvelope`.
- **Tailwind config untouched.** Tokens land in `globals.css` only; existing `bg-brand-*`/`text-ink-*` utilities continue to mean what they meant. The new tokens are consumed via inline `style={{ background: "var(--paper)" }}` — matching the existing pattern of brand-report components.
- **PDF unchanged.** The backend renderer keeps producing the dark-teal PDF until a separate slice. This means an inconsistency for one release: the PDF you download will look different from the in-app surfaces. Acceptable per the deferred-scope decision; flagged here so it's not a surprise during QA.
- **Constellation SVG.** The existing `CelebrationConstellation` SVG has color attributes hardcoded for the dark background. Recoloring it for paper-cream is part of the rewrite; verify nothing else imports it.
- **`heroDismissed` localStorage key.** Preserved as-is (`cortex.heroDismissed.brandReport.v1` per the engineering handoff).
- **No regressions to `?celebrate=preview` fixture path.** #66's preview/fixture path must continue to render the celebration without a backend.

## Acceptance criteria

1. Loading `/brand/dashboard` for a brand with a ready report shows the new paper-cream hero card (no dark teal anywhere on the card).
2. First-time post-onboarding shows the new celebration modal on top of the hero — paper-cream radial, top bar with `ALL AGENTS ONLINE`, two-column body with the 4-stat mini grid (counts match `productLines/mediaNetwork/competitors/risks` lengths in the envelope), and the bottom agent-badge strip.
3. The constellation visual language is preserved (still recognizable as "a constellation centered on the brand monogram"), just paper-toned.
4. Esc closes the celebration. Tab/Shift-Tab wrap. Click on the overlay (not the dialog content) closes.
5. Dismiss × on the hero collapses the card; refresh keeps it dismissed.
6. `?celebrate=preview` query path still works without a backend (#66 preview path preserved).
7. No new lint / type-check / test failures introduced by this PR.
