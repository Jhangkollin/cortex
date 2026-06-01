"""BrandRole enum — role a user holds within a brand."""

from enum import StrEnum


class BrandRole(StrEnum):
    """User role within a brand. Feeds BrandCapabilityPolicy.

    Separate enum (not shared with PublisherRole) so the type system enforces
    "brand routes accept brand roles" at compile time.
    """

    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
