---
title: Admin Operational Dashboard DB Snapshot
type: operations
tags: [atlas, admin, dashboard, db, usage, session-queue, workflow-runs]
updated: 2026-06-03
related: [atlas-pipeline-db-state, provider-and-llm-call-accounting, atlas-db-router-runtime-sharding-20260602, pipeline-progress-debugging]
---

# Admin Operational Dashboard DB Snapshot - 2026-06-03

This page records what the admin dashboard should prioritize based on the real
local Atlas operating DB, not a generic SaaS user-management model.

Evidence source:

- DB path: `~/.common_ai_agent/atlas.db`
- Snapshot time: 2026-06-03 11:16 KST
- Repo-local `atlas.db` was older, so it is not the operational source for this
  snapshot.
- Query style: SQLite aggregate reads only; no raw usernames, emails, feedback
  text, or user-identifying rows copied into this page.

## Executive Rule

The admin home screen should not answer "who are all users?" first. It should
answer:

```text
which five things need admin action today?
```

For this DB, the answer is:

1. user inactivity,
2. unattributed LLM cost,
3. stuck queue/session delivery,
4. stale running workflows,
5. identity/context integrity gaps.

## What The DB Can And Cannot Show

Available from current tables:

| Concern | Tables / columns |
|---|---|
| User count and roles | `users.role`, `users.last_login_at` |
| Login recency | `users.last_login_at` |
| Session state | `sessions.status`, `sessions.updated_at`, `sessions.user_id`, `sessions.owner`, `sessions.ip`, `sessions.workflow`, `sessions.session_uid` |
| LLM usage and cost | `llm_calls.session_id`, `llm_calls.ip_id`, `llm_calls.model`, `llm_calls.cost_usd`, token columns, `llm_calls.status` |
| Prompt/output queue health | `session_queue.processed_at`, `session_queue.delivered_at`, `session_queue.direction`, `session_queue.msg_type` |
| Workflow health | `workflow_runs.status`, `workflow_runs.updated_at`, `workflow_runs.duration_ms` |
| Feedback backlog | `feedback.status` |
| ACL shape | `ip_permissions.permission` |

Not available as first-class account-state fields:

- invite pending,
- account locked,
- deactivation scheduled,
- policy violation,
- MFA/security-setup status,
- license assignment.

Do not fake these categories in the admin UI until the schema grows those
fields.

## Snapshot Numbers

### Users

| Metric | Value |
|---|---:|
| Total users | 641 |
| Admins | 3 |
| Plain users | 637 |
| Agent role | 1 |
| Never logged in | 576 |
| Never-login rate | 89.9% |
| Logged in last 24h | 1 |
| Logged in last 7d | 5 |
| Logged in last 30d | 65 |
| Latest login | 2026-06-02 12:06:19 KST |

Admin implication: the first user card should be an inactivity card, not a
sortable full user table.

### Sessions

| Metric | Value |
|---|---:|
| Total sessions | 937 |
| Active sessions | 937 |
| Stale active sessions over 24h | 935 |
| Stale active sessions over 7d | 811 |
| 7d stale active rate | 86.6% |
| Sessions whose `user_id` is missing from `users` | 136 |
| Distinct missing user IDs referenced by sessions | 5 |
| Sessions missing `owner/ip/workflow` context | 562 |
| Sessions missing `session_uid` | 0 |
| Latest session update | 2026-06-02 13:48:08 KST |

Admin implication: show stale sessions and orphan/session-only identities before
normal active sessions. In this snapshot, `active` by itself is not a useful
healthy state because every session is active.

### LLM Cost And Attribution

| Metric | Value |
|---|---:|
| LLM calls | 15,469 |
| Distinct LLM `session_id` values | 319 |
| Distinct `ip_id` values | 183 |
| Total cost | $872.9942 |
| Total tokens | 974,231,453 |
| Average latency | 24,024.0 ms |
| Non-success calls | 58 |
| Empty `session_id` calls | 3,506 |
| Latest LLM call | 2026-06-02 08:03:23 KST |

Attribution split:

| Join state | Calls | Cost | Tokens |
|---|---:|---:|---:|
| `session_matched` | 6,131 | $320.3348 | 361,541,126 |
| `session_missing_from_sessions` | 5,832 | $292.4751 | 390,538,676 |
| `empty_session_id` | 3,506 | $260.1843 | 222,151,651 |

User-row attribution:

| User join state | Calls | Cost | Tokens |
|---|---:|---:|---:|
| Missing user row | 9,397 | $553.6861 | 613,634,658 |
| Registered user | 6,072 | $319.3082 | 360,596,795 |

Admin implication: "unattributed LLM cost" must be a top card. In this snapshot,
about 63.4% of cost cannot be cleanly attributed to a registered user row.

### Queue Health

| Metric | Value |
|---|---:|
| `session_queue` rows | 16,888 |
| Unprocessed rows | 16,888 |
| Undelivered rows | 16,531 |
| Distinct sessions in queue | 81 |
| Latest queue row | 2026-06-03 07:59:49 KST |

Top queue row categories by count:

| Direction | Message type | Rows | Unprocessed | Undelivered |
|---|---|---:|---:|---:|
| out | reasoning | 3,676 | 3,676 | 3,676 |
| out | tool | 3,155 | 3,155 | 3,155 |
| out | token | 2,505 | 2,505 | 2,505 |
| out | tool_result | 2,124 | 2,124 | 2,124 |
| out | todo | 1,259 | 1,259 | 1,259 |
| out | flush | 1,070 | 1,070 | 1,070 |
| out | cost | 1,032 | 1,032 | 1,032 |
| out | token_usage | 1,032 | 1,032 | 1,032 |

Admin implication: a queue-depth card should be red before any normal activity
charts. All queue rows are unprocessed in this snapshot, and there are zero
active websocket connections.

### Workflow Runs

| Metric | Value |
|---|---:|
| Workflow runs | 720 |
| Completed | 257 |
| Error | 302 |
| Blocked | 76 |
| Running | 74 |
| Cancelled | 11 |
| Stale running over 1h | 74 |
| Stale running over 24h | 74 |
| Latest workflow update | 2026-06-01 22:35:37 KST |

Admin implication: `running` must be interpreted with age. Here, every running
workflow is stale, so a naive "74 running" activity badge would be misleading.

### Feedback And Permissions

| Metric | Value |
|---|---:|
| Open feedback rows | 5 |
| Latest feedback | 2026-05-26 06:13:47 KST |
| IP permission rows | 5 |
| Permission split | `write=3`, `view=1`, `admin=1` |

Admin implication: feedback is smaller than the queue/workflow/cost issues in
this snapshot, but should still be shown as an actionable backlog.

## Recommended Admin First Screen

Order the cards by actionability:

1. **Unattributed LLM cost** - dollars and tokens not joined to a registered
   user; drill into empty or missing `session_id` buckets.
2. **Queue blocked** - unprocessed / undelivered rows, latest created time, top
   message types.
3. **Stale running workflows** - running count split by age, not only by status.
4. **Stale active sessions** - active sessions older than 24h / 7d.
5. **Inactive users** - never logged in, last 7d / 30d cohorts.
6. **Identity integrity** - session user IDs missing from `users`, sessions
   missing owner/IP/workflow context.
7. **Feedback backlog** - open feedback count and age.

Do not lead with a normal "641 users" table. Make the table a drill-down from
the cards above.

## Runtime Rollup Note

The DB has `session_runtime_dbs`, `runtime_usage_rollups`,
`runtime_rollup_offsets`, and `runtime_db_audit` tables, but the first two had
zero rows in this snapshot.

Until runtime rollups are populated, admin usage should aggregate directly from
the central `llm_calls`, `session_queue`, `sessions`, and `workflow_runs`
tables. Once rollups are active, the admin dashboard should prefer rollups for
speed but keep a reconciliation card for central-vs-runtime drift.

## Query Pattern For Rechecking

Use read-only aggregate checks and a timeout because the live SQLite file may be
busy:

```sh
sqlite3 -cmd ".timeout 10000" -header -column ~/.common_ai_agent/atlas.db \
  "SELECT COUNT(*) FROM users;"
```

Recommended recheck groups:

- `users`: total, role split, `last_login_at` cohorts.
- `sessions`: status split, stale active counts, user join integrity.
- `llm_calls`: total cost, token totals, empty/missing session attribution.
- `session_queue`: unprocessed and undelivered counts by `direction,msg_type`.
- `workflow_runs`: status split and stale running age.
- `feedback`: open count and latest created time.

## Related

- [[atlas-pipeline-db-state]] - what state already comes from DB versus files.
- [[provider-and-llm-call-accounting]] - how to count LLM calls consistently.
- [[atlas-db-router-runtime-sharding-20260602]] - why runtime rollups matter for
  multi-session scale.
- [[pipeline-progress-debugging]] - how to avoid trusting headless-only or
  stale product-flow signals.
