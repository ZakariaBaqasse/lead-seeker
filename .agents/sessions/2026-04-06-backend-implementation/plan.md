# Plan: Lead Seeker Backend Implementation

## Overview

Full FastAPI backend for Lead Seeker — a personal lead generation tool that auto-discovers funded GenAI startups and drafts cold outreach emails. Implementation follows `docs/Backend-Roadmap.md` exactly.

### Goals

- Bootable FastAPI app with config, auth, and DB layer
- All REST API endpoints operational (leads CRUD, stats, pipeline, profile reload)
- Daily pipeline: fetch → LLM extract → filter → dedup → store → draft email
- APScheduler embedded in-process (no Redis/Celery)
- Test coverage for all critical paths

### Success Criteria

- [ ] All REST API endpoints from TDD §7 operational
- [ ] Daily pipeline end-to-end (4 sources → Mistral extract → filter → dedup → store → email draft)
- [ ] X-API-Key auth enforced globally
- [ ] pipeline_runs table tracks every run
- [ ] profile.yaml loaded, cached, reloadable via endpoint
- [ ] Tests pass for filtering, dedup, API endpoints, pipeline integration

### Out of Scope

- Frontend (SvelteKit) — separate roadmap
- Email sending (user sends manually)
- Redis/Celery (APScheduler only)
- Multi-tenancy, JWT, OAuth

## Technical Approach

- Python 3.12, FastAPI, uv package manager
- Async SQLAlchemy + asyncpg for PostgreSQL
- Alembic for migrations
- APScheduler (AsyncIOScheduler) embedded in FastAPI lifespan
- Mistral API: 2 separate calls per lead (JSON-mode extraction + free-text email draft)
- httpx async for all external HTTP (30s timeout everywhere)
- tenacity for Mistral retries (3 attempts, exponential backoff)
- All secrets via Pydantic Settings from .env

### Key Security Constraint

FastAPI must only be reachable from localhost. X-API-Key validated on every request via global dependency. SvelteKit is the only caller (server-side only).

## Implementation Phases

### Phase 1: Scaffolding & Config
- config.py (Pydantic Settings), main.py (FastAPI + lifespan stub), auth.py (X-API-Key global dep), .env + .env.example

### Phase 2: Database Layer
- db.py (async engine + get_db), models/lead.py + models/pipeline_run.py, alembic init (async), initial migration, schemas/lead.py + schemas/pipeline.py

### Phase 3: REST API (parallel with Phase 4)
- api/leads.py (CRUD + regenerate), api/stats.py, register in main.py

### Phase 4: Profile Loader (parallel with Phase 3)
- profile.py (lru_cache + YAML validation), config/profile.yaml template, POST /api/profile/reload

### Phase 5: Source Fetchers
- pipeline/sources/__init__.py (RawArticle + dedupe_by_url), google_news.py, gnews.py (80/day cap), yc_directory.py, rss_feeds.py

### Phase 6: LLM Extraction & Filtering
- pipeline/extractor.py (Mistral JSON mode + tenacity), pipeline/filter.py (filter_lead + async is_duplicate)

### Phase 7: Email Drafting
- pipeline/drafter.py (Mistral free-text + tenacity), POST /api/leads/{id}/regenerate

### Phase 8: Pipeline Runner & Orchestration
- pipeline/runner.py (full orchestrator, pipeline_runs tracking), api/pipeline.py (run + status endpoints)

### Phase 9: APScheduler Integration
- Add AsyncIOScheduler to main.py lifespan, cron job at configured hour/minute

### Phase 10: Testing & Hardening
- tests/test_filter.py, tests/test_api.py, tests/test_pipeline.py, logging_config.py, defensive error review

## Testing Strategy

- Unit tests: filter criteria, dedup, profile loader, schema validation
- API tests: all endpoints + auth + pagination + error cases (pytest + httpx TestClient)
- Integration: full pipeline with mocked Mistral + fetchers
- pytest + pytest-asyncio for async tests

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Async SQLAlchemy complexity | Medium | Use standard async session patterns; test in Phase 2 |
| Alembic async config | Medium | Use run_async() wrapper in env.py |
| Mistral API failures | Medium | tenacity retries; pipeline continues on per-article failure |
| GNews rate limit | Low | Hard cap at 80/day, in-memory counter resets UTC 00:00 |
| APScheduler job silent failure | Medium | pipeline_runs table tracks every run |
