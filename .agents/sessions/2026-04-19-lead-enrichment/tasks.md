# Tasks: Lead Enrichment via Tavily Search

## Phase 1: Schema, Config & Migration

- [ ] 1.1 — Add `TAVILY_API_KEY: str = ""` to `Settings` in `app/config.py`
- [ ] 1.2 — Add `tavily-python` to dependencies in `pyproject.toml` and run `uv sync`
- [ ] 1.3 — Add `product_description` (Text, nullable) and `tech_stack` (Text, nullable) columns to Lead model (`app/models/lead.py`)
- [ ] 1.4 — Add `product_description` and `tech_stack` to `LeadOut` schema (`app/schemas/lead.py`)
- [ ] 1.5 — Create `EnrichmentResult` Pydantic schema with optional fields: `cto_name`, `linkedin_url`, `employee_count`, `product_description`, `tech_stack` (`app/schemas/lead.py`)
- [ ] 1.6 — Create Alembic migration `002_add_enrichment_columns` adding the two new columns (`alembic/versions/002_add_enrichment_columns.py`)
- [ ] 1.7 — Add `product_description: string | null` and `tech_stack: string | null` to frontend Lead interface (`frontend/src/lib/types.ts`)

## Phase 2: Enricher Module

- [ ] 2.1 — Create `app/pipeline/enricher.py` with `_search_tavily()`, `_build_snippets_text()`, `_parse_enrichment()`, and `enrich_lead()` functions
- [ ] 2.2 — Add `ENRICHMENT_PROMPT` to `app/pipeline/prompts.py`
- [ ] 2.3 — Add Langfuse tracing span `enrichment-llm-call` inside `_parse_enrichment()`

## Phase 3: Pipeline Integration & Drafter Update

- [ ] 3.1 — Refactor `_process_article()` in `runner.py` — split single session block into two (dedup check → enrichment → insert+draft)
- [ ] 3.2 — Import and call `enrich_lead()`, merge enrichment results into `Lead()` constructor
- [ ] 3.3 — Update `lead_data` dict passed to `draft_email()` to include `cto_name`, `product_description`, `tech_stack`
- [ ] 3.4 — Update `DRAFTING_PROMPT` in `prompts.py` with new placeholders and conditional fallbacks
- [ ] 3.5 — Update `draft_email()` in `drafter.py` to pass enriched fields with None-safe defaults

## Phase 4: Tests & Fixes

- [ ] 4.1 — Fix stale `mock_gnews` mock in `tests/test_pipeline.py` (remove it, not imported in runner.py)
- [ ] 4.2 — Add `mock_enrich_lead` to pipeline integration test and verify enriched fields on stored lead
- [ ] 4.3 — Create `tests/test_enricher.py` with unit tests: success, partial results, Tavily failure, Mistral failure, no API key, snippet truncation, LinkedIn URL extraction
