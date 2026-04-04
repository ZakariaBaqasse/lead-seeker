# Lead Seeker — Product Requirements Document

## 1. Overview

**Product Name:** Lead Seeker

**Purpose:** A personal lead generation tool that automatically discovers recently funded GenAI startups in Europe and the USA, gathers intel about them, drafts personalized outreach emails, and provides a dashboard to track outreach status and follow-ups.

**Target User:** Solo freelancer/contractor (single-user app, no multi-tenancy).

**Hosting:** Self-hosted on an existing $5/month Contabo VPS.

---

## 2. Problem Statement

Finding and qualifying leads manually — scanning news, identifying CTOs, looking up emails, writing personalized pitches — takes significant daily effort. This tool automates the discovery and email drafting steps so the user can focus on the human parts: reviewing drafts, sending emails, and closing deals.

---

## 3. Target Lead Profile

| Criteria        | Value                                                    |
| --------------- | -------------------------------------------------------- |
| Company size    | 10–50 employees                                          |
| Region          | Europe and USA                                           |
| Sector          | Generative AI / GenAI                                    |
| Funding recency | Received significant funding within the last 6–12 months |
| Contact target  | CTO (or equivalent technical decision-maker)             |

---

## 4. Goals & Non-Goals

### Goals

- Discover at least 10 qualifying startups per day automatically.
- Gather contextual intel (funding amount, recent news, company description) for each lead.
- Draft a personalized outreach email for each lead using an LLM.
- Provide a dashboard to review leads, edit drafts, and track outreach status.
- Keep costs at $0/month (aside from existing VPS) until revenue is generated.

### Non-Goals

- The app will **not** send emails automatically (MVP). The user sends emails manually.
- No multi-user support, authentication, or role-based access.
- No mobile app or responsive-first design — desktop browser is sufficient.

---

## 5. Phased Approach

### Phase 1 — MVP (Free)

- **Startup discovery:** Automated via multiple free sources — Google News RSS, GNews API (100 free req/day), Y Combinator Startup Directory, and RSS feeds from funding-focused publications (TechCrunch, EU-Startups, Sifted). Results are merged, deduplicated, and filtered by sector, region, company size, and funding recency.
- **CTO identification & email:** Manual. The dashboard presents a lead card with placeholder fields for LinkedIn URL and email that the user fills in themselves.
- **Email drafting:** Automated via Mistral API using company context (name, funding amount, news headline, sector).
- **Dashboard:** Lead management with status tracking (Draft → Sent → Replied / Archived).

### Phase 2 — Paid Enrichment (Post-Revenue)

- Plug in **Crunchbase API** (~$29/month) for structured startup discovery with reliable filtering by company size, sector, region, and funding round — replacing the news-based scraping approach.
- Plug in **Apollo.io API** ($49/month) to auto-populate CTO name, LinkedIn URL, and email.
- The manual input fields become auto-filled; the rest of the pipeline stays identical.

---

## 6. Features

### 6.1 Daily Lead Discovery Pipeline

- Runs automatically once per day via a scheduled job.
- Sources (aggregated and deduplicated):
  - **Google News RSS:** Targeted search queries (e.g., `"GenAI" AND ("seed" OR "Series A" OR "Series B") AND "2025"`).
  - **GNews API:** Structured news search with keyword, date, and country filters (100 free requests/day).
  - **Y Combinator Startup Directory:** Filter by industry (AI), region, batch, and company size via their JSON endpoint.
  - **Publication RSS feeds:** TechCrunch, Sifted, EU-Startups for European/US funding announcements.
- For each discovered article/entry:
  - **Step 1 — LLM extraction:** Feed the raw article text and/or headline to Mistral API to extract structured fields as JSON: company name, company domain, funding amount, funding round, funding date, employee count estimate, region, sector, and a 2–3 sentence company summary. Discard if Mistral cannot confidently extract a company name or funding event.
  - **Step 2 — Filter:** Discard if sector is not GenAI, region is not Europe/USA, employee count is outside 10–50, or funding date is older than 12 months.
  - **Step 3 — Deduplicate:** Skip if company domain or name already exists in the database.
  - **Step 4 — Store:** Save as a new lead with status `draft`.
  - **Step 5 — Draft email:** Call Mistral API to generate a personalized outreach email using the extracted context.
- Target: process 20–30 raw articles per day to yield ≥ 10 qualifying leads.

### 6.2 Dashboard

A single-page web UI with the following views:

**Lead List View**

- Table/card list of all leads, sortable and filterable by status, date, region.
- Each lead displays: company name, CTO name, email, LinkedIn URL, funding amount, funding date, status, created date, last contacted date.
- Quick-action buttons: advance status, view/edit email draft, archive.

**Lead Detail View**

- Full lead information with all gathered intel (news headline, funding details, company description).
- Editable fields: CTO name, CTO email, LinkedIn URL, notes.
- Email draft (editable text area) — the user can review and tweak before copying to send.
- Status controls to advance the lifecycle.

**Status Lifecycle**

```
Draft → Sent → Replied (Won) / Replied (Lost) → Archived
```

- **Draft:** Lead discovered, email drafted, awaiting user review.
- **Sent:** User has sent the email and marked it as sent (sets `sent_at` timestamp).
- **Replied (Won):** Positive reply received — lead converted.
- **Replied (Lost):** Negative reply received — lead closed.
- **Archived:** Lead removed from active pipeline (manual action).

### 6.3 Email Drafting (LLM)

- Uses Mistral API.
- Input context per lead: company name, CTO name (if available), funding amount, funding date, news headline/summary, company sector, company region, **plus the full freelancer profile context from `config/profile.yaml`** (see §6.5).
- Mistral selects the most relevant portfolio project to highlight based on the company's sector and needs.
- Output: a personalized cold outreach email that includes: a tailored opening referencing the company's recent funding, a relevant portfolio project with its demo video link as proof of work, and a concrete engagement proposition (time-bound, outcome-focused).
- Estimated cost: ~$0.01–$0.05 per email at current Mistral API rates.

### 6.4 LLM-Based Article Extraction

- Uses Mistral API to parse unstructured news article text into structured lead data.
- Runs as the first step in the daily pipeline, before filtering or deduplication.
- **Input:** Raw article text (headline + body snippet from RSS/GNews/scrape).
- **Output:** JSON object with the following fields:

```json
{
  "company_name": "Acme AI",
  "company_domain": "acme.ai",
  "funding_amount": "$12M",
  "funding_round": "Series A",
  "funding_date": "2026-03-15",
  "employee_count_estimate": 30,
  "region": "Europe",
  "country": "France",
  "sector": "GenAI",
  "summary": "Acme AI builds generative models for enterprise document automation. They raised a $12M Series A led by Index Ventures.",
  "is_relevant": true
}
```

- If `is_relevant` is `false` or required fields (company name, funding amount, funding date) are missing, the article is discarded without storing.
- Extraction and email drafting are **two separate Mistral calls** per lead to keep prompts focused and outputs reliable.
- Estimated extraction cost: ~$0.001–$0.005 per article at current Mistral API rates.

### 6.5 Freelancer Profile Configuration

- A static YAML file (`config/profile.yaml`) maintained manually by the user. It serves as the sole source of personal context injected into every email draft.
- **No upload UI, no LLM extraction from a resume** — the user writes it once and edits it as needed.
- Structure:

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

- The email drafting prompt receives the full profile. Mistral picks the single most relevant project to feature based on the target company's sector.
- The file is loaded at application startup and cached in memory; no database storage needed.

---

## 7. Tech Stack

| Layer          | Technology                                |
| -------------- | ----------------------------------------- |
| Backend        | Python, FastAPI                           |
| Database       | PostgreSQL                                |
| ORM/Migrations | SQLAlchemy + Alembic                      |
| Scheduler      | APScheduler (embedded in FastAPI process) |
| HTTP Client    | httpx (async)                             |
| LLM            | MIstral API                               |
| Frontend       | SvelteKit                                 |
| Hosting        | Contabo VPS ($5/month, existing)          |

**Why APScheduler over Celery:** The workload is light (~10 leads/day, under 2 minutes of processing). APScheduler runs inside the FastAPI process with no external dependencies (no Redis, no separate worker). Celery would be overkill.

---

## 8. Data Model

### `leads` Table

| Column                | Type      | Description                                    |
| --------------------- | --------- | ---------------------------------------------- |
| `id`                  | UUID / PK | Primary key                                    |
| `company_name`        | VARCHAR   | Name of the startup                            |
| `company_domain`      | VARCHAR   | Company website domain (for dedup)             |
| `company_description` | TEXT      | Brief company description                      |
| `region`              | VARCHAR   | Country or region (Europe/USA)                 |
| `employee_count`      | INTEGER   | Estimated headcount                            |
| `funding_amount`      | VARCHAR   | Funding round amount (e.g., "$5M")             |
| `funding_date`        | DATE      | Date of funding announcement                   |
| `funding_round`       | VARCHAR   | Round type (Seed, Series A, etc.)              |
| `news_headline`       | TEXT      | Source article headline                        |
| `news_url`            | VARCHAR   | Source article URL                             |
| `cto_name`            | VARCHAR   | CTO name (manual in Phase 1, auto in Phase 2)  |
| `cto_email`           | VARCHAR   | CTO email (manual in Phase 1, auto in Phase 2) |
| `linkedin_url`        | VARCHAR   | CTO LinkedIn profile URL (manual in Phase 1)   |
| `status`              | VARCHAR   | Current lifecycle status (see §6.2)            |
| `email_draft`         | TEXT      | Generated outreach email draft                 |
| `notes`               | TEXT      | Free-form user notes                           |
| `sent_at`             | TIMESTAMP | When the user marked the email as sent         |
| `created_at`          | TIMESTAMP | Record creation time                           |
| `updated_at`          | TIMESTAMP | Last modification time                         |

---

## 9. API Endpoints (Backend)

| Method | Path                         | Description                                           |
| ------ | ---------------------------- | ----------------------------------------------------- |
| GET    | `/api/leads`                 | List leads (with filters: status, region, date range) |
| GET    | `/api/leads/{id}`            | Get single lead detail                                |
| PATCH  | `/api/leads/{id}`            | Update lead fields (CTO info, notes, status)          |
| DELETE | `/api/leads/{id}`            | Archive/delete a lead                                 |
| POST   | `/api/leads/{id}/regenerate` | Regenerate email draft via Mistral API                |
| GET    | `/api/stats`                 | Dashboard summary stats (counts by status)            |
| POST   | `/api/pipeline/run`          | Manually trigger the daily discovery pipeline         |

---

## 10. Scheduled Jobs

| Job                  | Schedule | Description                                                                         |
| -------------------- | -------- | ----------------------------------------------------------------------------------- |
| Daily Lead Discovery | Once/day | Fetch articles → LLM extraction → filter → deduplicate → store leads → draft emails |

---

## 11. Data Sources (Phase 1 — Free)

| Need                | Source                          | Cost                  | Notes                                                   |
| ------------------- | ------------------------------- | --------------------- | ------------------------------------------------------- |
| Startup discovery   | Google News RSS                 | Free                  | General funding news queries for GenAI startups         |
| Startup discovery   | GNews API                       | Free                  | 100 req/day, structured JSON, keyword + date filters    |
| Startup discovery   | Y Combinator Directory          | Free                  | YC-backed companies, filterable by industry/region/size |
| Startup discovery   | TechCrunch, Sifted, EU-Startups | Free                  | RSS feeds for funding announcements                     |
| Company filtering   | Article content extraction      | Free                  | Parse employee count, region, sector from text          |
| LLM data extraction | Mistral API                     | ~$0.001–0.005/article | Extract structured fields from raw article text         |
| CTO name & email    | Manual entry by user            | Free                  | User fills in from LinkedIn/web search                  |
| Email drafting      | Mistral API                     | ~$0.01–0.05/email     | Minimal cost at 10/day                                  |

### Phase 2 Additions

| Need              | Source         | Cost      | Notes                                                         |
| ----------------- | -------------- | --------- | ------------------------------------------------------------- |
| Startup discovery | Crunchbase API | $29/month | Structured data: company size, funding rounds, sector, region |
| CTO name & email  | Apollo.io      | $49/month | 10,000 exports/month, one API call per lead                   |
| Backup enrichment | Hunter.io      | Free/paid | 25 free searches/month as fallback                            |

---

## 12. Constraints & Assumptions

- The user is the sole operator. No user table or auth system is needed — access is protected by HTTP Basic Auth at the SvelteKit layer. The FastAPI backend is bound to localhost only and is not publicly exposed.
- The VPS already runs other projects — the app should be lightweight and not compete for resources.
- The app must be served over HTTPS to ensure Basic Auth credentials are encrypted in transit.
- News scraping must respect robots.txt and rate limits.
- Email drafts are reviewed and sent manually — no automated sending in the MVP.
- Mistral API key is provided by the user via environment variable.
- The quality of lead discovery depends on the coverage and freshness of news RSS sources; some qualifying startups may be missed.

---

## 13. Success Metrics

| Metric                           | Target                           |
| -------------------------------- | -------------------------------- |
| Leads discovered per day         | ≥ 10 qualifying leads            |
| Time from discovery to draft     | < 5 minutes (automated)          |
| Manual effort per lead (Phase 1) | ~3–4 minutes (CTO lookup + send) |
| Manual effort per lead (Phase 2) | < 1 minute (review + send)       |
| First client acquisition         | Within first 2 months of use     |

---

## 14. Future Considerations (Out of Scope for MVP)

- Follow-up reminder system: daily check for leads in "Sent" status older than 3 days, auto-generate follow-up drafts, send digest email to user.
- Automated email sending (e.g., Gmail API integration).
- Multi-channel outreach (LinkedIn DMs).
- Lead scoring / prioritization based on funding size or company growth signals.
- CRM integration (HubSpot, Pipedrive).
- Team/multi-user support.
- Analytics on outreach performance (open rates, reply rates).
