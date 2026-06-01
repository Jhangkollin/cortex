import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { KpiRow } from "../kpi-row";
import { BASE_DATA } from "@/lib/discover/mock";

describe("kpi-row", () => {
  test("renders hero value + 3 minis with sparklines", () => {
    const { container } = render(
      <KpiRow hero={BASE_DATA.hero} minis={BASE_DATA.minis} />,
    );
    expect(screen.getByText("18.4")).toBeInTheDocument();
    expect(screen.getByText("Brand-cited answers")).toBeInTheDocument();
    expect(container.querySelectorAll(".mini")).toHaveLength(3);
    expect(container.querySelectorAll(".mini-spk")).toHaveLength(3);
    expect(container.querySelector(".h-main .spk")).toBeTruthy();
  });
});
