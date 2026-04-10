# Plan: Lead Seeker Frontend Implementation

## Overview

Implement the full frontend for Lead Seeker — a personal lead generation dashboard for discovering funded GenAI startups and managing outreach email drafts.

The frontend is a **SvelteKit 5** (runes mode) app using:
- **Bun** as package manager
- **TailwindCSS v4** (CSS-first config via `@theme`)
- **adapter-node** for VPS deployment
- **HTTP Basic Auth** enforced at `hooks.server.ts`
- All FastAPI calls proxied server-side (never from the browser)

A base SvelteKit project exists at `frontend/` with adapter-node, TailwindCSS v4, and Svelte 5 runes mode already configured. Missing: design tokens, auth hook, API client, components, and pages.

### Goals

- Implement all 5 roadmap phases from `docs/Frontend-Roadmap.md`
- Match the design system in `docs/Design-system.md`
- Follow the architecture described in `docs/Technical-Design-Doc.md`
- No browser calls to FastAPI — all requests through SvelteKit server routes
- Clean, atomic commits per task

### Success Criteria

- [ ] Basic Auth hook protects all routes (401 without credentials)
- [ ] Lead list view loads data, filters, sorts, paginates
- [ ] Lead detail view shows all fields, allows editing CTO info/notes
- [ ] Email draft viewable, copyable, and regeneratable
- [ ] Status lifecycle controls work
- [ ] Archive/delete with confirmation modal works
- [ ] Dashboard stats and pipeline trigger work
- [ ] Production build succeeds (`bun run build`)

### Out of Scope

- Backend implementation (already done or being done separately)
- Mobile/responsive layout (desktop-only per PRD)
- Email sending (user copies draft manually)
- Tests beyond `bun run check` (svelte-check)

---

## Technical Approach

SvelteKit server-side load functions fetch data from FastAPI and inject it as page props. Form actions handle mutations. The browser only ever sees the rendered HTML and makes SvelteKit-native form submissions.

### Architecture

```
Browser → SvelteKit hooks.server.ts (Basic Auth)
  → +page.server.ts (load + actions) → lib/api.ts → FastAPI
  → +page.svelte (render)
```

### Key Files

- `src/hooks.server.ts` — Basic Auth enforcement
- `src/lib/api.ts` — Typed fetch wrapper with X-API-Key
- `src/lib/types.ts` — TypeScript interfaces for all API responses
- `src/routes/+layout.svelte` — Sidebar + content shell
- `src/routes/+page.svelte` — Lead list view
- `src/routes/+page.server.ts` — Load leads, stats, pipeline status
- `src/routes/leads/[id]/+page.svelte` — Lead detail view
- `src/routes/leads/[id]/+page.server.ts` — Load single lead, mutations
- `src/lib/components/` — Reusable components (Button, Input, Modal, etc.)
- `src/lib/stores/toastStore.ts` — Toast notification store

### Component Map

| Component | Description |
|-----------|-------------|
| `StatusBadge` | Pill badge for lead status |
| `Button` | 4 variants (primary/secondary/ghost/danger) |
| `Input` | Styled form input |
| `TextArea` | Styled textarea |
| `DataTable` | Sortable, clickable rows |
| `Modal` | Overlay dialog |
| `Toast` + `ToastContainer` | Notification system |
| `EmptyState` | No-data placeholder |
| `LoadingSpinner` | Animated spinner |
| `SkeletonLoader` | Loading skeleton rows |
| `StatsHeader` | Status count cards |
| `PipelineStatus` | Last run info + trigger |

---

## Implementation Phases

### Phase 1: Foundation

1. Install missing dependencies: `lucide-svelte`, `clsx`, `date-fns` (files: `package.json`)
2. Design system: update `src/app.css` with `@theme` tokens, Inter font, base layer (files: `src/app.css`)
3. Environment config: `.env`, `.env.example` (files: `.env.example`, `.env`)
4. HTTP Basic Auth hook (files: `src/hooks.server.ts`)
5. API client + TypeScript types (files: `src/lib/api.ts`, `src/lib/types.ts`)
6. Layout shell with sidebar navigation (files: `src/routes/+layout.svelte`, update `src/routes/layout.css` → `src/app.css`)
7. App globals and app.html (files: `src/app.html`)

### Phase 2: Core UI Components

1. `StatusBadge.svelte` — pill badge by status
2. `Button.svelte` — 4 variants, 3 sizes, loading state
3. `Input.svelte` + `TextArea.svelte` — styled form inputs
4. `DataTable.svelte` — sortable rows, empty state slot
5. `Modal.svelte` — overlay, Escape key, backdrop click
6. `toastStore.ts` + `Toast.svelte` + `ToastContainer.svelte` — notification system
7. `EmptyState.svelte` — no-data placeholder
8. `LoadingSpinner.svelte` + `SkeletonLoader.svelte` — loading states
9. `StatsHeader.svelte` — stats count cards
10. `PipelineStatus.svelte` — last run info

### Phase 3: Lead List View

1. `+page.server.ts` — load (leads + stats + pipeline status) + form actions (advance-status, archive, run-pipeline)
2. `+page.svelte` — DataTable with all columns, navigation to detail
3. Filter bar: status/region/date dropdowns, reset button (URL-driven)
4. Sorting: column headers update URL, sort indicators
5. Pagination: previous/next, page indicator

### Phase 4: Lead Detail View

1. `leads/[id]/+page.server.ts` — load single lead + update/regenerate/delete actions
2. `leads/[id]/+page.svelte` — full detail layout with all sections
3. Editable fields: CTO name/email, LinkedIn URL, notes — form with `use:enhance`
4. Email draft display: monospace, copy-to-clipboard, regenerate
5. Status lifecycle dropdown + save
6. Delete/archive with confirmation modal

### Phase 5: Polish & Integration

1. Error handling: try-catch in server files, toast notifications
2. Empty states: all no-data scenarios
3. `+error.svelte` — custom SvelteKit error page
4. `Dockerfile` + `.dockerignore` for production build
5. Final `bun run check` + `bun run build` validation

---

## Testing Strategy

- `bun run check` (svelte-check) runs after each phase
- `bun run build` validates production build in Phase 5
- Manual QA against the checklist in `docs/Frontend-Roadmap.md §5.7`

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Svelte 5 runes syntax differences from Svelte 4 | Medium | Use `$props()`, `$state()`, `$derived()` throughout; no `export let` |
| TailwindCSS v4 `@theme` custom tokens not resolving | Medium | Follow exact pattern from roadmap doc; test with a simple class |
| Basic Auth browser prompt varies by browser | Low | Acceptable for single-user tool |
| FastAPI not running during dev | Low | Mock data or stub functions where needed; note in handoff |

## Assumptions

- Backend API endpoints follow the spec in `docs/Technical-Design-Doc.md §7`
- `BACKEND_URL` defaults to `http://localhost:8000` in development
- No app.css exists yet (layout.css in routes/ needs to become src/app.css)
- `bun` is used instead of `npm` for all install/run commands
- Svelte 5 event syntax: `onclick` not `on:click` (runes mode)

---

## Final Status

**Complete** — All 5 phases implemented, committed, and validated.

- `bun run check`: 0 errors, 0 warnings ✅
- `bun run build`: Success (159 SSR + 470 client modules) ✅
- 23 commits across `implement-frontend` branch
- All todos marked done in session DB
