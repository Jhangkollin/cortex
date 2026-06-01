"""Brand IQ Report — self-contained HTML/CSS print template.

Pure function ``render_report_html(report_json)`` converts a ``ReportDTO``-
shaped dict (camelCase, as stored in ``brand_report.report_json``) into a
single HTML document suitable for Playwright's ``page.pdf()``.

Design reference: /tmp/brandiq_design/cortex/project/brand-report/
  pages-1.jsx, pages-2.jsx, direction-c.jsx (ConstellationSVG), shared.jsx.

Key decisions:
- Inline <style> — zero external network calls at render time.
- @page { size: A4; margin: 0 } — Chromium writes each .page div to one sheet.
- Noto CJK fonts are expected to be installed in the container (apt fonts-noto-cjk).
- Fraunces is unavailable at render time; Georgia/serif substitutes for the
  italic display weight (close enough for the cover pull-quote).
- ConstellationSVG is inlined as literal SVG — no JS, no canvas.
- Defensive .get() everywhere — sparse JSON must not crash the template.
"""
# ruff: noqa: E501  (long strings inside HTML literals are acceptable)

from __future__ import annotations

import html
import math
import re
from collections.abc import Callable
from typing import TypedDict


class _MediaPt(TypedDict):
    x: float
    y: float
    label: str


class _ProductPt(TypedDict):
    x: float
    y: float


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_report_html(report_json: dict) -> str:  # type: ignore[type-arg]
    """Render a complete 8-page Brand IQ Report HTML document.

    Args:
        report_json: A dict matching the ``ReportDTO`` shape (camelCase keys).

    Returns:
        A self-contained HTML string ready for ``page.pdf()``.
    """
    meta = report_json.get("meta", {})
    core = report_json.get("core", [])
    core_judgement = report_json.get("coreJudgement", "")
    product_lines = report_json.get("productLines", [])
    product_note = report_json.get("productNote", "")
    sub_brands = report_json.get("subBrands", [])
    endorsements = report_json.get("endorsements", {})
    ip_collabs = report_json.get("ipCollabs", {})
    media_network = report_json.get("mediaNetwork", [])
    competitors = report_json.get("competitors", [])
    competitor_note = report_json.get("competitorNote", "")
    insights = report_json.get("insights", {})
    faq = report_json.get("faq", [])
    channels = report_json.get("channels", [])
    risks = report_json.get("risks", [])
    sources = report_json.get("sources", {})
    quality = report_json.get("quality", {})

    media_labels = [str(m.get("name", "")) for m in media_network if m.get("name")]

    # Each entry renders one page. The footer's "p.NN / TOTAL" denominator must
    # reflect the ACTUAL number of rendered pages, so we count this list and
    # pass `total` into every renderer rather than trusting meta.pageCount.
    page_renderers: list[Callable[[int], str]] = [
        lambda total: _page1_cover(meta, core_judgement, len(product_lines), media_labels, total),
        lambda total: _page2_core(meta, core, core_judgement, total),
        lambda total: _page3_portfolio(product_lines, product_note, sub_brands, endorsements, ip_collabs, total),
        lambda total: _page4_media(meta, media_network, total),
        lambda total: _page5_competitors(competitors, competitor_note, total),
        lambda total: _page6_insights(insights, total),
        lambda total: _page7_faq_channels(faq, channels, total),
        lambda total: _page8_caveats(risks, sources, quality, total),
    ]
    total_pages = len(page_renderers)
    pages = [render(total_pages) for render in page_renderers]

    return _wrap_document("\n".join(pages))


# ---------------------------------------------------------------------------
# Document wrapper
# ---------------------------------------------------------------------------

_CSS = """
/* ── Reset ─────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #fff; font-family: "Noto Sans CJK TC", "Noto Sans TC", "Microsoft JhengHei", "PingFang TC", "Heiti TC", Arial, sans-serif; }

/* ── CSS Variables ─────────────────────────────────────── */
:root {
  --lime-200: #d4f09a;
  --lime-500: #7cb342;
  --amber-200: #fcd34d;
  --amber-500: #f59e0b;
  --danger: #ef4444;
  --ink-900: #0e1c1a;
}

/* ── Page setup ─────────────────────────────────────────── */
@page { size: A4 portrait; margin: 0; }
@media print {
  html, body { width: 210mm; }
  .page { page-break-after: always; }
  .page:last-child { page-break-after: avoid; }
}

/* ── A4 page container ──────────────────────────────────── */
.page {
  width: 794px;
  height: 1123px;
  position: relative;
  overflow: hidden;
  color: #fff;
}

/* ── Typography helpers ─────────────────────────────────── */
.mono {
  font-family: "Courier New", "Courier", "Liberation Mono", monospace;
  letter-spacing: 0.06em;
}
.serif-tc {
  font-family: "Noto Serif CJK TC", "Noto Serif TC", "Source Han Serif TC", Georgia, serif;
}
.serif {
  font-family: Georgia, "Times New Roman", serif;
}

/* ── Grid background ────────────────────────────────────── */
.grid-bg {
  position: absolute;
  inset: 0;
  opacity: 0.5;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 36px 36px;
}

/* ── Page header ────────────────────────────────────────── */
.page-header {
  position: absolute;
  top: 26px;
  left: 36px;
  right: 36px;
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.5);
}
.page-header-rule {
  position: absolute;
  left: 36px;
  right: 36px;
  top: 50px;
  height: 1px;
  background: rgba(255,255,255,0.10);
}

/* ── Page footer ────────────────────────────────────────── */
.page-footer {
  position: absolute;
  left: 36px;
  right: 36px;
  bottom: 30px;
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.5);
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.10);
}

/* ── Section title ──────────────────────────────────────── */
.section-eyebrow {
  font-size: 10px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--lime-200);
  font-weight: 700;
}
.section-title-h1 {
  font-size: 30px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.02em;
  margin-top: 4px;
  line-height: 1.1;
}
.section-sub {
  font-size: 12px;
  color: rgba(255,255,255,0.7);
  margin-top: 6px;
  max-width: 560px;
}

/* ── Card / cell helpers ────────────────────────────────── */
.card {
  padding: 14px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 8px;
}
.card-sm {
  padding: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 6px;
}
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.grid-4 { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 10px; }

/* ── Certainty chip ─────────────────────────────────────── */
.chip-confirmed   { display: inline-flex; align-items: center; padding: 2px 7px; background: rgba(124,179,66,0.18); color: #DEEBC8; border-radius: 3px; font-size: 10px; font-weight: 700; letter-spacing: 0.04em; }
.chip-likely      { display: inline-flex; align-items: center; padding: 2px 7px; background: rgba(245,158,11,0.18); color: #FCD34D; border-radius: 3px; font-size: 10px; font-weight: 700; letter-spacing: 0.04em; }
.chip-insufficient { display: inline-flex; align-items: center; padding: 2px 7px; background: rgba(255,255,255,0.10); color: rgba(255,255,255,0.65); border-radius: 3px; font-size: 10px; font-weight: 700; letter-spacing: 0.04em; }

/* ── Table helpers ──────────────────────────────────────── */
.table-wrap {
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255,255,255,0.04);
}
.table-header {
  display: grid;
  padding: 10px 14px;
  font-size: 9px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.5);
  border-bottom: 1px solid rgba(255,255,255,0.10);
  background: rgba(0,0,0,0.18);
}
.table-row {
  display: grid;
  padding: 11px 14px;
  font-size: 11.5px;
  color: rgba(255,255,255,0.88);
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.table-row:last-child { border-bottom: none; }

/* ── Lime callout ───────────────────────────────────────── */
.lime-callout {
  padding: 16px 18px;
  background: rgba(124,179,66,0.08);
  border: 1px solid rgba(124,179,66,0.25);
  border-left: 3px solid var(--lime-500);
  border-radius: 6px;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  align-items: flex-start;
}
.amber-callout {
  padding: 10px 14px;
  background: rgba(245,158,11,0.08);
  border: 1px solid rgba(245,158,11,0.25);
  border-radius: 6px;
  font-size: 11.5px;
  color: rgba(255,255,255,0.85);
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
"""


def _wrap_document(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Brand IQ Report</title>
<style>
{_CSS}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _e(value: object) -> str:
    """HTML-escape a value, converting None to empty string."""
    if value is None:
        return ""
    return html.escape(str(value))


def _certainty_chip(value: str) -> str:
    """Return a CertaintyChip span for a given certainty string.

    Matches the contract's certainty vocabulary (已確認 / 高可能 / 資料不足).
    Any unrecognised value falls back to the neutral 資料不足 styling so a
    malformed certainty can never produce an unstyled chip.
    """
    v = str(value)
    if v == "已確認":
        css = "chip-confirmed"
    elif v == "高可能":
        css = "chip-likely"
    else:
        css = "chip-insufficient"  # neutral default for 資料不足 / unknown
    return f'<span class="{css}">{_e(v)}</span>'


def _section_title(num: int, en: str, title: str, sub: str = "") -> str:
    sub_html = f'<div class="section-sub">{_e(sub)}</div>' if sub else ""
    return f"""
<div style="margin-bottom: 14px">
  <div class="mono section-eyebrow">{str(num).zfill(2)} · {_e(en)}</div>
  <div class="section-title-h1">{_e(title)}</div>
  {sub_html}
</div>"""


def _page_header(section: str, en: str, brand_name: str, page: int) -> str:
    return f"""
<div class="mono page-header">
  <span>{_e(section)} · {_e(en)}</span>
  <span>{_e(brand_name)} · p.{str(page).zfill(2)}</span>
</div>
<div class="page-header-rule"></div>"""


def _page_footer(left: str, page: int, page_count: int) -> str:
    return f"""
<div class="mono page-footer">
  <span>{_e(left)}</span>
  <span>Cortex · Brand Intelligence</span>
  <span>p.{str(page).zfill(2)} / {page_count}</span>
</div>"""


# ---------------------------------------------------------------------------
# Constellation SVG
# ---------------------------------------------------------------------------


def _constellation_svg(
    size: int = 380,
    brand_mono: str = "A",
    accent: str = "#7CB342",
    media_labels: list[str] | None = None,
    product_count: int | None = None,
) -> str:
    """Generate the constellation SVG inline (no JS, no canvas).

    Node counts and media labels are derived from the report data:
    - ``media_labels`` — actual outlet names from ``mediaNetwork`` (drawn as
      labelled nodes). If empty, no media nodes are drawn (no fabricated names).
    - ``product_count`` — actual number of ``productLines`` (drawn as
      unlabelled inner-orbit nodes). If 0, no product nodes are drawn.

    The constellation is purely decorative; it must never invent outlet names
    or node counts the report doesn't contain.
    """
    cx = size / 2
    cy = size / 2
    inner_r = size * 0.20
    mid_r = size * 0.32
    outer_r = size * 0.44

    labels = media_labels or []
    media_count = len(labels)
    p_count = product_count or 0

    media_pts: list[_MediaPt] = [
        {
            "x": cx + math.cos((i / media_count) * math.pi * 2 - math.pi / 2) * outer_r,
            "y": cy + math.sin((i / media_count) * math.pi * 2 - math.pi / 2) * outer_r,
            "label": labels[i],
        }
        for i in range(media_count)
    ]

    product_pts: list[_ProductPt] = [
        {
            "x": cx + math.cos((i / p_count) * math.pi * 2 - math.pi / 2 + 0.35) * mid_r,
            "y": cy + math.sin((i / p_count) * math.pi * 2 - math.pi / 2 + 0.35) * mid_r,
        }
        for i in range(p_count)
    ]

    uid = f"cstr_{size}"

    lines_product = "".join(
        f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{p["x"]:.1f}" y2="{p["y"]:.1f}" '
        f'stroke="{accent}" stroke-opacity="0.18" stroke-width="0.6"/>'
        for p in product_pts
    )
    lines_media = (
        "".join(
            f'<line x1="{p["x"]:.1f}" y1="{p["y"]:.1f}" '
            f'x2="{media_pts[i % media_count]["x"]:.1f}" y2="{media_pts[i % media_count]["y"]:.1f}" '
            f'stroke="rgba(255,255,255,0.12)" stroke-width="0.5"/>'
            for i, p in enumerate(product_pts)
        )
        if media_count
        else ""
    )
    nodes_product = "".join(
        f'<circle cx="{p["x"]:.1f}" cy="{p["y"]:.1f}" r="3.5" fill="{accent}" opacity="0.7"/>' for p in product_pts
    )
    nodes_media = "".join(
        f"""<g>
  <circle cx="{m["x"]:.1f}" cy="{m["y"]:.1f}" r="7.5" fill="none" stroke="{accent}" stroke-width="1.2" opacity="0.8"/>
  <circle cx="{m["x"]:.1f}" cy="{m["y"]:.1f}" r="3" fill="{accent}"/>
  <text x="{m["x"]:.1f}" y="{m["y"] - 14:.1f}" text-anchor="middle"
    font-family="Courier New, monospace" font-size="9" fill="rgba(255,255,255,0.7)" letter-spacing="0.1em">{_e(m["label"])}</text>
</g>"""
        for m in media_pts
    )

    center_r = inner_r * 0.55
    center_text_y = cy + 7

    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="display:block">
  <defs>
    <radialGradient id="bgGlow{uid}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.18"/>
      <stop offset="60%" stop-color="{accent}" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <filter id="cstrGlow{uid}"><feGaussianBlur stdDeviation="1.6"/></filter>
  </defs>
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{size * 0.48:.1f}" fill="url(#bgGlow{uid})"/>
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{inner_r:.1f}" fill="none" stroke="rgba(255,255,255,0.08)"/>
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{mid_r:.1f}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-dasharray="2 4"/>
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{outer_r:.1f}" fill="none" stroke="rgba(255,255,255,0.08)"/>
  {lines_product}
  {lines_media}
  {nodes_product}
  {nodes_media}
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{center_r:.1f}" fill="{accent}" filter="url(#cstrGlow{uid})" opacity="0.35"/>
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{center_r:.1f}" fill="#fff"/>
  <text x="{cx:.1f}" y="{center_text_y:.1f}" text-anchor="middle"
    font-family="Georgia, serif" font-size="28" font-weight="700"
    fill="#0E2D2C">{_e(brand_mono or "?")}</text>
</svg>"""


# ---------------------------------------------------------------------------
# Page 1 — Cover
# ---------------------------------------------------------------------------


def _page1_cover(
    meta: dict,  # type: ignore[type-arg]
    core_judgement: str,
    product_count: int,
    media_labels: list[str],
    total_pages: int,
) -> str:
    # total_pages is accepted for a uniform page-renderer signature; the cover
    # has its own "Confidential" footer and shows no "p.NN / TOTAL" counter.
    _ = total_pages
    media_count = len(media_labels)
    subject = _e(meta.get("subject", ""))
    monogram = str(meta.get("monogram") or "?")
    report_id = _e(meta.get("reportId", ""))
    window_from = _e(meta.get("windowFrom", ""))
    window_to = _e(meta.get("windowTo", ""))
    primary_market = _e(meta.get("primaryMarket", ""))
    extended_markets = meta.get("extendedMarkets") or []
    extended_str = " · ".join(_e(m) for m in extended_markets)
    prepared_for = _e(meta.get("preparedFor", ""))
    prepared_by = _e(meta.get("preparedBy", ""))

    svg = _constellation_svg(
        size=420,
        brand_mono=monogram,
        accent="#7CB342",
        media_labels=media_labels,
        product_count=product_count,
    )

    # Pull quote — only the brand's own coreJudgement; omit the block if absent.
    pull_quote = ""
    if core_judgement:
        pull_quote = f"""
  <!-- strategic pin pull quote (from report's coreJudgement) -->
  <div class="serif-tc" style="position:absolute;left:36px;right:36px;top:740px;
    padding-top:18px;border-top:1px solid rgba(255,255,255,0.10);
    font-size:17px;color:rgba(255,255,255,0.88);font-style:italic;line-height:1.55">
    「{_e(core_judgement)}」
    <div class="mono" style="font-style:normal;font-size:10px;color:var(--lime-200);margin-top:8px;letter-spacing:0.14em;text-transform:uppercase">
      — Cortex Brand IQ · Strategic Pin
    </div>
  </div>"""

    contents = "\n".join(
        f"""<div style="font-family:Courier New,monospace">
  <div style="font-size:9px;letter-spacing:0.18em;color:rgba(255,255,255,0.5)">SEC · {_e(c["n"])}</div>
  <div class="serif-tc" style="font-size:14px;font-weight:600;color:#fff;margin-top:6px">{_e(c["t"])}</div>
  <div style="font-size:10px;color:rgba(255,255,255,0.45);margin-top:4px">{_e(c["p"])}</div>
</div>"""
        for c in [
            {"n": "01", "t": "品牌核心", "p": "p.02"},
            {"n": "02", "t": "產品線結構", "p": "p.03"},
            {"n": "03", "t": "媒體網絡", "p": "p.04"},
            {"n": "04", "t": "競品輪廓", "p": "p.05"},
            {"n": "05", "t": "戰略洞察", "p": "p.06"},
        ]
    )

    return f"""<div class="page" style="background:linear-gradient(180deg,#06181A 0%,#0E2D2C 80%,#144948 100%)">
  <!-- faint grid -->
  <div aria-hidden style="position:absolute;inset:0;opacity:0.6;pointer-events:none;
    background-image:linear-gradient(rgba(255,255,255,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.04) 1px,transparent 1px);
    background-size:36px 36px;
    -webkit-mask-image:radial-gradient(ellipse at center,#000 40%,transparent 80%);
    mask-image:radial-gradient(ellipse at center,#000 40%,transparent 80%)"></div>

  <!-- top bar -->
  <div class="mono" style="position:absolute;top:26px;left:36px;right:36px;display:flex;justify-content:space-between;
    font-size:9px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.55)">
    <span>Cortex · Brand Intelligence</span>
    <span>{report_id}</span>
  </div>
  <div style="position:absolute;left:36px;right:36px;top:50px;height:1px;background:rgba(255,255,255,0.08)"></div>

  <!-- eyebrow -->
  <div class="mono" style="position:absolute;left:36px;top:80px;font-size:11px;letter-spacing:0.2em;
    text-transform:uppercase;color:var(--lime-200);font-weight:700">
    ◇ Brand Constellation · Vol. 01
  </div>

  <!-- big title -->
  <div style="position:absolute;left:36px;right:36px;top:116px">
    <div style="font-size:60px;font-weight:800;color:#fff;letter-spacing:-0.025em;line-height:1.0">{subject}</div>
    <div class="serif" style="font-style:italic;font-size:36px;font-weight:500;
      color:var(--lime-200);letter-spacing:-0.02em;line-height:1.1;margin-top:4px">
      The shape of a brand.
    </div>
  </div>

  <!-- constellation centerpiece -->
  <div style="position:absolute;left:0;right:0;top:268px;display:grid;place-items:center">
    {svg}
  </div>

  <!-- legend (left) -->
  <div class="mono" style="position:absolute;left:36px;top:300px;font-size:10px;color:rgba(255,255,255,0.6);letter-spacing:0.06em">
    <div style="margin-bottom:12px;font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.4)">LEGEND</div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
      <span style="width:10px;height:10px;border-radius:50%;background:#fff;display:inline-block"></span> 品牌核心
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
      <span style="width:7px;height:7px;border-radius:50%;background:#7CB342;display:inline-block"></span> 產品線 · {product_count}
    </div>
    <div style="display:flex;align-items:center;gap:8px">
      <span style="width:9px;height:9px;border-radius:50%;border:1.5px solid #7CB342;display:inline-block"></span> 媒體節點 · {media_count}
    </div>
  </div>

  <!-- observation (right) -->
  <div class="mono" style="position:absolute;right:36px;top:300px;text-align:right;font-size:10px;color:rgba(255,255,255,0.6)">
    <div style="margin-bottom:12px;font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.4)">OBSERVATION</div>
    <div style="margin-bottom:6px">{window_from} →</div>
    <div style="margin-bottom:12px">{window_to}</div>
    <div style="font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.4)">MARKET</div>
    <div style="margin-top:6px">{primary_market}</div>
    <div style="color:rgba(255,255,255,0.4);margin-top:2px">+ {extended_str}</div>
  </div>

{pull_quote}

  <!-- contents strip -->
  <div style="position:absolute;left:36px;right:36px;bottom:88px;
    display:grid;grid-template-columns:repeat(5,1fr);gap:14px;
    padding-top:14px;border-top:1px solid rgba(255,255,255,0.10)">
    {contents}
  </div>

  <!-- footer -->
  <div class="mono" style="position:absolute;left:36px;right:36px;bottom:30px;
    display:flex;justify-content:space-between;
    font-size:9px;letter-spacing:0.22em;text-transform:uppercase;color:rgba(255,255,255,0.5)">
    <span>Confidential · {prepared_for}</span>
    <span>{prepared_by}</span>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Page 2 — 品牌核心
# ---------------------------------------------------------------------------


def _page2_core(meta: dict, core: list, core_judgement: str, total_pages: int) -> str:  # type: ignore[type-arg]
    subject = str(meta.get("subject", ""))

    core_cards = "\n".join(
        f"""<div class="card">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
    <span class="mono" style="font-size:9px;color:var(--lime-200);font-weight:700">0{i + 1}</span>
    <span style="font-size:13px;font-weight:700;color:#fff">{_e(row.get("item", ""))}</span>
    <span style="margin-left:auto">{_certainty_chip(row.get("certainty", "資料不足"))}</span>
  </div>
  <div style="font-size:11.5px;color:rgba(255,255,255,0.8);line-height:1.6">{_e(row.get("body", ""))}</div>
</div>"""
        for i, row in enumerate(core)
    )

    # At-a-glance — only cards whose value is present in report_json.
    # We do not invent stats (no "27年", no "Voice 4/47"); fields with no
    # data are omitted entirely rather than filled with placeholders.
    glance_cards: list[tuple[str, str, str]] = []
    if meta.get("founded"):
        glance_cards.append(("成立", str(meta["founded"]), "年份"))
    if meta.get("category"):
        glance_cards.append(("品類", str(meta["category"]), f"信心 {meta.get('confidence', '—')}%"))
    if meta.get("primaryMarket"):
        extended = meta.get("extendedMarkets") or []
        sub = f"+ {len(extended)} 延伸" if extended else "主市場"
        glance_cards.append(("主市場", str(meta["primaryMarket"]), sub))
    if meta.get("tagline"):
        glance_cards.append(("品牌標語", str(meta["tagline"]), "官方文案"))

    at_a_glance_block = ""
    if glance_cards:
        cards_html = "\n".join(
            f"""<div style="padding:14px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.10);border-radius:6px">
  <div class="mono" style="font-size:9px;letter-spacing:0.14em;color:rgba(255,255,255,0.55);text-transform:uppercase">{_e(label)}</div>
  <div style="font-size:22px;font-weight:700;color:#fff;line-height:1.15;margin-top:4px">{_e(value)}</div>
  <div style="font-size:10px;color:rgba(255,255,255,0.55);margin-top:4px">{_e(sub)}</div>
</div>"""
            for label, value, sub in glance_cards
        )
        at_a_glance_block = f"""
    <!-- at-a-glance (data-backed meta fields only) -->
    <div style="margin-top:18px">
      <div class="mono" style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.6);margin-bottom:8px">At a glance</div>
      <div class="grid-4">
        {cards_html}
      </div>
    </div>"""

    # judgement pull quote — only when coreJudgement is present
    judgement_block = ""
    if core_judgement:
        judgement_block = f"""
    <div class="lime-callout" style="margin-top:18px">
      <div class="serif" style="font-size:36px;font-style:italic;color:var(--lime-200);line-height:1;font-weight:700;margin-top:-2px">"</div>
      <div>
        <div class="mono" style="font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:var(--lime-200);margin-bottom:6px">Cortex 的判斷</div>
        <div class="serif-tc" style="font-size:15px;color:#fff;line-height:1.65;font-style:italic">{_e(core_judgement)}</div>
      </div>
    </div>"""

    return f"""<div class="page" style="background:#0E2D2C">
  <div class="grid-bg"></div>
  {_page_header("SEC · 01", "品牌核心 · The Anatomy", subject, 2)}

  <div style="position:absolute;left:36px;right:36px;top:76px">
    {_section_title(1, "Brand Anatomy", "品牌核心解剖", f"從公開資料整理 {_e(subject)} 的品牌主體、市場、定位與敘事。")}

    <div class="grid-2" style="margin-top:6px">
      {core_cards}
    </div>
{judgement_block}
{at_a_glance_block}
  </div>

  {_page_footer("SEC · 01 — 品牌核心", 2, total_pages)}
</div>"""


# ---------------------------------------------------------------------------
# Page 3 — 產品線結構
# ---------------------------------------------------------------------------


def _page3_portfolio(
    product_lines: list,  # type: ignore[type-arg]
    product_note: str,
    sub_brands: list,  # type: ignore[type-arg]
    endorsements: dict,  # type: ignore[type-arg]
    ip_collabs: dict,  # type: ignore[type-arg]
    total_pages: int,
) -> str:
    line_count = len(product_lines)
    product_rows = "\n".join(
        f"""<div class="table-row" style="grid-template-columns:1.0fr 1.4fr 1.5fr 1.5fr 0.5fr">
  <div style="font-weight:700;color:#fff">{_e(p.get("line", ""))}</div>
  <div style="color:rgba(255,255,255,0.75)">{_e(p.get("thesis", ""))}</div>
  <div class="mono" style="font-size:10.5px;color:rgba(255,255,255,0.85)">{_e(p.get("examples", ""))}</div>
  <div style="color:rgba(255,255,255,0.65);font-size:11px">{_e(p.get("signal", ""))}</div>
  <div style="text-align:right;font-weight:700;font-size:13px;
    color:{_confidence_color(p.get("confidence", 0))}">{_e(p.get("confidence", ""))}%</div>
</div>"""
        for p in product_lines
    )

    sub_brand_cards = "\n".join(
        f"""<div class="card-sm">
  <div class="mono" style="font-size:9px;letter-spacing:0.14em;text-transform:uppercase;color:rgba(255,255,255,0.5);margin-bottom:4px">{_e(s.get("type", ""))}</div>
  <div style="font-size:13px;font-weight:700;color:#fff">{_e(s.get("name", ""))}</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.65);margin-top:6px;line-height:1.5">{_e(s.get("note", ""))}</div>
</div>"""
        for s in sub_brands
    )

    endorsement_html = _section_status_card("代言人 / 名人合作", endorsements)
    ip_html = _section_status_card("IP 聯名", ip_collabs)

    note_block = ""
    if product_note:
        note_block = f"""
    <div class="amber-callout" style="margin-top:14px">
      <span style="font-size:14px;color:var(--amber-200)">ℹ</span>
      <span>{_e(product_note)}</span>
    </div>"""

    return f"""<div class="page" style="background:#0E2D2C">
  <div class="grid-bg"></div>
  {_page_header("SEC · 02", "產品線結構 · Portfolio", "", 3)}

  <div style="position:absolute;left:36px;right:36px;top:76px">
    {_section_title(2, "Product Portfolio", f"{line_count} 條產品線", "從公開資料整理的產品線結構，按產品線級別呈現。")}

    <div class="table-wrap">
      <div class="table-header" style="grid-template-columns:1.0fr 1.4fr 1.5fr 1.5fr 0.5fr">
        <span>線別</span><span>核心訴求</span><span>代表性產品</span><span>差異化訊號</span><span style="text-align:right">信心</span>
      </div>
      {product_rows}
    </div>
{note_block}

    <!-- sub-brands -->
    <div style="margin-top:22px">
      <div class="mono section-eyebrow" style="margin-bottom:8px">子品牌 / 系列 · Sub-brands</div>
      <div class="grid-3">
        {sub_brand_cards}
      </div>
    </div>

    <!-- endorsements / IP -->
    <div class="grid-2" style="margin-top:14px">
      {endorsement_html}
      {ip_html}
    </div>
  </div>

  {_page_footer("SEC · 02 — 產品線結構", 3, total_pages)}
</div>"""


def _section_status_card(title: str, section: dict) -> str:  # type: ignore[type-arg]
    status = str(section.get("status", "資料不足"))
    body = str(section.get("body", ""))
    return f"""<div style="padding:12px;background:rgba(255,255,255,0.02);
  border:1px dashed rgba(255,255,255,0.15);border-radius:6px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
    <span style="font-size:12px;font-weight:700;color:#fff">{_e(title)}</span>
    {_certainty_chip(status)}
  </div>
  <div style="font-size:11px;color:rgba(255,255,255,0.65);line-height:1.5">{_e(body)}</div>
</div>"""


def _confidence_color(confidence: object) -> str:
    try:
        c = int(str(confidence))
    except (TypeError, ValueError):
        return "#fff"
    if c >= 90:
        return "var(--lime-200)"
    if c >= 80:
        return "#fff"
    return "var(--amber-200)"


# ---------------------------------------------------------------------------
# Page 4 — 媒體網絡
# ---------------------------------------------------------------------------


def _page4_media(meta: dict, media_network: list, total_pages: int) -> str:  # type: ignore[type-arg]
    subject = str(meta.get("subject", ""))
    monogram = str(meta.get("monogram") or "?")
    outlet_count = len(media_network)
    media_labels = [str(m.get("name", "")) for m in media_network if m.get("name")]

    # Mini constellation uses short forms of the real outlet names (first 4 chars)
    # to avoid overflowing the small SVG, but still only the report's own data.
    short_labels = [lbl[:4] for lbl in media_labels]
    mini_svg = _constellation_svg(
        size=180,
        brand_mono=monogram,
        accent="#7CB342",
        media_labels=short_labels,
        product_count=outlet_count,
    )

    media_rows = "\n".join(
        f"""<div class="table-row" style="grid-template-columns:1.5fr 1.5fr 0.6fr 1.4fr 0.6fr 0.4fr">
  <div style="display:flex;align-items:center;gap:8px;font-weight:600">
    <span style="width:7px;height:7px;border-radius:50%;background:var(--lime-500);
      box-shadow:0 0 6px rgba(124,179,66,0.6);display:inline-block;flex-shrink:0"></span>
    {_e(m.get("name", ""))}
  </div>
  <div style="color:rgba(255,255,255,0.7)">{_e(m.get("audience", ""))}</div>
  <div style="text-align:right;font-weight:600">{_e(m.get("weekly", ""))}</div>
  <div style="color:rgba(255,255,255,0.7);font-size:11px">{_e(m.get("topics", ""))}</div>
  <div style="text-align:right;font-weight:700;font-size:13px;
    color:{_relevance_color(m.get("relevance", 0))}">{_e(m.get("relevance", ""))}</div>
  <div style="text-align:right">{_trend_arrow(m.get("trend", ""))}</div>
</div>"""
        for m in media_network
    )

    return f"""<div class="page" style="background:#0E2D2C">
  <div class="grid-bg"></div>
  {_page_header("SEC · 03", "媒體網絡 · The Reachable Galaxy", subject, 4)}

  <!-- mini constellation top-right -->
  <div style="position:absolute;right:30px;top:56px;opacity:0.85">
    {mini_svg}
  </div>

  <div style="position:absolute;left:36px;right:36px;top:70px">
    {
        _section_title(
            3,
            "Media Network",
            "你的品牌能被聽見的地方",
            f"Cortex 識別 {outlet_count} 家相關媒體節點，依相關性與題材分布整理。",
        )
    }
  </div>

  <div style="position:absolute;left:36px;right:36px;top:240px">
    <div class="table-wrap">
      <div class="table-header" style="grid-template-columns:1.5fr 1.5fr 0.6fr 1.4fr 0.6fr 0.4fr">
        <span>媒體</span><span>讀者輪廓</span><span style="text-align:right">週讀者</span>
        <span>主題</span><span style="text-align:right">相關性</span><span style="text-align:right">趨勢</span>
      </div>
      {media_rows}
    </div>
  </div>

  {_page_footer("SEC · 03 — 媒體網絡", 4, total_pages)}
</div>"""


def _relevance_color(relevance: object) -> str:
    try:
        r = int(str(relevance))
    except (TypeError, ValueError):
        return "rgba(255,255,255,0.7)"
    if r >= 90:
        return "var(--lime-200)"
    if r >= 80:
        return "#fff"
    return "rgba(255,255,255,0.7)"


def _trend_arrow(trend: str) -> str:
    if trend == "上升":
        return '<span style="color:var(--lime-200);font-size:13px">↑</span>'
    if trend == "下降":
        return '<span style="color:#FCA5A5;font-size:13px">↓</span>'
    return '<span style="color:rgba(255,255,255,0.6);font-size:13px">→</span>'


# ---------------------------------------------------------------------------
# Page 5 — 競品輪廓
# ---------------------------------------------------------------------------

# Competitor tier → (foreground, soft-background) tones, keyed on the canonical
# tier strings from the contract so reordering competitors never flips the
# colour semantics. Unknown tiers fall back to the neutral default.
_COMPETITOR_TONE_NEUTRAL = ("rgba(255,255,255,0.5)", "rgba(255,255,255,0.08)")
_COMPETITOR_TONES_BY_TIER = {
    "直接競品": ("var(--danger)", "rgba(239,68,68,0.15)"),
    "監測中（未選）": ("var(--amber-500)", "rgba(245,158,11,0.15)"),
    "替代型競品": _COMPETITOR_TONE_NEUTRAL,
}


def _competitor_tone(tier: str) -> tuple[str, str]:
    """Map a competitor tier value to its (fg, soft-bg) tone, neutral default."""
    return _COMPETITOR_TONES_BY_TIER.get(str(tier), _COMPETITOR_TONE_NEUTRAL)


def _competitor_card(c: dict) -> str:  # type: ignore[type-arg]
    fg, soft_bg = _competitor_tone(str(c.get("tier", "")))
    return f"""<div style="padding:14px;background:rgba(255,255,255,0.04);
  border:1px solid rgba(255,255,255,0.10);border-radius:8px;
  border-top:3px solid {fg}">
  <span style="display:inline-block;padding:3px 8px;border-radius:999px;
    background:{soft_bg};color:{fg};
    font-size:10px;font-weight:700;letter-spacing:0.08em;margin-bottom:8px">{_e(c.get("tier", ""))}</span>
  <div style="font-size:14px;font-weight:700;color:#fff;line-height:1.35">{_e(c.get("brands", ""))}</div>
  <div style="font-size:11.5px;color:rgba(255,255,255,0.7);margin-top:10px;line-height:1.6">{_e(c.get("basis", ""))}</div>
  <div style="margin-top:10px;padding-top:10px;border-top:1px dashed rgba(255,255,255,0.12)">
    <div class="mono" style="font-size:9px;letter-spacing:0.14em;text-transform:uppercase;color:rgba(255,255,255,0.5);margin-bottom:4px">相對位置</div>
    <div style="font-size:11.5px;color:rgba(255,255,255,0.88);line-height:1.55">{_e(c.get("position", ""))}</div>
  </div>
</div>"""


def _page5_competitors(
    competitors: list,  # type: ignore[type-arg]
    competitor_note: str,
    total_pages: int,
) -> str:
    # Render real competitor tiers as cards. We do NOT plot a 2×2 scatter:
    # the contract carries no positioning coordinates, so any plot would be
    # fabricated. The textual "相對位置" (position) field is the brand's own data.
    competitor_cards = "\n".join(_competitor_card(c) for c in competitors)

    note_block = ""
    if competitor_note:
        note_block = f"""
    <div style="margin-top:22px;padding:10px 14px;background:rgba(255,255,255,0.04);
      border:1px solid rgba(255,255,255,0.10);border-radius:6px;
      font-size:11px;color:rgba(255,255,255,0.7);display:flex;gap:8px;align-items:flex-start">
      <span style="color:var(--lime-200)">✦</span>
      <span><strong style="color:#fff">分析師備註：</strong>{_e(competitor_note)}</span>
    </div>"""

    return f"""<div class="page" style="background:#0E2D2C">
  <div class="grid-bg"></div>
  {_page_header("SEC · 04", "競品輪廓 · Competitor Landscape", "", 5)}

  <div style="position:absolute;left:36px;right:36px;top:76px">
    {
        _section_title(
            4,
            "Competitive Position",
            "你在這個品類的位置",
            "三層次競品分析：直接競爭、監測中、替代型。判斷基於品類重疊、通路重疊與品牌化程度。",
        )
    }

    <div class="grid-3">
      {competitor_cards}
    </div>
{note_block}
  </div>

  {_page_footer("SEC · 04 — 競品輪廓", 5, total_pages)}
</div>"""


# ---------------------------------------------------------------------------
# Page 6 — 戰略洞察
# ---------------------------------------------------------------------------


def _page6_insights(insights: dict, total_pages: int) -> str:  # type: ignore[type-arg]
    confirmed = insights.get("confirmed") or []
    inferences = insights.get("inferences") or []
    hypotheses = insights.get("hypotheses") or []

    cols = [
        {
            "h": "已確認事實",
            "en": "Confirmed",
            "items": confirmed,
            "tone": "var(--lime-200)",
            "bg": "rgba(124,179,66,0.10)",
            "border": "rgba(124,179,66,0.30)",
        },
        {
            "h": "合理推論",
            "en": "Inferences",
            "items": inferences,
            "tone": "#fff",
            "bg": "rgba(255,255,255,0.06)",
            "border": "rgba(255,255,255,0.18)",
        },
        {
            "h": "待驗證假設",
            "en": "Hypotheses",
            "items": hypotheses,
            "tone": "var(--amber-200)",
            "bg": "rgba(245,158,11,0.08)",
            "border": "rgba(245,158,11,0.30)",
        },
    ]

    insight_blocks = "\n".join(
        f"""<div style="padding:16px;border-radius:8px;background:{c["bg"]};
  border:1px solid {c["border"]}">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
    <span class="mono" style="font-size:11px;letter-spacing:0.16em;text-transform:uppercase;
      color:{c["tone"]};font-weight:700">0{i + 1} · {_e(c["en"])}</span>
    <span style="font-size:16px;font-weight:700;color:#fff">{_e(c["h"])}</span>
    <span class="mono" style="margin-left:auto;font-size:10px;color:rgba(255,255,255,0.5)">{len(c["items"])} 點</span>
  </div>
  <ol style="margin:0;padding:0;list-style:none;display:grid;gap:6px">
    {
            "".join(
                f'<li style="display:grid;grid-template-columns:auto 1fr;gap:10px;align-items:flex-start;'
                f'font-size:12.5px;color:rgba(255,255,255,0.92);line-height:1.65">'
                f'<span class="mono" style="font-size:10px;color:{c["tone"]};font-weight:700;margin-top:2px">'
                f"{str(idx + 1).zfill(2)}</span><span>{_e(item)}</span></li>"
                for idx, item in enumerate(c["items"])
            )
        }
  </ol>
</div>"""
        for i, c in enumerate(cols)
    )

    return f"""<div class="page" style="background:#0E2D2C">
  <div class="grid-bg"></div>
  {_page_header("SEC · 05", "戰略洞察 · Strategic Insights", "", 6)}

  <div style="position:absolute;left:36px;right:36px;top:76px">
    {
        _section_title(
            5,
            "Strategic Insights",
            "從訊號到行動",
            "按證據強度分層：已確認事實 → 合理推論 → 待驗證假設。每一層的決策重量不同。",
        )
    }

    <div style="display:grid;gap:12px">
      {insight_blocks}
    </div>
  </div>

  {_page_footer("SEC · 05 — 戰略洞察", 6, total_pages)}
</div>"""


# ---------------------------------------------------------------------------
# Page 7 — FAQ + 通路
# ---------------------------------------------------------------------------


def _page7_faq_channels(faq: list, channels: list, total_pages: int) -> str:  # type: ignore[type-arg]
    faq_count = len(faq)
    faq_cards = "\n".join(
        f"""<div class="card-sm">
  <div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:6px">
    <span class="mono" style="font-size:9px;color:var(--lime-200);font-weight:700;margin-top:1px">Q{i + 1}</span>
    <div style="font-size:12px;font-weight:600;color:#fff;line-height:1.5">{_e(row.get("q", ""))}</div>
  </div>
  <div style="font-size:10.5px;color:rgba(255,255,255,0.7);line-height:1.6">{_e(row.get("a", ""))}</div>
  <div style="display:flex;align-items:center;gap:6px;margin-top:8px;padding-top:6px;border-top:1px dashed rgba(255,255,255,0.10)">
    <span class="mono" style="font-size:9px;color:rgba(255,255,255,0.5)">{_e(row.get("source", ""))}</span>
    <span style="margin-left:auto;font-size:9px;padding:1px 6px;
      background:rgba(124,179,66,0.18);color:var(--lime-200);border-radius:3px;font-weight:700">{_e(row.get("level", ""))}</span>
  </div>
</div>"""
        for i, row in enumerate(faq)
    )

    channel_rows = "\n".join(
        f"""<div style="display:grid;grid-template-columns:180px 1.4fr 1.4fr;
  padding:11px 14px;font-size:11.5px;color:rgba(255,255,255,0.88);align-items:flex-start;
  border-bottom:1px solid rgba(255,255,255,0.06)">
  <div style="font-weight:700;color:#fff">{_e(ch.get("type", ""))}</div>
  <div style="color:rgba(255,255,255,0.75);padding-right:12px">{_e(ch.get("surfaces", ""))}</div>
  <div style="color:rgba(255,255,255,0.65);font-size:11px;line-height:1.5">{_e(ch.get("read", ""))}</div>
</div>"""
        for ch in channels
    )

    return f"""<div class="page" style="background:#0E2D2C">
  <div class="grid-bg"></div>
  {_page_header("SEC · 06–07", "Voice in the Wild · 讀者熱問 + 通路布局", "", 7)}

  <div style="position:absolute;left:36px;right:36px;top:76px">
    {
        _section_title(
            6,
            "Reader FAQ",
            "讀者最常問的問題",
            f"從 onboarding 階段抓取的 {faq_count} 個高強度問題，Cortex 預先準備了符合品牌語氣的回應。",
        )
    }

    <div class="grid-2" style="margin-bottom:22px">
      {faq_cards}
    </div>

    {_section_title(7, "Channels", "通路布局", "D2C、媒體網絡、實體與海外通路的當前覆蓋。")}

    <div class="table-wrap" style="border-radius:8px;overflow:hidden;background:rgba(255,255,255,0.04)">
      {channel_rows}
    </div>
  </div>

  {_page_footer("SEC · 06–07 — FAQ + Channels", 7, total_pages)}
</div>"""


# ---------------------------------------------------------------------------
# Page 8 — 風險 + 來源 + 品質
# ---------------------------------------------------------------------------


def _page8_caveats(risks: list, sources: dict, quality: dict, total_pages: int) -> str:  # type: ignore[type-arg]
    risk_cards = "\n".join(
        f"""<div style="padding:12px;background:{"rgba(239,68,68,0.08)" if r.get("level") == "高" else "rgba(245,158,11,0.06)"};
  border:1px solid {"rgba(239,68,68,0.30)" if r.get("level") == "高" else "rgba(245,158,11,0.25)"};border-radius:6px">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
    <span class="mono" style="font-size:9px;font-weight:700;padding:2px 6px;
      background:{"var(--danger)" if r.get("level") == "高" else "var(--amber-500)"};
      color:#fff;border-radius:3px;letter-spacing:0.08em">{_e(r.get("level", ""))} 風險</span>
    <span style="font-size:12px;font-weight:700;color:#fff">{_e(r.get("theme", ""))}</span>
  </div>
  <div class="mono" style="font-size:10px;color:rgba(255,255,255,0.5);margin-bottom:4px">觸發 · {_e(r.get("trigger", ""))}</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.7);line-height:1.55;margin-bottom:6px">{_e(r.get("note", ""))}</div>
  <div style="padding-top:6px;border-top:1px dashed rgba(255,255,255,0.10);font-size:11px;color:rgba(255,255,255,0.85);line-height:1.55">
    <span class="mono" style="font-size:9px;letter-spacing:0.14em;text-transform:uppercase;color:var(--lime-200)">建議 · </span>
    {_e(r.get("action", ""))}
  </div>
</div>"""
        for r in risks
    )

    source_tiers = [
        {"tier": "A · 官方來源", "items": sources.get("A") or [], "tone": "var(--lime-200)"},
        {"tier": "B · 高可信第三方", "items": sources.get("B") or [], "tone": "#fff"},
        {"tier": "C · 未納入主要事實", "items": sources.get("C") or [], "tone": "rgba(255,255,255,0.6)"},
    ]
    source_cards = "\n".join(
        f"""<div class="card-sm">
  <div class="mono" style="font-size:9px;letter-spacing:0.14em;text-transform:uppercase;
    color:{s["tone"]};font-weight:700;margin-bottom:8px">{_e(s["tier"])}</div>
  <ul style="margin:0;padding:0;list-style:none;display:grid;gap:4px">
    {
            "".join(
                f'<li style="font-size:10.5px;color:rgba(255,255,255,0.78);display:grid;grid-template-columns:8px 1fr;gap:6px;line-height:1.55">'
                f'<span style="color:{s["tone"]};margin-top:6px">·</span><span>{_e(src)}</span></li>'
                for src in s["items"]
            )
        }
  </ul>
</div>"""
        for s in source_tiers
    )

    quality_rows = [
        {"l": "高信心段落", "v": quality.get("high", ""), "tone": "var(--lime-200)"},
        {"l": "中低信心段落", "v": quality.get("midLow", ""), "tone": "var(--amber-200)"},
        {"l": "已知缺口", "v": quality.get("gaps", ""), "tone": "rgba(255,255,255,0.7)"},
        {"l": "來源衝突", "v": quality.get("conflicts", ""), "tone": "rgba(255,255,255,0.7)"},
        {"l": "不足以確認", "v": quality.get("open", ""), "tone": "rgba(255,255,255,0.7)"},
    ]
    quality_html = "\n".join(
        f"""<div style="display:grid;grid-template-columns:140px 1fr;padding:9px 14px;gap:14px;
  border-bottom:1px solid rgba(255,255,255,0.06);font-size:11.5px;line-height:1.55">
  <div class="mono" style="font-size:10px;letter-spacing:0.06em;color:{r["tone"]};font-weight:700;text-transform:uppercase">{_e(r["l"])}</div>
  <div style="color:rgba(255,255,255,0.82)">{_e(r["v"])}</div>
</div>"""
        for r in quality_rows
    )

    return f"""<div class="page" style="background:#0E2D2C">
  <div class="grid-bg"></div>
  {_page_header("SEC · 08–10", "Caveats · 風險、來源、品質", "", 8)}

  <div style="position:absolute;left:36px;right:36px;top:76px">
    {
        _section_title(
            8,
            "Compliance Signals",
            "合規風險訊號",
            "本段為公開資訊風險辨識，不構成法律意見。重要素材建議由合規人員複核。",
        )
    }

    <div class="grid-2" style="margin-bottom:18px">
      {risk_cards}
    </div>

    <!-- sources -->
    <div class="grid-3" style="margin-bottom:18px">
      {source_cards}
    </div>

    {_section_title(10, "Data Quality", "資料品質評估")}
    <div class="table-wrap" style="border-radius:6px;overflow:hidden;background:rgba(255,255,255,0.04)">
      {quality_html}
    </div>
  </div>

  {_page_footer("SEC · 08–10 — Caveats", 8, total_pages)}
</div>"""


# ---------------------------------------------------------------------------
# Sanitize filename helper (exported for pdf_service)
# ---------------------------------------------------------------------------

_UNSAFE_RE = re.compile(r"[^\w\s\-\.]", re.UNICODE)


def sanitize_filename(name: str) -> str:
    """Replace filesystem-unsafe characters with underscores."""
    return _UNSAFE_RE.sub("_", name).strip()
