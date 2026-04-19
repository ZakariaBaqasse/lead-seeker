# Plan: Lead Enrichment via Tavily Search

## Overview

Add an automated enrichment step to the lead pipeline that uses Tavily web search to populate CTO name, LinkedIn URL, employee count, product description, and tech stack for each new lead — before the email is drafted. This eliminates manual research and enables the drafter to produce more targeted, personalized emails.

### Goals

- Auto-populate `cto_name` and `linkedin_url` (currently always NULL) via web search
- Add `product_description` and `tech_stack` fields to capture what the company builds and with what technologies
- Ground-truth `employee_count` from web data (currently LLM-estimated from news articles)
- Feed enriched data into the drafting prompt so emails reference the CTO by name, mention the company's actual product, and align with their tech stack
- Keep enrichment best-effort: failure never blocks lead creation or pipeline progress

### Success Criteria

- [ ] Tavily search runs for each new lead that passes filters and DB dedup
- [ ] CTO name and LinkedIn URL extracted when available in search results
- [ ] Product description and tech stack extracted and stored
- [ ] Employee count updated from web data when available
- [ ] Drafter prompt uses enriched fields (CTO name, product, tech stack)
- [ ] Enrichment failure is graceful — lead is stored with whatever data is available
- [ ] Pipeline metrics track enrichment stats (enriched count, enrichment errors)
- [ ] Tavily API key configurable via `.env` (enrichment skipped when key is absent)
- [ ] Unit tests cover enricher logic, parsing, and failure modes
- [ ] DB migration adds new columns without breaking existing data

### Out of Scope

- CTO email lookup (unreliable from search, risks spammy appearance)
- Real-time re-enrichment of existing leads (manual re-enrichment endpoint can be added later)
- Tavily credit usage tracking/dashboard (user monitors via Tavily dashboard)
- Frontend display changes for new fields (tracked separately — frontend already has `cto_name`/`linkedin_url` in types; `product_description`/`tech_stack` display will be a follow-up)

---

## Technical Approach

### Search Strategy

Two Tavily searches per lead (2 credits total, `search_depth="basic"`):

1. **People search**: `"<company_name> CTO OR founder OR CEO LinkedIn"`
   - Targets: CTO/founder name, LinkedIn profile URL
   - LinkedIn URLs identifiable by `linkedin.com/in/` pattern in result URLs
   - `max_results=5`, `search_depth="basic"` (1 credit)

2. **Company intel search**: `"<company_name> product technology stack what does <company_name> do <company_name> number of employees"`
   - Targets: product description, technology stack, employee count
   - `max_results=5`, `search_depth="basic"` (1 credit)

### Result Parsing

One Mistral call (JSON mode) to parse combined Tavily snippets into structured `EnrichmentResult`:

- **Input**: concatenated search result titles + content snippets from both searches, **truncated to 4000 characters max** to control token cost
- **Output**: JSON with `cto_name`, `linkedin_url`, `employee_count`, `product_description`, `tech_stack`
- Same model (`mistral-small-2603`) and retry pattern as the extractor
- Langfuse tracing span named `enrichment-llm-call` for observability
- Prompt explicitly instructs: _"Return null for any field you are not confident about. Prefer no data over wrong data."_

This follows the existing project pattern: web API fetches raw data → Mistral structures it.

### Why `tavily-python` SDK (not raw `httpx`)

The existing codebase uses `httpx.AsyncClient` for all HTTP calls. For Tavily, we use the official `tavily-python` SDK instead because:

- It provides `AsyncTavilyClient` with native async support
- It handles auth, pagination, response parsing, and error types out of the box
- Tavily's REST API is undocumented for direct use — the SDK is the supported interface
- This is a search-specific integration (like `mistralai` SDK), not a generic HTTP call

### Pipeline Integration Point

Current flow:

```
fetch → dedup → extract → filter → DB dedup → store → draft
```

New flow:

```
fetch → dedup → extract → filter → DB dedup → enrich → store → draft
```

#### Session Management Refactoring

The current `_process_article()` in `runner.py` performs DB dedup and Lead insertion in a **single `async with AsyncSessionLocal()` block**. Since enrichment involves external API calls (Tavily + Mistral), it cannot run inside a DB session. The function will be refactored to:

```python
async def _process_article(article, profile):
    # ... extract + filter (no session needed) ...

    # Session 1: dedup check only
    async with AsyncSessionLocal() as session:
        if await is_duplicate(session, extraction):
            return 0, 0, None

    # Enrichment (external API calls, no DB session)
    enrichment = await enrich_lead(extraction)

    # Session 2: insert lead + draft email
    async with AsyncSessionLocal() as session:
        lead = Lead(
            # ... base fields from extraction ...
            # ... enriched fields merged in ...
        )
        session.add(lead)
        await session.commit()
        # ... draft email ...
```

This splits the single session block into two: one for the dedup read and one for the insert+draft. The enrichment runs between them with no open DB connection.

### Data Types

| Field                 | Python Type (Schema) | DB Column Type                 | Rationale                                                                                                                 |
| --------------------- | -------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `cto_name`            | `Optional[str]`      | `String(255)` — already exists | Person name                                                                                                               |
| `linkedin_url`        | `Optional[str]`      | `String(500)` — already exists | URL                                                                                                                       |
| `employee_count`      | `Optional[int]`      | `Integer` — already exists     | Overwritten with enriched value                                                                                           |
| `product_description` | `Optional[str]`      | `Text`                         | Free-form description of what the company builds                                                                          |
| `tech_stack`          | `Optional[str]`      | `Text`                         | Comma-separated string (e.g., `"Python, PyTorch, React, AWS"`) — simple, directly usable in prompts without serialization |

`tech_stack` is stored as `Text` (comma-separated) rather than `JSONB`/`ARRAY` because:

- The drafter prompt consumes it as plain text — no parsing needed
- The frontend displays it as a string — no array rendering needed
- Avoids JSON serialization complexity for what is essentially display text

### Failure Handling

- **Tavily searches**: tenacity retry (3 attempts, exponential backoff 2–10s). On final failure, that search returns empty results.
- **Mistral parsing**: same retry pattern as extractor. On failure, return `None`.
- **Complete enrichment failure** → return `None`, lead proceeds with extraction data only (CTO name, LinkedIn, product description, tech stack all remain NULL).
- **Partial results** (e.g., found CTO but not tech stack) → return `EnrichmentResult` with available fields, NULLs for missing.
- **Tavily API key not configured** → skip enrichment entirely, log at INFO level (not WARNING — this is a valid configuration).

### Drafter Prompt Updates

The `DRAFTING_PROMPT` in `prompts.py` will be updated to include enriched fields:

**New placeholders**: `{cto_name}`, `{product_description}`, `{tech_stack}`

**None-handling strategy**: The `draft_email()` function builds the prompt with conditional sections. When enriched fields are `None`, the prompt falls back to current behavior:

- `cto_name` is `None` → prompt uses `"the founding team"` instead of the name
- `product_description` is `None` → prompt uses `summary` (existing extraction summary)
- `tech_stack` is `None` → tech stack section omitted from prompt

**Prompt changes**:

- STARTUP CONTEXT section gets three new fields:
  ```
  - CTO/Founder: {cto_name} (or "Unknown — address the founding team")
  - Product: {product_description} (or the existing summary)
  - Tech Stack: {tech_stack} (or "Not available")
  ```
- EMAIL CONSTRAINTS section adds: _"If CTO name is provided, address the email to them directly. If tech stack is known, reference it when describing your relevant experience."_
- Example email greeting changes from `"Hi [Founder/CTO Name]"` to showing both the named and unnamed variants.

---

## Implementation Phases

### Phase 1: Schema, Config & Migration

Foundation work — no behavioral changes yet.

1. Add `TAVILY_API_KEY: str = ""` to `Settings` in `app/config.py` (files: `app/config.py`)
2. Add `tavily-python` dependency to `pyproject.toml` (files: `pyproject.toml`)
3. Add `product_description` (`Text`, nullable) and `tech_stack` (`Text`, nullable) columns to Lead model (files: `app/models/lead.py`)
4. Add `product_description` and `tech_stack` fields to `LeadOut` schema (files: `app/schemas/lead.py`)
5. Create `EnrichmentResult` Pydantic schema with fields: `cto_name: Optional[str]`, `linkedin_url: Optional[str]`, `employee_count: Optional[int]`, `product_description: Optional[str]`, `tech_stack: Optional[str]` — all Optional (files: `app/schemas/lead.py`)
6. Create Alembic migration `002_add_enrichment_columns` adding `product_description` and `tech_stack` columns to `leads` table (files: `alembic/versions/002_add_enrichment_columns.py`)
7. Add `product_description: string | null` and `tech_stack: string | null` to frontend `Lead` interface (files: `frontend/src/lib/types.ts`)

### Phase 2: Enricher Module

Core enrichment logic — new file, no existing code changes yet.

1. Create `app/pipeline/enricher.py` with three functions:
   - `_search_tavily(query: str) → list[dict]` — `AsyncTavilyClient` search wrapper with tenacity retry (3 attempts, exponential backoff). Returns list of result dicts `{title, url, content}`. On final failure, returns `[]`.
   - `_build_snippets_text(people_results: list[dict], company_results: list[dict]) → str` — concatenates titles + content from both search results, **truncated to 4000 characters**.
   - `_parse_enrichment(snippets_text: str, company_name: str) → EnrichmentResult | None` — Mistral JSON call to structure raw snippets. Uses `mistral-small-2603`, JSON mode, tenacity retry. Returns `None` on failure.
   - `enrich_lead(extraction: ExtractionResult) → EnrichmentResult | None` — orchestrator: checks `TAVILY_API_KEY`, runs both searches concurrently via `asyncio.gather()`, combines results, calls Mistral parser. Returns `None` on any failure. (files: `app/pipeline/enricher.py`)
2. Add `ENRICHMENT_PROMPT` to `app/pipeline/prompts.py` — instructs Mistral to extract CTO name, LinkedIn URL (prefer `linkedin.com/in/` URLs), employee count, product description (1-2 sentences), and tech stack (comma-separated) from search snippets. Includes: _"Return null for any field you are not confident about. If multiple people are named, prefer the CTO over CEO over founder. Only include tech stack items you are reasonably sure about."_ (files: `app/pipeline/prompts.py`)
3. Add Langfuse tracing to the enrichment Mistral call — span name `enrichment-llm-call`, consistent with `extraction-llm-call` and `drafting-llm-call` patterns (files: `app/pipeline/enricher.py`)

### Phase 3: Pipeline Integration & Drafter Update

Wire enrichment into the pipeline and update email drafting.

1. Refactor `_process_article()` in `runner.py` — split single session block into two (dedup check → enrichment → insert+draft), as described in the session management section above (files: `app/pipeline/runner.py`)
2. Import and call `enrich_lead()` between dedup check and lead insertion. Merge enrichment results into `Lead()` constructor: `cto_name`, `linkedin_url`, `product_description`, `tech_stack`, and override `employee_count` if enrichment provides one (files: `app/pipeline/runner.py`)
3. Update `lead_data` dict passed to `draft_email()` to include `cto_name`, `product_description`, `tech_stack` (files: `app/pipeline/runner.py`)
4. Update `DRAFTING_PROMPT` in `prompts.py` with new placeholders and conditional sections as described in the Drafter Prompt Updates section (files: `app/pipeline/prompts.py`)
5. Update `draft_email()` in `drafter.py` to pass enriched fields to the prompt, with None-safe defaults: `cto_name or "the founding team"`, `product_description or summary`, `tech_stack or "Not available"` (files: `app/pipeline/drafter.py`)

### Phase 4: Tests & Fixes

1. Fix stale mock in `tests/test_pipeline.py`: remove `mock_gnews` (no longer imported in `runner.py`), add `mock_enrich_lead` for the new enrichment step (files: `tests/test_pipeline.py`)
2. Create `tests/test_enricher.py` with unit tests:
   - `test_enrich_lead_success` — mock Tavily + Mistral → returns full `EnrichmentResult`
   - `test_enrich_lead_partial_results` — mock Tavily returns only people results, no company intel → partial `EnrichmentResult` with CTO but no tech stack
   - `test_enrich_lead_tavily_failure` — mock Tavily raises → returns `None`
   - `test_enrich_lead_mistral_failure` — mock Tavily succeeds, Mistral fails → returns `None`
   - `test_enrich_lead_skipped_no_api_key` — patch `settings.TAVILY_API_KEY` to `""` → returns `None`, no API calls made
   - `test_snippets_truncated` — verify `_build_snippets_text()` caps output at 4000 chars
   - `test_linkedin_url_extraction` — verify Mistral prompt correctly extracts `linkedin.com/in/` URLs from mixed results
     (files: `tests/test_enricher.py`)
3. Update `tests/test_pipeline.py` integration test to mock `enrich_lead` and verify enriched fields appear on the created lead (files: `tests/test_pipeline.py`)

---

## Testing Strategy

### Unit Tests (`test_enricher.py`)

- Mock `AsyncTavilyClient.search()` and Mistral API at the function level
- Verify correct search queries are constructed from `ExtractionResult` data
- Verify `EnrichmentResult` parsing from various Tavily response shapes
- Verify graceful degradation on partial results (some fields null)
- Verify `None` return on complete failure (both Tavily and Mistral)
- Verify enrichment skipped when `settings.TAVILY_API_KEY == ""` (patch the setting)
- Verify snippet truncation at 4000 chars

### Integration Tests (`test_pipeline.py`)

- Mock Tavily + Mistral + enricher in pipeline flow
- Verify enriched fields appear on stored leads
- Verify pipeline completes successfully even when enrichment fails
- Fix stale `fetch_gnews` mock (no longer imported)

### Edge Cases

- Company name with special characters in search query (e.g., `"AI.co"`, `"Über-Tech"`)
- Tavily returns empty results for both searches → `EnrichmentResult` is `None`
- Tavily returns results but Mistral can't parse them → `None`
- LinkedIn URL in result URL field vs. mentioned in snippet text
- Multiple people found (CTO vs CEO vs founder) — prompt instructs Mistral to prefer CTO
- Very long Tavily snippets — truncated to 4000 chars before Mistral call
- Tavily returns CTO of a **different company** with a similar name — prompt instructs "return null if not confident"

---

## Risks

| Risk                                     | Impact                             | Mitigation                                                                              |
| ---------------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------- |
| Tavily free tier exhaustion (1000/month) | Enrichment stops working           | Skip enrichment when key absent; 2 calls/lead stays within budget for ~15 leads/day     |
| Tavily returns irrelevant results        | Bad CTO name / product data stored | Mistral parsing prompt: "return null if not confident"; human reviews before sending    |
| Wrong person identified as CTO           | Email addressed to wrong person    | Prompt: "prefer CTO, return null if ambiguous"; user verifies before sending            |
| Mistral misparses search snippets        | Wrong structured data              | JSON mode + explicit schema in prompt; tenacity retry; same proven pattern as extractor |
| Enrichment adds latency (~3-5s/lead)     | Pipeline runs slower               | Acceptable for daily batch pipeline; runs within existing semaphore limit               |
| Rate limiting by Tavily                  | Temporary failures                 | Tenacity retry with exponential backoff handles transient rate limits                   |

---

## Assumptions

- Tavily `search_depth="basic"` (1 credit) returns sufficient data for CTO/product extraction in most cases
- Mistral `mistral-small-2603` is capable of extracting structured data from search snippets (same model used for article extraction, proven reliable)
- 2 Tavily searches per lead is the right balance between data quality and credit usage
- Frontend display of new fields (`product_description`, `tech_stack`) will be a separate follow-up task
- The existing `cto_email` field on the Lead model remains user-editable but is NOT auto-populated by enrichment
- `tech_stack` stored as comma-separated `Text` is sufficient — no need for `JSONB`/`ARRAY`

### Future Optimization (not in this plan)

- Add `cto_name` to `ExtractionResult` so the extraction LLM attempts to pull leadership names from the funding article itself. When found, skip the Tavily people search → halves credit usage. Deferred because it requires changing the extraction prompt (risk of regressions) and funding articles rarely mention CTO by name.

---

## Review Feedback

### Round 1 (Reviewer Subagent)

**Changes applied:**

1. **Session management** — added detailed refactoring plan showing split into two session blocks with enrichment between them
2. **`tech_stack` type** — defined as `Optional[str]` / `Text` (comma-separated), with rationale for choosing over `JSONB`/`ARRAY`
3. **Drafter prompt changes** — detailed new placeholders, None-handling strategy, and specific prompt modifications
4. **Snippet truncation** — set 4000 char limit for concatenated Tavily snippets
5. **Stale test fix** — added Phase 4 step 1 to fix `fetch_gnews` mock in `test_pipeline.py`
6. **`tavily-python` rationale** — added section explaining SDK choice over raw `httpx`
7. **Wrong-person risk** — added to risk table
8. **Test absent-key path** — specified `settings.TAVILY_API_KEY` patching approach

**Deferred:** Extracting CTO from article (future optimization, noted in Assumptions section).

---

## Final Status

(Updated after implementation completes — outcome, known issues, deviations from plan)
