---
title: Orchestrator + Single-Worker E2E (chat/log/IP) 2026-05-26
type: run
tags: [atlas, e2e, orchestrator, single-worker, chat-persistence, ssot-gen, latency, ux, validation]
created: 2026-05-26
related: [atlas-e2e-validation-20260519, atlas-pipeline-db-state, atlas-new-ip-recipe]
---

# Orchestrator + Single-Worker E2E (chat / log / IP) 2026-05-26

Goal: drive both exec modes, switching chats, verifying chat persistence, log
visibility, and IP creation (ssot/rtl/sim) ~10×; fix what breaks; UX matters.
Harness: `scripts/ui_tests/goal_mode_matrix.py` (stdlib urllib, isolated throwaway
users + unique IPs against the live server, in-band finalize to bound billing).

## Verified (both modes)

- **Chat persistence + isolation**: `/api/pipeline/orchestrator/chat` writes the
  user message to the trace ledger *before* the run starts; messages survive and
  stay scoped per IP. Read back via `/api/orchestrator/chat/messages?ip=`.
- **Log quality**: full reasoning trace replayable —
  `[user] → [assistant] → [tool dispatch_workflow] → [tool_result] → [tool yield_run]`.
- **IP creation (ssot)**: orchestrator produced a real 50 KB SSOT (`TBD=0`,
  `type: draft` gone, `function_model` present). create_ip seeds a *scaffold*
  ssot/rtl first; real ssot-gen overwrites it.

## Root cause of "slow / stuck" — quantified

`atlas.db.llm_calls` measured:

| worker model | latency / call | output tokens |
|---|---|---|
| **glm-5.1** | **78–81 s** | ~100 |
| gpt-5.3-codex | 9–11 s | ~400 |

glm-5.1 is a reasoning model: ~80 s even for tiny outputs, ~8× slower than
gpt-5.3-codex. ssot-gen makes several sequential calls → 15–20 min/stage. The
SSOT artifact is written early but the stage stays `running` through the slow
validation tail (`workflow_runs.status` stuck `running`, worker PID alive at
0 % CPU = blocked on LLM I/O). Orchestrator dispatches then `yield_run`s
(after_seconds=300) waiting for a `job_complete` that lags → user sees a spinner
that never finishes. DB/git/IO are all sub-ms — the bottleneck is entirely LLM.

`_WORKER_MODEL_DEFAULTS` (src/atlas_api_jobs.py) *intends* fast workers
(ssot-gen→gpt-5.5, rtl-gen→gpt-5.3-codex) and `ORCHESTRATOR_MODEL` defaults to
gpt-5.5, but the live server boots with the user's `.env` (`LLM_PROFILE=glm`,
`LLM_MODEL_NAME=glm-5.1`), so workers execute on glm-5.1 and the fast
per-workflow defaults are nullified.

**Lever**: set `ATLAS_WORKER_MODEL_<SUFFIX>` (e.g. `ATLAS_WORKER_MODEL_SSOT_GEN=gpt-5.5`)
or boot workers with a fast model. Model choice is a billing/quality decision —
surface, don't silently change.

## Fixes shipped (tested)

1. **`/context -v` empty window** (core/slash_commands.py): a fresh session shows
   "Current context window is empty (no messages this session yet)" + points to
   `/context -v -full` when a durable log exists — instead of a bare "No message
   history available".
2. **`/context -v -full` dead-end** (core/slash_commands.py): when no `SESSION_DIR`
   (session started without a project name), fall back to CWD
   `full_conversation.json` / `conversation_history.json` instead of
   "No session directory — run with a project name". Now surfaces the 613-message
   history that was on disk all along.
3. **Fresh IP shows `rtl=failed`** (src/atlas_api_jobs.py): create_ip's scaffold
   `rtl/<ip>.sv` (TODO/placeholder) + `list/<ip>.f` tripped the artifact
   validator → red `rtl` before rtl-gen ran. Gated the placeholder + disk-checker
   *and* the recovery (false-green) on a real verdict artifact
   (`rtl_compile.json` / `logs/stage_engine/ssot-rtl.json`). A never-run scaffold
   now reads `locked`/`idle`, not `failed` or `passed`. Regression test:
   `test_pipeline_state_scaffold_rtl_not_failed_before_rtl_gen_runs`.

Earlier same session: AtlasDB schema-init de-dup (`with AtlasDB()` 7.85 ms → 0.012 ms).

All: 90 pipeline/jobs/worker tests pass.

## Gotchas

- Worker model glm-5.1 → ~80 s/call; expect ssot-gen 15–20 min on the live server.
- `state == 'passed'` lags well behind the real artifact; key "did it make the IP"
  checks on the artifact (TBD-free, has function_model), not the state label.
- IP names must match `^[A-Za-z][A-Za-z0-9_]*$`; avoid "for/on <noun>" in chat
  (IP-extractor hijack). Finalize runs after driving (auto-advance is billable).
