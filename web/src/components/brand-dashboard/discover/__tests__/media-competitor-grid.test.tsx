import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { MediaCompetitorGrid } from "../media-competitor-grid";
import { BASE_DATA } from "@/lib/discover/mock";

void describe;

test("media rows + intent category bars", () => {
  const { container } = render(
    <MediaCompetitorGrid media={BASE_DATA.media} intent={BASE_DATA.intent} />,
  );
  expect(container.querySelectorAll(".media .row.media-simple")).toHaveLength(2);
  expect(container.querySelectorAll(".int-row")).toHaveLength(10);
  expect(screen.getByText("早安健康")).toBeInTheDocument();
  expect(container.querySelector(".int-top")).toBeTruthy();
});
