---
title: Cursor Pack — ROCEV Workflow Slim & Deliberations (2026-06-11)
category: tooling
type: design-rationale
tags: [cursor, workflow, rocev, slimming, stage-engine, fl-model, oracle, todo-loop]
updated: 2026-06-11
related: [cursor-agent-pack, req-obligation-contract-evidence-validation, workflow-ownership-and-boundaries, verification-contract-model, contract-reflection-workflow, workflow-improvement-candidates]
---

# Cursor Pack — ROCEV Workflow Slim & Deliberations

이 페이지는 `.cursor` 팩을 **ROCEV `req → rtl → tb → sim` 워크플로 골격만** 남기도록
슬림화하면서 내린 결정과 그 *근거*를 workflow 관점에서 기록한다. 팩의 as-built
구성(rules/hooks/agents/skills 목록)은 [[cursor-agent-pack]]에 있고, 이 문서는
그 위에서 **"무엇을 왜 남기고 왜 잘랐나"**를 다룬다. ROCEV 척추의 정의는
[[req-obligation-contract-evidence-validation]], 산출물 소유 경계는
[[workflow-ownership-and-boundaries]] 참조.

> 결과 요약: workflow 41→12 stage, agents 27→6, skills 21→3, rules 11→6,
> 5.7M→3.4M, 317파일 삭제, MCP 제거. 스모크 5/5 통과. `.cursor` 단독 추출 시에도
> 자족 실행.

## 1. 조직 원리 — workflow path가 곧 경계

슬림화의 기준선은 "데모가 *실제로 통과하는* 워크플로 경로"다. 기능별/표면별이
아니라 **`req → rtl → tb → sim`이 traverse하는 stage 폐포(closure)**를 KEEP,
그 밖(EDA·orchestration·signoff·mutation 등)을 DROP으로 둔다.

이게 가능하려면 두 가지를 먼저 답해야 했다:

1. 엔진이 stage를 **어떻게 호출**하나? (하드-import면 못 자른다)
2. `req→rtl→tb→sim`이 **실제로 어떤 stage들을 트리거**하나? (문서화된 명령보다 넓다)

## 2. 워크플로 라우팅 모델 — 왜 안전하게 자를 수 있나

핵심 발견: **`WorkflowStageEngine`은 stage를 하드-import하지 않고
`STAGE_MANIFEST.json` 기반으로 per-stage 스크립트를 `subprocess`로 호출한다.**

- 엔진은 `self.workflow_root / "<stage>" / "scripts" / "x.py"` 경로를 만들어
  `subprocess.run` (`src/workflow_stage_engine.py` 의 stage 메서드들, 예: fl/rtl/tb/sim).
- 유일한 동적 import는 `stage_contract_todos.py`를 **파일 경로로** 로드
  (`importlib.util.spec_from_file_location`, engine ~L2122) — 패키지 import 아님.
- `STAGE_ALIASES` / `STAGE_WORKFLOW`는 단순 dict라, 해당 stage를 **실행할 때만**
  디렉토리가 필요하다.
- `_resolve_workflow_root` (engine L28–37)는 `ssot-gen` 디렉토리를 workflow_root
  **탐지 마커**로 쓰지만, 없으면 기본 경로(`.cursor/workflow`)로 **graceful fallback**.

**결론(워크플로 관점):** off-path stage 디렉토리는 load-time에 아무것도 깨뜨리지
않는다. "호출되지 않는 stage = inert." 따라서 안전 드롭 = `req→rtl→tb→sim`이
트리거하지 않는 stage 전부.

## 3. DV 프로파일이 실제로 트리거하는 stage

문서화된 명령은 `--from-stage ssot-rtl --until lint`, `--from-stage ssot-tb-cocotb`
이지만, `STAGE_MANIFEST.json`의 `dv` 프로파일 순서는 더 넓다:

```
ssot-fl-model → ssot-cycle-model → ssot-equiv-goals → ssot-rtl → lint
            → ssot-tb-cocotb → sim → coverage → sim-debug → goal-audit
```

`ssot-tb-cocotb`(TB)는 **선행 산출물에 의존**한다 — `verify/equivalence_goals.json`
(equiv-goals), FL/CL 모델(fl/cycle-model). 즉 TB·sim을 닫으려면 모델 stage가
먼저 돌아야 한다. 그래서 `fl-model-gen`(fl/cl/equiv)·`coverage`·`sim_debug`·`reqcov`가
모두 KEEP 경계 안으로 들어온다.

## 4. fl-model-gen 딜레마 — 워크플로 설계 분기

가장 깊은 고민. "contract만 잘 있으면 FL model을 빼도 되나?"

코드가 답한다 — **contract(equivalence_goals)는 self-contained가 아니다. expected
값을 담지 않고 `FunctionalModel`을 *참조*만 한다:**

- `workflow/fl-model-gen/scripts/emit_equivalence_goals.py`
  - `"model_api": "FunctionalModel.apply"` (expected 값의 출처)
  - `"FunctionalModel is the golden oracle; sim-debug cannot change it to match RTL"`
- `workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py`
  - 생성된 cocotb TB가 `from functional_model import FunctionalModel`
  - "Scoreboard calls FunctionalModel.apply ... RTL observed outputs equal FL expected"

따라서 이 팩의 검증 철학은 **FL-vs-RTL 등가성**이다:

```
contract        = 무엇을 / 어떤 observable로 비교하나 + 변경통제(FL=golden)
expected 실제값  = sim 시점에 functional_model.py 를 실행해서 계산
```

**핵심 오해 해소:** `fl-model-gen`은 손으로 쓰는 모델이 아니라 **사용자가 작성한
SSOT/contract에서 `functional_model.py`를 자동 파생**한다. 즉 "contract 기반 저작"과
`fl-model-gen` 유지는 충돌이 아니라 한 몸이다.

| | FL model (채택) | contract-only (대안) |
|---|---|---|
| expected 출처 | 실행가능 모델이 계산 | scenario에 골든벡터 수기 |
| random/coverage 자극 | ✅ 자동 | ❌ 케이스마다 수기 |
| TB 생성기 | 그대로 동작 | `from functional_model import` 하드코딩 → **개조 필요** |

**결정: `fl-model-gen` KEEP.** 빼면 contract가 단순해지는 게 아니라 oracle이
사라지고, 골든벡터 수기 + TB 생성기 개조가 필요하다(별도 작업). 진짜 model-free
워크플로를 원하면 그것은 독립 트랙으로 잡는다.

## 5. Keep / Drop 매니페스트 (워크플로 근거)

| stage 그룹 | 처리 | 근거 |
|---|---|---|
| `req-gen` | KEEP | req 스테이지 게이트(locked truth) |
| `fl-model-gen` | KEEP | TB 등가성의 oracle(§4) |
| `rtl-gen` `lint` | KEEP | rtl 스테이지 + compile/lint 게이트 |
| `tb-gen` | KEEP | scoreboard, FL-vs-RTL 비교 |
| `sim` `coverage` `sim_debug` `reqcov` | KEEP | DV 프로파일 sim 닫기 경로(§3) |
| EDA: `syn` `sta` `sta-post` `pnr` `dft` `eda` | DROP | 별도 `eda` 프로파일, DV에 없음 |
| `orchestrator` `worker` `chat-responder` `cmux` `default` | DROP | 런타임/오케스트레이션 표면, ROCEV 경로 밖 |
| `signoff` `mutation` `contract-reflection` `spec-review` `ssot-gen` `architect` `hephaestus` `ip-contract` | DROP | sim 이후/이전 별도 단계 — 데모 골격 밖 |

`STAGE_MANIFEST.json`은 dangling 엔트리(드롭된 stage)를 남겨도 무방 — 엔진은
실행 시점에만 디렉토리를 찾고, 호출되지 않으면 무시(§2).

## 6. todo seed 다리 — 워크플로 개선 후보

todo 루프의 부품 3개가 있는데 **생성기→파일 다리가 끊겨** 있다:

```
stage_contract_todos.py  →  (stdout JSON only)   ✂ 끊김
cursor_todo.py add       →  current_todos.json   ←─ stop-todo-loop.py 가 읽음
```

- `workflow/req-gen/scripts/stage_contract_todos.py`는 locked req 번들을 읽어
  **obligation 1개당 todo 1개**(content/criteria/pass_condition 포함)를 만들지만
  `sys.stdout`에만 출력한다.
- `scripts/cursor_todo.py`는 `current_todos.json`을 직접 쓰지만 `add`로 한 개씩 수동.
- `hooks/stop-todo-loop.py`(stop, loop_limit 20)는 그 파일의 open todo를 끌고 간다.

**제안:** `cursor_todo.py seed <ip> <stage>` 서브커맨드(~10줄) = `stage_obligation_todos`
출력을 `current_todos.json`에 `pending`으로 적재(또는 id 기준 merge). 그러면
"stage 진입 시 seed → stop 훅이 obligation별로 끌고 감 → 게이트 증거로 close"가
완성된다. 단 stop 훅은 *조르기*만 하고 close는 에이전트 + 게이트가 한다(의도된
증거 규율). cf. [[workflow-improvement-candidates]].

## 7. 검증

슬림 팩 단독 스모크 (repo 루트 기준), 전부 통과:

| 스모크 | 결과 |
|---|---|
| 엔진 import (`from src.workflow_stage_engine import WorkflowStageEngine`) | OK |
| `rtl_to_signoff.py --help` (매니페스트 라우팅 로드) | OK |
| `check_sim_disk.py ghost_ip` | `FAIL: cannot locate IP` (crash 아님, 정직한 verdict) |
| `stage_contract_todos.py ghost_ip sim` (VCM projector) | JSON 출력 |
| `cursor_todo.py status` / `ip_wiki.py --help` | OK |

`--from-stage ssot-rtl --until lint`, `--from-stage ssot-tb-cocotb`가 쓰는 stage
(`ssot-fl-model → … → ssot-tb-cocotb`)는 모두 KEEP 안 — 데모 경로 미파손.

## 8. Open questions / 다음

- **model-free 트랙**: contract-only 검증을 1급으로 지원하려면 TB 생성기에
  scenario.expected 경로를 추가해야 함 (현재 `FunctionalModel` 결합).
- **seed 다리 구현 + 테스트**: §6 제안을 `tests/test_cursor_pack.py`에 seed→hook
  라운드트립으로 닫기.
- **[[cursor-agent-pack]] 동기화**: 그 문서는 MCP·전체 stage 기준(2026-06-10) —
  슬림/MCP-제거 반영 필요(stale).
- **VENDOR_MANIFEST/`test_cursor_pack` ratchet**: 슬림으로 깨질 수 있음 — 매니페스트
  재생성 or 테스트 갱신 필요.
