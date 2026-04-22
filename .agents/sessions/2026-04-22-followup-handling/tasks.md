# Tasks: Follow-Up Handling

## Phase 1: Data Model and Configuration

- [ ] 1.1 — Extend `LeadStatus` enum with `no_response`; restrict `LeadUpdate.status` to exclude `no_response`; update `LeadOut` to expose 6 new follow-up fields (`backend/app/schemas/lead.py`)
- [ ] 1.2 — Add 6 follow-up fields + `follow_up_count` check constraint (0–2) to SQLAlchemy `Lead` model (`backend/app/models/lead.py`)
- [ ] 1.3 — Create Alembic migration for new columns, check constraint, and composite index on `(status, follow_up_ready, follow_up_due_date)` + index on `follow_up_due_date` (`backend/alembic/versions/003_add_followup_fields.py`)
- [ ] 1.4 — Add `FOLLOW_UP_SCHEDULE_HOUR`, `FOLLOW_UP_SCHEDULE_MINUTE`, `FOLLOW_UP_TIMEZONE`, `FOLLOW_UP_BUSINESS_DAYS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` to `config.py` (`backend/app/config.py`)
- [ ] 1.5 — Update `StatsOut` to include `no_response` field; update `stats.py` endpoint to count `no_response` leads (`backend/app/schemas/pipeline.py`, `backend/app/api/stats.py`)

## Phase 2: Backend Follow-Up Domain Logic

- [ ] 2.1 — Create `backend/app/pipeline/followups.py` with: `add_business_days()`, `get_due_leads()`, `get_no_response_leads()` query helpers
- [ ] 2.2 — Extend `PATCH /api/leads/{id}` to: initialize follow-up state on first `draft→sent` transition; reject `no_response` as input; reject reopening terminal leads to `sent`; clear follow-up flags when transitioning to terminal outcomes (`backend/app/api/leads.py`)
- [ ] 2.3 — Add `POST /api/leads/{id}/follow-ups/mark-sent` endpoint with atomic transactional logic: recheck preconditions, increment `follow_up_count`, reset `follow_up_due_date`, clear `follow_up_ready` (`backend/app/api/leads.py`)

## Phase 3: Draft Generation and Scheduled Automation

- [ ] 3.1 — Add `FOLLOW_UP_PROMPT` and `FOLLOW_UP_CRITIQUE_PROMPT` (or a single prompt) for follow-up drafting to `prompts.py` (`backend/app/pipeline/prompts.py`)
- [ ] 3.2 — Add `draft_follow_up_email(lead_data, profile, follow_up_number)` function in `drafter.py` reusing the Mistral retry wrapper (`backend/app/pipeline/drafter.py`)
- [ ] 3.3 — Create `backend/app/notifications/telegram.py` with `send_followup_digest(ready_leads, no_response_leads)` using httpx and best-effort delivery
- [ ] 3.4 — Extend `followups.py` with `run_followup_job(session)` orchestrator: no-response transitions → draft generation → mark ready → Telegram digest; register second APScheduler job in `main.py` (`backend/app/pipeline/followups.py`, `backend/app/main.py`)

## Phase 4: Frontend Workflow and UX

- [ ] 4.1 — Add `no_response` to `LeadStatus` type; add 6 follow-up fields to `Lead` interface; add `no_response` to `StatsResponse` (`frontend/src/lib/types.ts`)
- [ ] 4.2 — Add follow-up section (count, due date, draft text, mark-sent button) to lead detail page; add `markFollowUpSent` form action (`frontend/src/routes/leads/[id]/+page.server.ts`, `frontend/src/routes/leads/[id]/+page.svelte`)
- [ ] 4.3 — Add `no_response` to status filter dropdown and stats display on dashboard (`frontend/src/routes/+page.svelte`, `frontend/src/routes/+page.server.ts`)
- [ ] 4.4 — Add styling for `no_response` status badge (`frontend/src/lib/components/StatusBadge.svelte`)

## Phase 5: Validation and Documentation

- [ ] 5.1 — Add `backend/tests/test_followups.py` with: business-day calculation tests (weekday, Friday→Wednesday, weekend edge cases, TZ boundary), follow-up eligibility, no-response eligibility, idempotency
- [ ] 5.2 — Extend `backend/tests/test_api.py` with: first-send initializes follow-up metadata, mark-sent increments count and resets due date, reply outcomes stop loop, manual PATCH cannot set `no_response`, terminal-to-sent reopen rejected, duplicate submission prevention
- [ ] 5.3 — Update `README.md` or backend README with new env vars (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `FOLLOW_UP_*`) and operational notes
