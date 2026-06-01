# User-flow v1+v2 Onboarding Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make signup→persona→chooser→(Quick v2 | Manual v1)→dashboard→signout and signin→dashboard→signout the enforced canonical flows, with a backend-authoritative `onboarded_at` and a server-component gate.

**Architecture:** cortex-api gains a nullable `brand.onboarded_at`, a branch-agnostic idempotent `POST .../onboarding/complete`, and a cheap `GET .../onboarding/status`. cortex-web replaces the client `RequireOnboarded` with a server-component gate on `/brand/*` that reads status server-side and `redirect()`s; persona routes to a new `/onboarding` chooser; v1 moves to `/onboarding/manual`; both branches stamp completion before landing on the dashboard.

**Tech Stack:** Python 3.12 / FastAPI / SQLModel / Alembic (asyncpg) / pytest with DI-container overrides; Next.js 16 App Router / NextAuth v5 / Vitest + jsdom.

**Spec:** `docs/superpowers/specs/2026-05-19-user-flow-v1v2-reconciliation-design.md`

**Refinements discovered during planning (authoritative over the spec where they differ):**
- Endpoints live in `app/api/brand_identity/router.py` (not `app/api/brand/router.py`). That router already owns the `brand` identity row via `BrandIdentityService` + `BrandIdentityContainer`; the spec's intent ("mutation via brand_identity service") is satisfied more cleanly here.
- **Open Item #1 resolved:** `BrandCapabilityPolicy._MATRIX` grants `VIEW_BRAND_DASHBOARD` to every role and `ADMIN = frozenset(BrandCapability)`. The persona-picker founder is ADMIN, so it holds the status-read capability pre-onboarding. Status endpoint gates on `VIEW_BRAND_DASHBOARD`; completion on `EDIT_BRAND_SETTINGS`.
- **Spec test-infra prerequisite dropped:** the Vitest+jsdom harness already exists (`web/vitest.config.ts`, `jsdom ^25`, `setupFiles`, `server-only` alias stub). No bootstrap task needed.

---

## File Structure

**cortex-api (Phase A — independently testable):**
- Modify `api/src/cortex_api/service/brand_identity/model/brand.py` — add `onboarded_at` column.
- Create `api/alembic/versions/e5f6a7b8c9d0_brand_onboarded_at.py` — additive migration (head is `d4e5f6a7b8c9`).
- Modify `api/src/cortex_api/service/brand_identity/service.py` — add `mark_onboarded()`.
- Modify `api/src/cortex_api/app/api/brand_identity/dto.py` — add `OnboardingStatusResponse`, `OnboardingCompleteResponse`.
- Modify `api/src/cortex_api/app/api/brand_identity/router.py` — add status + complete endpoints.
- Tests: `api/tests/unit/service/brand_identity/test_brand_identity_service.py` (extend), `api/tests/integration/test_brand_profile_api.py` (extend), `api/tests/integration/` migration round-trip.

**cortex-web (Phase B — depends on Phase A endpoints):**
- Modify `web/src/lib/cortex-api.ts` — add `getOnboardingStatus()`, `completeOnboarding()`.
- Create `web/src/components/shell/brand-shell.tsx` — the client shell extracted from today's layout.
- Rewrite `web/src/app/brand/layout.tsx` — server-component gate wrapping `BrandShell`.
- Create `web/src/app/(auth)/onboarding/manual/page.tsx` + `actions.ts` — v1 wizard moved verbatim, completion wired.
- Rewrite `web/src/app/(auth)/onboarding/page.tsx` — the chooser.
- Modify `web/src/app/(auth)/persona/page.tsx` — push `/onboarding`.
- Create `web/src/app/(auth)/onboarding/v2/complete-actions.ts` — v2 completion server action.
- Modify `web/src/app/(auth)/onboarding/v2/page.tsx` and `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx` — call completion before dashboard.
- Create `web/src/components/auth/sign-out-button.tsx`; modify `web/src/components/shell/sidebar.tsx` — wire signout.

---

## Phase A — cortex-api

All `cd api` first. Test pattern: override DI container providers (never `mock.patch`), per CLAUDE.md. Mirror the existing fixtures in `api/tests/unit/service/brand_identity/test_brand_identity_service.py` and `api/tests/integration/test_brand_profile_api.py`.

### Task A1: Add `onboarded_at` to the Brand model + migration

**Files:**
- Modify: `api/src/cortex_api/service/brand_identity/model/brand.py:29`
- Create: `api/alembic/versions/e5f6a7b8c9d0_brand_onboarded_at.py`
- Test: `api/tests/integration/test_brand_onboarded_at_migration.py`

- [ ] **Step 1: Add the column to the SQLModel**

In `brand.py`, add after the `archived_at` line (line 29):

```python
    onboarded_at: datetime | None = Field(
        default=None,
        description="Set once the brand finishes onboarding (manual or AI); NULL = not onboarded",
    )
```

- [ ] **Step 2: Create the migration**

Confirm current head: `cd api && uv run alembic heads` → expect `d4e5f6a7b8c9 (head)`.

Create `api/alembic/versions/e5f6a7b8c9d0_brand_onboarded_at.py`:

```python
"""brand.onboarded_at (nullable lifecycle stamp)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-19 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable, no server_default: NULL means "not onboarded". The
    # CLAUDE.md created_at/updated_at server_default rule does NOT apply to
    # this lifecycle stamp — a raw INSERT legitimately leaves it NULL.
    op.add_column("brand", sa.Column("onboarded_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("brand", "onboarded_at")
    # No ENUM created by this migration → no sa.Enum(...).drop() needed.
```

- [ ] **Step 3: Write the round-trip test**

Create `api/tests/integration/test_brand_onboarded_at_migration.py`:

```python
"""brand.onboarded_at migration round-trips (CLAUDE.md hard-won rule #3)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import command
from alembic.config import Config


def _cfg() -> Config:
    return Config("alembic.ini")


def test_upgrade_downgrade_upgrade_round_trips() -> None:
    cfg = _cfg()
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "d4e5f6a7b8c9")
    command.upgrade(cfg, "head")


def test_onboarded_at_column_present_and_nullable() -> None:
    cfg = _cfg()
    command.upgrade(cfg, "head")
    engine = sa.create_engine(cfg.get_main_option("sqlalchemy.url"))
    insp = sa.inspect(engine)
    cols = {c["name"]: c for c in insp.get_columns("brand")}
    assert "onboarded_at" in cols
    assert cols["onboarded_at"]["nullable"] is True
```

If `alembic.ini` uses an async URL the existing migration tests handle this — mirror whatever `api/tests/integration/test_brand_profile_repo.py` / existing migration tests do for engine setup if the sync `create_engine` above fails. Inspect that file first and copy its DB-URL fixture rather than inventing one.

- [ ] **Step 4: Run tests — verify pass**

Run: `cd api && uv run pytest tests/integration/test_brand_onboarded_at_migration.py -v`
Expected: PASS (both tests).

- [ ] **Step 5: Lint**

Run: `cd api && make lint`
Expected: ruff + mypy clean (mypy sees the new typed field).

- [ ] **Step 6: Commit**

```bash
git add api/src/cortex_api/service/brand_identity/model/brand.py api/alembic/versions/e5f6a7b8c9d0_brand_onboarded_at.py api/tests/integration/test_brand_onboarded_at_migration.py
git commit -m "feat(brand): add nullable brand.onboarded_at + round-trip-tested migration

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task A2: `BrandIdentityService.mark_onboarded()` (idempotent)

**Files:**
- Modify: `api/src/cortex_api/service/brand_identity/service.py` (add method after `update_brand`, ~line 140)
- Test: `api/tests/unit/service/brand_identity/test_brand_identity_service.py` (extend)

- [ ] **Step 1: Write the failing tests**

Append to `test_brand_identity_service.py` (mirror its existing fixture style for building a service + an ADMIN `BrandTenantCtx`; reuse the helpers already in that file — do not invent new fixtures):

```python
import datetime as _dt

import pytest

from cortex_api.core.exceptions import ForbiddenError
from cortex_api.service.brand_identity.model.brand_capability import BrandCapability


@pytest.mark.asyncio
async def test_mark_onboarded_stamps_when_null(brand_identity_service, admin_ctx):
    # admin_ctx is an ADMIN BrandTenantCtx for a brand created via the
    # existing create_brand_with_admin helper used elsewhere in this file.
    brand = await brand_identity_service.mark_onboarded(admin_ctx)
    assert brand.onboarded_at is not None


@pytest.mark.asyncio
async def test_mark_onboarded_is_idempotent(brand_identity_service, admin_ctx):
    first = await brand_identity_service.mark_onboarded(admin_ctx)
    stamp = first.onboarded_at
    second = await brand_identity_service.mark_onboarded(admin_ctx)
    assert second.onboarded_at == stamp  # not overwritten


@pytest.mark.asyncio
async def test_mark_onboarded_requires_edit_capability(
    brand_identity_service, viewer_ctx
):
    # viewer_ctx: a VIEWER BrandTenantCtx (no EDIT_BRAND_SETTINGS).
    with pytest.raises(ForbiddenError):
        await brand_identity_service.mark_onboarded(viewer_ctx)
```

If `admin_ctx` / `viewer_ctx` / `brand_identity_service` fixtures do not already exist in the file, add them following the exact construction the file's existing tests use for `create_brand_with_admin` + `enter_brand` (read the file top-to-bottom first; reuse, don't duplicate).

- [ ] **Step 2: Run — verify fail**

Run: `cd api && uv run pytest tests/unit/service/brand_identity/test_brand_identity_service.py -k mark_onboarded -v`
Expected: FAIL — `AttributeError: 'BrandIdentityService' object has no attribute 'mark_onboarded'`.

- [ ] **Step 3: Implement `mark_onboarded`**

In `service.py`, add after `update_brand` (before `enter_brand`):

```python
    async def mark_onboarded(self, actor: BrandTenantCtx):
        """Stamp `brand.onboarded_at` once. Idempotent: a second call is a
        no-op and returns the brand unchanged. Requires `EDIT_BRAND_SETTINGS`.
        """
        if BrandCapability.EDIT_BRAND_SETTINGS not in actor.capabilities:
            raise ForbiddenError("edit_brand_settings capability required")

        from datetime import datetime

        async with self._db.session() as session:
            brand = await self._brand_repo.get_by_id(session, actor.brand_id)
            if brand is None:
                raise NotFoundError(f"brand {actor.brand_id} not found")
            if brand.onboarded_at is None:
                brand = await self._brand_repo.update_fields(
                    session, brand, onboarded_at=datetime.utcnow()
                )
                self._logger.info("brand_onboarded", brand_id=str(actor.brand_id))
            return brand
```

(Keep the `from datetime import datetime` at module top if the file already imports it — check the imports block; `service.py` currently does NOT import datetime, so add `from datetime import datetime` to the top import group instead of the inline import shown above.)

- [ ] **Step 4: Run — verify pass**

Run: `cd api && uv run pytest tests/unit/service/brand_identity/test_brand_identity_service.py -k mark_onboarded -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Lint & full unit suite for the module**

Run: `cd api && uv run pytest tests/unit/service/brand_identity -v && make lint`
Expected: PASS, lint clean.

- [ ] **Step 6: Commit**

```bash
git add api/src/cortex_api/service/brand_identity/service.py api/tests/unit/service/brand_identity/test_brand_identity_service.py
git commit -m "feat(brand): idempotent BrandIdentityService.mark_onboarded

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task A3: DTOs + status & complete endpoints

**Files:**
- Modify: `api/src/cortex_api/app/api/brand_identity/dto.py`
- Modify: `api/src/cortex_api/app/api/brand_identity/router.py`
- Test: `api/tests/integration/test_brand_profile_api.py` (extend) — mirror its existing app/client fixture.

- [ ] **Step 1: Add DTOs**

In `dto.py` add (keep imports consistent with the file; it already uses pydantic `BaseModel`):

```python
class OnboardingStatusResponse(BaseModel):
    onboarded: bool


class OnboardingCompleteResponse(BaseModel):
    onboarded_at: datetime
```

Ensure `from datetime import datetime` is imported in `dto.py` (add to the import block if absent).

- [ ] **Step 2: Write the failing endpoint tests**

Append to `test_brand_profile_api.py`, mirroring how that file builds the FastAPI app + auth-overridden client (reuse its existing `client` / brand-context fixtures — read the file first):

```python
def test_onboarding_status_false_then_true(brand_admin_client, brand_id):
    r = brand_admin_client.get(f"/v1/brand/{brand_id}/onboarding/status")
    assert r.status_code == 200
    assert r.json() == {"onboarded": False}

    c = brand_admin_client.post(f"/v1/brand/{brand_id}/onboarding/complete")
    assert c.status_code == 200
    assert "onboarded_at" in c.json()

    r2 = brand_admin_client.get(f"/v1/brand/{brand_id}/onboarding/status")
    assert r2.json() == {"onboarded": True}


def test_onboarding_complete_is_idempotent(brand_admin_client, brand_id):
    first = brand_admin_client.post(f"/v1/brand/{brand_id}/onboarding/complete")
    second = brand_admin_client.post(f"/v1/brand/{brand_id}/onboarding/complete")
    assert first.json()["onboarded_at"] == second.json()["onboarded_at"]


def test_onboarding_complete_forbidden_without_edit_cap(brand_viewer_client, brand_id):
    r = brand_viewer_client.post(f"/v1/brand/{brand_id}/onboarding/complete")
    assert r.status_code == 403
```

If `brand_admin_client` / `brand_viewer_client` / `brand_id` fixtures don't exist, construct them exactly as the file's existing brand-profile tests build an authorized TestClient (same `active_brand` override pattern), changing only the capability set for the viewer variant.

- [ ] **Step 3: Run — verify fail**

Run: `cd api && uv run pytest tests/integration/test_brand_profile_api.py -k onboarding -v`
Expected: FAIL — 404 (routes not registered).

- [ ] **Step 4: Add the endpoints**

In `router.py`, add imports:

```python
from cortex_api.app.api.brand_identity.dto import (
    OnboardingCompleteResponse,
    OnboardingStatusResponse,
)
```

(extend the existing `from cortex_api.app.api.brand_identity.dto import (...)` group rather than adding a second import statement.)

Add after `update_brand` (before `list_brand_users`):

```python
@router.get(
    "/v1/brand/{brand_id}/onboarding/status",
    response_model=OnboardingStatusResponse,
    summary="Whether this brand has finished onboarding",
    dependencies=[Depends(requires_brand_capability(BrandCapability.VIEW_BRAND_DASHBOARD))],
)
@inject
async def get_onboarding_status(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> OnboardingStatusResponse:
    brand = await brand_identity_service.get_brand(tenant.brand_id)
    return OnboardingStatusResponse(onboarded=brand.onboarded_at is not None)


@router.post(
    "/v1/brand/{brand_id}/onboarding/complete",
    response_model=OnboardingCompleteResponse,
    summary="Mark this brand's onboarding complete (idempotent)",
    dependencies=[Depends(requires_brand_capability(BrandCapability.EDIT_BRAND_SETTINGS))],
)
@inject
async def complete_onboarding(
    brand_id: UUID,
    tenant: BrandTenantCtx = Depends(active_brand),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> OnboardingCompleteResponse:
    brand = await brand_identity_service.mark_onboarded(tenant)
    assert brand.onboarded_at is not None  # set by mark_onboarded
    return OnboardingCompleteResponse(onboarded_at=brand.onboarded_at)
```

- [ ] **Step 5: Run — verify pass**

Run: `cd api && uv run pytest tests/integration/test_brand_profile_api.py -k onboarding -v`
Expected: PASS (3 tests). Also run the app-boots smoke: `uv run pytest tests/unit/test_app_boots.py -v` → PASS.

- [ ] **Step 6: Lint + full api suite**

Run: `cd api && make lint && make test`
Expected: clean + green.

- [ ] **Step 7: Commit**

```bash
git add api/src/cortex_api/app/api/brand_identity/dto.py api/src/cortex_api/app/api/brand_identity/router.py api/tests/integration/test_brand_profile_api.py
git commit -m "feat(brand): onboarding status + idempotent complete endpoints

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Phase B — cortex-web

All `cd web` first. Tests use Vitest + jsdom (`npm test`). Mirror existing tests in `web/src/components/auth/__tests__/require-onboarded.test.tsx` for provider/router mocking patterns.

### Task B1: cortex-api client functions

**Files:**
- Modify: `web/src/lib/cortex-api.ts` (append after `pollAnalyze`)
- Test: `web/src/lib/onboarding/onboarding-api-client.test.ts` (create) — mirror an existing `cortex-api`-touching test for the `fetch` mock + `server-only` stub already configured in `vitest.config.ts`.

- [ ] **Step 1: Write failing tests**

Create `web/src/lib/onboarding/onboarding-api-client.test.ts`:

```ts
import { afterEach, describe, expect, it, vi } from "vitest";

import { completeOnboarding, getOnboardingStatus } from "@/lib/cortex-api";

const claims = {
  cortexUserId: "u1",
  email: "a@mlytics.com",
  displayName: "A",
  activeContext: { kind: "brand" as const, id: "b1", role: "admin", capabilities: [] },
};

afterEach(() => vi.restoreAllMocks());

describe("getOnboardingStatus", () => {
  it("GETs the status endpoint and returns the body", async () => {
    process.env.CORTEX_API_URL = "http://api";
    process.env.NEXTAUTH_SECRET = "x".repeat(32);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ onboarded: true }), { status: 200 }),
    );
    await expect(getOnboardingStatus(claims, "b1")).resolves.toEqual({
      onboarded: true,
    });
  });
});

describe("completeOnboarding", () => {
  it("POSTs the complete endpoint", async () => {
    process.env.CORTEX_API_URL = "http://api";
    process.env.NEXTAUTH_SECRET = "x".repeat(32);
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify({ onboarded_at: "2026-05-19T00:00:00Z" }), {
          status: 200,
        }),
      );
    await completeOnboarding(claims, "b1");
    expect(spy).toHaveBeenCalledWith(
      "http://api/v1/brand/b1/onboarding/complete",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
```

- [ ] **Step 2: Run — verify fail**

Run: `cd web && npx vitest run src/lib/onboarding/onboarding-api-client.test.ts`
Expected: FAIL — `getOnboardingStatus`/`completeOnboarding` not exported.

- [ ] **Step 3: Implement the client functions**

Append to `web/src/lib/cortex-api.ts`:

```ts
export interface OnboardingStatusResponse {
  onboarded: boolean;
}

export interface OnboardingCompleteResponse {
  onboarded_at: string;
}

/** `GET /v1/brand/{brand_id}/onboarding/status` — read by the server gate. */
export async function getOnboardingStatus(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<OnboardingStatusResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    `${apiBase()}/v1/brand/${brandId}/onboarding/status`,
    { headers: { Authorization: `Bearer ${token}` }, cache: "no-store" },
  );
  if (!res.ok) {
    throw new OnboardingStatusError(res.status);
  }
  return (await res.json()) as OnboardingStatusResponse;
}

/** Non-2xx from the status endpoint, carrying the HTTP status so the gate
 *  can branch (401/403 → /error, 404 → /onboarding, else → retry screen). */
export class OnboardingStatusError extends Error {
  constructor(public readonly status: number) {
    super(`cortex-api onboarding/status failed: ${status}`);
    this.name = "OnboardingStatusError";
  }
}

/** `POST /v1/brand/{brand_id}/onboarding/complete` — idempotent stamp. */
export async function completeOnboarding(
  claims: CortexTokenClaims,
  brandId: string,
): Promise<OnboardingCompleteResponse> {
  const token = await signCortexApiToken(claims);
  const res = await fetch(
    `${apiBase()}/v1/brand/${brandId}/onboarding/complete`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      cache: "no-store",
    },
  );
  if (!res.ok) {
    throw new Error(
      `cortex-api POST onboarding/complete failed: ${res.status} ${await res.text()}`,
    );
  }
  return (await res.json()) as OnboardingCompleteResponse;
}
```

- [ ] **Step 4: Run — verify pass**

Run: `cd web && npx vitest run src/lib/onboarding/onboarding-api-client.test.ts`
Expected: PASS.

- [ ] **Step 5: Typecheck + commit**

Run: `cd web && npm run type-check`
```bash
git add web/src/lib/cortex-api.ts web/src/lib/onboarding/onboarding-api-client.test.ts
git commit -m "feat(web): cortex-api onboarding status/complete client fns

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task B2: Extract the brand client shell

Pure refactor: move today's `app/brand/layout.tsx` body into a client component so the layout file can become a server gate in B3. No behavior change yet.

**Files:**
- Create: `web/src/components/shell/brand-shell.tsx`
- Modify: `web/src/app/brand/layout.tsx`

- [ ] **Step 1: Create `brand-shell.tsx`** — copy the current `app/brand/layout.tsx` verbatim into `web/src/components/shell/brand-shell.tsx`, rename the export `BrandLayout` → `BrandShell`, and **delete** the `<RequireOnboarded>` wrapper and its import (the server gate replaces it). Keep `"use client"`, the `useMockSession()` sidebar/user wiring, and the `geo-app` markup exactly.

- [ ] **Step 2: Make the layout delegate**

Replace `web/src/app/brand/layout.tsx` with:

```tsx
import { BrandShell } from "@/components/shell/brand-shell";

export default function BrandLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <BrandShell>{children}</BrandShell>;
}
```

- [ ] **Step 3: Verify no regression**

Run: `cd web && npm run type-check && npx vitest run`
Expected: PASS (existing suites green; behavior unchanged).

- [ ] **Step 4: Commit**

```bash
git add web/src/components/shell/brand-shell.tsx web/src/app/brand/layout.tsx
git commit -m "refactor(web): extract BrandShell from brand layout (no behavior change)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task B3: Server-component gate

**Files:**
- Create: `web/src/components/auth/onboarding-gate.tsx` (server component)
- Modify: `web/src/app/brand/layout.tsx`
- Test: `web/src/components/auth/__tests__/onboarding-gate.test.tsx`

- [ ] **Step 1: Write failing tests** (mock `@/lib/auth`'s `auth()`, `@/lib/cortex-api`, and `next/navigation`'s `redirect`):

```tsx
import { describe, expect, it, vi, beforeEach } from "vitest";

const redirect = vi.fn((url: string) => { throw new Error(`REDIRECT:${url}`); });
vi.mock("next/navigation", () => ({ redirect }));
const authMock = vi.fn();
vi.mock("@/lib/auth", () => ({ auth: authMock }));
const getOnboardingStatus = vi.fn();
vi.mock("@/lib/cortex-api", () => ({
  getOnboardingStatus,
  OnboardingStatusError: class extends Error {
    constructor(public status: number) { super(); }
  },
}));

import { resolveGateDestination } from "@/components/auth/onboarding-gate";

beforeEach(() => { redirect.mockClear(); authMock.mockReset(); getOnboardingStatus.mockReset(); delete process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH; });

describe("resolveGateDestination", () => {
  it("renders through when dev bypass on (no auth call)", async () => {
    process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH = "true";
    expect(await resolveGateDestination()).toBe("render");
    expect(authMock).not.toHaveBeenCalled();
  });
  it("→ /signin when no session", async () => {
    authMock.mockResolvedValue(null);
    expect(await resolveGateDestination()).toBe("/signin");
  });
  it("→ /persona when session but no brand context", async () => {
    authMock.mockResolvedValue({ user: { email: "a@mlytics.com", cortexUserId: "u" } });
    expect(await resolveGateDestination()).toBe("/persona");
  });
  it("→ /onboarding when brand ctx but not onboarded", async () => {
    authMock.mockResolvedValue({ user: { email: "a@mlytics.com", cortexUserId: "u", activeContext: { kind: "brand", id: "b", role: "admin", capabilities: [] } } });
    getOnboardingStatus.mockResolvedValue({ onboarded: false });
    expect(await resolveGateDestination()).toBe("/onboarding");
  });
  it("renders when onboarded", async () => {
    authMock.mockResolvedValue({ user: { email: "a@mlytics.com", cortexUserId: "u", activeContext: { kind: "brand", id: "b", role: "admin", capabilities: [] } } });
    getOnboardingStatus.mockResolvedValue({ onboarded: true });
    expect(await resolveGateDestination()).toBe("render");
  });
  it("→ /error on 403 status fetch", async () => {
    authMock.mockResolvedValue({ user: { email: "a@mlytics.com", cortexUserId: "u", activeContext: { kind: "brand", id: "b", role: "admin", capabilities: [] } } });
    const { OnboardingStatusError } = await import("@/lib/cortex-api");
    getOnboardingStatus.mockRejectedValue(new OnboardingStatusError(403));
    expect(await resolveGateDestination()).toBe("/error");
  });
  it("→ /onboarding on 404 status fetch", async () => {
    authMock.mockResolvedValue({ user: { email: "a@mlytics.com", cortexUserId: "u", activeContext: { kind: "brand", id: "b", role: "admin", capabilities: [] } } });
    const { OnboardingStatusError } = await import("@/lib/cortex-api");
    getOnboardingStatus.mockRejectedValue(new OnboardingStatusError(404));
    expect(await resolveGateDestination()).toBe("/onboarding");
  });
  it("→ error sentinel on 5xx status fetch", async () => {
    authMock.mockResolvedValue({ user: { email: "a@mlytics.com", cortexUserId: "u", activeContext: { kind: "brand", id: "b", role: "admin", capabilities: [] } } });
    const { OnboardingStatusError } = await import("@/lib/cortex-api");
    getOnboardingStatus.mockRejectedValue(new OnboardingStatusError(503));
    expect(await resolveGateDestination()).toBe("retry");
  });
});
```

- [ ] **Step 2: Run — verify fail**

Run: `cd web && npx vitest run src/components/auth/__tests__/onboarding-gate.test.tsx`
Expected: FAIL — module/function missing.

- [ ] **Step 3: Implement the gate**

Create `web/src/components/auth/onboarding-gate.tsx`:

```tsx
import "server-only";

import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { getOnboardingStatus, OnboardingStatusError } from "@/lib/cortex-api";

const DEV_BYPASS_AUTH = process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === "true";

export type GateDestination = "render" | "retry" | string;

/** Pure decision function (unit-testable). Returns "render", "retry", or a
 *  path string to redirect to. Never throws for control flow. */
export async function resolveGateDestination(): Promise<GateDestination> {
  if (DEV_BYPASS_AUTH) return "render";

  const session = await auth();
  if (!session?.user?.email) return "/signin";

  const ctx = session.user.activeContext;
  if (!ctx || ctx.kind !== "brand" || !ctx.id) return "/persona";

  try {
    const status = await getOnboardingStatus(
      {
        cortexUserId: session.user.cortexUserId ?? "",
        email: session.user.email,
        displayName: session.user.name ?? null,
        activeContext: ctx,
      },
      ctx.id,
    );
    return status.onboarded ? "render" : "/onboarding";
  } catch (e) {
    if (e instanceof OnboardingStatusError) {
      if (e.status === 401 || e.status === 403) return "/error";
      if (e.status === 404) return "/onboarding";
    }
    return "retry";
  }
}

export async function OnboardingGate({
  children,
}: {
  children: React.ReactNode;
}) {
  const dest = await resolveGateDestination();
  if (dest === "render") return <>{children}</>;
  if (dest === "retry") {
    return (
      <div
        role="alert"
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "var(--mly-ink-025, #f7f7f8)",
          textAlign: "center",
          padding: "40px 20px",
        }}
      >
        <div>
          <p style={{ fontWeight: 700, marginBottom: 6 }}>
            Couldn&apos;t check your workspace
          </p>
          <p style={{ fontSize: 13, color: "#6b7280", marginBottom: 16 }}>
            Nothing was lost — reload to try again.
          </p>
          <a href="/brand/dashboard" style={{ fontSize: 13, fontWeight: 600 }}>
            Retry
          </a>
        </div>
      </div>
    );
  }
  redirect(dest);
}
```

- [ ] **Step 4: Wire it into the layout**

Modify `web/src/app/brand/layout.tsx`:

```tsx
import { OnboardingGate } from "@/components/auth/onboarding-gate";
import { BrandShell } from "@/components/shell/brand-shell";

export default function BrandLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <OnboardingGate>
      <BrandShell>{children}</BrandShell>
    </OnboardingGate>
  );
}
```

- [ ] **Step 5: Run — verify pass**

Run: `cd web && npx vitest run src/components/auth/__tests__/onboarding-gate.test.tsx && npm run type-check`
Expected: PASS, types clean.

- [ ] **Step 6: Commit**

```bash
git add web/src/components/auth/onboarding-gate.tsx web/src/app/brand/layout.tsx web/src/components/auth/__tests__/onboarding-gate.test.tsx
git commit -m "feat(web): server-component onboarding gate on /brand/* (bypass-aware)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task B4: Move v1 wizard to `/onboarding/manual` + wire completion

**Files:**
- Create: `web/src/app/(auth)/onboarding/manual/page.tsx` (moved from `onboarding/page.tsx`)
- Create: `web/src/app/(auth)/onboarding/manual/actions.ts` (moved from `onboarding/actions.ts`, completion added)
- Delete: `web/src/app/(auth)/onboarding/actions.ts`
- Test: `web/src/app/(auth)/onboarding/manual/actions.test.ts`

- [ ] **Step 1: Move the wizard page** — `git mv web/src/app/\(auth\)/onboarding/page.tsx web/src/app/\(auth\)/onboarding/manual/page.tsx`. In the moved file, change the import `@/app/(auth)/onboarding/actions` → `@/app/(auth)/onboarding/manual/actions`, and change every `router.push("/onboarding?step=...")` / `goTo` URL base from `/onboarding` to `/onboarding/manual` (the `?step=N` contract is preserved, only the path segment changes). Final-step success still `router.push("/brand/dashboard")`.

- [ ] **Step 2: Move + extend the action** — `git mv web/src/app/\(auth\)/onboarding/actions.ts web/src/app/\(auth\)/onboarding/manual/actions.ts`. Add the completion call after the existing `updateBrand(...)` succeeds and before `return`:

```ts
import { completeOnboarding } from "@/lib/cortex-api";
// ... existing code through `const brand = await updateBrand(...)` ...

  await completeOnboarding(
    {
      cortexUserId: session.user.cortexUserId,
      email: session.user.email,
      displayName: session.user.name ?? null,
      activeContext,
    },
    activeContext.id,
  );

  return {
    brandId: brand.id,
    brandDisplayName: brand.display_name,
  };
```

- [ ] **Step 3: Write the failing test**

Create `web/src/app/(auth)/onboarding/manual/actions.test.ts` mocking `@/lib/auth` `auth()` and `@/lib/cortex-api` (`updateBrand`, `completeOnboarding`):

```ts
import { describe, expect, it, vi, beforeEach } from "vitest";

const auth = vi.fn();
vi.mock("@/lib/auth", () => ({ auth }));
const updateBrand = vi.fn();
const completeOnboarding = vi.fn();
vi.mock("@/lib/cortex-api", () => ({ updateBrand, completeOnboarding }));

import { completeBrandOnboarding } from "@/app/(auth)/onboarding/manual/actions";

beforeEach(() => { auth.mockReset(); updateBrand.mockReset(); completeOnboarding.mockReset(); });

it("stamps onboarding complete after updating the brand", async () => {
  auth.mockResolvedValue({
    user: { email: "a@mlytics.com", cortexUserId: "u", name: "A",
      activeContext: { kind: "brand", id: "b1", role: "admin", capabilities: [] } },
  });
  updateBrand.mockResolvedValue({ id: "b1", display_name: "Acme" });
  completeOnboarding.mockResolvedValue({ onboarded_at: "2026-05-19T00:00:00Z" });

  const r = await completeBrandOnboarding({ companyName: "Acme" } as never);

  expect(updateBrand).toHaveBeenCalled();
  expect(completeOnboarding).toHaveBeenCalledWith(
    expect.objectContaining({ activeContext: expect.objectContaining({ id: "b1" }) }),
    "b1",
  );
  expect(r).toEqual({ brandId: "b1", brandDisplayName: "Acme" });
});
```

- [ ] **Step 4: Run — verify fail then pass**

Run: `cd web && npx vitest run "src/app/(auth)/onboarding/manual/actions.test.ts"`
Expected: FAIL before Step 2 changes are saved; PASS after. (If executing strictly TDD, write the test first, watch it fail on the missing module, then move/extend.)

- [ ] **Step 5: Grep for stale references**

Run: `cd web && grep -rn '"/onboarding?step=\|(auth)/onboarding/actions\|onboarding\\?step=1' src | grep -v /manual/`
Expected: only `persona/page.tsx` (handled in B5) — no other stale `/onboarding?step` or old action import remains.

- [ ] **Step 6: Typecheck + commit**

Run: `cd web && npm run type-check && npx vitest run`
```bash
git add -A web/src/app/\(auth\)/onboarding
git commit -m "feat(web): move v1 wizard to /onboarding/manual + stamp completion

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task B5: New `/onboarding` chooser + persona redirect

**Files:**
- Create: `web/src/app/(auth)/onboarding/page.tsx` (the chooser)
- Modify: `web/src/app/(auth)/persona/page.tsx:91`
- Test: `web/src/app/(auth)/onboarding/__tests__/chooser.test.tsx`

- [ ] **Step 1: Write failing test**

Create `web/src/app/(auth)/onboarding/__tests__/chooser.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import OnboardingChooser from "@/app/(auth)/onboarding/page";

describe("OnboardingChooser", () => {
  it("offers both branches with correct hrefs", () => {
    render(<OnboardingChooser />);
    expect(screen.getByRole("link", { name: /quick/i })).toHaveAttribute(
      "href",
      "/onboarding/v2",
    );
    expect(screen.getByRole("link", { name: /manual/i })).toHaveAttribute(
      "href",
      "/onboarding/manual?step=1",
    );
  });
});
```

- [ ] **Step 2: Run — verify fail**

Run: `cd web && npx vitest run "src/app/(auth)/onboarding/__tests__/chooser.test.tsx"`
Expected: FAIL — module has no default export yet.

- [ ] **Step 3: Implement the chooser** (server component, two links; reuse existing token/typography classes seen in `persona/page.tsx` for visual consistency):

```tsx
import Link from "next/link";

export default function OnboardingChooser() {
  return (
    <div className="min-h-screen bg-ink-25 p-8">
      <div className="mb-8 text-[11px] font-bold uppercase tracking-[0.12em] text-brand-700">
        SET UP YOUR BRAND
      </div>
      <h1
        className="mb-2.5"
        style={{ font: "700 40px/1.1 var(--font-sans)", letterSpacing: "-0.02em" }}
      >
        How do you want to set up?
      </h1>
      <p className="mb-9 max-w-[560px] text-base text-ink-500">
        Let Cortex extract your brand from your website, or fill the details in
        yourself. You can edit everything later in Brand settings.
      </p>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Link
          href="/onboarding/v2"
          className="flex min-h-[220px] flex-col gap-3 rounded-md border border-brand-700 bg-brand-700 p-6 text-white shadow-elev-2 transition-transform hover:translate-y-[-1px]"
        >
          <h3 className="m-0 text-xl font-bold">Quick · AI setup</h3>
          <p className="m-0 text-sm text-brand-100">
            Enter your website. Cortex crawls it and pre-fills your brand
            profile in ~30 seconds.
          </p>
        </Link>
        <Link
          href="/onboarding/manual?step=1"
          className="flex min-h-[220px] flex-col gap-3 rounded-md border border-ink-200 bg-white p-6 transition-transform hover:translate-y-[-1px]"
        >
          <h3 className="m-0 text-xl font-bold text-ink-900">Manual · fill a form</h3>
          <p className="m-0 text-sm text-ink-500">
            Prefer to type it yourself? Walk through a short 5-step form.
          </p>
        </Link>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Update persona redirect** — in `web/src/app/(auth)/persona/page.tsx`, change `router.push("/onboarding?step=1")` to `router.push("/onboarding")`. Update the adjacent code comment that says "hands off to the visual 5-step wizard at `/onboarding?step=1`" to describe the chooser.

- [ ] **Step 5: Run — verify pass**

Run: `cd web && npx vitest run "src/app/(auth)/onboarding/__tests__/chooser.test.tsx" && npm run type-check`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add web/src/app/\(auth\)/onboarding/page.tsx "web/src/app/(auth)/onboarding/__tests__/chooser.test.tsx" web/src/app/\(auth\)/persona/page.tsx
git commit -m "feat(web): /onboarding chooser; persona routes to it

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task B6: Wire v2 completion (EN + zh-TW) and signout

**Files:**
- Create: `web/src/app/(auth)/onboarding/v2/complete-actions.ts`
- Modify: `web/src/app/(auth)/onboarding/v2/page.tsx` (`handleEnterDiscover` / `launchDone`)
- Modify: `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx` (same wiring)
- Create: `web/src/components/auth/sign-out-button.tsx`
- Modify: `web/src/components/shell/sidebar.tsx`
- Test: `web/src/app/(auth)/onboarding/v2/complete-actions.test.ts`, `web/src/components/auth/__tests__/sign-out-button.test.tsx`

- [ ] **Step 1: Failing test for the v2 completion action**

Create `web/src/app/(auth)/onboarding/v2/complete-actions.test.ts`:

```ts
import { describe, expect, it, vi, beforeEach } from "vitest";

const auth = vi.fn();
vi.mock("@/lib/auth", () => ({ auth }));
const completeOnboarding = vi.fn();
vi.mock("@/lib/cortex-api", () => ({ completeOnboarding }));

import { completeV2Onboarding } from "@/app/(auth)/onboarding/v2/complete-actions";

beforeEach(() => { auth.mockReset(); completeOnboarding.mockReset(); });

it("calls completeOnboarding for the active brand", async () => {
  auth.mockResolvedValue({
    user: { email: "a@mlytics.com", cortexUserId: "u", name: "A",
      activeContext: { kind: "brand", id: "b9", role: "admin", capabilities: [] } },
  });
  completeOnboarding.mockResolvedValue({ onboarded_at: "2026-05-19T00:00:00Z" });
  await completeV2Onboarding();
  expect(completeOnboarding).toHaveBeenCalledWith(
    expect.objectContaining({ activeContext: expect.objectContaining({ id: "b9" }) }),
    "b9",
  );
});

it("throws a friendly error with no brand context", async () => {
  auth.mockResolvedValue({ user: { email: "a@mlytics.com", cortexUserId: "u" } });
  await expect(completeV2Onboarding()).rejects.toThrow(/brand context/i);
});
```

- [ ] **Step 2: Implement the v2 completion action** (mirror `onboarding/manual/actions.ts` guard structure exactly):

```ts
"use server";

import { auth } from "@/lib/auth";
import { completeOnboarding } from "@/lib/cortex-api";

export async function completeV2Onboarding(): Promise<void> {
  const session = await auth();
  if (!session?.user?.email) throw new Error("Not signed in.");
  if (!session.user.cortexUserId) {
    throw new Error("Sign-in did not complete. Please sign out and sign in again.");
  }
  const activeContext = session.user.activeContext;
  if (!activeContext || activeContext.kind !== "brand" || !activeContext.id) {
    throw new Error(
      "No active brand context. Pick a workspace from the persona picker first.",
    );
  }
  await completeOnboarding(
    {
      cortexUserId: session.user.cortexUserId,
      email: session.user.email,
      displayName: session.user.name ?? null,
      activeContext,
    },
    activeContext.id,
  );
}
```

- [ ] **Step 3: Call it before the dashboard hop in v2**

In `web/src/app/(auth)/onboarding/v2/page.tsx`, change `handleEnterDiscover` to await completion, surface failure (do NOT navigate on error), and only then route:

```tsx
import { completeV2Onboarding } from "@/app/(auth)/onboarding/v2/complete-actions";
// ...
const [completeError, setCompleteError] = useState<string | null>(null);
const handleEnterDiscover = useCallback(async () => {
  try {
    await completeV2Onboarding();
  } catch (e) {
    setCompleteError(
      e instanceof Error ? e.message : "Couldn't finish onboarding. Try again.",
    );
    return; // stay on the success screen; gate would bounce us otherwise
  }
  router.push("/brand/dashboard");
}, [router]);
```

Render `completeError` near the `StepComplete` CTA (small `role="alert"` red text, matching the v2 error styling already in the file). Update the `onEnterDiscover={handleEnterDiscover}` call site to `onEnterDiscover={() => void handleEnterDiscover()}`.

- [ ] **Step 4: Mirror into zh-TW** — apply the identical change set to `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx` (same import, same `handleEnterDiscover`, localized error string e.g. `"無法完成設定，請再試一次。"`).

- [ ] **Step 5: Signout button — failing test**

Create `web/src/components/auth/__tests__/sign-out-button.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const nextSignOut = vi.fn();
vi.mock("next-auth/react", () => ({ signOut: nextSignOut }));
const mockSignOut = vi.fn();
vi.mock("@/components/auth/mock-session-provider", () => ({
  useMockSession: () => ({ signOut: mockSignOut }),
}));

import { SignOutButton } from "@/components/auth/sign-out-button";

beforeEach(() => { nextSignOut.mockReset(); mockSignOut.mockReset(); });

it("clears mock session AND calls NextAuth signOut to /signin", () => {
  render(<SignOutButton />);
  fireEvent.click(screen.getByRole("button", { name: /sign out/i }));
  expect(mockSignOut).toHaveBeenCalled();
  expect(nextSignOut).toHaveBeenCalledWith({ redirectTo: "/signin" });
});
```

- [ ] **Step 6: Implement `SignOutButton`**

Create `web/src/components/auth/sign-out-button.tsx`:

```tsx
"use client";

import { signOut as nextAuthSignOut } from "next-auth/react";

import { useMockSession } from "@/components/auth/mock-session-provider";

export function SignOutButton() {
  const { signOut: clearMockSession } = useMockSession();
  return (
    <button
      type="button"
      onClick={() => {
        clearMockSession(); // wipe localStorage so the provider can't re-project
        void nextAuthSignOut({ redirectTo: "/signin" });
      }}
    >
      Sign out
    </button>
  );
}
```

- [ ] **Step 7: Place the button in the sidebar** — read `web/src/components/shell/sidebar.tsx`, then render `<SignOutButton />` in its footer/account region (next to the existing user/org display). Match the sidebar's existing button styling classes; do not restyle the sidebar.

- [ ] **Step 8: Run — verify all pass**

Run: `cd web && npx vitest run && npm run type-check && npm run lint`
Expected: PASS, types + eslint clean.

- [ ] **Step 9: Commit**

```bash
git add web/src/app/\(auth\)/onboarding/v2 web/src/components/auth/sign-out-button.tsx "web/src/components/auth/__tests__/sign-out-button.test.tsx" web/src/components/shell/sidebar.tsx
git commit -m "feat(web): v2 completion stamp (EN+zh-TW) + real signout

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

### Task B7: Cleanup audit + full verification

**Files:**
- Modify: `web/src/components/auth/require-onboarded.tsx` (+ its test) — remove if unreferenced.

- [ ] **Step 1: Find remaining `RequireOnboarded` consumers**

Run: `cd web && grep -rn "RequireOnboarded\|require-onboarded" src | grep -v __tests__`
Expected: no production imports remain (B2 removed the only one). If any remain, leave them and note why in the commit; do **not** blanket-delete.

- [ ] **Step 2: Remove the dead guard** — if Step 1 shows zero production consumers, `git rm web/src/components/auth/require-onboarded.tsx web/src/components/auth/__tests__/require-onboarded.test.tsx`. The gate now lives server-side.

- [ ] **Step 3: Audit `onboardingComplete` consumers** (informational — do not change behavior)

Run: `cd web && grep -rn "onboardingComplete\|isAuthReady" src | grep -v __tests__`
For each hit, confirm it feeds UI (e.g. greeting/topbar), not route-gating. Record findings in the commit message. The client `onboardingComplete` projection stays — it is now vestigial-for-gating only.

- [ ] **Step 4: Full suite, both sides**

Run from repo root: `make test && make lint`
Expected: api pytest green + ruff/mypy clean; web vitest green + eslint/tsc clean.

- [ ] **Step 5: Manual smoke (documented, not automated)**

In the PR description, record these manual checks run with `NEXT_PUBLIC_DEV_BYPASS_AUTH` **unset** against a local stack: (a) fresh user → persona → chooser → Manual → dashboard; (b) same with Quick/v2; (c) sign out → `/signin`; (d) sign back in → straight to dashboard (Flow 2); (e) create brand, quit at chooser, re-signin → bounced to `/onboarding`. With bypass **on**: `/brand/dashboard` renders directly.

- [ ] **Step 6: Commit**

```bash
git add -A web/src/components/auth
git commit -m "chore(web): retire client RequireOnboarded; gate is now server-side

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**1. Spec coverage:**
- Decision 1 (chooser, v1→/onboarding/manual, peers) → B4, B5 ✓
- Decision 2 (backend source of truth) → A1–A3, B1 ✓
- Decision 3 (server gate, removes hydration race) → B2, B3 (RequireOnboarded removed B7) ✓
- Decision 4 (`onboarded_at` on `brand`) → A1 ✓
- Decision 5 (gate honors dev bypass) → B3 Step 3 + test ✓
- Decision 6 (failure policy 401/403→/error, 404→/onboarding, 5xx→retry) → B1 `OnboardingStatusError`, B3 `resolveGateDestination` + tests ✓
- Error: completion failure keeps user on wizard → B4 (manual returns before navigate; B6 v2 `return` on error) ✓
- Edge: abandoned mid-wizard composes → covered by B3 (`onboarded:false`→/onboarding); smoke B7 Step 5(e) ✓
- Edge: zh-TW v2 → B6 Step 4 ✓
- Open Item 1 (capability pre-onboarding) → resolved in planning; asserted by A3 viewer-403 + status uses VIEW_BRAND_DASHBOARD ✓
- Open Item 2 (mark_onboarded module) → resolved: `BrandIdentityService` (A2) ✓
- Open Item 3 (audit onboardingComplete/RequireOnboarded) → B7 ✓
- Spec test-infra prerequisite → struck (harness verified present) ✓

**2. Placeholder scan:** No "TBD/TODO/implement later". Inspection steps ("read sidebar.tsx then place the button", "reuse existing fixtures") name exact files and the concrete pattern to mirror — these are real actions, not deferred work.

**3. Type consistency:** `getOnboardingStatus`/`completeOnboarding`/`OnboardingStatusError` defined in B1 and used identically in B3/B4/B6. `resolveGateDestination` returns `"render" | "retry" | path` consistently in impl + tests. `completeV2Onboarding` (B6) and `completeBrandOnboarding` (B4) both take the same `{cortexUserId,email,displayName,activeContext}` claims shape used by the existing `createMyBrand`/`completeBrandOnboarding` actions. API: `mark_onboarded(actor)` signature matches A2 def, A3 call, and test usage.

No gaps found.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-19-user-flow-v1v2-reconciliation.md`. Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
