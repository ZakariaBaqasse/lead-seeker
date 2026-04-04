# Lead Seeker — Design System

Inspired by Notion's minimal, content-first aesthetic. Clean whites, soft grays, restrained use of color, and generous whitespace.

---

## 1. Color Palette

### Base (Backgrounds & Surfaces)

| Token                 | Hex       | Usage                                       |
| --------------------- | --------- | ------------------------------------------- |
| `color-bg`            | `#FFFFFF` | Main page background                        |
| `color-bg-subtle`     | `#F7F7F5` | Sidebar, secondary panels, table zebra rows |
| `color-surface`       | `#FFFFFF` | Cards, modals, dropdowns                    |
| `color-surface-hover` | `#F1F1EF` | Card/row hover state                        |
| `color-border`        | `#E3E2E0` | Dividers, input borders, table borders      |
| `color-border-strong` | `#CBCAC8` | Focused inputs, selected rows               |

### Text

| Token                  | Hex       | Usage                          |
| ---------------------- | --------- | ------------------------------ |
| `color-text-primary`   | `#1A1A1A` | Headings, body copy            |
| `color-text-secondary` | `#6B6B6B` | Labels, metadata, placeholders |
| `color-text-tertiary`  | `#A0A0A0` | Disabled state, hints          |
| `color-text-on-accent` | `#FFFFFF` | Text on filled accent buttons  |

### Accent (Blue — actions & highlights)

| Token                 | Hex       | Usage                                   |
| --------------------- | --------- | --------------------------------------- |
| `color-accent`        | `#2383E2` | Primary buttons, links, active nav item |
| `color-accent-hover`  | `#1A6FC7` | Button hover                            |
| `color-accent-subtle` | `#EAF3FD` | Badge backgrounds, row selection tint   |

### Semantic

| Token                  | Hex       | Usage                       |
| ---------------------- | --------- | --------------------------- |
| `color-success`        | `#2D9A5F` | Status: contacted, enriched |
| `color-success-subtle` | `#E8F5EE` | Success badge background    |
| `color-warning`        | `#D4A017` | Status: pending review      |
| `color-warning-subtle` | `#FDF6E3` | Warning badge background    |
| `color-danger`         | `#D44C47` | Errors, destructive actions |
| `color-danger-subtle`  | `#FDECEA` | Error badge background      |
| `color-neutral`        | `#6B6B6B` | Status: new / unprocessed   |
| `color-neutral-subtle` | `#F1F1EF` | Neutral badge background    |

---

## 2. Typography

### Font Stack

```
Primary (UI):   Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
Monospace:      "JetBrains Mono", "Fira Code", "Courier New", monospace
```

### Scale

| Token       | Size | Weight | Line Height | Usage                       |
| ----------- | ---- | ------ | ----------- | --------------------------- |
| `text-3xl`  | 24px | 700    | 1.3         | Page titles                 |
| `text-2xl`  | 20px | 600    | 1.35        | Section headings            |
| `text-xl`   | 18px | 600    | 1.4         | Card titles, modal headings |
| `text-lg`   | 16px | 500    | 1.5         | Sub-headings, table headers |
| `text-base` | 14px | 400    | 1.6         | Body text, table cells      |
| `text-sm`   | 12px | 400    | 1.5         | Labels, metadata, badges    |
| `text-xs`   | 11px | 400    | 1.4         | Timestamps, helper text     |
| `text-mono` | 13px | 400    | 1.5         | Company ID, API keys, code  |

---

## 3. Spacing

8px base unit. All spacing values are multiples of 4px.

| Token      | Value | Usage                                   |
| ---------- | ----- | --------------------------------------- |
| `space-1`  | 4px   | Icon padding, tight gaps                |
| `space-2`  | 8px   | Inner padding (badges, chips)           |
| `space-3`  | 12px  | Table cell padding, compact form fields |
| `space-4`  | 16px  | Standard padding (cards, sections)      |
| `space-5`  | 20px  | Card padding on wider panels            |
| `space-6`  | 24px  | Section gaps, modal padding             |
| `space-8`  | 32px  | Large section separation                |
| `space-12` | 48px  | Page-level vertical rhythm              |

---

## 4. Border Radius

| Token         | Value  | Usage                           |
| ------------- | ------ | ------------------------------- |
| `radius-sm`   | 3px    | Badges, chips, tags             |
| `radius-md`   | 6px    | Buttons, inputs, cards          |
| `radius-lg`   | 10px   | Modals, dropdown panels         |
| `radius-full` | 9999px | Pill buttons, avatar indicators |

---

## 5. Shadows

| Token          | Value                             | Usage                   |
| -------------- | --------------------------------- | ----------------------- |
| `shadow-sm`    | `0 1px 2px rgba(0,0,0,0.06)`      | Cards at rest           |
| `shadow-md`    | `0 2px 8px rgba(0,0,0,0.08)`      | Dropdowns, popovers     |
| `shadow-lg`    | `0 8px 24px rgba(0,0,0,0.10)`     | Modals, floating panels |
| `shadow-focus` | `0 0 0 2px rgba(35,131,226,0.35)` | Input/button focus ring |

---

## 6. Component Conventions

### Buttons

| Variant   | Background        | Text                   | Border         | Usage                         |
| --------- | ----------------- | ---------------------- | -------------- | ----------------------------- |
| Primary   | `color-accent`    | `color-text-on-accent` | none           | Main CTA (Generate email)     |
| Secondary | `color-bg-subtle` | `color-text-primary`   | `color-border` | Non-destructive actions       |
| Ghost     | transparent       | `color-text-secondary` | none           | Toolbar actions, icon buttons |
| Danger    | `color-danger`    | `color-text-on-accent` | none           | Delete, discard               |

All buttons: `radius-md`, `text-base`, `space-2` vertical / `space-4` horizontal padding.

### Inputs

- Background: `color-bg`
- Border: `color-border` at rest → `color-accent` on focus
- Border radius: `radius-md`
- Text: `color-text-primary` / placeholder `color-text-tertiary`
- Focus shadow: `shadow-focus`

### Badges / Status Tags

Compact pill shape (`radius-sm`, `space-1` vertical / `space-2` horizontal padding, `text-sm`).

| Status    | Background             | Text color      |
| --------- | ---------------------- | --------------- |
| New       | `color-neutral-subtle` | `color-neutral` |
| Enriched  | `color-success-subtle` | `color-success` |
| Contacted | `color-accent-subtle`  | `color-accent`  |
| Pending   | `color-warning-subtle` | `color-warning` |
| Error     | `color-danger-subtle`  | `color-danger`  |

### Data Table

- Header row: `color-bg-subtle`, `text-sm`, `color-text-secondary`, uppercase + `letter-spacing: 0.04em`
- Row border: `color-border` (horizontal only)
- Row hover: `color-surface-hover`
- Selected row: `color-accent-subtle` background
- Cell padding: `space-3` vertical / `space-4` horizontal

---

## 7. Layout

- **Sidebar width:** 240px (fixed)
- **Content max-width:** 1100px (centered)
- **Page padding:** `space-8` horizontal on desktop, `space-4` on mobile
- **Section gap:** `space-6` between card groups

---

## 8. Motion

Minimal animation. Only functional transitions.

| Token            | Value                     | Usage                           |
| ---------------- | ------------------------- | ------------------------------- |
| `duration-fast`  | 100ms                     | Hover color changes             |
| `duration-base`  | 150ms                     | Button press, badge updates     |
| `duration-slow`  | 250ms                     | Modal open/close, sidebar slide |
| `easing-default` | `cubic-bezier(0.2,0,0,1)` | All transitions                 |

---

## 9. Iconography

- Library: **Lucide** (consistent stroke-based icons, matches Notion's style)
- Default size: 16px in UI / 20px in headings
- Stroke width: 1.5px
- Color: inherits from parent text token

---

## 10. CSS Custom Properties (Reference)

Paste into your global stylesheet or `app.css`:

```css
:root {
  /* Backgrounds */
  --color-bg: #ffffff;
  --color-bg-subtle: #f7f7f5;
  --color-surface: #ffffff;
  --color-surface-hover: #f1f1ef;
  --color-border: #e3e2e0;
  --color-border-strong: #cbcac8;

  /* Text */
  --color-text-primary: #1a1a1a;
  --color-text-secondary: #6b6b6b;
  --color-text-tertiary: #a0a0a0;
  --color-text-on-accent: #ffffff;

  /* Accent */
  --color-accent: #2383e2;
  --color-accent-hover: #1a6fc7;
  --color-accent-subtle: #eaf3fd;

  /* Semantic */
  --color-success: #2d9a5f;
  --color-success-subtle: #e8f5ee;
  --color-warning: #d4a017;
  --color-warning-subtle: #fdf6e3;
  --color-danger: #d44c47;
  --color-danger-subtle: #fdecea;
  --color-neutral: #6b6b6b;
  --color-neutral-subtle: #f1f1ef;

  /* Typography */
  --font-ui: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", "Courier New", monospace;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* Border Radius */
  --radius-sm: 3px;
  --radius-md: 6px;
  --radius-lg: 10px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.1);
  --shadow-focus: 0 0 0 2px rgba(35, 131, 226, 0.35);

  /* Motion */
  --duration-fast: 100ms;
  --duration-base: 150ms;
  --duration-slow: 250ms;
  --easing-default: cubic-bezier(0.2, 0, 0, 1);
}
```
