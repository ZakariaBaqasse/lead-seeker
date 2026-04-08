# Tasks: Lead Seeker Backend Implementation

## Phase 1: Scaffolding & Config

- [ ] 1.2 — Config & env loading (`backend/app/config.py`, `backend/.env`, `backend/.env.example`)
- [ ] 1.3 — FastAPI app entry point (`backend/app/main.py`)
- [ ] 1.4 — API key auth dependency (`backend/app/auth.py`)

> Note: 1.1 (uv init, deps install, app folder) already done by user.

## Phase 2: Database Layer

- [ ] 2.1 — DB session setup (`backend/app/db.py`)
- [ ] 2.2 — Lead SQLAlchemy model (`backend/app/models/lead.py`)
- [ ] 2.3 — PipelineRun model (`backend/app/models/pipeline_run.py`)
- [ ] 2.4 — Alembic setup & initial migration (`backend/alembic/`)
- [ ] 2.5 — Pydantic schemas (`backend/app/schemas/lead.py`, `backend/app/schemas/pipeline.py`)

## Phase 3: REST API — Leads CRUD & Stats

- [ ] 3.1 — Leads list endpoint (`backend/app/api/leads.py`)
- [ ] 3.2 — Lead detail endpoint (`backend/app/api/leads.py`)
- [ ] 3.3 — Lead update endpoint (`backend/app/api/leads.py`)
- [ ] 3.4 — Lead delete endpoint (`backend/app/api/leads.py`)
- [ ] 3.5 — Stats endpoint (`backend/app/api/stats.py`)
- [ ] 3.6 — Register routes in main.py

## Phase 4: Freelancer Profile Loader

- [ ] 4.1 — Profile loader (`backend/app/profile.py`)
- [ ] 4.2 — Sample profile.yaml (`backend/config/profile.yaml`)
- [ ] 4.3 — Profile reload endpoint (`backend/app/api/pipeline.py`)

## Phase 5: Pipeline — Source Fetchers

- [ ] 5.1 — RawArticle data class (`backend/app/pipeline/sources/__init__.py`)
- [ ] 5.2 — Google News RSS fetcher (`backend/app/pipeline/sources/google_news.py`)
- [ ] 5.3 — GNews API fetcher (`backend/app/pipeline/sources/gnews.py`)
- [ ] 5.4 — YC Directory fetcher (`backend/app/pipeline/sources/yc_directory.py`)
- [ ] 5.5 — RSS feeds fetcher (`backend/app/pipeline/sources/rss_feeds.py`)

## Phase 6: Pipeline — LLM Extraction & Filtering

- [ ] 6.1 — Mistral extraction (`backend/app/pipeline/extractor.py`)
- [ ] 6.2 — Filtering logic (`backend/app/pipeline/filter.py`)
- [ ] 6.3 — Database deduplication (`backend/app/pipeline/filter.py`)

## Phase 7: Pipeline — Email Drafting

- [ ] 7.1 — Email drafter (`backend/app/pipeline/drafter.py`)
- [ ] 7.2 — Regenerate endpoint (`backend/app/api/leads.py`)

## Phase 8: Pipeline — Runner & Orchestration

- [ ] 8.1 — Pipeline runner (`backend/app/pipeline/runner.py`)
- [ ] 8.2 — Pipeline API endpoints (`backend/app/api/pipeline.py`)
- [ ] 8.3 — Register pipeline routes in main.py

## Phase 9: APScheduler Integration

- [ ] 9.1 — Scheduler setup in main.py lifespan
- [ ] 9.2 — Job error handling

## Phase 10: Testing & Hardening

- [ ] 10.1 — Unit tests for filtering (`backend/tests/test_filter.py`)
- [ ] 10.2 — Unit tests for API endpoints (`backend/tests/test_api.py`)
- [ ] 10.3 — Integration test for pipeline (`backend/tests/test_pipeline.py`)
- [ ] 10.4 — Additional test cases (`backend/tests/`)
- [ ] 10.5 — Structured logging setup (`backend/app/logging_config.py`)
- [ ] 10.6 — Defensive error handling review
