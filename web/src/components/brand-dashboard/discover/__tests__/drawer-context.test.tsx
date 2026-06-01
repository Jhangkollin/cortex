import { describe, test, expect, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";

import { DrawerProvider, useCortexDrawer } from "../drawer-context";

void vi;

function Probe() {
  const d = useCortexDrawer();
  return (
    <>
      <span data-testid="open">{String(d.drawerOpen)}</span>
      <button onClick={d.openDrawer}>open</button>
      <button onClick={d.closeDrawer}>close</button>
    </>
  );
}

describe("drawer-context", () => {
  test("opens and closes", () => {
    render(
      <DrawerProvider>
        <Probe />
      </DrawerProvider>,
    );
    expect(screen.getByTestId("open").textContent).toBe("false");
    act(() => screen.getByText("open").click());
    expect(screen.getByTestId("open").textContent).toBe("true");
    act(() => screen.getByText("close").click());
    expect(screen.getByTestId("open").textContent).toBe("false");
  });

  test("Escape closes; Cmd/Ctrl+K toggles", () => {
    render(
      <DrawerProvider>
        <Probe />
      </DrawerProvider>,
    );
    act(() =>
      window.dispatchEvent(
        new KeyboardEvent("keydown", { key: "k", metaKey: true }),
      ),
    );
    expect(screen.getByTestId("open").textContent).toBe("true");
    act(() =>
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" })),
    );
    expect(screen.getByTestId("open").textContent).toBe("false");
  });
});
