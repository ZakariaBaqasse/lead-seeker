# Lead Seeker — Backend Implementation Roadmap

## Overview

Step-by-step backend implementation plan derived from the [PRD](./PRD.md) and [Technical Design Document](./Technical-Design-Doc.md). Each phase builds on the previous one, with clear acceptance criteria and file references. The backend is a FastAPI application with APScheduler, PostgreSQL, and Mistral API integration.

### Goals

- Implement all backend functionality described in the PRD and TDD
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

- Frontend (SvelteKit) — separate roadmap
- Deployment/Dokploy configuration — separate task
- Phase 2 paid enrichment (Crunchbase, Apollo.io)
- Email sending functionality
- Mobile layout, multi-tenancy, WebSockets

---

## Phase 1: Project Scaffolding & Configuration

**Goal:** Bootable FastAPI app with config management, ready to accept routes.

### Tasks

**1.1 — Initialize Python project with uv** (`backend/`, `backend/app/`, `pyproject.toml`)

- Initialize with `uv init` inside `backend/`, creating `pyproject.toml` and `uv.lock`
- Create directory structure matching TDD §4
- Add dependencies via `uv add`: fastapi, uvicorn, sqlalchemy, alembic, asyncpg, httpx, apscheduler, pydantic, pydantic-settings, tenacity, pyyaml, mistralai
- Add dev dependencies via `uv add --dev`: pytest, pytest-asyncio, httpx (test client)

**1.2 — Configuration & environment loading** (`backend/app/config.py`, `backend/.env`)

- Pydantic Settings class reading from `.env`
- Fields: `DATABASE_URL`, `MISTRAL_API_KEY`, `API_SECRET_KEY`, `PIPELINE_SCHEDULE_HOUR` (default 6), `PIPELINE_SCHEDULE_MINUTE` (default 0)
- `.env.example` with placeholder values

**1.3 — FastAPI application entry point** (`backend/app/main.py`)

- Create FastAPI app instance with lifespan handler (for scheduler startup/shutdown)
- Include placeholder routers for leads, pipeline, stats
- CORS is **not required** for production — SvelteKit makes all FastAPI calls server-side over localhost. For local development without SvelteKit (standalone API testing), add dev-only CORS allowing `http://localhost:3000`. Do **not** expose CORS to the public internet.

**1.4 — API key authentication dependency** (`backend/app/auth.py`)

- `verify_api_key` dependency using `APIKeyHeader("X-API-Key")` per TDD §7
- Apply as global dependency on the FastAPI app

### Acceptance Criteria

- `uv run uvicorn app.main:app` starts without errors
- Unauthenticated requests return 403
- Authenticated requests with correct `X-API-Key` return 200 on a health endpoint

---

## Phase 2: Database Layer

**Goal:** PostgreSQL connection, SQLAlchemy models, Alembic migrations, Pydantic schemas.

### Tasks

**2.1 — Database session setup** (`backend/app/db.py`)

- Async SQLAlchemy engine + async session factory using `asyncpg`
- `get_db` dependency yielding async sessions
- Engine created from `settings.DATABASE_URL`

**2.2 — Lead SQLAlchemy model** (`backend/app/models/lead.py`)

- All columns from TDD §6:
  - `id` — UUID PK, default `gen_random_uuid()`
  - `company_name` — VARCHAR(255), NOT NULL
  - `company_domain` — VARCHAR(255)
  - `company_description` — TEXT
  - `region` — VARCHAR(100)
  - `country` — VARCHAR(100)
  - `employee_count` — INTEGER
  - `funding_amount` — VARCHAR(50)
  - `funding_date` — DATE
  - `funding_round` — VARCHAR(50)
  - `news_headline` — TEXT
  - `news_url` — VARCHAR(500)
  - `cto_name` — VARCHAR(255)
  - `cto_email` — VARCHAR(255)
  - `linkedin_url` — VARCHAR(500)
  - `status` — VARCHAR(50), NOT NULL, default `'draft'`. Allowed values: **`draft`**, **`sent`**, **`replied_won`**, **`replied_lost`**, **`archived`** (per PRD §6.2 lifecycle)
  - `email_draft` — TEXT
  - `notes` — TEXT
  - `sent_at` — TIMESTAMP WITH TIME ZONE
  - `created_at` — TIMESTAMP WITH TIME ZONE, default `now()`
  - `updated_at` — TIMESTAMP WITH TIME ZONE, default `now()`
- Indexes: `status`, `created_at DESC`, partial unique on `company_domain` (WHERE NOT NULL)

**2.3 — Pipeline runs model** (`backend/app/models/pipeline_run.py`)

- Fields: `id` (UUID PK), `started_at`, `completed_at`, `articles_fetched` (int), `articles_processed` (int), `leads_created` (int), `errors` (JSON), `status` (running/completed/failed)

**2.4 — Alembic setup & initial migration** (`backend/alembic/`)

- `alembic init` with async configuration
- Configure `env.py` for async engine (use `run_async()` wrapper — Alembic migrations run synchronously but connect via the async engine)
- Initial migration creating `leads` and `pipeline_runs` tables
- Test early: run `alembic upgrade head` immediately to validate the setup

**2.5 — Pydantic schemas** (`backend/app/schemas/lead.py`, `backend/app/schemas/pipeline.py`)

- `LeadStatus` — string enum: `draft`, `sent`, `replied_won`, `replied_lost`, `archived`
- `LeadOut` — full lead data for API responses (all fields)
- `LeadUpdate` — optional fields for PATCH: `cto_name`, `cto_email`, `linkedin_url`, `notes`, `status` (validated against `LeadStatus` enum)
- `LeadListResponse` — `{ items: list[LeadOut], total: int }`
- `LeadListParams` — query parameter schema with validation (see Phase 3.1)
- `PipelineRunOut` — pipeline run metadata for status endpoint
- `StatsOut` — counts by status `{ draft: int, sent: int, replied_won: int, replied_lost: int, archived: int }`
- `ExtractionResult` — structured JSON from Mistral extraction (company_name, company_domain, funding_amount, funding_round, funding_date, employee_count_estimate, region, country, sector, summary, is_relevant)

### Acceptance Criteria

- `alembic upgrade head` creates both tables with correct schema
- Models match TDD §6 exactly (column types, indexes, defaults)
- Status field only accepts the 5 defined enum values
- Pydantic schemas validate test data correctly

---

## Phase 3: REST API — Leads CRUD & Stats

**Goal:** All lead management endpoints operational with filtering, pagination, and input validation.

### Tasks

**3.1 — Leads list endpoint** (`backend/app/api/leads.py`)

- `GET /api/leads` with validated query params:
  - `status` — optional, validated against `LeadStatus` enum
  - `region` — optional string
  - `from_date`, `to_date` — optional, ISO 8601 date format
  - `page` — integer ≥ 1, default 1
  - `limit` — integer 1–100, default 20
- Returns `LeadListResponse` with pagination (`items` + `total` count)
- SQLAlchemy query with dynamic filters, ordered by `created_at DESC`
- Return 422 on invalid query params (Pydantic handles this)

**3.2 — Lead detail endpoint** (`backend/app/api/leads.py`)

- `GET /api/leads/{id}` returning single `LeadOut`
- 404 if not found

**3.3 — Lead update endpoint** (`backend/app/api/leads.py`)

- `PATCH /api/leads/{id}` accepting `LeadUpdate` body
- Updates only provided fields, sets `updated_at` to `now()`
- If `status` changes to `'sent'`, auto-set `sent_at` to `now()`
- Status transitions validated against the `LeadStatus` enum
- 404 if not found

**3.4 — Lead delete endpoint** (`backend/app/api/leads.py`)

- `DELETE /api/leads/{id}` returning 204
- Hard delete (lead is removed from DB)
- 404 if not found

**3.5 — Stats endpoint** (`backend/app/api/stats.py`)

- `GET /api/stats` returning counts grouped by status
- Query: `SELECT status, COUNT(*) FROM leads GROUP BY status`
- Returns `StatsOut` with zero-filled counts for all 5 statuses

**3.6 — Register routes in main.py** (`backend/app/main.py`)

- Include leads router with prefix `/api`
- Include stats router with prefix `/api`

### Acceptance Criteria

- All 5 endpoints return correct data with proper status codes
- Filtering by status, region, date range works correctly
- Pagination returns correct `total` and subset of items
- Invalid query params return 422 with descriptive errors
- Update correctly handles `sent_at` auto-setting on status change
- All endpoints require valid `X-API-Key`

---

## Phase 4: Freelancer Profile Loader

**Goal:** Load and cache `profile.yaml`, expose reload endpoint.

### Tasks

**4.1 — Profile loader** (`backend/app/profile.py`)

- `get_profile()` function with `lru_cache(maxsize=1)` per TDD §9
- Reads `backend/config/profile.yaml`, returns dict
- YAML schema validation at load time: require `name` (str), `title` (str), `pitch` (str), `projects` (list, each with `name`, `description`, `video_url`, `tags`), `skills` (list of strings)
- Raise clear `ValueError` with descriptive message on malformed or missing file

**4.2 — Sample profile.yaml** (`backend/config/profile.yaml`)

- Template with placeholder values matching PRD §6.5 structure:

```yaml
name: "Your Name"
title: "Senior Software Engineer / GenAI Contractor"
pitch: "One-sentence engagement proposition."

projects:
  - name: "Project Name"
    description: "What you built, for whom, and the measurable outcome."
    video_url: "https://drive.google.com/file/d/..."
    tags: ["RAG", "Python", "LLM"]

skills:
  - "Python, FastAPI, LangChain"
  - "SvelteKit, PostgreSQL, Docker"
```

**4.3 — Profile reload endpoint** (`backend/app/api/pipeline.py`)

- `POST /api/profile/reload` that calls `get_profile.cache_clear()` then reloads
- Returns validation result: `{ status: "ok" }` on success, or error details on malformed YAML

### Acceptance Criteria

- Profile loads at startup, returned from cache on subsequent calls
- Malformed YAML raises descriptive error at startup (fail-fast)
- Reload endpoint clears cache, re-reads file, and reports validation result
- Missing required fields in YAML produce clear error messages

---

## Phase 5: Pipeline — Source Fetchers

**Goal:** All 4 news source fetchers operational, returning `RawArticle` objects. Each fetcher is resilient — failures are logged but don't crash the pipeline.

### Tasks

**5.1 — RawArticle data class** (`backend/app/pipeline/sources/__init__.py`)

- `RawArticle(headline: str, body_snippet: str, url: str, source_name: str)`
- `dedupe_by_url(articles: list[RawArticle]) -> list[RawArticle]` — remove duplicate URLs across sources before LLM extraction (cheap dedup per TDD §3.2)

**5.2 — Google News RSS fetcher** (`backend/app/pipeline/sources/google_news.py`)

- Async httpx fetch of Google News RSS with targeted queries: `"GenAI" AND ("seed" OR "Series A" OR "Series B") AND "2025"`
- Parse RSS XML, extract headline + link + snippet
- **Explicit timeout:** `httpx.AsyncClient(timeout=30.0)`. Timeout → log warning, return empty list.
- Return list of `RawArticle`

**5.3 — GNews API fetcher** (`backend/app/pipeline/sources/gnews.py`)

- Async httpx call to GNews search endpoint with keyword filters: GenAI + funding
- **Rate limiting:** Hard cap at 80 requests/day (of the 100/day free limit). Track with an in-memory counter that resets at UTC 00:00. Log when approaching 80; skip GNews entirely if limit reached.
- **Explicit timeout:** `httpx.AsyncClient(timeout=30.0)`. Timeout → log warning, return empty list.
- Return list of `RawArticle`

**5.4 — YC Directory fetcher** (`backend/app/pipeline/sources/yc_directory.py`)

- Fetch YC JSON endpoint, filter by industry=AI, batch=recent
- **Explicit timeout:** `httpx.AsyncClient(timeout=30.0)`. Timeout → log warning, return empty list.
- Return list of `RawArticle`

**5.5 — RSS feeds fetcher** (`backend/app/pipeline/sources/rss_feeds.py`)

- Fetch TechCrunch, Sifted, EU-Startups RSS feeds
- Parse RSS XML for funding-related articles
- **Explicit timeout:** `httpx.AsyncClient(timeout=30.0)`. Timeout → log warning, return empty list.
- Return list of `RawArticle`

### Acceptance Criteria

- Each fetcher returns a list of `RawArticle` with populated fields
- GNews respects the 80 req/day cap; counter resets at UTC 00:00
- URL dedup removes cross-source duplicates
- Fetcher failures (timeout, network error, parse error) are caught and logged — return empty list, don't crash the pipeline
- All HTTP calls have explicit 30s timeout

---

## Phase 6: Pipeline — LLM Extraction & Filtering

**Goal:** Mistral API integration for article extraction, filtering logic, and DB-level deduplication.

### Tasks

**6.1 — Mistral extraction** (`backend/app/pipeline/extractor.py`)

- Async Mistral API client with **explicit timeout** on API calls
- Extraction function: takes `RawArticle`, returns `ExtractionResult` or `None`
- Uses `response_format={"type": "json_object"}` per TDD §5.3
- Extraction prompt per TDD §8.2:

```
You are a data extraction assistant. Given a news article about a startup funding event,
extract the following fields as a JSON object. If you cannot confidently extract a field,
use null. Set is_relevant=false if the article is not about a GenAI startup funding event.

Fields: company_name, company_domain, funding_amount, funding_round, funding_date
(YYYY-MM-DD), employee_count_estimate (integer or null), region (Europe/USA/Other),
country, sector (GenAI/Other), summary (2-3 sentences), is_relevant (bool).

Article:
{article_text}
```

- Wrapped in tenacity retry: 3 attempts, exponential backoff per TDD §8.4
- JSON parse failure after retries → log error, return `None` (article discarded)

**6.2 — Filtering logic** (`backend/app/pipeline/filter.py`)

- `filter_lead(extraction: ExtractionResult) -> bool`
- Reject if:
  - `is_relevant` is `false`
  - `sector` is not `"GenAI"`
  - `region` not in `("Europe", "USA")`
  - `employee_count_estimate` outside 10–50 range (if present)
  - `funding_date` older than 12 months from today
  - Missing required fields: `company_name`, `funding_amount`, `funding_date`

**6.3 — Database deduplication** (`backend/app/pipeline/filter.py`)

- `async is_duplicate(session, extraction: ExtractionResult) -> bool`
- Check `company_domain` against unique index (if domain present)
- Fallback: case-insensitive `company_name` match per TDD §6
- Returns `True` if lead already exists in DB

### Acceptance Criteria

- Extraction returns valid JSON matching `ExtractionResult` schema
- Non-relevant or unparseable articles are discarded with logging
- Filter correctly applies all criteria from PRD §6.1
- Deduplication catches both domain and name matches
- Retries work on transient Mistral API failures (429, 500, timeout)
- All Mistral API calls have explicit timeouts

---

## Phase 7: Pipeline — Email Drafting

**Goal:** Generate personalized outreach emails using Mistral API + profile context.

### Tasks

**7.1 — Email drafter** (`backend/app/pipeline/drafter.py`)

- Async function: takes lead data dict + profile dict, returns email draft string
- Email drafting prompt per TDD §8.3:

```
You are writing a cold outreach email on behalf of {name}, a {title}.

Freelancer profile:
{profile_yaml_as_text}

Target company:
- Name: {company_name}
- Recent news: {summary}
- Funding: {funding_amount} {funding_round} on {funding_date}
- Region: {country}

Choose the single most relevant portfolio project from the profile above based on the
company's industry. Write a concise, direct cold email (150–200 words) that:
1. Opens by referencing the company's recent funding news
2. Briefly introduces the freelancer and their most relevant project with the demo video link
3. Proposes a time-bound engagement (e.g., 3-month contract)
4. Ends with a clear, low-friction call to action

Do not use filler phrases like "I hope this finds you well". Be direct.
```

- Free text response (no JSON mode) per TDD §5.3
- **Explicit timeout** on Mistral API call
- Tenacity retry: 3 attempts, exponential backoff
- **If drafting fails after all retries:** log error, the lead is still stored in the database with `status='draft'` and `email_draft=NULL`. The user can manually trigger regeneration via `POST /api/leads/{id}/regenerate` later.

**7.2 — Regenerate endpoint** (`backend/app/api/leads.py`)

- `POST /api/leads/{id}/regenerate`
- Fetches lead from DB, loads profile via `get_profile()`, calls drafter
- Updates lead's `email_draft` field and `updated_at`
- Returns `{ email_draft: string }`
- 404 if lead not found

### Acceptance Criteria

- Email draft references company's funding news and a relevant portfolio project
- Regeneration replaces old draft with new one
- Failed drafting does **not** prevent lead from being stored (lead created with `email_draft=NULL`)
- Retry logic handles transient Mistral failures gracefully

---

## Phase 8: Pipeline — Runner & Orchestration

**Goal:** Full pipeline orchestrator wiring all stages together, with observability.

### Tasks

**8.1 — Pipeline runner** (`backend/app/pipeline/runner.py`)

- `async def run_pipeline(session)` orchestrating the full flow from TDD §3.2:
  1. Create `pipeline_runs` record (`status='running'`, `started_at=now()`)
  2. Fetch from all sources concurrently via `asyncio.gather()` (google_news, gnews, yc_directory, rss_feeds)
  3. URL-level dedup across all fetched articles
  4. For each article sequentially:
     - Extract structured data via Mistral → skip on failure
     - Filter by criteria → skip if rejected
     - Check DB deduplication → skip if duplicate
     - Store lead in `leads` table (`status='draft'`)
     - Draft email via Mistral → update lead's `email_draft` (or leave NULL on failure)
  5. Update `pipeline_runs` record: `articles_fetched`, `articles_processed`, `leads_created`, `errors` (JSON array), `completed_at=now()`, `status='completed'`
- Individual article failures are logged and counted in `errors` but do **not** abort the run

**8.2 — Pipeline API endpoints** (`backend/app/api/pipeline.py`)

- `POST /api/pipeline/run` — manually triggers `run_pipeline()`. This is a **synchronous endpoint** (blocks until the pipeline completes). Expected duration: < 2 minutes per TDD §11. Callers (SvelteKit server-side) should set an HTTP timeout ≥ 120 seconds.
- `GET /api/pipeline/status` — returns the last `pipeline_runs` record (last run time, leads found, error count)

**8.3 — Register pipeline routes** (`backend/app/main.py`)

- Include pipeline router with prefix `/api`

### Acceptance Criteria

- Manual trigger runs the full pipeline end-to-end
- Pipeline status shows last run metadata (time, counts, errors)
- Individual article failures don't crash the full run
- `pipeline_runs` table updated with accurate counts on every run
- Completed runs have all 4 sources attempted (even if some return empty)

---

## Phase 9: APScheduler Integration

**Goal:** Daily automatic pipeline execution with configured schedule.

### Tasks

**9.1 — Scheduler setup** (`backend/app/main.py`)

- APScheduler `AsyncIOScheduler` initialized in FastAPI lifespan context manager
- Add cron job: `run_pipeline` at configured hour/minute from settings (default 06:00 UTC per TDD §11)
- Scheduler starts on app startup, shuts down gracefully on app shutdown

**9.2 — Job error handling**

- Wrap the scheduled job invocation in `try/except` to prevent scheduler death on unhandled exceptions
- On failure: update `pipeline_runs` with `status='failed'`, log the full traceback
- The scheduler continues running — the next day's job will execute regardless of previous failure

### Acceptance Criteria

- Scheduler starts with the app and registers the pipeline job at the configured time
- Scheduler survives job failures without dying or skipping future runs
- Schedule time is configurable via `PIPELINE_SCHEDULE_HOUR` and `PIPELINE_SCHEDULE_MINUTE` environment variables
- Job start and completion are logged

---

## Phase 10: Testing & Hardening

**Goal:** Test coverage for critical paths, structured logging, and error resilience.

### Tasks

**10.1 — Unit tests for filtering logic** (`backend/tests/test_filter.py`)

- Test all filter criteria individually:
  - Sector: accept GenAI, reject Other
  - Region: accept Europe/USA, reject Other
  - Employee count: accept 10–50, reject outside range, accept when missing (nullable)
  - Funding date: accept within 12 months, reject older
  - Required fields: reject when company_name, funding_amount, or funding_date missing
- Test deduplication:
  - Domain match → duplicate
  - Case-insensitive name match → duplicate
  - No match → not duplicate

**10.2 — Unit tests for API endpoints** (`backend/tests/test_api.py`)

- Test leads CRUD:
  - List with filters (status, region, date range) and pagination
  - Detail: found and 404
  - Update: valid patch, status→sent sets sent_at, invalid status rejected
  - Delete: found and 404
- Test stats endpoint: correct counts with mixed statuses
- Test auth rejection: missing API key → 403, wrong API key → 403
- Test query param validation: invalid page/limit/status → 422

**10.3 — Integration test for pipeline** (`backend/tests/test_pipeline.py`)

- Mock Mistral API responses (extraction + drafting) and all source fetchers
- Run full pipeline, verify:
  - Leads created in DB with correct fields
  - `pipeline_runs` record created with accurate counts
  - Duplicate articles skipped
  - Failed extractions logged but run completes
  - Email draft failure → lead still exists with `email_draft=NULL`

**10.4 — Additional test cases** (`backend/tests/`)

- APScheduler job: verify job is registered with correct cron schedule at startup
- GNews counter: verify counter increments, rejects at 80, resets behavior
- Profile loader: verify LRU cache returns same object, reload clears cache, malformed YAML raises error
- Regenerate endpoint: verify new draft replaces old one

**10.5 — Structured logging setup** (`backend/app/main.py`, `backend/app/logging_config.py`)

- Python logging configuration: structured JSON logs in production, human-readable in dev
- Log pipeline stages: source fetch start/end/count, extraction results, filter decisions, dedup results, email drafting
- Log all API requests with method, path, status code, duration

**10.6 — Defensive error handling review**

- Verify all external HTTP calls (Mistral, news sources) have explicit 30s timeouts
- Verify DB sessions are properly closed on errors (async context managers)
- Verify no secrets leak into logs or error responses
- Verify `pipeline_runs` is updated even when the pipeline crashes mid-run (use try/finally)

### Acceptance Criteria

- All tests pass with `pytest`
- Filter tests cover all acceptance/rejection criteria from PRD §6.1
- API tests cover happy paths + error cases + auth
- Pipeline integration test verifies end-to-end flow with mocked externals
- All external HTTP calls have explicit 30s timeouts
- Logs are structured and include pipeline observability data

---

## Implementation Phases — Dependency Graph

```
Phase 1: Scaffolding
    │
    ▼
Phase 2: Database Layer
    │
    ├──────────────────┐
    ▼                  ▼
Phase 3: REST API    Phase 4: Profile Loader
    │                  │
    │    ┌─────────────┘
    │    │
    ▼    ▼
Phase 5: Source Fetchers
    │
    ▼
Phase 6: LLM Extraction & Filtering
    │
    ▼
Phase 7: Email Drafting  ◄── (depends on Phase 4 profile + Phase 6 extraction)
    │
    ▼
Phase 8: Pipeline Runner  ◄── (wires Phases 5–7 together)
    │
    ▼
Phase 9: APScheduler
    │
    ▼
Phase 10: Testing & Hardening  ◄── (covers all phases; write tests incrementally alongside Phases 5–9)
```

> **Note:** Phase 10 is listed last but tests should be written incrementally alongside Phases 5–9. The final phase is for gap-filling, integration tests, and hardening.

---

## Testing Strategy

| Type              | Scope                                                        | Tools                  |
| ----------------- | ------------------------------------------------------------ | ---------------------- |
| Unit tests        | Filtering, deduplication, profile loading, schema validation | pytest                 |
| API tests         | All endpoints with TestClient, auth, error responses         | pytest + httpx         |
| Integration tests | Pipeline runner with mocked external APIs                    | pytest + unittest.mock |
| Manual testing    | Full pipeline run against real APIs (dev environment)        | curl / httpie          |

---

## Risks

| Risk                                 | Impact | Mitigation                                                                           |
| ------------------------------------ | ------ | ------------------------------------------------------------------------------------ |
| Async SQLAlchemy complexity          | Medium | Use well-documented async session patterns; test DB operations in Phase 2            |
| Mistral API changes/downtime         | Medium | Tenacity retries with exponential backoff; pipeline continues on individual failures |
| RSS feed format changes              | Low    | Each fetcher has try/except; log parsing errors, return empty list                   |
| GNews rate limit exceeded            | Low    | Hard cap at 80 req/day with in-memory counter; counter resets at UTC 00:00           |
| APScheduler job silent failure       | Medium | `pipeline_runs` table tracks every run; surface last run status in dashboard         |
| Pipeline HTTP timeout (hung request) | Medium | All httpx and Mistral calls have explicit 30s timeout                                |
| POST /api/pipeline/run hangs         | Medium | Expected < 2 min; callers should set HTTP timeout ≥ 120s                             |

## Assumptions

- PostgreSQL is accessible at the `DATABASE_URL` before Phase 2 tasks run
- Mistral API key is valid and has sufficient credit
- VPS has Python 3.11+ available
- News RSS feeds (Google News, TechCrunch, Sifted, EU-Startups) remain publicly accessible
- GNews free tier remains at 100 req/day
- YC Directory JSON endpoint remains publicly accessible

---

## File Reference (Complete)

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, APScheduler, route registration
│   ├── config.py                # Pydantic Settings (env loading)
│   ├── auth.py                  # X-API-Key dependency
│   ├── db.py                    # Async SQLAlchemy engine + session
│   ├── profile.py               # profile.yaml loader with lru_cache
│   ├── logging_config.py        # Structured logging setup
│   ├── api/
│   │   ├── leads.py             # CRUD + regenerate endpoints
│   │   ├── pipeline.py          # Pipeline run/status + profile reload
│   │   └── stats.py             # Dashboard stats endpoint
│   ├── pipeline/
│   │   ├── runner.py            # Full pipeline orchestrator
│   │   ├── sources/
│   │   │   ├── __init__.py      # RawArticle dataclass, dedupe_by_url
│   │   │   ├── google_news.py   # Google News RSS fetcher
│   │   │   ├── gnews.py         # GNews API fetcher (rate-limited)
│   │   │   ├── yc_directory.py  # YC startup directory fetcher
│   │   │   └── rss_feeds.py     # TechCrunch/Sifted/EU-Startups RSS
│   │   ├── extractor.py         # Mistral extraction (JSON mode)
│   │   ├── filter.py            # Filtering logic + DB deduplication
│   │   └── drafter.py           # Mistral email draft (free text)
│   ├── models/
│   │   ├── lead.py              # SQLAlchemy Lead model
│   │   └── pipeline_run.py      # SQLAlchemy PipelineRun model
│   └── schemas/
│       ├── lead.py              # LeadOut, LeadUpdate, LeadListResponse, LeadStatus enum
│       └── pipeline.py          # PipelineRunOut, StatsOut, ExtractionResult
├── alembic/                     # DB migrations (async config)
├── config/
│   └── profile.yaml             # Freelancer profile context
├── tests/
│   ├── test_filter.py           # Filter + dedup unit tests
│   ├── test_api.py              # API endpoint tests
│   └── test_pipeline.py         # Pipeline integration tests
├── .env                         # MISTRAL_API_KEY, DATABASE_URL, API_SECRET_KEY
├── .env.example                 # Placeholder env file
├── pyproject.toml               # Project metadata & dependencies (uv)
└── uv.lock                      # Lockfile (committed to git)
```
