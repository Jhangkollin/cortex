"use client";

/**
 * Brand onboarding v2 wizard (zh-TW) — shared between the live route
 * (/onboarding/v2/zh-TW) and the public demo route (/demo/onboarding/zh-TW).
 *
 * `mode="live"` is the production flow: writes a vestigial completion flag
 * to localStorage (current behaviour preserved), threads through to the
 * caller-supplied `completeV2Onboarding` server action on Enter Discover,
 * and falls through to /brand/dashboard on success.
 *
 * `mode="demo"` is the public, auth-free clone: localStorage writes become
 * no-ops, `onComplete` is intentionally omitted, and Enter Discover
 * restarts the wizard so the next demo viewer sees step 0.
 *
 * All wizard data continues to flow through the OnboardingApi seam —
 * the live caller passes `getOnboardingApi()`, the demo caller passes
 * `new MockOnboardingApi()` directly.
 */

import type { Route } from "next";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  createAnotherBrandAction,
  listMyBrandsAction,
} from "@/app/(auth)/onboarding/v2/add-brand-actions";
import type { BrandListItem } from "@/lib/cortex-api";

import type {
  CrawlTask,
  DeployAgent,
  DeployLogLine,
  ExtractedBrand,
  LiveQuestion,
  Media,
  VoiceTone,
} from "@/components/onboarding-v2-zh/data";
import { EXTRACTED_BRAND, RAIL_STEPS, type InternalStep, railFor } from "@/components/onboarding-v2-zh/data";
import { LaunchOverlay } from "@/components/onboarding-v2-zh/launch-overlay";
import { Badge, Icon, OnbButton, TopBar } from "@/components/onboarding-v2-zh/primitives";
import { StepComplete } from "@/components/onboarding-v2-zh/step-complete";
import { StepCrawl } from "@/components/onboarding-v2-zh/step-crawl";
import { StepLaunch } from "@/components/onboarding-v2-zh/step-launch";
import { StepMedia } from "@/components/onboarding-v2-zh/step-media";
import { StepQuestions } from "@/components/onboarding-v2-zh/step-questions";
import { StepReview } from "@/components/onboarding-v2-zh/step-review";
import { StepPreparingReport } from "@/components/onboarding-v2-zh/step-preparing-report";
import { StepWelcome } from "@/components/onboarding-v2-zh/step-welcome";
import type { OnboardingApi } from "@/lib/onboarding/api";

const STORAGE_KEY = "cortex.onboarding.v2";

// Single source of truth for the demo's initial brand URL. Used for the
// initial `url` state and by restart() — never inline the literal so adding
// a real entered-URL flow is a one-line change.
const INITIAL_URL = "acmebank.asia";

export type WizardMode = "live" | "demo";

type LoadStatus = "idle" | "loading" | "ready" | "error";

export function OnboardingV2WizardZh({
  mode,
  api,
  onComplete,
  autoPlay = false,
  loop = false,
}: {
  mode: WizardMode;
  api: OnboardingApi;
  onComplete?: () => Promise<void>;
  /**
   * Demo-only kiosk mode. When true (and mode === "demo"), the wizard
   * advances itself through every step on timers, without any clicks.
   * Triggered by `?auto=1` on the demo route.
   */
  autoPlay?: boolean;
  /**
   * When true with autoPlay, step 7 (success screen) auto-restarts back
   * to step 0 after a viewing pause — turns the demo URL into a TV-screen
   * loop. Triggered by `?loop=1` on the demo route.
   */
  loop?: boolean;
}) {
  const router = useRouter();
  const { update: updateSession, data: sessionData } = useSession();

  // Always start at the welcome step. We deliberately do NOT read the
  // persisted `complete` flag to fast-forward returning users to the
  // success screen — that made the flow impossible to re-watch (every
  // reload after one completed run jumped straight to the final page).
  const [step, setStep] = useState<InternalStep>(0);

  const [url, setUrl] = useState(INITIAL_URL);
  const [brand, setBrand] = useState<ExtractedBrand | null>(null);
  const [pickedMedia, setPickedMedia] = useState<string[]>([]);
  const [voiceTone, setVoiceTone] = useState<VoiceTone["id"]>("expert");
  const [completeError, setCompleteError] = useState<string | null>(null);

  // After a successful real completion we hand off to the post-onboarding
  // report-preparing interstitial (Brand IQ celebration) INSTEAD of jumping
  // straight to the dashboard. Demo mode never sets this — it restarts.
  const [showPreparing, setShowPreparing] = useState(false);

  // Per-step data loaded through the OnboardingApi seam.
  const [crawlTasks, setCrawlTasks] = useState<CrawlTask[]>([]);
  const [mediaNetwork, setMediaNetwork] = useState<Media[]>([]);
  const [liveQuestions, setLiveQuestions] = useState<LiveQuestion[]>([]);
  const [voiceTones, setVoiceTones] = useState<VoiceTone[]>([]);
  const [deployAgents, setDeployAgents] = useState<DeployAgent[]>([]);
  const [deployLog, setDeployLog] = useState<DeployLogLine[]>([]);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>("idle");

  // Multi-brand: list of brands the user already has (loaded on mount).
  // Used to show the PortfolioBand and "新增品牌" CTA on step 7.
  const [brands, setBrands] = useState<BrandListItem[]>([]);
  const [addBrandBusy, setAddBrandBusy] = useState(false);
  const [addBrandError, setAddBrandError] = useState<string | null>(null);

  // Load the caller's brand list on mount so StepComplete can show the
  // multi-brand variant if the user already has >= 2 brands after this
  // onboarding run. Empty on error — never throws.
  // Loaded at mount: the just-completing brand shows "indexing" in the
  // PortfolioBand even after completeV2Onboarding stamps onboarded_at, since
  // we don't re-fetch. Acceptable — the user is about to navigate to
  // /brand/dashboard or restart for a new brand.
  useEffect(() => {
    if (mode !== "live") return;
    let cancelled = false;
    void (async () => {
      const list = await listMyBrandsAction();
      if (!cancelled) setBrands(list);
    })();
    return () => { cancelled = true; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Modeled wizard scaffolding (crawl tasks, questions, agents, deploy log).
  // Loaded once at mount so step 0 is immediately interactive.
  // NOTE: mediaNetwork 與 voiceTones 都 NOT loaded here — both are REAL
  // cortex-api calls that need the brand profile (persisted by analyze) AND
  // an active brand session. They are fetched in runAnalyze() after analyze
  // succeeds.
  const loadModeled = useCallback(async () => {
    try {
      // 注意：media、weekly-questions、語氣樣本都不在這裡載入；它們在
      // HttpOnboardingApi 下都是 REAL cortex-api 呼叫，需要 analyze 剛持久化的
      // brand profile 與啟用中的 brand session — mount 階段都還沒有。它們在
      // analyze 成功後於 runAnalyze() 內各自的 isolated void-async block 中載入。
      const [tasks, agents, log] = await Promise.all([
        api.getCrawlTasks(),
        api.getDeployAgents(),
        api.getDeployLog(),
      ]);
      setCrawlTasks(tasks);
      setDeployAgents(agents);
      setDeployLog(log);
    } catch {
      // Modeled data is local constants today; a transient failure here is
      // non-fatal — the wizard chrome still renders.
    }
  }, [api]);

  // The slow path: the real brand extraction (HttpOnboardingApi →
  // Server Action → cortex-api async analyze + poll, ~25s). Owns
  // loadStatus so StepCrawl can show the live scanning animation while
  // this is in flight and the wizard surfaces a retry on failure.
  const runAnalyze = useCallback(async (analyzeUrl: string) => {
    try {
      const extractedBrand = await api.analyzeBrand(analyzeUrl);
      setBrand(extractedBrand);
      setLoadStatus("ready");
      // Media network is a REAL backend call (LLM-ranked against the brand
      // profile analyze just persisted). Kick it off now — NOT awaited
      // before `ready`, so StepCrawl's Continue isn't blocked — it
      // populates while the user is on Review (step 2) so step 3 is ready.
      // Isolated catch: a media failure must not flip the analyze status.
      void (async () => {
        try {
          const network = await api.getMediaNetwork();
          setMediaNetwork(network);
          setPickedMedia(network.filter((m) => m.picked).map((m) => m.id));
        } catch {
          // Non-fatal: analyze succeeded; step 3 shows no outlets rather
          // than crashing the wizard. Real error surface stays on analyze.
        }
      })();
      // weekly-questions 同樣是 REAL backend call — 獨立的 isolated block。
      void (async () => {
        try {
          const lq = await api.getLiveQuestions();
          setLiveQuestions(lq);
        } catch {
          // 非致命：analyze 已成功；步驟 4 顯示空列表而不崩潰精靈。
        }
      })();
      // 語氣樣本同樣是 REAL backend call（依 analyze 剛存下的品牌 profile
      // 設定）— 與 media/questions 相同的 d8345ff 形狀。獨立的 isolated block：
      // 語氣失敗不可翻轉 analyze 狀態，也不可與其他 fetch 耦合。
      void (async () => {
        try {
          const tones = await api.getVoiceTones();
          setVoiceTones(tones);
        } catch {
          // 非致命：analyze 已成功；步驟 5 退回使用常數語氣樣本。
        }
      })();
    } catch {
      setLoadStatus("error");
    }
  }, [api]);

  // Mount: load only the instant modeled scaffolding. The real analyze is
  // user-triggered at step 0 (onAnalyze) — NOT on mount.
  useEffect(() => {
    // `loadModeled` only mutates state inside async continuations (after
    // `await` / in `catch`), so this is not a synchronous setState-in-
    // effect; the lint rule can't see across the useCallback boundary.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadModeled();
  }, [loadModeled]);

  const railStep = railFor(step);
  // Footer rail is shown for the multi-page navigable section: review (2) →
  // launch settings (5). Welcome/crawl have inline CTAs; overlay has none;
  // complete carries its own CTA.
  const showFooter = step >= 2 && step <= 5;

  const next = useCallback(
    () => setStep((s) => Math.min(s + 1, 7) as InternalStep),
    [],
  );
  const back = useCallback(
    () => setStep((s) => Math.max(s - 1, 2) as InternalStep),
    [],
  );

  const skipAll = useCallback(() => {
    if (mode === "live") {
      try {
        localStorage.setItem(STORAGE_KEY, "complete");
      } catch {
        // ignore — privacy-mode browsers; non-fatal
      }
    }
    setStep(7);
  }, [mode]);

  const restart = useCallback(() => {
    if (mode === "live") {
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch {
        // ignore
      }
    }
    setStep(0);
    setUrl(INITIAL_URL);
    setVoiceTone("expert");
    setBrand(null);
    // Media network is brand-specific and fetched per analyze — clear it
    // so a re-analyze refetches for the new brand instead of showing the
    // previous brand's outlets.
    setMediaNetwork([]);
    setPickedMedia([]);
    // Weekly questions are brand-specific and fetched per analyze — clear.
    setLiveQuestions([]);
    // 語氣樣本與品牌綁定、每次 analyze 重新抓取（同 media/questions）— 清空以便
    // 重新 analyze 時為新品牌重抓，而非沿用前一個品牌的語氣樣本。
    setVoiceTones([]);
    // Back to URL entry. Modeled scaffolding is already loaded; the real
    // analyze re-runs when the user clicks Analyze again (onAnalyze).
    setLoadStatus("idle");
  }, [mode]);

  const launch = useCallback(() => setStep(6), []);
  const launchDone = useCallback(() => {
    if (mode === "live") {
      try {
        localStorage.setItem(STORAGE_KEY, "complete");
      } catch {
        // ignore
      }
    }
    setStep(7);
  }, [mode]);

  const handleEnterDiscover = useCallback(async () => {
    if (mode === "demo" || !onComplete) {
      // Demo mode (no server action wired). Restart so the next viewer sees
      // step 0 instead of being stuck on the success screen.
      restart();
      return;
    }
    try {
      await onComplete();
    } catch (e) {
      setCompleteError(
        e instanceof Error ? e.message : "無法完成設定，請再試一次。",
      );
      return;
    }
    // Route through the report-preparing interstitial (Brand IQ celebration)
    // rather than navigating straight to the dashboard. The interstitial owns
    // the final hop to /brand/dashboard via its onDone.
    setShowPreparing(true);
  }, [mode, onComplete, restart]);

  // Creates a new brand, refreshes the JWT to carry the new activeContext,
  // clears the wizard's localStorage completion flag, and navigates back to
  // /onboarding/v2 so the wizard restarts against the new brand_id.
  // Guarded against double-clicks with addBrandBusy.
  const onAddBrand = useCallback(async () => {
    if (addBrandBusy) return;
    setAddBrandError(null);
    setAddBrandBusy(true);
    try {
      const { activeContext } = await createAnotherBrandAction();
      await updateSession({ activeContext });
      try { localStorage.removeItem(STORAGE_KEY); } catch { /* storage may be unavailable */ }
      router.push("/onboarding/v2");
    } catch (e) {
      setAddBrandBusy(false);
      setAddBrandError(e instanceof Error ? e.message : "無法新增品牌，請再試一次。");
      console.warn("[onboarding] add-another failed", e);
    }
  }, [addBrandBusy, router, updateSession]);

  const langSwitchHref = (mode === "demo"
    ? "/demo/onboarding"
    : "/onboarding/v2") as Route;

  // Auto-play orchestrator (demo + ?auto=1 only). Schedules a single timer
  // for each step transition and clears it on cleanup. Steps 1 and 6 wait
  // on async signals (loadStatus / overlay's isFinishing) before advancing.
  // LaunchOverlay handles its own step-6→7 transition via its autoPlay prop.
  useEffect(() => {
    if (!autoPlay || mode !== "demo") return;
    let id: ReturnType<typeof setTimeout> | null = null;
    if (step === 0) {
      id = setTimeout(() => {
        setLoadStatus("loading");
        void runAnalyze(url);
        setStep(1);
      }, 1500);
    } else if (step === 1 && loadStatus === "ready" && brand !== null) {
      id = setTimeout(() => setStep(2), 6000);
    } else if (step === 2 || step === 3 || step === 4) {
      id = setTimeout(() => setStep((s) => (s + 1) as InternalStep), 4000);
    } else if (step === 5) {
      id = setTimeout(() => launch(), 5000);
    } else if (step === 7 && loop) {
      id = setTimeout(() => restart(), 8000);
    }
    return () => {
      if (id !== null) clearTimeout(id);
    };
  }, [autoPlay, mode, loop, step, loadStatus, brand, url, runAnalyze, launch, restart]);

  // Scroll orchestrator (autoplay-only). The wizard's content can exceed
  // the viewport on review (2), media (3), questions (4), and launch (5);
  // without explicit scroll handling a viewer can be parked at the bottom
  // of one step when the next step mounts and miss its header entirely.
  // On every step entry, snap to top; then halfway through the viewing
  // pause, slow-scroll to the bottom of the new content so both halves
  // are seen before the next transition. Step 6 (fixed overlay) and step
  // 7 (short success screen) are exempt.
  useEffect(() => {
    if (!autoPlay || mode !== "demo") return;
    if (typeof window === "undefined") return;
    window.scrollTo({ top: 0, behavior: "smooth" });
    if (step >= 2 && step <= 5) {
      const panId = setTimeout(() => {
        window.scrollTo({
          top: document.documentElement.scrollHeight,
          behavior: "smooth",
        });
      }, 2500);
      return () => clearTimeout(panId);
    }
  }, [autoPlay, mode, step]);

  // Post-onboarding takeover. Once a real completion succeeds we hand the
  // whole screen to the report-preparing interstitial; it polls report state,
  // shows the Brand IQ celebration when ready, and performs the final hop to
  // the dashboard via onDone. Returned before the wizard step tree so it fully
  // replaces it. Never reached in demo mode (demo restarts instead).
  if (showPreparing) {
    return (
      <StepPreparingReport onDone={() => router.push("/brand/dashboard")} />
    );
  }

  // Error-only gate. Loading is intentionally NOT gated here: step 0 (URL
  // entry) and step 1 (StepCrawl's live scanning animation) must render
  // *during* the real ~25s analyze — that animation is the loading UX.
  // Brand-dependent steps (>=2) are only reachable via StepCrawl's
  // Continue, which is itself gated on loadStatus === "ready".
  if (loadStatus === "error") {
    return (
      <div
        className="onboarding-v2-root"
        style={{
          minHeight: "100vh",
          background: "var(--mly-ink-025)",
          display: "grid",
          placeItems: "center",
          padding: "40px 20px",
        }}
      >
        <div
          role="alert"
          style={{
            maxWidth: 420,
            textAlign: "center",
            background: "#fff",
            border: "1px solid var(--mly-ink-150)",
            borderRadius: 12,
            padding: "32px 28px",
          }}
        >
          <div
            style={{
              width: 44,
              height: 44,
              margin: "0 auto 14px",
              borderRadius: "50%",
              display: "grid",
              placeItems: "center",
              background: "var(--mly-ink-050)",
            }}
          >
            <Icon name="error_outline" size={22} color="var(--mly-ink-600)" />
          </div>
          <div
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: "var(--mly-ink-900)",
              marginBottom: 6,
            }}
          >
            無法載入 onboarding
          </div>
          <div
            style={{
              fontSize: 13,
              color: "var(--mly-ink-600)",
              lineHeight: 1.6,
              marginBottom: 20,
            }}
          >
            品牌分析的其中一個步驟沒有回應。資料不會遺失，請再試一次。
          </div>
          <OnbButton
            variant="primary"
            size="lg"
            icon="refresh"
            onClick={() => {
              setLoadStatus("loading");
              void runAnalyze(url);
            }}
          >
            重試
          </OnbButton>
        </div>
      </div>
    );
  }

  return (
    <div
      className="onboarding-v2-root"
      style={{
        minHeight: "100vh",
        background: "var(--mly-ink-025)",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {step <= 5 ? (
        <TopBar
          railStep={railStep}
          steps={RAIL_STEPS}
          onSkip={skipAll}
          onExit={restart}
          showDemoBadge={mode === "demo"}
          langSwitchHref={langSwitchHref}
        />
      ) : step === 6 ? null : (
        // Step 7 — slimmer "Brand Agent 已上線" topbar.
        <div
          style={{
            background: "#fff",
            borderBottom: "1px solid var(--mly-ink-150)",
            padding: "14px 0",
            position: "sticky",
            top: 0,
            zIndex: 50,
          }}
        >
          <div
            className="onb-rail"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: 6,
                  background: "var(--mly-teal-800)",
                  color: "#fff",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: 700,
                }}
              >
                C
              </div>
              {mode === "demo" ? <Badge color="ink">Demo</Badge> : null}
              <div>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 700,
                    color: "var(--mly-ink-900)",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <span
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: "50%",
                      background: "var(--mly-success)",
                      animation: "mly-pulse 1.4s infinite",
                    }}
                  />
                  Brand Agent 已上線
                </div>
                <div style={{ fontSize: 11, color: "var(--mly-ink-500)", marginTop: 1 }}>
                  {brand?.name ?? "你的品牌"} · onboarding 完成
                </div>
              </div>
            </div>
            <OnbButton variant="soft" size="sm" icon="restart_alt" onClick={restart}>
              重新做一次
            </OnbButton>
          </div>
        </div>
      )}

      {step !== 6 ? (
        <div style={{ flex: 1, padding: showFooter ? "32px 0 100px" : "32px 0 60px" }}>
          <div className="onb-rail">
            {step === 0 ? (
              <StepWelcome
                url={url}
                setUrl={setUrl}
                onAnalyze={() => {
                  setLoadStatus("loading");
                  void runAnalyze(url);
                  setStep(1);
                }}
                onManual={() => setStep(2)}
              />
            ) : null}
            {step === 1 ? (
              <StepCrawl
                url={url}
                ready={loadStatus === "ready" && brand !== null}
                brand={brand}
                onComplete={() => {
                  if (loadStatus === "ready" && brand !== null) setStep(2);
                }}
                crawlTasks={crawlTasks}
              />
            ) : null}
            {step === 2 && brand ? (
              <StepReview
                brand={brand}
                setBrand={(b) => setBrand(b)}
                onConfirm={() => setStep(3)}
              />
            ) : null}
            {step === 3 && brand ? (
              <StepMedia
                brand={brand}
                picked={pickedMedia}
                setPicked={setPickedMedia}
                mediaNetwork={mediaNetwork}
              />
            ) : null}
            {step === 4 && brand ? (
              <StepQuestions brand={brand} liveQuestions={liveQuestions} />
            ) : null}
            {step === 5 && brand ? (
              <StepLaunch
                brand={brand}
                pickedMedia={pickedMedia}
                voiceTone={voiceTone}
                setVoiceTone={setVoiceTone}
                onLaunch={launch}
                mediaNetwork={mediaNetwork}
                voiceTones={voiceTones}
                liveQuestions={liveQuestions}
              />
            ) : null}
            {step === 7 ? (
              <>
                <StepComplete
                  brand={brand ?? EXTRACTED_BRAND}
                  pickedMedia={pickedMedia}
                  onRestart={restart}
                  onEnterDiscover={() => void handleEnterDiscover()}
                  mediaNetwork={mediaNetwork}
                  brands={brands}
                  justOnboardedBrandId={sessionData?.user?.activeContext?.id ?? ""}
                  onAddBrand={mode === "live" ? () => void onAddBrand() : undefined}
                  addBrandBusy={addBrandBusy}
                  addBrandError={addBrandError}
                />
                {completeError ? (
                  <div
                    role="alert"
                    style={{
                      maxWidth: 420,
                      margin: "12px auto 0",
                      background: "#fff",
                      border: "1px solid var(--mly-ink-150)",
                      borderRadius: 12,
                      padding: "14px 18px",
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                    }}
                  >
                    <span
                      className="material-icons-outlined"
                      style={{ fontSize: 18, color: "var(--mly-ink-600)", flexShrink: 0 }}
                      aria-hidden
                    >
                      error_outline
                    </span>
                    <span
                      style={{
                        fontSize: 13,
                        color: "var(--mly-ink-600)",
                        lineHeight: 1.5,
                      }}
                    >
                      {completeError}
                    </span>
                  </div>
                ) : null}
              </>
            ) : null}
          </div>
        </div>
      ) : null}

      {step === 6 ? (
        <LaunchOverlay
          onDone={launchDone}
          deployAgents={deployAgents}
          deployLog={deployLog}
          mediaNetwork={mediaNetwork}
          autoPlay={autoPlay && mode === "demo"}
        />
      ) : null}

      {showFooter ? (
        <div
          style={{
            position: "sticky",
            bottom: 0,
            background: "#fff",
            borderTop: "1px solid var(--mly-ink-150)",
            padding: "12px 0",
            zIndex: 20,
            boxShadow: "0 -6px 18px rgba(0,0,0,0.04)",
          }}
        >
          <div
            className="onb-rail"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                fontSize: 12,
                color: "var(--mly-ink-500)",
              }}
            >
              <span style={{ fontFamily: "var(--font-mono)" }}>
                第 {railStep + 1} / {RAIL_STEPS.length} 步
              </span>
              <span
                style={{
                  width: 4,
                  height: 4,
                  borderRadius: "50%",
                  background: "var(--mly-ink-300)",
                }}
              />
              <span>{RAIL_STEPS[railStep]}</span>
              <span
                style={{
                  width: 4,
                  height: 4,
                  borderRadius: "50%",
                  background: "var(--mly-ink-300)",
                }}
              />
              <span style={{ color: "var(--mly-ink-400)" }}>
                之後仍可在「品牌設定」隨時修改
              </span>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              {step > 2 ? (
                <OnbButton variant="soft" onClick={back} icon="arrow_back">
                  上一步
                </OnbButton>
              ) : null}
              {step < 5 ? (
                <OnbButton variant="primary" onClick={next} iconRight="arrow_forward">
                  下一步：{RAIL_STEPS[railStep + 1]}
                </OnbButton>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
