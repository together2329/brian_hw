# Draft: Single Active Session Worker For 100 Users

## Requirements (confirmed)
- "Single Worker Mode에서 atlas ui 를 통해 어떻게 user 별 worker를 실행시키고 죽이는지 어떻게 유지하는지 조사좀"
- "session worker 는 뭐야? atlas_ui.py ?"
- "single mode 에서는 session worker가 user 별로 ?"
- "workflow 가 달라지면 session worker도 달라지나"
- "내가 원했던 single worker 컨셉은 한개를 띄우고 workflow command로 전환하는거 였는데 좀 다르게 구현이 되었군"
- "근데 어쩌피 orchestrator mode를 쓴다면 이런 session 별 worker mode 를 쓰는게 나중을 위해 좋으려나? 커버리지 관점"
- "나중에는 rtl-gen 도 여러 worker 들이 합심해서 하면 좋을 것 같거든."
- "subworker call 방식도 구현은 되어 있잖아 그지?"
- "근데 orchestrator mode 에서 각 worker 호출후 worker chatting 창에 작업 내용이 잘 보일까 현재?"
- "여기서 여러 rtl-gen sub worker 흐름까지 더하는거 가능?"
- "이 논의 내용 wiki에 추가."
- "single active session worker 구조에서 어떻게 동작해야 하는지. 100명이 사용하기에 충분한 구조인지 검토좀."
- "그럼 어떻게 헤야 할지 계획좀"

## Technical Decisions
- Treat `src/atlas_ui.py` as the Atlas control plane, not as the session worker.
- Treat `core.session_worker` subprocesses launched by `core/session_process_manager.py` through `core/atlas_multiuser.py` as interactive session workers.
- Define the near-term target as one active interactive session worker per authenticated owner/user.
- Keep the persisted namespace as `<owner>/<ip>/<workflow>` for history, DB rows, artifacts, and UI routing.
- Do not implement true in-process workflow mutation first; switch by stopping/exiting the old session worker and starting/warming the new context worker.
- Keep orchestrator workflow/job workers separate from interactive session workers.
- Do not add multi-lane `rtl-gen` subworkers in this first implementation; prepare naming/status seams and cover worker chat/log visibility first.
- Default capacity target: 100 registered users and bounded active concurrency. Use configurable limits before claiming 100 simultaneous high-output workers.
- Define "active interactive worker" as an alive `core.session_worker` OS process, not merely a currently running prompt.
- In single-active mode, workflow/IP switch must complete old worker termination before new worker warmup; no overlap is allowed.
- The owner slot key is the normalized browser/auth owner after `_session_owner_with_model()`, because that is the visible session namespace owner currently used by activation.
- `preserve_running=true` is honored only for orchestrator workflow/job focus changes; it must not keep an extra interactive session worker alive in strict single-active mode.
- Workflow switch uses graceful stop/request-stop, waits for acknowledgement or process exit, then hard kills after timeout.
- Interactive worker backpressure returns a visible `queued`/`capacity_wait` state for warmup and prompt attempts; it must not silently drop prompts.

## Research Findings
- `src/atlas_ui.py:1108` creates the FastAPI control plane; `src/atlas_ui.py:1167` instantiates `_MultiUserBridge`.
- `src/atlas_ui.py:1132` reads `ATLAS_SINGLE_WORKER_PER_OWNER` / `ATLAS_SINGLE_WORKER_PER_USER`; default is false at `src/atlas_ui.py:1145`.
- `src/atlas_api_sessions.py:74` enables session worker keepalive by default when exec mode is `single-worker`.
- `src/atlas_api_sessions.py:276` handles workflow/IP/user triple changes, but `preserve_running` changes stop/kill behavior.
- `core/atlas_multiuser.py:621` kills owner sibling workers only when `_single_worker_per_owner` is true.
- `core/atlas_multiuser.py:725` activates sessions; warm/spawn is separate through `warm_session`.
- `core/session_process_manager.py:452` spawns `python -m core.session_worker --session-id ... --db-path ...`.
- `core/session_process_manager.py:553` tracks active worker processes in memory and has no global admission limit in the interactive session-worker lane.
- `src/atlas_api_jobs.py:119` has orchestrator IPC worker limits, but those limits do not cap interactive session workers.
- `src/atlas_api_jobs.py:6213` dispatches orchestrator workflow jobs through `_dispatch_workflow_tool_bridge`, creating per-stage job records.
- `frontend/atlas/agent-worker-status.tsx` and `/api/orchestrator/workers` already expose workflow worker status, but chat transcript visibility still depends on job/log mapping.
- Existing `plans/atlas-runtime-db-100-users.md` covers runtime DB/session queue scaling; this plan should not duplicate DB-router work.
- Existing `doc/wiki/atlas-single-active-orchestrator-subworkers-20260603.md` records the design discussion and future subworker direction.

## Open Questions
- If the operator wants 100 simultaneous high-output interactive workers, the DB/runtime plan must be completed and load-tested first. This plan assumes bounded active concurrency with queue/backpressure.
- Exact production defaults for active worker cap and idle TTL can be tuned, but the plan will choose conservative defaults so implementation does not need to decide.
- Metis ambiguity resolved for planning: active means alive process; no handoff overlap; owner slot uses normalized owner-with-model; target load is 100 logged-in/session namespaces with cap-enforced active workers.

## Scope Boundaries
- INCLUDE: interactive session-worker lifecycle policy, owner-level active slot enforcement, stop/exit/kill semantics, idle TTL/reaper, admission control, UI/API worker-state contract, focused tests, and load harness.
- INCLUDE: orchestrator worker chat/log visibility verification and status distinction between interactive session worker and workflow job workers.
- EXCLUDE: actual `rtl-gen` subworker fanout implementation.
- EXCLUDE: Redis/Postgres queue migration.
- EXCLUDE: source code changes during planning.
