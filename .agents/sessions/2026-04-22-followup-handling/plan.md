# Plan: Follow-Up Handling

## Overview

Implement automated follow-up handling for Lead Seeker. The feature extends the manual outreach workflow by preparing follow-up drafts for leads that were contacted but haven't replied, after 3 business days. The app does NOT send emails automatically — it generates drafts, marks them ready, and sends a Telegram digest. Exactly 2 follow-ups per lead are supported.

### Goals

- Add an automated weekday follow-up job alongside the existing weekday discovery pipeline
- Generate follow-up drafts automatically after 3 business days with no reply
- Notify the user via a single Telegram digest per scheduled run
- Keep lead lifecycle understandable by separating follow-up progression from the main lead status

### Success Criteria

- [ ] Leads in `sent` status become eligible for follow-up after 3 business days with no reply
- [ ] Scheduler generates follow-up 1 and follow-up 2 drafts automatically (never more than 2)
- [ ] User can manually mark a generated follow-up as sent, restarting the 3-business-day timer
- [ ] Leads move to `no_response` only after follow-up 2 has been sent and another 3 business days pass
- [ ] Telegram sends one digest message per follow-up run containing newly ready follow-ups
- [ ] Existing discovery, lead management, and manual email flow continue to work without regression

### Out of Scope

- Automatic email sending
- Public-holiday calendars beyond Monday-Friday
- Multi-user notification preferences
- Full CRM sequencing beyond 2 follow-ups
- Tracking email opens/clicks/inbox responses automatically

## Technical Approach

### Key Design Decisions

- `no_response` is a new terminal `LeadStatus` value (automation-only, not manually settable)
- Follow-up state tracked via 6 new fields on `Lead`: `last_contact_at`, `follow_up_count`, `follow_up_due_date`, `follow_up_ready`, `follow_up_generated_at`, `follow_up_draft`
- Business-day calculations in `Africa/Casablanca` timezone (date-based, not hour-based)
- APScheduler second cron job for follow-up runner (weekdays only, `Africa/Casablanca`)
- Telegram delivery is best-effort: failures do not roll back DB state
- All critical transitions are atomic (recheck preconditions inside transaction)
- Separate API endpoint `POST /api/leads/{id}/follow-ups/mark-sent` for follow-up send confirmation

### Components

- **`backend/app/schemas/lead.py`**: Add `no_response` to `LeadStatus`; update `LeadOut` with new fields; restrict `LeadUpdate` to exclude `no_response`
- **`backend/app/models/lead.py`**: Add 6 new follow-up fields with check constraint on `follow_up_count`
- **`backend/alembic/versions/*`**: New migration for columns, constraint, indexes
- **`backend/app/config.py`**: Add `FOLLOW_UP_SCHEDULE_HOUR`, `FOLLOW_UP_SCHEDULE_MINUTE`, `FOLLOW_UP_TIMEZONE`, `FOLLOW_UP_BUSINESS_DAYS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- **`backend/app/pipeline/followups.py`**: Business-day utils, due-lead selection, no-response transitions, follow-up runner
- **`backend/app/notifications/telegram.py`**: Telegram Bot API digest delivery
- **`backend/app/pipeline/drafter.py`**: New `draft_follow_up_email()` function
- **`backend/app/pipeline/prompts.py`**: Follow-up prompt templates
- **`backend/app/api/leads.py`**: Extend `PATCH` for first-send follow-up init; add `POST /api/leads/{id}/follow-ups/mark-sent`
- **`backend/app/main.py`**: Register second APScheduler cron job
- **`backend/app/schemas/pipeline.py`** + **`backend/app/api/stats.py`**: Expose `no_response` in stats
- **`frontend/src/lib/types.ts`**: Add `no_response` to `LeadStatus`, follow-up fields to `Lead`, `StatsResponse`
- **`frontend/src/routes/leads/[id]/+page.svelte`** + **`+page.server.ts`**: Follow-up section and action button
- **`frontend/src/routes/+page.svelte`**: Add `no_response` filter and stats
- **`frontend/src/lib/components/StatusBadge.svelte`**: Style `no_response`

## Implementation Phases

### Phase 1: Data Model and Configuration

1. Extend `LeadStatus` with `no_response`, restrict `LeadUpdate` (files: `backend/app/schemas/lead.py`)
2. Add 6 follow-up fields + check constraint to the SQLAlchemy `Lead` model (files: `backend/app/models/lead.py`)
3. Create Alembic migration for new columns, check constraint, and indexes (files: `backend/alembic/versions/003_add_followup_fields.py`)
4. Add follow-up and Telegram settings to `config.py` (files: `backend/app/config.py`)
5. Update `LeadOut` schema to expose new fields; update `StatsOut` and `stats.py` to include `no_response` (files: `backend/app/schemas/lead.py`, `backend/app/schemas/pipeline.py`, `backend/app/api/stats.py`)

### Phase 2: Backend Follow-Up Domain Logic

1. Create `backend/app/pipeline/followups.py` with business-day utilities and eligibility queries
2. Extend `PATCH /api/leads/{id}` to initialize follow-up state on first `sent` transition and enforce terminal-state restrictions (files: `backend/app/api/leads.py`)
3. Add `POST /api/leads/{id}/follow-ups/mark-sent` endpoint with atomic follow-up-send logic (files: `backend/app/api/leads.py`)

### Phase 3: Draft Generation and Scheduled Automation

1. Add follow-up prompt templates to `backend/app/pipeline/prompts.py`
2. Add `draft_follow_up_email()` function to `backend/app/pipeline/drafter.py`
3. Create `backend/app/notifications/telegram.py` with Telegram digest delivery
4. Implement the scheduled follow-up runner in `backend/app/pipeline/followups.py` and register it in `backend/app/main.py`

### Phase 4: Frontend Workflow and UX

1. Extend `frontend/src/lib/types.ts` with `no_response`, follow-up fields, updated `StatsResponse`
2. Add follow-up section and `mark-sent` action to the lead detail page (`+page.server.ts`, `+page.svelte`)
3. Add `no_response` to dashboard filters and stats (`frontend/src/routes/+page.svelte`)
4. Style `no_response` in `StatusBadge.svelte`

### Phase 5: Validation and Documentation

1. Add tests for business-day logic, API transitions, scheduler behavior (files: `backend/tests/test_followups.py`, `backend/tests/test_api.py`)
2. Update README or docs with new environment variables and operational notes

## Testing Strategy

- Unit: business-day due-date calculation, weekend edge cases, UTC-to-local-date boundaries
- API: first-send init, follow-up mark-sent, reply/terminal outcomes stop loop, `no_response` serialization, manual PATCH cannot set `no_response`, reopening terminal leads rejected, duplicate submission prevention
- Runner: due leads become ready, already-ready skipped, count never exceeds 2, one Telegram digest per run, no message when nothing changed
- Frontend: follow-up section renders, action button works, `no_response` filter/badge

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Overloading main status with follow-up stages | High | Separate follow-up state in dedicated fields |
| Incorrect business-day calcs around TZ boundaries | High | Date-based calcs in Africa/Casablanca + explicit tests |
| Repeated generation for already-ready leads | High | Gate on `follow_up_ready = false`, test idempotency |
| Telegram failures causing lost state | Medium | Best-effort delivery, independent from DB commits |
| UI confusion between outcome status and follow-up stage | Medium | Separate section; only add `no_response` to status lists |

## Assumptions

- The product remains single-user
- Business days mean Monday-Friday only, no holiday provider
- `Africa/Casablanca` is the fixed IANA timezone
- Telegram is backend-only notification channel
- User still sends all emails manually and confirms in the app

## Final Status

✅ Implementation complete. All 5 phases delivered across 14 commits on branch `add-followup-handling`.

- 26/26 backend tests passing
- Frontend: `bun run check` — 0 errors, 0 warnings
- All business rules, atomic transitions, idempotency guards, and lifecycle restrictions implemented per spec
