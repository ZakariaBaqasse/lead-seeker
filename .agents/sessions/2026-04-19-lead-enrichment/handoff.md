# Handoff: Lead Enrichment via Tavily Search

<!-- Append a new phase section after each phase completes. -->

## Phase 1: Schema, Config & Migration

**Status:** complete

**Tasks completed:**
- 1.1: Added `TAVILY_API_KEY: str = ""` to `Settings` in `backend/app/config.py`
- 1.2: Added `tavily-python>=0.5.0` to `backend/pyproject.toml` and ran `uv sync` (installed `tavily-python==0.7.23`)
- 1.3: Added `product_description` (Text, nullable) and `tech_stack` (Text, nullable) to `Lead` model after `linkedin_url`
- 1.4: Added `product_description: Optional[str] = None` and `tech_stack: Optional[str] = None` to `LeadOut` schema
- 1.5: Created `EnrichmentResult` Pydantic model in `backend/app/schemas/lead.py` (before `ExtractionResult`)
- 1.6: Created `backend/alembic/versions/002_add_enrichment_columns.py` (revision `002`, down_revision `001`)
- 1.7: Added `product_description: string | null` and `tech_stack: string | null` to `Lead` interface in `frontend/src/lib/types.ts`

**Files changed:**
- `backend/app/config.py` — added `TAVILY_API_KEY: str = ""`
- `backend/pyproject.toml` — added `tavily-python>=0.5.0`
- `backend/uv.lock` — updated lockfile with tavily-python, tiktoken, regex
- `backend/app/models/lead.py` — added `product_description` and `tech_stack` columns
- `backend/app/schemas/lead.py` — added fields to `LeadOut`, new `EnrichmentResult` class
- `backend/alembic/versions/002_add_enrichment_columns.py` — new migration file
- `frontend/src/lib/types.ts` — added `product_description` and `tech_stack` to Lead interface

**Commits:**
- `6947e51` — ✨ feat: add TAVILY_API_KEY to settings
- `adf0f53` — ✨ feat: add tavily-python dependency
- `8158ff9` — ✨ feat: add product_description and tech_stack to Lead model
- `2d75cad` — ✨ feat: add product_description, tech_stack, and EnrichmentResult to schemas
- `fa81652` — ✨ feat: add migration 002 for enrichment columns
- `b525cdd` — ✨ feat: add product_description and tech_stack to frontend Lead type

**Decisions & context for next phase:**
- `EnrichmentResult` is defined in `app/schemas/lead.py` and can be imported by the enricher: `from app.schemas.lead import EnrichmentResult`
- `tavily-python` installed as `tavily-python` package; import as `from tavily import AsyncTavilyClient`
- New Lead model columns: `product_description` and `tech_stack` (Text, nullable) — placed after `linkedin_url`
- `TAVILY_API_KEY` accessed via `settings.TAVILY_API_KEY` (empty string default, no error if not set)
- Two pre-existing test failures exist (unrelated to Phase 1): `test_filter_non_genai_sector_rejected` and `test_pipeline_run_completes` — documented in Phase 4 tasks

## Phase 2: Enricher Module

**Status:** complete

**Tasks completed:**
- 2.1: Created `backend/app/pipeline/enricher.py` with `_search_tavily`, `_build_snippets_text`, `_parse_enrichment`, and `enrich_lead` functions
- 2.2: Added `ENRICHMENT_PROMPT` constant to `backend/app/pipeline/prompts.py`
- 2.3: (part of 2.1) Langfuse tracing span `enrichment-llm-call` added inside `_parse_enrichment` → `_call_mistral_enrichment`

**Files changed:**
- `backend/app/pipeline/enricher.py` — new file (135 lines)
- `backend/app/pipeline/prompts.py` — appended ENRICHMENT_PROMPT after EXTRACTION_PROMPT

**Commits:**
- `4bf0e98` — ✨ feat: add ENRICHMENT_PROMPT to prompts
- `7114faf` — ✨ feat: create enricher module with Tavily search and Mistral parsing

**Decisions & context for next phase:**
- `enrich_lead()` returns `EnrichmentResult | None` — caller must handle None gracefully
- Import path: `from app.pipeline.enricher import enrich_lead`
- Import EnrichmentResult: `from app.schemas.lead import EnrichmentResult`
- Retry is handled internally — `enrich_lead` never raises, always returns `None` on failure
- `_search_tavily` also never raises — retry logic is in `_search_tavily_with_retry`; outer wrapper catches and returns `[]`
- Tavily response shape: `response["results"]` list with keys `title`, `url`, `content`
- Snippets text truncated to 4000 chars before being passed to Mistral
- All 14 pre-existing test failures remain unchanged (none introduced by Phase 2)

## Phase 3: Pipeline Integration & Drafter Update

**Status:** complete

**Tasks completed:**
- 3.1/3.2/3.3: Refactored _process_article() — two session blocks, enrich_lead() called between dedup and insert, enriched fields in Lead constructor and lead_data
- 3.4: Updated DRAFTING_PROMPT with cto_name, product_description, tech_stack placeholders + Personalization constraint + updated example greeting
- 3.5: Updated draft_email() to pass enriched fields with None-safe defaults

**Files changed:**
- `backend/app/pipeline/runner.py` — session split, enrichment wired in
- `backend/app/pipeline/prompts.py` — DRAFTING_PROMPT updated
- `backend/app/pipeline/drafter.py` — draft_email() updated

**Commits:**
- `1f26a44` — ✨ feat: refactor _process_article to split sessions and wire enrichment
- `e3a73bb` — ✨ feat: update DRAFTING_PROMPT with enriched fields
- `06c8743` — ✨ feat: pass enriched fields to draft_email with None-safe defaults

**Decisions & context for next phase:**
- test_pipeline.py has stale `mock_gnews` fixture (patches `app.pipeline.runner.fetch_gnews` which no longer exists) and needs mock_enrich_lead — Phase 4 fixes this
- enrich_lead() always returns None or EnrichmentResult — runner uses conditional `if enrichment else` pattern throughout
- All 14 pre-existing test failures remain (no regressions introduced)

## Phase 4: Tests & Fixes

**Status:** complete

**Tasks completed:**
- 4.1: Removed stale mock_gnews, added mock_enrich_lead returning None
- 4.2: Also patched AsyncSessionLocal with TestingSessionLocal so runner's internal sessions use test DB; pipeline integration test now passes with leads_created == 1
- 4.3: Created tests/test_enricher.py with 8 unit tests

**Files changed:**
- `backend/tests/test_pipeline.py` — removed fetch_gnews mock, added enrich_lead mock, patched AsyncSessionLocal
- `backend/tests/test_enricher.py` — new file (8 tests)

**Commits:**
- `f8b6ac5` — 🐛 fix: remove stale mock_gnews and add mock_enrich_lead to pipeline test
- `70701bd` — ✅ test: add unit tests for enricher module

**Test results:**
- 63 passed, 13 failed (all 13 are pre-existing failures unrelated to enrichment)
- test_pipeline_run_completes: now PASSING (was previously failing)
- All 8 enricher tests: PASSING

**Decisions & context:**
- Root cause of test_pipeline_run_completes DNS failure: direnv loads DATABASE_URL=postgresql+asyncpg://root:root@db:5432/leadseeker into shell env; os.environ.setdefault() in conftest doesn't override it; _process_article() uses AsyncSessionLocal() directly (not the injected session), so it tried to connect to the unreachable Docker postgres host. Fixed by patching app.pipeline.runner.AsyncSessionLocal with TestingSessionLocal.
- 13 pre-existing failures: 12 test_api.py (403 auth issue) + 1 test_filter.py::test_filter_non_genai_sector_rejected (sector filtering not implemented)
