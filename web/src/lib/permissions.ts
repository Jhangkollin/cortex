/**
 * (activeContextKind, role) → capability matrix.
 *
 * The single place where frontend authorization decisions are made. Every
 * sidebar item, every action button, every gated surface checks here.
 *
 * The backend re-validates everything; this is UX, not security.
 *
 * Tier (free | enterprise) sits alongside role. KB read is gated by tier,
 * not role, so an enterprise viewer sees the KB and a free admin doesn't.
 * `OrgTier` stays Org-prefixed because tier belongs to the org/account. The
 * active context kind is the subset of Okis' PersonaType that has an app
 * workspace today; Developer does not have a dashboard capability matrix yet.
 */

export type ActiveContextKind = "brand" | "publisher";
export type OrgTier = "free" | "enterprise";
export type UserRole = "viewer" | "editor" | "admin" | "mlytics_admin";

export type Capability =
  | "view_brand_dashboard"
  | "edit_brand_settings"
  | "view_publisher_dashboard"
  | "edit_publisher_settings"
  | "view_knowledge_base"
  | "manage_knowledge_base"
  | "view_connectors"
  | "manage_connectors"
  | "manage_users"
  | "manage_org"
  | "view_admin_placements"
  | "view_kb_enterprise";

/**
 * Capability matrix keyed by (activeContextKind, role).
 *
 * `mlytics_admin` is the internal Mlytics ops role; it ignores activeContextKind and
 * always gets every capability including admin surfaces. The matrix duplicates
 * its row across both active context kinds so callers can look up uniformly.
 */
export const CAPABILITIES: Record<ActiveContextKind, Record<UserRole, Capability[]>> = {
  brand: {
    viewer: ["view_brand_dashboard"],
    editor: [
      "view_brand_dashboard",
      "edit_brand_settings",
      "view_connectors",
    ],
    admin: [
      "view_brand_dashboard",
      "edit_brand_settings",
      "view_connectors",
      "manage_connectors",
      "manage_users",
      "manage_org",
    ],
    mlytics_admin: [
      "view_brand_dashboard",
      "edit_brand_settings",
      "view_publisher_dashboard",
      "edit_publisher_settings",
      "view_knowledge_base",
      "manage_knowledge_base",
      "view_connectors",
      "manage_connectors",
      "manage_users",
      "manage_org",
      "view_admin_placements",
      "view_kb_enterprise",
    ],
  },
  publisher: {
    viewer: ["view_publisher_dashboard"],
    editor: [
      "view_publisher_dashboard",
      "edit_publisher_settings",
      "view_connectors",
    ],
    admin: [
      "view_publisher_dashboard",
      "edit_publisher_settings",
      "view_connectors",
      "manage_connectors",
      "manage_users",
      "manage_org",
    ],
    mlytics_admin: [
      "view_brand_dashboard",
      "edit_brand_settings",
      "view_publisher_dashboard",
      "edit_publisher_settings",
      "view_knowledge_base",
      "manage_knowledge_base",
      "view_connectors",
      "manage_connectors",
      "manage_users",
      "manage_org",
      "view_admin_placements",
      "view_kb_enterprise",
    ],
  },
};

export interface ActiveContext {
  kind: ActiveContextKind;
  role: UserRole;
  tier: OrgTier;
}

/**
 * Capability check. KB capabilities are tier-gated on top of role —
 * an enterprise viewer sees the KB; a free admin does not.
 */
export function hasCapability(
  activeContextKind: ActiveContextKind,
  role: UserRole,
  cap: Capability,
  tier: OrgTier = "free",
): boolean {
  if (cap === "view_knowledge_base" || cap === "view_kb_enterprise") {
    return tier === "enterprise" || role === "mlytics_admin";
  }
  return CAPABILITIES[activeContextKind][role].includes(cap);
}

/** Convenience: is this user an internal Mlytics operator? */
export function isMlyticsAdmin(role: UserRole): boolean {
  return role === "mlytics_admin";
}
