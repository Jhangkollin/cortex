"""PublisherRole enum — role a user holds within a publisher."""

from enum import StrEnum


class PublisherRole(StrEnum):
    """User role within a publisher. Feeds PublisherCapabilityPolicy.

    Separate enum (not shared with BrandRole) so the type system enforces
    "publisher routes accept publisher roles" at compile time.
    """

    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
