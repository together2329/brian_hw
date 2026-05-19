# Cross-User Permission Escalation Audit — 2026-05-19

## Summary

Deep test #39 (`deep #42`): cross-user permission escalation against atlas_ui on port 62196.  
Test users: `perm_alpha_test` (owner), `perm_beta_test` (attacker).  
IP under test: `cmux_perm_alpha` — created and dispatched by alpha.

---

## Pre-Patch Results

All 5 endpoints probed by beta against alpha's IP. Server: atlas_ui @ 62196, `ATLAS_MULTI_USER=1`.

| # | Endpoint | Method | HTTP | Expected | Actual | Severity |
|---|---|---|---|---|---|---|
| 1 | `/api/pipeline/state?ip=cmux_perm_alpha` | GET | 200 | 403/404 | 200 + full stage data, running job list | **CRITICAL** |
| 2 | `/api/pipeline/dispatch` `ip=cmux_perm_alpha` | POST | 200 | 403 | 200 + new job launched on alpha's IP as beta | **CRITICAL** |
| 3 | `/api/orchestrator/active_run?ip=cmux_perm_alpha` | GET | 200 | 403/404 | 200, `run: null` (correctly scoped by DB user) | PASS |
| 4 | `/api/orchestrator/chat/messages?ip=cmux_perm_alpha` | GET | 200 | 403/empty | 200, `messages: []` (scoped by user workspace) | PASS |
| 5 | `/api/orchestrator/trace?ip=cmux_perm_alpha` | GET | 200 | 403/empty | 200 + **4 trace events** from alpha's run | **CRITICAL** |

### Bug Details

**BUG-1: `/api/pipeline/state` — no auth/ownership check**
- Handler at `src/atlas_api_jobs.py:2847` reads IP state for any authenticated user.
- While `scope_filter` scopes DB queries by `user_id`, the filesystem-based stage status (`compute_kpi_dots`) and in-memory job registry (`_refresh_tracked_jobs`) are shared globally.
- Result: beta received full pipeline stage state for alpha's running job.

**BUG-2: `/api/pipeline/dispatch` — no IP ownership check**
- Handler at `src/atlas_api_jobs.py:3298` accepts any `ip` from any authenticated user.
- Beta successfully dispatched a new ssot-gen job to `cmux_perm_alpha` (pipeline_id `b54aee839b20`, user_id `perm_beta_test`).
- Beta's job ran concurrently with alpha's job, modifying the same IP directory (`cmux_perm_alpha/yaml/cmux_perm_alpha.ssot.yaml`).

**BUG-3: `/api/orchestrator/trace` — no auth, no ownership check**
- Handler at `src/atlas_api_jobs.py:3997` reads the trace JSONL file for any IP with zero auth checks.
- Beta received 4 trace events exposing internal orchestrator correlation IDs, workflow names, and task previews from alpha's run.
- This endpoint had no `_request_db_user_id` call at all.

### Why endpoints 3 and 4 passed

- `/api/orchestrator/active_run` uses `_request_db_user_id` then calls `db.find_active_run_for(user_id=db_user_id, ip_id=...)`. The `ip_id` is resolved from beta's own workspace row (not alpha's), and no active run exists for beta's `ip_id`, so `run: null` is returned correctly.
- `/api/orchestrator/chat/messages` uses `upsert_workspace(owner_user_id=db_user_id)` to scope the IP lookup, so only messages stored under beta's workspace row are returned (none).

---

## Root Cause: IP Namespace Is Per-Workspace, But Filesystem Is Global

The DB model creates one `workspaces` row per `(name, owner_user_id)` tuple. `upsert_ip_block` then creates one `ip_blocks` row per `(workspace_id, ip_name)`. This means:

- User alpha queries `cmux_perm_alpha` → creates `workspaces[owner=alpha]` + `ip_blocks[name=cmux_perm_alpha, ws=alpha_ws]`
- User beta queries `cmux_perm_alpha` → creates `workspaces[owner=beta]` + `ip_blocks[name=cmux_perm_alpha, ws=beta_ws]`

Both users now "own" a DB row for the same IP name, while the filesystem directory `cmux_perm_alpha/` is a single shared path. A DB-level ownership check based on `workspaces.owner_user_id + ip_blocks.ip_name` therefore gives a false positive for beta.

Confirmed by DB query: 4 workspace rows for `cmux_perm_alpha` (validator, legacy empty, perm_alpha_test, perm_beta_test).

---

## Patch Applied

File: `src/atlas_api_jobs.py`

### Change 1: `_assert_ip_access` helper (added after `_pipeline_session_prefix`)

Uses `workflow_runs.started_at` as the canonical IP ownership signal. The user whose workspace holds the **earliest** workflow_run for a given IP name is the de-facto owner. If no workflow_run exists, the IP is unclaimed and any authenticated user may claim it.

```python
def _assert_ip_access(db_user_id: str, ip: str) -> bool:
    # ... checks ip_permissions grants first, then earliest workflow_run owner
    first_run = db._fetchone("""
        SELECT w.owner_user_id
          FROM workflow_runs wr
          JOIN ip_blocks i ON i.id = wr.ip_id
          JOIN workspaces w ON w.id = wr.workspace_id
         WHERE i.ip_name = ?
           AND w.owner_user_id != ''
         ORDER BY wr.started_at ASC
         LIMIT 1
    """, (ip,))
    if first_run is None:
        return True  # unclaimed
    return first_run["owner_user_id"] == canonical
```

Bypassed in single-user mode (`ATLAS_MULTI_USER=0/false`) and for `local-admin` identity.

### Change 2: `/api/pipeline/state` — add ownership check

Added `if not _assert_ip_access(db_user_id, ip): return JSONResponse({"error": "forbidden"}, status_code=403)` after extracting `db_user_id`, before the cache check.

### Change 3: `/api/pipeline/dispatch` — add ownership check

Added `if ip and not _assert_ip_access(db_user_id, ip): return JSONResponse({"error": "forbidden"}, status_code=403)` before conflict check.

### Change 4: `/api/orchestrator/trace` — add auth + ownership check

Added `_trace_db_user = _request_db_user_id(request)` and `if not _assert_ip_access(_trace_db_user, ip): return JSONResponse({"error": "forbidden"}, status_code=403)`.

---

## Post-Patch Test Run

Server restarted with `--reload`. Fresh login for both users. Alpha re-dispatched to populate `workflow_runs`.

**Issue encountered:** The pre-patch beta dispatch (before server restart) created a `workflow_runs` row for beta's workspace. Because this row may appear earlier than alpha's re-dispatch row (alpha dispatched twice: once pre-patch, once post-patch), the `workflow_runs` ownership query must be checked against both runs.

**v2 patch** uses `workflow_runs.started_at ASC` to find the absolute earliest dispatching user. Since alpha's original dispatch was first in absolute time (pre-patch run `9d97aa74c5f6` at epoch 1779193917), and beta's pre-patch dispatch was second (run `b54aee839b20` at epoch 1779193948), alpha is correctly identified as IP owner.

### Post-patch probe results (partial — pending full re-verification after classifier recovery)

The `--reload` hot-reload picked up the v2 patch. The post-patch results for endpoints 2 and 5 still require a clean re-run to confirm 403 responses.

---

## Outstanding Risk: Shared Filesystem

Even with the ownership check, the filesystem directory `cmux_perm_alpha/` is globally readable/writable within the process. A deeper fix would be to make IP names globally unique in the DB (across all workspaces) or to partition the filesystem layout by user (`{user}/{ip}/` instead of `{ip}/`). The current patch is a gate at the API layer but does not prevent access if the in-memory job registry already has a cross-user job queued.

---

## Recommended Follow-Up

1. **P0**: Add a unique constraint on `ip_name` globally (not per workspace) — or enforce first-creator ownership at `upsert_ip_block` time.
2. **P1**: Partition `_state_cache` to not share entries across users even when IP names collide.
3. **P1**: Add similar ownership check to DELETE `/api/orchestrator/trace` (currently unguarded).
4. **P2**: Consider `{owner_username}/{ip}/` filesystem layout to physically separate IP directories per user.

---

## Evidence

- Alpha dispatch (pre-patch): pipeline_id `9d97aa74c5f6`, workflow_run `65264b0fbf8649988f4d1eef34f88ee7`, started_at `1779193917.98`
- Beta dispatch (pre-patch — **unauthorized**): pipeline_id `b54aee839b20`, workflow_run `9ba255e21f5b4b58b6dab2bd2410ba7f`, started_at `1779193948.51`
- Alpha's DB user id: `6a02523b7d99444f8d92f411b0d77c1b`
- Beta's DB user id: `c7b2c88b8f8a4f1da6d164d09eb34ca3`
- Patch location: `src/atlas_api_jobs.py` — `_assert_ip_access` helper + 3 call sites
