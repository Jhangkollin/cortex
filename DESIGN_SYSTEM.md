# Cortex Web — Design System Reference

> **Purpose**: Give any AI agent (or human) enough context to produce UI that is visually consistent with the Cortex onboarding / dashboard surface.  
> **Stack**: Next.js 16 App Router · Tailwind 4 · shadcn/ui · Material Icons Outlined · inline `style` for onboarding components.  
> **Token source**: `src/app/tokens.css` · `src/app/globals.css`

---

## How to use this document with an AI agent

To get the highest design consistency, always provide the agent with **all three files together**:

| File | What it provides |
|------|-----------------|
| `web/DESIGN_SYSTEM.md` *(this file)* | Rules, token semantics, usage guidelines, Do/Don't |
| `web/src/app/tokens.css` | Every token's actual hex value and semantic alias |
| `web/src/components/onboarding-v2/primitives.tsx` | Full implementation of `Card`, `Badge`, `OnbButton`, `Icon` |

### Prompt template

Copy the block below and paste it at the top of your agent prompt, then attach the three files above as context:

```
You are building UI that must be visually consistent with the Cortex onboarding design system.

Rules you MUST follow:
1. Colors — use only the CSS variables defined in tokens.css. Never hardcode hex values.
   Primary action:  var(--mly-teal-600)
   Icon / accent:   var(--mly-teal-700)
   Body text:       var(--mly-ink-900) / var(--mly-ink-800)
   Muted text:      var(--mly-ink-500)
   Card border:     var(--mly-ink-150)
   Card background: #ffffff
   Page background: #f8f8f6

2. Typography — 4-tier scale (Noto Sans), no exceptions:
   Tier 1 body:       16px  400
   Tier 2 label:      14px  700  (bold only)
   Tier 3 supporting: 13px  400
   Tier 4 micro:      12px  400  (700 + uppercase for overline)
   Step heading:      clamp(24px, 2.4vw, 32px) 700, font-family Fraunces serif
   KPI numbers:       font-family Roboto (--font-numeric)

3. Spacing — all padding / gap / margin must be multiples of 4px.
   Card padding:        20px
   Two-column gap:      24px
   Section gap:         16–20px
   Icon-to-label gap:   8px

4. Components — use Card, Badge, OnbButton, Icon from primitives.tsx.
   Do not recreate them inline.

5. Icons — Material Icons Outlined only.
   Usage: <Icon name="people" size={16} color="var(--mly-teal-700)" />

6. Do not use --brand-teal, paper-*, or any token not in tokens.css.
```

---

## 1. Color Tokens

All CSS variables are defined in `:root` and are available everywhere.

### Brand Teal (primary)

**Rule: always use the `--mly-teal-*` scale. `--brand-teal` is deprecated — do not use it.**

| Token | Value | Usage |
|-------|-------|-------|
| `--mly-teal-700` | `#1C726B` | Icon accent · decorative text · brand label on white |
| `--mly-teal-600` | `#225D59` | **Primary button fill** · interactive fill (= `--primary`) |
| `--mly-teal-800` | `#144948` | Button hover/active · dark surface |
| `--mly-teal-400` | `#38A69A` | Highlight accent |
| `--mly-teal-200` | `#80CBC4` | Selected/focus border |
| `--mly-teal-050` | `#E9EFEB` | Selected tint background · page tint |

**Decision guide**

```
What are you styling?
│
├─ Primary button background     →  var(--mly-teal-600)
├─ Primary button hover          →  var(--mly-teal-800)
├─ Icon / label on white bg      →  var(--mly-teal-700)
├─ Selected card border          →  var(--mly-teal-200)
├─ Selected card background      →  var(--mly-teal-050)
└─ Accent line / progress bar    →  var(--mly-teal-400) or var(--mly-teal-700)
```

### Ink (neutral greys)

| Token | Value | Usage |
|-------|-------|-------|
| `--mly-ink-900` | `#1A1A1A` | Maximum contrast / headings |
| `--mly-ink-800` | `#333333` | Body copy |
| `--mly-ink-700` | `#424242` | Secondary body |
| `--mly-ink-600` | `#616161` | Subheadings |
| `--mly-ink-500` | `#666666` | Muted labels |
| `--mly-ink-400` | `#757575` | Subtle labels / icons |
| `--mly-ink-300` | `#9E9E9E` | Placeholder |
| `--mly-ink-200` | `#CCCCCC` | Borders |
| `--mly-ink-150` | `#E0E0E0` | **Card borders (default)** / dividers |
| `--mly-ink-100` | `#EEEEEE` | Hairlines / section dividers |
| `--mly-ink-050` | `#F5F5F5` | Subtle backgrounds |
| `--mly-ink-025` | `#F9F9FB` | Page / onboarding background |

### Status

| Token | Value | Usage |
|-------|-------|-------|
| `--mly-success` | `#26A69A` | Success states |
| `--mly-danger` | `#E53935` | Error / danger |
| `--danger-deep` | `#C62828` | Danger text on light bg (WCAG AA) |
| `--danger-soft` | `#FCEAEA` | Danger pill background |
| `--danger-soft-border` | `#F0B5B5` | Danger pill border |
| `--mly-warn` | `#FFCA28` | Warning |

### Accents (use sparingly)

| Token | Value | Usage |
|-------|-------|-------|
| `--gold` | `#B98821` | Gold accent (media persona) |
| `--gold-soft` | `#F1E4C1` | Gold tint background |
| `--cortex-amber-500` | `#F59E0B` | Scan-line animation, savings hero |
| `--cortex-purple-fg` | `#5B21B6` | Enterprise pill text |
| `--cortex-purple-bg` | `#F5F3FF` | Enterprise pill background |

---

## 2. Typography

**Font stacks**:
- `--font-sans`: `"Noto Sans"` — body, UI labels (default)
- `--font-numeric`: `"Roboto"` — numbers, stats, CountUp displays
- `--font-mono`: `"Roboto Mono"` — code, badge timestamps, faux-browser UI (keep intentionally small)
- `--font-serif`: `"Fraunces"` — editorial headings (onboarding step titles only)

### Type scale (tokens.css)

| Token | Size / Weight / Leading | Font | Usage |
|-------|------------------------|------|-------|
| `--text-display` | `700 64px / 1.05` | sans | Hero only (LaunchOverlay) |
| `--text-h1` | `700 34px / 1.2` | sans | Page-level title |
| `--text-h2` | `700 24px / 1.25` | sans | Step heading |
| `--text-h3` | `700 20px / 1.4` | sans | Section heading |
| `--text-h4` | `700 16px / 1.5` | sans | Card heading |
| `--text-body` | `400 16px / 1.5` | sans | **Body copy, list items** |
| `--text-strong` | `700 16px / 1.5` | sans | Emphasis within body |
| `--text-label` | `700 14px / 1.5` | sans | Card headings, bold labels |
| `--text-small` | `400 13px / 1.5` | sans | Supporting text, captions, descriptions |
| `--text-micro` | `400 12px / 1.45` | sans | Badge labels, metadata, overline |
| `--text-overline` | `700 12px / 1.4` | sans | Section eyebrow (+ `uppercase` + `0.08em` tracking) |
| `--text-button` | `500 14px / 1.4` | sans | Button label |
| *(numeric hero)* | `700 40–72px` | `--font-numeric` | Full-section KPI hero |
| *(numeric card)* | `700 20–36px` | `--font-numeric` | Card-level metric |
| *(numeric inline)* | `700 16–20px` | `--font-numeric` | Inline stat value |
| *(serif heading)* | `700 28–34px` | `--font-serif` | Onboarding step title |

### Onboarding 4-tier hierarchy

This is the **confirmed and applied** scale across all onboarding components:

```
Tier 0 — Step heading (Fraunces)
  font-family: var(--font-serif)
  font-size: clamp(24px, 2.4vw, 32px)
  font-weight: 700

Tier 1 — Body / primary content (Noto Sans)
  font-size: 16px
  font-weight: 400
  line-height: 1.5–1.6
  → Use for: subtitle paragraphs, Q&A content, answer text

Tier 2 — Label / card heading (Noto Sans)
  font-size: 14px
  font-weight: 700  (always bold at this tier)
  → Use for: card titles, section label with icon, voice tone names

Tier 3 — Supporting / caption (Noto Sans)
  font-size: 13px
  font-weight: 400 (or 500 for emphasis)
  → Use for: descriptions under headings, secondary info, metadata strings

Tier 4 — Micro / overline (Noto Sans)
  font-size: 12px
  font-weight: 400 (700 + uppercase for overline)
  → Use for: badge text, footer stats, URL snippets, eyebrow labels

Special — faux-browser simulation
  font-size: 9–10px, font-family: var(--font-mono)
  → Intentionally small; do NOT scale up
```

### Decision guide

```
What are you writing?
│
├─ Step title (Fraunces serif)   →  clamp(24px, 2.4vw, 32px) 700
├─ Main paragraph under title    →  16px 400  (Tier 1)
├─ Card heading / section label  →  14px 700  (Tier 2)
├─ Description / caption         →  13px 400  (Tier 3)
├─ Badge / overline / metadata   →  12px      (Tier 4)
├─ Button label                  →  14px 500
├─ KPI / stat number             →  --font-numeric, size by context (see table)
└─ Faux-browser sim text         →  9–10px mono — never scale up
```

### Do / Don't

| ✅ Do | ❌ Don't |
|-------|---------|
| Use 16px for body/answer text | Use 14px for body (old default) |
| Use 14px **only** with fontWeight 600/700 | Mix 14px regular with 14px bold at same level |
| Use 13px for supporting/secondary text | Jump from 12px micro straight to 16px body |
| Use `--font-numeric` for all stat values | Use Roboto Mono for metric numbers |
| Keep faux-browser fonts at 9–10px | Scale up browser simulation text |
| Add one tier for emphasis | Skip tiers (e.g. micro → body) |

---

## 3. Spacing

**All `padding`, `gap`, `margin` values must be multiples of 4px.** Non-multiples (e.g. 6, 10, 14, 18) are not permitted.

4px base grid:

| Token | Value | Padding usage | Gap usage |
|-------|-------|--------------|-----------|
| `--sp-1` | `4px` | Badge/chip vertical; icon button | Icon-to-label in inline rows |
| `--sp-2` | `8px` | Badge/chip horizontal; compact row vertical | Tight inline elements |
| `--sp-3` | `12px` | Row item padding; small card body | Standard flex row items |
| `--sp-4` | `16px` | Input, button horizontal; section inner | Column / section gap |
| `--sp-5` | `20px` | **Card default padding** | Wide section gap |
| `--sp-6` | `24px` | Large section; modal edges | **Two-column layout gap** |
| `--sp-7` | `32px` | Step page content area | — |
| `--sp-8` | `40px` | Hero blocks | — |
| `--sp-9` | `48px` | Display/showcase sections | — |
| `--sp-10` | `64px` | Full-page hero | — |

### Padding decision guide

```
Element type?
│
├─ Badge / chip / pill
│     vertical → 0–4px  ·  horizontal → 8–12px
│
├─ List / table row
│     vertical → 8–12px  ·  horizontal → 12–16px
│
├─ Card  →  padding: 20px  (always, all sides)
│
├─ Button
│     height fixed by size (sm=32 / md=40 / lg=48)
│     horizontal → 12–20px
│
└─ Page section / hero
      vertical → 32–48px  ·  horizontal → 20–32px
```

### Gap decision guide

```
Context?
│
├─ Icon + label inline       →  gap: 8
├─ Chip / badge row          →  gap: 4–8
├─ Card list (vertical)      →  gap: 16–20
├─ Section cards (vertical)  →  gap: 16–24
└─ Two-column layout         →  gap: 24
```

---

## 4. Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--r-xs` | `2px` | Micro chips |
| `--r-sm` | `4px` | Default controls, bar fills |
| `--r-md` | `8px` | Rows, compact cards |
| `--r-lg` | `12px` | — |
| `--r-pill` | `999px` | Badges, pills, rounded inputs |
| (onboarding card) | `10px` | `Card` component default |

---

## 5. Elevation (box-shadow)

| Token | Value | Usage |
|-------|-------|-------|
| `--elev-1` | `0 1px 2px rgba(0,0,0,0.06), 0 1px 1px rgba(0,0,0,0.04)` | Card (default) |
| `--elev-2` | `0 2px 6px rgba(0,0,0,0.06), 0 2px 4px rgba(0,0,0,0.04)` | Popover |
| `--elev-3` | `0 6px 16px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.05)` | Modal |

---

## 6. Motion

| Token | Value |
|-------|-------|
| `--ease-std` | `cubic-bezier(0.4, 0, 0.2, 1)` |
| `--dur-state` | `120ms` — hover / toggle |
| `--dur-panel` | `200ms` — panel slide |
| `--dur-route` | `320ms` — page transition |

Animation utilities (defined in `globals.css`):
- `animation: mly-fade-up 300ms Xms backwards` — stagger reveal (content entering from below)
- `animation: mly-scan-line 2.5s linear infinite` — horizontal scan line

---

## 7. Core Components (`primitives.tsx`)

All live in `src/components/onboarding-v2/primitives.tsx`.

### `Card`

White surface with standard border and shadow.

```tsx
<Card style={{ padding: 20 }}>
  {children}
</Card>
```

**Default styles**:
- `background: #fff`
- `border: 1px solid var(--mly-ink-150)` ← always use this, never `--paper-border`
- `border-radius: 10px`
- `box-shadow: var(--elev-1)`

**Override via `style` prop** (spread after defaults).

---

### `OnbButton`

```tsx
<OnbButton
  variant="primary" | "soft" | "ghost" | "gold"
  size="sm" | "md" | "lg"
  icon="material_icon_name"       // left icon (optional)
  iconRight="material_icon_name"  // right icon (optional)
  disabled={false}
  onClick={fn}
>
  Label
</OnbButton>
```

| Variant | Background | Text | Usage |
|---------|-----------|------|-------|
| `primary` | `--mly-teal-700` | white | Primary CTA |
| `soft` | `rgba(teal, 0.06)` | `--mly-teal-700` | Secondary action |
| `ghost` | transparent | `--mly-ink-600` | Tertiary / Back |
| `gold` | `--gold` | white | Special (deprecated → use `primary`) |

---

### `Icon`

Renders a Material Icons Outlined symbol.

```tsx
<Icon name="hub" size={15} color="var(--mly-teal-600)" />
```

- `name`: any [Material Icons Outlined](https://fonts.google.com/icons) name in snake_case
- `size`: number (px)
- `color`: CSS color string

**Commonly used icons in Cortex**:
`hub`, `people`, `leaderboard`, `trending_up`, `sell`, `adjust`, `check_circle`, `category`, `edit`, `info`, `lock`, `credit_card`, `savings`, `home_work`, `rocket_launch`, `arrow_back`, `arrow_forward`, `search`, `close`

---

### `Badge`

```tsx
<Badge color="teal" | "gold" | "neutral" style={{}}>
  label
</Badge>
```

Pill-shaped label. `color="teal"` → teal-050 bg + teal-700 text.

---

### `CountUp`

Animates a number from 0 to `to`.

```tsx
<CountUp
  key={value}         // re-key to re-animate on value change
  to={9.6}
  duration={1200}     // ms
  decimals={1}        // decimal places
  suffix="M"          // appended string
/>
```

Use `var(--font-numeric)` for the containing element.

---

## 8. Card Anatomy & Header Pattern

Every card in the onboarding surface follows the same header pattern:

```tsx
{/* Card header row */}
<div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
  <Icon name="hub" size={15} color="var(--mly-teal-600)" />
  <div style={{ fontSize: 13, fontWeight: 700, color: "var(--mly-ink-900)" }}>
    Card title
  </div>
  {/* Optional right side — badge, timestamp, count */}
  <Badge color="teal" style={{ marginLeft: "auto" }}>6 outlets</Badge>
</div>
```

**Rules**:
- Icon size: **15px** (header), **12–13px** (body rows)
- Title: `fontSize: 13, fontWeight: 700, color: mly-ink-900`
- Right side: `marginLeft: "auto"` to push it to the far right
- Padding: **20px** (default card padding)

---

## 9. Layout Patterns

### Onboarding two-column grid

```tsx
<div style={{
  display: "grid",
  gridTemplateColumns: "1fr 2fr",  // left sidebar : right content
  gap: 24,
  alignItems: "flex-start",
}}>
  <div style={{ position: "sticky", top: 96 }}>
    {/* Left: brand info / progress */}
  </div>
  <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
    {/* Right: main content cards */}
  </div>
</div>
```

### Stat columns with dividers (horizontal metrics row)

```tsx
<div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr" }}>
  {stats.map((stat, i) => (
    <div key={stat.label} style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      padding: "0 12px",
      borderLeft: i > 0 ? "1px solid var(--mly-ink-100)" : undefined,
    }}>
      {/* icon + label */}
      <div style={{ fontSize: 28, fontWeight: 700, fontFamily: "var(--font-numeric)", color: "var(--mly-teal-700)" }}>
        {stat.value}
      </div>
      <div style={{ fontSize: 10, color: "var(--mly-ink-400)" }}>{stat.sub}</div>
    </div>
  ))}
</div>
```

### Section label (overline)

```tsx
<div style={{
  fontSize: 11,
  fontWeight: 700,
  letterSpacing: "0.07em",
  textTransform: "uppercase",
  color: "var(--mly-ink-400)",
  marginBottom: 10,
}}>
  Section title
</div>
```

### Row list (no cards, use for repeated items)

```tsx
{items.map((item, i) => (
  <div key={item.id} style={{
    display: "flex", gap: 12,
    padding: "10px 0",
    borderBottom: i < items.length - 1 ? "1px solid var(--mly-ink-100)" : undefined,
  }}>
    {/* Left accent bar */}
    <div style={{ width: 3, borderRadius: 99, background: "var(--mly-teal-200)", flexShrink: 0 }} />
    <div>{/* content */}</div>
  </div>
))}
```

### Inline chips / badges

```tsx
<span style={{
  padding: "1px 7px",
  borderRadius: 999,
  background: "var(--mly-ink-075, var(--mly-ink-100))",
  fontSize: 10,
  color: "var(--mly-ink-600)",
  fontWeight: 600,
}}>
  Label
</span>
```

---

## 10. Interactive States

### Checkbox (custom teal)

```tsx
<div style={{
  width: 16, height: 16,
  borderRadius: 4,
  border: `1.5px solid ${checked ? "var(--mly-teal-600)" : "var(--mly-ink-300)"}`,
  background: checked ? "var(--mly-teal-600)" : "#fff",
  display: "grid", placeItems: "center",
  transition: "background 150ms, border-color 150ms",
}}>
  {checked && (
    <svg width="9" height="7" viewBox="0 0 9 7" fill="none">
      <path d="M1 3.5L3.5 6L8 1" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )}
</div>
```

### Selected card

```tsx
<div style={{
  border: `1px solid ${checked ? "var(--mly-teal-200)" : "var(--mly-ink-150)"}`,
  background: checked ? "var(--mly-teal-025, #f0fafb)" : "var(--mly-ink-025)",
  transition: "border-color 150ms, background 150ms",
  cursor: "pointer",
}}>
```

### Disabled button

Use `disabled` prop on `OnbButton`. Visually: opacity reduced, cursor `not-allowed`.

---

## 11. Onboarding-specific Conventions

### Background
The onboarding wizard uses `var(--mly-ink-025)` (`#F9F9FB`) as the main content area background — **not white, not the old paper cream** (`--paper-warm`).

### Step headings
Use `--font-serif` (Fraunces) for editorial h2 headings within steps:
```tsx
<h2 style={{
  fontFamily: "var(--font-serif)",
  fontSize: 30,
  fontWeight: 700,
  color: "var(--mly-ink-900)",
  lineHeight: 1.2,
  margin: 0,
}}>
```

### Eyebrow pill (above h2)
```tsx
<div style={{
  display: "inline-flex", alignItems: "center", gap: 6,
  padding: "4px 12px",
  borderRadius: 999,
  background: "var(--mly-teal-050)",
  border: "1px solid var(--mly-teal-100)",
  fontSize: 11, fontWeight: 700, color: "var(--mly-teal-700)",
  letterSpacing: "0.06em", textTransform: "uppercase",
  marginBottom: 12,
}}>
  <Icon name="bolt" size={12} color="var(--mly-teal-600)" />
  Step label
</div>
```

### Stagger reveal animation
Apply progressively to cards appearing on load:
```tsx
style={{ animation: `mly-fade-up 300ms ${i * 80}ms backwards` }}
```

### Numbers / stats hero
Large display numbers always use:
- `fontFamily: "var(--font-numeric)"`
- `fontWeight: 700`
- `letterSpacing: "-0.04em"`
- Color: `var(--mly-teal-700)` (positive) or `var(--danger-deep)` (gap/risk)

---

## 12. Do's and Don'ts

| ✅ Do | ❌ Don't |
|------|---------|
| Use `var(--mly-ink-150)` for card borders | Use `var(--paper-border)` — legacy |
| Use `var(--mly-ink-025)` for page background | Use `var(--paper-warm)` or `--paper` cream tones |
| Use `var(--mly-teal-700)` for primary brand color | Use raw hex `#1C726B` (use the token) |
| Keep `Card` padding at **20px** | Mix 16px and 24px inconsistently |
| Use Material Icons Outlined names in snake_case | Invent icon names — check [Google Fonts Icons](https://fonts.google.com/icons) |
| Use `--font-numeric` for all numbers | Use `--font-sans` for stat displays |
| Put primary CTA in footer, disabled until ready | Put CTA inline in content area |
| Use `var(--mly-teal-*)` for selected/active states | Use `--gold` for primary actions |
| `borderRadius: 99` for pill shapes | Hard-code `borderRadius: 999` inconsistently |
| Consistent card header: `icon(15) + title(13,700)` | Mix icon sizes or title weights across cards |

---

## 13. Quick Reference: Most Used Combinations

### Default Card
```tsx
<Card style={{ padding: 20 }}>
```
`bg: #fff · border: mly-ink-150 · radius: 10px · shadow: elev-1`

### Subtle background section
```tsx
background: "var(--mly-ink-025)"
border: "1px solid var(--mly-ink-100)"
borderRadius: 8
```

### Teal selected/active pill
```tsx
background: "var(--mly-teal-050)"
border: "1px solid var(--mly-teal-100)"
color: "var(--mly-teal-700)"
```

### Danger text inline
```tsx
color: "var(--danger-deep)"  // #C62828, WCAG AA on white
```

### Mono label (timestamps, counts, IDs)
```tsx
fontFamily: "var(--font-mono)"
fontSize: 11
color: "var(--mly-ink-400)"
```

---

*Source files: `src/app/tokens.css` · `src/app/globals.css` · `src/components/onboarding-v2/primitives.tsx`*  
*Last updated: 2026-06-01*
