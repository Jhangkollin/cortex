import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { Rich } from "../rich-text";

test("renders plain strings and bold runs", () => {
  const { container } = render(
    <Rich value={[{ b: "8 missing" }, " on tracked questions"]} />,
  );
  expect(container.textContent).toBe("8 missing on tracked questions");
  expect(screen.getByText("8 missing").tagName).toBe("B");
});

test("renders an all-plain value with no <b>", () => {
  const { container } = render(<Rich value={["per article"]} />);
  expect(container.querySelector("b")).toBeNull();
  expect(container.textContent).toBe("per article");
});
