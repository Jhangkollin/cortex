/**
 * Light Edition repaint (Slice 2): StepWelcome — zh-Hant mirror of
 * ../../onboarding-v2/__tests__/step-welcome.test.tsx. Locked in lockstep
 * with the en tree so behavioural drift on either side surfaces in CI.
 *
 * Three behavioural micro-edits from handoff Appendix C/D (same contract,
 * zh-flavoured copy):
 *  - URL_SUGGESTIONS now has exactly 2 entries: "mlytics.com" and
 *    "moonbeam.io" (domain strings, untranslated). `acmebank.asia` and
 *    `verde-mobility.com` are gone.
 *  - Trust strip promises a ~60s crawl ("平均 60 秒完成爬取"), matching
 *    StepCrawl receipt's 74s timing. The legacy 90s copy must not appear.
 *  - The manual-fill fallback button ("沒有官網？手動填寫") drops the
 *    `edit_note` icon so the link reads lighter.
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StepWelcome } from "@/components/onboarding-v2-zh/step-welcome";

function renderWelcome() {
  return render(
    <StepWelcome
      url=""
      setUrl={() => undefined}
      onAnalyze={() => undefined}
      onManual={() => undefined}
    />,
  );
}

describe("StepWelcome (zh) — URL suggestions (Light Edition)", () => {
  it("renders exactly 2 suggestion buttons: mlytics.com and moonbeam.io", () => {
    renderWelcome();
    expect(screen.getByRole("button", { name: "mlytics.com" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "moonbeam.io" })).toBeInTheDocument();
    // The old demo brands must not survive the trim.
    expect(
      screen.queryByRole("button", { name: "acmebank.asia" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "verde-mobility.com" }),
    ).not.toBeInTheDocument();
  });
});

describe("StepWelcome (zh) — trust strip (Light Edition)", () => {
  it("promises a 60-second crawl, not the legacy 90s", () => {
    const { container } = renderWelcome();
    // zh copy is "平均 60 秒完成爬取"; assert on the localized "60 秒"
    // substring instead of "~60s".
    expect(container.textContent).toContain("60 秒");
    // The legacy 90s timing must not survive in either Arabic-numeral or
    // mixed form.
    expect(container.textContent).not.toContain("90 秒");
    expect(container.textContent).not.toContain("~90s");
  });
});

describe("StepWelcome (zh) — manual-fill fallback (Light Edition)", () => {
  it("renders the manual-fill text link without the edit_note icon", () => {
    const manualBtn = renderWelcome().getByRole("button", {
      name: /沒有官網.*手動填寫/,
    });
    // The icon was rendered as `<span class="material-icons-outlined">edit_note</span>`
    // inside the button. Absent its child <span>, the trimmed link
    // matches the prototype's plain-text affordance.
    expect(manualBtn.querySelector(".material-icons-outlined")).toBeNull();
    expect(manualBtn.textContent?.includes("edit_note")).toBe(false);
  });
});
