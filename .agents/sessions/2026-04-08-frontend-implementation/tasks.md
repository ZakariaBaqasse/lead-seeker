# Tasks: Lead Seeker Frontend Implementation

## Phase 1: Foundation

- [ ] 1.1 — Install missing dependencies: `lucide-svelte`, `clsx`, `date-fns` (`package.json`, `bun.lockb`)
- [ ] 1.2 — Design system: update `src/app.css` with `@theme` tokens, Inter font import, base layer (`src/app.css`, remove `src/routes/layout.css`)
- [ ] 1.3 — Environment config: create `.env.example` with all required variables; create `.env` template (`frontend/.env.example`, `frontend/.env`)
- [ ] 1.4 — HTTP Basic Auth hook: enforce Basic Auth on all requests (`src/hooks.server.ts`)
- [ ] 1.5 — API client + TypeScript types: typed fetch wrapper with X-API-Key header, all response interfaces (`src/lib/api.ts`, `src/lib/types.ts`)
- [ ] 1.6 — Layout shell: sidebar (240px) with navigation + main content area (`src/routes/+layout.svelte`)
- [ ] 1.7 — Update `src/app.html` to set page title and ensure app.css is loaded

## Phase 2: Core UI Components

- [ ] 2.1 — `StatusBadge.svelte`: pill badge with color by status (draft/sent/replied_won/replied_lost/archived) (`src/lib/components/StatusBadge.svelte`)
- [ ] 2.2 — `Button.svelte`: 4 variants (primary/secondary/ghost/danger), 3 sizes, disabled + loading states (`src/lib/components/Button.svelte`)
- [ ] 2.3 — `Input.svelte`: styled input with label, error state; `TextArea.svelte`: same but textarea (`src/lib/components/Input.svelte`, `src/lib/components/TextArea.svelte`)
- [ ] 2.4 — `DataTable.svelte`: sortable headers, hover rows, clickable rows, empty state slot, custom cell render (`src/lib/components/DataTable.svelte`)
- [ ] 2.5 — `Modal.svelte`: overlay backdrop, Escape key close, title + slot + close button (`src/lib/components/Modal.svelte`)
- [ ] 2.6 — Toast system: `toastStore.ts` (writable store, add/dismiss), `Toast.svelte`, `ToastContainer.svelte` (fixed top-right) (`src/lib/stores/toastStore.ts`, `src/lib/components/Toast.svelte`, `src/lib/components/ToastContainer.svelte`)
- [ ] 2.7 — `EmptyState.svelte`: centered icon + title + description + optional action button (`src/lib/components/EmptyState.svelte`)
- [ ] 2.8 — `LoadingSpinner.svelte` (animated spinner, 3 sizes) + `SkeletonLoader.svelte` (pulse rows) (`src/lib/components/LoadingSpinner.svelte`, `src/lib/components/SkeletonLoader.svelte`)
- [ ] 2.9 — `StatsHeader.svelte`: stats count cards with status colors (`src/lib/components/StatsHeader.svelte`)
- [ ] 2.10 — `PipelineStatus.svelte`: last run time (date-fns), leads found, error count, run button (`src/lib/components/PipelineStatus.svelte`)

## Phase 3: Lead List View

- [ ] 3.1 — `+page.server.ts`: load (getLeads + getStats + getPipelineStatus in parallel) + actions (advance-status, archive, run-pipeline) (`src/routes/+page.server.ts`)
- [ ] 3.2 — `+page.svelte` base: DataTable with columns (company, domain, funding, date, CTO, status, actions), row click → detail (`src/routes/+page.svelte`)
- [ ] 3.3 — Filter bar: status/region/date dropdowns + reset button; URL-driven state with goto() (`src/routes/+page.svelte`)
- [ ] 3.4 — Sorting: click headers, toggle direction, update URL params, sort indicators (`src/routes/+page.svelte`, `src/routes/+page.server.ts`)
- [ ] 3.5 — Pagination: previous/next buttons, page indicator, disabled at boundaries (`src/routes/+page.svelte`)

## Phase 4: Lead Detail View

- [ ] 4.1 — `leads/[id]/+page.server.ts`: load single lead + actions (update-lead, regenerate-email, delete-lead with redirect) (`src/routes/leads/[id]/+page.server.ts`)
- [ ] 4.2 — `leads/[id]/+page.svelte`: full layout — header (back link, company name, status), company info, funding info, CTO fields form, news source, notes, email draft (`src/routes/leads/[id]/+page.svelte`)
- [ ] 4.3 — Editable form: wrap CTO/notes in form with use:enhance, save/cancel buttons, success/error toasts (`src/routes/leads/[id]/+page.svelte`)
- [ ] 4.4 — Email draft: read-only display (monospace), copy-to-clipboard button, regenerate button with loading state (`src/routes/leads/[id]/+page.svelte`)
- [ ] 4.5 — Status dropdown: all 5 status values, submit updates status, toast confirmation (`src/routes/leads/[id]/+page.svelte`)
- [ ] 4.6 — Delete/archive: danger button → confirmation Modal → delete action → redirect to `/` (`src/routes/leads/[id]/+page.svelte`)

## Phase 5: Polish & Integration

- [ ] 5.1 — Error handling: try-catch in all server files, toast integration in page components, `+error.svelte` page (`src/routes/+error.svelte`, `src/routes/+page.server.ts`, `src/routes/leads/[id]/+page.server.ts`)
- [ ] 5.2 — Empty states: no leads, no filter results, missing optional fields, empty email draft (`src/routes/+page.svelte`, `src/routes/leads/[id]/+page.svelte`)
- [ ] 5.3 — `Dockerfile` (node:20-alpine, bun install, build, CMD node build) + `.dockerignore` (`frontend/Dockerfile`, `frontend/.dockerignore`)
- [ ] 5.4 — Final validation: `bun run check` passes, `bun run build` succeeds
