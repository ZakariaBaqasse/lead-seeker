# Plan: Lead Seeker Backend Implementation

## Overview

Implement the complete FastAPI backend for Lead Seeker — a personal, single-user lead generation tool that auto-discovers recently funded GenAI startups, drafts personalized cold outreach emails via Mistral API, and exposes a REST API for the SvelteKit dashboard.

The backend resides in `backend/`. All dependencies are already installed via `uv`. The `app/` folder needs to be created from scratch following the structure in TDD §4.

### Goals

- Implement all backend functionality described in PRD and TDD
- Deliver an API-complete backend that the SvelteKit frontend can consume
- Ensure the daily pipeline runs reliably with proper error handling and observability

### Success Criteria

- [ ] All REST API endpoints from TDD §7 operational
- [ ] Daily pipeline discovers, extracts, filters, deduplicates, stores, and drafts emails
- [ ] API key authentication enforced on all endpoints
- [ ] Pipeline run metadata tracked in `pipeline_runs` table
- [ ] `profile.yaml` loaded, cached, and reloadable
- [ ] Test coverage on all critical paths (filtering, dedup, API, pipeline)

### Out of Scope

- Frontend (SvelteKit)
- Deployment/Dokploy configuration
- Phase 2 paid enrichment (Crunchbase, Apollo.io)
- Email sending functionality
- Mobile layout, multi-tenancy, WebSockets

## Technical Approach

FastAPI application with:
- **AsyncIO** throughout (async SQLAlchemy, async httpx, async APScheduler)
- **PostgreSQL** via asyncpg driver (SQLAlchemy async engine)
- **Pydantic Settings** for config management from `.env`
- **APScheduler** embedded in FastAPI lifespan for daily pipeline cron
- **Mistral API** for both extraction (JSON mode) and email drafting (free text)
- **tenacity** for retry logic on all Mistral calls
- **httpx.AsyncClient(timeout=30.0)** for all external HTTP calls

### Key Design Decisions

- FastAPI auth: global `verify_api_key` dependency on the app instance (not per-router)
- CORS: dev-only, localhost:3000 only, never production
- Two separate Mistral calls per lead (extraction + drafting) — never combined
- Pipeline failures per article are logged and skipped, pipeline never aborts
- `company_domain` partial unique index (WHERE NOT NULL); fallback dedup by case-insensitive `company_name`
- Profile loaded once at startup via `@lru_cache(maxsize=1)`; reload via `POST /api/profile/reload`
- `status='sent'` auto-sets `sent_at=now()`

### Target File Structure

```
backend/
├── app/
│   ├── main.py               # FastAPI app + APScheduler lifespan
│   ├── config.py             # Pydantic Settings
│   ├── auth.py               # X-API-Key dependency
│   ├── db.py                 # Async SQLAlchemy engine + get_db
│   ├── profile.py            # profile.yaml loader with lru_cache
│   ├── api/
│   │   ├── leads.py          # CRUD + regenerate
│   │   ├── pipeline.py       # run, status, profile reload
│   │   └── stats.py          # stats
│   ├── models/
│   │   ├── lead.py           # SQLAlchemy Lead model
│   │   └── pipeline_run.py   # SQLAlchemy PipelineRun model
│   ├── schemas/
│   │   ├── lead.py           # Pydantic schemas
│   │   └── pipeline.py       # Pydantic schemas
│   └── pipeline/
│       ├── runner.py         # Full pipeline orchestrator
│       ├── extractor.py      # Mistral extraction call
│       ├── filter.py         # Filtering + DB dedup
│       ├── drafter.py        # Mistral email draft
│       └── sources/
│           ├── __init__.py   # RawArticle + dedupe_by_url
│           ├── google_news.py
│           ├── gnews.py
│           ├── yc_directory.py
│           └── rss_feeds.py
├── alembic/                  # DB migrations
├── config/
│   └── profile.yaml          # Freelancer profile template
├── tests/
│   ├── conftest.py
│   ├── test_filter.py
│   ├── test_api.py
│   └── test_pipeline.py
├── .env.example
└── pyproject.toml            # Already has all deps
```

## Implementation Phases

### Phase 1: Scaffolding & Configuration

1. Create `app/` directory structure with all `__init__.py` files (files: `backend/app/`, subdirs)
2. Implement `app/config.py` — Pydantic Settings reading from `.env` (files: `backend/app/config.py`, `backend/.env.example`)
3. Implement `app/auth.py` — `verify_api_key` dependency using `APIKeyHeader` (files: `backend/app/auth.py`)
4. Implement `app/main.py` — FastAPI app with lifespan, placeholder routers, dev CORS (files: `backend/app/main.py`)
5. Add `GET /api/health` returning `{ status: "ok" }`, protected by `verify_api_key` — used to verify auth wiring before CRUD routes exist
6. Delete old `backend/main.py` placeholder

### Phase 2: Database Layer

1. Implement `app/db.py` — async SQLAlchemy engine, session factory, `get_db` dependency (files: `backend/app/db.py`)
2. Implement `app/models/lead.py` — Lead SQLAlchemy model with all columns and indexes (files: `backend/app/models/lead.py`)
3. Implement `app/models/pipeline_run.py` — PipelineRun model (files: `backend/app/models/pipeline_run.py`)
4. Configure Alembic for async — `alembic init`, update `env.py` for async engine (files: `backend/alembic/`)
5. Create initial migration and run `alembic upgrade head` to validate (files: `backend/alembic/versions/`)
6. Implement Pydantic schemas: `app/schemas/lead.py`, `app/schemas/pipeline.py` (files: `backend/app/schemas/`)

### Phase 3: REST API — Leads CRUD & Stats

1. Implement `app/api/leads.py` — GET list with filters/pagination, GET detail, PATCH, DELETE (files: `backend/app/api/leads.py`)
2. Implement `app/api/stats.py` — GET /api/stats (files: `backend/app/api/stats.py`)
3. Register leads and stats routers in `main.py` (files: `backend/app/main.py`)

### Phase 4: Freelancer Profile Loader

1. Create `config/profile.yaml` — template with placeholder values (files: `backend/config/profile.yaml`)
2. Implement `app/profile.py` — `get_profile()` with `lru_cache`, YAML validation (files: `backend/app/profile.py`)
3. Implement `POST /api/profile/reload` in `app/api/pipeline.py` (stub file for pipeline routes) (files: `backend/app/api/pipeline.py`)

### Phase 5: Pipeline — Source Fetchers

1. Implement `pipeline/sources/__init__.py` — `RawArticle` dataclass + `dedupe_by_url()` (files: `backend/app/pipeline/sources/__init__.py`)
2. Implement `pipeline/sources/google_news.py` — async Google News RSS fetcher (files: `backend/app/pipeline/sources/google_news.py`)
3. Implement `pipeline/sources/gnews.py` — GNews API fetcher with 80/day rate cap (files: `backend/app/pipeline/sources/gnews.py`)
4. Implement `pipeline/sources/yc_directory.py` — YC JSON endpoint fetcher (files: `backend/app/pipeline/sources/yc_directory.py`)
5. Implement `pipeline/sources/rss_feeds.py` — TechCrunch/Sifted/EU-Startups RSS (files: `backend/app/pipeline/sources/rss_feeds.py`)

### Phase 6: Pipeline — LLM Extraction & Filtering

1. Implement `pipeline/extractor.py` — Mistral extraction call with JSON mode, tenacity retries (files: `backend/app/pipeline/extractor.py`)
2. Implement `pipeline/filter.py` — `filter_lead()` and `async is_duplicate()` (files: `backend/app/pipeline/filter.py`)

### Phase 7: Pipeline — Email Drafting

1. Implement `pipeline/drafter.py` — Mistral email draft call, tenacity retries, failure→NULL (files: `backend/app/pipeline/drafter.py`)
2. Implement `POST /api/leads/{id}/regenerate` in `app/api/leads.py` (files: `backend/app/api/leads.py`)

### Phase 8: Pipeline — Runner & Orchestration

1. Implement `pipeline/runner.py` — full pipeline orchestrator with asyncio.gather, pipeline_runs tracking. Wrap full pipeline body in `try/finally` — `pipeline_runs` must be updated to `status='failed'` and `completed_at=now()` on any unhandled exception (files: `backend/app/pipeline/runner.py`)
2. Implement `POST /api/pipeline/run` (**synchronous** — awaits `run_pipeline()` before returning; expected duration ≤ 2 min; callers must set HTTP timeout ≥ 120s; do NOT use BackgroundTasks) and `GET /api/pipeline/status` (last pipeline_run record) in `app/api/pipeline.py` (files: `backend/app/api/pipeline.py`)
3. Register pipeline router in `main.py` (files: `backend/app/main.py`)

### Phase 9: APScheduler Integration

1. Set up `AsyncIOScheduler` in FastAPI lifespan with configurable cron schedule (files: `backend/app/main.py`)
2. Wrap scheduled job in try/except; update `pipeline_runs` on failure (files: `backend/app/main.py`)

### Phase 10: Testing & Hardening

1. Set up `tests/conftest.py` — async test client, in-memory SQLite or test DB fixtures (files: `backend/tests/conftest.py`)
2. Implement `tests/test_filter.py` — unit tests for all filter criteria and dedup logic (files: `backend/tests/test_filter.py`)
3. Implement `tests/test_api.py` — API tests: CRUD, auth, validation, stats, regenerate (files: `backend/tests/test_api.py`)
4. Implement `tests/test_pipeline.py` — integration test with mocked Mistral + sources (files: `backend/tests/test_pipeline.py`)
5. Set up structured logging in `app/main.py` + `app/logging_config.py` (files: `backend/app/logging_config.py`)
6. Defensive review: timeouts, DB session cleanup, no secrets in logs (all files)

## Testing Strategy

- **Unit**: Filter logic, dedup, profile loading, schema validation — fast, no I/O
- **API**: All endpoints via httpx TestClient — mock DB where needed
- **Integration**: Full pipeline with mocked Mistral and mocked source fetchers
- **Auth**: Missing/wrong API key → 403 on every endpoint
- **Edge cases**: Empty pipeline results, draft failure → lead stored with NULL draft, GNews counter at limit

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Async SQLAlchemy complexity | Medium | Use well-documented patterns; test in Phase 2 immediately |
| Mistral API unavailable during dev | Low | Tenacity handles retries; tests use mocks |
| RSS feed format changes | Low | try/except per fetcher; return [] on any error |
| GNews rate limit exceeded | Low | Hard cap at 80/day; counter resets UTC 00:00 |
| APScheduler silent failure | Medium | `pipeline_runs` table tracks every run |

## Open Questions

_(resolved — converted to assumptions below)_

## Assumptions

1. The `app/` folder does not yet exist — will be created from scratch
2. The old `backend/main.py` placeholder will be removed (app entry point moves to `backend/app/main.py`)
3. Tests will use `pytest-asyncio` and `httpx.AsyncClient` with FastAPI's `AsyncClient`; in-memory SQLite (`aiosqlite`) will be used for DB tests to avoid needing a real Postgres in CI. **Note:** SQLite does not enforce partial unique indexes (`WHERE company_domain IS NOT NULL`), so `is_duplicate()` must be implemented as an explicit SELECT-before-insert (never relying on constraint violation), which will be verified against real Postgres manually
4. `alembic` will be initialized with `--template async` or manually configured for async operation
5. GNews API key is stored in `.env` as `GNEWS_API_KEY` (in addition to the keys already spec'd)
6. The `profile.yaml` file is loaded relative to the `backend/` working directory

## Final Status

_(Updated after implementation completes)_
