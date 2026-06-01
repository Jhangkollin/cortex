# Multi-brand onboarding — chunk 3 ("Add a brand" + complete-screen redesign)

> First slice of the multi-brand frontend. Closes the cross-brand contamination bug where re-entering `/onboarding/v2` silently overwrites the user's existing brand. Implements design **`multi-brand/Multi-brand explorations.html` § 3** (`PatternOnboardingComplete`). Reuses backend wiring that chunks 1 (sidebar switcher) and 2 (portfolio page) will consume.

## Why this exists

Today (`develop` as of 2026-05-26):

- Backend (#69) allows multiple brands per user (`brand_membership` no longer has a per-user founder-unique index).
- The frontend wizard does **not** call `createMyBrand` when re-entered; every server action in `web/src/app/(auth)/onboarding/v2/*-actions.ts` reads `claims.activeContext.id` from the NextAuth session — which still points at the user's existing brand.
- Result: re-running `/onboarding/v2` to onboard a new site (e.g. `daohe.academy`) PUTs the new profile onto the **existing** `brand_id`. The previous brand's profile is overwritten in place, and #71/#72's staleness-then-relevance regenerate the previous brand's voice / media / questions caches with the new data. Hamilton's brand was replaced by daohe in place — there is no row preserved anywhere for Hamilton.

The fix has two halves: a UI entry to create a new brand cleanly, and a server-side safety rail that refuses to overwrite an already-onboarded brand on direct navigation. This spec covers both, plus the design-mocked rewrite of the onboarding complete screen.

## In scope (this PR)

1. **Backend — list brands API.** `GET /v1/brands` returns the calling user's brands with the fields the complete-screen band + future sidebar switcher need.
2. **Backend — verify `createMyBrand` allows N>1 per user.** Post-#69 it already does; this is a verification step + an integration test pinning the contract.
3. **Server action — `createAnotherBrandAction`.** Wraps `createMyBrand`, returns the new `brandId` and the next `activeContext` shape so the client can call `session.update()` and the JWT picks up the new brand on its next callback.
4. **Step-complete rewrite** to match `PatternOnboardingComplete`: hero ("<Brand> joined your portfolio"), portfolio band (other brands + `NEW`-pip tile + "Add another brand" tile + single-brand fallback), two CTAs ("Open Discover" preserved, "Add a brand" new), agents grid kept.
5. **"Add a brand" wiring.** Click → `createAnotherBrandAction()` → `session.update({activeContext: newCtx})` → `router.push('/onboarding/v2')`. Wizard restarts against the fresh brand_id.
6. **Safety rail (the B-specific part).** `/onboarding/v2` server-component entry: if `activeContext.brand.onboarded_at !== null`, `redirect('/onboarding')`. The `/onboarding` chooser, when the user has any onboarded brand, surfaces an "Add another brand" button as the primary CTA above the Quick/Manual cards — clicking it uses the same `createAnotherBrandAction` + `session.update` + redirect flow.

## Out of scope (deferred to other chunks)

- **Chunk 1 — sidebar brand switcher.** Reuses `GET /v1/brands` + `createAnotherBrandAction` + `session.update`. Comes next.
- **Chunk 2 — brands portfolio page.** Deferred per user instruction.
- `RequireOnboarded` gate revision and a separate edit-existing-brand flow.
- Cross-brand views (compare visibility / share-of-voice across brands).
- Permissions: per-brand stakeholders, "invite to this brand" vs "invite to org".
- Per-brand visualisation of Knowledge Base / Brand Voice / Connectors / Media Network / History.
- Visibility / WoW-delta numbers on the portfolio-band tiles (the API exposes the shape; UI shows placeholders if real metrics aren't ready).

## Architecture

### 1. Backend — `GET /v1/brands`

Mirrors existing brand endpoints: pure FastAPI `Depends(authenticated_user)`, no per-brand capability check (the route returns *only* the caller's own memberships, scoped by `app_user.id`). Located at `api/src/cortex_api/app/api/brand/router.py` alongside the existing single-brand routes.

**Response shape** (`BrandListItemDTO`):

```python
class BrandListItemDTO(BaseModel):
    id: UUID
    display_name: str
    domain: str | None
    role: BrandRole              # the caller's role in this brand
    onboarded_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # Visibility / last_checked left off for now — chunk 1 can add them when
    # the insights read model gains a per-brand summary endpoint. The UI
    # gracefully renders "—" when absent so adding fields later is additive.
```

**Capability**: none beyond authentication — by definition the user can see brands they have membership in. Query joins `brand_membership` (user_id = caller) to `brand` (+ optional `brand_profile` for `display_name` fallback) ordered by `updated_at DESC`.

**Source of truth**: `brand` + `brand_membership`. `brand.display_name` is the canonical name; `brand_profile.name` is only used by the UI when the wizard is mid-flight and `brand.display_name` is still the placeholder. The list endpoint does **not** read `brand_profile`.

### 2. Server action — `createAnotherBrandAction`

New file `web/src/app/(auth)/onboarding/v2/add-brand-actions.ts` (mirrors the existing `*-actions.ts` files' shape, including the `"use server"` type-export trap guard documented in cortex#67). Wraps `createMyBrand` from `@/lib/cortex-api`:

```typescript
export async function createAnotherBrandAction(): Promise<{
  brandId: string;
  activeContext: ActiveContext;
}> {
  const session = await auth();
  // … cortexUserId / email guards mirror media-actions.ts …
  const created = await createMyBrand(claims);
  const newCtx: ActiveContext = {
    kind: "brand",
    id: created.id,
    role: "admin",
    capabilities: created.capabilities,   // ADMIN on a brand they founded
  };
  return { brandId: created.id, activeContext: newCtx };
}
```

The action **does not** call `session.update()` itself — that has to run client-side via `useSession()` because the NextAuth `jwt` callback's `trigger === "update"` is fired by the client `update()` helper. The action returns the new claims; the client calls `session.update({activeContext: result.activeContext})` and then `router.push('/onboarding/v2')`.

### 3. Step-complete UI

`web/src/components/onboarding-v2/step-complete.tsx` is rewritten to render the three blocks from `PatternOnboardingComplete`:

- **Hero** — driven by `brand_count`:
  - `count === 1`: "<Brand> · Agent is online" (the current copy — single-brand fallback, no regression).
  - `count >= 2`: "<Brand> joined your portfolio" + "You now manage **<count> brands** from one Cortex workspace — switch between them anytime from the sidebar."
- **Portfolio band** — only rendered when `count >= 2`. Tiles for other brands (favicon mono + name + "X% visibility · Y" or "indexing · first agents starting" placeholder), the just-onboarded one with a `NEW` pip, and an "Add another brand" affordance tile. Click on "Add another" calls `onAddBrand()`. Tiles for existing brands are display-only in chunk 3 (switching is chunk 1's responsibility).
- **Two CTAs**:
  - Primary "Open Discover" — preserves the existing lime-gradient + `handleEnterDiscover` flow (`router.push('/brand/dashboard')`).
  - Secondary "Add a brand" card — calls `onAddBrand()`.
- **Agents grid** — kept verbatim for live-feel parity with today's screen.

The component is rewritten in our Tailwind + tokens stack (not the prototype's vanilla CSS). Pixel-match the prototype's hierarchy/colours via tokens already in `web/src/styles/tokens.css`.

The zh sibling (`web/src/components/onboarding-v2-zh/step-complete.tsx`) gets the same restructure with translated copy.

### 4. `onAddBrand` wiring

In `web/src/app/(auth)/onboarding/v2/page.tsx` (and `zh-TW/page.tsx`):

```typescript
const { update } = useSession();
const router = useRouter();

const onAddBrand = useCallback(async () => {
  const { activeContext } = await createAnotherBrandAction();
  await update({ activeContext });   // triggers NextAuth jwt({trigger:"update"})
  // localStorage onboarding state is keyed by brand_id; clear before restart
  // so the new brand starts at step 0 (URL paste), not the previous one's
  // completion state.
  try { localStorage.removeItem("cortex.onboarding.v2"); } catch {}
  router.push("/onboarding/v2");
}, [update, router]);
```

Passed down to `<StepComplete onAddBrand={...} />`.

### 5. Safety rail

Two changes:

**`/onboarding/v2/page.tsx`** — currently a client page. Wrap with a **server-component layout** (`layout.tsx` or convert page to server with a child client component) that checks the session's active brand's `onboarded_at`. If non-null, `redirect('/onboarding')`. Implementation note: the `RequireOnboarded` middleware that protects `/brand/*` is the inverse of this — we can reuse its session-reading helper.

```typescript
// web/src/app/(auth)/onboarding/v2/layout.tsx (new — server component)
import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { getOnboardingStatus } from "@/lib/cortex-api";

export default async function OnboardingV2Layout({ children }: { children: React.ReactNode }) {
  const session = await auth();
  if (!session?.user?.activeContext || session.user.activeContext.kind !== "brand") {
    redirect("/onboarding");
  }
  const status = await getOnboardingStatus(/* claims */, session.user.activeContext.id);
  if (status.onboarded_at) {
    // The active brand is already onboarded — running the wizard on it would
    // overwrite its profile. Bounce to the chooser, which surfaces "Add another
    // brand" as the explicit, non-destructive entry.
    redirect("/onboarding");
  }
  return <>{children}</>;
}
```

**`/onboarding/page.tsx` (chooser)** — convert to a server component (it's currently `export default function OnboardingChooser()` with no data fetching). Fetch the user's brand list. If `brands.some(b => b.onboarded_at)`, render an "Add another brand" card above the Quick / Manual options as the primary CTA. The card is a client-component button that runs the same `onAddBrand` flow (action + `session.update` + redirect).

The chooser's stale comment about `createMyBrand` 409s is removed.

## Data flow

```
User on /brand/dashboard for Hamilton
      │
      │ (clicks "Add a brand" — sidebar later, or "Run again" / direct nav)
      ▼
/onboarding (chooser, server) — sees Hamilton.onboarded_at != null
      │ ↳ renders "Add another brand" as primary CTA
      ▼
[Click "Add another brand"]  (client)
      │
      ├── createAnotherBrandAction()   (server action → cortex-api POST /v1/brand)
      │     returns { brandId: <new>, activeContext: {kind:'brand', id:<new>, role:'admin', capabilities:[…]} }
      │
      ├── useSession().update({activeContext: newCtx})
      │     → NextAuth jwt({trigger:"update"}) → resolve-context → token.activeContext = newCtx
      │     → next request carries JWT with new brand_id
      │
      └── router.push('/onboarding/v2')
            │
            ▼
      OnboardingV2Layout (server) — checks activeContext.brand.onboarded_at
            │  is null (new brand) ✓
            ▼
      Wizard runs against the NEW brand_id
            analyze → confirm → media → questions → voice → complete
            Each *-actions.ts reads claims.activeContext = new brand ✓
            New brand_voice / brand_media_network / brand_weekly_questions rows
            are created under the new brand_id. Hamilton untouched.
            │
            ▼
      Step-complete: brand_count = 2
            Portfolio band shows [Hamilton tile] + [New brand · NEW pip] + [Add another tile]
            "Open Discover" routes to /brand/dashboard for the new brand.
```

## Error handling

| Failure | Behaviour | Reasoning |
|---|---|---|
| `createMyBrand` throws (network / 5xx) | `onAddBrand` shows an inline error toast; nothing changes (active_context unchanged). | The user can retry; we don't want to half-create state. |
| `session.update()` succeeds but resolve-context returns no `activeContext` | Detect post-update (`update()` returns the new session); if `activeContext.id !== newBrandId`, show an error and roll back navigation. | NextAuth's `update()` resolves to the new session; we can assert before navigating. |
| `GET /v1/brands` fails on step-complete | Hero degrades to single-brand copy; portfolio band hidden. `Open Discover` still works. | Never block the success moment on a side-call. |
| `getOnboardingStatus` fails in the safety-rail layout | Render the wizard (fail-open, since the inverse is more annoying than the bug). Log a warning. | A blocked wizard on a network blip is a worse UX than a rare overwrite; the bug fix is the common case, not the edge. |

## Testing

**Backend (`api/`):**
- `tests/integration/test_brand_list_api.py` — `GET /v1/brands` returns the caller's brands (multi-membership), excludes others, ordering by `updated_at DESC`, capability gate (`401` without auth, `200` with).
- `tests/integration/test_create_my_brand_multi.py` — calling `POST /v1/brand` twice for the same user creates two independent brands with two memberships (pins the post-#69 contract; covered partially by `test_post_brand_twice_creates_two_independent_brands` but extend with capability assertions on the second brand).

**Web (`web/`):**
- `tests/onboarding/add-brand-actions.test.ts` — `createAnotherBrandAction` calls `createMyBrand`, returns the new id + claims; throws clearly on missing session.
- `tests/components/onboarding-v2/step-complete.test.tsx` — renders the single-brand hero when `count === 1` (portfolio band absent); renders the portfolio band + `NEW` pip + "Add another" tile when `count >= 2`; "Add a brand" click invokes `onAddBrand`.
- `tests/integration/onboarding-v2-safety-rail.test.ts` — direct nav to `/onboarding/v2` when the active brand is onboarded redirects to `/onboarding`; redirect does not fire when `onboarded_at` is null.
- `tests/integration/onboarding-chooser-add-another.test.tsx` — chooser server-renders the "Add another brand" CTA when any of the user's brands has `onboarded_at`; absent otherwise.

**E2E** (optional, defer if Playwright wiring is too much for this PR):
- Onboard brand A → complete → click "Add a brand" on step-complete → wizard restarts → analyze a different URL → complete brand B → DB shows two independent brand rows, both onboarded, with distinct profiles / weekly_questions / brand_voice.

## File summary

**New files:**
- `api/src/cortex_api/app/api/brand/router.py` — extend with `GET /v1/brands` (or new `_router_list.py` if the existing router file is getting unwieldy).
- `api/src/cortex_api/app/api/brand/dto.py` — `BrandListItemDTO`.
- `api/tests/integration/test_brand_list_api.py`
- `api/tests/integration/test_create_my_brand_multi.py`
- `web/src/app/(auth)/onboarding/v2/add-brand-actions.ts`
- `web/src/app/(auth)/onboarding/v2/layout.tsx` (safety rail)
- `web/src/app/(auth)/onboarding/v2/zh-TW/layout.tsx` (mirror)
- `web/src/components/onboarding-v2/__tests__/step-complete-multi-brand.test.tsx`
- `web/tests/onboarding/add-brand-actions.test.ts`

**Modified files:**
- `web/src/components/onboarding-v2/step-complete.tsx` — rewrite to match `PatternOnboardingComplete`.
- `web/src/components/onboarding-v2-zh/step-complete.tsx` — mirror.
- `web/src/app/(auth)/onboarding/v2/page.tsx` — pass `onAddBrand` prop to `<StepComplete>`; load brand list for `brand_count` and portfolio-band data.
- `web/src/app/(auth)/onboarding/v2/zh-TW/page.tsx` — mirror.
- `web/src/app/(auth)/onboarding/page.tsx` — convert to server, surface "Add another brand" CTA if any onboarded brand exists; remove the stale `createMyBrand` 409 comment.
- `web/src/lib/cortex-api.ts` — add `listMyBrands(claims)` wrapper for `GET /v1/brands`.
- `web/src/lib/auth.ts` — no change expected (already handles `trigger:"update"`), but verify the `activeContext` shape returned by `createMyBrand` flows through unchanged.

## Risks and migrations

- **No DB migration.** All schema needed already exists (brand, brand_membership, brand_profile, onboarded_at column, BrandRole enum).
- **Session shape backward-compat.** The `activeContext` shape `session.update()` receives is the same shape the existing `jwt({trigger:"update"})` callback handles for persona-picker brand creation — so this is exercising a paved path, not inventing one.
- **localStorage `cortex.onboarding.v2`** stores wizard step. We clear it on "Add a brand" so the new brand starts at step 0. If it leaks across brands (it's a single key, not brand-scoped today), the worst case is the user starts at the wrong step for the new brand — but the clear guard handles the common path.
- **Routes order matters.** Adding the safety-rail `layout.tsx` to `/onboarding/v2/` does not affect any other route (Next.js scoping). The chooser server-component conversion replaces a pure-client component; verify there are no client-only hooks remaining.

## Acceptance criteria

1. `POST /v1/brand` called twice by the same user creates two independent brand rows + two ADMIN memberships (verified by integration test).
2. `GET /v1/brands` returns exactly the caller's brands.
3. Clicking "Add a brand" on step-complete results in a new brand_id appearing in the user's brand list, the JWT carrying the new `active_context.id` on the next request, and the wizard restarting from step 0 against that new brand.
4. Direct navigation to `/onboarding/v2` while the active brand is `onboarded_at != null` redirects to `/onboarding`. The chooser surfaces "Add another brand" as the primary CTA in that state.
5. Step-complete renders the single-brand hero (no portfolio band) when the user has exactly one brand; otherwise renders the portfolio band + `NEW` pip on the just-onboarded brand + "Add another brand" tile.
6. Re-running the Hamilton → daohe scenario in UAT: Hamilton's `brand_profile` is **not** overwritten; daohe lives at its own `brand_id` with its own weekly_questions / brand_voice / brand_media_network rows.
