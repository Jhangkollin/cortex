"""BrandPublisherScope — which publishers a brand opts into.

Composite PK on (brand_id, publisher_id, lang). A brand can opt into the
same publisher for multiple languages independently — the F2 eligible-brands
API (COR-57) filters by ``lang`` from the agent-ws request so each
language slice is scoped separately. ``publisher_id`` has no FK because
cortex does not own publisher onboarding at MVP — PHP retains that side.
When the publisher slice lands in cortex, an FK can be added in a
follow-up migration.

``status`` shares the ``placementrowstatus`` Postgres ENUM with
``brand_placement_settings.status`` — both express the same lifecycle
("is this row currently in effect?") applied to different scopes.

``lang`` was added in COR-57 (default ``zh-tw`` backfill on existing
rows) to honor the AD3 F2 contract. See
``aigc_coordinator/docs/2026-05-21-cor-57-eligible-brands-design.md``
§ 1.1.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

from cortex_api.service.placement.model.status import PlacementRowStatus


class BrandPublisherScope(SQLModel, table=True):
    __tablename__ = "brand_publisher_scope"

    brand_id: UUID = Field(foreign_key="brand.id", primary_key=True)
    publisher_id: UUID = Field(primary_key=True)
    lang: str = Field(primary_key=True, max_length=16, default="zh-tw")

    status: PlacementRowStatus = Field(
        default=PlacementRowStatus.ACTIVE,
        sa_column=Column(
            SAEnum(
                PlacementRowStatus,
                values_callable=lambda enum_cls: [m.value for m in enum_cls],
                name="placementrowstatus",
                create_type=False,
            ),
            nullable=False,
            server_default=PlacementRowStatus.ACTIVE.value,
        ),
    )

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )
