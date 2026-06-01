# Mlytics Cortex — E2E Feature Slices (Reordered)

**Author:** Okis Chuang (Head of Product, Mlytics)
**Reordered:** 2026-05-08
**Source of truth:** `product-narrative.md`, `prototype-walkthrough.md`, `cortex-prototype.html`
**Companion plan:** `cortex-4week-plan-v3.html` (Brand Customer slice, current sprint)

---

## Why this document exists

The Cortex prototype is two products in one — a public marketing site plus an authenticated, persona-tuned AI dashboard with agents, connectors, and a Knowledge Base. This document decomposes the prototype into independent vertical slices, each one a thin end-to-end story that a single persona can complete and that we could demo to a customer or close on.

A slice qualifies as a slice when **all four** are true:

1. **One persona owns it.** A real Content Owner, Brand, or Developer can pick it up and get value without help from another persona shipping their own slice first.
2. **It crosses the full stack.** The slice touches a real user surface, a real backend, real data plumbing, and (where applicable) real billing.
3. **It is demoable in under two minutes.**
4. **It moves a metric we already display in the prototype** — a KPI on Discover or a billing meter on Pricing.

---

## Platform foundations (cross-cutting, not slices)

| Foundation | What it is | Why it is shared |
|---|---|---|
| **Persona-aware app shell** | Sidebar, top tabs, status block, persona greeting, restart-flow button | Every authenticated slice renders inside this shell |
| **KPI & sparkline service** | Time-series metrics store + sparkline endpoint, persona-scoped | Every Discover dashboard reads from this; the four KPI cards are the visible product |
| **Agent runtime** | Prompt routing, tool-calling, KB context injection, run history | Every "agent card" on Discover is a thin orchestration over this |
| **Connector framework** | OAuth, webhook, polling, status-pill state machine (LIVE / BETA / AVAILABLE) | Every connector tile in the catalog is one config inside this framework |
| **Tenant + billing primitives** | Org → seats, usage meters per Cortex product, contract-aware gating | Pricing has two axes (seats × usage); both need to exist before any slice can monetize |

---

## Slice catalog (in chosen order)


### Now — this quarter — 6 slices

#### 1. B3 — Brand Embed (publisher placements)

| Field | Value |
|---|---|
| **Family** | B |
| **Persona** | Brand Customer (with Content Owner cooperation) |
| **Maps to surfaces** | Discover (Brand Embed card) + publisher article (sponsored answer slot) |
| **Maps to product** | Brand Embed (usage billing) |
| **Size** | L |

**Value statement.** A brand can author a "custom answer" once and have it appear inside Cortex Q&A widgets on publisher articles when reader intent matches — verified placements visible on Discover.

**Demo script.** Brand authors a 3-line answer + product image + CTA. Publishes. Reader on 經理人 article asks matching question (CO1 widget). Cortex selects this brand's answer, renders it with disclosure. Brand sees "8 placements live" on Discover. Click → list with publisher + article + impression count.

**In scope.** Custom answer authoring UI. Intent → answer matching. Sponsored placement slot in CO1 widget (with disclosure). Placement counter + per-placement metrics. Editorial review queue (brand answer must pass review).

**Out of scope.** A/B testing of multiple answer variants. Dynamic creative per reader segment. Programmatic bidding for placement (manual rate cards). Video / rich media beyond image.

**Success metric.** First paid brand placement on a partner publisher. ≥80% editorial review approval rate (signals brands respect publisher quality bar).

**Dependencies.** X1, X2, X5 (placements created here are reflected in Ops Admin), CO1 (widget host), CO4 (intent matching engine reused).

---

#### 2. X2 — Pricing → contracted seats live

| Field | Value |
|---|---|
| **Family** | X |
| **Persona** | All three (revenue) |
| **Maps to surfaces** | Pricing page → Stripe checkout → Org admin → Seat assignment |
| **Maps to product** | Platform tier (Developer $20 / Pro $50 / Enterprise $200) |
| **Size** | M |

**Value statement.** A prospect on the Pricing page can buy Pro seats with a credit card and have their teammates sign in with the right entitlements within an hour.

**Demo script.** Land on Pricing. Click *Pro · $50/seat · MOST POPULAR*. Buy 5 seats. Receive admin invite. Invite teammates. Teammates sign in and see Pro-only capabilities (priority support badge, SSO toggle, audit log tab).

**In scope.** Stripe checkout for Developer + Pro tiers. Org → seat assignment. Tier gating on the app shell (Pro-only and Enterprise-only nav items render conditionally). Self-serve invite flow. Audit log scaffold.

**Out of scope.** Usage meter billing for Cortex products (AI Q&A Widget, Media GEO, Decisive Engine) — that is per-slice. Enterprise tier (manual contract motion until Enterprise demand justifies self-serve). Annual / commit pricing. Procurement / SOC 2 docs.

**Success metric.** First $1 of MRR through Stripe. ≥5 self-serve Pro signups in pilot month with <10% support-ticket rate on signup.

**Dependencies.** X1 (auth + persona model). *Note: ship X2 in parallel with X1 + B1 — letting Brand pilots run unbilled lengthens time-to-revenue by a quarter.*

---

#### 3. X1 — Sign-up to persona-tuned empty Discover

| Field | Value |
|---|---|
| **Family** | X |
| **Persona** | All three (foundation) |
| **Maps to surfaces** | Home/Login → Persona picker → Brand onboarding wizard (5 steps) → App shell → Discover (empty state) |
| **Maps to product** | None directly — enables every other product |
| **Size** | M |

**Value statement.** A new user can sign up with work email, declare their persona, complete the Brand onboarding wizard (company → domain → industry → contact → placement preferences), and land in their Cortex with the right greeting, the right KPI card titles, and the right agent slot labels — even if every value is "—".

**Demo script.** Open Cortex.mlytics.com. Click Continue with Google. Land on the persona picker. Pick *Brand Customer*. Walk through 5-step onboarding (industry chip = Finance, domain = acmebank.asia). Land on a Discover view that says "Good afternoon, CMO / 王小明 · How your brand is *seen, found, and chosen*," with four KPI cards titled AI Surface Visibility / Cited As Answer / Buyer Intent Matched / Cost Per Qualified Lead and six agent slots ready to be filled.

**In scope.** Real Google OAuth + work-email SSO. Persona picker writes a `persona` field on the org. **Brand onboarding wizard (the 5-step flow already designed in `renderOnboarding()`)**, persisted to a `brand_profiles` record visible to Mlytics Ops (handoff to X5). App shell with sidebar, top tabs, status block, restart-flow button. Persona-tuned Discover scaffold (templated greeting, KPI titles, agent slot labels, suggested-query prompts) — values stub to "—" with "connect a source" CTAs.

**Out of scope.** Real KPI data (that ships in CO2/B1). Agent execution (that ships in CO3/B2). Connectors catalog populated (that is X3). Billing. Knowledge Base. Content Owner / Developer onboarding wizards (Brand-only this horizon — Coming-soon stubs on persona picker are kept).

**Success metric.** Time from "Continue with Google" to a Discover view ≤ 30s (without onboarding) or ≤ 3 min (with onboarding). Persona switch round-trips cleanly. ≥3 internal users pilot all three personas without a defect.

**Dependencies.** None — this is the foundation.

---

#### 4. X5 — Mlytics Ops Admin (Brand × Article placement)

| Field | Value |
|---|---|
| **Family** | X |
| **Persona** | Mlytics Ops (internal) |
| **Maps to surfaces** | `renderAdmin()` — admin nav (dark) + Brand × Article placement table + tabs for Placements / Subscriptions / Revenue Share |
| **Maps to product** | Internal tool — replaces Excel/Notion |
| **Size** | M |

**Value statement.** A Mlytics Ops user can manage Brand × Article placement assignments and subscription state in one tool, replacing the current Excel/Notion process — so a new Brand pilot can be onboarded end-to-end without spreadsheet hand-offs.

**Demo script.** Ops user signs in with admin role. Sees the Brand placement table: 6 brands across finance / fintech / insurance / wealth / DTC, each with article count out of 100 quota, subscription pill (Active / Pending / Paused). Click *+ 新增 placement* → assign 鉅亨網 article #4823 to *Acme Bank Asia*. Status flips to active; quota bar fills. Use *📥 CSV 匯入* to bulk-upload placements; use *📤 對帳匯出* to download monthly reconciliation.

**In scope.** Admin role + auth (separate tenant or admin claim on existing user model). `placements` table (brand_id, article_id, status, dates) and `subscriptions` table (brand_id, plan, state, MRR). Brand list with quota, subscription state, edit button. CSV import + reconciliation export. Subscription state-machine UI (Active / Pending / Paused) with audit trail.

**Out of scope.** Anything in the Brand-customer app surface. Self-service publisher placement (publishers don't yet log into this tool). Real-time dashboard for ops leads (data is correct but not curated). Revenue Share tab is stubbed only.

**Success metric.** Ops time-to-onboard a new Brand pilot drops from days (current Excel/Notion process) to <2 hours. Zero placement double-bookings in first quarter post-ship. ≥6 brand pilots managed exclusively through this tool.

**Dependencies.** X1 (brand_profiles record from Brand onboarding is the input). Independent of X2 (subscriptions can be manually entered until X2 is wired in *Next*).

---

#### 5. B1 — Brand Monitor → Media GEO Lite

| Field | Value |
|---|---|
| **Family** | B |
| **Persona** | Brand Customer |
| **Maps to surfaces** | Discover (KPI strip + Brand Funnel + Brand Monitor card + Suggested-query "Where am I being cited?") |
| **Maps to product** | Media GEO ($2K/mo · 100 custom answers) |
| **Size** | M (becomes L if pre-flight Q1 or Q2 is "no") |

**Value statement.** A brand can answer "where am I being cited as the answer in AI search?" in under 30 seconds — across ChatGPT, Perplexity, Gemini, and the Citation Network — see weekly trends, and trace each citation back to a publisher source.

**Demo script.** New Brand pilot logs in. Connects domain (e.g. example.com). Discover populates: AI Surface Visibility 34% (+6pt), Cited As Answer 147 (+23%), Buyer Intent Matched 47 (+18%), Cost Per Qualified Lead $42 (-8%), with sparklines. Brand Funnel (4 stages, widget_view → brand_clicks → answer_views → cta_clicks) renders from `aigc_clickstream_metrics`. Click Brand Monitor card → "Where am I being cited?" agent returns ranked list of surfaces with quote excerpts. Click Suggested-query "我的品牌在 AI 搜尋裡被引用幾次？" → same view, prefilled.

**In scope.** AI surface scraping pipeline (ChatGPT, Perplexity, Gemini citations). Domain-level brand mention detection. AI Surface Visibility + Cited As Answer + Buyer Intent Matched + CPL KPIs with weekly deltas, all four with sparklines. **Brand Funnel** (the 4-stage chart) backed by `aigc_clickstream_metrics`. Brand Monitor agent (drill-in: 147 citations broken down by publisher with `cited_pct` matching the prototype's `PUBLISHERS_CITE` data). Citation excerpt rendering. Per-domain alerting on visibility drop. Suggested-query strip (4 brand-personalized prompts wired live).

**Out of scope.** Custom answer authoring (that is the rest of Media GEO — separate slice if scope grows). Sentiment analysis. Multi-domain (brand + sub-brand). Localized Asia AI surfaces beyond the Citation Network publishers. Real-time alerting on new citations (post-MVP).

**Success metric.** Time-to-first-insight under 60s after domain connect. ≥10 Brand pilots with weekly engagement on Brand Monitor. KPI numbers reconcile with manual SQL spot-check on the underlying clickstream table.

**Dependencies.** X1. AI surface scraping infra is the riskiest piece — TOS / scraping policy needs legal sign-off before pilot. Pre-flight Q1, Q2, Q4 must resolve "yes."

---

#### 6. B2 — Audience Finder + Lead Pilot

| Field | Value |
|---|---|
| **Family** | B |
| **Persona** | Brand Customer |
| **Maps to surfaces** | Discover (Audience Finder + Lead Pilot cards + new "Leads inbox") |
| **Maps to product** | Lead Pilot (performance billing — CPL) |
| **Size** | L |

**Value statement.** A brand sees Buyer Intent Matched (47/today) tick up as Cortex finds qualified buyers across publisher Q&A surfaces — and Lead Pilot routes those leads into the brand's inbox with full intent context. CPL billing meter ticks too.

**Demo script.** Brand Discover: Buyer Intent Matched 47, Cost Per Qualified Lead $42. Click Audience Finder → see the 47 leads with intent excerpts ("looking for a credit card with airline miles, budget $0 annual fee, currently has Chase Sapphire"). Click one → Lead Pilot has already pushed it to brand's CRM with Salesforce tag.

**In scope.** Intent classifier (queries from CO1 widget + AI surface mentions). Buyer Intent Matched + CPL KPIs with sparklines. Audience Finder agent (filters intent inbox). Lead Pilot agent (push to CRM). CPL billing meter wired through X2.

**Out of scope.** Custom intent taxonomies per brand. Lead scoring beyond default model. CRM integrations beyond first 2 (Salesforce, HubSpot). Lead enrichment with third-party data.

**Success metric.** First brand pilot with paid CPL leads converting at ≥10% to opportunity. ≥$X CPL revenue in pilot quarter.

**Dependencies.** X1, X2 (CPL billing meter), X3 (CRM connectors), B1 (intent signal upstream).

---


### Next — 1–2 quarters — 4 slices

#### 1. X4 — Knowledge Base [Enterprise]

| Field | Value |
|---|---|
| **Family** | X |
| **Persona** | Enterprise across all three personas |
| **Maps to surfaces** | Knowledge Base page (gated behind Enterprise tier) |
| **Maps to product** | Enterprise wedge — multiplies the value of every agent |
| **Size** | XL |

**Value statement.** An Enterprise customer can connect their CMS archive, brand guidelines, and audience research as 3+ KB sources — and every Cortex agent answers using *their* corpus instead of generic web data.

**Demo script.** From Discover, agents say "Differentiated answers — connect your sources." Solutions architect connects Editorial CMS archive (184K docs). Embedding pipeline runs. Reader Insight agent now cites publisher's own articles by title.

**In scope.** Multi-source ingest (CMS, PDF/Notion, Substack/Beehiiv, Q&A widget logs, daily web crawl). `text-3-large` embedding pipeline. Tenant isolation. Citations pane on agent answers. Source health monitoring. Solutions-architect-assisted onboarding (not yet self-serve).

**Out of scope.** Self-serve KB for Pro tier. Cross-tenant federated search. Customer-managed embedding model. SLA on embed freshness beyond daily.

**Success metric.** ≥3 Enterprise customers with a connected source in first quarter post-GA. Citation rate on agent answers ≥40% when KB is connected.

**Dependencies.** X1, X3 (connector framework). Agent runtime must support context injection.

---

#### 2. CO2 — Reader Insight Dashboard

| Field | Value |
|---|---|
| **Family** | CO |
| **Persona** | Content Owner |
| **Maps to surfaces** | Discover (KPI strip + Reader Insight agent card) |
| **Maps to product** | Decisive Engine ($1K/mo) – analytics use case |
| **Size** | S |

**Value statement.** A Content Owner who connects GA4 sees their three signature KPIs populate in real time — Active Readers (WAU), Avg Engagement Time, and Q&A Resolution Rate — and can ask the Reader Insight agent for narrative summaries of weekly trends.

**Demo script.** Owner connects GA4 (one click via X3 framework). Discover KPIs flip from "—" to 184K WAU / 3m 42s / 74%. Click Reader Insight agent → "Summarize this week vs. last." Agent returns a 4-bullet narrative grounded in the GA4 data.

**In scope.** GA4 metric pipeline → KPI service. Sparkline rendering on KPI cards (delta vs. 7d). Reader Insight agent (read-only, GA4 + Q&A logs as tools). Suggested-query "What are my readers loving most this week?" wired live.

**Out of scope.** Content Love Score (composite metric — needs CO1 Q&A signal + GA4 — defer to CO3). Cross-publisher reader graph. Predictive recommendations. Recharts-style deep dashboards (these live in connected GA4, not Cortex).

**Success metric.** Median time from GA4 connect → first KPI render <5 min. Reader Insight agent NPS ≥+30 in pilot.

**Dependencies.** X1, X3 (GA4 connector), agent runtime.

---

#### 3. D1 — Unified Model API (one key, every model)

| Field | Value |
|---|---|
| **Family** | D |
| **Persona** | Developer |
| **Maps to surfaces** | Developer landing page → API docs → API key console |
| **Maps to product** | Unified Model API (PAYG) |
| **Size** | M |

**Value statement.** A developer can sign up, get an API key, and call any frontier model (OpenAI, Anthropic, Google, open-source) through one endpoint with one auth pattern — pay-as-you-go, usage on the dashboard.

**Demo script.** `curl https://api.cortex.mlytics.com/v1/chat -H "Authorization: Bearer ..." -d '{"model":"claude-opus-4-6","messages":[...]}'`. Switch model to `gpt-4o`. Same call signature works. Open dashboard → see token spend per model.

**In scope.** Unified API gateway (OpenAI-compatible chat completions schema). Multi-provider routing. Per-key usage metering. API key console. Docs site with quickstart + SDK snippets (Python, TS).

**Out of scope.** Streaming (v2). Function calling parity across providers (best-effort initially). Fine-tuning. Embeddings (separate product slice if demand).

**Success metric.** ≥100 developers signed up. Median TTFE (time to first call) under 10 min.

**Dependencies.** X1, X2 (PAYG billing meter).

---

#### 4. X3 — Connectors marketplace v1 (top 8 LIVE)

| Field | Value |
|---|---|
| **Family** | X |
| **Persona** | All three (different connector subsets per persona) |
| **Maps to surfaces** | Connectors page (4 sections × persona-filtered tiles) |
| **Maps to product** | Enables agents that read from external systems |
| **Size** | L |

**Value statement.** A user can connect their first 1–2 systems (GA4, WordPress, Stripe, Mailchimp) in under 5 minutes via OAuth and see the LIVE pill light up — and from that moment, persona-relevant agents can actually read their data.

**Demo script.** From Discover, click an empty agent card → "Connect Google Analytics 4." OAuth pops, scopes confirmed, redirect back. Connector tile flips to LIVE. Reader Insight agent now shows a real WAU number instead of "—".

**In scope.** OAuth/webhook framework with status pill state machine. First wave LIVE: GA4, WordPress, Notion, Stripe, Mailchimp, Substack, Shopify, plus one TW publisher (鉅亨網) for Citation Network proof. Persona-filtered connector catalog UI. Citation Network publisher tiles (16 publishers in prototype) wired to read-only registry.

**Out of scope.** All AVAILABLE-only tiles (Beehiiv, Medium, Buffer, AdSense, ETtoday, 商業周刊). Citation Network at full 18 publishers — that is BD-led work in parallel. BYO connectors / SDK. Budget controls per connector.

**Success metric.** Median time-to-first-connector under 5 min. ≥80% of pilot orgs have at least 1 LIVE connector after week 1.

**Dependencies.** X1. Per-connector BD/legal — track separately. Pre-flight Q5 must resolve "yes" before publisher tiles ship as LIVE.

---


### Later — 3–6+ months — 8 slices

#### 1. CO3 — Content Pilot + Distribution to Citation Network

| Field | Value |
|---|---|
| **Family** | CO |
| **Persona** | Content Owner |
| **Maps to surfaces** | Discover (Content Pilot card + Distribution Pilot card) |
| **Maps to product** | Decisive Engine + Citation Network amplification |
| **Size** | L |

**Value statement.** A publisher can ask Content Pilot "what should I write next?" and get topic recommendations grounded in their CMS archive and reader Q&A signal — then Distribution Pilot pushes the article into the Citation Network where partner publishers can cite it.

**Demo script.** Click Content Pilot → "What topic should we cover this week?" Agent returns 3 ideas with rationale, citing reader Q&A frequency from CO1. Owner publishes draft. Click Distribution Pilot → publishes to 鉅亨網 + 遠見 + 經理人 with cross-citation. Watch citation counter on Discover increment.

**In scope.** Content Pilot agent (CMS + Q&A logs + GA4 as tools). Content Love Score composite metric. Distribution Pilot agent (publisher partner API integration for first 3 partners). Cross-publisher citation tracking.

**Out of scope.** Generative drafting (Content Pilot recommends, doesn't write). Automated SEO optimization. Distribution to publishers outside the named Citation Network. BD work to add new publisher partners.

**Success metric.** ≥3 publisher partners in Citation Network with active two-way citation traffic. ≥10 articles published with Content Pilot input per pilot org per month.

**Dependencies.** X1, X3, CO1 (Q&A logs as input), CO2 (KPI service). BD: signed partnership agreements with first 3 Citation Network publishers.

---

#### 2. CO4 — Monetize Lens → Full Conversation CPL

| Field | Value |
|---|---|
| **Family** | CO |
| **Persona** | Content Owner (with Brand handoff) |
| **Maps to surfaces** | Discover (Monetize Lens card) + new "Earnings" subview |
| **Maps to product** | Full Conversation (CPL billing) |
| **Size** | XL |

**Value statement.** Every qualified Q&A interaction on a publisher becomes a billable lead routed to a paying brand — publisher sees per-conversation revenue, brand sees the qualified intent, money moves.

**Demo script.** Reader on 鉅亨網 asks credit-card mileage Q (CO1). Cortex matches intent to a paying brand (B2 Lead Pilot inventory). Reader sees a sponsored answer with disclosure. If reader clicks through and converts, publisher sees the CPL hit Earnings ($512 / 1K conv. — the prototype number realized).

**In scope.** Intent matching engine (cross-publisher demand graph). Sponsored answer rendering inside CO1 widget with disclosure. CPL billing pipeline (publisher revenue share + brand spend). Earnings subview on Content Owner Discover. Editorial guardrails for sponsored vs. organic answers.

**Out of scope.** Real-time bidding marketplace (manual rate cards in v1). Multi-brand auctions per intent. Affiliate-network integrations (Amazon, etc.). Refund / dispute flows beyond manual.

**Success metric.** First $X of CPL revenue paid out. Publisher trust score (no editorial complaints). ≥1 brand actively spending against publisher inventory.

**Dependencies.** X1, X2 (billing primitives), CO1 (widget + Q&A logs), B2 (Lead Pilot demand side). This slice has the highest dependency cost — schedule it after both supply and demand sides are warm. **CO4 is the slice that proves the entire Mlytics thesis.**

---

#### 3. B4 — Sales Converter (intent → CRM)

| Field | Value |
|---|---|
| **Family** | B |
| **Persona** | Brand Customer |
| **Maps to surfaces** | Discover (Sales Converter card) |
| **Maps to product** | Lead Pilot extension |
| **Size** | M |

**Value statement.** Every qualified intent flows automatically to the brand's sales tooling with the full context of why it qualified — no copy-paste, no missed leads.

**Demo script.** Sales rep gets a Salesforce notification: new lead with attached "Cortex intent context" (publisher source, query asked, KB excerpts the reader saw). Rep opens the lead in their normal workflow with everything they need to follow up.

**In scope.** Bidirectional Salesforce + HubSpot sync. Intent context object schema. Per-rep routing rules. Conversion-back signal (closed-won feeds CPQ + improves matching). 78% fill rate target.

**Out of scope.** Pipedrive, Zoho, Microsoft Dynamics (later). Marketing automation (Marketo, Pardot). Lead enrichment / scoring beyond what Lead Pilot delivers.

**Success metric.** 78% fill rate (matching prototype claim) — qualified leads with full context attached. ≤5min lead delivery latency.

**Dependencies.** X1, X3 (CRM connectors), B2 (Lead Pilot is the producer).

---

#### 4. D2 — Decisive Engine API (autonomous routing)

| Field | Value |
|---|---|
| **Family** | D |
| **Persona** | Developer |
| **Maps to surfaces** | Developer landing → Decisive Engine console (basic) |
| **Maps to product** | Decisive Engine API ($1K/mo Pro · $5K/mo Enterprise + SLA) |
| **Size** | L |

**Value statement.** A developer can configure cost / latency / quality preferences and the Decisive Engine routes each request to the cheapest model that meets their bar — and prove it reduced their model spend.

**Demo script.** Set policy: "minimize cost, p95 latency <2s, quality ≥ GPT-4 Turbo on math benchmark." Send 1000 requests. Dashboard shows: 60% routed to Claude Haiku (cheap), 30% Sonnet (medium), 10% Opus (hard). Total cost cut by 47%.

**In scope.** Routing policy DSL. Per-request classifier (question difficulty + domain). Cost / latency / quality SLA. Routing decision log (auditable). Pro tier billing meter.

**Out of scope.** Real-time policy editing during traffic. Multi-region routing (US+EU+APAC) — Enterprise tier only initially. Custom classifier training.

**Success metric.** First customer with ≥30% verifiable cost reduction. ≥10 paying Decisive Engine accounts.

**Dependencies.** X1, X2, D1 (unified API is the substrate).

---

#### 5. D3 — Bring Your Own (BYO model / CDN)

| Field | Value |
|---|---|
| **Family** | D |
| **Persona** | Developer (Enterprise) |
| **Maps to surfaces** | BYO console (Enterprise-gated) |
| **Maps to product** | Decisive Engine BYO (custom contract) |
| **Size** | L |

**Value statement.** An Enterprise developer brings their own provider contracts (e.g., Azure OpenAI commit, Cloudflare CDN) and Cortex routes through them — preserving their procurement and compliance while gaining Cortex's intelligence.

**Demo script.** Developer connects Azure OpenAI deployment + Cloudflare account. BYO console verifies. Decisive Engine policies now include BYO routes. Cost dashboard shows split: Cortex-hosted vs. BYO usage.

**In scope.** BYO model adapters (Azure, Bedrock, Vertex, self-hosted). BYO CDN adapters (Cloudflare, Akamai, Fastly). Adapter health monitoring. Compliance / audit log support.

**Out of scope.** Self-service BYO (Enterprise + solutions architect only initially). On-prem deployment of Cortex itself. White-labeled API surface.

**Success metric.** ≥2 Enterprise customers using BYO at >$50K/yr commit each. Zero compliance escalations.

**Dependencies.** X1, X2, X4 (often co-sold with KB), D1, D2.

---

#### 6. L1 — Custom Agent builder

| Field | Value |
|---|---|
| **Family** | L |
| **Persona** | All three (advanced users) |
| **Maps to surfaces** | Discover ("+ Custom Agent" slot in agent grid) |
| **Maps to product** | Pro / Enterprise feature |
| **Size** | L |

**Value statement.** A user can build a new agent in their persona dashboard from a template — pick tools (KB / connectors), prompt, name, icon — and pin it next to the preset agents.

**Demo script.** Click "+ Custom Agent." Pick template "research analyst." Connect: KB + Audience research source + Brand Monitor as tool. Name "Quarterly Briefing." Save. New card appears in Discover grid. Run it.

**In scope.** Agent builder UI. Template library (3–5 templates per persona). Tool picker. Prompt editor. Agent sharing within org. Run history.

**Out of scope.** Marketplace of community-built agents. Code-level agent customization. Multi-step / DAG agents (single-prompt-with-tools only). External agent SDK.

**Success metric.** ≥40% of Pro orgs build at least 1 custom agent within 30 days of GA.

**Dependencies.** X1, X3, X4, agent runtime, plus at least 2 persona slices shipped (so users have a frame for what an agent does).

---

#### 7. L2 — Cortex tab (intelligence / classifier console)

| Field | Value |
|---|---|
| **Family** | L |
| **Persona** | All three (advanced) |
| **Maps to surfaces** | Cortex tab (currently a wireframe stub) |
| **Maps to product** | Cortex sub-product (intelligence layer) |
| **Size** | XL |

**Value statement.** A user can configure routing policies, inspect classifier outputs, and tune confidence thresholds — making the AI decisions in their stack auditable and tuneable.

**Demo script.** Open Cortex tab. See a flow: incoming request → classifier (intent type, confidence) → router → model. Adjust confidence threshold. Watch routing rates shift in the live counter.

**In scope.** Classifier introspection UI. Confidence threshold controls. Routing decision visualization. Policy diff view. Audit log export.

**Out of scope.** Custom classifier training (BYO classifier model). Multi-tenant policy library. Real-time A/B of policies on production traffic.

**Success metric.** Defined post-pilot of L2.

**Dependencies.** X1, D2 (Decisive Engine API is the runtime this exposes).

---

#### 8. L4 — Partnership program live

| Field | Value |
|---|---|
| **Family** | L |
| **Persona** | All three (GTM motion) |
| **Maps to surfaces** | Public Partnership page → Partner dashboard (post-approval) |
| **Maps to product** | Affiliate (20% recurring · 24mo) · Referral ($2K credit each side) · Reseller (up to 35% margin) |
| **Size** | M |

**Value statement.** A partner can apply, get approved, get a tracked referral link, and earn measurable revenue — in a real funnel, not a contact-form-to-spreadsheet motion.

**Demo script.** Submit Affiliate application on Partnership page. Auto-approve email arrives. Partner dashboard shows tracked link + payout balance. Referred customer signs up via link → partner sees commission accrue in real time.

**In scope.** Application form + auto-approval rules per track. Partner dashboard (link, balance, attribution). Stripe payout integration for monthly affiliate / referral credits. Reseller manual workflow (no self-serve).

**Out of scope.** Multi-tier affiliate (sub-affiliates). Co-branded partner portals. Marketplace listings.

**Success metric.** First partner-attributed paying customer. ≥10 active affiliates with click traffic.

**Dependencies.** X1, X2 (billing primitives — payouts inverse of charges).

---


## Now / Next / Later summary

| Horizon | Slice | Title |
|---|---|---|
| **NOW** | B3 | Brand Embed (publisher placements) |
| **NOW** | X2 | Pricing → contracted seats live |
| **NOW** | X1 | Sign-up to persona-tuned empty Discover |
| **NOW** | X5 | Mlytics Ops Admin (Brand × Article placement) |
| **NOW** | B1 | Brand Monitor → Media GEO Lite |
| **NOW** | B2 | Audience Finder + Lead Pilot |
| **NEXT** | X4 | Knowledge Base [Enterprise] |
| **NEXT** | CO2 | Reader Insight Dashboard |
| **NEXT** | D1 | Unified Model API (one key, every model) |
| **NEXT** | X3 | Connectors marketplace v1 (top 8 LIVE) |
| **LATER** | CO3 | Content Pilot + Distribution to Citation Network |
| **LATER** | CO4 | Monetize Lens → Full Conversation CPL |
| **LATER** | B4 | Sales Converter (intent → CRM) |
| **LATER** | D2 | Decisive Engine API (autonomous routing) |
| **LATER** | D3 | Bring Your Own (BYO model / CDN) |
| **LATER** | L1 | Custom Agent builder |
| **LATER** | L2 | Cortex tab (intelligence / classifier console) |
| **LATER** | L4 | Partnership program live |

---

## Critical path and risks

The narrowest critical path through *Now* and into *Next* depends on which slices are sequenced where. Re-derive after each reordering — pay particular attention to two-sided slices (CO4 needs both a Content Owner supply slice and a Brand demand slice warm) and to platform foundations that gate multiple persona slices (X1, X3).

Three risks that persist regardless of ordering:

1. **Citation Network is a BD program, not a feature.** The 18 publishers in the prototype need signed agreements before CO3/CO4 can demo. Track the BD pipeline as if it were a slice with its own owner and dates.
2. **AI surface scraping (B1) has legal exposure.** ChatGPT, Perplexity, and Gemini terms of service vary. Get legal sign-off before pilot, not after.
3. **The platform foundations are owned by *no one* in the slice list.** Before *Now* horizon starts, name a single platform owner and protect ~30% of their capacity from feature slices.

---

*Source documents:* [product-narrative.md](./product-narrative.md) · [prototype-walkthrough.md](./prototype-walkthrough.md) · [cortex-prototype.html](./cortex-prototype.html) · [cortex-4week-plan-v3.html](./cortex-4week-plan-v3.html)
