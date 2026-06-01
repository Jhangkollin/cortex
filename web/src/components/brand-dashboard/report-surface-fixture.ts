/**
 * Backend-free fixtures for the Brand IQ report surface.
 *
 * The real surface (`brand-report-surface.tsx`) is only drivable by live
 * cortex-api state, so the hero + celebration can't be exercised locally. These
 * fixtures let the pure presentational view (`brand-report-surface-view.tsx`)
 * and its tests render the "ready" path with no backend.
 *
 * `READY_FIXTURE` is a realistic `status: "ready"` envelope whose `report`
 * object fully populates the `BrandIqReport` contract — including every `meta`
 * field the hero and celebration actually read (`subject`, `monogram`,
 * `reportDate`, `pageCount`, plus the envelope's `reportId`). Sample content
 * uses the fictional brand "Acme Bank Asia".
 *
 * `PREVIEW_UI_STATE` mirrors the `ReportUiStateResponse` shape exactly
 * (celebratePending + heroDismissed + celebrateReady). `celebrateReady` is true
 * so the preview path still shows the celebration under the server-flag gate.
 */

import type {
  ReportEnvelope,
  ReportUiStateResponse,
} from "@/app/brand/dashboard/report-types";

export const READY_FIXTURE: ReportEnvelope = {
  reportId: "BIQ-FIXTURE-0001",
  status: "ready",
  error: null,
  report: {
    meta: {
      subject: "Acme Bank Asia",
      enName: "Acme Bank Asia",
      legalName: "Acme Bank Asia Holdings Ltd.",
      domain: "acmebank.asia",
      primaryMarket: "TW",
      extendedMarkets: ["HK", "SG", "JP"],
      reportDate: "2026-05-24",
      windowFrom: "2025-11-24",
      windowTo: "2026-05-24",
      monogram: "A",
      brandColor: "#1C726B",
      tagline: "Banking that moves at the speed of you.",
      founded: "2014",
      category: "Digital Banking",
      confidence: 0.86,
      reportId: "BIQ-FIXTURE-0001",
      pageCount: 12,
      preparedFor: "Acme Bank Asia · Leadership",
      preparedBy: "Cortex · Brand Agent",
    },
    core: [
      {
        item: "定位",
        body: "面向亞太年輕專業族群的數位優先銀行，主打即時、透明的金流體驗。",
        certainty: "已確認",
      },
      {
        item: "差異化",
        body: "以無分行、開放 API 與秒級轉帳作為核心競爭力。",
        certainty: "高可能",
      },
    ],
    coreJudgement:
      "Acme Bank Asia 是一家以行動體驗為核心、深耕亞太多市場的數位銀行品牌。",
    productLines: [
      {
        line: "Everyday Banking",
        thesis: "零月費、即時轉帳的日常帳戶。",
        examples: "Acme Account, Acme Card",
        signal: "官網首頁主打、App 商店截圖",
        confidence: 0.9,
      },
      {
        line: "Wealth",
        thesis: "低門檻的自動化理財與基金平台。",
        examples: "Acme Invest",
        signal: "產品頁、新聞稿",
        confidence: 0.72,
      },
    ],
    productNote: "產品線以官網與 App 商店資料為主要來源。",
    subBrands: [
      {
        type: "子品牌",
        name: "Acme Invest",
        note: "理財與投資子品牌，共用主品牌識別。",
      },
    ],
    endorsements: {
      status: "高可能",
      body: "與區域金融科技獎項有合作背書，惟未取得官方公告全文。",
    },
    ipCollabs: {
      status: "資料不足",
      body: "未發現明確的 IP 聯名合作紀錄。",
    },
    mediaNetwork: [
      {
        name: "TechAsia Daily",
        audience: "亞太科技讀者",
        weekly: "120 萬",
        relevance: 0.78,
        topics: "金融科技、數位銀行",
        trend: "上升",
      },
      {
        name: "Finance Weekly TW",
        audience: "台灣財經讀者",
        weekly: "45 萬",
        relevance: 0.64,
        topics: "個人理財",
        trend: "持平",
      },
    ],
    competitors: [
      {
        tier: "直接競爭",
        brands: "LINE Bank, Rakuten Bank",
        basis: "同為亞太數位銀行，目標客群重疊。",
        position: "規模較大、品牌知名度較高。",
      },
    ],
    competitorNote: "競品清單以公開市場報導與品牌官網推估。",
    insights: {
      confirmed: ["數位優先、無實體分行", "主力市場為台灣"],
      inferences: ["年輕專業族群為核心客群", "API 開放策略為差異化重點"],
      hypotheses: ["可能規劃跨境支付產品", "或將拓展東南亞市場"],
    },
    faq: [
      {
        q: "Acme Bank Asia 是哪裡的銀行？",
        a: "以台灣為主要市場、並服務香港、新加坡與日本的數位銀行。",
        source: "官網「關於我們」",
        level: "已確認",
      },
    ],
    channels: [
      {
        type: "官方網站",
        surfaces: "acmebank.asia",
        read: "品牌定位與產品說明的主要來源。",
      },
      {
        type: "社群",
        surfaces: "Instagram, LinkedIn",
        read: "品牌語氣偏年輕、專業。",
      },
    ],
    risks: [
      {
        theme: "監理合規",
        trigger: "跨市場營運",
        where: "多法域",
        note: "不同市場的金融監理要求差異大。",
        level: "中",
        action: "確認各市場牌照與合規揭露。",
      },
    ],
    sources: {
      A: ["官網", "App 商店頁面"],
      B: ["新聞稿", "財經媒體報導"],
      C: ["社群貼文", "第三方評論"],
    },
    quality: {
      high: "品牌定位、主力市場、產品線。",
      midLow: "競品推估、媒體網絡權重。",
      gaps: "IP 聯名、實際財務數據。",
      conflicts: "未發現明顯矛盾。",
      open: "東南亞拓展計畫仍待證實。",
    },
  },
};

export const PREVIEW_UI_STATE: ReportUiStateResponse = {
  celebratePending: true,
  heroDismissed: false,
  celebrateReady: true,
};
