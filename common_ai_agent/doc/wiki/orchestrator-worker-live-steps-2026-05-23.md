# Orchestrator worker live steps in the detail view — findings + TODO

> **Date:** 2026-05-23 · **Status:** in progress · **Priority: HIGH**
> When you click the orchestrator-chat worker strip chip (`▶ ssot-gen running`),
> the detail view must show the worker's **live ReAct steps** (what it's
> actually doing), not just a "workflow switched" message. This is the gap the
> mockup promised. See [[atlas-ui-playwright-screenshot-recipe-2026-05-23]] for
> how we capture/verify it.

## Root cause (verified live on :3001)

1. **Session-location mismatch (the core bug).**
   - On chip click the UI switches to session `<owner>/<ip>/<workflow>` and the
     feed hydrates from `.session/<owner>/<ip>/<workflow>/conversation.json` —
     which is **EMPTY** for orchestrator-dispatched workers (probe: `/api/session/state?mode=conversation` → `n:0` for 4 sessions).
   - The orchestrator-dispatched worker actually writes to a **different path**:
     `.session/<owner>/<ip>/pipeline/<run_id>/NN-<stage>/{todo.json,cost.json}`
     (no `conversation.json` there either).
2. **DB angle.** Orchestrator *chat* → DB `chat_messages` → faux-stream poll
   (`/api/orchestrator/chat/messages`) → works. Worker *steps* are **not** in DB
   chat and **not** in the session conversation the UI reads.
3. **The worker's ReAct transcript IS available live — just not wired to the UI.**
   `/api/job/{job_id}/log` proxies the worker agent-server's `GET {worker}/log/{run_id}`
   and returns live entries. **Verified:** dispatched ssot-gen, polled
   `/api/job/<jid>/log?tail=6` → `entries=6 types=system,context,plan,task,action`
   while running. Falls back to (empty) session conversation only if the worker
   call fails.
4. **(ip, workflow) → running job_id mapping** exists:
   `/api/pipeline/progress-debug?ip=<ip>` → `_summarize_worker_progress`
   (`src/atlas_api_jobs.py:918`) → `active: [{job_id, run_id, workflow, worker, status, elapsed_sec, ...}]`.

## Conclusion
The data + endpoints already exist. **B (live transcript) is a frontend-only
wire-up** mirroring the orchestrator faux-stream poll. A (task progress) comes
from the same job log / todo.json.

## What changed (2026-05-23) — B DONE & verified

- [x] **B — live transcript poll (frontend).** Added an effect in
      `frontend/atlas/workspace.jsx` (sibling to the orchestrator faux-stream
      poll): when `workflow !== 'orchestrator'` && active IP, it resolves the
      running job for (ip, workflow) via `/api/pipeline/progress-debug?ip=`
      (matches `worker.active[].workflow`/`stage_id`), then polls
      `/api/job/{job_id}/log?since=<lastIndex>` every 1.5s and appends new
      entries to the chat feed. Dedupe by `entry.index`; stops when job ends.
- [x] **Map entry.type → feed kind.** `response/assistant→agent`,
      `action→action`, `observation→obs`, everything else
      (`task/plan/context/system/thought`)→`thought` (context truncated 1200ch).
- [x] **Verified live:** orchestrator-dispatched ssot-gen → switch to the
      `ssot-gen` worker session → **CHAT** tab shows the worker's real steps
      (e.g. `thought: LLM runtime active: model=glm-5.1 effort=low`, 10 feed
      elements). `progress-debug` correctly returned the orchestrator job
      (`job_id` + `worker` url), so the (ip,workflow)→job_id mapping works.

## Still open

- [ ] **UX: worker session defaults to the VALIDATION tab, not CHAT.** The user
      lands on the stage tool and must click **CHAT** to see the transcript.
      Make a chip-click (or opening a worker session with a running job) surface
      the CHAT tab automatically.
- [ ] **A — progress header.** Show `<workflow> · <done>/<total> · <current task>`
      above the transcript, from `todo.json` (`pipeline/<run_id>/<stage>/todo.json`)
      or job status/elapsed from progress-debug.
- [ ] **Optional inline.** Let the orchestrator strip chip expand to a mini live
      progress without leaving the orchestrator chat.
- [ ] **Test:** add `scripts/ui_tests/worker_detail_live.mjs` — dispatch → switch
      → CHAT tab → assert feed gains transcript entries; screenshot. Cleanup
      in-band (finalize as blocked); never kill shared canonical workers.

## Key files
- Backend (read-only, already works): `src/atlas_api_jobs.py` — `/api/job/{job_id}/log` (~6036, proxies `{worker}/log/{run_id}`), `/api/pipeline/progress-debug` (~4001), `_summarize_worker_progress` (918).
- Frontend (to change): `frontend/atlas/workspace.jsx` — add the worker-log poll next to the orchestrator faux-stream poll; render via the existing feed (`data-kind`).
