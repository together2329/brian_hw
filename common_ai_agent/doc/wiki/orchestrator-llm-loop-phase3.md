---
title: Orchestrator LLM Loop (Phase 3)
type: process
tags: [atlas-ui, orchestrator, llm-loop, evidence, phase3, implementation]
updated: 2026-05-18
related: [orchestrator-chat-only-product-plan, orchestrator-worker-handoff, atlas-pipeline-screen, atlas-pipeline-db-state, full-flow-pipeline, multi-user-worker-conflicts, orchestrator-loop-on-react-loop-plan]
---

> **Status: scaffold, scheduled for removal (2026-05-18).** The custom
> mini-loop in `src/orchestrator/loop.py` was reviewed and ruled NOT the
> stable surface. The locked decision is to migrate to
> `core/react_loop.py::run_react_agent_impl` (Phase 3.5 plan:
> [[orchestrator-loop-on-react-loop-plan]]). Treat everything in this page as
> *interim implementation* — DB schema (`orchestrator_runs`,
> `orchestrator_steps`), tools (`src/orchestrator/tools.py`), runner +
> Waker (`src/orchestrator/runner.py`), HTTP routes, and UI banner all stay
> after migration. Only `src/orchestrator/loop.py` itself goes away,
> replaced by `src/orchestrator/react_bridge.py` (~80 lines) that builds a
> `ReactLoopDeps` for production loop. Do not extend `loop.py` with new
> features — implement them in the migration plan instead.


# Orchestrator LLM Loop (Phase 3)

[[orchestrator-chat-only-product-plan]]의 **Capability Ladder L2 — Evidence-Gated
Orchestrator Loop** 단계를 구현한 결과 기록. 우측 Orchestrator chat이 키워드
매칭이 아니라 **진짜 LLM 제어 루프**로 동작한다.

## 초등학생 버전 설명

ATLAS가 IP를 만드는 과정을 **레스토랑 주방**에 비유하면:

- 손님(사용자) → 오른쪽 chat 창
- 주방장(LLM 오케스트레이터) → 손님 주문을 듣고 누가 뭘 할지 결정
- 요리사들(worker들) → ssot-gen / rtl-gen / sim / lint / sta …
- 주문 영수증철(DB) → 누가 언제 뭘 했는지 전부 기록

**예전 방식**: 손님이 "라면 줘"라고 하면 주방장이 **단어만 보고** 무조건 라면 도구
8개를 한꺼번에 끓이기 시작. 라면이 탔는지 안 탔는지 못 본다. 손님이 추가 요청을
해도 못 알아듣는다.

**Phase 3 새 방식**:
1. 손님: "ipA 만들고 끝까지 가줘"
2. 주방장(LLM)이 한 번에 **한 가지 도구**만 고름: "먼저 ssot-gen 시켜야겠다"
3. 일 시키고 → 결과 확인 → 영수증에 적기 → 다음에 뭐 할지 또 결정
4. 라면이 타면(stage 실패) → `classify_failure` 도구로 **누구 잘못인지** 분류 →
   해당 worker에게 다시 시킴
5. 모르겠으면 손님한테 직접 물어봄 (`ask_user`): "양념 매운 거 괜찮아요?"
6. 손님이 답할 때까지 **멈춰서 기다림** (UI에 빨간 배너로 표시)
7. 손님이 답하면 그 답을 받아서 이어서 일함

**핵심 차이점**:
- 한 번에 한 도구만 고른다 → 매 단계마다 진짜로 보고 판단함
- 모든 결정이 DB에 영구 기록된다 → 나중에 "왜 그렇게 했어?" 추궁 가능
- 실패는 종착점이 아님 → 자동으로 누가 고쳐야 하는지 분류해서 재시도
- 손님이 사이에 끼어들면 → 같은 주문에 추가 메모로 붙임 (새 주문 시작 X)
- LLM이 50번 결정해도 답이 안 나오면 → 30분 한도 또는 50스텝 한도에서 멈추고
  사람한테 넘김 (`final_state = cap_exceeded`)

이게 plan 문서의 한 줄 정의:

> "한 문장 goal을 input하면 ATLAS가 requirement import → worker dispatch →
> evidence gate → failure routing → human Q&A까지 한 loop 안에서 처리"

## What Shipped

| Layer | File(s) | Purpose |
|---|---|---|
| DB | `core/atlas_db.py` | `orchestrator_runs`, `orchestrator_steps` 2개 신규 테이블 + `workflow_runs`/`artifacts`에 `orchestrator_run_id` & `trigger_source` 컬럼 + 6 helper (`create_orchestrator_run`, `append_orchestrator_step`, `update_orchestrator_run`, `find_active_run_for`, `list_orchestrator_steps`, `latest_orchestrator_step`) |
| 분류기 | `src/orchestrator/classify.py` | system_prompt 산문에 있던 owner routing matrix를 pure `classify_failure(stage, evidence, error_text)` 함수로 추출 |
| 도구 8종 (callables) | `src/orchestrator/tools.py` | `read_pipeline_state`, `dispatch_workflow` (단일 `workflow` 또는 `stages=[...]` 리스트로 fan-out 둘 다 지원), `wait_job` (non-blocking), `read_artifact`, `classify_failure_tool`, `ask_user`, `write_handoff`, `mark_downstream_stale` — 모두 기존 helper wrapping, `(result_dict, evidence_summary ≤ 2KB)` 반환 |
| 추가 도구 1종 (loop-handled) | `src/orchestrator/loop.py` + `src/orchestrator/runner.py` | `yield_run(wake_on={job_ids, user_message, after_seconds})` — `tools.py` callable이 아니라 loop이 직접 처리해 runner의 `Waker.wait()`로 sleep. CPU interrupt 비유의 "interrupt" 경로 |
| LLM tool 스키마 9개 | `src/orchestrator/prompts.py::tool_schemas()` | 위 8 + yield_run 총 9개를 OpenAI function-calling 형식으로 노출. 한 LLM 응답이 여러 `tool_calls`를 담으면 loop이 ThreadPoolExecutor로 병렬 실행 |
| Prompt + Schema | `src/orchestrator/prompts.py` | OpenAI function-calling 8 schema + system prompt builder |
| Loop engine | `src/orchestrator/loop.py` | `OrchestratorContext` + `OrchestratorLoop.iterate()` + `.run(max_steps=50, max_seconds=1800)`, terminal states `completed/blocked/error/paused` |
| Background runner | `src/orchestrator/runner.py` | `ThreadPoolExecutor(max_workers=4)`, single-flight `(user_id, ip_id)` → 활성 run 1개, 동시 chat은 `user_reply` step으로 append |
| HTTP route | `src/atlas_api_jobs.py:3149` | 키워드 dispatch 완전 제거 → `runner.submit_or_attach` 위임, `{ok, run_id, status, ip}` 즉시 반환 |
| Read endpoints | `src/atlas_api_jobs.py` | `GET /api/orchestrator/runs/{run_id}` (run + 전체 steps), `GET /api/orchestrator/active_run?ip=X` (활성 run + 최신 step) |
| UI | `frontend/atlas/pipeline.jsx`, `frontend/atlas/styles.css` | `PendingQABanner` (SSOT QA polling) + `OrchestratorTraceStrip` (orchestrator dispatch trace) + StageCard `orch` 배지 (trigger_source=orchestrator_chat) + 신규 CSS `.pipe-stage-orch-pill`. Note: `ask_user` UI for orchestrator runs lives in `frontend/atlas/workspace.jsx` (`AskUserPrompt`), not in Pipeline screen. |

## Decision Locks (slop-회피)

Phase 3 진행 중 일부러 거부한 패턴:

- **No env-gated dual path**: 키워드 fallback (`ATLAS_ORCHESTRATOR_LLM=0`)
  도입하지 않음. LLM 호출 실패 → run을 `status="error"`, `final_state="llm_error"`로
  종료하고 UI에 빨간 배너 노출. 두 코드 경로 영구 유지 회피.
- **No placeholder import_document tool**: `import_document`는 Phase 2 산출물이라
  Phase 3 도구셋에서 제외. `NotImplementedError → ask_user escalate` 같은
  ad-hoc shim 없음.
- **`wait_job` non-blocking**: 장시간 worker를 in-tool으로 block하지 않음. 즉시
  현재 상태 반환 → 다음 iteration에서 LLM이 다시 판단 → 그 사이 user message
  처리 가능.
- **Single-flight `(user_id, ip_id)`**: 같은 (사용자, IP)에 새 chat이 오면 새
  run 시작이 아니라 기존 run에 `user_reply` step append. 병렬 run 의도 시에는
  다른 IP 필요.

## Observability Matrix

| 일어난 일 | DB | trace_events | UI |
|---|---|---|---|
| LLM 호출 자체 실패 | `orchestrator_runs.status=error`, `final_state=llm_error` | (앞으로 추가될 `orchestrator_run_error`) | (앞으로 추가될 빨간 chat 배너) |
| Tool 실행 중 예외 | step `verdict=tool_error`, `evidence_read_json.result.error` | — | — |
| 워커 URL 없음 | step에 handoff 결과 + `dispatched_workflow` | 기존 handoff 이벤트 | 기존 "handoff waiting" 배너 |
| `ask_user` 호출 | run `status=paused`, step `verdict=awaiting_user` | `orchestrator_ask_user` (correlation_id=run_id) | **"Human decision waiting" 배너** (이번 phase 신규) |
| Retry budget 초과 | `final_state=budget_exhausted` | — | StageCard failed + 배너 |
| 50-step / 30-min hard cap | `final_state=cap_exceeded` | — | (앞으로 추가) |
| 동시 chat append | 기존 run에 step `tool_name=user_reply` | — | chat reply: "Appended to active run" |

## Tests (54 pass, 5 skip) — Phase 3 baseline; Phase 3.5 updated counts below

| File | Coverage |
|---|---|
| `tests/test_atlas_db_orchestrator.py` (11) | CRUD round-trip, active-run uniqueness, ALTER 멱등성, JSON column 직렬화 |
| `tests/test_orchestrator_classify.py` (13) | 5 fixture (compile/lint/sim mismatch/coverage gap/STA setup/STA hold) routing 결정 + precedence (frontier > rtl_bug > tb_bug) |
| `tests/test_orchestrator_tools.py` (12) | bridge stubs로 read/dispatch, `wait_job` 스냅샷, `read_artifact` JSON parse, `ask_user`가 run paused로 만드는지, `write_handoff` durable JSON, `mark_downstream_stale` deps walk |
| `tests/test_orchestrator_loop.py` (11) | ~~삭제됨 (Phase 3.5)~~ — 동일한 terminal-state contract 검증은 `tests/test_orchestrator_react_loop_parity.py` (5 tests)가 인계. 원본 11개 테스트는 커스텀 `OrchestratorLoop` scaffold를 직접 테스트했으나 scaffold 제거로 더 이상 대상 없음. |
| `tests/test_orchestrator_runner.py` (4→6) | submit_or_attach started/appended/이전 run 완료 후 새 run, IP별 독립 실행 + Phase 3.5 Step 4에서 worker-complete → waker hook 2개 테스트 추가 |
| `tests/test_orchestrator_route.py` (6) | FastAPI TestClient — POST started/appended, missing message/ip 400, GET run detail, 404 |
| `tests/test_pipeline_orchestrator_worker_integration.py` (5 skipped) | `@_PHASE3_SKIP` — legacy keyword-dispatch contract 검증 테스트. 새 async contract로 재작성 필요 (별도 PR) |

## Out of Scope (다음 phase에서)

- **Phase 2 `import_document`**: PDF→requirement extraction. land 후 동일 wrapper
  패턴으로 `src/orchestrator/tools.py`에 합류.
- **`workflow_runs.trigger_source` write path**: 컬럼은 존재하지만
  `_make_job_record`가 채우는 코드는 follow-up. dispatch tool이 payload에
  실어 보내는 것까지만 구현됨.
- **Phase 4 per-stage retry budget**: 현재는 50-step / 30-min hard cap만 있음.
  per-stage 카운터 + budget exhaustion routing은 별도 작업.
- **Phase 5 SYN/STA/PnR/PSTA evidence gate**: `classify_failure`에 timing rule
  은 들어 있지만 stage gate 자체 강화는 별도.
- **Trace event push**: 현재는 2s polling으로 `PendingQABanner`가 SSOT QA 상태를,
  `OrchestratorTraceStrip`이 trace 이벤트를 확인. SSE/WebSocket push는 폴링 부담이 문제될 때 도입.
- **Legacy integration test 재작성**: 5개 `@_PHASE3_SKIP` 테스트가 가진 product
  검증 (worker payload provenance, dedupe, multi-user scoping)은 새 async
  contract용 변형으로 다시 작성 필요.

## Related

- [[orchestrator-chat-only-product-plan]] — 본 phase가 구현하는 product plan
- [[orchestrator-worker-handoff]] — `write_handoff` tool이 wrap하는 durable queue
- [[atlas-pipeline-screen]] — 우측 Orchestrator chat panel이 사는 화면
- [[atlas-pipeline-db-state]] — 새로 추가된 `orchestrator_runs`/`orchestrator_steps`
  테이블과 기존 `workflow_runs`/`artifacts` 컬럼 확장 위치
- [[multi-user-worker-conflicts]] — single-flight `(user_id, ip_id)` 규칙의 배경
- [[full-flow-pipeline]] — `dispatch_workflow` tool이 dispatch하는 stage DAG
