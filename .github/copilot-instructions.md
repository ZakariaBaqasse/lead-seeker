# Lead Seeker — Copilot Instructions

## What This Project Is

Lead Seeker is a personal, single-user lead generation tool. It auto-discovers recently funded GenAI startups (EU/USA, 10–50 employees), drafts personalized cold outreach emails via Mistral API, and provides a dashboard to manage outreach status. There is no authentication system — HTTP Basic Auth is handled entirely at the SvelteKit layer; FastAPI is only accessible from localhost.

## Repository Layout

```
lead-seeker/
├── backend/          # FastAPI app (Python 3.12, uv)
│   ├── app/          # Application source (to be built per roadmap)
│   ├── alembic/      # DB migrations
│   ├── config/
│   │   └── profile.yaml   # Freelancer profile — injected into every email draft
│   └── pyproject.toml
├── frontend/         # SvelteKit app (Bun, Svelte 5, TailwindCSS v4)
├── docs/             # PRD, TDD, Backend/Frontend roadmaps — primary design reference
└── docker-compose.yaml
```

## Commands

### Backend (run from `backend/`)

```bash
# Install dependencies
uv sync

# Run dev server
uv run uvicorn app.main:app --reload

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_leads.py

# Run a single test by name
uv run pytest tests/test_leads.py::test_filter_by_status -v

# Apply DB migrations
uv run alembic upgrade head

# Create a new migration
uv run alembic revision --autogenerate -m "description"
```

### Frontend (run from `frontend/`)

```bash
bun install
bun run dev          # dev server on :5173
bun run build
bun run check        # svelte-check type checking
bun run check:watch
```

### Full Stack (from repo root)

```bash
docker compose up             # start all services
docker compose watch          # with hot-reload sync
```

Services: `db` (Postgres :54320), `api` (FastAPI :8080→8000), `frontend` (SvelteKit :5173).

## Architecture

### Request Flow

```
Browser → Traefik (HTTPS) → SvelteKit (Basic Auth enforcement in hooks.server.ts)
  → Server-side load functions (+page.server.ts) → FastAPI (X-API-Key, localhost only)
  → PostgreSQL
```

**FastAPI is never called from the browser.** SvelteKit server-side functions are the sole callers and inject `X-API-Key` from the server `.env`. This keeps secrets out of the browser entirely.

### Backend App Structure (target layout per `docs/Technical-Design-Doc.md §4`)

```
app/
├── main.py               # FastAPI app + APScheduler lifespan setup
├── config.py             # Pydantic Settings (reads .env)
├── auth.py               # X-API-Key dependency (global on app)
├── db.py                 # Async SQLAlchemy engine + get_db dependency
├── profile.py            # profile.yaml loader with lru_cache(maxsize=1)
├── api/
│   ├── leads.py          # CRUD: GET/PATCH/DELETE /api/leads, POST /api/leads/{id}/regenerate
│   ├── pipeline.py       # POST /api/pipeline/run, GET /api/pipeline/status, POST /api/profile/reload
│   └── stats.py          # GET /api/stats
├── models/
│   ├── lead.py           # SQLAlchemy Lead model
│   └── pipeline_run.py   # SQLAlchemy PipelineRun model
├── schemas/
│   ├── lead.py           # Pydantic: LeadOut, LeadUpdate, LeadListResponse, LeadStatus, ExtractionResult
│   └── pipeline.py       # Pydantic: PipelineRunOut, StatsOut
└── pipeline/
    ├── runner.py          # Orchestrates full pipeline via asyncio.gather()
    ├── extractor.py       # Mistral call #1: raw article → ExtractionResult JSON
    ├── filter.py          # Sector/region/employee/funding-recency filter
    ├── drafter.py         # Mistral call #2: lead context + profile.yaml → email draft
    └── sources/
        ├── __init__.py    # RawArticle dataclass + dedupe_by_url()
        ├── google_news.py
        ├── gnews.py
        ├── yc_directory.py
        └── rss_feeds.py
```

### Daily Pipeline Flow

Each source fetcher runs concurrently via `asyncio.gather()` → URL dedup → LLM extraction (Mistral call #1, JSON mode) → filter → DB dedup → store → email draft (Mistral call #2). Failures per article are logged and skipped; the pipeline never aborts.

## Key Conventions

### Authentication
- FastAPI uses a global `verify_api_key` dependency (`APIKeyHeader("X-API-Key")`). Apply it to the FastAPI app instance, not per-router.
- Frontend `.env` contains `APP_PASSWORD` (for Basic Auth) and `BACKEND_URL`.
- Backend `.env` contains `DATABASE_URL`, `MISTRAL_API_KEY`, `API_SECRET_KEY`, `PIPELINE_SCHEDULE_HOUR`, `PIPELINE_SCHEDULE_MINUTE`.

### Database
- Async SQLAlchemy with `asyncpg`. All DB operations must use `async with` sessions via the `get_db` dependency.
- `company_domain` has a partial unique index (`WHERE company_domain IS NOT NULL`). Dedup falls back to case-insensitive `company_name` match when domain is null.
- `status` enum values (enforced at schema layer): `draft`, `sent`, `replied_won`, `replied_lost`, `archived`.
- When status is updated to `'sent'`, auto-set `sent_at = now()`.

### Mistral API
- **Two separate calls per lead** — extraction and email drafting are never combined into one prompt.
- Extraction call uses `response_format={"type": "json_object"}`.
- All Mistral calls wrapped with `tenacity` retry: 3 attempts, exponential backoff.
- JSON parse failure after retries → log error, return `None`, discard article (never abort pipeline).

### Profile Loading
- `get_profile()` in `app/profile.py` uses `@lru_cache(maxsize=1)`. Reload via `POST /api/profile/reload` calls `get_profile.cache_clear()`.
- Validate YAML at load time — required keys: `name`, `title`, `pitch`, `projects` (list), `skills` (list). Raise descriptive `ValueError` on missing/malformed.

### Source Fetchers
- Each fetcher returns `list[RawArticle]`. On any failure (timeout, network, parse error), log a warning and return `[]` — never raise.
- All HTTP calls use `httpx.AsyncClient(timeout=30.0)`.
- GNews is capped at 80 req/day (of 100 free); track with an in-memory counter that resets at UTC 00:00.

### Frontend
- SvelteKit is configured for **Svelte 5 runes mode** for all project files (`runes: true` in `svelte.config.js`).
- Uses `@sveltejs/adapter-node` for production.
- TailwindCSS v4 (via `@tailwindcss/vite` plugin).
- Basic Auth enforcement goes in `src/hooks.server.ts`. All FastAPI calls go in `+page.server.ts` / `src/lib/api.ts` (server-side only).

### CORS
- CORS is **not needed in production** — SvelteKit calls FastAPI server-side over localhost.
- For local dev without SvelteKit (standalone API testing only), add dev-only CORS allowing `http://localhost:3000`. Never expose to public internet.

### Out of Scope (don't add these)
- No Redis, Celery, or task queues (APScheduler is embedded in the FastAPI process)
- No email sending (user sends manually from clipboard)
- No WebSockets or real-time updates (dashboard polls on load)
- No resume parsing or file upload (profile comes from `config/profile.yaml` only)
- No multi-tenancy, JWT, OAuth, or user table

## Design Reference

The `docs/` directory is the authoritative design reference:
- `docs/PRD.md` — product requirements, data model, status lifecycle
- `docs/Technical-Design-Doc.md` — architecture, DB schema, API spec, pipeline implementation notes, prompt templates
- `docs/Backend-Roadmap.md` — phased implementation plan with per-file acceptance criteria
- `docs/Frontend-Roadmap.md` — frontend implementation plan
