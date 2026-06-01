import { describe, test, expect } from "vitest";
import { render } from "@testing-library/react";

import { GeoFunnel } from "../geo-funnel";
import { BASE_DATA } from "@/lib/discover/mock";

describe("geo-funnel", () => {
  test("5 blocks, 4 arrows, one is-here, bottleneck+leverage", () => {
    const { container } = render(<GeoFunnel funnel={BASE_DATA.funnel} />);
    expect(container.querySelectorAll(".fnl-nm")).toHaveLength(5);
    expect(container.querySelectorAll(".conn")).toHaveLength(4);
    expect(container.querySelectorAll(".fnl-nm.is-here")).toHaveLength(1);
    expect(container.querySelector(".conn.is-bottleneck")).toBeTruthy();
    expect(container.querySelector(".conn.is-leverage")).toBeTruthy();
    expect(container.querySelector(".fnl-takeaway")).toBeTruthy();
  });
});
