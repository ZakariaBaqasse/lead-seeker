# Plan: Data Source Enhancement

## Overview

The lead discovery pipeline currently suffers from poor lead yield. The root cause is twofold: too few RSS feeds (only 3), and an overly aggressive keyword filter that requires **both** a narrow AI keyword (`"genai"`, `"generative ai"`, `"generative artificial intelligence"`) **and** a funding keyword to match. This causes most relevant articles to be silently discarded before they ever reach the LLM extractor.

This plan addresses both problems: expanding the RSS feed list and replacing the brittle keyword filter with a tiered approach that differentiates between funding-dedicated and general-purpose feeds.

### Goals

- Increase the volume of relevant articles reaching the LLM extractor by 5-10x
- Add funding-focused RSS feeds (tech.eu, VentureBeat, Crunchbase News, TechFundingNews) that produce high quality, pre-filtered content
- Replace the current rigid `_is_relevant()` filter with a tiered system that is looser for funding-focused feeds and broader for general feeds
- Leverage RSS `<category>` metadata when available to improve filtering signal
- Keep Mistral API costs reasonable by not sending obviously irrelevant articles (Apple earnings, crypto drama, etc.) to the extractor

### Success Criteria

- [ ] RSS feed list expanded from 3 to 7+ feeds covering EU and US startup funding
- [ ] Keyword filter broadened: AI keywords expanded to include `"AI"` (word-boundary), `"artificial intelligence"`, `"machine learning"`, `"LLM"`, `"deep learning"`, `"foundation model"`
- [ ] Funding keywords expanded to include `"investment"`, `"round"`, `"backed"`, `"million"`, `"venture"`
- [ ] Funding-focused feeds (tech.eu, sifted, eu-startups, techfundingnews, crunchbase news) only require funding keyword OR a funding-related `<category>` tag to pass through
- [ ] General feeds (TechCrunch, VentureBeat) require both AI + funding keywords (using the broadened lists)
- [ ] RSS `<category>` tags parsed and used as a supplementary filter signal
- [ ] All existing tests pass; new tests cover the tiered filter logic
- [ ] Pipeline integration test updated to reflect any new source registration
- [ ] Logged metrics show increased article throughput from RSS sources

### Out of Scope

- ProductHunt API integration (separate future effort)
- YC Directory scraping (separate future effort)
- Changes to the LLM extractor prompt or `filter_lead()` in `filter.py`
- Changes to SerpAPI or GNews source fetchers
- Changes to the `enrich_article_body()` fetcher or the drafter

## Current State Analysis

### Current RSS feed list (`backend/app/pipeline/sources/rss_feeds.py`)

| Feed                    | Type               | Notes                                               |
| ----------------------- | ------------------ | --------------------------------------------------- |
| `techcrunch.com/feed/`  | General tech       | High volume (~50 articles/day), most are irrelevant |
| `sifted.eu/feed`        | EU startup funding | Already curated for EU startups, low volume         |
| `eu-startups.com/feed/` | EU startup funding | Already curated, low volume                         |

### Current filter logic

```python
AI_KEYWORDS = ["genai", "generative ai", "generative artificial intelligence"]
FUNDING_KEYWORDS = ["funding", "raises", "raised", "seed", "series a", "series b", "secures"]

def _is_relevant(text: str) -> bool:
    lower = text.lower()
    has_ai = any(kw in lower for kw in AI_KEYWORDS)
    has_funding = any(kw in lower for kw in FUNDING_KEYWORDS)
    return has_ai and has_funding  # requires BOTH
```

**Problem:** The AI keywords are extremely narrow. An article titled _"AI startup raises $10M Series A"_ is filtered out because `"AI"` doesn't match any of `["genai", "generative ai", "generative artificial intelligence"]`. The same happens for articles mentioning "artificial intelligence", "machine learning", or "LLM".

Additionally, funding-focused feeds like sifted.eu already curate their content to startup funding news — requiring an AI keyword match on top is wasteful since the LLM extractor already classifies `is_relevant` and `sector`.

### Pipeline flow (for context)

```
RSS fetch → _is_relevant() filter → [articles] → enrich_article_body() → extract_article() (Mistral)
→ filter_lead() → is_duplicate() → store Lead → draft_email() (Mistral)
```

The `_is_relevant()` filter sits at the earliest stage. Articles rejected here never reach the extractor. The downstream `filter_lead()` in `filter.py` enforces hard criteria (sector, region, employee count, funding recency) on the **extracted** data, so false positives from a looser RSS filter get caught there without wasting email drafting tokens.

**Cost model:** Mistral extraction call costs ~$0.002-0.01 per article (mistral-small). Even sending 20 extra articles/day costs $0.04-0.20/day. Missing good leads costs far more in opportunity.

## Technical Approach

### Feed Tiering

Feeds are classified into two tiers based on their content curation:

- **`funding`** — Feeds that already curate for startup funding/investment news (sifted, eu-startups, tech.eu, techfundingnews, crunchbase news). For these, we only check for **funding signal** (keywords or category tags). The AI/sector filtering is delegated to the LLM extractor.

- **`general`** — Feeds that cover broad tech news (TechCrunch, VentureBeat). For these, we require **both** AI signal **and** funding signal using the broadened keyword lists.

### Category tag parsing

RSS feeds like tech.eu embed `<category>` tags (e.g., `"Artificial Intelligence"`, `"Fintech"`). These are free metadata that can substitute for keyword matching. If a `<category>` tag matches an AI or funding term, it counts as a signal.

### Data model change

The `RSS_FEEDS` list changes from `list[tuple[str, str]]` to `list[tuple[str, str, str]]` where the third element is the feed tier (`"funding"` or `"general"`).

### Components

- **`backend/app/pipeline/sources/rss_feeds.py`**: Main file being modified. Expanded feed list, new keyword lists, tiered `_is_relevant()` logic, category tag extraction.
- **`backend/tests/test_rss_filter.py`**: New test file for the RSS filter logic (unit tests for `_is_relevant`, `_has_ai_signal`, `_has_funding_signal`, category parsing).
- **`backend/tests/test_pipeline.py`**: Update existing pipeline integration test mock patches if runner imports change.

## Implementation Phases

### Phase 1: Expand RSS feed list and add feed tiering

1. Update `RSS_FEEDS` list to include new feeds with tier classification (file: `backend/app/pipeline/sources/rss_feeds.py`)
   - Add `("https://tech.eu/feed", "tech_eu", "funding")`
   - Add `("https://venturebeat.com/feed/", "venturebeat", "general")`
   - Add `("https://techfundingnews.com/feed/", "techfundingnews", "funding")`
   - Add `("https://news.crunchbase.com/feed/", "crunchbase_news", "funding")`
   - Add tier to existing feeds: `techcrunch` → `"general"`, `sifted` → `"funding"`, `eu_startups` → `"funding"`
2. Update `fetch_rss_feeds()` to unpack the new tuple format and pass tier to the filter function

### Phase 2: Broaden keyword lists and implement tiered filter

1. Expand `AI_KEYWORDS` to a broader list and add a compiled regex for word-boundary matching on short terms like `"AI"` (file: `backend/app/pipeline/sources/rss_feeds.py`)
   - New AI terms: `"ai"` (word-boundary regex `\bai\b`), `"artificial intelligence"`, `"machine learning"`, `"llm"`, `"deep learning"`, `"foundation model"`, `"genai"`, `"generative ai"`, `"generative artificial intelligence"`, `"large language model"`
   - Keep funding keywords but add: `"investment"`, `"round"`, `"backed"`, `"million"`, `"venture"`, `"capital"`, `"pre-seed"`
2. Add `_has_ai_signal(text, categories)` helper — returns `True` if any AI keyword is found in text or categories
3. Add `_has_funding_signal(text, categories)` helper — returns `True` if any funding keyword is found in text or categories
4. Replace `_is_relevant(text)` with `_is_relevant(text, categories, tier)`:
   - If `tier == "funding"`: return `_has_funding_signal(text, categories)` (AI check delegated to LLM extractor)
   - If `tier == "general"`: return `_has_ai_signal(text, categories) and _has_funding_signal(text, categories)`
5. Update `fetch_rss_feeds()` to extract `<category>` tags from each RSS item and pass them to `_is_relevant()`

### Phase 3: Tests

1. Create `backend/tests/test_rss_filter.py` with unit tests:
   - `_has_ai_signal()` matches broad terms (`"AI startup"`, `"machine learning"`, `"LLM-powered"`)
   - `_has_ai_signal()` does NOT match `"said"`, `"email"`, `"failover"` (word-boundary check for `"ai"`)
   - `_has_funding_signal()` matches funding terms in text and categories
   - `_is_relevant()` with `tier="funding"` passes funding-only articles without AI keywords
   - `_is_relevant()` with `tier="general"` requires both signals
   - `_is_relevant()` uses category tags as supplementary signal
   - Edge cases: empty text, empty categories, None values
2. Update `backend/tests/test_pipeline.py` to fix mock patches if the runner import list changed (currently references `fetch_google_news` and `fetch_yc_directory` which don't exist in the runner)
3. Run full test suite to confirm no regressions

## Testing Strategy

- **Unit tests** for `_has_ai_signal()`, `_has_funding_signal()`, `_is_relevant()` covering:
  - Positive matches for all new AI keywords (including word-boundary `\bai\b`)
  - False positive prevention: `"said"` should not trigger AI match, `"aided"` should not trigger AI match
  - Category tag matching independent of text content
  - Tier behavior: `funding` tier requires only funding signal, `general` tier requires both
  - Empty/missing inputs
- **Integration test** (`test_pipeline.py`): ensure the pipeline still runs end-to-end with mocked sources
- **Manual verification**: run the pipeline once with real feeds and inspect logs for articles passed/rejected counts per feed

## Risks

| Risk                                                                               | Impact | Mitigation                                                                                                                         |
| ---------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| New RSS feeds return 403 or require auth                                           | Medium | Each feed wrapped in try/except, failure logged and skipped. Pipeline never aborts. Verified tech.eu feed is accessible.           |
| Broad `\bai\b` regex causes false positives on general feeds                       | Low    | Only used in conjunction with funding keywords on general feeds. LLM extractor + `filter_lead()` catch false positives downstream. |
| VentureBeat feed has high volume (~30/day) and inflates Mistral costs              | Low    | Still filtered by both AI + funding keywords. At $0.01/call, even 20 extra articles cost $0.20/day.                                |
| Word-boundary regex `\bai\b` is case-insensitive and may match unexpected patterns | Low    | Test suite covers edge cases. The `re.IGNORECASE` flag is explicitly used.                                                         |
| RSS feed XML format varies (Atom vs RSS 2.0)                                       | Medium | New feeds verified to use standard RSS 2.0 `<item>` structure. Atom feeds would need different parsing — not in scope.             |

## Open Questions

_None — all questions resolved during discovery._

## Assumptions

- All new RSS feeds use standard RSS 2.0 format with `<item>`, `<title>`, `<link>`, `<description>`, and optionally `<category>` elements. Verified for tech.eu.
- Mistral extraction cost per article remains ~$0.002-0.01 (mistral-small model).
- The existing `filter_lead()` in `filter.py` is sufficient to catch false-positive articles that pass the loosened RSS filter — no changes needed there.
- The existing pipeline integration test in `test_pipeline.py` has stale mock patches (`fetch_google_news`, `fetch_yc_directory`) that need to be fixed regardless of this change.

## Review Feedback

_(Updated during plan review rounds)_

## Final Status

_(Updated after implementation completes — outcome, known issues, deviations from plan)_
