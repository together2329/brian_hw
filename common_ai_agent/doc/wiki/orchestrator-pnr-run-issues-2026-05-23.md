# Orchestrator full-pipeline (→ PnR) run — issue punch list

> **Date:** 2026-05-23
> **Context:** Drove a brand-new IP `orch_demo_173125` ("8-bit synchronous
> up counter") through the orchestrator with a single chat instruction
> ("run to green through PnR"). The orchestrator dispatched ssot-gen and
> then **stalled at SSOT** — never advanced to fl-model.
> **Goal at the time:** `pnr까지` (reach place-and-route).
> **Outcome:** Blocked at the very first stage. Below is what works, what
> doesn't, and the concrete fixes for a later session.

---

## What worked ✅

- Orchestrator chat (gpt-5.5 via OpenCode OAuth) accepted the new IP and
  ran its decision loop: `read_pipeline_state → dispatch_workflow →
  wait_job → …`. This is genuinely orchestrator-driven (verified via the
  run step history, not hand-dispatched).
- `dispatch_workflow(ssot-gen)` lazy-spawned a per-user worker on
  `127.0.0.1:6900` (lazy-spawn path works).
- ssot-gen produced a real, on-spec **6.4 KB SSOT YAML**
  (`ROOT_IP/orch_demo_173125/yaml/orch_demo_173125.ssot.yaml`) — correct
  top_module, sub_modules, description matching the 8-bit counter ask.

## What broke ❌ (fix these)

### P0 — worker shuts down mid-run → job stuck `running` → orchestrator waits forever
- Worker log (`.session/workers/ssot-gen-6900.log`) ends with:
  ```
  [cleanup] Removed 1 expired run(s)
  INFO:     Shutting down ... Finished server process [88921]
  ```
- The ssot-gen worker spent a very long time `Thinking…` on **glm-5.1**
  (primary 7/60), the run was declared **expired** by a cleanup pass, and
  the worker process **exited**.
- The SSOT file was already written, but the job in `_jobs` stayed
  `status="running"` with `err: poll failed: <urlopen error [Errno 61]
  Connection refused>` — the status poller can't reach the dead worker, so
  it never transitions to `completed`.
- The orchestrator's `wait_job` therefore sees `running` forever and never
  dispatches the next stage. **This is the single blocker for the whole
  pipeline.**
- **Fix candidates:**
  1. When a status poll gets `Connection refused` AND the stage's primary
     artifact exists on disk (e.g. the SSOT YAML), reconcile the job to
     `completed` instead of leaving it `running`.
  2. Make the lazy-worker **reaper** also cover orchestrator-direct
     per-user-port workers (5700+ hashed ports), not just the
     `_LAZY_WORKER_PROCS` registry — right now a worker that exits on its
     own (not via `proc.terminate()`) may not be reconciled.
  3. Don't let a worker shut down while it still owns an unfinished job;
     or on shutdown, write a final `completed/error` status the parent can
     read.

### P0 — run "expired" cleanup is too aggressive for slow workers
- glm-5.1 with deep thinking on ssot-gen exceeded the run-expiry window
  and got cleaned up mid-flight. Either raise the expiry for actively
  "running" worker runs, or treat "artifact written" as keep-alive.

### P1 — `rtl` stage shows `failed` although it was never dispatched
- Pipeline state reported `rtl: failed` (scoresheet all `idle`) while
  fl-model/equivalence were `locked` and rtl had never run. Spurious /
  stale state in the pipeline view; should be `locked`/`pending` until rtl
  actually runs.

### P1 — IP extractor hijacks natural-language words as the IP
- `src/atlas_api_jobs.py:_extract_ip_from_orchestrator_message` matches
  `\bfor\s+<token>\b` / `\bon\s+<token>\b` against the message body and
  prefers it over the explicit `ip` field. The message "...do not stop
  **for confirmation**" made it dispatch to IP `confirmation`.
- **Fix:** prefer the explicit `ip` body field when present and valid;
  only fall back to message parsing when `ip` is empty. Or exclude a
  stop-word set (confirmation, now, green, help, status, …).

### P2 — model split surprises (slow)
- Orchestrator runs gpt-5.5 (OAuth) but the dispatched **workers default
  to glm-5.1** (`.env LLM_PROFILE=glm`). glm-5.1 deep-thinking is very slow
  on ssot-gen, which is what triggered the expiry. Consider a faster
  worker model/effort default for early stages, or surface the per-stage
  model in the UI so the slowness is explainable.

### P2 — monitor "continue" nudges add noise
- Polling-side "continue" nudges land as `user_reply` → `yield_run` churn
  in the run history. Harmless but inflates step count and can re-pause the
  loop. The orchestrator should auto-advance on `wait_job` completion
  without external nudging once P0 is fixed.

---

## Repro

```bash
# server: orchestrator mode, gpt-5.5, USE_OPENCODE_OAUTH=true
python3 src/atlas_ui.py --port 3001 --root <ROOT_IP> \
  --workflow-root <common_ai_agent> --exec o --host 127.0.0.1 --model gpt-5.5

# login admin/1151, then:
POST /api/pipeline/orchestrator/chat {message:"...counter...start from SSOT", ip:"orch_demo_X"}
# watch: GET /api/pipeline/state?ip=orch_demo_X  → ssot stuck "running"
# root cause: .session/workers/ssot-gen-<port>.log ends in "Shutting down"
```

## Priority order for the fix session
1. P0 job-reconciliation on dead-worker poll (artifact-exists → completed)
2. P0 run-expiry keep-alive for active runs
3. P1 IP-extractor explicit-ip preference
4. P1 spurious `rtl: failed`
5. P2 worker model/effort + nudge noise
