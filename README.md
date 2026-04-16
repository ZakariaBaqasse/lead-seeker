# Lead Seeker

A personal, single-user lead generation tool that auto-discovers recently funded GenAI startups (EU & USA, 10–50 employees), drafts personalized cold outreach emails via the Mistral API, and provides a dashboard to manage outreach status.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Setup & Running](#setup--running)
  - [Full Stack (Docker)](#full-stack-docker)
  - [Backend (local)](#backend-local)
  - [Frontend (local)](#frontend-local)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Overview

Lead Seeker automates the most tedious parts of a freelancer's business development workflow:

1. **Discovery** — A daily pipeline scrapes Google News RSS, GNews API, Y Combinator Directory, and niche RSS feeds (TechCrunch, EU-Startups, Sifted), deduplicates results, and filters by sector (GenAI), region (EU/USA), company size (10–50), and funding recency (≤12 months).
2. **Extraction** — A first Mistral LLM call parses raw articles into structured lead data (company name, domain, funding amount, region, employee count, etc.).
3. **Drafting** — A second Mistral LLM call generates a personalized cold email using lead context and your freelancer profile (`backend/config/profile.yaml`).
4. **Dashboard** — A SvelteKit frontend lets you review leads, edit email drafts, and track outreach status (`draft → sent → replied_won / replied_lost / archived`).

There is no email sending — you copy the draft and send it manually. There is no authentication beyond HTTP Basic Auth enforced in SvelteKit hooks; FastAPI is only reachable from localhost.

---

## Architecture

```
Browser → SvelteKit (Basic Auth in hooks.server.ts)
        → +page.server.ts / src/lib/api.ts  (server-side only)
        → FastAPI  (X-API-Key, localhost only)
        → PostgreSQL
```

- The browser **never** talks directly to FastAPI.
- Secrets (`API_SECRET_KEY`, `MISTRAL_API_KEY`) live only on the server side.
- APScheduler is embedded in the FastAPI process — no separate task queue.

---

## Tech Stack

| Layer     | Technology                                                                                   |
| --------- | -------------------------------------------------------------------------------------------- |
| Backend   | Python 3.12, FastAPI, SQLAlchemy (async), asyncpg, APScheduler, Mistral API, tenacity, httpx |
| Frontend  | SvelteKit (Svelte 5 runes), TailwindCSS v4, Bun                                              |
| Database  | PostgreSQL 16                                                                                |
| Packaging | uv (backend), Bun (frontend)                                                                 |
| Container | Docker Compose                                                                               |

---

## Project Structure

```
lead-seeker/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app + APScheduler lifespan
│   │   ├── config.py             # Pydantic Settings
│   │   ├── auth.py               # X-API-Key global dependency
│   │   ├── db.py                 # Async SQLAlchemy engine
│   │   ├── profile.py            # profile.yaml loader (lru_cache)
│   │   ├── api/                  # Route handlers (leads, pipeline, stats)
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   └── pipeline/             # Discovery → extraction → filter → draft
│   │       └── sources/          # gnews, google_news, rss_feeds, yc_directory
│   ├── alembic/                  # DB migrations
│   ├── config/
│   │   └── profile.yaml          # Your freelancer profile (injected into every draft)
│   └── tests/
├── frontend/
│   └── src/
│       ├── hooks.server.ts       # Basic Auth enforcement
│       ├── lib/api.ts            # Server-side FastAPI client
│       └── routes/               # SvelteKit pages
├── docs/                         # PRD, TDD, roadmaps — primary design reference
└── docker-compose.yaml
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/) (for full-stack)
- [uv](https://docs.astral.sh/uv/) (for local backend development)
- [Bun](https://bun.sh/) (for local frontend development)
- [direnv](https://direnv.net/) (for environment variable management)

---

## Environment Variables

This project uses [direnv](https://direnv.net/) with a `.envrc` file at the repo root to manage environment variables. Create `.envrc` in the project root:

```bash
# .envrc — managed by direnv, never commit this file

# --- PostgreSQL ---
export POSTGRES_USER=root
export POSTGRES_PASSWORD=your-postgres-password
export POSTGRES_DB=leadseeker

# --- Backend (FastAPI) ---
export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:54320/${POSTGRES_DB}"
export API_SECRET_KEY=your-random-secret-key          # shared between FastAPI and SvelteKit
export MISTRAL_API_KEY=your-mistral-api-key
export GNEWS_API_KEY=your-gnews-api-key               # free tier: 100 req/day
export PIPELINE_SCHEDULE_HOUR=6                        # UTC hour to run daily pipeline
export PIPELINE_SCHEDULE_MINUTE=0

# --- Frontend (SvelteKit) ---
export BACKEND_URL=http://localhost:8000               # FastAPI base URL (server-side)
export APP_PASSWORD=your-basic-auth-password           # HTTP Basic Auth password
export PORT=5173
```

Then allow and load it:

```bash
direnv allow
```

> **Note:** When running via Docker Compose, the values are picked up automatically from your shell environment (exported by direnv). The `DATABASE_URL` inside Docker uses the `db` service hostname instead of `localhost`.

---

## Setup & Running

### Full Stack (Docker)

```bash
# Start all services (db, api, frontend)
docker compose up

# Start with hot-reload sync (frontend file watching)
docker compose watch
```

Services exposed:

| Service  | URL                   |
| -------- | --------------------- |
| Frontend | http://localhost:5173 |
| API      | http://localhost:8080 |
| Database | localhost:54320       |

### Backend (local)

```bash
cd backend

# Install dependencies
uv sync

# Apply migrations
uv run alembic upgrade head

# Start dev server
uv run uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

Before first run, update `config/profile.yaml` with your name, title, pitch, and skills — this file is injected into every email draft generated by the pipeline.

### Frontend (local)

```bash
cd frontend

# Install dependencies
bun install

# Start dev server
bun run dev
```

Frontend will be at `http://localhost:5173`. Requires the backend and database to be running.

---

## Database Migrations

```bash
cd backend

# Apply all pending migrations
uv run alembic upgrade head

# Create a new migration after model changes
uv run alembic revision --autogenerate -m "describe your change"
```

---

## Testing

```bash
cd backend

# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_api.py

# Run a specific test by name
uv run pytest tests/test_pipeline.py::test_filter_by_employee_count -v
```

---

## Documentation

All design and implementation references live in [`docs/`](docs/):

| File                                                           | Description                                                                             |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| [`docs/PRD.md`](docs/PRD.md)                                   | Product Requirements Document — goals, lead profile, status lifecycle, data model       |
| [`docs/Technical-Design-Doc.md`](docs/Technical-Design-Doc.md) | Architecture, DB schema, full API spec, pipeline implementation notes, prompt templates |
| [`docs/Backend-Roadmap.md`](docs/Backend-Roadmap.md)           | Phased backend implementation plan with per-file acceptance criteria                    |
| [`docs/Frontend-Roadmap.md`](docs/Frontend-Roadmap.md)         | Frontend implementation plan and component breakdown                                    |
| [`docs/Design-system.md`](docs/Design-system.md)               | UI design system: color palette, typography, spacing, component patterns                |
