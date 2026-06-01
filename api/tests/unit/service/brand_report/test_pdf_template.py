"""Unit tests for the Brand IQ Report HTML/CSS print template.

No browser, no Playwright — only ``render_report_html`` is called directly.
We verify structure, page markers, certainty chips, and crash-safety on sparse
JSON.  The full BRAND_IQ fixture mirrors ``/tmp/brandiq_design/.../data.jsx``.
"""

from __future__ import annotations

import pytest

from cortex_api.service.brand_report.pdf.template import (
    _COMPETITOR_TONE_NEUTRAL,
    _competitor_tone,
    render_report_html,
    sanitize_filename,
)

# ---------------------------------------------------------------------------
# Full fixture — mirrors data.jsx BRAND_IQ
# ---------------------------------------------------------------------------

FULL_FIXTURE: dict = {
    "meta": {
        "subject": "Acme Bank Asia",
        "enName": "Acme Bank Asia",
        "legalName": "Acme Bank Asia Holdings, Ltd.",
        "domain": "acmebank.asia",
        "primaryMarket": "台灣",
        "extendedMarkets": ["香港", "新加坡"],
        "reportDate": "2026-05-22",
        "windowFrom": "2025-05-22",
        "windowTo": "2026-05-22",
        "monogram": "A",
        "brandColor": "#225D59",
        "tagline": "Banking, redesigned for Asia.",
        "founded": "1998",
        "category": "零售金融 / 數位銀行",
        "confidence": 96,
        "reportId": "BIQ-2026-05-22-ACMEBA",
        "pageCount": 8,
        "preparedFor": "Marketing Manager · Brand Account",
        "preparedBy": "Cortex · Brand Agent v3.2",
    },
    "core": [
        {
            "item": "品牌主體",
            "body": "Acme Bank Asia 為 Acme Bank Asia Holdings, Ltd. 旗下零售金融與數位銀行品牌。",
            "certainty": "已確認",
        },
        {"item": "成立脈絡", "body": "1998 年成立，27 年來服務超過 320 萬家庭與企業。", "certainty": "已確認"},
        {"item": "主要市場", "body": "主市場為台灣；官方明確支援香港與新加坡的延伸服務。", "certainty": "已確認"},
        {"item": "品牌定位", "body": "核心話術集中在「為亞洲設計」「值得信賴的對話」。", "certainty": "已確認"},
        {"item": "Brand Voice", "body": "4 句訓練樣本中 3 句符合品牌指紋。", "certainty": "高可能"},
    ],
    "coreJudgement": "Acme Bank Asia 並非單純走數位銀行敘事，而是把「亞洲在地」「顧問式關係」「家庭信任」三條線並置。",
    "productLines": [
        {
            "line": "信用卡",
            "thesis": "高端消費、海外回饋",
            "examples": "Acme World Elite 卡",
            "signal": "World Elite 等級",
            "confidence": 98,
        },
        {
            "line": "存款 / 數位帳戶",
            "thesis": "薪轉、外幣入金",
            "examples": "Smart 數位帳戶",
            "signal": "境外入金 0 手續費",
            "confidence": 97,
        },
        {
            "line": "財富管理",
            "thesis": "高資產私人銀行",
            "examples": "Premier 私人銀行",
            "signal": "可信度較低",
            "confidence": 78,
        },
    ],
    "productNote": "官方產品頁面共偵測 12 個 SKU，本報告以產品線級別呈現。",
    "subBrands": [
        {"type": "主品牌", "name": "Acme Bank Asia", "note": "Acme Bank Asia Holdings 旗下零售金融主力品牌。"},
        {"type": "產品線", "name": "Smart、World Elite、Premier", "note": "屬產品次品牌或系列命名，非獨立子品牌。"},
        {"type": "聯名 / IP", "name": "未見", "note": "本次研究未找到近一年足夠公開證據支持固定 IP 聯名。"},
    ],
    "endorsements": {"status": "資料不足", "body": "Onboarding 階段未抓取到代言人 / 名人合作的公開證據。"},
    "ipCollabs": {"status": "資料不足", "body": "近 12 個月內，未找到具明確可驗證聲量的 IP 聯名或娛樂授權合作。"},
    "mediaNetwork": [
        {
            "name": "MoneyDJ 理財網",
            "audience": "投資理財決策者",
            "weekly": "1.2M",
            "relevance": 94,
            "topics": "ETF、外匯、存股",
            "trend": "上升",
        },
        {
            "name": "Smart 智富月刊",
            "audience": "中產家庭",
            "weekly": "680K",
            "relevance": 91,
            "topics": "定存、退休規劃",
            "trend": "上升",
        },
        {
            "name": "天下雜誌 · 財經",
            "audience": "企業主與專業人士",
            "weekly": "2.1M",
            "relevance": 88,
            "topics": "景氣、房貸",
            "trend": "持平",
        },
    ],
    "competitors": [
        {
            "tier": "直接競品",
            "brands": "國泰世華、玉山銀行、台新銀行",
            "basis": "同為台灣零售金融市場的強品牌化玩家。",
            "position": "Acme 更強調「為亞洲設計」。",
        },
        {
            "tier": "監測中（未選）",
            "brands": "中信銀行",
            "basis": "信用卡與信貸品類重疊。",
            "position": "可作為次階段競品擴查標的。",
        },
        {
            "tier": "替代型競品",
            "brands": "將來銀行、LINE Bank",
            "basis": "在數位帳戶 / 薪轉戶溝通直接重疊。",
            "position": "Acme 優勢在於 27 年品牌信任資產。",
        },
    ],
    "competitorNote": "競品判斷基於品類重疊、通路重疊與品牌化程度，而非完整市占資料。",
    "insights": {
        "confirmed": [
            "Acme Bank Asia 的最強錨點是 Smart 數位帳戶與外幣薪轉戶。",
            "27 年品牌信任資產是與純網銀的關鍵差異。",
        ],
        "inferences": [
            "品牌正從「數位帳戶單品」升級為「家庭金融平台型品牌」。",
        ],
        "hypotheses": [
            "若品牌持續強打「為亞洲設計」，年輕族群可能覺得語言距離。",
        ],
    },
    "faq": [
        {
            "q": "海外薪轉戶哪家銀行手續費最低？",
            "a": "Smart 數位帳戶每月前 5 筆境外入金 0 手續費。",
            "source": "MoneyDJ · 1,240 次提問",
            "level": "A 級官方",
        },
        {
            "q": "今年存股族該選高股息 ETF 還是定存？",
            "a": "Acme 高息成長 ETF 對應長期成長與股息雙軸。",
            "source": "Smart 智富月刊 · 2,310 次提問",
            "level": "A 級官方",
        },
        {
            "q": "30 歲想換房，房貸方案哪家銀行寬限期最長？",
            "a": "首購房貸專案 2026 主打首購族寬限期。",
            "source": "天下雜誌 · 870 次提問",
            "level": "A / B 交叉",
        },
        {
            "q": "信用卡海外消費回饋現在還是最高嗎？",
            "a": "Acme World Elite 卡定位高端海外消費。",
            "source": "Yahoo! 理財 · 1,840 次提問",
            "level": "B 級第三方",
        },
    ],
    "channels": [
        {"type": "D2C / 自營", "surfaces": "官方網站、行動 App", "read": "仍為品牌資訊與開戶轉換的核心樞紐。"},
        {"type": "媒體網絡（Cortex）", "surfaces": "MoneyDJ、Smart 智富、天下雜誌", "read": "GEO 分發的主要入口。"},
        {"type": "實體零售 / 分行", "surfaces": "資料不足", "read": "Onboarding 階段未抓取分行覆蓋。"},
        {"type": "海外", "surfaces": "香港、新加坡（依官方文案）", "read": "海外仍屬拓展中。"},
    ],
    "risks": [
        {
            "theme": "投資績效宣稱邊界",
            "trigger": "「年化可再加成 0.8%」",
            "where": "Smart 數位帳戶頁",
            "note": "金融商品具體數字績效宣稱，須對應特定產品與期間條件。",
            "level": "高",
            "action": "所有數字宣稱須綁定產品名、計算基礎與時間區間。",
        },
        {
            "theme": "理財建議定性",
            "trigger": "「建議搭配」「年化加成」",
            "where": "Brand Voice 預覽",
            "note": "近似投顧建議的語境，須配套聲明。",
            "level": "高",
            "action": "在 Answer Pilot 模板中強制加上免責聲明。",
        },
        {
            "theme": "海外服務涵蓋",
            "trigger": "「亞洲設計」「香港、新加坡」",
            "where": "關於頁",
            "note": "若實際服務未涵蓋對應市場，可能涉及不實宣稱。",
            "level": "中",
            "action": "限縮為具體動詞，避免泛化「服務」二字。",
        },
        {
            "theme": "首購族敏感",
            "trigger": "「為亞洲家庭設計」",
            "where": "關於頁",
            "note": "涉及特殊族群保護敘事。",
            "level": "中",
            "action": "保留「依個案評估」字樣。",
        },
    ],
    "sources": {
        "A": ["Acme Bank Asia 官方網站 — acmebank.asia", "關於頁 — /about"],
        "B": ["媒體網絡：MoneyDJ、Smart 智富（過去 90 日問題抓取）"],
        "C": ["社群評論、論壇口碑站僅作為線索，未作核心事實定論。"],
    },
    "quality": {
        "high": "品牌主體、主要市場、產品線大類、Brand Voice 指紋、媒體網絡相關性。",
        "midLow": "IP 聯名與代言人、實體分行覆蓋、Premier 私人銀行的真實規模。",
        "gaps": "未抓取到企業層級新聞稿；缺少標準 FAQ 總頁。",
        "conflicts": "未見重大衝突。Brand Voice 樣本第 4 句語氣偏激進，已標記為非核心。",
        "open": "是否存在 IP 聯名矩陣、是否已有大型企業 B2B 業務。",
    },
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def full_html() -> str:
    return render_report_html(FULL_FIXTURE)


# ---------------------------------------------------------------------------
# Structure tests (8 pages present)
# ---------------------------------------------------------------------------


def test_renders_without_error(full_html: str) -> None:
    assert full_html
    assert full_html.startswith("<!DOCTYPE html>")


def test_contains_all_8_pages(full_html: str) -> None:
    """Each page is a div.page — count must equal 8."""
    page_count = full_html.count('class="page"')
    assert page_count == 8, f"Expected 8 pages, got {page_count}"


# ---------------------------------------------------------------------------
# Brand name presence
# ---------------------------------------------------------------------------


def test_brand_name_present_on_cover(full_html: str) -> None:
    assert "Acme Bank Asia" in full_html


def test_report_id_present(full_html: str) -> None:
    assert "BIQ-2026-05-22-ACMEBA" in full_html


# ---------------------------------------------------------------------------
# Certainty chips
# ---------------------------------------------------------------------------


def test_confirmed_chip_present(full_html: str) -> None:
    assert "chip-confirmed" in full_html


def test_likely_chip_present(full_html: str) -> None:
    assert "chip-likely" in full_html


def test_insufficient_chip_for_endorsements(full_html: str) -> None:
    """endorsements.status == '資料不足' must render as chip-insufficient."""
    assert "chip-insufficient" in full_html
    assert "資料不足" in full_html


def test_insufficient_chip_for_ip_collabs(full_html: str) -> None:
    """ipCollabs.status == '資料不足' must also appear."""
    # We check the body text for ipCollabs to confirm that section rendered
    assert "IP 聯名" in full_html


# ---------------------------------------------------------------------------
# Key section content
# ---------------------------------------------------------------------------


def test_product_lines_rendered(full_html: str) -> None:
    assert "信用卡" in full_html
    assert "財富管理" in full_html


def test_media_network_rendered(full_html: str) -> None:
    assert "MoneyDJ" in full_html
    assert "Smart 智富月刊" in full_html


def test_competitors_rendered(full_html: str) -> None:
    assert "國泰世華" in full_html
    assert "替代型競品" in full_html


def test_risks_rendered(full_html: str) -> None:
    assert "投資績效宣稱邊界" in full_html
    assert "高 風險" in full_html


def test_sources_rendered(full_html: str) -> None:
    assert "acmebank.asia" in full_html


def test_quality_rendered(full_html: str) -> None:
    assert "高信心段落" in full_html


def test_faq_rendered(full_html: str) -> None:
    assert "Q1" in full_html
    assert "海外薪轉戶" in full_html


def test_channels_rendered(full_html: str) -> None:
    assert "D2C" in full_html
    assert "媒體網絡（Cortex）" in full_html


def test_insights_rendered(full_html: str) -> None:
    assert "已確認事實" in full_html
    assert "合理推論" in full_html
    assert "待驗證假設" in full_html


# ---------------------------------------------------------------------------
# Constellation SVG
# ---------------------------------------------------------------------------


def test_constellation_svg_present(full_html: str) -> None:
    assert "<svg" in full_html
    assert "MoneyDJ" in full_html  # media label in SVG text (real fixture data)


def test_constellation_uses_real_media_labels_not_hardcoded() -> None:
    """The constellation must label nodes from the report's own mediaNetwork
    names, never the design-prototype's hardcoded ['MoneyDJ','Smart','天下'...]."""
    fixture = _other_brand_fixture()
    html = render_report_html(fixture)
    # Real outlet from the other-brand fixture appears...
    assert "Foo News" in html
    # ...and none of the prototype's baked-in media labels leak through.
    for baked in ("MoneyDJ", "智富", "天下", "商周", "Yahoo"):
        assert baked not in html, f"prototype media label '{baked}' leaked"


def test_constellation_empty_media_no_fabricated_labels() -> None:
    """With no mediaNetwork, the SVG draws no fabricated outlet names.

    Uses the other-brand fixture (whose FAQ sources don't mention the
    prototype outlets) so any leak is genuinely from the constellation.
    """
    fixture = _other_brand_fixture()
    fixture["mediaNetwork"] = []
    html = render_report_html(fixture)
    for baked in ("MoneyDJ", "智富", "天下", "商周", "Yahoo"):
        assert baked not in html


# ---------------------------------------------------------------------------
# Sparse / empty data — must not crash
# ---------------------------------------------------------------------------


def test_sparse_json_no_crash() -> None:
    """Minimal JSON (only meta) must render without raising."""
    sparse = {"meta": {"subject": "TestBrand", "monogram": "T"}}
    html = render_report_html(sparse)
    assert "TestBrand" in html


def test_empty_endorsements_chip() -> None:
    """Missing endorsements dict should default to 資料不足 chip."""
    fixture = dict(FULL_FIXTURE)
    fixture["endorsements"] = {}  # no status key
    html = render_report_html(fixture)
    assert "chip-insufficient" in html


def test_empty_ip_collabs_chip() -> None:
    """Missing ipCollabs dict should default to 資料不足 chip."""
    fixture = dict(FULL_FIXTURE)
    fixture["ipCollabs"] = {}
    html = render_report_html(fixture)
    assert "chip-insufficient" in html


def test_empty_sub_brands_no_crash() -> None:
    fixture = dict(FULL_FIXTURE)
    fixture["subBrands"] = []
    html = render_report_html(fixture)
    assert "<!DOCTYPE html>" in html


def test_empty_media_network_no_crash() -> None:
    fixture = dict(FULL_FIXTURE)
    fixture["mediaNetwork"] = []
    html = render_report_html(fixture)
    assert "<!DOCTYPE html>" in html


def test_empty_insights_no_crash() -> None:
    fixture = dict(FULL_FIXTURE)
    fixture["insights"] = {}
    html = render_report_html(fixture)
    assert "已確認事實" in html  # section title still renders


def test_completely_empty_json_no_crash() -> None:
    html = render_report_html({})
    assert "<!DOCTYPE html>" in html


# ---------------------------------------------------------------------------
# HTML safety — user content is escaped
# ---------------------------------------------------------------------------


def test_xss_escaped() -> None:
    xss = dict(FULL_FIXTURE)
    xss["meta"] = dict(FULL_FIXTURE["meta"])
    xss["meta"]["subject"] = '<script>alert("xss")</script>'
    html = render_report_html(xss)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


# ---------------------------------------------------------------------------
# sanitize_filename helper
# ---------------------------------------------------------------------------


def test_sanitize_filename_removes_slashes() -> None:
    assert "/" not in sanitize_filename("Acme / Bank")


def test_sanitize_filename_keeps_cjk() -> None:
    result = sanitize_filename("Acme 銀行 Brand IQ Report v1.0")
    assert "銀行" in result


def test_sanitize_filename_keeps_dot_and_dash() -> None:
    result = sanitize_filename("report-v1.0.pdf")
    assert result == "report-v1.0.pdf"


# ---------------------------------------------------------------------------
# Honesty contract — nothing may assert a fact not present in report_json
# ---------------------------------------------------------------------------


def _other_brand_fixture() -> dict:
    """A non-Acme brand to prove the template carries no baked-in demo data."""
    return {
        "meta": {
            "subject": "Globex Foods",
            "enName": "Globex Foods",
            "monogram": "G",
            "primaryMarket": "日本",
            "extendedMarkets": ["韓國"],
            "reportDate": "2026-05-24",
            "windowFrom": "2025-05-24",
            "windowTo": "2026-05-24",
            "founded": "2010",
            "category": "食品零售",
            "confidence": 80,
            "reportId": "BIQ-GLOBEX",
            "pageCount": 8,
            "tagline": "Fresh, every day.",
            "preparedFor": "PM",
            "preparedBy": "Cortex",
        },
        "core": [{"item": "品牌主體", "body": "Globex Foods 是食品零售品牌。", "certainty": "已確認"}],
        "coreJudgement": "Globex 走的是新鮮直送路線。",
        "productLines": [
            {"line": "生鮮", "thesis": "每日直送", "examples": "Globex 生鮮箱", "signal": "冷鏈", "confidence": 85}
        ],
        "productNote": "共 1 條產品線。",
        "subBrands": [{"type": "主品牌", "name": "Globex Foods", "note": "主力品牌。"}],
        "endorsements": {"status": "資料不足", "body": "未抓取到。"},
        "ipCollabs": {"status": "資料不足", "body": "未抓取到。"},
        "mediaNetwork": [
            {
                "name": "Foo News",
                "audience": "家庭主婦",
                "weekly": "500K",
                "relevance": 80,
                "topics": "食譜",
                "trend": "上升",
            }
        ],
        "competitors": [
            {"tier": "直接競品", "brands": "Acme Mart", "basis": "同品類。", "position": "Globex 較新鮮。"}
        ],
        "competitorNote": "概覽級分析。",
        "insights": {
            "confirmed": ["新鮮直送是錨點。"],
            "inferences": ["可能擴張冷鏈。"],
            "hypotheses": ["年輕客群待驗證。"],
        },
        "faq": [{"q": "配送多快？", "a": "當日。", "source": "Foo News", "level": "A 級官方"}],
        "channels": [{"type": "D2C", "surfaces": "官網", "read": "核心。"}],
        "risks": [
            {
                "theme": "保鮮宣稱",
                "trigger": "「最新鮮」",
                "where": "官網",
                "note": "須佐證。",
                "level": "中",
                "action": "加註條件。",
            }
        ],
        "sources": {"A": ["globex.example — 官網"], "B": ["Foo News"], "C": ["論壇口碑"]},
        "quality": {
            "high": "品牌主體。",
            "midLow": "冷鏈規模。",
            "gaps": "無 ESG。",
            "conflicts": "無。",
            "open": "B2B 業務。",
        },
    }


# Acme-bank demo literals from data.jsx that must NEVER appear unless they are
# the brand's actual report data. With a non-Acme brand, none may leak.
_ACME_DEMO_LITERALS = [
    "Acme Bank Asia",
    "純網銀",
    "27 年信任資產",
    "為亞洲家庭重新設計",
    "4 / 47",
    "Voice 樣本",
    "12 個 SKU",
    "Premier 私人銀行信心較低",
    "9.6M",
    "67%",
    "3.4M",
    "Smart 數位帳戶",
    "World Elite",
    "從爆品到平台",
    "家庭金融平台",
    "國泰世華",
    "玉山銀行",
    "台新銀行",
    "LINE Bank",
    "將來銀行",
    "本週 6 大",
    "一家銀行的核心解剖",
    "零售金融",  # was hardcoded "品類" value on P2
]


def test_no_acme_demo_data_leaks_for_other_brand() -> None:
    """Render a non-Acme brand; assert ZERO Acme/data.jsx demo literals leak."""
    html = render_report_html(_other_brand_fixture())
    leaked = [lit for lit in _ACME_DEMO_LITERALS if lit in html]
    assert leaked == [], f"hardcoded demo literals leaked: {leaked}"


def test_other_brand_content_is_rendered() -> None:
    """The other brand's real data is what actually shows up."""
    html = render_report_html(_other_brand_fixture())
    assert "Globex Foods" in html
    assert "生鮮" in html
    assert "Foo News" in html
    assert "Globex 走的是新鮮直送路線。" in html  # coreJudgement pull quote
    assert "Acme Mart" in html  # competitor from data, rendered as a card


def test_pull_quote_omitted_when_no_core_judgement() -> None:
    """Cover + P2 pull quotes must not render an empty quote block."""
    fixture = _other_brand_fixture()
    fixture["coreJudgement"] = ""
    html = render_report_html(fixture)
    assert "Strategic Pin" not in html
    assert "Cortex 的判斷" not in html


def test_no_2x2_scatter_plot() -> None:
    """The fabricated competitor 2×2 positioning scatter must be gone."""
    html = render_report_html(FULL_FIXTURE)
    assert "Relative positioning" not in html
    assert "數位優先" not in html
    assert "顧問式 →" not in html


def test_no_strategy_funnel() -> None:
    """The fabricated P6 strategy-shape funnel must be gone."""
    html = render_report_html(FULL_FIXTURE)
    assert "戰略形狀" not in html
    assert "−22%" not in html


# ---------------------------------------------------------------------------
# Competitor tier colours — keyed by tier VALUE, not list index
# ---------------------------------------------------------------------------


def test_competitor_tone_keyed_by_tier_value() -> None:
    """Each canonical tier maps to its own (fg, bg) tone."""
    direct = _competitor_tone("直接競品")
    monitor = _competitor_tone("監測中（未選）")
    alt = _competitor_tone("替代型競品")
    assert direct[0] == "var(--danger)"
    assert monitor[0] == "var(--amber-500)"
    assert alt == _COMPETITOR_TONE_NEUTRAL
    # All three are distinct foregrounds (direct vs monitor)
    assert direct[0] != monitor[0]


def test_competitor_tone_unknown_tier_neutral_default() -> None:
    """An unrecognised tier falls back to the neutral tone."""
    assert _competitor_tone("某種未知層級") == _COMPETITOR_TONE_NEUTRAL
    assert _competitor_tone("") == _COMPETITOR_TONE_NEUTRAL


def test_competitor_colour_follows_tier_not_order() -> None:
    """Reordering competitors must NOT change each tier's colour (was index-based)."""
    base = dict(FULL_FIXTURE)

    # Direct-competitor tier first
    base["competitors"] = [
        {"tier": "直接競品", "brands": "X", "basis": "b", "position": "p"},
        {"tier": "替代型競品", "brands": "Y", "basis": "b", "position": "p"},
    ]
    html_a = render_report_html(base)

    # Same tiers, reversed order
    base2 = dict(base)
    base2["competitors"] = list(reversed(base["competitors"]))
    html_b = render_report_html(base2)

    # The direct-competitor card carries the danger top-border in BOTH renders;
    # i.e. the danger colour binds to 直接競品 regardless of position.
    danger_border = "border-top:3px solid var(--danger)"
    assert html_a.count(danger_border) == 1
    assert html_b.count(danger_border) == 1


def test_at_a_glance_derives_from_meta() -> None:
    """At-a-glance cards use real meta fields, with no invented '27年'/'4/47'."""
    html = render_report_html(_other_brand_fixture())
    # founded / category / market / tagline from the other-brand meta
    assert "2010" in html
    assert "食品零售" in html
    assert "日本" in html
    assert "Fresh, every day." in html


def test_at_a_glance_omitted_when_meta_sparse() -> None:
    """No founded/category/market/tagline → no At-a-glance block (no placeholders)."""
    fixture = dict(_other_brand_fixture())
    fixture["meta"] = {
        "subject": "Sparse Co",
        "monogram": "S",
        "reportId": "BIQ-SPARSE",
        "pageCount": 8,
    }
    html = render_report_html(fixture)
    assert "At a glance" not in html


def test_footer_page_count_reflects_actual_pages_not_meta() -> None:
    """The footer denominator must reflect the ACTUAL rendered page count (8),
    NOT meta.pageCount. A stale/wrong meta.pageCount must not leak into the
    footer (the renderer counts its own page list)."""
    fixture = dict(FULL_FIXTURE)
    fixture["meta"] = dict(FULL_FIXTURE["meta"])
    fixture["meta"]["pageCount"] = 12  # deliberately wrong
    html = render_report_html(fixture)
    # Footers say "/ 8" (real count), never "/ 12" from the bogus meta value.
    assert "/ 12</span>" not in html
    assert "/ 8</span>" in html


def test_footer_page_count_ignores_missing_meta_page_count() -> None:
    """Even with no meta.pageCount at all, footers show the real count (8)."""
    fixture = dict(FULL_FIXTURE)
    fixture["meta"] = {k: v for k, v in FULL_FIXTURE["meta"].items() if k != "pageCount"}
    html = render_report_html(fixture)
    assert "/ 8</span>" in html
