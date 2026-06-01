"""BrandCapability enum — capabilities scoped to brand-side actions."""

from enum import StrEnum


class BrandCapability(StrEnum):
    """Brand-side capabilities.

    Separate enum from PublisherCapability — type system rejects mixing.
    Values are snake-cased strings so they round-trip cleanly through JWT
    claims (which are JSON).
    """

    VIEW_BRAND_DASHBOARD = "view_brand_dashboard"
    EDIT_BRAND_SETTINGS = "edit_brand_settings"
    MANAGE_BRAND_USERS = "manage_brand_users"
    INVITE_BRAND_USERS = "invite_brand_users"
    VIEW_BRAND_KNOWLEDGE = "view_brand_knowledge"
    MANAGE_BRAND_KNOWLEDGE = "manage_brand_knowledge"
    VIEW_BRAND_CONNECTORS = "view_brand_connectors"
    MANAGE_BRAND_CONNECTORS = "manage_brand_connectors"
