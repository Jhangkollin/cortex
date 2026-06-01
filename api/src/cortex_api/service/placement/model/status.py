"""Shared StrEnum for placement row lifecycle.

Both ``brand_placement_settings.status`` (per-brand eligibility) and
``brand_publisher_scope.status`` (per-(brand,publisher) opt-in) share the
same value set ``{active, inactive}`` and map to one Postgres ENUM type
``placementrowstatus``. The values describe the same concept — "is this
row currently in effect?" — applied to different scopes.

If a future story needs to diverge (e.g. ``archived`` on settings but not
scope), split into per-table enums in the same migration that adds the
new value, with a docstring explaining why.
"""

from __future__ import annotations

from enum import StrEnum


class PlacementRowStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
