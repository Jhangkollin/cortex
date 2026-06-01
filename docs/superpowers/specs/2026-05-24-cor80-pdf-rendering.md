# COR-80 · Brand IQ Report PDF Rendering

**Date:** 2026-05-24
**Status:** Implementation

---

## Decision

Render the 8-page Brand IQ Report to a downloadable PDF using **Playwright headless Chromium** inside the `cortex-api` container. The HTML template is self-contained (no external network calls at render time) and is built server-side from the `ReportDTO` JSON.

---

## Approach

### Why Playwright / Chromium

- Native print-to-PDF with background colours, A4 sizing, and Chinese font rendering.
- The `playwright` package is already in `uv.lock` (pulled transitively by `cortex-brand-extract`'s `render` extra).
- No separate rendering service; on-demand GET keeps the footprint simple at MVP load.
- A pooled browser is a later optimisation — launch-per-render is sufficient for p95 load.

### Self-contained HTML

The template (`service/brand_report/pdf/template.py`) outputs a single HTML file with:
- Inline `<style>` — no external CSS.
- `@page { size: A4; margin: 0; }` + `@media print { ... }` for PDF sizing.
- Bundled CJK font-families (`Noto Sans CJK TC`, `Noto Serif CJK TC`) installed in the image; a serif fallback for the display font (Fraunces → Georgia/serif).
- The constellation SVG inlined — no `<canvas>`, no JS at render time.
- 8 A4 sections separated by `page-break-after: always`.

### Image size impact

`uv run playwright install --with-deps chromium` adds ~300 MB to the runtime image. `fonts-noto-cjk` adds ~150 MB. The final image grows from ~350 MB to ~800 MB. This is acceptable for MVP; a sidecar renderer is a later option if the image size becomes a concern.

---

## Page mapping (prototype → PDF)

| PDF Page | Prototype section | Data fields |
|---|---|---|
| P1 Cover | `ReportPage1` | `meta.*`, `ConstellationSVG` |
| P2 品牌核心 | `ReportPage2` | `core[]`, `coreJudgement`, `meta.founded/confidence/primaryMarket` |
| P3 產品線結構 | `ReportPage3` | `productLines[]`, `productNote`, `subBrands[]`, `endorsements`, `ipCollabs` |
| P4 媒體網絡 | `ReportPage4` | `mediaNetwork[]`, constellation mini-SVG |
| P5 競品輪廓 | `ReportPage5` | `competitors[]`, `competitorNote` |
| P6 戰略洞察 | `ReportPage6` | `insights.{confirmed,inferences,hypotheses}` |
| P7 FAQ + 通路 | `ReportPage7` | `faq[]`, `channels[]` |
| P8 風險 + 來源 + 品質 | `ReportPage8` | `risks[]`, `sources.{A,B,C}`, `quality.*` |

---

## Module layout

```
api/src/cortex_api/service/brand_report/
  pdf/
    __init__.py
    template.py      # render_report_html(report_json: dict) -> str
    renderer.py      # async render_pdf(html, *, timeout_ms) -> bytes
  pdf_service.py     # BrandReportPdfService.generate_pdf(brand_id, report_id)
```

### DI wiring

- `pdf_service` added to `BrandReportContainer` as `providers.Singleton`.
- Injected deps: `service` (read), `renderer` (callable, injectable for test fakes), `config`.
- Router picks it up via `Provide[BrandReportContainer.pdf_service]`.

---

## New endpoint

```
GET /v1/brand/{brand_id}/report/{report_id}/pdf
```

- Auth: `active_brand` + `VIEW_BRAND_DASHBOARD` capability (same as `get_report`).
- Returns: `application/pdf` with `Content-Disposition: attachment; filename*=UTF-8''...` (RFC 5987 encoding for CJK brand names).
- Not-ready report → `ConflictError` → HTTP 409.
- Unknown report → `NotFoundError` → HTTP 404.

---

## Config

`pdf_render_timeout_ms: int = 15000` added to `service/brand_report/config.py`.

---

## Dockerfile change

In the **runtime** stage (after the existing `apt-get` block):

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*
RUN /app/api/.venv/bin/playwright install --with-deps chromium
```

Chromium is run as the `cortex` (non-root) user; `--no-sandbox` flag is required in containerised environments and is set in `renderer.py`.

---

## Test plan

| Layer | File | What it tests |
|---|---|---|
| Unit | `tests/unit/service/brand_report/test_pdf_template.py` | Template produces 8 sections, brand name present, 資料不足 chips for empty sections, no crash on sparse JSON |
| Unit | `tests/unit/service/brand_report/test_pdf_service.py` | `generate_pdf` with fake renderer → bytes + filename; not-ready → ConflictError |
| Integration | `tests/integration/test_pdf_api.py` | HTTP GET /pdf with fake renderer → 200 + application/pdf + Content-Disposition; 404; 403 |

No real Chromium in CI unit gate; renderer is DI-overridable.
