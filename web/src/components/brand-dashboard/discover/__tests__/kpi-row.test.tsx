import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { KpiRow } from "../kpi-row";
import { BASE_DATA } from "@/lib/discover/mock";

describe("kpi-row", () => {
  test("renders 4 equal KPI cards with sparklines", () => {
    const { container } = render(<KpiRow kpis={BASE_DATA.kpis} />);
    expect(screen.getByText("48")).toBeInTheDocument();
    expect(screen.getByText("相關問題數 (TOP 500 抽樣)")).toBeInTheDocument();
    expect(container.querySelectorAll(".mini")).toHaveLength(4);
    expect(container.querySelectorAll(".mini-spk")).toHaveLength(4);
  });
});
