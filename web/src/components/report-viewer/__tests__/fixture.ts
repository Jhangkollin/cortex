/**
 * BRAND_IQ fixture for report-viewer tests.
 * Mirrors the prototype's data.jsx exactly so tests validate real-world data shapes.
 */
import type { BrandIqReport } from "@/lib/cortex-api";

export const BRAND_IQ_FIXTURE: BrandIqReport = {
  meta: {
    subject: "Acme Bank Asia",
    enName: "Acme Bank Asia",
    legalName: "Acme Bank Asia Holdings, Ltd.",
    domain: "acmebank.asia",
    primaryMarket: "台灣",
    extendedMarkets: ["香港", "新加坡"],
    reportDate: "2026-05-22",
    windowFrom: "2025-05-22",
    windowTo: "2026-05-22",
    monogram: "A",
    brandColor: "#225D59",
    tagline: "Banking, redesigned for Asia.",
    founded: "1998",
    category: "零售金融 / 數位銀行",
    confidence: 96,
    reportId: "BIQ-2026-05-22-ACMEBA",
    pageCount: 8,
    preparedFor: "Marketing Manager · Brand Account",
    preparedBy: "Cortex · Brand Agent v3.2",
  },
  core: [
    {
      item: "品牌主體",
      body: "Acme Bank Asia 為 Acme Bank Asia Holdings, Ltd. 旗下零售金融與數位銀行品牌。",
      certainty: "已確認",
    },
    {
      item: "成立脈絡",
      body: "據官方關於頁，Acme Bank Asia 於 1998 年成立，27 年來服務超過 320 萬家庭與企業。",
      certainty: "已確認",
    },
    {
      item: "主要市場",
      body: "主市場為台灣；官方明確支援香港與新加坡的延伸服務。",
      certainty: "已確認",
    },
    {
      item: "品牌定位",
      body: "核心話術集中在「為亞洲設計」「值得信賴的對話」「為人服務的銀行」。",
      certainty: "已確認",
    },
    {
      item: "Brand Voice",
      body: "4 句訓練樣本中 3 句符合品牌指紋。",
      certainty: "高可能",
    },
  ],
  coreJudgement:
    "Acme Bank Asia 並非單純走數位銀行敘事，而是把「亞洲在地」「顧問式關係」「家庭信任」三條線並置。",
  productLines: [
    {
      line: "信用卡",
      thesis: "高端消費、海外回饋",
      examples: "Acme World Elite 卡",
      signal: "World Elite 等級、海外回饋為主訴求",
      confidence: 98,
    },
    {
      line: "存款 / 數位帳戶",
      thesis: "薪轉、外幣入金、零手續費",
      examples: "Smart 數位帳戶",
      signal: "境外入金 0 手續費",
      confidence: 97,
    },
    {
      line: "房貸",
      thesis: "首購族與寬限期",
      examples: "首購房貸專案 2026",
      signal: "與首購族購屋情境綁定",
      confidence: 94,
    },
    {
      line: "投資 / ETF",
      thesis: "高息與成長雙軸",
      examples: "Acme 高息成長 ETF",
      signal: "存股族 + 退休規劃語境",
      confidence: 92,
    },
    {
      line: "外匯",
      thesis: "外幣綜合存款",
      examples: "外幣綜合存款",
      signal: "薪轉外幣戶交叉銷售",
      confidence: 91,
    },
    {
      line: "信貸",
      thesis: "薪轉戶優惠",
      examples: "信用貸款・薪轉戶優惠",
      signal: "與薪轉產品交叉銷售",
      confidence: 88,
    },
    {
      line: "財富管理",
      thesis: "高資產私人銀行",
      examples: "Premier 私人銀行",
      signal: "可信度較低",
      confidence: 78,
    },
  ],
  productNote:
    "官方產品頁面共偵測 12 個 SKU，本報告以產品線級別呈現。",
  subBrands: [
    { type: "主品牌", name: "Acme Bank Asia", note: "Acme Bank Asia Holdings 旗下零售金融主力品牌。" },
    { type: "產品線", name: "Smart、World Elite、Premier", note: "屬產品次品牌或系列命名。" },
    { type: "聯名 / IP", name: "未見", note: "本次研究未找到近一年足夠公開證據。" },
  ],
  endorsements: {
    status: "資料不足",
    body: "Onboarding 階段未抓取到代言人 / 名人合作的公開證據。",
  },
  ipCollabs: {
    status: "資料不足",
    body: "近 12 個月內，未找到 Acme Bank Asia 具明確可驗證聲量的 IP 聯名。",
  },
  mediaNetwork: [
    { name: "MoneyDJ 理財網", audience: "投資理財決策者", weekly: "1.2M", relevance: 94, topics: "ETF、外匯、存股", trend: "上升" },
    { name: "Smart 智富月刊", audience: "中產家庭・規劃中", weekly: "680K", relevance: 91, topics: "定存、退休規劃", trend: "上升" },
    { name: "天下雜誌 · 財經", audience: "企業主與專業人士", weekly: "2.1M", relevance: 88, topics: "景氣、房貸", trend: "持平" },
    { name: "商業周刊", audience: "管理階層・40+", weekly: "1.7M", relevance: 84, topics: "信用卡、高資產", trend: "上升" },
    { name: "TechOrange", audience: "科技工作者", weekly: "540K", relevance: 76, topics: "數位帳戶、支付", trend: "上升" },
    { name: "Yahoo! 奇摩 · 理財", audience: "大眾消費者", weekly: "3.4M", relevance: 72, topics: "信用卡回饋、貸款", trend: "持平" },
  ],
  competitors: [
    {
      tier: "直接競品",
      brands: "國泰世華、玉山銀行、台新銀行",
      basis: "同為台灣零售金融與信用卡市場的強品牌化玩家。",
      position: "Acme 更強調「為亞洲設計」與顧問式溝通。",
    },
    {
      tier: "監測中（未選）",
      brands: "中信銀行",
      basis: "信用卡與信貸品類重疊。",
      position: "可作為次階段競品擴查標的。",
    },
    {
      tier: "替代型競品",
      brands: "將來銀行、LINE Bank、純網銀群",
      basis: "在數位帳戶 / 薪轉戶溝通直接重疊。",
      position: "Acme 優勢在於 27 年品牌信任資產。",
    },
  ],
  competitorNote: "競品判斷基於品類重疊、通路重疊與品牌化程度，屬概覽級分析。",
  insights: {
    confirmed: [
      "Acme Bank Asia 的最強錨點是 Smart 數位帳戶與外幣薪轉戶。",
      "27 年品牌信任資產是與純網銀的關鍵差異。",
      "產品結構已從單點存款，擴張到多品類布局。",
    ],
    inferences: [
      "品牌正從「數位帳戶單品」升級為「家庭金融平台型品牌」。",
      "外幣薪轉戶可望成為流量入口。",
      "海外策略更像「華語市場的漸進擴張」。",
    ],
    hypotheses: [
      "若持續強打「為亞洲設計」，年輕族群可能覺得語言距離。",
      "若實體分行擴大，品牌語氣可能需要調整。",
    ],
  },
  faq: [
    { q: "海外薪轉戶哪家銀行手續費最低？", a: "Smart 數位帳戶每月前 5 筆境外入金 0 手續費。", source: "MoneyDJ", level: "A 級官方" },
    { q: "今年存股族該選高股息 ETF 還是定存？", a: "Acme 高息成長 ETF 對應長期成長。", source: "Smart 智富月刊", level: "A 級官方" },
    { q: "30 歲想換房，房貸方案哪家銀行寬限期最長？", a: "首購房貸專案 2026 主打首購族寬限期。", source: "天下雜誌", level: "A / B 交叉" },
    { q: "信用卡海外消費回饋現在還是最高嗎？", a: "Acme World Elite 卡定位高端海外消費。", source: "Yahoo! 理財", level: "B 級第三方" },
    { q: "數位帳戶開戶要綁哪些券商比較順？", a: "Smart 數位帳戶開放跨券商連結。", source: "TechOrange", level: "A / B 交叉" },
    { q: "美元定存利率比新台幣高很多，要不要全部換過去？", a: "建議以外幣綜合存款做匯率平均成本。", source: "MoneyDJ", level: "A 級官方" },
  ],
  channels: [
    { type: "D2C / 自營", surfaces: "官方網站、行動 App、LINE 導購入口", read: "仍為品牌資訊與開戶轉換的核心樞紐。" },
    { type: "媒體網絡（Cortex）", surfaces: "MoneyDJ、Smart 智富、天下雜誌等 6 家", read: "GEO 分發的主要入口。" },
    { type: "實體零售 / 分行", surfaces: "資料不足", read: "建議向客戶確認據點。" },
    { type: "海外", surfaces: "香港、新加坡（依官方文案）", read: "海外仍屬拓展中。" },
  ],
  risks: [
    {
      theme: "投資績效宣稱邊界",
      trigger: "「年化可再加成 0.8%」「優於市場 12 個基點」",
      note: "金融商品具體數字績效宣稱，須對應特定產品與期間條件。",
      level: "高",
      action: "所有數字宣稱須綁定產品名、計算基礎與時間區間。",
    },
    {
      theme: "理財建議定性",
      trigger: "「建議搭配」「年化加成」",
      note: "近似投顧建議的語境。",
      level: "高",
      action: "在 Answer Pilot 模板中強制加上免責聲明。",
    },
    {
      theme: "海外服務涵蓋",
      trigger: "「亞洲設計」「香港、新加坡」",
      note: "若實際服務未涵蓋對應市場，可能涉及不實宣稱。",
      level: "中",
      action: "限縮為具體動詞，避免泛化「服務」二字。",
    },
    {
      theme: "首購族 / 銀髮族敏感",
      trigger: "「為亞洲家庭設計」「27 年家庭信任」",
      note: "涉及特殊族群保護敘事。",
      level: "中",
      action: "在房貸與退休理財文案中保留諮詢字樣。",
    },
  ],
  sources: {
    A: [
      "Acme Bank Asia 官方網站 — acmebank.asia",
      "關於頁 — /about",
      "Smart 數位帳戶商品頁 — /accounts/smart",
    ],
    B: [
      "媒體網絡：MoneyDJ、Smart 智富等（過去 90 日問題抓取）",
      "競品比對：國泰世華、玉山、台新（金管會公開資料）",
    ],
    C: ["社群評論、論壇口碑站僅作為線索，未作核心事實定論。"],
  },
  quality: {
    high: "品牌主體、主要市場、產品線大類、Brand Voice 指紋。",
    midLow: "IP 聯名與代言人、實體分行覆蓋、Premier 私人銀行的真實規模。",
    gaps: "未抓取到企業層級新聞稿；缺少標準 FAQ 總頁。",
    conflicts: "未見重大衝突。Brand Voice 樣本第 4 句語氣偏激進。",
    open: "是否存在 IP 聯名矩陣、各主力 SKU 真實銷售排名。",
  },
};
