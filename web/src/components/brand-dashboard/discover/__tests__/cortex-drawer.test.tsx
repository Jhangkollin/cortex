import { describe, test, expect } from "vitest";
import { render, screen, act, fireEvent } from "@testing-library/react";

import { DrawerProvider } from "../drawer-context";
import { AskCortexTrigger } from "../ask-cortex-trigger";
import { CortexDrawer } from "../cortex-drawer";

describe("cortex-drawer", () => {
  test("trigger opens the docked drawer; Esc closes", () => {
    render(
      <DrawerProvider>
        <AskCortexTrigger />
        <CortexDrawer />
      </DrawerProvider>,
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    act(() =>
      screen.getByRole("button", { name: /Ask Cortex/i }).click(),
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    act(() =>
      window.dispatchEvent(
        new KeyboardEvent("keydown", { key: "Escape" }),
      ),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  test("⌘K is suppressed while typing in an input, but Esc still closes", () => {
    render(
      <DrawerProvider>
        <input data-testid="probe-input" />
        <AskCortexTrigger />
        <CortexDrawer />
      </DrawerProvider>,
    );
    const input = screen.getByTestId("probe-input");
    input.focus();

    // ⌘K dispatched from an INPUT must NOT toggle the drawer open.
    act(() =>
      fireEvent.keyDown(input, { key: "k", metaKey: true }),
    );
    expect(screen.queryByRole("dialog")).toBeNull();

    // Open via the trigger, then confirm Esc still closes even though the
    // input is focused (Esc is exempt from the input suppression).
    act(() =>
      screen.getByRole("button", { name: /Ask Cortex/i }).click(),
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    act(() =>
      fireEvent.keyDown(input, { key: "Escape" }),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
