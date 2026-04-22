# Lead Seeker - Follow-Up Handling Spec

## Overview

This document defines the product and technical specification for automated follow-up handling in Lead Seeker. The feature extends the existing manual outreach workflow by preparing follow-up drafts for leads that were contacted, have not replied, and have aged for 3 business days. The app does not send emails automatically. It prepares the draft, marks it ready, and notifies the user via Telegram so the user can review and send the follow-up manually.

The design supports exactly 2 follow-ups per lead. The 3-business-day timer resets after every manual send, including the first cold email and both follow-ups. If a lead still has not replied 3 business days after the second follow-up was sent, the system transitions that lead into a dedicated terminal `no_response` outcome.

### Goals

- Add an automated weekday follow-up job alongside the existing weekday discovery pipeline.
- Generate follow-up drafts automatically after 3 business days with no reply.
- Keep the lead lifecycle understandable by separating follow-up progression from the main lead status.
- Notify the user via a single Telegram digest per scheduled run.
- Preserve the current product constraint that all outbound emails are sent manually by the user.

### Success Criteria

- [ ] Leads in `sent` status become eligible for follow-up after 3 business days with no reply.
- [ ] The scheduler generates follow-up 1 and follow-up 2 drafts automatically, but never more than 2 follow-ups.
- [ ] The user can manually mark a generated follow-up as sent and restart the 3-business-day timer.
- [ ] Leads move to `no_response` only after follow-up 2 has been sent and another 3 business days pass without a reply.
- [ ] Telegram sends one digest message per follow-up run containing newly ready follow-ups.
- [ ] Existing discovery, lead management, and manual email flow continue to work without regression.

### Out of Scope

- Automatic email sending.
- Public-holiday calendars or country-specific holiday logic beyond Monday-Friday business days.
- Multi-user notification preferences or multiple Telegram recipients.
- Full CRM sequencing beyond the initial email plus 2 follow-ups.
- Tracking email opens, clicks, or inbox responses automatically.

## Product Requirements

### User Problem

After a lead is marked as contacted, the user needs a reliable way to remember when a follow-up should happen, generate a context-aware follow-up draft, and avoid manually checking every sent lead every day.

### Primary Workflow

1. A lead starts with status `draft` and a cold outreach draft in `email_draft`.
2. The user manually sends that first email and marks the lead as `sent`.
3. The backend records the outbound contact time and computes a due date 3 business days later in the `Africa/Casablanca` timezone.
4. A weekday scheduler checks for due leads.
5. If a lead is due, still in `sent`, has no reply outcome, and has sent fewer than 2 follow-ups, the backend generates the next follow-up draft, stores it, marks it ready, and includes it in a Telegram digest.
6. The user reviews the ready draft, sends it manually outside the app, and marks that follow-up as sent in the app.
7. The timer resets for another 3 business days.
8. After follow-up 2 is sent, the system waits one final 3-business-day window. If there is still no reply, the lead becomes `no_response`.

### Lifecycle Rules

- The main lead status remains outcome-oriented: `draft`, `sent`, `replied_won`, `replied_lost`, `archived`, `no_response`.
- Follow-up progress is not represented as additional main statuses such as `follow_up_ready` or `follow_up_sent`.
- A lead remains in `sent` while it is in the waiting or follow-up-ready loop.
- `replied_won`, `replied_lost`, `archived`, and `no_response` end the follow-up loop immediately.
- The system supports exactly 2 follow-ups. Once `follow_up_count = 2`, no further follow-up draft generation is allowed.
- `no_response` is an automation-only terminal outcome. It must not be manually selectable through the standard lead update flow.
- Reopening a terminal lead back into `sent` is out of scope for MVP. If needed later, it should be a dedicated reset action, not an unrestricted status edit.

### Business Day Definition

- Business days are Monday through Friday only.
- The authoritative timezone for both cron scheduling and business-day calculations is `Africa/Casablanca`.
- Due calculation is date-based rather than hour-based. The system computes a `follow_up_due_date`, not a precise due timestamp.
- Example: if the user sends on Monday, the lead becomes due on Thursday. If the user sends on Friday, the lead becomes due on Wednesday.

## Technical Approach

### Design Principles

- Keep the main status field focused on the high-level lead outcome.
- Store follow-up state as explicit fields on the lead so the scheduler logic is queryable and the UI can remain understandable.
- Reuse current backend patterns: APScheduler for cron jobs, async SQLAlchemy sessions, Pydantic schemas, and Mistral-based drafting with retries.
- Keep Telegram delivery best-effort for MVP so notification failures do not roll back lead-state mutations.

### Proposed Components

- `backend/app/main.py`: register a second weekday APScheduler job for follow-up handling.
- `backend/app/pipeline/followups.py`: own business-day calculations, due-lead selection, follow-up generation, and no-response transitions.
- `backend/app/notifications/telegram.py`: send Telegram digests through the Bot API.
- `backend/app/pipeline/drafter.py`: add a dedicated follow-up drafting path beside the existing cold-email drafting path.
- `backend/app/pipeline/prompts.py`: add one or more prompts tailored for follow-up messaging.
- `backend/app/api/leads.py`: keep generic updates narrow and add explicit follow-up send handling.

## Data Model

### Status Strategy

The current status enum should gain one new terminal value:

- `no_response`: the lead received the initial email and 2 follow-ups, still did not reply, and has aged through the final waiting window.

The existing meanings remain unchanged:

- `draft`: discovered lead, not yet contacted.
- `sent`: initial email sent and the lead is somewhere in the follow-up waiting loop.
- `replied_won`: positive reply or active opportunity.
- `replied_lost`: negative reply or explicit rejection.
- `archived`: manually archived for reasons outside the automated follow-up lifecycle.

### New Lead Fields

Add the following fields to the `leads` table:

| Field                    | Type                             | Purpose                                                                              |
| ------------------------ | -------------------------------- | ------------------------------------------------------------------------------------ |
| `last_contact_at`        | `TIMESTAMP WITH TIME ZONE NULL`  | Time the most recent outbound email was manually sent, whether initial or follow-up. |
| `follow_up_count`        | `INTEGER NOT NULL DEFAULT 0`     | Number of follow-ups already sent by the user. Valid range for MVP: 0-2.             |
| `follow_up_due_date`     | `DATE NULL`                      | Local business date when the next automation step becomes eligible.                  |
| `follow_up_ready`        | `BOOLEAN NOT NULL DEFAULT FALSE` | Whether a generated follow-up draft is currently awaiting manual send.               |
| `follow_up_generated_at` | `TIMESTAMP WITH TIME ZONE NULL`  | When the currently stored or latest follow-up draft was generated.                   |
| `follow_up_draft`        | `TEXT NULL`                      | The generated follow-up draft text. Separate from the original `email_draft`.        |

Add a hard invariant for the counter:

- database check constraint: `follow_up_count >= 0 AND follow_up_count <= 2`
- backend validation must reject any transition that would move the counter outside this range

### Field Semantics

- `sent_at` remains the timestamp of the first cold email send.
- `email_draft` remains the original cold outreach draft.
- `follow_up_draft` stores the latest generated follow-up draft and is not overwritten by the original cold email path.
- `follow_up_draft` is retained after the user marks a follow-up as sent so the user can still reference the latest generated copy.
- `follow_up_count` counts sent follow-ups, not generated follow-ups.
- The next follow-up number is derived, not stored:
  - if `follow_up_count = 0` and `follow_up_ready = true`, the ready draft is follow-up 1
  - if `follow_up_count = 1` and `follow_up_ready = true`, the ready draft is follow-up 2

### Recommended Query Support

Add indexes if needed after implementation profiling, but the initial migration should at least consider:

- index on `follow_up_due_date`
- composite index on `(status, follow_up_ready, follow_up_due_date)`

These keep the scheduled due-lead query efficient.

## Business Rules

### Initial Manual Send

When the user marks a lead as `sent` for the first time:

- set `status = sent`
- set `sent_at` if it is currently null
- set `last_contact_at = now()`
- set `follow_up_count = 0`
- set `follow_up_ready = false`
- compute `follow_up_due_date = add_business_days(local_contact_date, 3)`

For MVP, this transition is only supported from `draft` to `sent`.

### Eligible for Follow-Up Generation

A lead is eligible for automatic follow-up draft generation when all of the following are true:

- `status = sent`
- `follow_up_ready = false`
- `follow_up_due_date <= current_local_date`
- `follow_up_count < 2`

### When a Follow-Up Draft Is Generated

When the scheduler generates a follow-up draft:

- store the draft in `follow_up_draft`
- set `follow_up_ready = true`
- set `follow_up_generated_at = now()`
- do not increment `follow_up_count`
- do not change the main `status`
- include the lead in the current Telegram digest

### When the User Marks a Follow-Up as Sent

When the user manually sends a ready follow-up and confirms it in the UI:

- require `status = sent`
- require `follow_up_ready = true`
- require `follow_up_count < 2`
- increment `follow_up_count` by 1
- set `last_contact_at = now()`
- set `follow_up_ready = false`
- compute a new `follow_up_due_date = add_business_days(local_contact_date, 3)`
- keep `follow_up_draft` as the last generated copy for audit and review

### Transition to Reply or Terminal Outcomes

When the lead becomes `replied_won`, `replied_lost`, `archived`, or `no_response`:

- the follow-up loop stops immediately
- the scheduler must ignore the lead from that point forward
- `follow_up_ready` should be cleared to avoid stale UI state
- `follow_up_due_date` may be cleared because no next automation step remains
- retain `follow_up_draft` for historical reference

### Transition to `no_response`

A lead becomes `no_response` automatically when all of the following are true:

- `status = sent`
- `follow_up_count = 2`
- `follow_up_ready = false`
- `follow_up_due_date <= current_local_date`

This means the second follow-up was already sent manually and the final 3-business-day wait has elapsed without a reply.

Only the follow-up service or scheduler may perform this transition.

### Failure Handling

- If follow-up draft generation fails for a due lead, the job logs the error and leaves the lead eligible for a future run.
- If Telegram delivery fails, the job logs the error but does not roll back follow-up state changes.
- The scheduled job must be idempotent for already-ready leads. A lead with `follow_up_ready = true` must not be regenerated and must not be renotified on every run.

### Atomicity and Concurrency Rules

The feature must defend against duplicate scheduler runs, retried requests, and double submission from the UI.

- generating a ready follow-up draft must happen inside one transaction that rechecks `status = sent`, `follow_up_ready = false`, `follow_up_count < 2`, and `follow_up_due_date <= current_local_date` before the update commits
- marking a follow-up as sent must happen inside one transaction that rechecks `status = sent`, `follow_up_ready = true`, and `follow_up_count < 2` before incrementing the counter
- auto-closing to `no_response` must happen inside one transaction that rechecks `status = sent`, `follow_up_ready = false`, `follow_up_count = 2`, and `follow_up_due_date <= current_local_date`
- if those preconditions no longer hold at commit time, the operation becomes a no-op or a defined conflict response rather than mutating stale state
- duplicate manual submissions must not increment `follow_up_count` twice

## API Changes

### Existing Endpoint Behavior to Extend

`PATCH /api/leads/{id}` currently handles the first transition to `sent` and sets `sent_at`. It should also initialize follow-up timing for the first outbound send.

Recommended additional behavior when status becomes `sent`:

- set `last_contact_at`
- set `follow_up_due_date`
- clear any stale `follow_up_ready` flag

Restrictions for MVP:

- manual `PATCH` may return `no_response` in responses, but it must not accept `no_response` as an input status
- manual `PATCH` to `sent` is only valid for the first outbound send from `draft`
- reopening terminal states back to `sent` is rejected

### New Endpoint

Add an explicit endpoint for manual follow-up send confirmation:

- `POST /api/leads/{id}/follow-ups/mark-sent`

Purpose:

- mark the currently ready follow-up as manually sent
- increment the sent follow-up count
- recompute the next due date
- keep the generic `PATCH` endpoint from accumulating follow-up-specific side effects

Recommended response:

- return the updated `LeadOut`

### Optional Follow-Up Regeneration Endpoint

If the user wants manual regeneration later, add:

- `POST /api/leads/{id}/follow-ups/regenerate`

This is optional for MVP because the scheduler already generates drafts automatically.

### Schema Changes

`LeadOut` should expose:

- `last_contact_at`
- `follow_up_count`
- `follow_up_due_date`
- `follow_up_ready`
- `follow_up_generated_at`
- `follow_up_draft`

`LeadStatus` should expose the new `no_response` enum value.

`LeadUpdate.status` should be restricted to manual statuses only and exclude `no_response`.

The frontend type definitions should match the backend schema exactly.

## Scheduler Design

### New Scheduled Job

Register a second APScheduler cron job alongside the discovery pipeline:

- weekdays only: Monday-Friday
- schedule in `Africa/Casablanca`
- configurable hour and minute via environment variables
- unique job id, separate from `daily_pipeline`

Recommended settings:

- `FOLLOW_UP_SCHEDULE_HOUR`
- `FOLLOW_UP_SCHEDULE_MINUTE`
- `FOLLOW_UP_TIMEZONE= Africa/Casablanca`
- `FOLLOW_UP_BUSINESS_DAYS = 3`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

The existing discovery pipeline schedule remains unchanged in UTC unless explicitly modified in a separate task. This feature changes only the new follow-up job timezone.

### Job Execution Order

Each scheduler run should:

1. Determine the current local date in `Africa/Casablanca`.
2. Select leads that must be closed to `no_response`.
3. Apply those terminal transitions.
4. Select leads newly due for follow-up draft generation.
5. Generate follow-up drafts for eligible leads.
6. Mark those leads as ready.
7. Send one Telegram digest containing the newly ready leads and, optionally, the newly closed `no_response` leads.
8. Log a run summary.

### Idempotency Rules

- Leads already marked `follow_up_ready = true` are skipped.
- Leads in non-`sent` statuses are skipped.
- Leads with `follow_up_count >= 2` are not drafted again.
- Leads already moved to `no_response` are skipped.

## Drafting Strategy

### Why a Separate Prompt Is Required

The existing cold outreach prompt is optimized for first contact. A follow-up email has different goals:

- acknowledge prior outreach without sounding repetitive
- remain concise and low-friction
- reference the original context without repeating the full cold email
- keep the tone direct and professional rather than overly apologetic or salesy

### Follow-Up Draft Inputs

The follow-up drafting function should receive:

- lead context already used for the cold email
- original `email_draft`
- `follow_up_count` to determine whether this is follow-up 1 or 2
- the profile data from `profile.yaml`
- any available product and tech-stack context

### Drafting Output Constraints

- concise email body suitable for manual sending
- explicit sequence-aware behavior: follow-up 1 and follow-up 2 should not read the same
- no fabricated claims or metrics
- no promise of free consulting work

## Telegram Notification Design

### Notification Mode

Use one batched Telegram digest per scheduler run.

### Digest Contents

The message should include:

- run timestamp
- count of newly ready follow-ups
- per-lead list containing company name and which follow-up is ready
- optional secondary section for leads auto-closed to `no_response`

Example structure:

```text
Follow-up run complete

Ready now: 3
- Acme AI - Follow-up 1 ready
- Northstar Labs - Follow-up 2 ready
- Orbit ML - Follow-up 1 ready

Closed as no_response: 1
- Delta Vision
```

### Delivery Rules

- Send no Telegram message when nothing changed in that run, unless a verbose mode is added later.
- Do not send one message per lead.
- Log the payload or a redacted summary for observability.

## Frontend UX Specification

### Dashboard

The lead list should remain centered on main lead status and not expose follow-up stages as primary statuses.

Required changes:

- add `no_response` to dashboard status filters and stats
- optionally add a follow-up indicator column or badge showing:
  - `Follow-up 1 ready`
  - `Follow-up 2 ready`
  - `Due on <date>`
- keep the existing lead table understandable without turning it into a CRM sequence grid

### Lead Detail Page

Add a dedicated follow-up section showing:

- follow-up count sent so far
- next due date
- whether a follow-up draft is ready
- the current follow-up draft text
- a focused action button to mark the ready follow-up as sent

Recommended behavior:

- do not expose `no_response` as a normal manual selection in the status dropdown
- do expose reply outcomes and archive actions as before
- when `follow_up_ready = true`, make the next action visually obvious

### Status Badge

Add styling for the new `no_response` status.

## Observability and Logging

The follow-up job should log:

- run start and finish
- number of due leads scanned
- number of drafts generated
- number of leads auto-closed to `no_response`
- drafting failures
- Telegram delivery success or failure

If the project later needs run history comparable to `pipeline_runs`, add a dedicated `follow_up_runs` table. For MVP this is optional, not required.

## Security and Configuration

- Telegram credentials must live in backend environment variables, not in the frontend.
- FastAPI remains localhost-only; Telegram calls originate from the backend.
- No browser-side Telegram integration is required.
- The existing API-key protection model remains unchanged.

## Testing Strategy

### Unit Tests

- business-day due-date calculation in `Africa/Casablanca`
- weekend edge cases for send dates on Thursday, Friday, and Saturday
- UTC-to-local-date boundary cases around midnight in `Africa/Casablanca`
- follow-up eligibility selection logic
- no-response eligibility logic after follow-up 2
- idempotency when `follow_up_ready = true`
- validation that `follow_up_count` cannot exceed 2

### API Tests

- marking a lead `sent` initializes follow-up metadata
- marking a ready follow-up as sent increments `follow_up_count` and resets due date
- reply outcomes stop the follow-up loop
- `no_response` appears correctly in serialized output and stats
- manual `PATCH` cannot set `no_response`
- reopening terminal leads back to `sent` is rejected
- duplicate manual follow-up-send submission cannot increment the counter twice

### Runner and Scheduler Tests

- due leads generate drafts and become ready
- leads already ready are not regenerated
- follow-up count never exceeds 2
- one run creates one Telegram digest even if multiple leads are ready
- no Telegram message is sent when nothing changed
- the follow-up job uses `Africa/Casablanca` while the existing discovery job keeps its current UTC behavior
- scheduler and manual terminal updates do not race into invalid state

### Frontend Checks

- lead detail page renders the follow-up section and action button correctly
- dashboard filters can filter by `no_response`
- status badge renders `no_response` distinctly

## Risks

| Risk                                                           | Impact | Mitigation                                                                                    |
| -------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------- |
| Overloading the main status field with follow-up stages        | High   | Keep follow-up progression in separate fields and add only one new terminal status            |
| Incorrect business-day calculations around timezone boundaries | High   | Use date-based calculations in `Africa/Casablanca` and test weekend boundaries explicitly     |
| Repeated generation for already-ready leads                    | High   | Gate on `follow_up_ready = false` and test idempotency                                        |
| Telegram failures causing lost state or inconsistent runs      | Medium | Keep notification delivery best-effort and independent from DB commits                        |
| UI confusion between outcome status and follow-up stage        | Medium | Present follow-up state in a separate section and only add `no_response` to main status lists |
| Draft quality for follow-ups being too similar to cold emails  | Medium | Use dedicated follow-up prompts and sequence-aware instructions                               |

## Implementation Phases

### Phase 1: Data Model and Configuration

Goal: add the minimum backend primitives required to track follow-up state and schedule the job.

1. Extend `LeadStatus` with `no_response`.
   Files: `backend/app/schemas/lead.py`, `backend/app/api/stats.py`, `backend/app/schemas/pipeline.py`
2. Add follow-up tracking fields to the SQLAlchemy `Lead` model.
   Files: `backend/app/models/lead.py`
3. Create an Alembic migration for the new columns, constraints, and indexes.
   Files: `backend/alembic/versions/*`
4. Add follow-up and Telegram settings.
   Files: `backend/app/config.py`, backend `.env.example` or README docs if present
5. Restrict backend status mutation rules so `no_response` is automation-only and terminal-to-sent reopen is rejected for MVP.
   Files: `backend/app/schemas/lead.py`, `backend/app/api/leads.py`

Acceptance criteria:

- database migration runs cleanly
- schemas serialize the new fields
- backend enforces the follow-up invariants before any scheduler or UI work begins

### Phase 2: Backend Follow-Up Domain Logic

Goal: implement the rules that decide when leads become due, ready, sent, or closed.

1. Add business-day utilities that compute due dates in `Africa/Casablanca`.
   Files: new helper module under `backend/app/pipeline/`
2. Add due-lead selection and terminal `no_response` selection logic.
   Files: same follow-up service module
3. Extend first-send handling inside the existing lead update path.
   Files: `backend/app/api/leads.py`
4. Add explicit follow-up send confirmation endpoint.
   Files: `backend/app/api/leads.py`, `backend/app/schemas/lead.py`

Acceptance criteria:

- first send initializes follow-up state
- follow-up send increments count and resets due date
- final no-response eligibility is computed correctly

### Phase 3: Draft Generation and Scheduled Automation

Goal: create and run the automated weekday follow-up processor.

1. Add follow-up prompt templates.
   Files: `backend/app/pipeline/prompts.py`
2. Add a dedicated follow-up drafting function reusing Mistral retry behavior.
   Files: `backend/app/pipeline/drafter.py`
3. Add the scheduled follow-up runner.
   Files: `backend/app/main.py`, new follow-up runner/service module
4. Add Telegram digest delivery.
   Files: new `backend/app/notifications/telegram.py`

Acceptance criteria:

- due leads become ready automatically
- already-ready leads are skipped
- the run emits one digest message for all newly ready leads

### Phase 4: Frontend Workflow and UX

Goal: expose follow-up state and manual actions without cluttering the main lead lifecycle.

1. Extend shared frontend types.
   Files: `frontend/src/lib/types.ts`
2. Add follow-up metadata and actions to the lead detail page.
   Files: `frontend/src/routes/leads/[id]/+page.server.ts`, `frontend/src/routes/leads/[id]/+page.svelte`
3. Add `no_response` to dashboard filters and stats display.
   Files: `frontend/src/routes/+page.svelte`, relevant stats components
4. Add visual support for the new terminal status.
   Files: `frontend/src/lib/components/StatusBadge.svelte`

Acceptance criteria:

- the user can see when a follow-up is ready
- the user can mark the ready follow-up as sent
- the dashboard distinguishes `no_response` from `archived`

### Phase 5: Validation and Documentation

Goal: make the feature safe to ship and understandable to operate.

1. Add or extend backend tests for business-day logic, API transitions, and scheduled behavior.
   Files: `backend/tests/test_api.py`, new backend follow-up test modules
2. Add frontend checks where practical.
   Files: frontend test surface if present, otherwise manual verification notes in docs
3. Document operational behavior and environment variables.
   Files: `README.md`, `backend/README.md`

Acceptance criteria:

- critical lifecycle rules are covered by tests
- environment requirements are documented
- manual QA steps are written down

## Assumptions

- The product remains single-user.
- Business days mean Monday-Friday only, with no holiday provider.
- `Africa/Casablanca` is the fixed IANA timezone used for this feature.
- Telegram is used only as a backend notification channel, not an interaction surface.
- The user still sends all emails manually and confirms sent actions in the app.

## Review Feedback

- Review round 1: changes needed for backend-only `no_response` enforcement, atomic transition rules, hard follow-up-count invariants, draft lifecycle clarity, phase ordering, and explicit timezone scope.
- Review round 2: approved after those changes. One non-blocking improvement was added for UTC-to-local-date boundary tests in `Africa/Casablanca`.

## Final Status

Planning complete. Ready for review and approval before implementation.
