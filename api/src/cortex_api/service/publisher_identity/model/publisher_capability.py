"""PublisherCapability enum — capabilities scoped to publisher-side actions."""

from enum import StrEnum


class PublisherCapability(StrEnum):
    """Publisher-side capabilities.

    Separate enum from BrandCapability — type system rejects mixing.
    """

    VIEW_PUBLISHER_DASHBOARD = "view_publisher_dashboard"
    EDIT_PUBLISHER_SETTINGS = "edit_publisher_settings"
    MANAGE_PUBLISHER_USERS = "manage_publisher_users"
    INVITE_PUBLISHER_USERS = "invite_publisher_users"
    VIEW_PUBLISHER_KNOWLEDGE = "view_publisher_knowledge"
    MANAGE_PUBLISHER_KNOWLEDGE = "manage_publisher_knowledge"
    MANAGE_PUBLISHER_PLACEMENTS = "manage_publisher_placements"
