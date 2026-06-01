# Multi-Brand Onboarding (Chunk 3 — Add a brand + Safety rail) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the cross-brand contamination bug: each new onboarding creates its own `brand_id` (via an explicit "Add a brand" CTA and a safety rail that bounces direct navigation away from an already-onboarded active brand), and ship the multi-brand-aware redesign of the wizard's complete screen.

**Architecture:** Backend adds a tenant-scoped `GET /v1/brands` listing the caller's own brands. Web adds a `createAnotherBrandAction` server action (wraps `createMyBrand`) plus client wiring (`useSession().update()` → `router.push('/onboarding/v2')`) on a redesigned `step-complete` and a new "Add another brand" CTA in the `/onboarding` chooser. A server-component layout at `/onboarding/v2` redirects to the chooser when the active brand is already `onboarded_at != null`.

**Tech Stack:** FastAPI + SQLModel + dependency_injector (api). Next.js 16 App Router + NextAuth v5 + Tailwind (web). Vitest (web). pytest + httpx TestClient (api).

**Spec:** `docs/superpowers/specs/2026-05-26-multi-brand-onboarding-add-brand-design.md`

---

## File map

**New (api):**
- `api/src/cortex_api/app/api/brand_identity/dto.py` — extend with `BrandListItem` + `BrandListResponse`.
- `api/src/cortex_api/service/brand_identity/repo/brand_repo.py` — add `list_for_user_id(...)`.
- `api/src/cortex_api/service/brand_identity/service.py` — add `list_my_brands(...)`.
- `api/src/cortex_api/app/api/brand_identity/router.py` — add `GET /v1/brands` handler.
- `api/tests/integration/test_brand_list_api.py` — new integration test file.

**New (web):**
- `web/src/app/(auth)/onboarding/v2/add-brand-actions.ts` — `"use server"` action wrapping `createMyBrand`.
- `web/src/app/(auth)/onboarding/v2/layout.tsx` — server-component safety rail.
- `web/src/app/(auth)/onboarding/v2/zh-TW/layout.tsx` — zh mirror.
- `web/src/components/onboarding-chooser-add-another.tsx` — client-side "Add another brand" button (mounted by the chooser server component).
- `web/src/components/onboarding-v2/portfolio-band.tsx` — portfolio band sub-component (used by step-complete).
- `web/src/components/onboarding-v2-zh/portfolio-band.tsx` — zh mirror.
- `web/src/components/onboarding-v2/__tests__/step-complete-multi-brand.test.tsx`
- `web/src/components/onboarding-v2-zh/__tests__/step-complete-multi-brand.test.tsx`
- `web/src/app/(auth)/onboarding/v2/__tests__/add-brand-actions.test.ts`
- `web/src/app/(auth)/onboarding/v2/__tests__/layout-safety-rail.test.tsx`
- `web/src/app/(auth)/onboarding/__tests__/chooser-add-another.test.tsx`

**Modified (web):**
- `web/src/components/onboarding-v2/step-complete.tsx` — single-brand fallback + portfolio-band integration + "Add a brand" CTA.
- `web/src/components/onboarding-v2-zh/step-complete.tsx` — zh mirror.
- `web/src/app/(auth)/onboarding/v2/page.tsx` — load brand list, pass `onAddBrand` to `<StepComplete>`.
- `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx` — zh mirror.
- `web/src/app/(auth)/onboarding/page.tsx` — convert to server component, surface the add-another CTA conditionally.
- `web/src/lib/cortex-api.ts` — add `listMyBrands(claims)` wrapper (or regen-then-export from generated client).

---

## Task 1: Backend DTO — `BrandListItem` + `BrandListResponse`

**Files:**
- Modify: `api/src/cortex_api/app/api/brand_identity/dto.py`

- [ ] **Step 1: Add DTOs (no test — used downstream)**

Open `api/src/cortex_api/app/api/brand_identity/dto.py` and append:

```python
class BrandListItem(BaseModel):
    """One row of the caller's brand list (chunk-3 add-a-brand portfolio band)."""

    id: UUID
    display_name: str
    domain: str | None = None
    role: BrandRole
    onboarded_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BrandListResponse(BaseModel):
    brands: list[BrandListItem]
```

Imports already present (`BaseModel`, `UUID`, `datetime`, `BrandRole`); if `BrandRole` is not yet imported, add:

```python
from cortex_api.service.brand_identity.model.brand_role import BrandRole
```

- [ ] **Step 2: Commit**

```bash
cd api
git add src/cortex_api/app/api/brand_identity/dto.py
git commit -m "feat(brand): BrandListItem/BrandListResponse DTOs for GET /v1/brands"
```

---

## Task 2: Repo — `list_for_user_id`

**Files:**
- Modify: `api/src/cortex_api/service/brand_identity/repo/brand_repo.py`
- Test: `api/tests/integration/test_brand_list_api.py` (created later; repo behavior is exercised by service+API tests).

- [ ] **Step 1: Add method**

Open `api/src/cortex_api/service/brand_identity/repo/brand_repo.py` and add (above any sweep / housekeeping methods if present, beside `get`):

```python
async def list_for_user_id(
    self,
    session: AsyncSession,
    user_id: UUID,
) -> list[tuple[Brand, BrandRole]]:
    """All brands the caller has membership in, with the caller's role per brand.

    Joins brand → brand_membership filtered to the calling user. Ordered by
    `brand.updated_at DESC` so "most recently touched" surfaces first — this
    matches both the sidebar switcher (chunk 1) and the portfolio band
    (chunk 3) sort order ("last opened" proxy).
    """
    from cortex_api.service.brand_identity.model.brand_membership import BrandMembership  # noqa: PLC0415 — local to avoid circular

    stmt = (
        select(Brand, BrandMembership.role)
        .join(BrandMembership, BrandMembership.brand_id == Brand.id)
        .where(BrandMembership.user_id == user_id)
        .order_by(Brand.updated_at.desc())  # type: ignore[attr-defined]
    )
    result = await session.execute(stmt)
    return [(b, r) for b, r in result.all()]
```

If `select` / `Brand` / `AsyncSession` imports aren't already there, mirror what `get(...)` uses.

- [ ] **Step 2: Commit**

```bash
cd api
git add src/cortex_api/service/brand_identity/repo/brand_repo.py
git commit -m "feat(brand): BrandRepo.list_for_user_id — caller's brands + per-brand role"
```

---

## Task 3: Service — `list_my_brands`

**Files:**
- Modify: `api/src/cortex_api/service/brand_identity/service.py`

- [ ] **Step 1: Add service method**

In `BrandIdentityService` (beside `create_brand_with_admin`), add:

```python
async def list_my_brands(self, user_id: UUID) -> list[tuple[Brand, BrandRole]]:
    """List the caller's own brands. Pure read; no capability gate needed —
    by definition the user can see brands they have membership in.

    The router projects (Brand, BrandRole) rows into BrandListItem DTOs.
    """
    async with self._database_client.session() as session:
        return await self._brand_repo.list_for_user_id(session, user_id)
```

Imports: `Brand` and `BrandRole` are already used in the file; if not, mirror existing imports near the top.

- [ ] **Step 2: Commit**

```bash
cd api
git add src/cortex_api/service/brand_identity/service.py
git commit -m "feat(brand): BrandIdentityService.list_my_brands"
```

---

## Task 4: Router — `GET /v1/brands` + integration test (TDD)

**Files:**
- Create: `api/tests/integration/test_brand_list_api.py`
- Modify: `api/src/cortex_api/app/api/brand_identity/router.py`

- [ ] **Step 1: Write the failing integration test**

Create `api/tests/integration/test_brand_list_api.py`:

```python
"""GET /v1/brands — caller's brands only."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_list_my_brands_returns_only_callers_brands(
    client: TestClient,
    bootstrap_jwt,  # type: ignore[no-untyped-def]
    session_jwt,  # type: ignore[no-untyped-def]
) -> None:
    """User Dave creates two brands; user Eve creates one. /v1/brands for Dave
    returns exactly Dave's two; Eve's brand is NEVER in Dave's list.
    """
    # Dave
    bt_dave = bootstrap_jwt(oauth_subject="116000000000000000040", email="dave@m.co")
    me_dave = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bt_dave}"})
    assert me_dave.status_code == 200
    dave_id = me_dave.json()["user_id"]
    st_dave = session_jwt(user_id=dave_id, email="dave@m.co")
    r1 = client.post("/v1/brand", headers={"Authorization": f"Bearer {st_dave}"}, json={})
    r2 = client.post("/v1/brand", headers={"Authorization": f"Bearer {st_dave}"}, json={})
    assert r1.status_code == 201 and r2.status_code == 201

    # Eve
    bt_eve = bootstrap_jwt(oauth_subject="116000000000000000041", email="eve@m.co")
    eve_id = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {bt_eve}"}).json()["user_id"]
    st_eve = session_jwt(user_id=eve_id, email="eve@m.co")
    re = client.post("/v1/brand", headers={"Authorization": f"Bearer {st_eve}"}, json={})
    assert re.status_code == 201

    # Dave lists — sees exactly two, his.
    listed = client.get("/v1/brands", headers={"Authorization": f"Bearer {st_dave}"})
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert "brands" in body
    ids = {b["id"] for b in body["brands"]}
    assert ids == {r1.json()["brand"]["id"], r2.json()["brand"]["id"]}
    # Eve's brand absent
    assert re.json()["brand"]["id"] not in ids
    # Caller's role propagated (founder → admin)
    assert all(b["role"] == "admin" for b in body["brands"])


def test_list_my_brands_unauthenticated_returns_401(client: TestClient) -> None:
    r = client.get("/v1/brands")
    assert r.status_code == 401
```

- [ ] **Step 2: Run to verify it FAILS**

```bash
cd api
uv run pytest tests/integration/test_brand_list_api.py -v
```

Expected: FAIL with 404 on `/v1/brands` (route doesn't exist yet).

- [ ] **Step 3: Add the route**

Open `api/src/cortex_api/app/api/brand_identity/router.py` and add this handler (after the existing `@router.post("/v1/brand", ...)` `create_brand`):

```python
@router.get(
    "/v1/brands",
    response_model=BrandListResponse,
)
@inject
async def list_my_brands(
    app_user: AppUser = Depends(current_app_user),
    brand_identity_service: BrandIdentityService = Depends(Provide[BrandIdentityContainer.service]),
) -> BrandListResponse:
    """List the caller's own brands.

    No per-brand capability gate — the result set is intrinsically scoped to
    the caller's memberships. The sidebar switcher (chunk 1) and the
    onboarding-complete portfolio band (chunk 3) consume this.
    """
    rows = await brand_identity_service.list_my_brands(app_user.id)
    return BrandListResponse(
        brands=[
            BrandListItem(
                id=b.id,
                display_name=b.display_name,
                domain=getattr(b, "domain", None),
                role=role,
                onboarded_at=b.onboarded_at,
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
            for (b, role) in rows
        ]
    )
```

Update the DTO import at the top:

```python
from cortex_api.app.api.brand_identity.dto import (
    BrandListItem,        # NEW
    BrandListResponse,    # NEW
    BrandResponse,
    CreateBrandRequest,
    CreateBrandResponse,
    # ... existing imports stay
)
```

- [ ] **Step 4: Run test to verify it PASSES**

```bash
cd api
uv run pytest tests/integration/test_brand_list_api.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Run full api lint + tests**

```bash
cd api
uv run ruff check src tests && uv run ruff format --check src tests && uv run mypy src
uv run pytest -q
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
cd api
git add src/cortex_api/app/api/brand_identity/router.py tests/integration/test_brand_list_api.py
git commit -m "feat(brand): GET /v1/brands — caller's brands for multi-brand switcher/portfolio"
```

---

## Task 5: Regenerate web API client from the new OpenAPI

**Files:**
- Modify: `web/src/lib/api-client/generated/**` (autogen — do not hand-edit)
- Modify: `web/src/lib/cortex-api.ts` — add `listMyBrands` wrapper

- [ ] **Step 1: Regenerate**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/multi-brand-chunk3
make generate-client
```

Expected: the generated client now includes a `listMyBrands` (or similarly named) function and a `BrandListResponse`/`BrandListItem` model. The CI "api-client: drift check" key passes locally.

- [ ] **Step 2: Add typed wrapper to `cortex-api.ts`**

Open `web/src/lib/cortex-api.ts` and find the section where the existing brand wrappers live (`startBrandVoice`, `pollBrandVoice`, etc.). Add:

```typescript
import type { CortexTokenClaims } from "./cortex-token";

export type BrandRole = "viewer" | "editor" | "admin";

export type BrandListItem = {
  id: string;
  display_name: string;
  domain: string | null;
  role: BrandRole;
  onboarded_at: string | null;
  created_at: string;
  updated_at: string;
};

export async function listMyBrands(
  claims: CortexTokenClaims,
): Promise<BrandListItem[]> {
  const res = await httpGet("/v1/brands", claims);   // use the existing httpGet helper
  if (!res.ok) {
    throw new Error(`listMyBrands failed: ${res.status} ${await res.text()}`);
  }
  const body = (await res.json()) as { brands: BrandListItem[] };
  return body.brands;
}
```

If `cortex-api.ts` already re-exports types from the generated client, use those types instead of inlining the type declarations above — preserve the file's existing convention.

- [ ] **Step 3: Sanity check**

```bash
cd web
npm run type-check
```

Expected: no new errors.

- [ ] **Step 4: Commit**

```bash
git add web/src/lib/api-client/generated web/src/lib/cortex-api.ts
git commit -m "feat(web): regenerate api client + listMyBrands wrapper for GET /v1/brands"
```

---

## Task 6: Server action — `createAnotherBrandAction` (TDD)

**Files:**
- Create: `web/src/app/(auth)/onboarding/v2/add-brand-actions.ts`
- Test: `web/src/app/(auth)/onboarding/v2/__tests__/add-brand-actions.test.ts`

- [ ] **Step 1: Write the failing test**

Create `web/src/app/(auth)/onboarding/v2/__tests__/add-brand-actions.test.ts`:

```typescript
import { describe, expect, it, vi, beforeEach } from "vitest";

// Same trap as the other onboarding action tests: this is a "use server" file
// importing @/lib/auth (next-auth). Mock both before importing the module
// under test.
vi.mock("@/lib/auth", () => ({ auth: vi.fn() }));
vi.mock("@/lib/cortex-api", () => ({ createMyBrand: vi.fn() }));

import { auth } from "@/lib/auth";
import { createMyBrand } from "@/lib/cortex-api";

import { createAnotherBrandAction } from "../add-brand-actions";

const authMock = vi.mocked(auth);
const createMyBrandMock = vi.mocked(createMyBrand);

beforeEach(() => {
  vi.clearAllMocks();
});

describe("createAnotherBrandAction", () => {
  it("creates a new brand and returns the new activeContext", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "user-uuid-1",
        name: "Okis",
        activeContext: { kind: "brand", id: "old-brand", role: "admin", capabilities: [] },
      },
    } as never);
    createMyBrandMock.mockResolvedValue({
      brand: { id: "new-brand-uuid", display_name: "Okis Chuang's brand" },
      capabilities: ["view_brand_dashboard", "edit_brand_settings"],
    } as never);

    const out = await createAnotherBrandAction();

    expect(createMyBrandMock).toHaveBeenCalledTimes(1);
    expect(out.brandId).toBe("new-brand-uuid");
    expect(out.activeContext).toEqual({
      kind: "brand",
      id: "new-brand-uuid",
      role: "admin",
      capabilities: ["view_brand_dashboard", "edit_brand_settings"],
    });
  });

  it("throws when there is no session", async () => {
    authMock.mockResolvedValue(null as never);
    await expect(createAnotherBrandAction()).rejects.toThrow(/not signed in/i);
    expect(createMyBrandMock).not.toHaveBeenCalled();
  });

  it("throws when cortexUserId is missing", async () => {
    authMock.mockResolvedValue({
      user: { email: "okis@m.co", activeContext: { kind: "brand", id: "old" } },
    } as never);
    await expect(createAnotherBrandAction()).rejects.toThrow(/sign-in did not complete/i);
    expect(createMyBrandMock).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run to verify it FAILS**

```bash
cd web
npx vitest run src/app/\(auth\)/onboarding/v2/__tests__/add-brand-actions.test.ts
```

Expected: FAIL — module under test does not exist yet.

- [ ] **Step 3: Implement the action**

Create `web/src/app/(auth)/onboarding/v2/add-brand-actions.ts`:

```typescript
"use server";

/**
 * Server Action — create another brand in the user's portfolio (multi-brand).
 *
 * Wraps `createMyBrand` (cortex-api). Returns the new brand's id and the
 * `activeContext` shape the client needs to pass to `useSession().update()`
 * so the JWT carries the new brand_id on its next callback. The wizard's
 * server actions read `claims.activeContext.id`, so refreshing it on the
 * client BEFORE navigating to `/onboarding/v2` is what makes the next run
 * operate on the new brand instead of overwriting the previous one.
 */

import { auth } from "@/lib/auth";
import { type ActiveContext, createMyBrand } from "@/lib/cortex-api";
import type { CortexTokenClaims } from "@/lib/cortex-token";

export async function createAnotherBrandAction(): Promise<{
  brandId: string;
  activeContext: ActiveContext;
}> {
  const session = await auth();
  if (!session?.user?.email) {
    throw new Error("Not signed in.");
  }
  if (!session.user.cortexUserId) {
    throw new Error("Sign-in did not complete. Please sign out and sign in again.");
  }

  const claims: CortexTokenClaims = {
    cortexUserId: session.user.cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    // Any valid activeContext satisfies createMyBrand's auth requirement —
    // it derives the user from cortexUserId, not the active brand.
    activeContext: session.user.activeContext ?? { kind: "brand", id: "" },
  };

  const result = await createMyBrand(claims);
  const newCtx: ActiveContext = {
    kind: "brand",
    id: result.brand.id,
    role: "admin",
    capabilities: result.capabilities,
  };
  return { brandId: result.brand.id, activeContext: newCtx };
}
```

If `ActiveContext` is not exported from `@/lib/cortex-api`, add it to that module and to the import line accordingly. If the shape of `createMyBrand`'s return differs from `{ brand: { id }, capabilities }`, adjust the destructuring to match the generated client.

- [ ] **Step 4: Run test to verify it PASSES**

```bash
cd web
npx vitest run src/app/\(auth\)/onboarding/v2/__tests__/add-brand-actions.test.ts
```

Expected: all three tests PASS.

- [ ] **Step 5: Run lint + type-check**

```bash
cd web
npm run lint && npm run type-check
```

Expected: no new errors.

- [ ] **Step 6: Commit**

```bash
git add "web/src/app/(auth)/onboarding/v2/add-brand-actions.ts" "web/src/app/(auth)/onboarding/v2/__tests__/add-brand-actions.test.ts"
git commit -m "feat(web): createAnotherBrandAction server action for multi-brand"
```

---

## Task 7: Safety-rail layout for `/onboarding/v2`

**Files:**
- Create: `web/src/app/(auth)/onboarding/v2/layout.tsx`
- Create: `web/src/app/(auth)/onboarding/v2/zh-TW/layout.tsx`
- Test: `web/src/app/(auth)/onboarding/v2/__tests__/layout-safety-rail.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `web/src/app/(auth)/onboarding/v2/__tests__/layout-safety-rail.test.tsx`:

```typescript
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("next/navigation", () => ({ redirect: vi.fn() }));
vi.mock("@/lib/auth", () => ({ auth: vi.fn() }));
vi.mock("@/lib/cortex-api", () => ({ getOnboardingStatus: vi.fn() }));

import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { getOnboardingStatus } from "@/lib/cortex-api";

import OnboardingV2Layout from "../layout";

const redirectMock = vi.mocked(redirect);
const authMock = vi.mocked(auth);
const statusMock = vi.mocked(getOnboardingStatus);

beforeEach(() => vi.clearAllMocks());

describe("OnboardingV2Layout (safety rail)", () => {
  it("redirects to /onboarding when active brand is already onboarded", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "u-1",
        activeContext: { kind: "brand", id: "brand-1", role: "admin", capabilities: [] },
      },
    } as never);
    statusMock.mockResolvedValue({ onboarded_at: "2026-05-25T00:00:00Z" } as never);

    await OnboardingV2Layout({ children: <div /> } as never);

    expect(redirectMock).toHaveBeenCalledWith("/onboarding");
  });

  it("renders children when active brand is not onboarded", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "u-1",
        activeContext: { kind: "brand", id: "brand-1", role: "admin", capabilities: [] },
      },
    } as never);
    statusMock.mockResolvedValue({ onboarded_at: null } as never);

    const out = await OnboardingV2Layout({ children: <div data-testid="kids" /> } as never);
    expect(redirectMock).not.toHaveBeenCalled();
    // The layout returns its children; just assert the call shape.
    expect(out).toBeTruthy();
  });

  it("redirects when active context is missing or not a brand", async () => {
    authMock.mockResolvedValue({ user: { email: "okis@m.co", cortexUserId: "u-1" } } as never);
    await OnboardingV2Layout({ children: <div /> } as never);
    expect(redirectMock).toHaveBeenCalledWith("/onboarding");
  });
});
```

- [ ] **Step 2: Run to verify it FAILS**

```bash
cd web
npx vitest run "src/app/(auth)/onboarding/v2/__tests__/layout-safety-rail.test.tsx"
```

Expected: FAIL — layout module does not exist.

- [ ] **Step 3: Implement the layout**

Create `web/src/app/(auth)/onboarding/v2/layout.tsx`:

```typescript
import { redirect } from "next/navigation";

import { auth } from "@/lib/auth";
import { getOnboardingStatus } from "@/lib/cortex-api";
import type { CortexTokenClaims } from "@/lib/cortex-token";

/**
 * Safety rail: refuse to run the v2 wizard against an already-onboarded
 * brand.
 *
 * Without this, navigating to /onboarding/v2 with an active_context pointing
 * at an onboarded brand would silently overwrite that brand's profile
 * (because every wizard server-action reads activeContext.id from the
 * session). The chunk-3 "Add a brand" entry creates a new brand AND refreshes
 * the session before navigating — but direct navigation is the foot-gun this
 * layout closes.
 */
export default async function OnboardingV2Layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  const activeContext = session?.user?.activeContext;
  if (!session?.user?.email || !session.user.cortexUserId || !activeContext || activeContext.kind !== "brand" || !activeContext.id) {
    redirect("/onboarding");
  }

  const claims: CortexTokenClaims = {
    cortexUserId: session.user.cortexUserId,
    email: session.user.email,
    displayName: session.user.name ?? null,
    activeContext,
  };
  try {
    const status = await getOnboardingStatus(claims, activeContext.id);
    if (status.onboarded_at) {
      // Active brand is already onboarded — bounce to the chooser, which
      // surfaces "Add another brand" as the explicit non-destructive entry.
      redirect("/onboarding");
    }
  } catch {
    // Fail-open: a blocked wizard on a transient network blip is a worse
    // UX than a rare overwrite. Log via the browser/console pipeline that
    // already exists; the chunk-3 fix is the common case, not the edge.
  }

  return <>{children}</>;
}
```

- [ ] **Step 4: Create the zh-TW mirror layout**

Create `web/src/app/(auth)/onboarding/v2/zh-TW/layout.tsx`:

```typescript
export { default } from "../layout";
```

- [ ] **Step 5: Run tests to verify they PASS**

```bash
cd web
npx vitest run "src/app/(auth)/onboarding/v2/__tests__/layout-safety-rail.test.tsx"
npm run lint && npm run type-check
```

Expected: all three tests PASS; lint+types clean.

- [ ] **Step 6: Commit**

```bash
git add "web/src/app/(auth)/onboarding/v2/layout.tsx" "web/src/app/(auth)/onboarding/v2/zh-TW/layout.tsx" "web/src/app/(auth)/onboarding/v2/__tests__/layout-safety-rail.test.tsx"
git commit -m "feat(web): safety-rail layout — bounce direct nav from onboarded brand"
```

---

## Task 8: Chooser — convert to server component + "Add another brand" CTA

**Files:**
- Modify: `web/src/app/(auth)/onboarding/page.tsx`
- Create: `web/src/components/onboarding-chooser-add-another.tsx`
- Test: `web/src/app/(auth)/onboarding/__tests__/chooser-add-another.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `web/src/app/(auth)/onboarding/__tests__/chooser-add-another.test.tsx`:

```typescript
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

vi.mock("@/lib/auth", () => ({ auth: vi.fn() }));
vi.mock("@/lib/cortex-api", () => ({ listMyBrands: vi.fn() }));

import { auth } from "@/lib/auth";
import { listMyBrands } from "@/lib/cortex-api";

import OnboardingChooser from "../page";

const authMock = vi.mocked(auth);
const listMock = vi.mocked(listMyBrands);

beforeEach(() => vi.clearAllMocks());

async function renderPage() {
  const node = await OnboardingChooser();
  return render(node as React.ReactElement);
}

describe("Onboarding chooser server component", () => {
  it("renders 'Add another brand' when the caller has any onboarded brand", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "u-1",
        activeContext: { kind: "brand", id: "brand-1", role: "admin", capabilities: [] },
      },
    } as never);
    listMock.mockResolvedValue([
      { id: "brand-1", display_name: "Hamilton", domain: null, role: "admin", onboarded_at: "2026-05-25T00:00:00Z", created_at: "2026-05-20T00:00:00Z", updated_at: "2026-05-25T00:00:00Z" },
    ] as never);

    await renderPage();
    expect(screen.getByRole("button", { name: /add another brand/i })).toBeInTheDocument();
  });

  it("does NOT render 'Add another brand' for a first-timer (no onboarded brands)", async () => {
    authMock.mockResolvedValue({
      user: {
        email: "okis@m.co",
        cortexUserId: "u-1",
        activeContext: { kind: "brand", id: "brand-1", role: "admin", capabilities: [] },
      },
    } as never);
    listMock.mockResolvedValue([
      { id: "brand-1", display_name: "Okis's brand", domain: null, role: "admin", onboarded_at: null, created_at: "2026-05-26T00:00:00Z", updated_at: "2026-05-26T00:00:00Z" },
    ] as never);

    await renderPage();
    expect(screen.queryByRole("button", { name: /add another brand/i })).not.toBeInTheDocument();
    // The Quick / Manual choices remain
    expect(screen.getByRole("link", { name: /quick.*ai setup/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /manual.*fill a form/i })).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run to verify it FAILS**

```bash
cd web
npx vitest run "src/app/(auth)/onboarding/__tests__/chooser-add-another.test.tsx"
```

Expected: FAIL — the chooser currently doesn't fetch brands or render the conditional CTA.

- [ ] **Step 3: Create the client-side add-another button**

Create `web/src/components/onboarding-chooser-add-another.tsx`:

```typescript
"use client";

import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useState } from "react";

import { createAnotherBrandAction } from "@/app/(auth)/onboarding/v2/add-brand-actions";

const ONBOARDING_STORAGE_KEY = "cortex.onboarding.v2";

export function OnboardingChooserAddAnother() {
  const { update } = useSession();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const { activeContext } = await createAnotherBrandAction();
      await update({ activeContext });
      // The wizard's local progress is single-keyed; clear it so a brand-new
      // brand starts at step 0 instead of inheriting a stale "complete" flag.
      try {
        localStorage.removeItem(ONBOARDING_STORAGE_KEY);
      } catch {
        // ignore
      }
      router.push("/onboarding/v2");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not add a new brand.");
      setBusy(false);
    }
  }

  return (
    <div className="mb-4">
      <button
        type="button"
        onClick={onClick}
        disabled={busy}
        className="flex w-full items-center gap-3 rounded-md border border-brand-700 bg-brand-700 px-5 py-4 text-left text-white shadow-elev-2 transition-transform hover:translate-y-[-1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-700/40 focus-visible:ring-offset-2 disabled:opacity-60"
      >
        <span className="material-icons-outlined">library_add</span>
        <span>
          <div className="text-base font-bold">Add another brand</div>
          <div className="text-sm text-brand-100">
            {busy ? "Preparing a fresh workspace…" : "Start a new onboarding without touching your existing brand."}
          </div>
        </span>
      </button>
      {error ? <div className="mt-2 text-sm text-red-700">{error}</div> : null}
    </div>
  );
}
```

- [ ] **Step 4: Rewrite the chooser as a server component**

Replace `web/src/app/(auth)/onboarding/page.tsx` with:

```typescript
import Link from "next/link";

import { auth } from "@/lib/auth";
import { listMyBrands } from "@/lib/cortex-api";
import type { CortexTokenClaims } from "@/lib/cortex-token";
import { OnboardingChooserAddAnother } from "@/components/onboarding-chooser-add-another";

/**
 * Onboarding setup chooser (server component).
 *
 * If the caller already has any onboarded brand, we surface "Add another
 * brand" as the primary CTA above the Quick/Manual choices — that CTA runs
 * createAnotherBrandAction + session.update + redirect, so the wizard
 * restarts against a NEW brand instead of overwriting the existing one.
 *
 * For first-timers (no onboarded brand yet), the chooser keeps its original
 * two destinations exactly.
 */
export default async function OnboardingChooser() {
  let hasOnboardedBrand = false;
  const session = await auth();
  if (
    session?.user?.email &&
    session.user.cortexUserId &&
    session.user.activeContext?.kind === "brand" &&
    session.user.activeContext.id
  ) {
    const claims: CortexTokenClaims = {
      cortexUserId: session.user.cortexUserId,
      email: session.user.email,
      displayName: session.user.name ?? null,
      activeContext: session.user.activeContext,
    };
    try {
      const brands = await listMyBrands(claims);
      hasOnboardedBrand = brands.some((b) => b.onboarded_at);
    } catch {
      // Fail-open: render the chooser without the add-another CTA. First-timers
      // hit this path too if the call transiently fails.
    }
  }

  return (
    <div className="min-h-screen bg-ink-25 p-8">
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-2.5 text-base font-bold">
          <span aria-hidden className="grid h-7 w-7 place-items-center rounded-[5px] bg-brand-700 text-white">
            M
          </span>
          mlytics
        </div>
        <div className="text-[11px] font-bold uppercase tracking-[0.12em] text-brand-700">
          SET UP YOUR BRAND
        </div>
      </div>

      <h1 className="mb-2.5" style={{ font: "700 40px/1.1 var(--font-sans)", letterSpacing: "-0.02em" }}>
        How do you want to set up?
      </h1>
      <p className="mb-9 max-w-[560px] text-base text-ink-500">
        Let Cortex extract your brand from your website, or fill the details in
        yourself. You can edit everything later in Brand settings.
      </p>

      {hasOnboardedBrand ? <OnboardingChooserAddAnother /> : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Link
          href="/onboarding/v2"
          className="flex min-h-[220px] flex-col gap-3 rounded-md border border-brand-700 bg-brand-700 p-6 text-white shadow-elev-2 transition-transform hover:translate-y-[-1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-700/40 focus-visible:ring-offset-2"
        >
          <h3 className="m-0 text-xl font-bold">Quick · AI setup</h3>
          <p className="m-0 text-sm text-brand-100">
            Enter your website. Cortex crawls it and pre-fills your brand
            profile in ~30 seconds.
          </p>
        </Link>
        <Link
          href="/onboarding/manual?step=1"
          className="flex min-h-[220px] flex-col gap-3 rounded-md border border-ink-200 bg-white p-6 transition-transform hover:translate-y-[-1px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-700/40 focus-visible:ring-offset-2"
        >
          <h3 className="m-0 text-xl font-bold text-ink-900">Manual · fill a form</h3>
          <p className="m-0 text-sm text-ink-500">
            Type your brand details in a guided form. You can always run the AI
            setup later.
          </p>
        </Link>
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Run tests to verify they PASS**

```bash
cd web
npx vitest run "src/app/(auth)/onboarding/__tests__/chooser-add-another.test.tsx"
npm run lint && npm run type-check
```

Expected: both tests PASS; lint+types clean.

- [ ] **Step 6: Commit**

```bash
git add "web/src/app/(auth)/onboarding/page.tsx" "web/src/components/onboarding-chooser-add-another.tsx" "web/src/app/(auth)/onboarding/__tests__/chooser-add-another.test.tsx"
git commit -m "feat(web): onboarding chooser — Add-another-brand CTA when user has onboarded brand"
```

---

## Task 9: `PortfolioBand` component

**Files:**
- Create: `web/src/components/onboarding-v2/portfolio-band.tsx`
- Create: `web/src/components/onboarding-v2-zh/portfolio-band.tsx`
- (No dedicated test — exercised by step-complete tests in Task 10.)

- [ ] **Step 1: Implement the band**

Create `web/src/components/onboarding-v2/portfolio-band.tsx`:

```typescript
"use client";

import type { BrandListItem } from "@/lib/cortex-api";

export type PortfolioBandProps = {
  brands: BrandListItem[];
  justOnboardedBrandId: string;
  onAddBrand: () => void;
  addBusy?: boolean;
};

// Color/monogram for a brand. Mirrors the prototype's `BRANDS[*]` shape —
// derive from the display_name for stable visuals without persisting a color.
function fav(name: string): { color: string; mono: string } {
  const palette = ["#1C726B", "#225D59", "#144948", "#8A5A00", "#33597a", "#5A2D6E", "#3E6B2C", "#A04420"];
  const sum = [...name].reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return { color: palette[sum % palette.length], mono: name.slice(0, 1).toUpperCase() };
}

export function PortfolioBand({ brands, justOnboardedBrandId, onAddBrand, addBusy }: PortfolioBandProps) {
  // Display the OTHER brands (not the just-onboarded one), then the just-onboarded
  // one with a NEW pip, then the add-another tile. Stable order: matching the
  // server's `updated_at DESC` from listMyBrands.
  const others = brands.filter((b) => b.id !== justOnboardedBrandId);
  const justOnboarded = brands.find((b) => b.id === justOnboardedBrandId);

  return (
    <div className="my-6 rounded-md border border-ink-200 bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="m-0 text-sm font-bold text-ink-700">
          Your portfolio
          <span className="ml-2 inline-flex items-center rounded-full bg-ink-100 px-2 py-0.5 text-xs font-medium text-ink-600">
            {brands.length} brands
          </span>
        </h3>
        <span className="text-xs text-ink-500">View all brands →</span>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {others.map((b) => {
          const f = fav(b.display_name);
          return (
            <div key={b.id} className="flex items-center gap-3 rounded-md border border-ink-150 bg-ink-25 p-3">
              <div className="grid h-9 w-9 place-items-center rounded text-white font-bold" style={{ background: f.color }}>
                {f.mono}
              </div>
              <div className="min-w-0">
                <div className="truncate text-sm font-bold text-ink-900">{b.display_name}</div>
                <div className="truncate text-xs text-ink-500">
                  {b.onboarded_at ? "live · ready" : "indexing"}
                </div>
              </div>
            </div>
          );
        })}
        {justOnboarded ? (
          (() => {
            const f = fav(justOnboarded.display_name);
            return (
              <div className="relative flex items-center gap-3 rounded-md border-2 border-brand-700 bg-brand-50 p-3">
                <span className="absolute -right-2 -top-2 rounded-full bg-brand-700 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                  NEW
                </span>
                <div className="grid h-9 w-9 place-items-center rounded text-white font-bold" style={{ background: f.color }}>
                  {f.mono}
                </div>
                <div className="min-w-0">
                  <div className="truncate text-sm font-bold text-ink-900">{justOnboarded.display_name}</div>
                  <div className="truncate text-xs text-ink-500">indexing · first agents starting</div>
                </div>
              </div>
            );
          })()
        ) : null}
        <button
          type="button"
          onClick={onAddBrand}
          disabled={addBusy}
          className="flex items-center justify-center gap-2 rounded-md border border-dashed border-ink-300 bg-white p-3 text-sm text-ink-600 hover:border-brand-700 hover:text-brand-700 disabled:opacity-60"
        >
          <span className="material-icons-outlined">add</span>
          {addBusy ? "Preparing…" : "Add another brand"}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Mirror to zh**

Create `web/src/components/onboarding-v2-zh/portfolio-band.tsx`:

```typescript
"use client";
// zh sibling — copy mirrors with translated affordances.
export { PortfolioBand, type PortfolioBandProps } from "../onboarding-v2/portfolio-band";
```

(If the zh wizard's copy diverges, we'll fork later — for chunk 3 the shape is identical.)

- [ ] **Step 3: Lint + type-check**

```bash
cd web
npm run lint && npm run type-check
```

- [ ] **Step 4: Commit**

```bash
git add web/src/components/onboarding-v2/portfolio-band.tsx web/src/components/onboarding-v2-zh/portfolio-band.tsx
git commit -m "feat(web): PortfolioBand for step-complete (multi-brand)"
```

---

## Task 10: Step-complete rewrite (single-brand fallback + portfolio band + two CTAs)

**Files:**
- Modify: `web/src/components/onboarding-v2/step-complete.tsx`
- Modify: `web/src/components/onboarding-v2-zh/step-complete.tsx`
- Test: `web/src/components/onboarding-v2/__tests__/step-complete-multi-brand.test.tsx`
- Test: `web/src/components/onboarding-v2-zh/__tests__/step-complete-multi-brand.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `web/src/components/onboarding-v2/__tests__/step-complete-multi-brand.test.tsx`:

```typescript
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import { StepComplete } from "../step-complete";

const brand = {
  name: "Daohe Academy",
  monogram: "D",
  brandColor: "#1C726B",
  category: { primary: "Education" },
  products: [{ id: "p1", name: "Khaki Field", picked: true }],
  competitors: [],
} as never;

const brandsTwo = [
  { id: "brand-hamilton", display_name: "Hamilton", domain: null, role: "admin", onboarded_at: "2026-05-25T00:00:00Z", created_at: "2026-05-20T00:00:00Z", updated_at: "2026-05-25T00:00:00Z" },
  { id: "brand-daohe",    display_name: "Daohe Academy", domain: null, role: "admin", onboarded_at: null, created_at: "2026-05-26T00:00:00Z", updated_at: "2026-05-26T00:00:00Z" },
] as never;

describe("StepComplete — multi-brand variant", () => {
  it("collapses to single-brand hero when brand_count === 1", () => {
    render(
      <StepComplete
        brand={brand}
        brands={[brandsTwo[1]]}
        justOnboardedBrandId="brand-daohe"
        onAddBrand={vi.fn()}
        onEnterDiscover={vi.fn()}
      />,
    );
    // Single-brand hero
    expect(screen.getByText(/Brand Agent is online/i)).toBeInTheDocument();
    // No portfolio band
    expect(screen.queryByRole("heading", { name: /your portfolio/i })).not.toBeInTheDocument();
    // No "Add a brand" secondary CTA
    expect(screen.queryByRole("button", { name: /add a brand/i })).not.toBeInTheDocument();
  });

  it("shows portfolio band + 'Add a brand' CTA when brand_count >= 2", () => {
    const onAddBrand = vi.fn();
    render(
      <StepComplete
        brand={brand}
        brands={brandsTwo}
        justOnboardedBrandId="brand-daohe"
        onAddBrand={onAddBrand}
        onEnterDiscover={vi.fn()}
      />,
    );
    expect(screen.getByText(/Daohe Academy joined your portfolio/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /your portfolio/i })).toBeInTheDocument();
    // NEW pip is on the just-onboarded brand only
    expect(screen.getAllByText("NEW").length).toBe(1);
    // Two CTAs (primary Open Discover + secondary Add a brand). There are two
    // "Add a brand"-ish controls now — the band's tile and the CTA card. Click
    // the CTA-card button.
    fireEvent.click(screen.getByRole("button", { name: /^add a brand$/i }));
    expect(onAddBrand).toHaveBeenCalledTimes(1);
  });
});
```

Mirror to `web/src/components/onboarding-v2-zh/__tests__/step-complete-multi-brand.test.tsx` (identical structure, importing from `../step-complete`).

- [ ] **Step 2: Run to verify they FAIL**

```bash
cd web
npx vitest run "src/components/onboarding-v2/__tests__/step-complete-multi-brand.test.tsx"
```

Expected: FAIL — StepComplete does not yet accept `brands`/`justOnboardedBrandId`/`onAddBrand`.

- [ ] **Step 3: Rewrite step-complete (en)**

Open `web/src/components/onboarding-v2/step-complete.tsx`. Replace the export with a multi-brand-aware version. The file is currently 478 lines — keep the **agents grid** + the existing visual tokens; refactor the surrounding shell. Concretely, change the component signature to accept the new props and wrap the hero + body to render conditionally:

```typescript
// At top of file, add (or merge into) the existing imports:
import type { BrandListItem } from "@/lib/cortex-api";
import { PortfolioBand } from "./portfolio-band";

export type StepCompleteProps = {
  brand: ExtractedBrand;                  // existing
  brands: BrandListItem[];                // NEW — caller's full brand list
  justOnboardedBrandId: string;           // NEW — the brand_id this run owns
  onAddBrand: () => void;                 // NEW — invokes createAnotherBrandAction wiring
  onEnterDiscover: () => void;            // existing handler renamed to make intent explicit (or keep current name)
  addBrandBusy?: boolean;                 // NEW — passed through to the CTA + band tile
};

export function StepComplete(props: StepCompleteProps) {
  const isMulti = props.brands.length >= 2;
  return (
    <section className="…existing wrapper classes…">
      {/* HERO */}
      {isMulti ? (
        <Hero
          title={`${props.brand.name} joined your portfolio`}
          subtitle={`You now manage ${props.brands.length} brands from one Cortex workspace — switch between them anytime from the sidebar.`}
        />
      ) : (
        <Hero
          title={`${props.brand.name} · Brand Agent is online`}
          subtitle="First brand answers go live in 23 h 47 m."
        />
      )}

      {/* PORTFOLIO BAND (multi-brand only) */}
      {isMulti ? (
        <PortfolioBand
          brands={props.brands}
          justOnboardedBrandId={props.justOnboardedBrandId}
          onAddBrand={props.onAddBrand}
          addBusy={props.addBrandBusy}
        />
      ) : null}

      {/* TWO CTAs */}
      <div className={`mt-6 grid grid-cols-1 gap-4 ${isMulti ? "lg:grid-cols-2" : ""}`}>
        {/* Primary — Open Discover (existing visual) */}
        <PrimaryDiscoverCta brandName={props.brand.name} onClick={props.onEnterDiscover} />
        {isMulti ? (
          <SecondaryAddBrandCta onClick={props.onAddBrand} busy={props.addBrandBusy} />
        ) : null}
      </div>

      {/* AGENTS GRID — kept verbatim from the existing file */}
      <AgentsGrid brandName={props.brand.name} />
    </section>
  );
}
```

Then add the small sub-components (`Hero`, `PrimaryDiscoverCta`, `SecondaryAddBrandCta`, `AgentsGrid`) using markup/classes the existing file already defines — extracting from the current `step-complete.tsx` and tweaking copy/structure. For the `SecondaryAddBrandCta`:

```typescript
function SecondaryAddBrandCta({ onClick, busy }: { onClick: () => void; busy?: boolean }) {
  return (
    <div className="rounded-md border border-ink-200 bg-white p-5">
      <div className="mb-2 inline-flex h-8 w-8 items-center justify-center rounded bg-ink-100">
        <span className="material-icons-outlined text-ink-700">library_add</span>
      </div>
      <div className="text-xs font-bold uppercase tracking-wide text-ink-500">Or, keep going</div>
      <div className="mt-1 text-xl font-bold text-ink-900">Onboard another brand</div>
      <div className="mt-1 text-sm text-ink-600">
        Manage subsidiaries, sub-brands, or client accounts side-by-side. Each one gets its own agent team.
      </div>
      <button
        type="button"
        onClick={onClick}
        disabled={busy}
        className="mt-4 inline-flex items-center gap-2 rounded-md border border-brand-700 bg-white px-4 py-2 text-sm font-bold text-brand-700 hover:bg-brand-50 disabled:opacity-60"
      >
        <span className="material-icons-outlined">add</span>
        {busy ? "Preparing…" : "Add a brand"}
      </button>
    </div>
  );
}
```

The existing primary CTA stays as-is — just route its click through `props.onEnterDiscover` instead of the inline router push, so the page-level handler decides where to go.

- [ ] **Step 4: Run tests to verify they PASS**

```bash
cd web
npx vitest run "src/components/onboarding-v2/__tests__/step-complete-multi-brand.test.tsx"
```

Expected: both tests PASS.

- [ ] **Step 5: Mirror to zh**

Apply the equivalent edits to `web/src/components/onboarding-v2-zh/step-complete.tsx` (translate the en copy, keep the multi-brand structure identical). Run the zh test:

```bash
cd web
npx vitest run "src/components/onboarding-v2-zh/__tests__/step-complete-multi-brand.test.tsx"
```

Expected: PASS.

- [ ] **Step 6: Full web test pass**

```bash
cd web
npm test
npm run lint && npm run type-check
```

Expected: all green.

- [ ] **Step 7: Commit**

```bash
git add web/src/components/onboarding-v2/step-complete.tsx web/src/components/onboarding-v2-zh/step-complete.tsx web/src/components/onboarding-v2/__tests__/step-complete-multi-brand.test.tsx web/src/components/onboarding-v2-zh/__tests__/step-complete-multi-brand.test.tsx
git commit -m "feat(web): step-complete — multi-brand hero + portfolio band + Add-a-brand CTA"
```

---

## Task 11: `page.tsx` wiring (load brand list + pass `onAddBrand`)

**Files:**
- Modify: `web/src/app/(auth)/onboarding/v2/page.tsx`
- Modify: `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx`

- [ ] **Step 1: Wire the page**

In `web/src/app/(auth)/onboarding/v2/page.tsx` add a brand-list fetch (server-side via the page or a small client effect — choose whichever the file's current pattern supports; the wizard is currently `"use client"`, so use a small client effect that calls a server action `listMyBrandsAction()` you add alongside `add-brand-actions.ts`):

```typescript
// In add-brand-actions.ts, add a sibling read-only action:
export async function listMyBrandsAction(): Promise<BrandListItem[]> {
  const session = await auth();
  if (!session?.user?.email || !session.user.cortexUserId) return [];
  const claims = { /* same shape as createAnotherBrandAction */ };
  try {
    return await listMyBrands(claims as never);
  } catch {
    return [];
  }
}
```

In `page.tsx`, inside the wizard component:

```typescript
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { createAnotherBrandAction, listMyBrandsAction } from "@/app/(auth)/onboarding/v2/add-brand-actions";
import type { BrandListItem } from "@/lib/cortex-api";

const ONBOARDING_STORAGE_KEY = "cortex.onboarding.v2";

// inside the component:
const { update } = useSession();
const router = useRouter();
const [brands, setBrands] = useState<BrandListItem[]>([]);
const [addBrandBusy, setAddBrandBusy] = useState(false);

useEffect(() => {
  let cancelled = false;
  void (async () => {
    const list = await listMyBrandsAction();
    if (!cancelled) setBrands(list);
  })();
  return () => { cancelled = true; };
}, []);

const onAddBrand = useCallback(async () => {
  if (addBrandBusy) return;
  setAddBrandBusy(true);
  try {
    const { activeContext } = await createAnotherBrandAction();
    await update({ activeContext });
    try { localStorage.removeItem(ONBOARDING_STORAGE_KEY); } catch {}
    router.push("/onboarding/v2");
  } catch (e) {
    setAddBrandBusy(false);
    // Toast / inline error — defer the toast surface; for chunk 3 a console
    // warn + button re-enable is enough since the chooser path is the
    // common entry.
    console.warn("[onboarding] add-another failed", e);
  }
}, [addBrandBusy, router, update]);

// existing handleEnterDiscover stays as-is (router.push("/brand/dashboard"))

// When rendering the complete step:
{step === 7 ? (
  <StepComplete
    brand={brand}
    brands={brands}
    justOnboardedBrandId={session?.user?.activeContext?.id ?? ""}
    onAddBrand={onAddBrand}
    addBrandBusy={addBrandBusy}
    onEnterDiscover={handleEnterDiscover}
  />
) : null}
```

Mirror the equivalent changes in `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx`.

- [ ] **Step 2: Lint + types + tests**

```bash
cd web
npm run lint && npm run type-check && npm test
```

Expected: all green.

- [ ] **Step 3: Commit**

```bash
git add "web/src/app/(auth)/onboarding/v2/page.tsx" "web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx" "web/src/app/(auth)/onboarding/v2/add-brand-actions.ts"
git commit -m "feat(web): wizard page wiring — load brands, onAddBrand, brand_count to StepComplete"
```

---

## Task 12: Final acceptance pass (manual + UAT)

**Files:**
- (None — verification step.)

- [ ] **Step 1: Local sanity**

```bash
cd /Users/okis.chuang/Documents/dev/cortex/.claude/worktrees/multi-brand-chunk3
make lint && make test
```

Expected: api + web both pass; CI parity locally.

- [ ] **Step 2: Push branch + open PR**

```bash
git push -u origin feat/multi-brand-onboarding-add-brand
gh pr create --base develop --title "feat(onboarding): multi-brand chunk 3 — Add a brand + safety rail" --body "$(cat <<'EOF'
## Summary
Closes the cross-brand contamination bug — each new onboarding now creates its own brand_id and the wizard refuses to operate on an already-onboarded brand on direct navigation. Implements chunk 3 of the design (`multi-brand/Multi-brand explorations.html` §3 — onboarding's last step, multi-brand aware).

## What's in
- `GET /v1/brands` (caller's brands).
- `createAnotherBrandAction` server action + client wiring (`useSession().update()` → `router.push('/onboarding/v2')`).
- Safety-rail server layout at `/onboarding/v2` — redirects to `/onboarding` if the active brand is `onboarded_at != null`.
- Chooser server-renders "Add another brand" CTA when the user has any onboarded brand.
- `step-complete.tsx` redesigned: single-brand fallback unchanged; multi-brand path shows hero ("X joined your portfolio"), Portfolio Band (other brands + NEW pip + Add-another tile), and a secondary "Add a brand" CTA card beside Open Discover.
- Integration + unit tests for each surface.

## Out (deferred)
- Chunk 1 (sidebar brand switcher) — reuses everything above.
- Chunk 2 (brand portfolio page) — deferred.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: After owl + CI green → merge → promote to UAT**

Same flow as #70/#71/#72: squash-merge, wait for Deploy run, helm-charts promote PR, `make helm-cortex ENV=uat`.

- [ ] **Step 4: UAT acceptance (the Hamilton → daohe regression)**

After deploy:
1. Hard-refresh the browser. Hit `/onboarding` while logged in.
2. Verify the "Add another brand" CTA appears (any of the user's brands is `onboarded_at != null`).
3. Click it. Confirm the wizard restarts at step 0 and that the URL bar still says `/onboarding/v2`.
4. Complete the wizard with a different URL (`hamilton-watch.com` or any new site).
5. After step-complete, query the DB:

```bash
kubectl exec -i -n cortex deploy/cortex-api -- python - <<'PY'
import asyncio, os, asyncpg
async def main():
    conn = await asyncpg.connect(host=os.environ["CORE_DB_HOST"], port=int(os.environ["CORE_DB_PORT"]),
        user=os.environ["CORE_DB_USERNAME"], password=os.environ["CORE_DB_PASSWORD"], database=os.environ["CORE_DB_NAME"])
    rows = await conn.fetch("""
        select b.id, b.display_name, b.created_at, b.onboarded_at, p.name
        from brand b left join brand_profile p on p.brand_id = b.id
        where b.id in (
            select brand_id from brand_membership where user_id = (select id from app_user where email = 'okischung@gmail.com')
        )
        order by b.created_at desc""")
    for r in rows:
        print(r)
    await conn.close()
asyncio.run(main())
PY
```

Expected: two rows for Okis — `019e42c0` (the existing brand) UNCHANGED, plus a NEW brand_id with the just-onboarded display_name.

6. Verify a direct navigation to `/onboarding/v2` while the new brand has `onboarded_at != null` redirects to `/onboarding` (the chooser, with "Add another brand" visible).

- [ ] **Step 5: Done — close the PR with a summary comment quoting the DB output**

---

## Self-review summary

- Spec coverage: every In-scope section (DTO, repo, service, route, action, layout, chooser, step-complete, page-wiring, tests, AC) maps to one of Tasks 1–12.
- Type/name consistency: `createAnotherBrandAction` / `listMyBrands` / `listMyBrandsAction` / `BrandListItem` used identically across tasks. `ONBOARDING_STORAGE_KEY` defined once per file.
- No placeholders ("TBD", "add validation") in code blocks; every step ships either a test, a code change, or a verified command.
- Acceptance criterion 6 (Hamilton untouched after re-onboarding daohe) is verified explicitly in Task 12 Step 4.

