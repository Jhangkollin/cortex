import type { ComposerModel, DiscoverData } from "./types";

export const BASE_DATA: DiscoverData = {
  alerts: [
    {
      kind: "warn",
      icon: "inbox",
      cat: "需求池",
      headline: [{ b: "48 題相關問題" }, "・~35K 月相關曝光"],
      sub: "",
      cta: "看 Top 10 問題 →",
    },
    {
      kind: "opp",
      icon: "trending_up",
      cat: "主力承載",
      headline: [{ b: "早安健康" }, " 承載 95% 相關流量"],
      sub: "",
      cta: "為何如此集中 →",
    },
    {
      kind: "sig",
      icon: "card_giftcard",
      cat: "母親節商機",
      headline: [{ b: "蛋白質/肌少症" }, "・腎臟保健 是 Top 2 類別"],
      sub: "",
      cta: "看類別匹配 →",
    },
  ],
  kpis: [
    { lab: "相關問題數 (TOP 500 抽樣)", v: "48", note: "高度匹配", trend: "answers" },
    { lab: "月相關曝光佔算", v: "35,398", note: "views/month", trend: "views" },
    { lab: "主力承載媒體", v: "早安健康", note: "95.2%", trend: "clicks" },
    { lab: "估算月度獲客等值", v: "NT$87,787", note: "/月・等同付費", trend: "revenue" },
  ],
  funnel: {
    title: "獲客通路數學",
    sub: "若 Mlytics 在這些相關答案中嵌入達摩本草 — 估算",
    disclaimer: "所有數字皆為假設值・30 天部署後校正 →",
    blocks: [
      { v: "48", nm: [{ b: "相關問題" }] },
      { v: "24", nm: [{ b: "預估嵌入 (50%)" }] },
      { v: "17.7K", nm: [{ b: "月度品牌曝光" }], here: true },
      { v: "1,097", nm: [{ b: "月度品牌點擊" }] },
      { v: "NT$87.8K", nm: [{ b: "等同付費獲取" }] },
    ],
    arrows: [
      { rate: "50%", label: ["採納率"] },
      { rate: "×737", kind: "leverage", label: [{ b: "leverage" }, "\n曝光/題"] },
      { rate: "6.2%", label: ["CTR"] },
      { rate: "NT$80", label: ["每次點擊"] },
    ],
    takeaway: [
      "若 Mlytics 在 ",
      { b: "24 個相關答案" },
      " 中嵌入品牌露出，預估每月 ",
      { b: "17.7K 曝光" },
      "、",
      { b: "1,097 點擊" },
      "，等同 ",
      { b: "NT$87.8K" },
      " 付費獲取價值。",
    ],
    takeawayCta: "了解估算方法 →",
  },
  media: {
    title: "主力承載媒體",
    sub: "相關 Q&A 流量・高度集中",
    rows: [
      { nm: "早安健康", vis: 95 },
      { nm: "遠見雜誌", vis: 5 },
    ],
  },
  intent: {
    rows: [
      { nm: "蛋白質/肌少症/抗老", count: 7, views: 6739, top: true },
      { nm: "腎臟保健", count: 5, views: 5475 },
      { nm: "飲食原則/抗發炎", count: 7, views: 4929 },
      { nm: "失智/大腦健康", count: 7, views: 4198 },
      { nm: "血糖/糖尿病", count: 4, views: 3129 },
      { nm: "心血管/一般營養", count: 5, views: 2691 },
      { nm: "自律神經/睡眠", count: 5, views: 2646 },
      { nm: "體重/代謝", count: 3, views: 2392 },
      { nm: "腸道/益生菌", count: 2, views: 1830 },
      { nm: "眼睛健康", count: 3, views: 1377 },
    ],
  },
  questions: [
    { q: "為什麼全愛吐司和花生醬被洪水祥醫師視為腎臟的「高碳地雷」？", views: 2310, publisher: "早安健康", match: "魚油／維他命" },
    { q: "為什麼過了44歲，單餐蛋白質攝取不到30克，肌肉就會開始流失？", views: 2051, publisher: "早安健康", match: "綜合維他命／瑪卡" },
    { q: "醫師分享的「水炒花椰菜」和「氣炸羽衣甘藍」如何快速料理並保留營養？", views: 1417, publisher: "早安健康", match: "消化酵素" },
    { q: "研究指出，44歲後肌肉合成抗性增加，該如何透過飲食「破門而入」？", views: 1330, publisher: "早安健康", match: "綜合維他命" },
    { q: "洪水祥醫師分享的62歲陳大哥，採取哪些早餐飲食改變後，eGFR進步了20分？", views: 1267, publisher: "早安健康", match: "魚油" },
    { q: "117成人入瑞璃麗亞每天吃3環優格，這對她的腸道健康和發炎指數有何影響？", views: 1214, publisher: "早安健康", match: "ABC PRO+ 益生菌" },
    { q: "張小姐透過哪些飲食調整，成功甩掉14公斤並改善精神狀況？", views: 1129, publisher: "早安健康", match: "消化酵素／益生菌" },
    { q: "對於未洗腎的腎病患者，洪水祥醫師建議的蛋白質「221」精準配額是什麼？", views: 1090, publisher: "早安健康", match: "魚油／維他命" },
    { q: "飯後多久做一次「7秒運動」最有效？", views: 1089, publisher: "早安健康", match: "消化酵素" },
    { q: "哪些日常的負面口頭禪會加速大腦退化，形成「老人腦」？", views: 860, publisher: "早安健康", match: "葉黃素／魚油" },
  ],
  geo: {
    sub: "達摩本草品牌在 Google AI Overviews 與 LLM 搜尋引擎的曝光潛力",
    tags: ["保健食品比較查詢", "魚油濃度標準", "葉黃素挑選", "益生菌選擇", "母親節保健禮品", "蛋白質補充建議", "腎臟保健飲食"],
    status: "待整合",
    note: "Search API (Brave / Google) 整合後 30 天內提供廠商資料",
  },
};

// Transcribed verbatim from cortex-composer.jsx MODELS (lines 7-12).
export const COMPOSER_MODELS: ComposerModel[] = [
  { id: "gemini-flash", name: "Gemini 2.5 Flash", desc: "Lowest latency, low cost", icon: "bolt", lat: "23ms" },
  { id: "gemini-pro", name: "Gemini 2.5 Pro", desc: "General reasoning, multimodal", icon: "memory", lat: "84ms" },
  { id: "claude-opus", name: "Claude Opus 4.7", desc: "Highest reasoning quality", icon: "psychology", lat: "312ms" },
  { id: "gpt-5", name: "GPT-5", desc: "Broad capability, tool use", icon: "developer_mode", lat: "156ms" },
];
