# Atlas Runtime DB Refactor for 100 Active Users — Hardened Implementation Plan (v2, SUPERSEDES draft)

> This plan supersedes `plans/atlas-runtime-db-100-users.md`. All file:line anchors below were re-verified by reading the code. Where the draft was wrong, the correction is called out inline. Where grounding/critiques found an INVALID assumption, the fix is folded into the owning task. Design background: `doc/wiki/atlas-db-router-runtime-sharding-20260602.md`.

---

## 1. Verdict on the existing draft

**Verdict: structurally sound, but NOT execution-ready as written.** The router-first / control-vs-runtime split is the right SQLite-at-100 model and the four mechanics (path-scoped locks, per-session queue, output coalescing, control-DB rollups) are mechanically feasible. But the draft is grounded on several wrong anchors, three INVALID assumptions, two non-existent test artifacts in its own gates, and it omits the **two dominant real-mode costs** (serial broadcaster fan-out + connection-close-per-poll) and **four data-loss/double-delivery hazards** (non-monotonic queue ordering, cross-DB accept atomicity, correlated-subselect cursor, rollback idempotency). It is approve-with-major-revisions.

### Anchor corrections (verified by reading)
| Draft ref | Reality | Fix |
|---|---|---|
| `core/atlas_db.py:601` "process-wide `_WRITE_LOCK`" | `:601-609` is the doc comment; the symbol `_WRITE_LOCK = threading.RLock()` is at **`:610`** | cite `:610` |
| `core/atlas_db.py:640` `_connect()` | `def _connect` is at **`:641`**; busy_timeout `:664`, WAL retry loop `:666-673`, cache write `:674` | cite `:641` |
| `core/atlas_db.py:208` session_queue schema | comment `:208`; `CREATE TABLE session_queue` `:209-219`. Columns: id, session_id, direction, msg_type, payload, created_at, processed_at, delivered_at, expires_at. **No session_uid** (it lives on `sessions`, `:74`) | confirmed; draft's "do not add session_uid" is correct |
| `core/atlas_db.py:2440` "dequeue/poll" | `def dequeue_message` is at **`:2424`**; `:2440` is the `with self._lock:` inside it (`BEGIN IMMEDIATE` `:2443`). `poll_messages` is a separate method at **`:2475`** | cite dequeue `:2424`, poll `:2475` |
| `core/session_worker.py:512` `emit_tool_result` | `:512` is inside `_persist_cost_ledger`; `def emit_tool_result` is at **`:540`** | cite `:540` |
| `core/atlas_db.py:3990` "visible user/IP usage" | inside the docstring; `def summarize_llm_usage_for_user_ip` is at **`:3983`** | cite `:3983` |
| `src/atlas_api_sessions.py:472` "`upsert_runtime_session` ... returns session_uid" | **misattributed.** `:473` is only a CALL site; the method is **defined at `core/atlas_db.py:1837`** (verified: reuses existing `session_uid` else `_new_id()` `:1857`, raises `ValueError` on cross-user `:1855-1856`) | cite definition `core/atlas_db.py:1837`; the capability the plan needs exists |
| `tests/test_db_schema_complete.py:458` | `:458` is a section banner; the test is at **`:462`**, and it uses `direction='inbound'`, NOT the `'in'/'out'` IPC literals | cite `:462`; note it does not pin IPC direction literals |
| `tests/test_lazy_worker_cold_start_storm.py:134` | mid-test; `def` at **`:125`** | cite `:125` |
| `tests/test_chat_full_multiuser_system.py:318` | a pytest fixture, not a test; the isolation test is **`test_chat_traffic_does_not_corrupt_admin_usage` at `:286`** | cite `:286` |

### INVALID / partial assumptions the grounding found (these break the draft as written)
1. **INVALID — Task 7/8 read-path reference lists are incomplete.** Beyond the cited readers, these ALSO read runtime tables and will silently return empty/partial after the split, and are NOT in the draft: `summarize_ip_room_context`/`_recent_events_for_ip` (`core/atlas_db.py:4334`) — **feeds the orchestrator "current ground truth" panel injected into the agent's next ReAct iteration** (the agent itself loses context, not just the UI); `summarize_global_room_context` (`:4444`); `list_chat_messages` (`:3797`); `list_run_artifact_version_sets` (`:3162`); `user_dashboard._workflow_runs` (`core/atlas_user_dashboard.py:187`); `src/atlas_api_jobs.py:_recent_chat_context_for_ip` (`:446`) — **reads chat trace to build worker prompts**. Also `build_admin_usage_payload` (`core/atlas_admin_usage.py:112`) reads messages/parts/trace_events/todo_events for tool/intervention/todo tabs — a **count-only rollup cannot reconstruct these**, so those tabs go silently empty.
2. **PARTIAL — "worker callsites already have a session context."** Only the orchestrator (`src/orchestrator/react_bridge.py:703`, `session_id=ctx.session_id`) truly does. `core/react_loop.py:1380` resolves via a best-effort env chain (`_atlas_runtime_session_context`, can be `''`); `src/headless_workflow.py:1994` reads `ATLAS_SESSION_ID` — **which `build_worker_env` NEVER sets** (it sets `ATLAS_ACTIVE_SESSION`). So a process-mode headless worker already writes `session_id=''` today (swallowed by `try/except: pass`) and would be **unroutable**. Task 6 must route via the `ATLAS_ACTIVE_SESSION` resolution chain, not `ctx.session_id`/`ATLAS_SESSION_ID`.
3. **PARTIAL/INVALID — "chat in control, trace_events in runtime" treats one table as two.** Chat IS trace_events: `record_chat_message` (`core/atlas_db.py:3749`) delegates to `record_trace_event(event_type='chat_message')` with **no session_id** (verified). The split needs a write-time routing predicate inside `record_trace_event` that the draft never specifies.
4. **PARTIAL — "raw DB browser allowlist makes adding session_uid safe."** Misdescribed. `core/atlas_admin_db.py:79` is a dynamic `sqlite_master` table-NAME SQL-injection guard, NOT a DB-PATH allowlist. Both endpoint sites (`src/atlas_admin.py:443/451/461`, `src/atlas_ui.py:9788/9799/9812`) hardcode `with AtlasDB()` (control only) gated solely by `_admin_required`. Per-session ownership + path containment must be **built from scratch**.

### Named test/symbol/flag that does NOT exist (the draft's own DoD/gates depend on these)
- **`tests/test_runtime_db_100_user_scale.py` — DOES NOT EXIST.** Hard-referenced by the F2 command (draft line 489). F2 is **unrunnable** (`file or directory not found`) until Task 10 creates it. → Split F2 into a baseline gate (runnable now) + a scale gate (post-Task-10).
- **`tests/test_atlas_input_deep_runtime.py` — exists but is git-UNTRACKED** (`?? tests/test_atlas_input_deep_runtime.py`). It is in the DoD line-50 command. Passes locally, **fails on a clean clone/CI**. → A Task-0 step must `git add`+commit it before any DoD claim.
- **`ATLAS_RUNTIME_DB_REAL_SUBPROCESS_STRESS`, `ATLAS_CONTROL_DB_PATH`, `ATLAS_RUNTIME_DB_PATH`, `ATLAS_RUNTIME_DB_MODE`, `AtlasDBRouter`, `core/atlas_db_router.py`, `core/runtime_rollup.py`, `session_runtime_dbs`, `runtime_usage_rollups`** — none exist (greenfield, expected). No anchor for them is a "fix"; they are new code.
- **No FakeClock / clock-injection seam exists anywhere in `tests/`** (grep empty). Task 5's "deterministic test clock" requires building the seam first; `AtlasDB._now()` is a hard `time.time()` (`:704-706`).

---

## 2. Hardened architecture

The four pillars stand. Folded-in hardening below.

### 2.1 Control vs runtime split (router-first)
- **Control DB** (`ATLAS_CONTROL_DB_PATH`, default = today's `atlas.db`): `users`, `workspaces`, `ip_blocks`, `ip_permissions`, auth, `sessions` (incl. `session_uid` `:74`), `workflow_runs`, chat (`trace_events` where `event_type='chat_message'`), and the new `session_runtime_dbs` manifest + `runtime_usage_rollups` + `runtime_rollup_offsets`.
- **Runtime DB** per session at `<runtime-root>/<session_uid[0:2]>/<session_uid>.db`: `session_queue`, `messages`, `parts`, session-scoped `trace_events`, `llm_calls`.
- `core/atlas_db_router.py` is the single resolution point. `ATLAS_RUNTIME_DB_MODE=central` (default) returns the control path everywhere → behavior-preserving phase. `=session` returns per-session paths.

### 2.2 Path-scoped locks (verified safe)
- Replace the single class-level `_WRITE_LOCK` (`core/atlas_db.py:610`, assigned to every `self._lock` at `:634`) with `_LOCKS_BY_PATH: dict[str, RLock]` keyed by `Path(db_path).resolve()`, guarded by a `_LOCKS_GUARD`. `:memory:` gets an instance-local lock (today it shares the global one — verified).
- **Safe because** WAL + busy_timeout are applied inside `_connect()` (`:664-673`) independent of the lock object; the lock only serializes Python-level access. Per-path locks serialize only same-file callers; each runtime file has its own single-writer WAL queue.
- **Keep the one-time schema-init guard** (`_INITIALIZED_PATHS`, `:619`/`:745`) — this is the prior 7.85ms→0.012ms win and must be preserved alongside the lock change.

### 2.3 Strict total-order queue (NEW — closes the data-loss hazard)
**The single most important correctness fix.** Today every consumer orders by `created_at` alone with NO id tiebreaker: dequeue `ORDER BY created_at ASC` (`:2449`), poll `ORDER BY created_at ASC` with cursor `created_at > (SELECT created_at WHERE id=?)` (`:2491-2492`), `latest_output_id ORDER BY created_at DESC` (`session_process_manager.py:495`). `created_at = time.time()` (wall clock, `:704-706`) — non-monotonic and tie-prone. Today this is masked by the global lock serializing inserts; once locks are path-scoped and the coalescer bursts near-identical timestamps, the strict `>` cursor can **skip** a same-timestamp row (silent token/prompt loss) and NTP step can make a later prompt sort *before* the cursor (lost prompt).
- **Fix: use SQLite `rowid` (monotonic, collision-free per file) as the ordering + cursor key.** Change dequeue/poll/`latest_output_id` to `ORDER BY created_at, id` (or rowid) and the poll cursor to a value-based `rowid > :cursor` instead of the correlated subselect. Land this in **Task 2/4, before any split**, with a regression test inserting ≥2 rows at an artificially equal `created_at`.

### 2.4 Value-based poll cursor (NEW — closes the silent-stall hazard)
The correlated subselect (`:2491`) returns NULL when the cursor id is absent in the target runtime DB (recreated DB, mode switch) → `created_at > NULL` is never true → **0 rows, no error, permanent output stall**; or if `latest_output_id` returns None on a recreated DB the in-memory cursor (`atlas_multiuser.py:358/402`) restarts from top → **duplicate token delivery**. Fix: value-based `rowid` cursor (from 2.3); when the cursor row is absent, raise a distinct recoverable status (never silent 0-rows); re-seed `_process_output_cursors` atomically on any runtime-DB swap.

### 2.5 Cross-DB accept atomicity (NEW — closes the lost/double-prompt hazard)
SQLite has no cross-DB transaction. The accept path writes the `sessions` row (control, `upsert_runtime_session` `core/atlas_db.py:1837`) then the prompt (runtime). Harden:
- **`session_uid` is resolved-or-minted ONCE and persisted; never re-minted on retry** — so the first enqueue and `atlas_multiuser` spawn-then-retry (`:748-770`) derive the **byte-identical** runtime path. Path derivation is a pure deterministic function of `session_uid`.
- **Ordering:** create+init the runtime DB and persist the manifest row BEFORE accepting/acking the prompt. "Runtime DB not yet initialized" is a hard recoverable error surfaced to the WS layer, never a silent `None` (note `send_input` early-returns None if `not is_alive`, `session_process_manager.py:426-428`).

### 2.6 Hot-path connection reuse (NEW — the real poll-latency fix)
`poll_output`/`send_input`/`latest_output_id` each call `db.close()` in `finally` (`session_process_manager.py:463/485/501`); `close()` pops the thread-local cached connection (`atlas_db.py:1075`), so the next poll re-opens + re-runs busy_timeout + the WAL retry loop (`:664-673`). At 100 sessions = 100 reconnect+WAL cycles **per broadcaster pass**, on one thread. **Path-scoped locks do nothing for this.** Fix: stop closing on the hot poll/enqueue path — have the router hold a long-lived per-(thread,path) `AtlasDB` so the `_TLS` cache survives; assert connections-opened-per-poll ≈ 0 in steady state.

### 2.7 Serial broadcaster fan-out (NEW — acknowledge + mitigate)
ONE `_broadcast_outbox` loop (`src/atlas_ui.py:1327`) → `bridge.next_event()` → `_poll_process_outputs` (`atlas_multiuser.py:346`) iterates `manager.list_active()` **sequentially** (`:357`), polling each session's runtime DB in turn. Wall time scales O(N × per-poll-cost). Mitigate: poll only sessions with ≥1 connected WS client, and/or back off sessions whose last poll returned 0 rows. The plan must state DB-path locks do not address this; Task 10's SLA proof must run through this real path.

### 2.8 Output coalescing (corrected scope)
Worker-side batcher merges only `token`/`reasoning`. Flush on: 50ms timer, 4KB, before any non-mergeable event, before `flush`/`agent_state`, at shutdown. Re-expand `token_batch`/`reasoning_batch` at the SINGLE point `_poll_process_outputs` (`:346`) so the browser is unchanged (no `*_batch` subscriber exists — expansion is **mandatory**, not optional). **Drop `file_changed`/`stop`/`interrupt` from the worker never-coalesce set** — `file_changed` is emitted by the main-process bridge (`atlas_multiuser.py:415`), `stop`/`interrupt` are INBOUND queue types the worker reads; the worker batcher never sees them. Real never-coalesce set (all verified worker emits): `tool` (`:538`), `tool_result` (`:540`), `cost` (`:592`), `token_usage` (`:593`, note: emits TWO rows), `context` (`:457`), `ask_user*` (`:719/722/765/766`), `agent_state` (`:617`), `worker_started/stopped/exited` (`:864/868/875`), `error` (`:861/871`), `flush` (`:439`). The `<=30 rows` target is **wall-clock dependent**: state it as `rows ≈ ceil(wall_ms/50) + ceil(bytes/4096) + non_mergeable_count`; test the 4KB (size) and 50ms (time) triggers separately.

### 2.9 Runtime-only schema subset (NEW — cold-spawn cost)
`init_db` (`:738`) is gated only per-path (`_INITIALIZED_PATHS`, `:745`); the 7.85ms win does NOT amortize across 100 distinct paths. Each runtime DB pays a full ~80-statement bootstrap and materializes ~24 unused control tables. Add a **runtime-only schema subset** (just `session_queue`/`messages`/`parts`/`trace_events`/`llm_calls` + their indexes) for runtime DBs, and/or pre-create at activation (off the hot path). Measure cold-spawn p95 separately.

### 2.10 Rollups + read-path safety
`runtime_usage_rollups` must carry the dimensions admin tabs need (per-tool counts, intervention counts, todo-flow) OR those tabs must be explicitly de-scoped to "summary-only" in runtime mode — never silently empty. Rollup high-water must be a monotonic `rowid`/seq, NOT `(created_at, uuid)` (uuid is random `:701-702`). Every moved read path (full list in §1.1) routes through the router or reads a rollup; a missing/corrupt runtime DB returns an **explicit stale/unavailable signal**, never false-empty.

### 2.11 Path-traversal + isolation hardening
`session_uid` is `uuid4().hex` (`:702`, no path chars) — the filename primitive is safe **iff** the path is always built from `session_uid`, never `session_id`. Make "sha256(session_id) only in tests" an **executable boundary**: `runtime_route(..., create=True)` always resolves `session_uid` and **fails closed** if none; any derived-key fallback is gated behind `ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY` (default off). The Task-8 raw-browser param accepts ONLY `session_uid`, resolves it through the manifest, asserts the resolved real path is under `Path(ATLAS_RUNTIME_DB_ROOT).resolve()`, enforces ownership, returns 404 (no path) on miss, never echoes a filesystem path. Change `_authorize_session_request` (`src/atlas_api_sessions.py:1010-1030`) to **fail CLOSED** and keep the ownership lookup on the CONTROL DB so runtime-DB health never affects authz.

### 2.12 Lifecycle / retention (NEW)
- `_delete_session_metadata_on_conn` (`core/atlas_db.py:4812`, deletes session_queue/messages/parts on ONE control connection `:4821-4825`) must be rerouted through the router to also delete the runtime `.db`+`-wal`+`-shm`, the manifest row, and the rollup row — gated on queue_depth==0 with an audit row. Otherwise every delete orphans a runtime file forever.
- UI-restart recovery: on startup scan `session_runtime_dbs`, set each poll cursor to the oldest UNDELIVERED out-row (not `latest_output_id`, which skips buffered output), reconcile orphan worker PIDs (orphan pruning matches `--session-id AND --db-path`, `session_process_manager.py:229-233`; a restart with empty `_processes` leaves ghosts).
- `cleanup_old_messages` (`:2516`) deletes by `created_at`/`expires_at` WITHOUT checking `delivered_at`/`processed_at` — per runtime DB it could purge an undelivered prompt for a cold worker. Exclude undelivered/unprocessed rows.
- Forced rollback (runtime→control queue copy): stop/drain workers first, copy with `INSERT OR IGNORE` preserving original row ids (idempotency), write an audit row; document whether historical runtime messages/traces are imported or left orphaned.

---

## 3. Risk register (ranked, deduped)

| # | Risk | Severity | Mitigation | Owning task(s) |
|---|---|---|---|---|
| R1 | Queue ordering/dequeue/poll-cursor depend on non-monotonic `time.time()` `created_at` with no id tiebreaker → skipped/reordered prompt or token (silent) | **High** | Switch ordering + cursor to monotonic `rowid`/seq; tie-equal-timestamp regression test | **2, 4** (before split); affects 5, 7 |
| R2 | Per-poll `db.close()` defeats the `_TLS` connection cache → 100 reconnect+WAL cycles/pass; dominates poll p95 | **High** | Stop closing on hot poll/enqueue path; router holds long-lived per-(thread,path) AtlasDB; assert opens/poll≈0 | **3, 4, 10** |
| R3 | Single serial broadcaster scans all 100 sessions sequentially; lock-scoping doesn't help | **High** | Poll only WS-connected sessions / backoff on empty; SLA proof runs real bridge path | **2 (doc), 4, 10** |
| R4 | No cross-DB atomicity on prompt accept; retry can re-mint uid → prompt lands in 2 files (lost/double) | **High** | Resolve-or-mint `session_uid` once; init runtime DB + manifest before ack; deterministic path | **1, 3, 4, 9** |
| R5 | Poll cursor correlated-subselect returns NULL when cursor id absent → silent 0-row stall or re-deliver | **High** | Value-based `rowid` cursor; distinct "cursor not found" status; atomic cursor re-seed on DB swap | **4, 5** |
| R6 | Synthetic harness bypasses the real bottleneck (`send_input` is `is_alive`-gated) → green harness, slow prod | **High** | Inject fake `_processes` so `list_active()`==100 and the serial fan-out + connect/close churn run; or make a ≥50-worker real-subprocess scenario the SLA | **10** |
| R7 | Task 7/8 read-path lists incomplete; moved readers return silent empty/partial; agent loses ground-truth/prompt context | **High** | Enumerate & route ALL readers (§1.1 list incl. `_recent_events_for_ip:4334`, `_recent_chat_context_for_ip:446`); explicit stale signal | **6, 7, 8** |
| R8 | Count-only rollup can't reconstruct tool/intervention/todo admin tabs → silently empty | **High** | Expand rollup schema for those dims OR de-scope tabs to "summary-only" with explicit marker; parity test vs central mode | **7, 8** |
| R9 | "deterministic test clock" has no seam; flush timing untestable | **High** | Build injectable `now_fn` + public `flush()` on the batcher; separate size-trigger and time-trigger tests | **5** |
| R10 | DoD/F2 unrunnable: untracked test + nonexistent scale test | **High** | Task-0 commit `test_atlas_input_deep_runtime.py`; split F2 into baseline (now) + scale (post-10) | **0, 10, F2** |
| R11 | Existing concurrency test can't prove de-serialization (passes for global OR path locks) | **High** | New two-DB test: hold write txn on A, assert B completes < hard bound; negative shim (global lock) must time out | **2, 10** |
| R12 | Session-delete scrubs control tables, orphans runtime files + manifest/rollup rows forever | **High** | Reroute `_delete_session_metadata_on_conn` through router; delete file+wal+shm+manifest+rollup; GC job | **9** (refs 4,6,1) |
| R13 | UI restart skips undelivered runtime output (`latest_output_id` cursor) + drops `_jobs`; orphan workers ghost-write | **High** | Restart recovery: oldest-undelivered cursor, PID reconcile, rebuild/accept `_jobs` loss | **9** |
| R14 | Task-8 raw-browser session param is a new path-resolution + cross-user surface; "allowlist" gives no path safety | **High** | session_uid-only → manifest → containment under `ATLAS_RUNTIME_DB_ROOT` + ownership; 404 no-path on miss; shared helper for both endpoint copies | **8** |
| R15 | "sha256(session_id) only in tests" is prose, not enforced → raw input can reach filenames | **Medium** | Executable boundary: fail-closed when no session_uid; derived-key behind off-by-default flag | **1, 4** |
| R16 | Worker callsites lack a real session ctx; headless writes `session_id=''` (ATLAS_SESSION_ID never set) → unroutable, swallowed | **Medium** | Route via `ATLAS_ACTIVE_SESSION` chain; surface routing failure instead of `try/except: pass` for accounting | **3, 6** |
| R17 | Chat IS trace_events (no session_id); "keep chat in control, move traces to runtime" is one table needing a write-time predicate | **Medium** | Specify `record_trace_event` routing: `chat_message`→control; session-scoped+non-chat→runtime; deterministic merge in Task 8 | **6, 8** |
| R18 | Forced rollback has no idempotency/ordering → double-delivery on retry; rollups unrebuildable | **Medium** | `INSERT OR IGNORE` preserving ids; stop workers first; audit row; run-twice test | **9, 7** |
| R19 | 100 distinct runtime DBs each pay full ~80-stmt bootstrap on cold spawn; widens accept-before-ready window | **Medium** | Runtime-only schema subset; pre-create at activation; measure cold-spawn p95 separately | **1, 2, 10** |
| R20 | Fail-open `_authorize_session_request` (`except: pass`→None) becomes cross-user read risk once reads span runtime DBs | **Medium** | Fail CLOSED; keep ownership lookup on control DB; inject-error test asserts 403 | **8** |
| R21 | local-admin/bypass + new runtime selector = arbitrary cross-user runtime read / path disclosure | **Medium** | Never echo paths; containment under root even in bypass mode; F4 grep asserts no `path`/`db_path` field + rejects `/ \ .. :` | **8, F4** |
| R22 | `cleanup_old_messages` purges undelivered prompts for cold workers | **Low** | Exclude `delivered_at IS NULL AND processed_at IS NULL` from age purge; test old-but-undelivered survives | **4, 9** |
| R23 | Manifest `runtime_db_path` trusted on read; no containment re-check | **Low** | Recompute expected path from session_uid+root on every open; reject out-of-root | **1, 7, 9** |
| R24 | Duplicate admin read surface (`atlas_admin.py` + `atlas_ui.py`) drifts | **Low** | Factor resolve+authz+containment into one shared helper; test both modules | **8** |
| R25 | Fleet observability (file vs manifest count, disk bytes, undelivered totals, orphan count) not wired | **Medium** | Add fleet gauges to the health/audit JSON the harness consumes | **9, 10** |

---

## 4. Revised task plan (10 tasks, 4 waves + Task 0)

Structure preserved. Anchors corrected, acceptance hardened, dependencies made explicit. **Bold "SCOPE↑"** marks tasks the grounding showed are bigger than the draft assumed.

### Task 0 (NEW, prerequisite) — Commit untracked baseline test
- **Goal:** make the DoD reproducible on a clean clone.
- **Files:** `tests/test_atlas_input_deep_runtime.py` (currently `?? untracked`).
- **Acceptance:** `git ls-files` shows the file tracked; DoD line-50 command passes on a fresh clone.
- **Dep:** none. Do first.

### Task 1 — `AtlasDBRouter` + Runtime Manifest **SCOPE↑**
- **Goal:** central resolution point; manifest; deterministic, traversal-safe paths.
- **Key files (verified):** new `core/atlas_db_router.py`; `core/atlas_db.py` (class `:593`, lock `:610`, `_connect` `:641`, `upsert_runtime_session` **`:1837`**, schema region `:74` sessions / `:209` queue); `core/session_names.py:40` (normalize — note: does NOT enforce 3 parts; 2-part namespaces valid, so path logic must not assume exactly 3 segments).
- **Critical acceptance:** `mode=central` → runtime path == control path; `mode=session` → manifest row + `<root>/<uid[0:2]>/<uid>.db`; basename is NOT `alice/ip_deep/rtl-gen`; traversal-like strings rejected.
- **New sub-steps (critiques):** (a) `session_uid` resolved-or-minted ONCE, persisted, never re-minted on retry [R4]; (b) fail CLOSED when no session_uid; derived-key fallback only under `ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY` (default off) [R15]; (c) recompute+containment-check path under `ATLAS_RUNTIME_DB_ROOT` on every open [R23]; (d) ship a runtime-only schema subset; measure init time [R19]; (e) correct the Task-1 reference to `core/atlas_db.py:1837`.
- **Dep:** Task 0. Blocks 3,4,6,7,8,9,10.

### Task 2 — Path-scoped locks **+ strict total-order queue (MERGED, SCOPE↑)**
- **Goal:** de-serialize different DB files; fix the ordering hazard before any split.
- **Key files (verified):** `core/atlas_db.py` lock **`:610`** (assigned `:634`), `_connect` **`:641`** (WAL/busy_timeout `:664-673`), dequeue **`:2424`** (`ORDER BY created_at` `:2449`), poll **`:2475`** (cursor `:2491`), `latest_output_id` (`session_process_manager.py:495`); tests `tests/test_atlas_db_concurrent_writers.py:49`, `tests/test_db_concurrent_workflow_runs.py:43`.
- **Critical acceptance:** same path serialized (existing tests green); **two-DB test: hold a BEGIN IMMEDIATE write on A, B completes < 200ms; a forced global-lock shim makes the same test TIME OUT** (proves de-serialization, not just no-error) [R11]; WAL/busy_timeout still applied; `_INITIALIZED_PATHS` guard preserved.
- **New sub-step (R1):** change dequeue/poll/`latest_output_id` ordering + cursor to monotonic `rowid` (`ORDER BY created_at, id`; value-based cursor); regression test with ≥2 rows at equal `created_at` asserts both returned once, lower id first. **This must land here, not deferred to Task 7.**
- **Dep:** none (can start with Task 1). Blocks 4, 10.

### Task 3 — Inject router into `SessionProcessManager` + worker env
- **Goal:** route DB paths; wire env without breaking the `--db-path` channel.
- **Key files (verified):** `core/session_process_manager.py` `_resolve_db_path:95`, `build_worker_env:111`, `spawn:271` (`--db-path` `:298`), `send_input:410`, `poll_output:465`, `latest_output_id:487`; `core/session_worker.py:108-111` (worker binds queue DB from `--db-path` ONLY); test `tests/test_process_based_sessions.py:111`.
- **Critical acceptance:** central mode keeps existing assertions; runtime mode → `--db-path == ATLAS_DB_PATH == ATLAS_TRACE_DB_PATH == runtime path` AND `ATLAS_CONTROL_DB_PATH == control`; `send_input`/`poll_output`/`latest_output_id` open the SAME runtime DB for a session. Add a runtime-mode sibling of `test_process_based_sessions.py:111`.
- **New sub-steps (critiques):** (a) the worker queue moves via `--db-path` ONLY — env vars only redirect secondary opens; ensure worker queue AND worker llm_calls land in the SAME runtime DB [R16]; (b) **stop calling `db.close()` on the hot poll/enqueue path** — router holds long-lived per-(thread,path) AtlasDB; assert opens-per-poll≈0 [R2]; (c) thread `session_id` through the `atlas_multiuser` callers (`poll_output:360`, `latest_output_id:478`, `send_input:748/770/878`).
- **Dep:** 1. Blocks 4.

### Task 4 — Move `session_queue` IPC to runtime DBs **SCOPE↑**
- **Goal:** per-session queue with no cross-DB lost/double prompts.
- **Key files (verified):** `core/atlas_db.py` schema `:209`, `enqueue_message:2388`, dequeue `:2424`, poll `:2475`, cleanup `:2516`; `core/session_worker.py:349` emit; tests `tests/test_atlas_input_deep_runtime.py:141`, `tests/test_db_schema_complete.py:462` (note: uses `direction='inbound'`, does NOT pin `in`/`out`).
- **Critical acceptance:** two sessions' in/out rows land in two runtime files; control queue empty in runtime mode; **value-based cursor makes forward progress; a `since_id` absent from the runtime DB yields a non-silent recoverable status, NOT 0 rows** [R5]; `sum(polled tokens) == sum(emitted)` per session (no silent drop).
- **New sub-steps (critiques):** (a) deterministic same-uid path on spawn-retry; init DB + manifest before ack; spawn-fail-then-retry test asserts exactly-once delivery [R4]; (b) `cleanup_old_messages` excludes undelivered/unprocessed rows; test old-but-undelivered survives [R22]; (c) **choose ONE recovery contract:** missing file → recreate + emit `runtime_db_recreated` metric (never silent); corrupt file → quarantine, manifest `status='error'`, surface error [R13/ops].
- **Dep:** 1, 3. Blocks 5, 10.

### Task 5 — Coalesce live output writes **SCOPE↑ (test seam)**
- **Goal:** cut token/reasoning row amplification; preserve order; zero frontend change.
- **Key files (verified):** `core/session_worker.py` emit `:349`, `emit_content:426`, `emit_reasoning:432`, `emit_tool_result` **`:540`**; `core/atlas_multiuser.py:346` (single expansion point, `put_nowait:393`); `core/react_loop.py:1059` (StreamParser per-LINE callbacks); browser `frontend/atlas/workspace-root-data-hook.tsx:699/715` (no `*_batch` subscriber → expansion mandatory).
- **Critical acceptance:** size-trigger test (1000 small emits, timer frozen, manual `flush()`) → ≤ N rows by 4KB math; **separate** time-trigger test advances fake clock past 50ms → exactly one flush; expanded text == input exactly; non-mergeable event forces flush in-position.
- **New sub-steps (critiques):** (a) build injectable `now_fn`/`monotonic_fn` + public `flush()` on the batcher (no seam exists today) [R9]; (b) **drop `file_changed`/`stop`/`interrupt`** from the never-coalesce set (not worker emits); test ordering against real emits (`token, tool/ask_user/cost/flush/agent_state, token`); (c) state `<=30` as a wall-time function, not flat.
- **Dep:** 4. Blocks 10.

### Task 6 — Route runtime persistence (`messages`/`trace_events`/`llm_calls`) **SCOPE↑**
- **Goal:** session-scoped writes to runtime DB; chat stays control.
- **Key files (verified):** `core/atlas_db.py` `save_message:1928`, `record_trace_event:3636`, `record_llm_call:3890`, `record_chat_message:3749` (NO session_id → delegates to trace_events); `core/react_loop.py:1380` (real call; `:1339` is comment; resolves via `_atlas_runtime_session_context`, can be `''`); `src/headless_workflow.py:1992-2010` (reads `ATLAS_SESSION_ID` — never set by `build_worker_env`); `src/orchestrator/react_bridge.py:703` (the ONLY real `ctx.session_id`); test `tests/test_react_loop_worker_llm_call_persist.py:88`.
- **Critical acceptance:** worker `llm_calls` land in runtime DB (control count 0 except rollups); user/global chat stays in control; central mode unchanged.
- **New sub-steps (critiques):** (a) route via `ATLAS_ACTIVE_SESSION` chain, NOT `ctx.session_id`/`ATLAS_SESSION_ID` [R16]; surface routing failure for accounting instead of silent `try/except: pass`; (b) specify `record_trace_event` write-time predicate: `event_type='chat_message'`→control; session-scoped non-chat→runtime [R17]; (c) headless worker with no session must not silently write `session_id=''`.
- **Dep:** 1. Blocks 7, 8.

### Task 7 — Control-DB usage rollups **SCOPE↑**
- **Goal:** admin/dashboard totals without runtime fanout.
- **Key files (verified):** new `core/runtime_rollup.py`; `core/atlas_db.py` (manifest/rollup tables), `summarize_llm_usage_for_user_ip` **`:3983`**, `list_run_artifact_version_sets:3162`; `core/atlas_admin_usage.py:112` (reads llm_calls + messages + parts + trace_events + todo_events); `core/atlas_user_dashboard.py:96` + `_workflow_runs:187`.
- **Critical acceptance:** idempotent across runs (run-twice keeps counts); rollup high-water on monotonic `rowid`/seq, NOT `(created_at, uuid)` [R1]; rollup-vs-raw totals equal; admin reads rollups without opening runtime files.
- **New sub-step (R8):** rollup schema must carry per-tool / intervention / todo-flow dims OR those tabs are explicitly "summary-only" with a marker — never silently empty.
- **Dep:** 1, 6. Blocks 8, 10.

### Task 8 — Update read paths for split data **SCOPE↑ (security)**
- **Goal:** route every runtime reader; safe raw-DB inspect; preserve isolation.
- **Key files (verified):** `src/atlas_api_sessions.py:637` (`_db_conversation_messages`), `:1010` (`_authorize_session_request`, fail-open); `src/atlas_api_chat.py:102/116/131`; `src/atlas_admin.py:438-465`; `core/atlas_admin_db.py:79` (table-NAME guard, NOT path guard); `src/atlas_ui.py:9428` + raw-DB `:9781-9817` (DUPLICATE surface). **Plus the omitted readers** (R7): `core/atlas_db.py:_recent_events_for_ip:4334`, `summarize_global_room_context:4444`, `list_chat_messages:3797`, `list_run_artifact_version_sets:3162`; `src/atlas_api_jobs.py:_recent_chat_context_for_ip:446`; `core/atlas_user_dashboard.py:_workflow_runs:187`.
- **Critical acceptance:** session history reads runtime DB; admin uses rollups; cross-user runtime read denied; **bogus/unresolvable session_uid → 404 with NO filesystem path in body**; missing/corrupt DB → explicit error, never false-empty.
- **New sub-steps (critiques):** (a) raw-browser: session_uid-only → manifest → containment under root + ownership; shared helper applied to BOTH `atlas_admin.py` and `atlas_ui.py` [R14/R24]; (b) `_authorize_session_request` fail CLOSED; ownership lookup stays on control DB; inject-error test asserts 403 [R20]; (c) test under `is_local_admin_mode()`/bypass that runtime inspect still scopes to manifest paths and never returns a path field [R21]; (d) "no silently-empty admin surface" parity test vs central mode for tool/todo/intervention/run-summary tabs.
- **Dep:** 6, 7. Blocks 10.

### Task 9 — Operational guardrails: rollback, cleanup, metrics, failure modes **SCOPE↑**
- **Goal:** durable lifecycle for ~100 on-disk runtime files.
- **Key files (verified):** `core/session_process_manager.py:410` (`[prompt-latency]` log), `:229-233` (orphan prune matches session+db-path); `core/atlas_db.py:2516` (cleanup), `:4812` (`_delete_session_metadata_on_conn`, control-only delete); `doc/wiki/db-concurrent-write-race-20260519.md`.
- **Critical acceptance:** health audit reports per-DB queue depth + `rollback_allowed`; forced rollback requires explicit flag + audit; missing/corrupt DB → clear status, no false history; metrics in JSON for the harness.
- **New sub-steps (critiques):** (a) reroute `_delete_session_metadata_on_conn` through router; delete file+wal+shm+manifest+rollup gated on queue_depth==0; orphan-GC job; zero-orphan test [R12]; (b) UI-restart recovery: oldest-undelivered cursor, PID reconcile, `_jobs` policy; undelivered-rows-replayed test [R13]; (c) forced rollback `INSERT OR IGNORE` preserving ids, workers stopped first, run-twice → one row [R18]; (d) fleet gauges: file vs manifest count, total bytes, undelivered totals, orphan count, oldest age [R25].
- **Dep:** 1, 4, 7. Blocks 10.

### Task 10 — 100-session verification harness **SCOPE↑ (validity)**
- **Goal:** prove the SLA on the REAL path, not the DB floor.
- **Key files (verified):** new `tests/test_runtime_db_100_user_scale.py`; styles from `tests/test_lazy_worker_cold_start_storm.py:125`, `tests/test_atlas_db_concurrent_writers.py:49`, `tests/test_multiuser_bridge.py:47`, `tests/test_atlas_input_deep_runtime.py:141`.
- **Critical acceptance:** p95 enqueue ≤ 250ms, p95 poll ≤ 500ms, zero lost prompts, zero cross-session rows, zero `database is locked`, rollup lag ≤ 10s; rollup totals == raw totals.
- **New sub-steps (critiques):** (a) **inject fake `_processes` so `list_active()`==100** and the harness drives `next_event()`/`_poll_process_outputs` (the serial fan-out + connect/close churn) — direct-AtlasDB numbers are a FLOOR, not the SLA [R6/R2/R3]; (b) measure cold-spawn (schema bootstrap + first enqueue) p95 as a SEPARATE metric [R19]; (c) per-session `sum(polled)==sum(emitted)` output-stall assertion [R5]; (d) make the ≥10-worker real-subprocess smoke (gated by `ATLAS_RUNTIME_DB_REAL_SUBPROCESS_STRESS=1`) the authoritative `--db-path` co-location check (queue + llm_calls/trace in same runtime DB) and run it in ≥1 CI lane.
- **Dep:** 1-9.

### Final Verification Wave (corrected)
- **F1 Plan compliance:** evidence file per task; central AND runtime modes pass.
- **F2 → split:** **F2a (baseline, runnable now):** `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_process_based_sessions.py tests/test_atlas_input_deep_runtime.py tests/test_atlas_db_concurrent_writers.py tests/test_atlas_multiuser_session_scope.py tests/test_react_loop_worker_llm_call_persist.py -q`. **F2b (scale, post-Task-10):** add `tests/test_runtime_db_100_user_scale.py`. (Draft's single F2 is unrunnable until Task 10 — R10.)
- **F3 Real runtime QA:** start UI with `ATLAS_RUNTIME_DB_MODE=session`, two sessions; live output arrives, runtime queues populated, control queue empty, rollups populate.
- **F4 Scope fidelity:** no Redis/Postgres; **no HTTP param accepts a path** (assert runtime inspect rejects `/ \ .. :` and never returns a `path`/`db_path` field, incl. under bypass mode — R21); no token-by-token insert path remains.

---

## 5. Open decisions for the user

1. **Queue ordering key:** switch to SQLite `rowid` (monotonic, simplest, recommended) or keep `created_at` with an `id` tiebreaker plus a new per-DB sequence column? (Determines cursor, dequeue, and rollup high-water consistency.) [R1]
2. **Runtime schema:** ship a runtime-only 5-table subset (cuts ~100× cold-spawn DDL and ~24 unused tables/file) or accept the full ~80-statement bootstrap per file? [R19]
3. **session_uid for unactivated sessions:** fail CLOSED (no uid → recoverable error, security-correct, recommended) or allow a derived-key fallback behind an off-by-default flag? [R15]
4. **Admin tabs that rollups can't reconstruct** (tool-usage, intervention, todo-flow): expand the rollup schema to carry them, or de-scope those tabs to "summary-only" in runtime mode? [R8]
5. **Forced-rollback history:** on rollback to central mode, re-import historical runtime messages/traces/llm_calls into control, or leave them orphaned (history truncates) and document it? [R18]
6. **Coalescing thresholds:** keep 50ms / 4KB, or different? (Affects the `<=N rows` bound and UI smoothness.)
7. **Retention:** archive vs hard-delete runtime `.db` on session delete, and the GC interval / max age for idle runtime files? [R12]
8. **SLA proof path:** is the synthetic-with-fake-`_processes` bridge path sufficient as the SLA gate, or do you require a ≥50-worker real-subprocess run for sign-off? [R6]

---

## 6. Execution recommendation

**Land router-first and behavior-preserving; flip `ATLAS_RUNTIME_DB_MODE=session` only after the correctness fixes are in.**

- **Commit first (do now): Task 0** — track `test_atlas_input_deep_runtime.py` so the DoD is reproducible. Tiny, unblocks F2a.
- **Wave 1 (parallel): Tasks 1, 2, 3.**
  - Task 2 is the **gate** — path-scoped locks AND the monotonic `rowid` ordering/cursor fix (R1/R5) must land before any split, with the two-DB de-serialization test (R11) and the equal-timestamp regression. Everything downstream depends on the queue being a strict total order.
  - Task 1 and Task 3 build the router and inject it in central mode (no behavior change yet). Task 3 also lands the hot-path connection-reuse fix (R2) — without it the latency targets are unreachable regardless of locks.
- **Wave 2: Task 4 → Task 5 (serial); Task 6 in parallel.** Task 4 flips the queue to per-session with deterministic-path accept atomicity (R4) and the value-based cursor (R5). Task 5 needs Task 4 + the new clock seam. Task 6 (depends only on 1) can run alongside; it carries the `ATLAS_ACTIVE_SESSION` routing fix (R16) and the trace/chat predicate (R17).
- **Wave 3 (parallel): Tasks 7, 8, 9.** 7 needs 6; 8 needs 6+7; 9 needs 1+4+7. 8 carries the security hardening (R14/R20/R21/R24); 9 carries lifecycle/orphan/rollback (R12/R13/R18/R25).
- **Wave 4: Task 10** with fake-`_processes` bridge driving (R6), cold-spawn measurement (R19), output-stall assertion (R5), then **F1, F2a (now), F2b (post-10), F3, F4**.

**Parallelism:** Waves 1 and the start of 2 can overlap once Task 2's ordering fix is merged (it's a precondition for 4). Tasks 6, 7, 8, 9 are largely independent surfaces and parallelize well within their dependency edges. The only hard serial spine is **2 → 4 → 5 → 10** (the queue correctness path) and **1 → (6,7,8,9) → 10**.

**Verify-as-you-go gates:** after Task 2, run F2a + the two-DB + equal-timestamp tests (proves de-serialization and total order before splitting). After Task 4, run the placement + exactly-once + cursor-progress tests. After Task 8, run the cross-user-deny + no-false-empty parity tests. Do not claim DoD until F2a passes on a fresh clone and Task 10's SLA runs through the real bridge path.