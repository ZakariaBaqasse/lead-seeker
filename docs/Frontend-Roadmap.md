# Lead Seeker — Frontend Implementation Roadmap

**Document Version:** 1.0
**Last Updated:** April 2026
**Project:** Lead Seeker (Personal Lead Generation Tool)
**Frontend Stack:** SvelteKit + Tailwind CSS + HTTP Basic Auth → FastAPI (localhost:8000)

---

## Overview

This roadmap breaks down the frontend implementation into 5 sequential phases, each with clear deliverables, dependencies, and acceptance criteria. The frontend is designed as a single-user, desktop-only SvelteKit application that proxies all API calls to a local FastAPI backend via SvelteKit server-side load functions and form actions.

**Key Architectural Decisions:**

- All lead data flows through SvelteKit server-side → HTTP Basic Auth enforcement
- Frontend never directly communicates with FastAPI; all requests go through SvelteKit routes
- API client helper (`lib/api.ts`) wraps fetch calls and adds `X-API-Key` header
- No WebSockets — polling on page load/refresh only
- Tailwind CSS for utility-first styling with custom theme extending the design system tokens
- CSS custom properties defined in `app.css` and mapped into `tailwind.config.js` for design system consistency

---

## Phase 1: Project Scaffolding & Foundation

**Objective:** Set up the SvelteKit project, establish authentication, design system, and baseline infrastructure for all subsequent development.

### 1.1 SvelteKit Project Initialization

**Description:**
Initialize a new SvelteKit project with Node adapter for self-hosting on a VPS. Configure package.json with required dependencies and deployment scripts.

**Tasks:**

- Create SvelteKit project via `npm create svelte@latest`
- Select **adapter-node** (for self-hosting)
- Install core dependencies: `svelte`, `sveltekit`, `node-adapter`
- Install and configure **Tailwind CSS v4** (`@tailwindcss/vite`):
  - Add `@import 'tailwindcss'` to `src/app.css`
  - Register Tailwind Vite plugin in `vite.config.ts`
- Install UI/utility dependencies:
  - `lucide-svelte` (icons)
  - `clsx` (conditional class composition)
  - `date-fns` (date/time formatting)
- Configure `svelte.config.js` with adapter-node and preprocess settings
- Add build/dev/preview scripts to `package.json`

**Files to Create/Modify:**

- `package.json` — Add dependencies, scripts
- `svelte.config.js` — Adapter configuration
- `vite.config.ts` — Tailwind Vite plugin registration
- `src/app.css` — Tailwind directives + CSS custom properties
- `.env.example` — Document environment variables
- `tsconfig.json` — Strict TypeScript settings

**Dependencies:** None (initial phase)

**Acceptance Criteria:**

- [ ] Project runs locally with `npm run dev`
- [ ] Tailwind CSS classes apply correctly (e.g., `class="p-4 text-sm"` works)
- [ ] TypeScript strict mode enabled
- [ ] All core dependencies installed
- [ ] `.env.example` documents `BACKEND_URL`, `APP_PASSWORD`, `API_SECRET_KEY`, `PORT`

---

### 1.2 Design System Implementation (Tailwind CSS)

**Description:**
Extend Tailwind CSS with custom theme tokens from `docs/Design-system.md`. Define CSS custom properties in `app.css` and map them into Tailwind's `@theme` directive so all design tokens are available as Tailwind utility classes.

**Tasks:**

- Configure `src/app.css`:
  - Add `@import 'tailwindcss'` at the top
  - Define CSS custom properties under `@theme` for:
    - Colors: `--color-bg`, `--color-bg-subtle`, `--color-accent`, `--color-danger`, etc.
    - Shadows: `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-focus`
  - Define remaining CSS custom properties in `:root` for values not directly mapped to Tailwind (transitions, etc.)
  - Import Inter font via `@import` from Google Fonts or self-host
  - Add base layer overrides for typography defaults (`body { @apply font-sans text-sm text-[--color-text-primary]; }`)
- Tailwind theme extension via `@theme` in `app.css` (Tailwind v4 CSS-first config):
  - **Colors:** Map all design system color tokens so they're usable as e.g., `bg-accent`, `text-danger`, `border-border`
  - **Font families:** `--font-sans: Inter, ...system fonts`, `--font-mono: JetBrains Mono, ...`
  - **Border radius:** `--radius-sm: 3px`, `--radius-md: 6px`, `--radius-lg: 10px`
  - **Shadows:** `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-focus`
- No separate `reset.css` needed — Tailwind's Preflight handles browser resets

**Files to Create/Modify:**

- `src/app.css` — Tailwind directives, `@theme` block, CSS custom properties, Inter font import, base layer overrides

**Example `app.css` structure:**

```css
@import "tailwindcss";

@theme {
  --color-bg: #ffffff;
  --color-bg-subtle: #f7f7f5;
  --color-surface: #ffffff;
  --color-surface-hover: #f1f1ef;
  --color-border: #e3e2e0;
  --color-border-strong: #cbcac8;
  --color-text-primary: #1a1a1a;
  --color-text-secondary: #6b6b6b;
  --color-text-tertiary: #a0a0a0;
  --color-text-on-accent: #ffffff;
  --color-accent: #2383e2;
  --color-accent-hover: #1a6fc7;
  --color-accent-subtle: #eaf3fd;
  --color-success: #2d9a5f;
  --color-success-subtle: #e8f5ee;
  --color-warning: #d4a017;
  --color-warning-subtle: #fdf6e3;
  --color-danger: #d44c47;
  --color-danger-subtle: #fdecea;
  --color-neutral: #6b6b6b;
  --color-neutral-subtle: #f1f1ef;

  --font-sans: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", "Courier New", monospace;

  --radius-sm: 3px;
  --radius-md: 6px;
  --radius-lg: 10px;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.1);
  --shadow-focus: 0 0 0 2px rgba(35, 131, 226, 0.35);
}

:root {
  --duration-fast: 100ms;
  --duration-base: 150ms;
  --duration-slow: 250ms;
  --easing-default: cubic-bezier(0.2, 0, 0, 1);
}
```

**Usage examples** (replaces raw CSS throughout components):

```svelte
<!-- Before (raw CSS) -->
<div style="background: var(--color-bg-subtle); padding: 16px; border-radius: 6px;">

<!-- After (Tailwind) -->
<div class="bg-bg-subtle p-4 rounded-md">
```

**Dependencies:** Phase 1.1 (Tailwind installed)

**Acceptance Criteria:**

- [ ] Tailwind utility classes using custom theme tokens work (e.g., `bg-accent`, `text-text-secondary`, `rounded-md`)
- [ ] Inter font loads without FOUT (`font-display: swap`)
- [ ] Preflight resets applied (consistent form elements, typography)
- [ ] All design system colors are available as Tailwind color utilities

---

### 1.3 Environment Configuration

**Description:**
Set up environment variable handling for development and production.

**Tasks:**

- Create `.env` file (gitignored) with:
  - `BACKEND_URL` (default: `http://localhost:8000`)
  - `APP_PASSWORD` (HTTP Basic Auth password)
  - `API_SECRET_KEY` (X-API-Key header for FastAPI)
  - `PORT` (SvelteKit dev server, default 5173)
- Create `.env.example` (committed) showing required variables
- Ensure production builds use correct env values from system/container

**Files to Create/Modify:**

- `.env` (gitignored)
- `.env.example` (committed)

**Dependencies:** Phase 1.1

**Acceptance Criteria:**

- [ ] Server-side env variables accessible in `+page.server.ts` via `$env/static/private`
- [ ] `.env.example` clearly documents all required variables

---

### 1.4 HTTP Basic Auth Hook

**Description:**
Implement authentication at the SvelteKit server level using `hooks.server.ts`. All requests are protected by HTTP Basic Auth.

**Tasks:**

- Create `src/hooks.server.ts` with:
  - Extract `Authorization` header from request
  - Decode Base64 Basic Auth credentials
  - Compare against `APP_PASSWORD` (from env)
  - Return 401 Unauthorized if credentials invalid
  - Call `resolve()` to proceed if valid

**Files to Create/Modify:**

- `src/hooks.server.ts`

**Dependencies:** Phase 1.3 (environment variables)

**Key Implementation Details:**

- Use `event.request.headers.get('authorization')` to extract header
- Decode Basic Auth: `atob()` for Base64 decoding
- Extract username and password from `username:password` format
- For single-user app, expect any username; validate password against `APP_PASSWORD`
- Use constant-time comparison to prevent timing attacks

**Acceptance Criteria:**

- [ ] Requests without valid Basic Auth header return 401
- [ ] Requests with correct credentials proceed to routes
- [ ] Invalid password returns 401 (no 403 distinction needed)
- [ ] No auth credentials logged or exposed in responses

---

### 1.5 API Client Helper

**Description:**
Create a utility module to wrap fetch calls to FastAPI, automatically adding authentication headers and handling errors.

**Tasks:**

- Create `src/lib/api.ts` with:
  - Fetch wrapper that automatically adds `X-API-Key` header
  - Handle JSON request/response serialization
  - Standard error handling (non-2xx status codes)
- Create TypeScript interfaces for API responses:
  - `Lead` (all fields from data model)
  - `LeadsResponse { items: Lead[], total: number }`
  - `StatsResponse { draft: number, sent: number, replied_won: number, replied_lost: number, archived: number }`
  - `PipelineStatus { last_run: string, leads_found: number, errors: string[] }`
  - `RegenerateEmailResponse { email_draft: string }`
- Export typed fetch helper functions:
  - `getLeads(filters)`, `getLead(id)`, `updateLead(id, data)`, `deleteLead(id)`
  - `regenerateEmail(id)`, `getStats()`, `getPipelineStatus()`, `runPipeline()`

**Files to Create/Modify:**

- `src/lib/api.ts`
- `src/lib/types.ts`

**Implementation Pattern:**

```
Only called from +page.server.ts / +page.server.ts load/actions
All requests sent to http://localhost:8000/api/*
X-API-Key header added server-side
Errors wrapped with user-friendly messages
```

**Dependencies:** Phase 1.3 (environment config for BACKEND_URL, API_SECRET_KEY)

**Acceptance Criteria:**

- [ ] All API functions are typed and exported
- [ ] X-API-Key header automatically added
- [ ] Errors handled gracefully (throw with message, not raw HTTP)
- [ ] Can be called from server-side load/action functions
- [ ] No direct browser calls to FastAPI (all proxied through SvelteKit)

---

### 1.6 Layout Shell

**Description:**
Create the main layout wrapper with sidebar navigation and content area.

**Tasks:**

- Create `src/routes/+layout.svelte` with:
  - 240px fixed sidebar on the left (`color-bg-subtle` background)
  - Main content area on the right (`color-bg` background)
  - Navigation items in sidebar:
    - "Leads" (link to `/`)
  - Active navigation highlight (accent color) based on current route
- Ensure sidebar is always visible

**Files to Create/Modify:**

- `src/routes/+layout.svelte`

**Design Details:**

- Sidebar: `w-60 bg-bg-subtle border-r border-border` (240px, subtle bg, right border)
- Main content: `flex-1 p-6 bg-bg` (flex-grow, padding, white bg)
- Nav links: `text-sm text-text-secondary hover:text-accent` (secondary by default, accent on hover/active)
- Active nav: `text-accent bg-accent-subtle rounded-md`
- Spacing: `space-y-1` between nav items, `p-4` inside sidebar

**Dependencies:** Phase 1.2 (design system)

**Acceptance Criteria:**

- [ ] Sidebar visible on all pages
- [ ] Active nav item highlighted correctly
- [ ] Layout does not break with different content sizes
- [ ] Design system spacing/colors applied consistently

---

### Phase 1 Summary

| Deliverable       | Description                                |
| ----------------- | ------------------------------------------ |
| SvelteKit project | Node adapter, all dependencies installed   |
| Design system     | Tailwind CSS with custom theme, Inter font |
| Auth hook         | HTTP Basic Auth protecting all routes      |
| API client        | Typed functions for all FastAPI endpoints  |
| Layout shell      | Sidebar navigation + content area          |

**Definition of Done:** Project runs locally, styles load, navigation works, 401 returned without credentials, API helper imports without errors.

---

## Phase 2: Core UI Components

**Objective:** Build reusable, styled components consistent with the design system. These components form the building blocks for all views.

### 2.1 Status Badge Component

**Description:**
Small pill-shaped badge displaying lead status. Used in lists and detail views.

**Tasks:**

- Create `src/lib/components/StatusBadge.svelte`:
  - Prop: `status` enum (`draft` | `sent` | `replied_won` | `replied_lost` | `archived`)
  - Display human-readable label ("Draft", "Sent", "Reply Won", "Reply Lost", "Archived")
  - Tailwind classes mapped by status:
    - **draft** → `bg-neutral-subtle text-neutral`
    - **sent** → `bg-accent-subtle text-accent`
    - **replied_won** → `bg-success-subtle text-success`
    - **replied_lost** → `bg-danger-subtle text-danger`
    - **archived** → `bg-neutral-subtle text-neutral`
  - Base classes: `inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium`

**Files to Create/Modify:**

- `src/lib/components/StatusBadge.svelte`

**Dependencies:** Phase 1.2 (design system)

**Acceptance Criteria:**

- [ ] All 5 status types display with correct colors
- [ ] Used in Phase 3 and 4 without additional styling

---

### 2.2 Button Component

**Description:**
Reusable button with multiple variants and states.

**Tasks:**

- Create `src/lib/components/Button.svelte`:
  - Props:
    - `variant`: `primary` | `secondary` | `ghost` | `danger` (default: `primary`)
    - `size`: `sm` | `md` | `lg` (default: `md`)
    - `disabled`: boolean
    - `loading`: boolean (show spinner, disable click)
    - `type`: `button` | `submit` | `reset` (default: `button`)
    - `href`: optional (renders as `<a>` for link-style buttons)
  - Tailwind classes per variant:
    - **primary** → `bg-accent text-text-on-accent hover:bg-accent-hover`
    - **secondary** → `bg-bg-subtle text-text-primary border border-border hover:bg-surface-hover`
    - **ghost** → `bg-transparent text-accent hover:bg-accent-subtle`
    - **danger** → `bg-danger text-text-on-accent hover:bg-danger/90`
  - Size mapping:
    - **sm** → `text-xs px-2 py-1`
    - **md** → `text-sm px-3 py-1.5`
    - **lg** → `text-base px-4 py-2`
  - Base classes: `inline-flex items-center justify-center rounded-md font-medium transition-colors duration-[--duration-fast] focus:outline-none focus:shadow-focus`
  - Disabled state: `opacity-50 cursor-not-allowed pointer-events-none`
  - Loading state: spinner icon, disabled interactions

**Files to Create/Modify:**

- `src/lib/components/Button.svelte`

**Dependencies:** Phase 1.2 (design system)

**Acceptance Criteria:**

- [ ] All 4 variants display correctly
- [ ] All 3 sizes apply correct padding/text scale
- [ ] Disabled state prevents interactions
- [ ] Loading state shows spinner and disables button
- [ ] Focus ring visible on keyboard navigation

---

### 2.3 Input & TextArea Components

**Description:**
Styled form inputs and textareas for lead detail editing.

**Tasks:**

- Create `src/lib/components/Input.svelte`:
  - Props: `value`, `placeholder`, `type` (text | email | number | date), `disabled`, `required`, `name`, `id`, `label`
  - Tailwind classes: `w-full bg-bg border border-border rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:shadow-focus focus:border-accent transition-colors duration-[--duration-fast]`
  - Error state (optional `error` prop): `border-danger` instead of `border-border`, helper text below in `text-danger text-xs`

- Create `src/lib/components/TextArea.svelte`:
  - Same styling as Input, but `<textarea>`
  - Resizable (vertical), minimum height ~100px

**Files to Create/Modify:**

- `src/lib/components/Input.svelte`
- `src/lib/components/TextArea.svelte`

**Dependencies:** Phase 1.2 (design system)

**Acceptance Criteria:**

- [ ] Inputs accept all specified types
- [ ] Focus state shows accent outline
- [ ] Placeholders visible and styled
- [ ] TextArea resizable and styled consistently

---

### 2.4 DataTable Component

**Description:**
Reusable table component for displaying lead lists with sorting and hover states.

**Tasks:**

- Create `src/lib/components/DataTable.svelte`:
  - Props:
    - `columns`: `{ key, label, sortable?, width?, render? }[]`
    - `rows`: array of row objects
    - `onSort`: `(key, direction) => void`
    - `onRowClick`: `(row) => void`
  - Header row: `bg-bg-subtle text-xs text-text-secondary uppercase tracking-wider`
  - Data rows: `border-b border-border hover:bg-surface-hover transition-colors duration-[--duration-fast]`
  - Sortable columns show chevron icons (Lucide `ChevronUp`/`ChevronDown`)
  - Cell padding: `px-4 py-3`
  - Custom `render` function in column definition for formatted cells
  - Empty state: show EmptyState component if no rows

**Files to Create/Modify:**

- `src/lib/components/DataTable.svelte`

**Dependencies:** Phase 1.2 (design system)

**Acceptance Criteria:**

- [ ] Columns and rows render correctly
- [ ] Hover state visible on rows
- [ ] Sorting indicators show on sortable columns
- [ ] Empty state displays when no rows

---

### 2.5 Modal / Dialog Component

**Description:**
Modal overlay for confirmations and forms.

**Tasks:**

- Create `src/lib/components/Modal.svelte`:
  - Props: `isOpen`, `onClose`, `title`, `size` (sm | md | lg)
  - Backdrop: `fixed inset-0 bg-black/20` (click to close)
  - Modal box: `bg-surface rounded-lg shadow-lg p-6`
  - Header: title + close button (Lucide `X` icon)
  - Body: `<slot>` for content
  - Size mapping: sm → 300px, md → 500px, lg → 700px max-width
  - Keyboard: Escape key closes modal
  - Animation: fade-in (100–150ms)

**Files to Create/Modify:**

- `src/lib/components/Modal.svelte`

**Dependencies:** Phase 1.2 (design system)

**Acceptance Criteria:**

- [ ] Modal opens/closes correctly based on `isOpen` prop
- [ ] Escape key closes modal
- [ ] Backdrop click closes modal
- [ ] Title and slot content display correctly

---

### 2.6 Toast / Notification System

**Description:**
Temporary notification messages for user feedback.

**Tasks:**

- Create `src/lib/stores/toastStore.ts`:
  - Svelte writable store to manage toast queue
  - Functions: `addToast(message, type, duration)`, `dismissToast(id)`
  - Auto-dismiss via `setTimeout()`

- Create `src/lib/components/Toast.svelte`:
  - Props: `message`, `type` (success | error | warning | info), `duration` (default 3000ms), `onClose`
  - Tailwind classes by type:
    - **success** → `bg-success-subtle text-success`
    - **error** → `bg-danger-subtle text-danger`
    - **warning** → `bg-warning-subtle text-warning`
    - **info** → `bg-accent-subtle text-accent`
  - Base classes: `flex items-center gap-3 p-4 rounded-md shadow-md`, close button
  - Animation: slide-in from top-right

- Create `src/lib/components/ToastContainer.svelte`:
  - Subscribes to toast store, renders toast stack
  - Fixed position: top-right corner

**Files to Create/Modify:**

- `src/lib/stores/toastStore.ts`
- `src/lib/components/Toast.svelte`
- `src/lib/components/ToastContainer.svelte`

**Dependencies:** Phase 1.2 (design system)

**Acceptance Criteria:**

- [ ] Toast displays with correct color/icon by type
- [ ] Auto-dismisses after specified duration
- [ ] Manual close button works
- [ ] Multiple toasts stack correctly

---

### 2.7 Empty State Component

**Description:**
Placeholder display when no data is available.

**Tasks:**

- Create `src/lib/components/EmptyState.svelte`:
  - Props: `title`, `description`, `icon` (optional Lucide icon), `action` (optional `{ label, onClick }`)
  - Tailwind: `flex flex-col items-center justify-center text-center py-12`, icon `w-12 h-12 text-text-tertiary mb-4`, title `text-xl font-semibold text-text-primary mb-2`, description `text-sm text-text-secondary mb-6`
  - Action button: Button component (primary variant)

**Files to Create/Modify:**

- `src/lib/components/EmptyState.svelte`

**Dependencies:** Phase 1.2, Phase 2.2 (Button)

**Acceptance Criteria:**

- [ ] Title and description display correctly
- [ ] Icon renders if provided
- [ ] Action button clickable and styled

---

### 2.8 Loading Spinner & Skeleton Loader

**Description:**
Visual feedback during data loading.

**Tasks:**

- Create `src/lib/components/LoadingSpinner.svelte`:
  - Props: `size` (sm: 16px, md: 24px, lg: 32px)
  - Color: `color-accent`, smooth rotation animation

- Create `src/lib/components/SkeletonLoader.svelte`:
  - Props: `count` (number of rows), `type` (row | card | line)
  - Animated placeholder rectangles with opacity pulse
  - Color: `color-border` at 50% opacity

**Files to Create/Modify:**

- `src/lib/components/LoadingSpinner.svelte`
- `src/lib/components/SkeletonLoader.svelte`

**Dependencies:** Phase 1.2 (design system)

**Acceptance Criteria:**

- [ ] Spinner animates smoothly at all sizes
- [ ] Skeleton loaders pulse and indicate loading state
- [ ] No jarring layout shift when content replaces skeleton

---

### Phase 2 Summary

| Deliverable    | Components                                 |
| -------------- | ------------------------------------------ |
| Status display | StatusBadge                                |
| Actions        | Button (4 variants)                        |
| Form inputs    | Input, TextArea                            |
| Data display   | DataTable                                  |
| Overlays       | Modal                                      |
| Feedback       | Toast, ToastContainer, toastStore          |
| States         | EmptyState, LoadingSpinner, SkeletonLoader |

**Definition of Done:** All components render without errors, all variants/props work as specified, styling uses design system tokens exclusively.

---

## Phase 3: Lead List View (Main Dashboard)

**Objective:** Build the primary interface for viewing, filtering, sorting, and managing leads. This is the landing page users see after login.

### 3.1 Server-Side Data Loading

**Description:**
Implement `src/routes/+page.server.ts` to fetch leads from FastAPI with filtering, sorting, and pagination.

**Tasks:**

- Create `src/routes/+page.server.ts`:
  - Export `load()` function:
    - Parse query params from URL: `status`, `region`, `from`, `to`, `page`, `limit`, `sort_by`, `sort_dir`
    - Validate/sanitize query params
    - Call `getLeads()`, `getStats()`, `getPipelineStatus()` in parallel
    - Return: `{ leads, total, page, limit, stats, pipelineStatus }`
  - Export `actions`:
    - `advance-status` — PATCH `/api/leads/{id}` to update status
    - `archive` — DELETE `/api/leads/{id}`
    - `run-pipeline` — POST `/api/pipeline/run`
  - Error handling: catch API errors, return user-friendly messages

**Files to Create/Modify:**

- `src/routes/+page.server.ts`

**API Endpoints Used:**

- `GET /api/leads?status=&region=&from=&to=&page=&limit=`
- `GET /api/stats`
- `GET /api/pipeline/status`
- `PATCH /api/leads/{id}`
- `DELETE /api/leads/{id}`
- `POST /api/pipeline/run`

**Acceptance Criteria:**

- [ ] `load()` fetches leads with current query params
- [ ] Stats and pipeline status fetched in parallel
- [ ] Form actions update lead status and archive correctly
- [ ] Errors handled gracefully (no blank page)

---

### 3.2 Lead List Display & Table

**Description:**
Render leads in a data table with all relevant columns.

**Tasks:**

- Update `src/routes/+page.svelte`:
  - Import and use DataTable component
  - Define columns:
    - Company Name (clickable → navigates to detail view)
    - Company Domain
    - Funding Amount (formatted)
    - Funding Date (formatted via `date-fns`)
    - CTO Name (or "—" if empty)
    - CTO Email (or "—" if empty)
    - Status (StatusBadge component via custom `render`)
    - Actions (View, Quick Status, Archive buttons)
  - Row click navigates to `/leads/{id}` via `goto()`
  - Display total lead count in header

**Files to Create/Modify:**

- `src/routes/+page.svelte`

**Dependencies:** Phase 2.4 (DataTable), Phase 2.2 (Button), Phase 2.1 (StatusBadge), Phase 3.1

**Acceptance Criteria:**

- [ ] All lead columns render with correct data
- [ ] View button navigates to lead detail page
- [ ] Status badge colors match status value
- [ ] Empty fields show "—" placeholder

---

### 3.3 Filter Controls

**Description:**
Filter bar above the table for filtering by status, region, and date range.

**Tasks:**

- Add filter bar section in `+page.svelte`:
  - Status dropdown: all status values (`draft`, `sent`, `replied_won`, `replied_lost`, `archived`)
  - Region dropdown: Europe, USA
  - Date range: two date inputs (from / to)
  - Reset button: clear all filters
- Filters update URL query params and reload data via `goto()` with updated search params

**Files to Create/Modify:**

- `src/routes/+page.svelte` — Filter section
- `src/routes/+page.server.ts` — Validate filter params

**Implementation Pattern:**

- Filters are form inputs that update URL: `?status=sent&region=Europe&from=2025-01-01`
- Use SvelteKit `goto()` to update URL without full reload

**Acceptance Criteria:**

- [ ] Status filter updates lead list correctly
- [ ] Region filter works
- [ ] Date range filtering works
- [ ] Reset button clears all filters
- [ ] URL query params reflect current filters (bookmarkable)

---

### 3.4 Sorting & Pagination

**Description:**
Column header sorting and pagination controls.

**Tasks:**

- Sorting:
  - Click column header to toggle sort direction (asc ↔ desc)
  - Sort indicator (chevron) on active column
  - Update URL: `?sort_by=company_name&sort_dir=asc`
  - Sortable columns: Company Name, Funding Date, Status, Created Date
  - Default sort: Created Date descending

- Pagination:
  - Previous/Next buttons below table
  - Page indicator: "Page 2 of 10"
  - Default: 20 leads per page
  - Total pages: `Math.ceil(total / limit)`
  - Disabled at boundaries

**Files to Create/Modify:**

- `src/routes/+page.svelte` — Sort indicators, pagination controls
- `src/routes/+page.server.ts` — Parse `page`, `limit`, `sort_by`, `sort_dir` params

**Acceptance Criteria:**

- [ ] Column header click sorts data and updates URL
- [ ] Sort direction toggles on repeated clicks
- [ ] Pagination controls display correct page info
- [ ] Next/Previous buttons respect page boundaries

---

### 3.5 Dashboard Stats Header

**Description:**
Summary statistics cards above the lead list showing counts by status.

**Tasks:**

- Create `src/lib/components/StatsHeader.svelte`:
  - Props: `stats` object `{ draft, sent, replied_won, replied_lost, archived, total }`
  - Render cards (one per status + total):
    - Each card: status name, count, subtle badge color
    - `color-surface` bg, `color-border` border, padding `space-4`, `radius-md`
  - Flex layout, `space-3` gap

- Add to `+page.svelte` above filter bar

**Files to Create/Modify:**

- `src/lib/components/StatsHeader.svelte`
- `src/routes/+page.svelte` — Import and render

**Dependencies:** Phase 1.2, Phase 3.1 (fetch stats)

**Acceptance Criteria:**

- [ ] Stats cards display with correct counts
- [ ] Colors match status badge colors
- [ ] Total count displayed

---

### 3.6 Pipeline Status & Manual Trigger

**Description:**
Show last pipeline run time and provide manual trigger button.

**Tasks:**

- Create `src/lib/components/PipelineStatus.svelte`:
  - Props: `pipelineStatus` object `{ last_run, leads_found, errors }`
  - Display: "Last run: 2 hours ago" (via `date-fns` `formatDistanceToNow()`)
  - "Leads found: 12" from last run
  - Error count if any

- Add "Run Discovery Now" button:
  - Triggers `run-pipeline` form action (POST `/api/pipeline/run`)
  - Loading state while running
  - Success toast: "Pipeline started"
  - Error toast on failure

**Files to Create/Modify:**

- `src/lib/components/PipelineStatus.svelte`
- `src/routes/+page.svelte` — Add component and trigger button
- `src/routes/+page.server.ts` — `run-pipeline` action

**Dependencies:** Phase 2.2 (Button), Phase 2.6 (Toast), Phase 3.1

**Acceptance Criteria:**

- [ ] Pipeline status displays with last run time
- [ ] Run button triggers discovery and shows loading state
- [ ] Success/error toast appears
- [ ] Page data refreshes to show updated status

---

### Phase 3 Summary

| Deliverable       | Description                                |
| ----------------- | ------------------------------------------ |
| Lead list         | DataTable with all columns, row navigation |
| Filters           | Status, region, date range dropdowns       |
| Sorting           | Column header sorting with URL persistence |
| Pagination        | Previous/Next with page indicator          |
| Stats header      | Count cards by status                      |
| Pipeline controls | Status indicator + manual trigger          |

**Definition of Done:** Page loads with leads from FastAPI, filters/sorting/pagination work, stats display, pipeline trigger works with feedback.

---

## Phase 4: Lead Detail View

**Objective:** Build a detailed view for individual leads. Allow editing lead fields, viewing/regenerating email drafts, and managing status lifecycle.

### 4.1 Server-Side Data Loading for Single Lead

**Description:**
Implement `src/routes/leads/[id]/+page.server.ts` to fetch a single lead and handle mutations.

**Tasks:**

- Create `src/routes/leads/[id]/+page.server.ts`:
  - Export `load({ params })`:
    - Call `getLead(params.id)`
    - Handle 404 if lead not found
    - Return `{ lead }`
  - Export `actions`:
    - `update-lead` — PATCH `/api/leads/{id}` with form data (cto_name, cto_email, linkedin_url, notes, status)
    - `regenerate-email` — POST `/api/leads/{id}/regenerate`, return new draft
    - `delete-lead` — DELETE `/api/leads/{id}`, redirect to `/`

**Files to Create/Modify:**

- `src/routes/leads/[id]/+page.server.ts`

**Key Implementation Details:**

- Use `event.request.formData()` to extract form fields
- Use `throw error(404)` if lead not found
- Use `throw redirect(303, '/')` after successful deletion

**Acceptance Criteria:**

- [ ] Load function fetches lead correctly
- [ ] Update action modifies lead and returns updated data
- [ ] Regenerate action returns new email draft
- [ ] Delete action redirects to lead list
- [ ] 404 error shown if lead ID invalid

---

### 4.2 Lead Detail Layout

**Description:**
Render lead information in a structured detail layout with all fields.

**Tasks:**

- Create `src/routes/leads/[id]/+page.svelte` with sections:

  **Header:**
  - Back navigation: `← Back to Leads` link
  - Company name (`text-3xl`, bold)
  - Status badge (StatusBadge component)

  **1. Company Information** (read-only)
  - Company Name, Domain (link to website), Description, Employee Count

  **2. Funding Information** (read-only)
  - Funding Amount, Date (formatted), Round, Region, Country

  **3. CTO Details** (editable)
  - CTO Name (Input), CTO Email (Input type="email"), LinkedIn URL (Input type="url")

  **4. News / Source** (read-only)
  - News Headline (link to `news_url`)

  **5. Notes** (editable)
  - Notes (TextArea)

  **6. Email Draft** (read-only + regenerate)
  - Email draft in monospace font, `color-bg-subtle` background
  - Copy-to-clipboard button
  - Regenerate button

  **Metadata sidebar:**
  - Created At, Updated At, Sent At (if applicable), Lead ID

**Files to Create/Modify:**

- `src/routes/leads/[id]/+page.svelte`

**Design Details:**

- Section spacing: `space-8` between sections
- Editable fields: Input/TextArea with labels above
- Email draft container: `color-bg-subtle` bg, `color-border` border, padding `space-4`, `radius-md`, `font-mono`

**Dependencies:** Phase 2.3 (Input, TextArea), Phase 2.1 (StatusBadge), Phase 4.1

**Acceptance Criteria:**

- [ ] All lead information displays correctly
- [ ] Editable fields are labeled clearly
- [ ] Company domain and news URL are clickable links
- [ ] Email draft displays in monospace font

---

### 4.3 Editable Fields & Form Submission

**Description:**
Wire editable form inputs to SvelteKit form actions for persisting changes.

**Tasks:**

- Wrap CTO fields and notes in `<form method="POST" action="?/update-lead">`
- Each input has `name` attribute matching API field names
- Add Save and Cancel buttons at bottom of form
- Use SvelteKit `use:enhance` for progressive enhancement:
  - Set `isSubmitting` flag for loading states
  - Show success toast on completion
  - Show error toast on failure
- Copy-to-clipboard for email draft:
  - Use `navigator.clipboard.writeText()` client-side
  - Show "Copied!" feedback

**Files to Create/Modify:**

- `src/routes/leads/[id]/+page.svelte` — Form wrapping, submit buttons
- `src/lib/utils/clipboard.ts` — Copy utility (optional)

**Implementation Pattern:**

```svelte
<form method="POST" action="?/update-lead" use:enhance>
  <Input name="cto_name" value={lead.cto_name} label="CTO Name" />
  <Input name="cto_email" type="email" value={lead.cto_email} label="CTO Email" />
  <Input name="linkedin_url" type="url" value={lead.linkedin_url} label="LinkedIn URL" />
  <TextArea name="notes" value={lead.notes} label="Notes" />
  <Button type="submit" loading={submitting}>Save Changes</Button>
  <Button variant="secondary" on:click={resetForm}>Cancel</Button>
</form>
```

**Dependencies:** Phase 2.2 (Button), Phase 2.3 (Input, TextArea), Phase 4.1, Phase 2.6 (Toast)

**Acceptance Criteria:**

- [ ] Form submits and updates lead on server
- [ ] Success toast shows after update
- [ ] Error handling if update fails
- [ ] Copy-to-clipboard works for email draft
- [ ] Cancel button resets form to last saved state

---

### 4.4 Email Draft Display & Regeneration

**Description:**
Display the AI-generated email draft with copy and regeneration capabilities.

**Tasks:**

- Email draft section:
  - Display in read-only container (monospace, `color-bg-subtle` bg, 1px `color-border`)
  - Full height (~300px) for readability
  - Copy-to-clipboard button (Lucide `Copy` icon)

- Regenerate button:
  - Button component (variant: secondary)
  - Triggers `regenerate-email` form action
  - Loading spinner while regenerating
  - Success: new draft replaces old one
  - Toast: "Email draft regenerated"

**Files to Create/Modify:**

- `src/routes/leads/[id]/+page.svelte` — Email section
- `src/routes/leads/[id]/+page.server.ts` — Ensure regenerate action works

**Acceptance Criteria:**

- [ ] Email draft displays in readable monospace font
- [ ] Copy-to-clipboard button works
- [ ] Regenerate triggers and shows new draft
- [ ] Loading state during regeneration
- [ ] Toast confirms success/failure

---

### 4.5 Status Lifecycle Controls

**Description:**
Controls to change lead status through its lifecycle: Draft → Sent → Replied (Won/Lost) → Archived.

**Tasks:**

- Add status change UI:
  - Dropdown/select for all status values
  - Submit button to save new status
  - Include in the update-lead form action (status field)
  - Toast: "Status updated to [new status]"

**Implementation Pattern:**

```svelte
<select name="status" value={lead.status}>
  <option value="draft">Draft</option>
  <option value="sent">Sent</option>
  <option value="replied_won">Reply - Won</option>
  <option value="replied_lost">Reply - Lost</option>
  <option value="archived">Archived</option>
</select>
```

**Files to Create/Modify:**

- `src/routes/leads/[id]/+page.svelte` — Status change UI

**Dependencies:** Phase 2.1 (StatusBadge), Phase 4.1

**Acceptance Criteria:**

- [ ] All 5 status values are selectable
- [ ] Form submission updates status correctly
- [ ] Toast confirms status change
- [ ] Status badge reflects new status

---

### 4.6 Delete / Archive Action

**Description:**
Delete or archive a lead with confirmation modal.

**Tasks:**

- Delete/Archive button:
  - Button component (variant: danger), icon: Lucide `Trash2`
  - Located at bottom of page

- Confirmation modal:
  - Modal component with warning message
  - Cancel (secondary) and Delete (danger) buttons
  - Submit triggers `delete-lead` form action
  - After deletion: redirect to `/`
  - Toast on lead list: "Lead archived successfully"

**Implementation Pattern:**

```svelte
<Button variant="danger" on:click={() => showDeleteModal = true}>Archive Lead</Button>

<Modal isOpen={showDeleteModal} title="Archive this lead?" onClose={() => showDeleteModal = false}>
  <p>This cannot be undone.</p>
  <form method="POST" action="?/delete-lead">
    <Button variant="danger" type="submit">Archive</Button>
    <Button variant="secondary" on:click={() => showDeleteModal = false}>Cancel</Button>
  </form>
</Modal>
```

**Files to Create/Modify:**

- `src/routes/leads/[id]/+page.svelte` — Delete button + modal

**Dependencies:** Phase 2.5 (Modal), Phase 2.2 (Button), Phase 4.1

**Acceptance Criteria:**

- [ ] Delete button opens confirmation modal
- [ ] Modal submission deletes lead and redirects to list
- [ ] Cancel closes modal without action
- [ ] Confirmation prevents accidental deletion

---

### Phase 4 Summary

| Deliverable      | Description                            |
| ---------------- | -------------------------------------- |
| Lead detail page | `/leads/[id]` with all lead fields     |
| Editable form    | CTO name/email, LinkedIn URL, notes    |
| Email draft      | Display, copy-to-clipboard, regenerate |
| Status controls  | Dropdown to change lifecycle status    |
| Archive action   | Delete with confirmation modal         |

**Definition of Done:** Page loads with correct lead data, all edit/regenerate/status/delete actions work, form submissions show loading/success/error states, navigation back to list works.

---

## Phase 5: Polish & Integration

**Objective:** Add refinements, error handling, loading states, and prepare for production deployment.

### 5.1 Error Handling & User Feedback

**Description:**
Comprehensive error handling for API failures, network errors.

**Tasks:**

- Server-side error handling in both `+page.server.ts` files:
  - Wrap API calls in try-catch
  - Return user-friendly error messages (don't expose API details)
  - Log errors server-side

- Client-side toast notifications:
  - Use `toastStore.addToast()` on error/success
  - Leverage SvelteKit `use:enhance` for form action feedback

- Specific error cases:
  - Lead not found (404) → Error banner with back button
  - Network timeout → Suggest retry
  - Empty lead list → EmptyState component

**Files to Create/Modify:**

- `src/routes/+page.server.ts` — Try-catch wrapping
- `src/routes/leads/[id]/+page.server.ts` — Error handling, 404 check
- `src/routes/+page.svelte` — Integrate toastStore
- `src/routes/leads/[id]/+page.svelte` — Error zone, toasts
- `src/routes/+error.svelte` — Custom SvelteKit error page

**Acceptance Criteria:**

- [ ] API errors caught and shown as toasts
- [ ] 404 leads show error page, not blank
- [ ] Network timeouts handled gracefully
- [ ] No unhandled promise rejections

---

### 5.2 Empty States

**Description:**
Appropriate messaging for all no-data scenarios.

**Tasks:**

- Lead list empty (no leads in DB):
  - EmptyState: "No leads found" + "Run Discovery Now" button
- Filters return 0 results:
  - EmptyState: "No results" + "Clear Filters" button
- Lead detail 404:
  - Error page: "Lead not found" + back button
- Missing optional fields (CTO name/email empty):
  - Display "—" or "Not provided"
- Email draft empty:
  - Display "Awaiting email generation"

**Files to Create/Modify:**

- `src/routes/+page.svelte` — Empty state conditionals
- `src/routes/leads/[id]/+page.svelte` — Handle missing fields
- `src/routes/+error.svelte` — Custom error page

**Acceptance Criteria:**

- [ ] Empty lead list shows EmptyState with action
- [ ] No-result filters show clear option
- [ ] Missing fields display gracefully
- [ ] 404 shows error page with navigation

---

### 5.6 Production Build & Deployment

**Description:**
Configure for production deployment on VPS via Dokploy.

**Tasks:**

- Test production build: `npm run build`
- Verify bundle size and no build errors

- Create `Dockerfile`:

  ```dockerfile
  FROM node:20-alpine
  WORKDIR /app
  COPY package*.json ./
  RUN npm ci --omit=dev
  COPY . .
  RUN npm run build
  EXPOSE 3000
  CMD ["node", "build"]
  ```

- Create `.dockerignore` (exclude node_modules, .git, etc.)

- Environment variables for production:
  - `BACKEND_URL` — FastAPI URL (e.g., `http://localhost:8000`)
  - `APP_PASSWORD` — HTTP Basic Auth password
  - `API_SECRET_KEY` — X-API-Key for FastAPI
  - `PORT` — SvelteKit server port (default 3000)

- Optional: health check endpoint at `/health` returning `{ status: 'ok' }`

**Files to Create/Modify:**

- `frontend/Dockerfile`
- `frontend/.dockerignore`
- `.env.example` — Complete variable list

**Acceptance Criteria:**

- [ ] Production build completes without errors
- [ ] Docker image builds successfully
- [ ] Container runs and serves frontend on port 3000
- [ ] All environment variables documented

---

### 5.7 QA Checklist

Manual testing before launch:

- [ ] User can authenticate with correct password (Basic Auth)
- [ ] Lead list loads and displays leads
- [ ] Filters (status, region, date) work correctly
- [ ] Sorting by column header works
- [ ] Pagination next/previous buttons work
- [ ] Stats header counts match lead count
- [ ] Click row navigates to lead detail page
- [ ] Edit CTO name/email/LinkedIn and save
- [ ] Email draft displays and copy-to-clipboard works
- [ ] Regenerate email draft shows new content
- [ ] Change lead status and verify update
- [ ] Archive lead and verify redirect + toast
- [ ] Run discovery pipeline and verify status updates
- [ ] Error handling: invalid lead ID, network error
- [ ] Keyboard navigation (Tab, Escape) works
- [ ] No console errors in Chrome, Firefox

---

### Phase 5 Summary

| Deliverable    | Description                              |
| -------------- | ---------------------------------------- |
| Error handling | Try-catch, toasts, error pages           |
| Loading states | Skeletons, spinners, form states         |
| Accessibility  | ARIA labels, focus management            |
| Empty states   | EmptyState component for all scenarios   |
| Visual polish  | Spacing, typography, color consistency   |
| Deployment     | Dockerfile, env config, production build |
| QA             | Manual testing checklist                 |

**Definition of Done:** All pages render without errors, all user flows tested, production build succeeds, Docker image runs, application ready for deployment.

---

## File Inventory

Complete list of files created across all phases:

```
frontend/
├── Dockerfile
├── .dockerignore
├── .env
├── .env.example
├── package.json
├── svelte.config.js
├── tsconfig.json
├── src/
│   ├── app.css
│   ├── app.html
│   ├── hooks.server.ts
│   ├── app.css
│   ├── lib/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   ├── stores/
│   │   │   └── toastStore.ts
│   │   ├── utils/
│   │   │   └── clipboard.ts
│   │   └── components/
│   │       ├── StatusBadge.svelte
│   │       ├── Button.svelte
│   │       ├── Input.svelte
│   │       ├── TextArea.svelte
│   │       ├── DataTable.svelte
│   │       ├── Modal.svelte
│   │       ├── Toast.svelte
│   │       ├── ToastContainer.svelte
│   │       ├── EmptyState.svelte
│   │       ├── LoadingSpinner.svelte
│   │       ├── SkeletonLoader.svelte
│   │       ├── StatsHeader.svelte
│   │       └── PipelineStatus.svelte
│   └── routes/
│       ├── +layout.svelte
│       ├── +page.svelte
│       ├── +page.server.ts
│       ├── +error.svelte
│       └── leads/
│           └── [id]/
│               ├── +page.svelte
│               └── +page.server.ts
```

---

## Key Architectural Principles

1. **Server-First Data Loading:** All data fetches through SvelteKit `load()` functions — no direct browser-to-FastAPI calls.
2. **Form Actions for Mutations:** Lead edits, status updates, and deletions use SvelteKit form actions with POST requests.
3. **API Client Abstraction:** `src/lib/api.ts` wraps all fetch calls with `X-API-Key` header — single point of change.
4. **Design System Consistency:** All styling uses Tailwind utility classes with custom theme tokens — no inline styles or magic numbers.
5. **Component Reusability:** UI components are generic and reused across pages.
6. **Progressive Enhancement:** `use:enhance` on forms for loading states without full page reloads.
7. **No Real-Time Features:** Polling on load/refresh only — no WebSockets.
8. **Single-User Premise:** No session management — HTTP Basic Auth only.

---

## Dependency Installation (Phase 1)

```bash
npx sv create frontend
cd frontend

bun install tailwindcss @tailwindcss/vite
bun install lucide-svelte clsx date-fns
```
