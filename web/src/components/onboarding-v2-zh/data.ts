/**
 * Mock data backing the v2 onboarding journey (zh-Hant).
 *
 * Mirrors src/components/onboarding-v2/data.ts with the original design's
 * Traditional Chinese copy. Everything is client-only.
 */

export type CrawlTask = {
  id: string;
  label: string;
  detail: string;
  icon: string;
  delay: number;
};

export const CRAWL_TASKS: CrawlTask[] = [
  { id: "fetch", label: "讀取首頁", detail: "acmebank.asia · 200 OK", icon: "language", delay: 600 },
  { id: "meta", label: "抓取 metadata", detail: "title, og:image, schema.org", icon: "code", delay: 700 },
  { id: "logo", label: "辨識品牌標誌", detail: "Logo / favicon / Apple touch", icon: "interests", delay: 800 },
  { id: "products", label: "掃描產品頁", detail: "解析 12 個產品頁", icon: "category", delay: 1000 },
  { id: "category", label: "推斷品類", detail: "零售金融 / 數位銀行 · 96% 信心", icon: "psychology", delay: 700 },
  { id: "voice", label: "擷取 Brand Voice", detail: "從關於頁、新聞稿取 47 句樣本", icon: "campaign", delay: 800 },
  { id: "competitors", label: "比對競品", detail: "媒體網絡同品類 4 家", icon: "groups", delay: 700 },
  { id: "done", label: "完成", detail: "所有資料可在下一步修改", icon: "task_alt", delay: 600 },
];

export type Product = {
  id: string;
  name: string;
  category: string;
  url: string;
  icon: string;
  picked: boolean;
  confidence: number;
};

export type VoiceSample = {
  src: string;
  text: string;
  picked: boolean;
};

export type Competitor = {
  id: string;
  name: string;
  domain: string;
  picked: boolean;
  matchScore: number;
};

export type ExtractedBrand = {
  url: string;
  name: string;
  legalName: string;
  tagline: string;
  monogram: string;
  brandColor: string;
  category: { value: string; confidence: number; alternatives: string[] };
  region: string[];
  founded: string;
  about: string;
  voiceSamples: VoiceSample[];
  products: Product[];
  productMoreCount: number;
  competitors: Competitor[];
};

export const EXTRACTED_BRAND: ExtractedBrand = {
  url: "acmebank.asia",
  name: "Acme Bank Asia",
  legalName: "Acme Bank Asia Holdings, Ltd.",
  tagline: "為亞洲量身重塑的銀行體驗。",
  monogram: "A",
  brandColor: "#225D59",
  category: {
    value: "零售金融 / 數位銀行",
    confidence: 96,
    alternatives: ["金融服務", "FinTech 平台"],
  },
  region: ["台灣", "香港", "新加坡"],
  founded: "1998",
  about:
    "27 年來，Acme Bank Asia 在亞洲協助超過 320 萬家庭與企業，把銀行體驗從繁瑣的流程，重新設計成一段值得信賴的對話。",
  voiceSamples: [
    { src: "/about", text: "我們相信銀行該為人服務，而不是反過來。", picked: true },
    { src: "/press/2025-q4", text: "每一筆財務決定，背後都該有一位顧問。", picked: true },
    { src: "/blog/asia-2026", text: "亞洲的下一代成長動能，來自不被服務的中段消費者。", picked: false },
    { src: "/about", text: "27 年來，我們在亞洲協助超過 320 萬家庭。", picked: true },
  ],
  products: [
    { id: "p1", name: "Acme World Elite 卡", category: "信用卡", url: "/credit-cards/world-elite", icon: "credit_card", picked: true, confidence: 98 },
    { id: "p2", name: "Smart 數位帳戶", category: "存款", url: "/accounts/smart", icon: "savings", picked: true, confidence: 97 },
    { id: "p3", name: "首購房貸專案 2026", category: "房貸", url: "/mortgages/first-home", icon: "home_work", picked: true, confidence: 94 },
    { id: "p4", name: "Acme 高息成長 ETF", category: "投資", url: "/investments/etf-growth", icon: "trending_up", picked: true, confidence: 92 },
    { id: "p5", name: "外幣綜合存款", category: "外匯", url: "/accounts/fx", icon: "currency_exchange", picked: true, confidence: 91 },
    { id: "p6", name: "信用貸款・薪轉戶優惠", category: "信貸", url: "/loans/salary", icon: "request_quote", picked: true, confidence: 88 },
    { id: "p7", name: "Premier 私人銀行", category: "財富", url: "/private/premier", icon: "diamond", picked: false, confidence: 78 },
  ],
  productMoreCount: 5,
  competitors: [
    { id: "c1", name: "國泰世華", domain: "cathaybk.com.tw", picked: true, matchScore: 94 },
    { id: "c2", name: "玉山銀行", domain: "esunbank.com.tw", picked: true, matchScore: 91 },
    { id: "c3", name: "台新銀行", domain: "taishinbank.com.tw", picked: true, matchScore: 88 },
    { id: "c4", name: "中信銀行", domain: "ctbcbank.com", picked: false, matchScore: 84 },
  ],
};

export type Media = {
  id: string;
  name: string;
  audience: string;
  weeklyReaders: number | null;
  contextAgent: string;
  relevance: number;
  picked: boolean;
  topics: string[];
  trend: "up" | "down" | "flat";
};

export const MEDIA_NETWORK: Media[] = [
  { id: "moneydj", name: "MoneyDJ 理財網", audience: "投資理財決策者", weeklyReaders: 1_200_000, contextAgent: "投資理財脈絡", relevance: 94, picked: true, topics: ["ETF", "外匯", "存股"], trend: "up" },
  { id: "smart", name: "Smart 智富月刊", audience: "中產家庭・規劃中", weeklyReaders: 680_000, contextAgent: "財富規劃脈絡", relevance: 91, picked: true, topics: ["定存", "退休規劃", "保險"], trend: "up" },
  { id: "cw", name: "天下雜誌 · 財經", audience: "企業主與專業人士", weeklyReaders: 2_100_000, contextAgent: "總體財經脈絡", relevance: 88, picked: true, topics: ["景氣", "房貸", "企業金融"], trend: "flat" },
  { id: "bw", name: "商業周刊", audience: "管理階層・40+", weeklyReaders: 1_700_000, contextAgent: "商業決策脈絡", relevance: 84, picked: true, topics: ["信用卡", "高資產"], trend: "up" },
  { id: "techorange", name: "TechOrange", audience: "科技工作者", weeklyReaders: 540_000, contextAgent: "金融科技脈絡", relevance: 76, picked: true, topics: ["數位帳戶", "支付", "API"], trend: "up" },
  { id: "yahoo", name: "Yahoo! 奇摩 · 理財", audience: "大眾消費者", weeklyReaders: 3_400_000, contextAgent: "大眾消費脈絡", relevance: 72, picked: true, topics: ["信用卡回饋", "貸款"], trend: "flat" },
  { id: "ctee", name: "工商時報", audience: "商業決策者", weeklyReaders: 890_000, contextAgent: "企業金融脈絡", relevance: 68, picked: false, topics: ["企業貸", "外匯避險"], trend: "down" },
  { id: "stockfeel", name: "StockFeel 股感", audience: "年輕投資者", weeklyReaders: 420_000, contextAgent: "零售投資脈絡", relevance: 64, picked: false, topics: ["新手投資", "ETF"], trend: "up" },
];

export type LiveQuestion = {
  id: string;
  text: string;
  media: string;
  intent: "Explore" | "Understand" | "Evaluate" | "Act";
  score: number;
  asks: number;
  when: string;
  competitorMentions: string[];
};

export const LIVE_QUESTIONS: LiveQuestion[] = [
  { id: "q1", text: "海外薪轉戶哪家銀行手續費最低、又能直接換匯入金？", media: "MoneyDJ 理財網", intent: "Evaluate", score: 92, asks: 1240, when: "2 小時前", competitorMentions: ["國泰世華", "中信"] },
  { id: "q2", text: "今年存股族該選高股息 ETF 還是定存？我怕利率反轉", media: "Smart 智富月刊", intent: "Understand", score: 88, asks: 2310, when: "5 小時前", competitorMentions: ["元大", "國泰"] },
  { id: "q3", text: "30 歲想換房，房貸方案哪家銀行寬限期最長？", media: "天下雜誌", intent: "Act", score: 86, asks: 870, when: "今天 09:14", competitorMentions: ["玉山", "台新"] },
  { id: "q4", text: "信用卡海外消費回饋現在還是國泰最高嗎？", media: "Yahoo! 理財", intent: "Evaluate", score: 81, asks: 1840, when: "昨天", competitorMentions: ["國泰世華"] },
  { id: "q5", text: "數位帳戶開戶要綁哪些券商比較順？", media: "TechOrange", intent: "Explore", score: 74, asks: 620, when: "2 天前", competitorMentions: ["將來銀行"] },
  { id: "q6", text: "美元定存利率比新台幣高很多，要不要全部換過去？", media: "MoneyDJ 理財網", intent: "Understand", score: 82, asks: 990, when: "4 小時前", competitorMentions: ["國泰", "台新"] },
];

export const INTENT_COLOR = {
  Explore: { bg: "#E0F2F1", fg: "#00695C" },
  Understand: { bg: "#E3F2FD", fg: "#0D47A1" },
  Evaluate: { bg: "#FFF8E1", fg: "#8D6E00" },
  Act: { bg: "#FFEBEE", fg: "#B71C1C" },
} as const;

// zh-Hant labels for the four reader intents — used by IntentPill in the
// pill chrome and by the filter chips in StepQuestions. Keys are the same
// as INTENT_COLOR (and the LiveQuestion.intent union) so a typo here trips
// at compile time.
export const INTENT_LABEL_ZH: Record<keyof typeof INTENT_COLOR, string> = {
  Explore: "探索",
  Understand: "了解",
  Evaluate: "評估",
  Act: "行動",
};

// Light Edition (2026-05-27): trimmed demo list to the two brands the
// prototype actually validates against (handoff Appendix C). When a real
// hot-brand API lands, source from the backend instead.
export const URL_SUGGESTIONS = ["mlytics.com", "moonbeam.io"];

export type VoiceTone = {
  id: "expert" | "warm" | "playful";
  label: string;
  desc: string;
  icon: string;
  sample: string;
};

export const VOICE_TONES: VoiceTone[] = [
  {
    id: "expert",
    label: "專業顧問",
    desc: "客觀、數據驅動",
    icon: "school",
    sample:
      "如果您每月薪資以美元或人民幣入帳，Acme Bank Asia 的 Smart 數位帳戶提供前 5 筆境外轉入 0 手續費，搭配即時匯率優於市場 12 個基點。對於月薪 5 萬美元以上的薪轉戶，建議搭配「外幣綜合存款」做匯率平均成本，年化可再加成 0.8%。",
  },
  {
    id: "warm",
    label: "溫暖陪伴",
    desc: "親近、有同理心",
    icon: "favorite",
    sample:
      "如果你每個月領的是外幣薪水，會擔心換匯的手續費吃掉一筆——這很正常。Acme 的 Smart 數位帳戶每月前 5 筆境外入金免手續費，匯率比市面好上一點點，對長期薪轉的人來說，一年下來省下的金額其實會讓你有感。",
  },
  {
    id: "playful",
    label: "活潑直白",
    desc: "年輕、口語化",
    icon: "celebration",
    sample:
      "嘿，海外薪轉最怕的就是『換匯被剝一層皮』。Acme Smart 數位帳戶每月前 5 筆境外入金 0 手續費，匯率還偏甜，懶得算的話直接用就對了——它幫你省的，就是別人在計較的。",
  },
];

export type DeployAgent = {
  id: string;
  name: string;
  kind: "context" | "core";
  icon: string;
};

export const DEPLOY_AGENTS: DeployAgent[] = [
  { id: "context-moneydj", name: "上下文代理 · MoneyDJ", kind: "context", icon: "hub" },
  { id: "context-smart", name: "上下文代理 · Smart 智富", kind: "context", icon: "hub" },
  { id: "context-cw", name: "上下文代理 · 天下雜誌", kind: "context", icon: "hub" },
  { id: "context-bw", name: "上下文代理 · 商業周刊", kind: "context", icon: "hub" },
  { id: "context-tech", name: "上下文代理 · TechOrange", kind: "context", icon: "hub" },
  { id: "context-yahoo", name: "上下文代理 · Yahoo! 理財", kind: "context", icon: "hub" },
  { id: "answer-pilot", name: "Answer Pilot", kind: "core", icon: "edit_note" },
  { id: "geo-pilot", name: "GEO Pilot · 媒體分發", kind: "core", icon: "explore" },
  { id: "monetize-lens", name: "Monetize Lens · 點擊歸因", kind: "core", icon: "insights" },
  { id: "market-radar", name: "Market Radar · 競品監測", kind: "core", icon: "radar" },
];

export type DeployLogLine = { t: string; text: string; status: "OK" | "DONE" };

export const DEPLOY_LOG: DeployLogLine[] = [
  { t: "+00s", text: "授權上下文代理存取媒體網絡 API…", status: "OK" },
  { t: "+01s", text: "上傳 Brand Profile：Acme Bank Asia", status: "OK" },
  { t: "+02s", text: "載入 6 個產品的知識卡 (KB)", status: "OK" },
  { t: "+03s", text: "校準 Brand Voice 指紋（4 句訓練樣本）", status: "OK" },
  { t: "+05s", text: "部署 上下文代理 · MoneyDJ → ap-tw-1", status: "OK" },
  { t: "+06s", text: "部署 上下文代理 · Smart 智富 → ap-tw-1", status: "OK" },
  { t: "+07s", text: "部署 上下文代理 · 天下雜誌 → ap-tw-1", status: "OK" },
  { t: "+08s", text: "部署 上下文代理 · 商業周刊 → ap-tw-1", status: "OK" },
  { t: "+09s", text: "部署 上下文代理 · TechOrange → ap-tw-1", status: "OK" },
  { t: "+10s", text: "部署 上下文代理 · Yahoo! → ap-tw-2", status: "OK" },
  { t: "+12s", text: "Answer Pilot 待命 · 訂閱本週問題佇列", status: "OK" },
  { t: "+13s", text: "GEO Pilot 連線 · 4 媒體分發通道", status: "OK" },
  { t: "+14s", text: "Monetize Lens 上線 · 點擊歸因追蹤", status: "OK" },
  { t: "+15s", text: "Market Radar 上線 · 4 家競品監測啟用", status: "OK" },
  { t: "+16s", text: "首批問題分派 · 5 則高強度進入草稿佇列", status: "OK" },
  { t: "+17s", text: "Brand Agent 全數上線 · ready", status: "DONE" },
];

export const RAIL_STEPS = ["連結網站", "確認品牌", "媒體網絡", "本週問題", "啟動 Agent", "完成"] as const;

export type RailIndex = 0 | 1 | 2 | 3 | 4 | 5;

// Internal step numbering — see ../onboarding-v2/data.ts for the spec.
export type InternalStep = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;

export function railFor(step: InternalStep): RailIndex {
  if (step <= 1) return 0;
  if (step === 6) return 4;
  if (step >= 7) return 5;
  return (step - 1) as RailIndex;
}
