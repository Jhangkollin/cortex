/**
 * BrandReportHero state machine tests (COR-82).
 *
 * Tests:
 *   - null when heroDismissed
 *   - null when no report (latestReport == null)
 *   - skeleton "準備中…" when status == "pending" or "running"
 *   - failed state with retry button when status == "failed"
 *   - 重試 click invokes onRetry (no silent no-op)
 *   - ready state with CTA links when status == "ready"
 *   - dismiss × calls onDismiss
 */

import { describe, test, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { BrandReportHero } from "../brand-report-hero";
import type { ReportEnvelope } from "@/app/brand/dashboard/report-types";

// Minimal server-only stub — cortex-api is imported only for types here.
vi.mock("@/app/brand/dashboard/report-actions", () => ({}));

const noop = () => {};

function _report(status: ReportEnvelope["status"]): ReportEnvelope {
  return {
    reportId: "BIQ-test",
    status,
    error: status === "failed" ? "LLM timeout" : null,
    report:
      status === "ready"
        ? // Partial fixture — only `meta` fields the hero reads. Cast through
          // `unknown` because the test intentionally omits the other 14
          // required BrandIqReport fields the hero never touches.
          ({
            meta: {
              subject: "TestCo",
              monogram: "T",
              primaryMarket: "TW",
              extendedMarkets: [],
              reportDate: "2026-05-24",
              pageCount: 8,
              reportId: "BIQ-test",
            },
          } as unknown as ReportEnvelope["report"])
        : null,
  };
}

describe("BrandReportHero", () => {
  test("returns null when heroDismissed", () => {
    const { container } = render(
      <BrandReportHero
        report={_report("ready")}
        heroDismissed={true}
        onDismiss={noop}
        onRetry={noop}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  test("returns null when report is null", () => {
    const { container } = render(
      <BrandReportHero
        report={null}
        heroDismissed={false}
        onDismiss={noop}
        onRetry={noop}
      />,
    );
    expect(container.firstChild).toBeNull();
  });

  test("shows skeleton when status is pending", () => {
    render(
      <BrandReportHero
        report={_report("pending")}
        heroDismissed={false}
        onDismiss={noop}
        onRetry={noop}
      />,
    );
    expect(screen.getByText(/準備中/)).toBeInTheDocument();
  });

  test("shows skeleton when status is running", () => {
    render(
      <BrandReportHero
        report={_report("running")}
        heroDismissed={false}
        onDismiss={noop}
        onRetry={noop}
      />,
    );
    expect(screen.getByText(/準備中/)).toBeInTheDocument();
  });

  test("shows failed state with 重試 button", () => {
    render(
      <BrandReportHero
        report={_report("failed")}
        heroDismissed={false}
        onDismiss={noop}
        onRetry={noop}
      />,
    );
    expect(screen.getByText("重試")).toBeInTheDocument();
    expect(screen.getByText(/Brand IQ 報告 · 生成失敗/)).toBeInTheDocument();
  });

  test("clicking 重試 invokes onRetry", () => {
    const onRetry = vi.fn();
    render(
      <BrandReportHero
        report={_report("failed")}
        heroDismissed={false}
        onDismiss={noop}
        onRetry={onRetry}
      />,
    );
    fireEvent.click(screen.getByText("重試"));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  test("shows ready state with brand name and single primary CTA", () => {
    render(
      <BrandReportHero
        report={_report("ready")}
        heroDismissed={false}
        onDismiss={noop}
        onRetry={noop}
      />,
    );
    expect(screen.getByText(/TestCo 的品牌側寫已準備好/)).toBeInTheDocument();
    expect(screen.getByText(/查看 Brand IQ 報告/)).toBeInTheDocument();
    expect(screen.queryByText(/開啟 Report Viewer/)).toBeNull();
    expect(screen.queryByText(/下載 PDF/)).toBeNull();
  });

  test("calls onDismiss when × is clicked", () => {
    const onDismiss = vi.fn();
    render(
      <BrandReportHero
        report={_report("ready")}
        heroDismissed={false}
        onDismiss={onDismiss}
        onRetry={noop}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: /關閉/ }));
    expect(onDismiss).toHaveBeenCalledOnce();
  });

  test("primary CTA link points to /brand/reports/{reportId}", () => {
    render(
      <BrandReportHero
        report={_report("ready")}
        heroDismissed={false}
        onDismiss={noop}
        onRetry={noop}
      />,
    );
    const primaryLink = screen.getByText(/查看 Brand IQ 報告/).closest("a");
    expect(primaryLink?.href).toContain("/brand/reports/BIQ-test");
  });

  describe("Light Edition — paper-cream surface", () => {
    function readyFixture() {
      return {
        reportId: "BIQ-TEST-2",
        status: "ready" as const,
        report: {
          meta: {
            subject: "Acme Bank Asia",
            monogram: "A",
            pageCount: 8,
            reportDate: "2026-05-22",
            preparedBy: "Cortex",
          },
          productLines: [{}, {}, {}, {}, {}, {}, {}],
          mediaNetwork: [{}, {}, {}, {}, {}, {}],
          competitors: [{}, {}, {}],
          risks: [{}, {}, {}, {}],
        } as never,
      };
    }

    test("ReadyHero renders single primary CTA linking to the viewer route", () => {
      render(
        <BrandReportHero
          report={readyFixture()}
          heroDismissed={false}
          onDismiss={() => {}}
          onRetry={() => {}}
        />,
      );
      expect(screen.getByRole("link", { name: /查看 Brand IQ 報告/ })).toBeInTheDocument();
      expect(screen.queryByRole("link", { name: /開啟 Report Viewer/ })).toBeNull();
      expect(screen.queryByRole("link", { name: /下載.*PDF/ })).toBeNull();
    });

    test("ReadyHero card uses the paper-cream background token", () => {
      render(
        <BrandReportHero
          report={readyFixture()}
          heroDismissed={false}
          onDismiss={() => {}}
          onRetry={() => {}}
        />,
      );
      const titleNode = screen.getByText(/品牌側寫已準備好/);
      let el: HTMLElement | null = titleNode as HTMLElement;
      let foundPaper = false;
      while (el) {
        const bg = el.style?.background ?? "";
        if (bg.includes("var(--paper") || bg.includes("#F4EDDF")) {
          foundPaper = true;
          break;
        }
        el = el.parentElement;
      }
      expect(foundPaper).toBe(true);
    });

    test("ReadyHero dismiss × calls onDismiss", () => {
      const onDismiss = vi.fn();
      render(
        <BrandReportHero
          report={readyFixture()}
          heroDismissed={false}
          onDismiss={onDismiss}
          onRetry={() => {}}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /關閉/ }));
      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    test("returns null when heroDismissed is true", () => {
      const { container } = render(
        <BrandReportHero
          report={readyFixture()}
          heroDismissed={true}
          onDismiss={() => {}}
          onRetry={() => {}}
        />,
      );
      expect(container.firstChild).toBeNull();
    });

    test("FailedState calls onRetry on click", () => {
      const onRetry = vi.fn();
      render(
        <BrandReportHero
          report={{ reportId: "BIQ-X", status: "failed", error: "boom" } as never}
          heroDismissed={false}
          onDismiss={() => {}}
          onRetry={onRetry}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /重試/ }));
      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });
});
