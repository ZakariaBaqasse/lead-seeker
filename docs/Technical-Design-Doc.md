# Lead Seeker — Technical Design Document

## 1. Overview

This document describes the technical architecture, component design, trade-offs, and known risks for Lead Seeker. It is a blueprint for implementation and assumes familiarity with the [PRD](./PRD.md).

---

## 2. Non-Goals (Scope Guard)

The following are explicitly out of scope for this implementation to prevent creep:

- No email sending — the app copies drafts to clipboard/screen; the user sends manually.
- No authentication system — no users table, sessions, JWTs, or OAuth flows. HTTP Basic Auth only.
- No Celery, Redis, or task queues — APScheduler embedded in the FastAPI process is sufficient.
- No resume parsing or file upload — profile context comes from a static YAML file only.
- No real-time updates — the dashboard is polled on load/refresh, no WebSockets.
- No scraping of LinkedIn — CTO details are filled in manually by the user in Phase 1.
- No mobile layout — desktop browser only.
- No multi-tenancy, no team features.

---

## 3. System Architecture

### 3.1 High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Contabo VPS                          │
│                                                             │
│  ┌──────────────┐   HTTPS    ┌─────────────────────────┐   │
│  │   Traefik    │◄──────────►│   SvelteKit (port 3000) │   │
│  │  (Dokploy-   │            │   - Basic Auth hook      │   │
│  │   managed,   │            │   - Server-side routes   │   │
│  │   TLS/SSL)   │            │   - Dashboard UI         │   │
│  └──────────────┘            └──────────┬──────────────┘   │
│                                         │ HTTP (localhost)  │
│                              ┌──────────▼──────────────┐   │
│                              │   FastAPI (port 8000)    │   │
│                              │   - REST API endpoints   │   │
│                              │   - APScheduler jobs     │   │
│                              │   - Pipeline logic       │   │
│                              └──────────┬──────────────┘   │
│                                         │                   │
│                         ┌───────────────┼───────────────┐  │
│                         │               │               │  │
│               ┌─────────▼──┐   ┌────────▼──────┐  ┌────▼────────────┐  │
│               │ PostgreSQL │   │  Mistral API  │  │  News Sources   │  │
│               │ (leads DB) │   │  (external)   │  │  (external)     │  │
│               └────────────┘   └───────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Daily Pipeline Flow

```
APScheduler (once/day)
        │
        ▼
┌───────────────────┐
│  Fetch articles   │  ← Google News RSS, GNews API,
│  from all sources │    YC Directory, TechCrunch/Sifted/EU-Startups RSS
└────────┬──────────┘
         │ raw article text (20–30 items)
         ▼
┌───────────────────┐
│  LLM Extraction   │  ← Mistral API call #1 per article
│  (Mistral)        │    Output: structured JSON or discard
└────────┬──────────┘
         │ structured fields
         ▼
┌───────────────────┐
│  Filter           │  ← sector=GenAI, region=EU/USA,
│                   │    employees=10–50, funding ≤ 12mo
└────────┬──────────┘
         │ qualifying leads
         ▼
┌───────────────────┐
│  Deduplicate      │  ← check company_domain / company_name
│                   │    against existing DB records
└────────┬──────────┘
         │ new leads only
         ▼
┌───────────────────┐
│  Store lead       │  ← INSERT into leads table, status='draft'
│  (PostgreSQL)     │
└────────┬──────────┘
         │ lead context + profile.yaml
         ▼
┌───────────────────┐
│  Draft email      │  ← Mistral API call #2 per lead
│  (Mistral)        │    Personalized outreach + proof-of-work project
└────────┬──────────┘
         │ email_draft
         ▼
┌───────────────────┐
│  Update lead      │  ← UPDATE leads SET email_draft = ...
│  (PostgreSQL)     │
└───────────────────┘
```

### 3.3 Request Flow (Dashboard)

```
Browser
  │  HTTPS request
  ▼
Traefik (TLS termination, managed by Dokploy)
  │  HTTP
  ▼
SvelteKit server
  │  Basic Auth check (hooks.server.ts) → 401 if invalid
  │  Server-side load function (+page.server.ts)
  │  HTTP request (localhost:8000)
  ▼
FastAPI
  │  Query PostgreSQL
  ▼
Response JSON → SvelteKit renders page → Browser
```

---

## 4. Project Structure

```
lead-seeker/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, APScheduler setup
│   │   ├── api/
│   │   │   ├── leads.py             # CRUD endpoints
│   │   │   ├── pipeline.py          # Manual trigger endpoint
│   │   │   └── stats.py             # Dashboard stats endpoint
│   │   ├── pipeline/
│   │   │   ├── runner.py            # Orchestrates the full pipeline
│   │   │   ├── sources/
│   │   │   │   ├── google_news.py   # Google News RSS fetcher
│   │   │   │   ├── gnews.py         # GNews API fetcher
│   │   │   │   ├── yc_directory.py  # YC startup directory fetcher
│   │   │   │   └── rss_feeds.py     # TechCrunch/Sifted/EU-Startups
│   │   │   ├── extractor.py         # Mistral extraction call
│   │   │   ├── filter.py            # Filtering logic
│   │   │   └── drafter.py           # Mistral email draft call
│   │   ├── models/
│   │   │   └── lead.py              # SQLAlchemy Lead model
│   │   ├── schemas/
│   │   │   └── lead.py              # Pydantic schemas
│   │   ├── db.py                    # PostgreSQL session setup
│   │   └── profile.py               # profile.yaml loader & cache
│   ├── alembic/                     # DB migrations
│   ├── config/
│   │   └── profile.yaml             # Freelancer profile context
│   ├── .env                         # MISTRAL_API_KEY, DATABASE_URL, etc.
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── hooks.server.ts          # Basic Auth enforcement
    │   ├── routes/
    │   │   ├── +page.svelte         # Lead list view
    │   │   ├── +page.server.ts      # Server-side data load
    │   │   ├── leads/[id]/
    │   │   │   ├── +page.svelte     # Lead detail view
    │   │   │   └── +page.server.ts  # Load + form actions
    │   │   └── api/                 # SvelteKit API routes (proxy to FastAPI)
    │   └── lib/
    │       ├── components/          # Reusable UI components
    │       └── api.ts               # FastAPI client helpers
    ├── .env                         # APP_PASSWORD, BACKEND_URL
    └── package.json
```

---

## 5. Tech Stack & Trade-offs

### 5.1 Backend: FastAPI + APScheduler

| Decision      | Chosen               | Rejected              | Reason                                                     |
| ------------- | -------------------- | --------------------- | ---------------------------------------------------------- |
| Web framework | FastAPI              | Flask, Django         | Async-native, Pydantic validation, fast to write           |
| Scheduler     | APScheduler          | Celery + Redis        | No external broker needed; ~10 jobs/day is trivially light |
| HTTP client   | httpx (async)        | requests              | Non-blocking; fits FastAPI's async model                   |
| ORM           | SQLAlchemy + Alembic | raw SQL, Tortoise ORM | Familiar, mature, migration support                        |

**APScheduler trade-off:** If the FastAPI process crashes mid-pipeline, the job will not retry automatically. Acceptable for a personal tool — the next day's run will pick up new articles anyway. If robustness becomes a concern, add a simple `pipeline_runs` table to track last successful run.

### 5.2 Database: PostgreSQL

Chosen over SQLite for reliability under concurrent reads (dashboard + scheduled job running simultaneously) and easier Phase 2 migration. For this workload (< 1000 rows/month), any database would work — but PostgreSQL is already familiar and available on the VPS.

### 5.3 LLM: Mistral API

| Decision        | Chosen              | Rejected       | Reason                                                                |
| --------------- | ------------------- | -------------- | --------------------------------------------------------------------- |
| LLM provider    | Mistral             | Claude, GPT-4o | Cheaper per token; sufficient quality for extraction + email drafting |
| Calls per lead  | 2 (extract + draft) | 1 combined     | Separate prompts produce more reliable, focused outputs               |
| Response format | JSON mode           | Free text      | Structured output avoids parsing errors in the extraction step        |

**Mistral JSON mode:** Use `response_format={"type": "json_object"}` in the extraction call to guarantee parseable output. The email drafting call uses free text.

### 5.4 Frontend: SvelteKit

| Decision    | Chosen                               | Rejected                 | Reason                                                                              |
| ----------- | ------------------------------------ | ------------------------ | ----------------------------------------------------------------------------------- |
| Framework   | SvelteKit                            | Next.js, plain HTML      | Lighter than Next.js; server-side hooks ideal for Basic Auth; familiar for the user |
| Auth        | HTTP Basic Auth (hooks.server.ts)    | JWT, sessions, Lucia     | Zero overhead; browser handles the login prompt; one file, ~15 lines                |
| API pattern | Server-side load functions → FastAPI | Direct browser → FastAPI | API key never reaches the browser; FastAPI stays on localhost                       |

### 5.5 Security Model

- Traefik (managed by Dokploy) terminates TLS. SvelteKit handles Basic Auth before any route resolves.
- FastAPI is bound to `127.0.0.1:8000` — not reachable from outside the VPS.
- SvelteKit server-side functions make all FastAPI calls with an `X-API-Key` header sourced from the server-side `.env`, never exposed to the browser.
- FastAPI validates the `X-API-Key` on every request as a simple middleware check.
- No secrets stored in the database or served to the client.

```
Internet → Traefik (HTTPS, Dokploy-managed) → SvelteKit (Basic Auth) → FastAPI (API Key, localhost only)
```

---

## 6. Data Model

### `leads` table

```sql
CREATE TABLE leads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name    VARCHAR(255) NOT NULL,
    company_domain  VARCHAR(255) UNIQUE,
    company_description TEXT,
    region          VARCHAR(100),
    country         VARCHAR(100),
    employee_count  INTEGER,
    funding_amount  VARCHAR(50),
    funding_date    DATE,
    funding_round   VARCHAR(50),
    news_headline   TEXT,
    news_url        VARCHAR(500),
    cto_name        VARCHAR(255),
    cto_email       VARCHAR(255),
    linkedin_url    VARCHAR(500),
    status          VARCHAR(50) NOT NULL DEFAULT 'draft',
    email_draft     TEXT,
    notes           TEXT,
    sent_at         TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE UNIQUE INDEX idx_leads_domain ON leads(company_domain)
    WHERE company_domain IS NOT NULL;
```

**Status enum values:** `draft`, `sent`, `replied_won`, `replied_lost`, `archived`

**Deduplication strategy:** `company_domain` has a unique index (partial, excluding NULLs). If domain is unavailable, a case-insensitive match on `company_name` is used as fallback before insert.

---

## 7. API Design

All endpoints are prefixed `/api/`. SvelteKit's server-side functions are the only callers — browsers never hit FastAPI directly.

### Leads

| Method   | Path                         | Request                                                     | Response                        |
| -------- | ---------------------------- | ----------------------------------------------------------- | ------------------------------- |
| `GET`    | `/api/leads`                 | `?status=&region=&from=&to=&page=&limit=`                   | `{ items: Lead[], total: int }` |
| `GET`    | `/api/leads/{id}`            | —                                                           | `Lead`                          |
| `PATCH`  | `/api/leads/{id}`            | `{ cto_name?, cto_email?, linkedin_url?, notes?, status? }` | `Lead`                          |
| `DELETE` | `/api/leads/{id}`            | —                                                           | `204`                           |
| `POST`   | `/api/leads/{id}/regenerate` | —                                                           | `{ email_draft: string }`       |

### Pipeline & Stats

| Method | Path                   | Description                                  |
| ------ | ---------------------- | -------------------------------------------- |
| `POST` | `/api/pipeline/run`    | Manually trigger the full discovery pipeline |
| `GET`  | `/api/pipeline/status` | Last run time, leads found, errors           |
| `GET`  | `/api/stats`           | Counts by status for dashboard summary cards |

### Authentication (internal)

FastAPI reads `X-API-Key` from every request header. A simple dependency:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(key: str = Security(api_key_header)):
    if key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=403)
```

---

## 8. Pipeline Implementation Notes

### 8.1 Source Fetchers

Each source is an independent async function returning a list of `RawArticle(headline, body_snippet, url, source_name)`. They run concurrently via `asyncio.gather()`.

```python
async def run_pipeline():
    raw_articles = await asyncio.gather(
        fetch_google_news(),
        fetch_gnews(),
        fetch_yc_directory(),
        fetch_rss_feeds(),
    )
    articles = dedupe_by_url([a for batch in raw_articles for a in batch])
    ...
```

### 8.2 LLM Extraction Prompt (sketch)

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

Use `response_format={"type": "json_object"}` to guarantee parseable output. Wrap the call in a try/except — if JSON parsing fails, discard and log the article.

### 8.3 Email Drafting Prompt (sketch)

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

### 8.4 Rate Limiting & Error Handling

- GNews API: 100 req/day hard limit — cap fetcher to 80 requests to leave headroom.
- Mistral API: wrap all calls in exponential backoff (`tenacity` library, 3 retries).
- If a single article extraction fails, log and continue — do not abort the full pipeline run.
- Store last pipeline run metadata (start time, articles processed, leads created, errors) in a `pipeline_runs` table for observability.

---

## 9. Freelancer Profile Loading

```python
# app/profile.py
import yaml
from functools import lru_cache

@lru_cache(maxsize=1)
def get_profile() -> dict:
    with open("config/profile.yaml") as f:
        return yaml.safe_load(f)
```

Loaded once at startup via `lru_cache`. To reload after editing `profile.yaml` without restarting the app, add a `POST /api/profile/reload` endpoint that calls `get_profile.cache_clear()`.

---

## 10. Deployment

### Services on VPS

| Service    | How                                                              | Port                  |
| ---------- | ---------------------------------------------------------------- | --------------------- |
| FastAPI    | Dokploy app, `uvicorn app.main:app --host 127.0.0.1 --port 8000` | 8000 (localhost only) |
| SvelteKit  | Dokploy app, `node build`                                        | Traefik-routed        |
| Traefik    | Managed by Dokploy — no manual config needed                     | 80 → 443              |
| PostgreSQL | Dokploy-managed service                                          | 5432 (localhost only) |

### Traefik / Dokploy Notes

No manual reverse proxy configuration is needed. Dokploy handles:

- Automatic TLS certificate provisioning via Let's Encrypt.
- Routing the public domain to the SvelteKit container.
- HTTP → HTTPS redirect.

The only required Dokploy configuration is setting the public domain on the SvelteKit service. FastAPI is **not** exposed via Traefik — it stays internal with no public domain assigned, only reachable inside the VPS network.

### Environment Variables

**Backend (`backend/.env`)**

```
DATABASE_URL=postgresql://user:pass@localhost:5432/leadseeker
MISTRAL_API_KEY=...
API_SECRET_KEY=...          # shared secret with SvelteKit
```

**Frontend (`frontend/.env`)**

```
APP_PASSWORD=...            # Basic Auth password
BACKEND_URL=http://127.0.0.1:8000
API_SECRET_KEY=...          # same as backend
```

---

## 11. Risks & Mitigations

| Risk                                                                                 | Likelihood | Impact | Mitigation                                                                                                                                                  |
| ------------------------------------------------------------------------------------ | ---------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **News sources yield < 10 qualifying leads/day**                                     | High       | Medium | Tune search queries; add more RSS sources; lower the bar on employee count filtering if volume is consistently low                                          |
| **Mistral extraction produces wrong/hallucinated fields** (e.g., wrong funding date) | Medium     | Medium | Show all extracted fields on the lead detail page for the user to verify before sending; do not auto-discard borderline cases — flag them for manual review |
| **GNews 100 req/day limit hit**                                                      | Medium     | Low    | Cap requests to 80; Google News RSS and publication RSS feeds are unlimited and provide most coverage                                                       |
| **Duplicate leads from multiple sources**                                            | High       | Low    | Dual deduplication: URL-level before extraction (cheap) + domain/name-level after extraction (DB query)                                                     |
| **APScheduler job silently fails**                                                   | Low        | Medium | Log job start/end/errors to `pipeline_runs` table; surface last run status in the dashboard header                                                          |
| **Mistral API cost overrun**                                                         | Low        | Low    | Budget is ~$0.15/day at full volume; set a Mistral spend alert at $10/month                                                                                 |
| **VPS resource contention** (pipeline + other projects)                              | Low        | Low    | Pipeline runs at a fixed off-peak time (e.g., 06:00 UTC); completes in < 2 minutes                                                                          |
| **Basic Auth credentials intercepted**                                               | Low        | High   | Enforced HTTPS via Traefik + Let's Encrypt (managed by Dokploy) eliminates this; FastAPI is not exposed via Traefik — internal only                         |
| **profile.yaml edited to empty/invalid during run**                                  | Low        | Low    | Validate YAML schema at startup and on `/api/profile/reload`; reject malformed files                                                                        |
