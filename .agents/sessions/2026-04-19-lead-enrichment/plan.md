# Plan: Lead Enrichment via Tavily Search

> Source of truth: `docs/Lead-enrichement.md` — this file is a session summary.

## Overview

Add an automated enrichment step to the lead pipeline that uses Tavily web search to populate CTO name, LinkedIn URL, employee count, product description, and tech stack for each new lead — before the email is drafted.

New pipeline flow:
```
fetch → dedup → extract → filter → DB dedup → enrich → store → draft
```

## Implementation Phases

### Phase 1: Schema, Config & Migration
- Add `TAVILY_API_KEY` to `Settings` in `app/config.py`
- Add `tavily-python` to `pyproject.toml`
- Add `product_description` (Text) and `tech_stack` (Text) to Lead model
- Add `product_description` and `tech_stack` to `LeadOut` schema
- Create `EnrichmentResult` Pydantic schema in `app/schemas/lead.py`
- Create Alembic migration `002_add_enrichment_columns`
- Add `product_description` and `tech_stack` to frontend `types.ts`

### Phase 2: Enricher Module
- Create `app/pipeline/enricher.py` with:
  - `_search_tavily()` — async Tavily wrapper with tenacity retry
  - `_build_snippets_text()` — concatenate + truncate to 4000 chars
  - `_parse_enrichment()` — Mistral JSON call with Langfuse tracing
  - `enrich_lead()` — orchestrator
- Add `ENRICHMENT_PROMPT` to `app/pipeline/prompts.py`

### Phase 3: Pipeline Integration & Drafter Update
- Refactor `_process_article()` in `runner.py` — split into two session blocks with enrichment between
- Import and call `enrich_lead()`, merge results into `Lead()` constructor
- Update `DRAFTING_PROMPT` with new placeholders
- Update `draft_email()` in `drafter.py` with None-safe enriched field handling

### Phase 4: Tests & Fixes
- Fix stale `mock_gnews` in `tests/test_pipeline.py`
- Add `mock_enrich_lead` to pipeline integration test
- Create `tests/test_enricher.py` with 7 unit tests

## Final Status

(Updated after implementation completes)
