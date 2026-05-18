---
title: Orchestrator Loop on react_loop — Reuse Plan (Phase 3.5)
type: process
tags: [atlas-ui, orchestrator, react-loop, refactor, plan, reviewed, on-hold]
updated: 2026-05-18
related: [orchestrator-llm-loop-phase3, orchestrator-chat-only-product-plan, orchestrator-worker-handoff, multi-user-worker-conflicts]
---

# Orchestrator Loop on react_loop — Reuse Plan (Phase 3.5)

> **Architectural decision LOCKED (2026-05-18)**: the orchestrator loop will
> run on top of `core/react_loop.py::run_react_agent_impl` via dependency
> injection (Option B in the chat). The custom mini-loop in
> `src/orchestrator/loop.py` is treated as a **temporary scaffold** to be
> removed once the migration lands — not a permanent surface. Reason:
> stability. `react_loop.py` is the production-validated path that already
> covers compression / TodoTracker sync / per-IP context injection / parallel
> tool execution / streaming UI / ESC interrupt. Re-implementing those in a
> parallel loop is not a stable foundation.
>
> **Status (2026-05-18)**: SPIKE ON HOLD. Review pass found 1 P0 + 4 P1 + 2 P2.
>
> Prereqs before spike (Step 1) can run:
>
> - [x] **P-A — plan revision**: review findings reflected throughout (sketch
>       replaced, tool counts unified to "8 tools.py callable + 1 loop-handled
>       yield_run = 9 LLM schemas", `available_tools.update(...)` removed,
>       `main._build_react_loop_deps()` reference removed, yield_run kept as
>       separate tool, `orchestrator_inject_fn` ctx-bound variant required,
>       `llm_calls` linkage corrected). Done in this document.
> - [x] **P-B — integration-test rebaseline (2026-05-18)**: all 4 active
>       failures triaged. Final state of
>       `tests/test_pipeline_orchestrator_worker_integration.py`:
>       **9 passed, 6 skipped, 0 failed** (was 4 failed). All 4 confirmed
>       pre-existing on commit `496a44d1f` (verified via `git worktree`),
>       i.e. not Phase 3 regressions. Triage:
>       - **#1 `test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints`**
>         — real production bug + test bug + tight window. (a) Fixed
>         `_refresh_tracked_jobs` in `src/atlas_api_jobs.py` to also poll jobs
>         in status `pending` (only `running` before), gated on `run_id`
>         presence — without this, once the worker poll observes a "pending"
>         server-side state the local status sticks there forever. (b) Added
>         missing `reasoning_effort` kwarg to `fake_react_task` so the
>         executor doesn't silently TypeError. (c) Extended polling window
>         from 20×0.1s to 50×0.2s.
>       - **#2 `test_job_dispatch_keeps_llm_model_separate_from_lint_toolchain`**
>         — test expectation drift. `_WORKER_MODEL_DEFAULTS["lint"]` flipped
>         to `"deepseek"`; the adjacent passing test
>         `test_orchestrator_worker_status_exposes_default_model_bindings`
>         already asserts the new default. Updated test #2 to match.
>       - **#3 `test_full_ip_pipeline_can_complete_all_stages_across_two_workers`**
>         — pre-existing test infrastructure gap. Marked with explicit
>         `@pytest.mark.skip` and a reason that points to the underlying
>         cause: ssot stage's `_job_artifact_recovery` shells out to
>         `workflow/ssot-gen/scripts/check_ssot_disk.sh` which validates the
>         full SSOT YAML schema; the mock worker's `_write_mock_stage_artifact`
>         only emits `ip: <ip>\nrequirements: []` which the real validator
>         rejects, chain-blocking every downstream stage. Symlinking the
>         workflow dir into `tmp_path` (kept in the test) makes the validator
>         reachable but does not solve the schema validity. Fix needs either
>         a full schema-valid mock SSOT or a per-test validator override —
>         test-infrastructure work, out of P-B scope.
>       - **#4 `test_pipeline_dispatch_persists_db_identity_for_admin_sessions`**
>         — same lint default drift as #2. Updated expected
>         `model_profile == ["gpt-5.3-codex", "deepseek"]`.
>
> Phase 3.5 spike can now start. Targeted Phase 3 suite still green: 57
> passed across the 6 orchestrator test files (verified post-P-B).
>
> Phase 3 targeted suite is green: 57 passed across
> `test_atlas_db_orchestrator.py` (11), `test_orchestrator_classify.py` (13),
> `test_orchestrator_tools.py` (12), `test_orchestrator_loop.py` (11),
> `test_orchestrator_runner.py` (4), `test_orchestrator_route.py` (6).

[[orchestrator-llm-loop-phase3]]가 ship한 LLM control loop은 `call_llm_raw`를
직접 부르는 **별도 mini-loop**다. 그래서 main agent loop이 자동으로 해주는
compression / TodoTracker / per-IP context injection / LLM call accounting /
streaming UI / ESC interrupt 같은 기능을 **하나도 받지 못한다**.

본 문서는 그 격차를 메우기 위한 refactor 제안 — Orchestrator loop을
`core/react_loop.py::run_react_agent_impl` 위에서 돌게 하는 작업 — 의 review
용 plan이다. 실행은 별도 PR.

## 현재 상태 (격차)

| 기능 | 기존 ReAct loop (`core/react_loop.py`) | Phase 3 Orchestrator loop (`src/orchestrator/loop.py`) |
|---|---|---|
| Context compression | ✓ `core/compressor.compress_history` | ✗ `_messages` 무한 누적 |
| TodoTracker DB sync (`workflow_todos`) | ✓ | ✗ |
| Per-IP context injection (`orchestrator_inject`) | ✓ | ✗ |
| LLM call accounting (`llm_calls` 테이블) | △ — `AtlasTrace.record_llm_call(...)` explicit 호출 필요 (`core/atlas_trace.py:395`); `llm_client._record_call`은 in-memory perf log일 뿐 | ✗ — `call_llm_raw` 자체 카운터만 |
| Provider/model 동적 전환 | ✓ `scoped_runtime` | ✗ `config.MODEL_NAME` 고정 |
| Tool 스트리밍 UI | ✓ WS 토큰별 | ✗ 결과 일괄 |
| ESC interrupt, agent_mode flip | ✓ | ✗ |
| Reasoning effort per-call | ✓ | 부분 (run 단위) |

## 재사용 가능한 hook (확인됨)

`core/react_loop.py:91 ReactLoopDeps`는 dependency-injected dataclass.
관련 필드:

| Field | Purpose | Orchestrator 활용 |
|---|---|---|
| `cfg` | config namespace | production config 그대로 |
| `llm_call_fn` | streaming LLM call | production `llm_client.stream_chat` 그대로 |
| `compress_fn` | `compress_history` | **그대로 — compression 무료** |
| `execute_tool_fn` | tool dispatcher | **wrapper로 감싸 `orchestrator_steps` 기록** |
| `execute_parallel_fn` | parallel actions | 그대로 — 병렬 tool call 보존 |
| `orchestrator_inject_fn` | per-iteration context inject | `build_orchestrator_inject_fn(db, bridge)`는 env/contextvar 의존 → ctx-bound variant 필요 (review P2 항목). `build_orchestrator_inject_fn_for(db, ctx)` 신규 작성. |
| `poll_human_input_fn` | mid-run user input | **runner의 waker.wait()로 매핑 — yield_run 대체 가능** |
| `available_tools` | tool registry dict | **orchestrator 9개 LLM schema (8 tools.py callable + loop-handled yield_run)로 replace (not update)** — review P0 항목. `build_prompt_fn`/`llm_call_fn`도 함께 orchestrator-scoped로 교체해야 generic agent tool들이 LLM에 새지 않음. |

## 통합 설계 (sketch — review findings 반영)

새 파일: `src/orchestrator/react_bridge.py`. 핵심 원칙은 **explicit
construction** — production helper에 기대지 않고, react_loop이 요구하는
필드를 core 모듈에서 직접 묶어 만든다. tools/prompts/llm_call은 **replace**
(not update). injector는 ctx-bound 신규 builder.

```python
def build_orchestrator_deps(db, runner, ctx) -> ReactLoopDeps:
    # core 모듈에서 명시적으로 가져온다 — src.main import 금지 (review P1).
    from core import compressor, tool_dispatcher, parallel_executor
    from core.orchestrator_inject import build_orchestrator_inject_fn_for
    from src import llm_client

    # 8개 orchestrator tool만 노출 — generic agent tool은 안 보이도록 (P0).
    orchestrator_tools = _register_orchestrator_tools(ctx, runner)
    # step row 영구화 wrapper. 병렬 dispatch에서도 LLM-call order로
    # step_index를 보존하기 위해 내부에 central collector를 둔다 (P2).
    execute_tool = _wrap_with_step_persistence(
        inner=tool_dispatcher.dispatch_tool,
        db=db,
        run_id=ctx.run_id,
        allowed_tools=set(orchestrator_tools),
    )

    return ReactLoopDeps(
        cfg=config,
        llm_call_fn=_orchestrator_llm_call(orchestrator_tools),  # 8 schemas only
        compress_fn=compressor.compress_history,
        build_prompt_fn=_orchestrator_prompt_builder(ctx),       # not the generic one
        process_obs_fn=tool_dispatcher.process_observation,
        execute_tool_fn=execute_tool,
        execute_parallel_fn=parallel_executor.execute_actions_parallel,
        available_tools=orchestrator_tools,                       # REPLACE, not update
        orchestrator_inject_fn=build_orchestrator_inject_fn_for(db=db, ctx=ctx),
        poll_human_input_fn=None,   # yield_run is its own tool, not this path (P1)
        # ESC/emit_* fn은 background 실행이라 None (=no-op stub) 유지
        ...
    )
```

`OrchestratorLoop.run()`은 다음으로 축소:

```python
def run(self, max_steps=50, max_seconds=1800) -> RunOutcome:
    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": self.initial_user_message}]
    tracker = IterationTracker(max_iterations=max_steps)
    deps = build_orchestrator_deps(self.db, self.ctx.runner, self.ctx)
    try:
        run_react_agent_impl(
            messages, tracker, "orchestrator", deps,
            mode="oneshot", preface_enabled=False,   # background, no UI preface
        )
    except Exception as exc:
        self.db.update_orchestrator_run(self.ctx.run_id, status="error",
                                        final_state="llm_error", ended=True)
        return RunOutcome(...)
    # 종료 verdict는 마지막 orchestrator_step에서 읽어옴
    ...
```

yield_run은 react_loop이 아니라 wrapper 안에서 처리:

```python
def _wrap_with_step_persistence(*, inner, db, run_id, allowed_tools):
    collector = _OrderedStepCollector(db, run_id)
    def execute_tool(tool_name, args_str, *a, **kw):
        if tool_name == "yield_run":
            waker = runner.register_waker(run_id=run_id, ...)
            try:
                reason = waker.wait()
            finally:
                runner.unregister_waker(run_id)
            collector.append(tool_name="yield_run", verdict=reason, ...)
            return f"woken: {reason}"
        # 정상 tool — production dispatcher에 위임 + step row 기록
        out = inner(tool_name, args_str, *a, **kw)
        collector.append(tool_name=tool_name, args=args_str, result=out, ...)
        return out
    return execute_tool
```

## 유지 (그대로 ship된 산출물)

- `src/orchestrator/tools.py` — 8 tool callable. 변경 없음 (production
  `execute_tool_fn`이 호출). yield_run은 callable이 아니라 wrapper 안에서
  처리 (위 sketch 참조).
- `src/orchestrator/classify.py` — pure routing. 변경 없음.
- `src/orchestrator/runner.py` — single-flight + waker. **`poll_user_message`
  메서드만 추가** (single-flight append → waker wake와 동일 경로).
- `orchestrator_runs` / `orchestrator_steps` 스키마. 변경 없음.
- `GET /api/orchestrator/runs/{id}`, `GET /api/orchestrator/active_run`,
  `POST /api/pipeline/orchestrator/chat` — 변경 없음 (runner의 contract 유지).
- `tests/test_orchestrator_classify.py` / `test_atlas_db_orchestrator.py` /
  `test_orchestrator_tools.py` — 변경 없음.

**Test status as of 2026-05-18 (do not paper over this):**

- Phase 3 targeted suite (6 files, 57 tests): all green —
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/test_atlas_db_orchestrator.py
  tests/test_orchestrator_classify.py tests/test_orchestrator_tools.py
  tests/test_orchestrator_loop.py tests/test_orchestrator_runner.py
  tests/test_orchestrator_route.py` → 57 passed.
- Legacy integration suite (`tests/test_pipeline_orchestrator_worker_integration.py`):
  **4 failed, 6 passed, 5 skipped**. The 5 skips are intentional Phase 3
  contract-change markers (`@_PHASE3_SKIP`). The 4 failures are NOT —
  they are unresolved and must be triaged in Prereq P-B (see
  `## 단계적 진행`). Failure sites: line 431, 577, 652, 728.

## 다시 짜는 것

- `src/orchestrator/loop.py::OrchestratorLoop.iterate/run` — 250줄 → ~80줄로 축소.
  iterate() 사실상 제거 (react_loop이 iteration 관리), run()은 deps 빌드 + 호출.
- `src/orchestrator/react_bridge.py` — 신규 (~150줄).
  - `_wrap_with_step_persistence(inner_dispatch, db, run_id)`
  - `_register_orchestrator_tools(ctx, runner)` — 8 tool callable mapping (yield_run은 wrapper 내부 처리이므로 별도)
  - `build_orchestrator_deps(db, runner, ctx)` — main에서 production deps
    뽑아오기 + orchestrator 특화 override
- `tests/test_orchestrator_loop.py` — 스크립트된 LLM caller 대신
  `run_react_agent_impl`을 stub해서 동일한 step-persistence 행동을 검증하는
  형태로 재작성. 8개 케이스 그대로 살림.
- `tests/test_orchestrator_runner.py` — `poll_user_message` 케이스 추가, 기존
  4개 케이스는 변경 없음.

## yield_run 재배선

현재 yield_run은 내 custom loop이 `_handle_yield` 메서드에서 직접 처리.
react_loop 통합 후에는:

- LLM이 `yield_run(wake_on={...})` 호출
- `execute_tool_fn` wrapper가 이 tool을 감지 → ctx.runner에 waker 등록 →
  반환값으로 빈 문자열을 돌려 react_loop이 다음 iteration 진입을 잠시 멈춤
- 더 깔끔한 방법: `poll_human_input_fn`을 waker.wait()와 연결하면 react_loop이
  자체적으로 "사용자 input 기다림" semantics로 이미 지원 — 별도 hook 불필요할 수도

검증 필요: react_loop의 `poll_human_input_fn`이 정확히 어디서 호출되는지
(매 iteration 시작? streaming 중간? 종료 직전?)에 따라 yield의 위치가 결정됨.

## 위험 / 검증 항목

리뷰어가 확인해야 할 것:

1. **무인 background 실행 호환성**: `run_react_agent_impl`은 interactive
   session용. `emit_*_fn`, `esc_check_fn` 등을 모두 None/no-op으로 주고
   FastAPI background thread에서 굴려도 동작하는가? `Spinner`, `EscapeWatcher`
   같은 TTY 의존성이 무인 환경에서 안전하게 noop으로 떨어지는가?
2. **`mode="oneshot"`의 의미**: react_loop이 oneshot에서 어디까지 가는가?
   사용자 input prompt가 없으면 자동 종료하는가?
3. **production deps 추출 가능성**: `main._build_react_loop_deps()` 같은
   helper가 실제로 존재하는가? 없으면 main.py에서 deps 구성 코드를
   `react_bridge.py`로 옮길 때 회귀 위험.
4. **`orchestrator_inject_fn`의 session 의존성**: 기존 injector는
   `get_atlas_bridge_session_id()`에 의존. background orchestrator thread에
   contextvar가 적절히 설정돼 있는가? 안 그러면 IP context 못 받음.
5. **`poll_human_input_fn` 호출 빈도**: 매 iteration마다 부르면
   waker.wait()이 매번 즉시 반환해야(부하 없도록) 함. timeout=0 polling이
   가능한 API인가?
6. **`execute_tool_fn` wrapping이 parallel tool call을 깨지 않는가**:
   `execute_parallel_fn`이 wrapped dispatch를 호출할 때 동일 인터페이스
   유지되는지.
7. **orchestrator_steps의 step_index 순서 보장**: ~~step_index는 DB
   auto-increment라 문제 없을 듯~~ → **틀림**. 병렬 thread가 직접 append하면
   completion order가 됨 (review P2 항목). wrapper 안에 single-thread
   collector 또는 pre-assigned index 필요.
8. ~~**LLM call accounting double-count 위험**: react_loop은 자체적으로
   `llm_calls` row를 만듦~~ → **잘못된 전제**였음. 실제 react_loop은
   `llm_client._record_call` (in-memory)만 호출하고 DB 기록은 따로
   `AtlasTrace.record_llm_call()` 명시 호출이 필요. 또한 `llm_calls` 스키마에
   `correlation_id` 컬럼 자체가 없음 (review P1 항목). 새 linkage 설계는
   `## Review Findings` 참조.

## 단계적 진행 (slop 회피)

리뷰가 P0/P1 issue를 잡았기 때문에 spike 시작 전 **prereq 두 개**가 먼저:

| Prereq | 작업 | Gate |
|---|---|---|
| P-A | 본 plan을 review findings 반영해 재작성 (P0 tool replace, P1 deps factory, P1 yield_run separate, P1 llm_calls 설계, P2 step ordering, P2 ctx-bound injector). 이 문서가 spike 시작 가능 상태가 됨 | **완료 (2026-05-18)** — 본 페이지 자체 |
| P-B | `tests/test_pipeline_orchestrator_worker_integration.py`의 4개 active failure 트리아지 — intentional contract change면 테스트 갱신, 진짜 regression이면 fix. 6개 `@_PHASE3_SKIP`은 별개 작업 | **미완료** — 2026-05-18 기준 4 failed / 6 passed / 6 skipped 그대로 |

prereq 끝나고서:

| Step | 작업 | 검증 |
|---|---|---|
| 1 | `_runspaces/orchestrator_react_spike.py`에서 react_bridge의 explicit deps factory로 toy orchestrator 1 iteration 실행 — 시그니처/호환성 + tool registry **replace** 동작 확인 | 결과를 본 plan의 `## Spike Results` 섹션으로 inline 추가 |
| 2 | `src/orchestrator/react_bridge.py` 신규 — explicit deps factory (no `src.main` import) + tool replace (not update) + ctx-bound `orchestrator_inject` + parallel step-order collector. 단위 테스트 | `tests/test_orchestrator_react_bridge.py` 신규 |
| 3 | `OrchestratorLoop.run()` 내부를 `run_react_agent_impl` 호출로 교체. 기존 `tests/test_orchestrator_loop.py` 케이스가 새 backend로도 통과하는지 확인 (LLM stub은 ReactLoopDeps.llm_call_fn으로 주입) | 회귀 없으면 commit |
| 4 | `yield_run` 별도 tool 유지 — `execute_tool_fn` wrapper가 `ctx.runner.register_waker(...)` 호출 후 `waker.wait()` block, wake reason을 tool result로 반환 | runner 테스트 케이스 추가 |
| 5 | End-to-end 테스트: 토큰 한도 시 `compress_fn` 발화 / todo_write가 `workflow_todos`에 가는지 / ctx-bound injector가 IP context를 매 iteration 주입하는지 / `AtlasTrace.record_llm_call(run_id=...)`이 호출되는지 | 새 `tests/test_orchestrator_react_integration.py` |
| 6 | `[[orchestrator-llm-loop-phase3]]` 갱신 — "Phase 3.5 react_loop 통합 land됨" 섹션, custom loop 제거 기록 | wiki 갱신 |

## 안 하는 것 (의도적)

- **`run_react_agent_impl`을 fork**: 의존성 그래프가 너무 복잡. wrapper로
  충분.
- **`run_agent_session` 사용**: 한 task 끝까지 실행하는 sub-agent helper로
  설계됨 — control loop 의도와 불일치.
- **Compression 직접 구현**: 똑같이 하면 ad-hoc shim. 무조건 production
  `compress_fn` 재사용.

## Review Findings (2026-05-18)

Independent review against the original sketch surfaced concrete bugs in the
proposed integration. Each finding is reproducible against the cited
file:line. The plan above must be revised to address them before the spike
runs.

### P0 — `available_tools.update(...)` leaks generic agent tools

**Issue.** The sketch in `## 통합 설계` does `base.available_tools.update(...)`
to add the 8 orchestrator tools on top of production deps. But the production
wrapper at `src/main.py:1195` first captures `tools.AVAILABLE_TOOLS.keys()`
when constructing the LLM-facing tool schema, so the LLM ends up seeing every
generic agent tool — Read, Write, Edit, web_search, dispatch_workflow,
spawn_subagent, todo_write, ... — alongside the orchestrator's 8. The
orchestrator's prompt at `src/orchestrator/prompts.py:8` and tool schema at
`src/orchestrator/prompts.py:201`은 9개 schema (8 tools.py callable + 1
loop-handled yield_run)를 노출하도록 작성됨 — production deps의 generic agent
tool과 섞이면 의도와 다른 surface가 LLM에 노출됨.

**Fix.** `react_bridge.build_orchestrator_deps(...)` must **replace** —
not merge — three fields on the constructed `ReactLoopDeps`:

- `available_tools = {orchestrator 8 tools.py callables only}` (yield_run은
  callable이 아니라 wrapper 안에서 처리 — `available_tools` 등록 대상이
  아님)
- `build_prompt_fn` → orchestrator-scoped builder that does NOT inject the
  generic agent prompt fragments
- `llm_call_fn` → orchestrator-scoped call that publishes only the 8 schemas

A `.update(...)` anywhere in this builder is a bug.

### P1 — `main._build_react_loop_deps()` does not exist

**Issue.** `## 통합 설계` line 56 references a helper called
`main._build_react_loop_deps()`. There is no such helper. The deps are
constructed inline at two places that have drifted apart: `src/main.py:1190`
and `core/agent_server.py:1045`.

**Fix.** Do not import from `src.main`. `src/orchestrator/react_bridge.py`
must build the `ReactLoopDeps` directly from `core.compressor`,
`core.tool_dispatcher`, `core.parallel_executor`, `core.orchestrator_inject`,
`llm_client`, etc. — explicit construction, no `main` dependency. (Separately:
the duplication between `main` and `agent_server` is its own follow-up; this
plan does not have to fix that, but should not paper over it either.)

### P1 — `yield_run` ≠ `poll_human_input_fn`

**Issue.** `## yield_run 재배선` floated absorbing `yield_run` into
`poll_human_input_fn`. They are not the same thing.
`poll_human_input_fn` fires only when `ENABLE_HUMAN_IN_THE_LOOP` is true
(`core/react_loop.py:2031`) and is invoked at the END of an iteration to ask
"did a human type something while I was streaming?". `yield_run` (currently
at `src/orchestrator/loop.py:357`) sleeps the loop on a Waker that triggers
on any of: watched job complete, user message arrives, timer expires.
Different signal set, different invocation point.

**Decision.** Keep `yield_run` as a separate orchestrator tool. The
`execute_tool_fn` wrapper recognises `yield_run`, calls
`ctx.runner.register_waker(...)`, blocks on `waker.wait()`, then returns the
wake reason as the tool result. `poll_human_input_fn` stays mapped to "mid-
stream user message injection only" — orthogonal to yield.

### P1 — Plan under-reported test status

**Issue.** The "유지 (그대로 ship된 산출물)" bullet says "51 of 57 tests"
without flagging that `tests/test_pipeline_orchestrator_worker_integration.py`
has **4 active failures** (lines 431, 577, 652, 728) on top of the 5
intentionally-skipped tests. The failures touch real worker completion, lint
model/toolchain expectation, full pipeline completion, and DB identity model
profile. Some may be legitimate fallout from Phase 3's contract change;
others may be regressions.

**Prereq for any 3.5 work.** Triage the 4 failures into "intentional contract
change → update test" vs "real regression → fix". This must happen BEFORE
the spike so the spike isn't running against a broken baseline.

### P1 — `llm_calls` accounting is not free

**Issue.** The "자동으로 얻는 것" bullet on LLM call accounting is wrong.
`llm_client._record_call` at `src/llm_client.py:483` is an in-memory perf
log, not a DB write. DB persistence to `llm_calls` requires an explicit call
to `AtlasTrace.record_llm_call()` at `core/atlas_trace.py:395`. Additionally,
the `llm_calls` schema at `core/atlas_db.py:398` has no `correlation_id`
column — the "correlation_id로 묶음" idea floated as an open question is not
implementable without a schema change.

**Decision (provisional).** Linkage strategy: pass `run_id=<orchestrator_run_id>`
+ `message_id` on every `AtlasTrace.record_llm_call(...)` issued from inside
an orchestrator iteration. The new step row stores its own `id` (PK), and
we add a separate `orchestrator_step_id` field on a new `llm_call_orchestrator`
mapping if richer linkage is needed later. No `correlation_id` invention.

### P2 — Parallel step ordering

**Issue.** The current custom loop preserves LLM-call order when appending
steps after parallel execution (`src/orchestrator/loop.py:291`). After
migration, if the wrapped `execute_tool_fn` is called inside each parallel
worker thread and each thread calls `append_orchestrator_step` directly, the
DB-assigned `step_index` (`core/atlas_db.py:3505`) records **completion
order**, not call order — making the trace harder to read for fan-outs where
slow stages finish later.

**Fix.** The wrapper must funnel step appends through a single thread-safe
collector (or pre-allocate `step_index` values in LLM-call order before
dispatching the parallel batch). This is a wrapper-internal concern;
`append_orchestrator_step` itself does not need to change.

### P2 — `orchestrator_inject_fn` is env/contextvar bound

**Issue.** The current injector at `core/orchestrator_inject.py:45` reads the
active IP from `os.environ.get("ATLAS_ACTIVE_IP")` and the active session
from a contextvar at `core/orchestrator_inject.py:165`. The background
orchestrator thread already has `ctx.user_id`, `ctx.ip_id`, `ctx.session_id`
explicitly — relying on env/contextvar in this path is fragile (background
threads do not inherit FastAPI's contextvar set, and the env mirror races
between concurrent users).

**Fix.** Add an ctx-bound variant: `build_orchestrator_inject_fn_for(db,
ctx)` that closes over the explicit triple rather than reading env. Use it
from `react_bridge.build_orchestrator_deps`; leave the legacy env-bound
factory alone for non-orchestrator callers.

## Progress (Steps 1–5 + budgets + evidence gate, 2026-05-18)

| Step | Status | Notes |
|---|---|---|
| 1 Spike | ✓ **landed** | `_runspaces/orchestrator_react_spike.py` (14/14 checks). See `## Spike Results` below. |
| 2A Bridge unit tests | ✓ **landed** | `tests/test_orchestrator_react_bridge.py` — 15 tests formalising the spike checks. Verified P0/P1/P2 review findings are discharged structurally. |
| 2B react_loop call-shape compat | ✓ **landed** | +2 tests in the same file. `deps.execute_tool_fn(name, args_str, pre_parsed_kwargs=...)` accepts react_loop's exact call shape; unknown tools route through `tool_dispatcher.dispatch_tool` returning "Tool not found" (no leak). |
| 2C trigger_source write path | ✓ **landed** | `core/atlas_db.py::start_workflow_run` now accepts `trigger_source` + `orchestrator_run_id` kwargs and persists them onto `workflow_runs` and `artifacts`. `_make_job_record` / `_record_job_db_start` / `_dispatch_workflow_tool_bridge` forward these from the dispatch payload. New `tests/test_trigger_source_write.py` (4 tests) covers DB column persistence, payload extraction in the bridge, and pipeline-button default. **Frontend `orch` pill in `pipeline.jsx` now lights up against real production data — previously the column was always NULL.** |
| 3a OrchestratorReactLoop class | ✓ **landed** | `src/orchestrator/react_bridge.py::OrchestratorReactLoop` wraps `run_react_agent_impl`. Includes `_translate_caller_to_stream(caller, error_sink)` that converts the legacy `llm_caller(messages, schemas) -> dict` contract into react_loop's streaming protocol (`("native_tool_calls", [{id,name,arguments}])` + `("finish_reason", …)`). `error_sink` promotes silent LLM exceptions inside the streaming generator to `status="error"` + `final_state="llm_error"`. New `tests/test_orchestrator_react_loop.py` (2 tests) covers single-tool-call natural completion and the LLM-exception path. |
| 3b runner factory switch | ✓ **landed** | `src/orchestrator/runner.py::_build_loop` now constructs `OrchestratorReactLoop` for production. The legacy `OrchestratorLoop` mini-loop stays in `src/orchestrator/loop.py` only as a temporary scaffold for the 11 legacy `tests/test_orchestrator_loop.py` cases. |
| 4 Worker-complete → waker hook | ✓ **landed** | `src/atlas_api_jobs.py::_advance_pipeline_from` now calls `src.orchestrator.runner.notify_job_complete(job_id, status)` at the top, guarded by lazy import + try/except (silent no-op when no runner is initialised). Two tests in `tests/test_orchestrator_runner.py` confirm: (a) a registered Waker fires with reason `"job_complete:<job_id>:completed"` and (b) absence of a runner is a clean no-op. yield_run interrupt is now wired end-to-end: a yielded orchestrator_run wakes the moment a watched worker finishes. |
| 4b Per-stage retry budgets | ✓ **landed** | New `src/orchestrator/budgets.py::BudgetTracker` thread-safe per-stage counter scoped to one orchestrator_run. Defaults mirror `workflow/orchestrator/system_prompt.md:65-73` (`ssot-gen=3`, `rtl-gen=5`, `tb-gen=3`, `sim=2`, `sim_debug=1`, `coverage=2`, `goal-audit=1`); SYN/STA/PnR/PSTA get conservative defaults (`3/2/2/2`), all other stages fall back to `4`. `react_bridge._bind_orchestrator_tools` wraps `dispatch_workflow` to consult the tracker — exhausted attempts return `{ok:false, error:"retry budget exhausted: …"}` and write a `verdict="tool_failed"` step row so the LLM can pivot to `ask_user` or escalate. `stages=[…]` fan-out counts each target separately; `workflow="__final__"` is the loop terminator and never consumes budget. New `tests/test_orchestrator_budgets.py` (11 tests). |
| 5 SYN evidence gate | ✓ **landed** | New `src/atlas_api_jobs.py::_synthesis_artifact_failure()` validates the mapped netlist exists, error-count is sane, and status reports a recognised pass alias before letting a SYN job declare success. `_job_artifact_failure` routes SYN through this gate. New `tests/test_evidence_gates.py` (11 tests) exercises missing netlist, error count, non-pass status, pass aliases, unparseable status, no-dir, and integration. STA/PnR/PSTA gates remain on the conservative existing path; further tightening is its own follow-up. |
| 5b e2e (compression / todo / accounting) | ✓ **landed** | Compression: `_compress_fn(messages, todo_tracker=None, **kw)` closure pre-binds `cfg` + `llm_call_fn`. TodoTracker sync inherited from `run_react_agent_impl`. **llm_calls accounting + streaming gap both fixed in one focused change**: TDD test `tests/test_orchestrator_llm_call_accounting.py` first surfaced that bridge's `_llm_call` was returning a string from `call_llm_raw` (would have broken the moment a real LLM streamed in production — all 139 prior tests passed only because they used the `llm_caller=` test seam which bypasses `_llm_call` via `_translate_caller_to_stream`). Fix replaces `_llm_call` body to delegate to `llm_client.chat_completion_stream(...)` (generator) with `tools=tool_schemas()` when `ENABLE_NATIVE_TOOL_CALLS` is set, then on stream-exhaustion writes one `llm_calls` row via `db.record_llm_call(run_id=ctx.run_id, ip_id=…, session_id=…, tokens_input/output/cache_*)` reading the `llm_client` module globals (same convention `src/main.py:1228` uses). Accounting failures are swallowed so they cannot break the LLM call itself. |
| 6 Scaffold cleanup — parity tests | ✓ **landed** | New `tests/test_orchestrator_react_loop_parity.py` (5 tests) drives `OrchestratorReactLoop` end-to-end with scripted `llm_caller`s and asserts the 5 legacy contracts that survived the migration: (1) `dispatch_workflow(workflow="__final__", payload.state="completed")` ends with `status="completed"`, (2) `payload.state="blocked"` preserves `final_state="blocked"` (no collapse to "completed"), (3) `ask_user` puts the run in `status="paused"` with `ended_at` left NULL, (4) tool exception → step `verdict="tool_error"` + loop continues to a clean final, (5) native parallel tool_calls in one LLM response → every tool persists a step row + each dispatch hits the bridge. **Three real production bugs surfaced and fixed in the process**: (a) bridge `_dispatch_workflow` didn't recognise `__final__` (called the real `_dispatch_workflow_bridge` which doesn't know that pseudo-workflow); (b) `_wrap._call` dropped native_tool_call kwargs into a `**_` catch-all instead of routing them to `pre_parsed_kwargs` — every tool dispatch received `kw={}`; (c) `execute_parallel_fn` was bound to the bare `parallel_executor.execute_actions_parallel` whose signature is `(actions, *, tracker, cfg, execute_tool_fn, …)` but react_loop calls it as `(actions, tracker, agent_mode=…)` — TypeError on first parallel call. Bridge now wraps with `cfg` + `execute_tool_fn` pre-bound (`src/main.py:1072` pattern). |
| 6 Scaffold cleanup — deletion | ✓ **landed** | `src/orchestrator/loop.py` reduced from ~470 lines to a 50-line data-types module containing only `OrchestratorContext`, `RunOutcome`, and the `FINAL_WORKFLOW="__final__"` sentinel. Deleted: `OrchestratorLoop` class, `StepResult`, `LLMCaller` type alias, `_default_llm_caller`. Deleted: `tests/test_orchestrator_loop.py` (11 cases that exercised the scaffold class directly). Dropped the unused `OrchestratorLoop` import in `tests/test_orchestrator_runner.py` (the `_ControlledLoop` test double inherits `RunOutcome` only). Refactored `_build_loop` docstring in `src/orchestrator/runner.py` to remove the "legacy scaffold still around" note. Test count reflects the deletion: 146 → 135 (exactly -11). |
| 7 Frontend `orch` pill verification | 🔄 **rolled back via UI swap** | The orch pill renderer + `OrchestratorAskUserBanner` were removed when the user swapped `frontend/atlas/pipeline.jsx` to the May-17 visual layout from `ATLAS_UI_ENHANCEMENT/` (see 2026-05-18 log entry). The DB column write path (`trigger_source` + `orchestrator_run_id` in `core/atlas_db.py` and `src/atlas_api_jobs.py`) **stays** — only the JSX renderers were rolled back. Re-adding the pill + banner onto the swapped-in layout is a small front-end-only follow-up. Snapshot of the rendered version is preserved at `frontend/atlas/pipeline.jsx.pre-enhancement-swap-20260518.bak`. |

**Test totals after Steps 1–6 + budgets + SYN gate + streaming/accounting +
parity + scaffold deletion (2026-05-18 end-of-session):** 14 test files (the
legacy `tests/test_orchestrator_loop.py` is gone) —
`test_orchestrator_classify.py`, `test_atlas_db_orchestrator.py`,
`test_orchestrator_tools.py`, `test_orchestrator_runner.py`,
`test_orchestrator_route.py`, `test_orchestrator_react_bridge.py`,
`test_orchestrator_react_loop.py`, `test_orchestrator_react_loop_parity.py`,
`test_orchestrator_budgets.py`, `test_pipeline_orchestrator_worker_integration.py`,
`test_trigger_source_write.py`, `test_evidence_gates.py`,
`test_atlas_db.py`, `test_orchestrator_llm_call_accounting.py` →
**135 passed, 6 skipped, 0 failed in 11.56s**. 6 skips: 6 `@_PHASE3_SKIP`
legacy keyword cases + 1 SSOT-validator fixture gap
(`test_full_ip_pipeline_can_complete_all_stages_across_two_workers`).
The -11 drop versus the previous turn is exactly the deleted legacy
`OrchestratorLoop` scaffold tests; parity is now covered by
`test_orchestrator_react_loop_parity.py` (5 tests) which proves the same
five terminal-state contracts on the production `OrchestratorReactLoop`.

## Spike Results (Step 1, 2026-05-18)

`_runspaces/orchestrator_react_spike.py` ran end-to-end against
`src/orchestrator/react_bridge.py` and **all 14 checks passed** (run via
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 _runspaces/orchestrator_react_spike.py`).

The spike does NOT yet drive `run_react_agent_impl` with a stub LLM — that's
Step 2 (full unit test). It DOES prove the deps factory builds cleanly and
the orchestrator-scoped fields are wired correctly:

| Check | Outcome |
|---|---|
| No `src.main` import (P1) | ✓ |
| `available_tools` is exactly the 8 orchestrator callables — generic agent tools (Read, Write, web_search, …) absent (P0) | ✓ |
| `read_pipeline_state` callable returns a string observation suitable for the LLM observation field | ✓ |
| Each orchestrator callable invocation persists exactly +1 `orchestrator_steps` row via the `_OrderedStepCollector` (P2) | ✓ |
| `yield_run` is intercepted by `deps.execute_tool_fn` before reaching `tool_dispatcher.dispatch_tool` (i.e. it is NOT a `available_tools` callable; it's wrapper-handled) | ✓ |
| `yield_run` with `wake_on.after_seconds=0.05` returns `"woken: timer"` and writes its own step row | ✓ |
| `build_prompt_fn` builds a system prompt that embeds **all 9 tool schemas** (8 + yield_run), proving the LLM surface is orchestrator-scoped | ✓ |
| `compress_fn is core.compressor.compress_history` (production function reused as-is — compression is free) | ✓ |
| `orchestrator_inject_fn` is wired with the ctx-bound variant `build_orchestrator_inject_fn_for(db, ctx)` — no env / contextvar reliance (P2) | ✓ |

Phase 3 targeted suite remains green: **57 passed** in 3.46s after the spike.

What the spike intentionally skipped (and Step 2 must cover):

- A stub `llm_call_fn` that emits one `tool_calls` payload through the real
  `run_react_agent_impl` and asserts the observation/step round-trip end to
  end. Mocking the streaming tool-call protocol is non-trivial and belongs
  in unit tests against `react_bridge`, not a single-pass spike.
- Cross-thread step ordering under parallel `execute_actions_parallel` —
  the `_OrderedStepCollector` is present but parallel call ordering isn't
  asserted yet.
- `llm_calls` accounting linkage (passing `run_id`/`message_id` to
  `AtlasTrace.record_llm_call`) — `_llm_call` inside the bridge calls
  `llm_client.call_llm_raw` directly today; production wiring needs the
  AtlasTrace hook added.
- `orchestrator_inject_fn` execution against a real IP block (with
  `summarize_ip_room_context` returning content). Smoke-tested via
  callable check only.

Decisions confirmed in code:

- `yield_run` as a separate tool ✓ (P1 — verified via spike check 5).
- `available_tools` REPLACED, not merged ✓ (P0 — verified via spike check 2).
- No `src.main` dependency ✓ (P1 — verified via spike check 1).
- ctx-bound `orchestrator_inject_fn` ✓ (P2 — verified via spike check 9).

## Decisions Recorded (Phase 3.5 prerequisites)

Updates to the five Open Questions originally listed for the reviewer:

1. **`mode="oneshot"` vs `"interactive"`** → oneshot for the background
   orchestrator, with `preface_enabled=False`, explicit `__final__` to
   terminate, and the existing 50-step / 30-min cap retained as a safety net.
2. **`main._build_react_loop_deps()` helper** → does NOT exist. Build deps
   directly in `react_bridge.py` from core modules.
3. **`yield_run` as separate tool vs `poll_human_input_fn` absorption** →
   keep as separate tool (different signal semantics; see P1 finding).
4. **Rewrite 5 skipped + 4 failing integration tests before or after 3.5?** →
   before. Active 4 failures get rebaselined first; 5 skipped get rewritten
   to the new async contract; only then does the spike start.
5. **`llm_calls`/`orchestrator_steps` linkage** → not a "duplicate row"
   problem. Pass `run_id`/`message_id` to `AtlasTrace.record_llm_call(...)`
   from inside orchestrator iterations. No `correlation_id` invention. If
   richer linkage is needed, design a separate mapping table.

## Open Questions for Reviewer (all closed above)

The five questions originally listed here were decided in `## Decisions
Recorded` above. Section kept as a redirect so prior cross-references stay
valid. New questions arising from review go in `## Review Findings`.

## Related

- [[orchestrator-llm-loop-phase3]] — 본 refactor가 대체하는 custom loop의 현 상태
- [[orchestrator-chat-only-product-plan]] — 원본 product plan
- [[orchestrator-worker-handoff]] — yield_run이 보존해야 할 worker 완료 hook 경로
- [[multi-user-worker-conflicts]] — single-flight `(user_id, ip_id)` 규칙 (변경 없음)
