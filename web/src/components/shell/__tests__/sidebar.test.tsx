import { describe, test, expect, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { act } from "react";

import { Sidebar } from "@/components/shell/sidebar";

const pushMock = vi.fn();
const nextAuthSignOutMock = vi.fn();
const mockSignOut = vi.fn();

vi.mock("next/navigation", () => ({
  usePathname: () => "/brand/dashboard",
  useRouter: () => ({ push: pushMock }),
}));

vi.mock("next-auth/react", () => ({
  signOut: (...args: unknown[]) => nextAuthSignOutMock(...args),
}));

vi.mock("@/components/auth/mock-session-provider", () => ({
  useMockSession: () => ({ signOut: mockSignOut }),
}));

const baseProps = {
  activeContextKind: "brand" as const,
  role: "admin" as const,
  tier: "enterprise" as const,
  user: {
    displayName: "CMO / Wang",
    orgName: "Acme Bank Asia",
    initial: "王",
  },
};

describe("Sidebar §04", () => {
  test("renders the v2 §04 nav items", () => {
    render(<Sidebar {...baseProps} />);
    expect(screen.getByText("Discover")).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
    expect(screen.getByText("Media Network")).toBeInTheDocument();
    expect(screen.getByText("Knowledge Base")).toBeInTheDocument();
    expect(screen.getByText("Brand Voice")).toBeInTheDocument();
    expect(screen.getByText("Connectors")).toBeInTheDocument();
  });

  test("does not render removed §04 elements", () => {
    render(<Sidebar {...baseProps} />);
    expect(screen.queryByText("New decision")).not.toBeInTheDocument();
    expect(screen.queryByText("GEO Monitor")).not.toBeInTheDocument();
    expect(screen.queryByText("Brand Cortex")).not.toBeInTheDocument();
    expect(screen.queryByText("ENT")).not.toBeInTheDocument();
  });

  test("only one row is aria-current on /brand/dashboard", () => {
    render(<Sidebar {...baseProps} />);
    const active = screen
      .getAllByRole("link")
      .filter((el) => el.getAttribute("aria-current") === "page");
    expect(active).toHaveLength(1);
    expect(active[0]).toHaveTextContent("Discover");
  });
});

describe("Sidebar user-menu popover", () => {
  test("trigger is collapsed by default; clicking opens the menu", () => {
    pushMock.mockClear();
    mockSignOut.mockClear();
    nextAuthSignOutMock.mockClear();
    render(<Sidebar {...baseProps} />);
    const trigger = screen.getByRole("button", { name: /account menu/i });
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("menu")).toBeNull();
    fireEvent.click(trigger);
    expect(trigger).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("menu")).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /account settings/i })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /reset demo/i })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /sign out/i })).toBeInTheDocument();
  });

  test("avatar contains the user initial", () => {
    render(<Sidebar {...baseProps} />);
    const trigger = screen.getByRole("button", { name: /account menu/i });
    expect(trigger.textContent).toContain("王");
  });

  test("Reset demo routes to /demo/onboarding and closes the menu", () => {
    pushMock.mockClear();
    render(<Sidebar {...baseProps} />);
    fireEvent.click(screen.getByRole("button", { name: /account menu/i }));
    fireEvent.click(screen.getByRole("menuitem", { name: /reset demo/i }));
    expect(pushMock).toHaveBeenCalledWith("/demo/onboarding");
    expect(screen.queryByRole("menu")).toBeNull();
  });

  test("Sign out clears the mock session AND calls NextAuth signOut with /signin", () => {
    mockSignOut.mockClear();
    nextAuthSignOutMock.mockClear();
    render(<Sidebar {...baseProps} />);
    fireEvent.click(screen.getByRole("button", { name: /account menu/i }));
    fireEvent.click(screen.getByRole("menuitem", { name: /sign out/i }));
    expect(mockSignOut).toHaveBeenCalledOnce();
    expect(nextAuthSignOutMock).toHaveBeenCalledOnce();
    expect(nextAuthSignOutMock).toHaveBeenCalledWith({ callbackUrl: "/signin" });
  });

  test("Sign out menu item carries the .is-danger class (red emphasis)", () => {
    render(<Sidebar {...baseProps} />);
    fireEvent.click(screen.getByRole("button", { name: /account menu/i }));
    const signOut = screen.getByRole("menuitem", { name: /sign out/i });
    expect(signOut.className).toContain("is-danger");
  });

  test("Escape closes the menu", () => {
    render(<Sidebar {...baseProps} />);
    fireEvent.click(screen.getByRole("button", { name: /account menu/i }));
    expect(screen.getByRole("menu")).toBeInTheDocument();
    act(() => {
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    });
    expect(screen.queryByRole("menu")).toBeNull();
  });

  test("click outside closes the menu", () => {
    render(
      <div>
        <Sidebar {...baseProps} />
        <button>outside</button>
      </div>,
    );
    fireEvent.click(screen.getByRole("button", { name: /account menu/i }));
    expect(screen.getByRole("menu")).toBeInTheDocument();
    fireEvent.mouseDown(screen.getByText("outside"));
    expect(screen.queryByRole("menu")).toBeNull();
  });
});
