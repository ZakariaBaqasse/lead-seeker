# Handoff

<!-- Append a new phase section after each phase completes. -->

## Phase 1 — Schema & Config Foundation

**Status:** ✅ Complete  
**Commits:** `83f0fc7`, `830828e`, `8e692db`, `7526375`, `6f84dfb`

### What was done

| Task | File(s) | Summary |
|------|---------|---------|
| 1.1 | `app/schemas/lead.py` | Added `no_response` to `LeadStatus`; new `ManualLeadStatus` enum for `LeadUpdate.status`; added 6 follow-up fields to `LeadOut` |
| 1.2 | `app/models/lead.py` | Added 6 follow-up mapped columns; `CheckConstraint` for `follow_up_count` (0-2); 2 new indexes |
| 1.3 | `alembic/versions/003_add_followup_fields.py` | Migration adding columns, check constraint, and indexes; `down_revision = '002'` |
| 1.4 | `app/config.py` | Added `FOLLOW_UP_SCHEDULE_HOUR/MINUTE`, `FOLLOW_UP_TIMEZONE`, `FOLLOW_UP_BUSINESS_DAYS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| 1.5 | `app/schemas/pipeline.py`, `app/api/stats.py` | Added `no_response: int = 0` to `StatsOut` and populated it in the stats endpoint |

### Test result
`uv run pytest tests/test_api.py -x -q` — 1 pre-existing failure (`test_health_with_auth` returns 403; confirmed failing on `main` before any changes). No regressions introduced.

## Phase 4 — Frontend UX

**Status:** ✅ Complete  
**Commit:** `45b0c2f`

### What was done

| Task | File(s) | Summary |
|------|---------|---------|
| 4.1 | `frontend/src/lib/types.ts` | Added `no_response` to `LeadStatus`; added 5 follow-up fields to `Lead` interface; added `no_response: number` to `StatsResponse`; updated `LeadUpdate.status` to `Exclude<LeadStatus, 'no_response'>` |
| 4.2 | `frontend/src/lib/api.ts` | Added `markFollowUpSent()` function calling `POST /api/leads/{id}/follow-ups/mark-sent` |
| 4.2 | `frontend/src/routes/leads/[id]/+page.server.ts` | Added `markFollowUpSent` form action; imported new API function |
| 4.2 | `frontend/src/routes/leads/[id]/+page.svelte` | Added follow-up state (`follow_up_count`, `follow_up_due_date`, `follow_up_ready`, `follow_up_draft`); synced via `$effect`; added Follow-Up section showing status, ready banner, draft textarea with copy, and mark-sent form button |
| 4.3 | `frontend/src/routes/+page.svelte` | Added `no_response` option to status filter select |
| 4.3 | `frontend/src/routes/+page.server.ts` | Added `no_response: 0` to stats fallback; cast advance-status to `Exclude<LeadStatus, 'no_response'>` |
| 4.4 | `frontend/src/lib/components/StatusBadge.svelte` | Added `no_response` case with `bg-warning-subtle text-warning` styling |
| 4.4 | `frontend/src/lib/components/StatsHeader.svelte` | Added "No Response" stat card; updated grid to `lg:grid-cols-7` |

### Build result
`bun run check` — 0 errors, 0 warnings.

### Notes for next phases
- The follow-up section is visible when `lead.status === 'sent'` or when follow-up data exists; it shows the draft and a "Mark Follow-Up as Sent" button only when `follow_up_ready === true`.
- `no_response` is intentionally excluded from the manual status selector in the lead detail form — it can only be set by the backend scheduler.
 (from Phase 1)
- Migration `003` is ready to apply; run `uv run alembic upgrade head` against dev DB before testing follow-up logic.
- `ManualLeadStatus` is imported alongside `LeadStatus` — Phase 2 code that handles status transitions should use `LeadStatus` for reads and `ManualLeadStatus` for user-facing updates.
- Config keys are wired via `pydantic-settings`; populate `.env` with real Telegram credentials when wiring up notifications.

## Phase 2 — Business Logic & API Extensions

**Status:** ✅ Complete  
**Commits:** `d5226d2`, `aab9116`

### What was done

| Task | File(s) | Summary |
|------|---------|---------|
| 2.1 | `app/pipeline/followups.py` | New module: `add_business_days()` (Mon–Fri, Africa/Casablanca); `get_due_leads()` and `get_no_response_leads()` async query helpers |
| 2.2 | `app/api/leads.py` | Extended `PATCH /leads/{id}`: draft→sent sets `last_contact_at`, `follow_up_count=0`, `follow_up_ready=False`, `follow_up_due_date=+3 biz days`; terminal reopening to `sent` raises 422; terminal outcome transitions clear follow-up scheduling fields |
| 2.3 | `app/api/leads.py` | New `POST /leads/{id}/follow-ups/mark-sent`: validates preconditions (status=sent, ready=True, count<2); increments `follow_up_count`, resets `follow_up_ready`, advances `follow_up_due_date` by 3 business days |

### Test result
`API_SECRET_KEY=test-secret uv run pytest tests/test_api.py -x -q` — **13 passed**, 0 failures.

### Notes for Phase 3
- `add_business_days` and `get_due_leads`/`get_no_response_leads` are ready to be called from the scheduler job.
- The `mark-sent` endpoint is fully wired; frontend can call it when user confirms a follow-up was sent.
- No `with_for_update()` used (SQLite test compatibility); acceptable for single-instance deployment.

## Phase 3 — Draft Generation and Scheduled Automation

**Status:** ✅ Complete  
**Commits:** `2fa0b0c`, `c7a5a6c`, `ea59923`, `baa79af`

### What was done

| Task | File(s) | Summary |
|------|---------|---------|
| 3.1 | `app/pipeline/prompts.py` | Added `FOLLOW_UP_DRAFTING_PROMPT` (with placeholders for company_name, cto_name, follow_up_number, original_email_draft, profile_yaml_as_text, product_description, tech_stack) and `FOLLOW_UP_CRITIQUE_PROMPT` (7-point checklist; rewrites if any fail) |
| 3.2 | `app/pipeline/drafter.py` | Added `draft_follow_up_email(lead_data, profile, follow_up_number)` reusing `_call_mistral_drafting` with tenacity retry; two Mistral calls (drafting → critique/rewrite); brace-escapes profile YAML; returns None on failure |
| 3.3 | `app/notifications/__init__.py`, `app/notifications/telegram.py` | New `notifications` package; `send_followup_digest(ready_leads, no_response_leads)` using `httpx.AsyncClient(timeout=10.0)`; skips silently if Telegram credentials unconfigured; logs on HTTP errors, returns False |
| 3.4 | `app/pipeline/followups.py`, `app/main.py` | Added `run_followup_job(session)` orchestrator: (1) closes no_response leads with atomic per-lead recheck+commit, (2) generates follow-up drafts for due leads and marks ready, (3) sends Telegram digest; added `_scheduled_followup_job` wrapper and second `scheduler.add_job()` call using `FOLLOW_UP_SCHEDULE_HOUR/MINUTE/TIMEZONE` settings |

### Test result
`API_SECRET_KEY=test-secret uv run pytest tests/test_api.py -x -q` — **13 passed**, 0 failures.

### Notes for Phase 4
- `run_followup_job` is fully wired and scheduler-registered; the frontend (Phase 4) can surface `follow_up_ready`, `follow_up_draft`, and `follow_up_count` fields already present on `LeadOut`.
- Telegram is best-effort and does not affect DB state; configure `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` in backend `.env` when ready.
- `draft_follow_up_email` pulls `email_draft` from `lead_data` as the original cold email context — ensure lead_data dict includes that key when calling manually.

## Phase 5 — Validation and Documentation

**Status:** ✅ Complete  
**Commits:** `7e6f1da`, `4b59fff`

### What was done

| Task | File(s) | Summary |
|------|---------|---------|
| 5.1 | `backend/tests/test_followups.py` | Created comprehensive test file: 5 unit tests for `add_business_days()` (Mon/Thu/Fri start, zero days, weekend start); 8 API-level tests covering first-send initialization, `no_response` rejection, terminal-reopen block, mark-sent increment, duplicate mark-sent block, max-count rejection, terminal-transition flag clearing, and stats `no_response` count |
| 5.2 | `README.md` | Added `FOLLOW_UP_SCHEDULE_HOUR/MINUTE`, `FOLLOW_UP_TIMEZONE`, `FOLLOW_UP_BUSINESS_DAYS`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` to the `.envrc` example in the Environment Variables section |

### Test results

```
tests/test_api.py + tests/test_followups.py: 26 passed in 0.34s
```

Pre-existing failure in `tests/test_filter.py::test_filter_non_genai_sector_rejected` is unrelated to this feature (predates all follow-up work; last touched in commit `262a4f0`).
