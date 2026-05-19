# atlas.db FK Integrity Audit — 2026-05-19

Audited two databases: canonical home (`~/.common_ai_agent/atlas.db`) and PWD legacy
(`./atlas.db`). Queries run read-only; no data was modified.

---

## Summary

| FK Check | Home DB orphans | PWD DB orphans | Status |
|---|---|---|---|
| `workflow_runs.ip_id` → `ip_blocks.id` | 0 | 0 | PASS |
| `workflow_runs.orchestrator_run_id` → `orchestrator_runs.id` | 0 | 0 | PASS |
| `ip_blocks.workspace_id` → `workspaces.id` | 0 | 0 | PASS |
| `llm_calls.run_id` → `workflow_runs.id` | **91** | **622** | SEE NOTE |
| `orchestrator_steps.run_id` → `orchestrator_runs.id` | 0 | 0 | PASS |

**Q4 finding:** All apparent orphans in `llm_calls.run_id` resolve against
`orchestrator_runs.id` — none are truly dangling. The column is a polymorphic
run reference (either a `workflow_run` id or an `orchestrator_run` id). No data
corruption exists.

---

## Home DB (`~/.common_ai_agent/atlas.db`)

### Row counts
| Table | Count |
|---|---|
| `llm_calls` | 113 |
| `workflow_runs` | 23 |
| `orchestrator_runs` | (≥10 distinct run_ids resolved) |

### Q1 — `workflow_runs.ip_id → ip_blocks.id`
```sql
SELECT COUNT(*) FROM workflow_runs
WHERE ip_id IS NOT NULL AND ip_id NOT IN (SELECT id FROM ip_blocks);
```
Result: **0**

### Q2 — `workflow_runs.orchestrator_run_id → orchestrator_runs.id`
```sql
SELECT COUNT(*) FROM workflow_runs
WHERE orchestrator_run_id IS NOT NULL AND orchestrator_run_id != ''
  AND orchestrator_run_id NOT IN (SELECT id FROM orchestrator_runs);
```
Result: **0**

### Q3 — `ip_blocks.workspace_id → workspaces.id`
```sql
SELECT COUNT(*) FROM ip_blocks
WHERE workspace_id NOT IN (SELECT id FROM workspaces);
```
Result: **0**

### Q4 — `llm_calls.run_id → workflow_runs.id`
```sql
SELECT COUNT(*) FROM llm_calls
WHERE run_id IS NOT NULL AND run_id != ''
  AND run_id NOT IN (SELECT id FROM workflow_runs);
```
Result: **91** — but all 10 distinct orphan `run_id` values resolve to `orchestrator_runs.id`.
Truly dangling (not in workflow_runs **and** not in orchestrator_runs): **0**

#### Sample orphan rows (up to 5)
| llm_call id | run_id | model | created_at |
|---|---|---|---|
| 7c8189f6f4b8416991b256dea737f920 | 0441cffed5ab425eb97650fbc13f686c | gpt-5.5 | 1779176924 |
| df41eee0a65340b98b62c2cdf621eaa4 | 0441cffed5ab425eb97650fbc13f686c | gpt-5.5 | 1779176928 |
| 981916463acd482abb28f4fca83ec76a | 0441cffed5ab425eb97650fbc13f686c | gpt-5.5 | 1779176934 |
| d158854a5ce14b46bf22c054b6e6a1cf | 0441cffed5ab425eb97650fbc13f686c | gpt-5.5 | 1779177537 |
| db6e87cf32dd4554abb99ede8571bf12 | 0441cffed5ab425eb97650fbc13f686c | gpt-5.5 | 1779177545 |

### Q5 — `orchestrator_steps.run_id → orchestrator_runs.id`
```sql
SELECT COUNT(*) FROM orchestrator_steps
WHERE run_id NOT IN (SELECT id FROM orchestrator_runs);
```
Result: **0**

---

## PWD DB (`./atlas.db`)

### Row counts
| Table | Count |
|---|---|
| `llm_calls` | 622 |
| `workflow_runs` | 378 |
| `orchestrator_runs` | (19 distinct run_ids resolved) |

### Q1 — `workflow_runs.ip_id → ip_blocks.id`
Result: **0**

### Q2 — `workflow_runs.orchestrator_run_id → orchestrator_runs.id`
Result: **0**

### Q3 — `ip_blocks.workspace_id → workspaces.id`
Result: **0**

### Q4 — `llm_calls.run_id → workflow_runs.id`
Result: **622** apparent orphans — all 19 distinct orphan `run_id` values resolve to
`orchestrator_runs.id`. Truly dangling: **0**

#### Sample orphan rows (up to 5)
| llm_call id | run_id | model | created_at |
|---|---|---|---|
| e9ad36f031824ee9870446680a2dfaa6 | 470507e819b3472f94b79e3e9332138a | gpt-5.5 | 1779111444 |
| 2b7d19097ad747ab9994b705640439fe | 470507e819b3472f94b79e3e9332138a | gpt-5.5 | 1779111449 |
| fa5304daa5fa44ea873f18469797e7fd | 7bf070b0ce4347c889499033cbf26fb1 | gpt-5.5 | 1779130256 |
| b4af23bc3a5b4e00a596933ce1fe3b35 | 7bf070b0ce4347c889499033cbf26fb1 | gpt-5.5 | 1779130265 |
| 2155aaf30e814a05992099af66c6d608 | 7bf070b0ce4347c889499033cbf26fb1 | gpt-5.5 | 1779130267 |

### Q5 — `orchestrator_steps.run_id → orchestrator_runs.id`
Result: **0**

---

## Diagnosis

`llm_calls.run_id` is a polymorphic FK: it can point to either `workflow_runs.id`
or `orchestrator_runs.id`. The schema does not enforce this with a DB-level
constraint, so the "orphan" count from a strict `workflow_runs`-only check is
misleading. There are zero truly dangling rows in either database.

---

## Recommended Cleanup SQL

No cleanup is required. All data is consistent.

If future schema tightening is desired, consider adding a check constraint or
renaming the column to `run_id` with an explicit note in schema docs that it is
polymorphic. Example documentation SQL (do not execute without migration plan):

```sql
-- INFORMATIONAL ONLY — do not run without a migration plan
-- Option A: document the polymorphic intent via a comment (SQLite has no column comments natively)
-- Option B: split into two nullable FKs:
--   ALTER TABLE llm_calls ADD COLUMN workflow_run_id TEXT REFERENCES workflow_runs(id);
--   ALTER TABLE llm_calls ADD COLUMN orchestrator_run_id TEXT REFERENCES orchestrator_runs(id);
-- and migrate existing data before dropping run_id.
```

---

## Tables Present (both DBs)

`artifact_version_edges`, `artifact_versions`, `artifacts`, `feedback`,
`ip_blocks`, `ip_permissions`, `llm_calls`, `messages`, `orchestrator_runs`,
`orchestrator_steps`, `parts`, `rtl_versions`, `run_artifact_versions`,
`session_queue`, `sessions`, `todo_events`, `trace_events`, `users`,
`workflow_events`, `workflow_runs`, `workflow_stages`, `workflow_todos`,
`workspaces`, `ws_connections`

Home DB additionally has: `test`
