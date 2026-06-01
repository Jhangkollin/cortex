/**
 * EmptyDiscover — render smoke test.
 *
 * Verifies the freshly-onboarded empty state renders without crashing.
 * `EmptyDiscover` calls `useMockSession()` internally (for `enableDemoData`),
 * which throws outside its provider — so we mock the module the same way
 * `auth/__tests__/sign-out-button.test.tsx` does (vi.hoisted spy).
 */
import { render } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { EmptyDiscover } from "../empty-discover";

const { mockEnableDemoData } = vi.hoisted(() => ({
  mockEnableDemoData: vi.fn(),
}));

vi.mock("@/components/auth/mock-session-provider", () => ({
  useMockSession: () => ({ enableDemoData: mockEnableDemoData }),
}));

describe("EmptyDiscover", () => {
  test("renders without crashing", () => {
    const { container } = render(<EmptyDiscover />);
    expect(container).toBeTruthy();
  });
});
