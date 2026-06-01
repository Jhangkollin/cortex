import { describe, it, expect } from "vitest";

import { TIERS, getTier, annualPrice } from "@/lib/pricing/tiers";

describe("pricing tiers — single source of truth", () => {
  it("exposes exactly three tiers in display order: Developer, Pro, Enterprise", () => {
    expect(TIERS).toHaveLength(3);
    expect(TIERS.map((t) => t.id)).toEqual(["dev", "pro", "ent"]);
    expect(TIERS.map((t) => t.name)).toEqual([
      "Developer",
      "Pro",
      "Enterprise",
    ]);
  });

  it("prices match the design spec ($20 / $50 / $200 per seat per month)", () => {
    expect(getTier("dev").price.monthly).toBe(20);
    expect(getTier("pro").price.monthly).toBe(50);
    expect(getTier("ent").price.monthly).toBe(200);
  });

  it("annual price is 20% off monthly (spec §V1 toggle)", () => {
    // Spec says "SAVE 20%" pill on annual toggle. annualPrice() is the
    // helper rendered in the tier card when billing === 'annual'.
    expect(annualPrice(20)).toBe(16);
    expect(annualPrice(50)).toBe(40);
    expect(annualPrice(200)).toBe(160);
  });

  it("only Pro is marked popular (drives the featured card emphasis)", () => {
    expect(getTier("dev").popular).toBe(false);
    expect(getTier("pro").popular).toBe(true);
    expect(getTier("ent").popular).toBe(false);
  });

  it("minimum seats: Developer 1, Pro 5, Enterprise custom (null)", () => {
    expect(getTier("dev").minSeats).toBe(1);
    expect(getTier("pro").minSeats).toBe(5);
    expect(getTier("ent").minSeats).toBeNull();
  });

  it("CTAs route correctly: dev/pro to Stripe, Enterprise to sales", () => {
    expect(getTier("dev").cta).toEqual({
      kind: "stripe",
      label: "Start with Developer",
    });
    expect(getTier("pro").cta).toEqual({
      kind: "stripe",
      label: "Start Pro trial — 14 days",
    });
    expect(getTier("ent").cta).toEqual({
      kind: "sales",
      label: "Talk to sales",
    });
  });

  it("each tier carries at least one feature line for the bullet list", () => {
    for (const tier of TIERS) {
      expect(tier.features.length).toBeGreaterThan(0);
      for (const feature of tier.features) {
        expect(typeof feature.label).toBe("string");
        expect(typeof feature.included).toBe("boolean");
      }
    }
  });

  it("Pro lists at least one negative feature (close-icon, muted) so the upgrade story to Enterprise is visible", () => {
    const proNegatives = getTier("pro").features.filter((f) => !f.included);
    expect(proNegatives.length).toBeGreaterThan(0);
  });

  it("getTier throws on an unknown id rather than returning undefined", () => {
    // Returning undefined would silently break the tier card grid.
    // Throw early so a typo at the call site is caught in dev.
    expect(() => getTier("bogus" as never)).toThrow(/unknown tier/i);
  });
});
