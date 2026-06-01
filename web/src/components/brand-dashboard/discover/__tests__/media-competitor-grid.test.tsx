import { describe, test, expect } from "vitest";
import { render, screen } from "@testing-library/react";

import { MediaCompetitorGrid } from "../media-competitor-grid";
import { BASE_DATA } from "@/lib/discover/mock";

void describe;

test("media rows + competitor h2h with you/lead", () => {
  const { container } = render(
    <MediaCompetitorGrid media={BASE_DATA.media} comp={BASE_DATA.comp} />,
  );
  expect(container.querySelectorAll(".media .row:not(.head)")).toHaveLength(5);
  expect(container.querySelector(".h2h.you")).toBeTruthy();
  expect(container.querySelector(".h2h.lead")).toBeTruthy();
  expect(screen.getByText("−15.8 pp")).toBeInTheDocument();
});
