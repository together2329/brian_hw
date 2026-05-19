# Flow Fixes Verification — 2026-05-19

Live UI verification of five landed fixes (commits f17e66c41, 207f87c19,
acb1c849e, 7709566d9 plus the partial DB-path unification). Verifier:
`verifier-cmux`. Environment: ATLAS UI `127.0.0.1:62196`, model `gpt-5.5`,
effort `xhigh`, restarted to pick up Python source changes.

Cross-links: [[atlas-pipeline-screen]] · [[orchestrator-chat-ux]] ·
[[ssot-rtl-flow-verify-20260519]] · [[atlas-browser-control-runbook]].

## TL;DR Verdict

| # | Fix | Commit | Verdict | Evidence |
|---|---|---|---|---|
| 5 | seed propagation → worker prompt | f17e66c41 | FAIL | `workflow_runs.trigger_source` empty for the IP-aware run |
| 6 | workspace_id alignment chat/dispatch | 207f87c19 | FAIL | Two `ip_blocks` rows with the same `ip_name` (UI-create `956f979d…` vs worker-create `a5705f61…`) |
| 7 | workers write `llm_calls` + `cost_usd` to atlas.db | acb1c849e | FAIL | No `workflow='ssot-gen'` rows in either DB after a live worker run; only stale `orchestrator` rows with `cost_usd=0.0` |
| 8 | Document Import UI button | 7709566d9 | BLOCKED | Chat panel did not mount under `ip=cmux_verify_5fix` (`view=pipeline`); `IpxactImportBtn` global exists but DOM count 0; cannot exercise the button |
| 9 | unify atlas.db path | (prior task) | PARTIAL (as flagged) | `workflow_runs` and `ip_blocks` for this run landed only in `HOME` DB; `llm_calls` totals: HOME=7, PWD=622 — split persists |

Net: **0/5 PASS**. P0 chain (seed → workspace alignment → worker cost) is broken
for the chat-path even after restart.

## Restart confirmation

```
killed PID 27161 (5fix-pre)  →  port 62196 free  →  nohup atlas_ui.py …
nohup PID=45576
curl http://127.0.0.1:62196/ → HTTP=200
```

`atlas_ui.log` confirms cold start (`[atlas] Multi-user enabled`,
`[Workflow] 'orchestrator' loaded via /api/session/activate (prev='', ip='default')`).

## Verification scenario

1. cmux Chrome (`surface:9`, then `surface:14`) already logged in as
   `validator`. `+ IP` button → typed `cmux_verify_5fix` → clicked OK.
   `ip_blocks` row appeared in HOME db with `id=956f979d01204666a12a893fb0778b8b`.
   PWD db: 0 rows for this name → already evidence of split DB.
2. After IP create the URL flipped to
   `?session=validator/cmux_verify_5fix/ssot-gen&workflow=ssot-gen`. The
   `view=pipeline` page rendered the IP/workflow header but **did not mount
   the chat `<textarea>`** (0 inputs, body innerText empty after reload).
   `localStorage.atlasActiveSession` had been forcibly set to
   `validator/cmux_verify_5fix/ssot-gen` but the React tree showed
   `bodyChildren=5, classNames=[""…]` — Babel-in-browser compile finishes,
   but the SPA short-circuits the chat panel for this IP/workflow combo.
3. `window.backend.send` trace patch confirmed: when chat *did* exist
   transiently it shipped payload
   `session: "validator/default/default"` regardless of URL `ip=` — the
   chat panel reads from `atlasActiveSession`, not from URL.
4. Fallback: direct WS to `ws://127.0.0.1:62196/ws/agent` with the browser
   `atlas_session=…` cookie + `Origin` header. Server replied `hello`,
   `agent_received(session_id=validator/cmux_verify_5fix/ssot-gen)`,
   `worker_started(pid=11072)`. So backend honours the session string from
   the wire; the **chat panel never sent that string** in the live UI run.

## Evidence per fix

### Fix #5 — seed propagation in dispatch_workflow (FAIL)

`workflow_runs` for the worker that the WS bypass spawned:
```
ssot-gen|running||a5705f61e5b74951ba54f69b075c1663|1779185718.23
```
`trigger_source` column is the empty string. The chat-only echo case earlier
in this DB shows the seed propagating once (`orchestrator_chat` against
ip `18161f65…`), so the fix works on the orchestrator-chat path but does
**not** propagate when the worker is spawned out of an explicit `ssot-gen`
session. Worker therefore had no seed prompt: `ssot.yaml` is still the
canonical scaffold with every field `TBD` after 5+ minutes of wallclock.

Proposed follow-up: have `dispatch_workflow` carry the seed onto the
non-chat ssot-gen path as well (search `runner.py` for the
`trigger_source='orchestrator_chat'` site and mirror it).

### Fix #6 — workspace_id alignment (FAIL)

```
sqlite> SELECT id, ip_name FROM ip_blocks WHERE ip_name='cmux_verify_5fix';
956f979d01204666a12a893fb0778b8b|cmux_verify_5fix   ← UI create
a5705f61e5b74951ba54f69b075c1663|cmux_verify_5fix   ← worker create
```
Two rows for the same logical IP — the chat/dispatch path generated a fresh
ip_id rather than reusing the UI one. Downstream artefacts therefore split
into two namespaces and queries keyed off either id miss half the truth.

Proposed follow-up: in the chat-path workspace lookup, resolve
`ip_blocks.id` by `(owner, ip_name)` before insert.

### Fix #7 — worker llm_calls + cost_usd (FAIL)

HOME atlas.db `llm_calls` total: **7 rows**, all `workflow='orchestrator'`,
all `cost_usd=0.0`. PWD atlas.db `llm_calls` total: **622 rows** but the
newest (`created_at > now-15m`) is **0**. Worker PID 11072 has been live
for 5m+ and the WS stream shows real `token_usage` frames (input ≈ 18 k,
output ≈ 500 per turn) — none of those landed in either DB.

Proposed follow-up: in `core/session_worker` (or wherever
`acb1c849e` patched), confirm the writer is invoked from the
ssot-gen worker, not only from the orchestrator chat path, and verify the
DB path resolver picks up `ATLAS_DB_PATH`.

### Fix #8 — Document Import UI button (BLOCKED)

`IpxactImportBtn` is a registered global; no `📄 Import Doc` button text
was reachable from `view=pipeline` because the chat/SSOT pane did not
mount under `ip=cmux_verify_5fix`. The button cannot be exercised in this
session without first fixing #6 (chat panel mount under non-default IP).

Proposed follow-up: smoke-test the button in `ip=default` first — if it
renders there, the gating is the same as #6.

### Fix #9 — DB path unification (PARTIAL, expected)

Confirmed flagged behaviour: this run's `workflow_runs` and `ip_blocks`
landed in `HOME`, while `llm_calls` historical mass is in `PWD`. New
ssot-gen worker rows landed in **neither**, which is a separate bug
(see #7).

## Chat body dump

```
url: http://127.0.0.1:62196/?session=validator/cmux_verify_5fix/ssot-gen
       &ip=cmux_verify_5fix&workflow=ssot-gen&session_id=validator&view=pipeline
inputs: []
entryCount: 0
```

i.e. the chat panel did not mount on the IP-aware URL after reload —
the entire UI verification surface is missing for this case.

WS bypass frames (truncated):
```
<< hello {frontend: 'atlas', running: False, chat_feed_summary: True}
<< agent_received {msg_id: 47d116e4…, session_id: validator/cmux_verify_5fix/ssot-gen}
<< worker_started {pid: 11072, session_id: validator/cmux_verify_5fix/ssot-gen}
<< reasoning **Considering task requirements**
<< token_usage {input: 18919, cached: 0, output: 558}
<< flush
<< todo  ── TODO ── ⏸ 1. Inspect cmux_verify_5fix workspace and SSOT validation assets
<< todo  ── TODO ── ⏸ 2. Author cmux_verify_5fix…
<< token_usage {input: 19697, cached: 18944, output: 78}
<< todo  ── TODO ── ▶ 1. Inspect cmux_verify_5fix workspace and SSOT validation assets
[recv idle 222s] frames so far: 33
```

## Attachments

- `/tmp/verifier_cmux/screen_postreload.png` — pipeline view after reload (black)
- `/tmp/verifier_cmux/screen_s14_orchestrator.png` — alt surface, identical state
- `/tmp/verifier_cmux/screen_final_s9.png` — final shot
- `/tmp/verifier_cmux/ws_prompt.py` — WS bypass script

## Edge case

`llm_calls` for `workflow='orchestrator'` with `cost_usd > 0`: **none**
(`cost_usd=0.0` on all 7 HOME-db rows). f17e66c41 wired the chat → worker
seed, but the cost-writer landed earlier on the orchestrator path has not
produced positive cost rows here either.

## Recommended priorities

1. **#7 first** — without `llm_calls` writes the cost panel never updates,
   blocking the entire observability story.
2. **#6 next** — `ip_blocks` duplication contaminates every downstream
   query.
3. **#5 then** — once #6 is sound, propagate seed on the non-chat path.
4. **#8 last** — likely unblocks itself when #6 lands.

DB-path unification (#9) should remain PARTIAL until the writes from #7
land in a single canonical DB.
