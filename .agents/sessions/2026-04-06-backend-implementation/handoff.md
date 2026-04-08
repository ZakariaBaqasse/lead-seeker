# Handoff

<!-- Append a new phase section after each phase completes. -->

## Phase 1: Scaffolding & Config — COMPLETE

### Commits
- `e355768` — `✨ feat: add config & env loading (task 1.2)`
- `6ba1261` — `✨ feat: add FastAPI app entry point with stub routers (task 1.3)`
- `36ce3a7` — `✨ feat: add X-API-Key auth dependency (task 1.4)`

### Files Created
- `backend/app/config.py` — Pydantic `Settings` class loading from `.env`
- `backend/.env` — local dev env vars (not committed to main, safe for local use)
- `backend/.env.example` — placeholder template
- `backend/app/__init__.py` — package marker
- `backend/app/main.py` — FastAPI app with lifespan stub, CORS, `/health`, stub router includes
- `backend/app/auth.py` — `verify_api_key` dependency (X-API-Key header, 403 on mismatch)
- `backend/app/api/__init__.py`, `leads.py`, `stats.py`, `pipeline.py` — stub routers with auth dep
- `backend/app/models/__init__.py`, `backend/app/schemas/__init__.py` — empty package markers

### Verification
- `uv run python -c "from app.main import app; print('App loaded OK')"` → **OK**
- `uvicorn app.main:app` started and `GET /health` returned `{"status":"ok"}` with HTTP 200

### Design Decisions
- Auth applied **per-router** (not global app dep) so `/health` stays unauthenticated without special exclusion logic
- CORS enabled only when `DATABASE_URL` contains `localhost` (dev detection)
- `settings = Settings()` instantiated at module level; `.env` read via pydantic-settings

## Phase 2: Database Layer — COMPLETE

### Commits
- `713c070` — `✨ feat: add async database session and Base (task 2.1)`
- `68329dd` — `✨ feat: add Lead and PipelineRun SQLAlchemy models (tasks 2.2-2.3)`
- `df74901` — `✨ feat: add Alembic async config and initial migration (task 2.4)`
- `0fa2204` — `✨ feat: add Pydantic schemas for leads and pipeline (task 2.5)`

### Files Created
- `backend/app/db.py` — async SQLAlchemy engine, `AsyncSessionLocal`, `Base`, `get_db` dependency
- `backend/app/models/lead.py` — `Lead` ORM model with all columns; indexes on `status` and `created_at`
- `backend/app/models/pipeline_run.py` — `PipelineRun` ORM model
- `backend/app/schemas/lead.py` — `LeadOut`, `LeadUpdate`, `LeadListResponse`, `LeadListParams`, `LeadStatus`
- `backend/app/schemas/pipeline.py` — `PipelineRunOut`, `StatsOut`, `ExtractionResult`
- `backend/alembic/` — Alembic setup with async `env.py`
- `backend/alembic/versions/b0b20fd4e0c2_create_leads_and_pipeline_runs_tables.py` — full initial migration

### Verification
- `uv run python -c "from app.models.lead import Lead; ..."` → **All imports OK**
- Migration syntax verified via `importlib.util` import → **OK**

### Design Decisions
- DB not accessible in this environment → migration created manually (not `--autogenerate`) with same schema as models
- Partial unique index on `company_domain WHERE NOT NULL` added manually in migration using `postgresql_where=text(...)`
- `__pycache__` committed (not gitignored at worktree level); safe to ignore retroactively

## Phase 3: REST API — Leads CRUD & Stats — COMPLETE

### Commits
- `196bf09` — `✨ feat: implement leads CRUD endpoints (tasks 3.1-3.4)`
- `c6abd39` — `✨ feat: implement stats endpoint (task 3.5)`

### Files Modified
- `backend/app/api/leads.py` — full implementation replacing stub:
  - `GET /api/leads` with `LeadFilters` class-based dependency (status, region, from_date, to_date, page, limit)
  - `GET /api/leads/{lead_id}` — 404 on missing
  - `PATCH /api/leads/{lead_id}` — partial update; auto-sets `sent_at` when status→sent
  - `DELETE /api/leads/{lead_id}` — 204 response
  - `# TODO: Phase 7 - regenerate endpoint` stub comment
- `backend/app/api/stats.py` — full implementation replacing stub:
  - `GET /api/stats` — counts per status via GROUP BY

### Task 3.6 Note
`main.py` already had correct `app.include_router(leads.router)`, `app.include_router(stats.router)`, `app.include_router(pipeline.router)` — no changes needed.

### Verification
- `uv run python -c "from app.api.leads import router; from app.api.stats import router as sr; print('Routers import OK')"` → **OK**
- `uv run python -c "from app.main import app; print('App import OK')"` → **OK**

### Design Decisions
- Stubs already had `/api/` prefix in router, so `include_router` in main.py uses no additional prefix — consistent with existing pattern
- `LeadFilters` uses class-based `Depends()` pattern (not Pydantic model) to work with FastAPI query param binding
- `flush()` + `refresh()` used in PATCH to persist and reload ORM state without committing (session commit handled by `get_db` context manager)

## Phase 4: Freelancer Profile Loader ✅

**Completed by**: Phase 4 worker
**Commits**: dd9c972, 19acec4, 2cd75a8

### Files Created/Modified
- `backend/app/profile.py` — `get_profile()` with `lru_cache(maxsize=1)` + `_validate_profile()` validation
- `backend/config/profile.yaml` — sample profile template
- `backend/app/api/pipeline.py` — replaced stub with `pipeline_router` + `profile_router`; `POST /reload` endpoint on `profile_router`

### Notes for Phase 8 / Post-Phase-3 fixup
`app/main.py` must include both routers:
```python
from app.api.pipeline import pipeline_router, profile_router
app.include_router(pipeline_router, prefix="/api")
app.include_router(profile_router, prefix="/api")
```
The old stub `router` export no longer exists — any import of `from app.api.pipeline import router` will break and must be updated.

## Phase 2: Database Layer

**Status:** complete (with reviewer fixes applied)

**Tasks completed:**
- 2.1: async SQLAlchemy engine + `get_db` dependency with commit/rollback handling
- 2.2: `Lead` model — 21 columns, ORM indexes; partial unique on `company_domain` handled in migration
- 2.3: `PipelineRun` model — 8 fields, JSON errors column
- 2.4: Alembic async env.py (asyncio.run pattern), hand-written initial migration
- 2.5: Pydantic schemas — LeadOut, LeadUpdate, LeadListResponse, LeadListParams, LeadStatus, StatsOut, ExtractionResult, PipelineRunOut

**Files changed:**
- `backend/app/db.py` — new
- `backend/app/models/lead.py` — new
- `backend/app/models/pipeline_run.py` — new
- `backend/alembic/env.py` — new (async pattern)
- `backend/alembic/versions/b0b20fd4e0c2_create_leads_and_pipeline_runs_tables.py` — new
- `backend/app/schemas/lead.py` — new
- `backend/app/schemas/pipeline.py` — new

**Commits:**
- `713c070` — db.py
- `68329dd` — models
- `df74901` — alembic
- `0fa2204` — schemas
- `7ffc1dd` — reviewer fixes (server_default now(), DESC index, router wiring)

**Decisions & context:**
- `employee_count_estimate` in ExtractionResult → `employee_count` in Lead model. Phase 6 extractor must rename when building Lead rows.
- Partial unique index expressed via `postgresql_where` in migration, not model `__table_args__`
- DB not accessible during dev; migration was hand-written (not autogenerate)

## Phase 3: REST API — Leads CRUD & Stats

**Status:** complete

**Tasks completed:**
- 3.1–3.4: `GET /api/leads` (filtered+paginated), `GET /api/leads/{id}`, `PATCH /api/leads/{id}` (auto-sets sent_at), `DELETE /api/leads/{id}`
- 3.5: `GET /api/stats` — per-status counts, zero-filled
- 3.6: Router registration in main.py (leads/stats had /api prefix in router, pipeline/profile added without duplicate)

**Files changed:**
- `backend/app/api/leads.py` — full CRUD
- `backend/app/api/stats.py` — stats endpoint
- `backend/app/main.py` — fixed imports and router includes

**Commits:** `196bf09`, `c6abd39`

**Decisions & context:**
- `LeadFilters` class-based Depends used for query params (FastAPI pattern, not Pydantic model)
- PATCH uses `model_dump(exclude_unset=True)` to update only provided fields

## Phase 4: Freelancer Profile Loader

**Status:** complete

**Tasks completed:**
- 4.1: `get_profile()` with `lru_cache(maxsize=1)` + `_validate_profile()` — fail-fast on malformed YAML
- 4.2: `config/profile.yaml` template with placeholder values
- 4.3: `POST /api/profile/reload` in `pipeline.py` — clears cache, reloads, returns validation result

**Files changed:**
- `backend/app/profile.py` — new
- `backend/config/profile.yaml` — new
- `backend/app/api/pipeline.py` — replaced stub with `pipeline_router` + `profile_router`

**Commits:** `dd9c972`, `19acec4`, `2cd75a8`

**Decisions & context:**
- Two routers in pipeline.py: `pipeline_router` (prefix /pipeline) and `profile_router` (prefix /profile)
- Phase 8 must add POST /run and GET /status to `pipeline_router` and include both in main.py (already done in main.py fix commit 7ffc1dd)

## Phase 5: Pipeline Source Fetchers ✅

**Commits**: 0235289, 80cd7b9, c332028, 1f6bc8c, 111646c

### Files Created
- `backend/app/pipeline/__init__.py` — empty package init
- `backend/app/pipeline/sources/__init__.py` — `RawArticle` dataclass + `dedupe_by_url()`
- `backend/app/pipeline/sources/google_news.py` — async Google News RSS fetcher
- `backend/app/pipeline/sources/gnews.py` — async GNews API fetcher with 80/day rate cap
- `backend/app/pipeline/sources/yc_directory.py` — async YC Directory fetcher
- `backend/app/pipeline/sources/rss_feeds.py` — concurrent RSS feeds fetcher (TechCrunch/Sifted/EU-Startups)

### Files Modified
- `backend/app/config.py` — added `GNEWS_API_KEY: Optional[str] = None`

### Design Decisions
- `GNEWS_API_KEY` is optional; `fetch_gnews()` returns `[]` immediately if not set
- GNews rate counter uses `threading.Lock` (thread-safe) with auto-reset on date change
- YC Directory filters by `RECENT_BATCHES` set (S24/W24/S25/W25/W26) and AI keywords in `one_liner`/`long_description`
- RSS feeds use `asyncio.gather()` for concurrent fetching; individual feed failure is isolated
- All fetchers return `[]` on any exception (no propagation)

---

## Phase 6 — LLM Extraction & Filtering

**Commits**: f76bd0a, c6f9a7b

### Files Created
- `backend/app/pipeline/extractor.py` — Mistral LLM extraction with tenacity retries
- `backend/app/pipeline/filter.py` — Lead filtering and DB deduplication logic

### Design Decisions
- Mistral SDK v2+ (`mistralai>=2.3.0`) uses `from mistralai.client import Mistral` (not `from mistralai import Mistral`)
- Async API: `client.chat.complete_async(model=..., messages=..., response_format={"type": "json_object"})`
- Retry pattern: `@retry` on `_call_mistral_extraction`, `RetryError` caught in outer `extract_article`
- Filter criteria: `is_relevant=True`, `sector=GenAI`, `region in {Europe, USA}`, employees 10–50 (if present), funding within 365 days, required fields present
- Deduplication: checks `company_domain` first, then case-insensitive `company_name` match
- No `dateutil` dependency — uses stdlib `datetime` + `timedelta` only

## Phase 7: Email Drafting ✅

**Commits:**
- `d96b377` ✨ feat: add Mistral email drafter with tenacity retries (task 7.1)
- `8514af5` ✨ feat: add POST /api/leads/{id}/regenerate endpoint (task 7.2)

**Files created/modified:**
- `backend/app/pipeline/drafter.py` (new) — `draft_email()` using Mistral free-text, tenacity 3-retry, returns `str | None`
- `backend/app/api/leads.py` (modified) — Added `POST /{lead_id}/regenerate`, returns `{"email_draft": ...}` or 502

**Notes:**
- Uses `timeout_ms=30000` on Mistral call (SDK parameter)
- No `response_format` (free text, unlike extractor)
- Verification: imports OK, regenerate route registered at `/api/leads/{lead_id}/regenerate`

## Phase 8: Pipeline Runner & Orchestration

**Status:** complete

**Tasks completed:**
- 8.1: `app/pipeline/runner.py` — full orchestrator: concurrent source fetching, URL dedup, LLM extraction, filter, DB dedup, lead creation, email drafting, error isolation per-article, pipeline_runs record updated on success/failure
- 8.2: `POST /api/pipeline/run` + `GET /api/pipeline/status` added to `pipeline_router` in `app/api/pipeline.py`
- 8.3: `app/main.py` already had correct router includes — no changes needed

**Files changed:**
- `backend/app/pipeline/runner.py` — new
- `backend/app/api/pipeline.py` — added two pipeline_router routes, added imports

**Commits:**
- `1a40b86` — ✨ feat: add full pipeline runner orchestrator (task 8.1)
- `a3b52cb` — ✨ feat: add pipeline run/status API endpoints (task 8.2)

**Decisions & context:**
- `run_pipeline()` uses its own `AsyncSessionLocal` session (not `get_db`) — long-running session pattern
- `return_exceptions=True` in `asyncio.gather` ensures one failing source doesn't abort the gather
- Individual article errors are appended to `errors[]` list but do NOT abort the run
- Pipeline run record updated to `status='failed'` on catastrophic exception before re-raising
- `email_draft=NULL` is acceptable — lead is still saved if drafting fails

## Phase 9: APScheduler Integration ✅

**Commit:** `efdda1b` — ✨ feat: add APScheduler cron job for daily pipeline (tasks 9.1-9.2)

**Changes in `app/main.py`:**
- Added imports: `logging`, `AsyncIOScheduler`, `CronTrigger`, `run_pipeline`
- Added `logger = logging.getLogger(__name__)`
- Defined `_scheduled_pipeline_job()` async function with try/except error handling — logs success/failure without crashing the scheduler
- Replaced lifespan stub with full scheduler lifecycle: creates `AsyncIOScheduler`, adds a `CronTrigger` job using `settings.PIPELINE_SCHEDULE_HOUR`/`PIPELINE_SCHEDULE_MINUTE`, starts on app startup, shuts down (no wait) on app shutdown

**Verification:** `uv run python -c "from app.main import app, lifespan, _scheduled_pipeline_job; ..."` passed all assertions.

## Phase 10: Testing & Hardening ✅

**Commits:**
- `20075bf` — ✅ test: add unit tests for filter, deduplication, API, and pipeline (tasks 10.1–10.4)
- `1e2f653` — ✨ feat: add structured logging config (task 10.5)

**Test files created:**
- `tests/__init__.py` — empty package marker
- `tests/conftest.py` — shared fixtures: `override_settings`, `client`, `api_key_headers`
- `tests/test_filter.py` — 23 tests: `TestFilterLead` (20 cases) + `TestIsDuplicate` (3 async cases)
- `tests/test_api.py` — 12 tests: auth (403/200), leads CRUD 404s, pagination 422, stats shape
- `tests/test_pipeline.py` — 13 tests: dedupe_by_url, _validate_profile, lru_cache, pipeline runner (mock all externals)
- `tests/test_gnews_counter.py` — 4 tests: daily counter reset, limit blocking, increments

**Test results:** 48/48 passed in 0.22s

**pyproject.toml:** Added `[tool.pytest.ini_options] asyncio_mode = "auto"` for pytest-asyncio 1.x

**Structured logging (`app/logging_config.py`):**
- Dev (localhost): human-readable `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Production: JSON-structured format
- Quietens httpx, httpcore, apscheduler loggers
- Called at module level in `app/main.py` before `FastAPI()` instantiation

**Hardening review:**
- `runner.py` already has `try/except/raise` that updates `run.status="failed"` and commits before re-raising — no changes needed
- No secrets (API keys, passwords) found in any log statements
- `get_db()` already rolls back on exception with `try/yield/except/rollback` pattern
