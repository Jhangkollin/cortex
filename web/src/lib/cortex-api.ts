/**
 * Server-side fetch wrapper for cortex-api.
 *
 * **Server-only** — imports `cortex-token` which depends on
 * `NEXTAUTH_SECRET`. Import only from Server Components, Server Actions,
 * and Route Handlers.
 *
 * URL: `process.env.CORTEX_API_URL` set in the chart for in-cluster service
 * discovery (`http://cortex-api.cortex.svc.cluster.local:8000`). Local dev
 * sets via `.env`.
 */

import "server-only";

import {
  signBootstrapToken,
  signCortexApiToken,
  type CortexTokenClaims,
} from "@/lib/cortex-token";

function apiBase(): string {
  const url = process.env.CORTEX_API_URL;
  if (!url) {
    throw new Error(
      "CORTEX_API_URL missing — set in cortex-web env (chart sets it from the cortex-api Service ClusterIP).",
    );
  }
  return url.replace(/\/$/, "");
}

/**
 * Non-2xx from a cortex-api call, carrying the HTTP status so callers can
 * branch on it (e.g. 404 → not-found UI) without brittle message substring
 * matching. The message keeps the upstream detail for server-side logging;
 * callers MUST NOT render it to the browser (it can contain the in-cluster
 * api URL + response body).
 */
export class CortexApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "CortexApiError";
  }
}

// ---------------------------------------------------------------------------
// DTOs (mirror api/src/cortex_api/app/api/{auth,brand_identity}/dto.py)
// ---------------------------------------------------------------------------

export interface MembershipSummary {
  kind: "brand" | "publisher";
  id: string;
  display_name: string;
  role: string;
}

export interface ActiveContextResponse {
  kind: "brand" | "publisher";
  id: string;
  role: string;
  capabilities: string[];
}

export interface MeResponse {
  user_id: string;
  email: string;
  display_name: string | null;
  active_context: ActiveContextResponse | null;
  memberships: MembershipSummary[];
}

export interface BrandResponse {
  id: string;
  display_name: string;
  industry: string | null;
  domain: string | null;
  created_at: string;
}

export interface CreateBrandResponse {
  brand: BrandResponse;
  role: string;
  capabilities: string[];
}

/**
 * Mirrors `api/src/cortex_api/app/api/brand/dto.py::BrandProfileResponse`
 * (snake_case scalars; collection fields default to `[]` server-side).
 */
export interface BrandProfileResponse {
  brand_id: string;
  name: string;
  legal_name?: string | null;
  tagline?: string | null;
  monogram?: string | null;
  brand_color?: string | null;
  founded?: string | null;
  about?: string | null;
  source_url?: string | null;
  industry_vertical?: string | null;
  primary_jurisdiction?: string | null;
  category_value?: string | null;
  category_confidence?: number | null;
  category_alternatives: string[];
  region: string[];
  voice_samples: Record<string, unknown>[];
  products: Record<string, unknown>[];
  competitors: Record<string, unknown>[];
  media_matches: Record<string, unknown>[];
  extraction_meta?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * `GET /v1/auth/me` — call with a bootstrap token (no active_context yet).
 *
 * Use during NextAuth's `jwt` callback on first sign-in to upsert AppUser
 * and discover memberships. Once memberships are known, switch to
 * `signCortexApiToken(...)` for subsequent calls.
 *
 * `displayName` (when provided) is baked into the bootstrap JWT as a
 * `display_name` claim; cortex-api forwards it into the AppUser upsert so
 * `app_user.display_name` is populated from minute one. Omit (or pass
 * null/empty) when the OAuth profile didn't carry one — the JWT claim is
 * dropped rather than sending an empty string.
 */
export async function fetchMeWithBootstrap(
  oauthSubject: string,
  email: string,
  displayName?: string | null,
): Promise<MeResponse> {
  const token = await signBootstrapToken(oauthSubject, email, displayName);
  const res = await fetch(`${apiBase()}/v1/auth/me`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(
      `cortex-api /v1/auth/me failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as MeResponse;
}

/**
 * `POST /v1/auth/resolve-context` — verify membership + resolve role +
 * capabilities for a given context. Returns the fields to bake into the
 * NextAuth token's `active_context` claim.
 */
export async function resolveContext(
  claims: CortexTokenClaims,
  kind: "brand" | "publisher",
  id: string,
): Promise<ActiveContextResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/auth/resolve-context`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ kind, id }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(
      `cortex-api /v1/auth/resolve-context failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as ActiveContextResponse;
}

/**
 * `POST /v1/brand` — self-serve brand workspace creation. Called from the
 * persona picker Server Action.
 */
export async function createBrand(
  claims: CortexTokenClaims,
  displayName?: string,
): Promise<CreateBrandResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(displayName ? { display_name: displayName } : {}),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(
      `cortex-api POST /v1/brand failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as CreateBrandResponse;
}

/**
 * `PATCH /v1/brand/{brand_id}` — partial update of brand profile fields.
 *
 * Caller must currently hold `EDIT_BRAND_SETTINGS` capability for the brand
 * (i.e. EDITOR or ADMIN). The wizard caller is the founder of a freshly
 * created brand → ADMIN → has the capability by default.
 *
 * Only fields explicitly set in `body` are forwarded — `undefined` keys are
 * stripped so we never accidentally PATCH `display_name: ""` and overwrite a
 * meaningful name with empty string.
 */
export interface UpdateBrandBody {
  display_name?: string;
  industry?: string;
  domain?: string;
}

/**
 * Callers MUST omit fields they don't want to write — passing `display_name: ""`
 * here would PATCH the brand to an empty name. The "empty-means-absent"
 * contract is owned at the call site (the Server Action) because that's
 * where the wizard semantic lives. `updateBrand` is a transport.
 */
export async function updateBrand(
  claims: CortexTokenClaims,
  brandId: string,
  body: UpdateBrandBody,
): Promise<BrandResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(
      `cortex-api PATCH /v1/brand/${brandId} failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as BrandResponse;
}

/**
 * `GET /v1/auth/me` — call with the current session's signed token.
 * Used at root-page load time to refresh memberships post-OAuth.
 */
export async function fetchMe(claims: CortexTokenClaims): Promise<MeResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/auth/me`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(
      `cortex-api /v1/auth/me failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as MeResponse;
}

// --- analyze (SP-3a) — DTOs mirror api/.../app/api/brand/dto.py ---
export interface AnalyzeJobDTO {
  job_id: string;
  status: "pending" | "running" | "succeeded" | "failed";
  error?: string | null;
  cost_usd?: number | null;
  profile?: BrandProfileResponse | null;
}

export async function startAnalyze(
  claims: CortexTokenClaims,
  brandId: string,
  url: string,
): Promise<AnalyzeJobDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/profile/analyze`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`cortex-api POST analyze failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as AnalyzeJobDTO;
}

export async function pollAnalyze(
  claims: CortexTokenClaims,
  brandId: string,
  jobId: string,
): Promise<AnalyzeJobDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/profile/analyze/${jobId}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`cortex-api GET analyze failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as AnalyzeJobDTO;
}

// --- media-network (SP-MEDIA) — DTOs mirror api/.../app/api/brand/dto.py ---
export interface MediaOutletDTO {
  hostname: string;
  member_name: string;
  wau: number | null;
  relevance: number;
  why: string;
  topics: string[];
  context_agent_label: string;
  audience_descriptor: string;
}

export interface MediaNetworkDTO {
  brand_id: string;
  status: string;
  outlets: MediaOutletDTO[];
  error?: string | null;
}

export async function startMediaNetwork(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<MediaNetworkDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/media-network`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({}),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`cortex-api POST media-network failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as MediaNetworkDTO;
}

export async function pollMediaNetwork(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<MediaNetworkDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/media-network`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`cortex-api GET media-network failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as MediaNetworkDTO;
}

// --- brand-voice (SP-VOICE) — DTOs mirror api/.../app/api/voice/dto.py ---
export interface BrandVoiceDTO {
  brand_id: string;
  status: string;
  samples: Record<string, string>;
  error?: string | null;
}

export async function startBrandVoice(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<BrandVoiceDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/brand-voice`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({}),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`cortex-api POST brand-voice failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as BrandVoiceDTO;
}

export async function pollBrandVoice(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<BrandVoiceDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/brand-voice`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`cortex-api GET brand-voice failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as BrandVoiceDTO;
}

// --- weekly-questions (SP-QUESTIONS) — DTOs mirror api/.../app/api/questions/dto.py ---
export interface WeeklyQuestionDTO {
  id: string;
  text: string;
  media: string;
  asks: number;
  when: string;
  intent: string;
  score: number;
  competitorMentions: string[];
}

export interface WeeklyQuestionsDTO {
  brand_id: string;
  status: string;
  questions: WeeklyQuestionDTO[];
  error?: string | null;
}

export async function startWeeklyQuestions(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<WeeklyQuestionsDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/weekly-questions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({}),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`cortex-api POST weekly-questions failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as WeeklyQuestionsDTO;
}

export async function pollWeeklyQuestions(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<WeeklyQuestionsDTO> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/weekly-questions`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`cortex-api GET weekly-questions failed: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as WeeklyQuestionsDTO;
}

// --- onboarding (B1) — DTOs mirror api/.../app/api/brand_identity/dto.py ---

export interface OnboardingStatusResponse {
  onboarded: boolean;
}

export interface OnboardingCompleteResponse {
  onboarded_at: string;
}

/** Non-2xx from the status endpoint, carrying the HTTP status so the gate
 *  can branch (401/403 -> /error, 404 -> /onboarding, else -> retry). */
export class OnboardingStatusError extends Error {
  constructor(public readonly status: number) {
    super(`cortex-api onboarding/status failed: ${status}`);
    this.name = "OnboardingStatusError";
  }
}

/** GET /v1/brand/{brand_id}/onboarding/status — read by the server gate. */
export async function getOnboardingStatus(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<OnboardingStatusResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    `${apiBase()}/v1/brand/${brandId}/onboarding/status`,
    { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" },
  );
  if (!res.ok) {
    throw new OnboardingStatusError(res.status);
  }
  return (await res.json()) as OnboardingStatusResponse;
}

// ── Brand IQ Report (COR-81) ───────────────────────────────────────────────

/**
 * Mirrors the BRAND_IQ contract from the frontend prototype (data.jsx).
 *
 * NOTE — casing: these fields are intentionally camelCase, unlike every other
 * DTO in this file (which is snake_case to match the rest of cortex-api). The
 * report endpoint is the ONE exception: slice-1's `ReportDTO`
 * (`api/.../service/brand_report/contract.py`) declares camelCase field names
 * natively — by design, to match this BRAND_IQ prototype contract — with no
 * snake_case aliasing. So camelCase here is correct, not an oversight.
 *
 * Honesty marker: "資料不足" appears in certainty/status fields where data
 * is insufficient.
 */
export interface BrandIqMeta {
  subject: string;
  enName?: string;
  legalName?: string;
  domain?: string;
  primaryMarket: string;
  extendedMarkets: string[];
  reportDate: string;
  windowFrom?: string;
  windowTo?: string;
  monogram: string;
  brandColor?: string;
  tagline?: string;
  founded?: string;
  category?: string;
  confidence?: number;
  reportId: string;
  pageCount: number;
  preparedFor?: string;
  preparedBy?: string;
}

export interface BrandIqCoreItem {
  item: string;
  body: string;
  certainty: "已確認" | "高可能" | "資料不足";
}

export interface BrandIqProductLine {
  line: string;
  thesis: string;
  examples: string;
  signal: string;
  confidence: number;
}

export interface BrandIqSubBrand {
  type: string;
  name: string;
  note: string;
}

export interface BrandIqEndorsement {
  status: "已確認" | "高可能" | "資料不足";
  body: string;
}

export interface BrandIqMediaNode {
  name: string;
  audience: string;
  weekly: string;
  relevance: number;
  topics: string;
  trend: "上升" | "下降" | "持平";
}

export interface BrandIqCompetitor {
  tier: string;
  brands: string;
  basis: string;
  position: string;
}

export interface BrandIqInsights {
  confirmed: string[];
  inferences: string[];
  hypotheses: string[];
}

export interface BrandIqFaqItem {
  q: string;
  a: string;
  source: string;
  level: string;
}

export interface BrandIqChannel {
  type: string;
  surfaces: string;
  read: string;
}

export interface BrandIqRisk {
  theme: string;
  trigger: string;
  where?: string;
  note: string;
  level: "高" | "中" | "低";
  action: string;
}

export interface BrandIqSources {
  A: string[];
  B: string[];
  C: string[];
}

export interface BrandIqQuality {
  high: string;
  midLow: string;
  gaps: string;
  conflicts: string;
  open: string;
}

/** Full BRAND_IQ report object — shape mirrors the prototype data.jsx contract. */
export interface BrandIqReport {
  meta: BrandIqMeta;
  core: BrandIqCoreItem[];
  coreJudgement: string;
  productLines: BrandIqProductLine[];
  productNote?: string;
  subBrands: BrandIqSubBrand[];
  endorsements: BrandIqEndorsement;
  ipCollabs: BrandIqEndorsement;
  mediaNetwork: BrandIqMediaNode[];
  competitors: BrandIqCompetitor[];
  competitorNote?: string;
  insights: BrandIqInsights;
  faq: BrandIqFaqItem[];
  channels: BrandIqChannel[];
  risks: BrandIqRisk[];
  sources: BrandIqSources;
  quality: BrandIqQuality;
}

export interface ReportEnvelope {
  reportId: string;
  status: "pending" | "running" | "ready" | "failed";
  error?: string | null;
  report?: BrandIqReport | null;
}

export interface ReportVersionItem {
  reportId: string;
  version: string;
  createdAt: string;
  status: string;
  current: boolean;
  costUsd?: number | null;
}

export interface GenerateReportResponse {
  reportId: string;
  status: string;
  estimatedSeconds: number;
  pollUrl: string;
}

/**
 * `POST /v1/brand/{brand_id}/report` — kick off async report generation.
 * Returns HTTP 202 immediately. Poll with `fetchBrandReport` until ready.
 */
export async function generateReport(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<GenerateReportResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/report`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new CortexApiError(
      res.status,
      `cortex-api POST /v1/brand/${brandId}/report failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as GenerateReportResponse;
}

/**
 * `GET /v1/brand/{brand_id}/report/{report_id}` — poll until ready.
 *
 * Returns `ReportEnvelope`. When `status == "ready"`, `envelope.report`
 * contains the full BrandIqReport object.
 */
export async function fetchBrandReport(
  claims: CortexTokenClaims,
  brandId: string,
  reportId: string,
): Promise<ReportEnvelope> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    `${apiBase()}/v1/brand/${brandId}/report/${reportId}`,
    { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" },
  );
  if (!res.ok) {
    throw new CortexApiError(
      res.status,
      `cortex-api GET /v1/brand/${brandId}/report/${reportId} failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as ReportEnvelope;
}

/**
 * `GET /v1/brand/{brand_id}/report/{report_id}/pdf` — fetch the rendered PDF.
 *
 * Returns the raw `Response` so the caller (a Next route handler) can stream
 * the binary body straight back to the browser with the upstream
 * `Content-Type` / `Content-Disposition`. The signed Bearer token never
 * leaves the server. Does NOT throw on non-2xx — the route handler relays the
 * upstream status (e.g. 404/501 until COR-80 merges) verbatim.
 */
export async function fetchBrandReportPdf(
  claims: CortexTokenClaims,
  brandId: string,
  reportId: string,
): Promise<Response> {
  const token = await signCortexApiToken(claims);
  return fetch(`${apiBase()}/v1/brand/${brandId}/report/${reportId}/pdf`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
}

/**
 * `GET /v1/brand/{brand_id}/reports` — version list (newest first).
 */
export async function listBrandReports(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<ReportVersionItem[]> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/reports`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(
      `cortex-api GET /v1/brand/${brandId}/reports failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as ReportVersionItem[];
}

// ── Brand Report UI-state (COR-82) ───────────────────────────────────────────

export interface ReportUiStateResponse {
  celebratePending: boolean;
  heroDismissed: boolean;
  /**
   * Authoritative server-computed celebration gate:
   * `celebrate_pending AND NOT consumed AND a READY report exists`. The web
   * celebration gate keys on this flag rather than correlating
   * `celebratePending` with the report status client-side.
   */
  celebrateReady: boolean;
}

/**
 * `GET /v1/brand/{brand_id}/report/ui-state` — read both flags in one query.
 */
export async function getReportUiState(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<ReportUiStateResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brand/${brandId}/report/ui-state`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new CortexApiError(
      res.status,
      `cortex-api GET /v1/brand/${brandId}/report/ui-state failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as ReportUiStateResponse;
}

/**
 * `POST /v1/brand/{brand_id}/report/ui-state/arm` — arm the celebration flag.
 * Called at onboarding completion, before redirecting to /brand/dashboard.
 */
export async function armReportCelebrate(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<void> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    `${apiBase()}/v1/brand/${brandId}/report/ui-state/arm`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      cache: "no-store",
    },
  );
  if (!res.ok) {
    throw new CortexApiError(
      res.status,
      `cortex-api POST /v1/brand/${brandId}/report/ui-state/arm failed: ${res.status} ${await res.text()}`,
    );
  }
}

/**
 * `POST /v1/brand/{brand_id}/report/ui-state/celebrate-consume` — consume flag.
 * Idempotent. Called on first Discover visit so the modal never shows again.
 */
export async function consumeReportCelebrate(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<void> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    `${apiBase()}/v1/brand/${brandId}/report/ui-state/celebrate-consume`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      cache: "no-store",
    },
  );
  if (!res.ok) {
    throw new CortexApiError(
      res.status,
      `cortex-api POST /v1/brand/${brandId}/report/ui-state/celebrate-consume failed: ${res.status} ${await res.text()}`,
    );
  }
}

/**
 * `POST /v1/brand/{brand_id}/report/ui-state/hero-dismiss` — dismiss the hero card.
 * Permanent. Called when the user clicks the × on the hero.
 */
export async function dismissReportHero(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<void> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    `${apiBase()}/v1/brand/${brandId}/report/ui-state/hero-dismiss`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      cache: "no-store",
    },
  );
  if (!res.ok) {
    throw new CortexApiError(
      res.status,
      `cortex-api POST /v1/brand/${brandId}/report/ui-state/hero-dismiss failed: ${res.status} ${await res.text()}`,
    );
  }
}

// --- brands list (multi-brand chunk 3) — DTOs mirror api/.../app/api/brand_identity/dto.py ---

export type BrandRole = "viewer" | "editor" | "admin";

export interface BrandListItem {
  id: string;
  display_name: string;
  domain: string | null;
  role: BrandRole;
  onboarded_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BrandListResponse {
  brands: BrandListItem[];
}

/**
 * `GET /v1/brands` — list all brands the caller holds a membership in.
 *
 * No per-brand capability gate — the result set is intrinsically scoped to
 * the caller's memberships. Used by the sidebar switcher and the
 * onboarding-complete portfolio band (chunk 3).
 */
export async function listMyBrands(
  claims: CortexTokenClaims,
): Promise<BrandListItem[]> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(`${apiBase()}/v1/brands`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new CortexApiError(
      res.status,
      `cortex-api GET /v1/brands failed: ${res.status} ${await res.text()}`,
    );
  }
  const body = (await res.json()) as BrandListResponse;
  return body.brands;
}

/** POST /v1/brand/{brand_id}/onboarding/complete — idempotent stamp. */
export async function completeOnboarding(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<OnboardingCompleteResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    `${apiBase()}/v1/brand/${brandId}/onboarding/complete`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      cache: "no-store",
    },
  );
  if (!res.ok) {
    throw new Error(
      `cortex-api POST onboarding/complete failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as OnboardingCompleteResponse;
}
