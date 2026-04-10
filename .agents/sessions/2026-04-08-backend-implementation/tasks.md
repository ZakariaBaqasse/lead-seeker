# Tasks: Lead Seeker Backend Implementation

## Phase 1: Scaffolding & Configuration

- [ ] 1.1 — Create `app/` directory structure with all `__init__.py` files (`backend/app/`, `backend/app/api/`, `backend/app/models/`, `backend/app/schemas/`, `backend/app/pipeline/`, `backend/app/pipeline/sources/`)
- [ ] 1.2 — Implement `app/config.py` — Pydantic Settings with DATABASE_URL, MISTRAL_API_KEY, API_SECRET_KEY, GNEWS_API_KEY, PIPELINE_SCHEDULE_HOUR (default 6), PIPELINE_SCHEDULE_MINUTE (default 0) (`backend/app/config.py`, `backend/.env.example`)
- [ ] 1.3 — Implement `app/auth.py` — `verify_api_key` dependency using `APIKeyHeader("X-API-Key")` (`backend/app/auth.py`)
- [ ] 1.4 — Implement `app/main.py` — FastAPI app with lifespan context manager, placeholder router includes, dev-only CORS for localhost:3000 (`backend/app/main.py`)
- [ ] 1.5 — Add `GET /api/health` returning `{ status: "ok" }`, protected by `verify_api_key` — used to verify auth wiring is correct before any CRUD routes exist (`backend/app/main.py`)
- [ ] 1.6 — Remove old `backend/main.py` placeholder and update `Dockerfile` if needed

## Phase 2: Database Layer

- [ ] 2.1 — Implement `app/db.py` — async SQLAlchemy engine (asyncpg), async session factory, `get_db` dependency yielding `AsyncSession` (`backend/app/db.py`)
- [ ] 2.2 — Implement `app/models/lead.py` — Lead model with all columns, indexes (status, created_at DESC, partial unique on company_domain WHERE NOT NULL) (`backend/app/models/lead.py`)
- [ ] 2.3 — Implement `app/models/pipeline_run.py` — PipelineRun model (id, started_at, completed_at, articles_fetched, articles_processed, leads_created, errors JSON, status) (`backend/app/models/pipeline_run.py`)
- [ ] 2.4 — Initialize Alembic with async config, update `env.py` for async engine (`backend/alembic/`)
- [ ] 2.5 — Generate and validate initial migration; run `alembic upgrade head` to confirm tables are created (`backend/alembic/versions/`)
- [ ] 2.6 — Implement Pydantic schemas: `LeadStatus`, `LeadOut`, `LeadUpdate`, `LeadListResponse`, `LeadListParams`, `ExtractionResult` in `app/schemas/lead.py`; `PipelineRunOut`, `StatsOut` in `app/schemas/pipeline.py`

## Phase 3: REST API — Leads CRUD & Stats

- [ ] 3.1 — Implement `GET /api/leads` with filter params (status, region, from_date, to_date, page, limit), pagination, ordered by created_at DESC (`backend/app/api/leads.py`)
- [ ] 3.2 — Implement `GET /api/leads/{id}` — single lead with 404 handling (`backend/app/api/leads.py`)
- [ ] 3.3 — Implement `PATCH /api/leads/{id}` — partial update, auto-set sent_at when status→sent, 404 handling (`backend/app/api/leads.py`)
- [ ] 3.4 — Implement `DELETE /api/leads/{id}` — hard delete returning 204, 404 handling (`backend/app/api/leads.py`)
- [ ] 3.5 — Implement `GET /api/stats` — counts by status with zero-fill for all 5 statuses (`backend/app/api/stats.py`)
- [ ] 3.6 — Register leads and stats routers in `main.py` with `/api` prefix (`backend/app/main.py`)

## Phase 4: Freelancer Profile Loader

- [ ] 4.1 — Create `config/profile.yaml` — template with placeholder values (`backend/config/profile.yaml`)
- [ ] 4.2 — Implement `app/profile.py` — `get_profile()` with `@lru_cache(maxsize=1)`, YAML validation (required keys: name, title, pitch, projects list, skills list) (`backend/app/profile.py`)
- [ ] 4.3 — Implement `POST /api/profile/reload` in `app/api/pipeline.py` — clears cache, reloads, returns validation result (`backend/app/api/pipeline.py`)

## Phase 5: Pipeline — Source Fetchers

- [ ] 5.1 — Implement `pipeline/sources/__init__.py` — `RawArticle` dataclass (headline, body_snippet, url, source_name) + `dedupe_by_url()` (`backend/app/pipeline/sources/__init__.py`)
- [ ] 5.2 — Implement `pipeline/sources/google_news.py` — async Google News RSS fetcher with targeted queries, 30s timeout, return [] on any error (`backend/app/pipeline/sources/google_news.py`)
- [ ] 5.3 — Implement `pipeline/sources/gnews.py` — GNews API fetcher, in-memory 80/day counter with UTC reset, 30s timeout, return [] on error (`backend/app/pipeline/sources/gnews.py`)
- [ ] 5.4 — Implement `pipeline/sources/yc_directory.py` — YC JSON endpoint fetcher, filter AI/recent, 30s timeout, return [] on error (`backend/app/pipeline/sources/yc_directory.py`)
- [ ] 5.5 — Implement `pipeline/sources/rss_feeds.py` — TechCrunch, Sifted, EU-Startups RSS fetcher, 30s timeout, return [] on error (`backend/app/pipeline/sources/rss_feeds.py`)

## Phase 6: Pipeline — LLM Extraction & Filtering

- [ ] 6.1 — Implement `pipeline/extractor.py` — Mistral extraction call with JSON mode, exact prompt from roadmap, tenacity 3-attempt retry, return None on failure (`backend/app/pipeline/extractor.py`)
- [ ] 6.2 — Implement `pipeline/filter.py` — `filter_lead(extraction)` checking sector/region/employees/funding_date/required fields; `async is_duplicate(session, extraction)` checking domain then name (`backend/app/pipeline/filter.py`)

## Phase 7: Pipeline — Email Drafting

- [ ] 7.1 — Implement `pipeline/drafter.py` — Mistral email draft call (free text), exact prompt from roadmap, tenacity retry, failure→return None (lead stored with NULL draft) (`backend/app/pipeline/drafter.py`)
- [ ] 7.2 — Implement `POST /api/leads/{id}/regenerate` in leads router — fetch lead, call drafter, update email_draft + updated_at, return `{email_draft: string}` (`backend/app/api/leads.py`)

## Phase 8: Pipeline — Runner & Orchestration

- [ ] 8.1 — Implement `pipeline/runner.py` — `async run_pipeline(session)` orchestrating: create pipeline_run, asyncio.gather all sources, URL dedup, sequential article processing (extract→filter→dedup→store→draft), update pipeline_run on completion. **Wrap full body in `try/finally`** — pipeline_run must be updated to `status='failed'` and `completed_at=now()` on any unhandled exception (`backend/app/pipeline/runner.py`)
- [ ] 8.2 — Implement `POST /api/pipeline/run` (**synchronous** — awaits `run_pipeline()` before returning; callers must set HTTP timeout ≥ 120s; do NOT use BackgroundTasks) and `GET /api/pipeline/status` (last pipeline_run record) in `app/api/pipeline.py` (`backend/app/api/pipeline.py`)
- [ ] 8.3 — Register pipeline router in `main.py` with `/api` prefix (`backend/app/main.py`)

## Phase 9: APScheduler Integration

- [ ] 9.1 — Set up `AsyncIOScheduler` in FastAPI lifespan, add cron job for `run_pipeline` at configured hour/minute (default 06:00 UTC) (`backend/app/main.py`)
- [ ] 9.2 — Wrap scheduled job in try/except; update pipeline_run status to 'failed' on unhandled exception; log full traceback (`backend/app/main.py`)

## Phase 10: Testing & Hardening

- [ ] 10.1 — Set up `tests/conftest.py` — async test client, DB session override with SQLite (`backend/tests/conftest.py`)
- [ ] 10.2 — Implement `tests/test_filter.py` — unit tests for all filter criteria (sector, region, employee count, funding date, required fields) and dedup (domain match, name match, no match) (`backend/tests/test_filter.py`)
- [ ] 10.3 — Implement `tests/test_api.py` — CRUD endpoints, auth 403, query param validation 422, stats counts, regenerate endpoint (`backend/tests/test_api.py`)
- [ ] 10.4 — Implement `tests/test_pipeline.py` — integration test with mocked Mistral + mocked source fetchers, verify leads created, pipeline_run updated, dedup/error handling (`backend/tests/test_pipeline.py`)
- [ ] 10.5 — Set up structured logging (`backend/app/logging_config.py`, `backend/app/main.py`)
- [ ] 10.6 — Defensive review: verify timeouts, DB session cleanup, no secrets in logs, pipeline_run updated on crash via try/finally
