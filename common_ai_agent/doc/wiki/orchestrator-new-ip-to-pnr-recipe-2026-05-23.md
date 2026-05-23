# Orchestrator: new IP → PnR, green end-to-end (recipe)

> **Date:** 2026-05-23
> **Result:** A brand-new IP `orch_pnr_182839` ("8-bit synchronous up
> counter") was driven by the orchestrator from a single chat instruction
> all the way to **PnR passing — all 11 stages green.** This is the
> working counterpart to the earlier blocked run documented in
> [[orchestrator-pnr-run-issues-2026-05-23]].

---

## Final stage result

```
ssot ✓  fl-model ✓  equivalence ✓  rtl ✓  lint ✓
tb ✓    sim ✓        coverage ✓     syn ✓  sta ✓  pnr ✓   → PNR_PASSED
```

Timing shape (single new IP, glm-5.1 low-effort workers):
- ssot → fl-model → equivalence → lint: first ~15 min (each a real LLM
  authoring pass)
- rtl: the long pole (~7–10 min — heaviest authoring stage)
- tb → sim → coverage → syn → sta → pnr: the last six closed in ~30 s
  total once RTL landed (light EDA stages run fast).

## What made it work (vs the earlier blocked run)

The earlier run stalled at SSOT because the worker exited mid-run (run
expired at 2× the 600 s TTL while glm-5.1 "thought") and the job stuck at
`running`. Two settings fixed it, plus one code fix:

1. **`AGENT_SERVER_RUN_TTL=3600`** — workers survive ~2 h instead of being
   killed at 20 min, so a slow authoring pass is not reaped mid-flight.
2. **Low reasoning effort on workers** — `ATLAS_WORKER_REASONING_EFFORT_*
   = low` for every workflow. glm-5.1 at low effort finishes stages in
   minutes instead of spinning for 20+ min.
3. **Stuck-job guard** (committed) — if a worker DOES go unreachable, the
   status poller now marks the job `error` after N failed polls so the
   orchestrator's `wait_job` sees a terminal state and can react instead
   of hanging forever (`src/atlas_api_jobs.py`,
   `ATLAS_JOB_POLL_FAIL_LIMIT`).

## Repro recipe

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent

# 1. Launch orchestrator server with survivable + fast workers
export AGENT_SERVER_RUN_TTL=3600
export ATLAS_ORCHESTRATOR_REASONING_EFFORT=low        # routing layer is light
export ATLAS_LAZY_WORKER_START_TIMEOUT=45
for S in SSOT_GEN FL_MODEL_GEN RTL_GEN LINT TB_GEN SIM COVERAGE \
         SIM_DEBUG SYN STA PNR STA_POST; do
  export ATLAS_WORKER_MODEL_${S}=glm-5.1
  export ATLAS_WORKER_REASONING_EFFORT_${S}=low
done
python3 src/atlas_ui.py --port 3001 --root /path/to/ROOT_IP \
  --workflow-root "$PWD" --exec o --host 127.0.0.1

# 2. Drive it (login admin/1151, then one chat message)
POST /api/pipeline/orchestrator/chat
  { "message": "Build an 8-bit synchronous up counter and drive the entire
                pipeline to green through place-and-route. Auto-advance
                every stage in DAG order; do not pause.",
    "ip": "orch_pnr_<id>" }

# 3. Watch
GET /api/pipeline/state?ip=orch_pnr_<id>   # stages flip pending→running→passed
GET /api/orchestrator/runs/<run_id>         # orchestrator step history
```

## How the orchestrator drives it (mechanism)

The orchestrator is a ReAct loop (gpt-5.5). Per stage it:
`read_pipeline_state → dispatch_workflow(<stage>) → yield_run(wake_on=
{job_ids, user_message, after_seconds}) → [worker runs] → wake → read
state → dispatch next`. `yield_run` parks the loop so it doesn't burn LLM
calls while a worker grinds; it wakes on job completion, a user message,
or a timeout. Workers lazy-spawn on first dispatch (per-user hashed
ports 5700+).

## Gotchas to avoid (learned this session)

- **Don't put `for <word>` / `on <word>` in the chat message.** The IP
  extractor (`_extract_ip_from_orchestrator_message`) parses those and
  hijacked the IP to `confirmation` once. Prefer the explicit `ip` field
  and avoid those phrases. (Open fix in the issues doc.)
- **gpt-5.5 needs `USE_OPENCODE_OAUTH=true`** in `.config`, else the
  ChatGPT-backend call 403s and the "answer" is a 403 HTML page. The
  OAuth token in `~/.local/share/opencode/auth.json` is valid; the switch
  just has to be on.
- **A still-`running` stage with a dead worker** = the stuck-job bug;
  the poll-fail guard now converts it to `error` so the loop continues.

## See also
- [[orchestrator-pnr-run-issues-2026-05-23]] — the punch list (IP
  extractor, spurious rtl:failed, run-expiry, worker model speed).
- [[atlas-test-feature-coverage]] — which test gates which feature.
