# arm_m0_min Completion Readiness Checklist

Status: complete; locked requirement scope is human-approved.

This checklist maps the original goal, "make one CPU and help if blocked", to
real artifacts. It is a review aid only; the approval authority is the promoted
requirement packet and manifest under `arm_m0_min/req/`.

## Objective

Deliver a small CPU IP through the common_ai_agent evidence pipeline, using the
project wiki and workflow rules, and stop only when the generated CPU has real
SSOT, model, RTL, TB, sim, lint, coverage, equivalence, and requirement
approval evidence.

## Locked CPU Scope

- IP: `arm_m0_min`
- Intended use: minimal ARMv6-M-like teaching/reference CPU
- ISA subset: `ADD`, `SUB`, `AND`, `ORR`, `EOR`, `MOV`, `CMP`, `LDR`, `STR`,
  `B`, `BEQ`, `BNE`, `LSL`, `LSR`, `ASR`
- Microarchitecture: 3-stage in-order IF / ID / EX-WB pipeline
- Bus: separate AHB-Lite-like instruction/data master interfaces
- Explicitly out of scope: interrupts, exception return, privilege, debug,
  MPU/MMU/cache, NVIC, SysTick, and production ARM compatibility

## Prompt To Artifact Checklist

| Requirement | Evidence | Current result |
|---|---|---|
| CPU IP exists | `arm_m0_min/` | pass |
| SSOT exists and is the authority | `arm_m0_min/yaml/arm_m0_min.ssot.yaml` | pass |
| Functional model exists | `arm_m0_min/model/functional_model.py`, `arm_m0_min/model/fl_model_check.json` | pass |
| Cycle model exists | `arm_m0_min/model/cycle_model.py`, SSOT `cycle_model` section | pass |
| RTL exists | 8 files under `arm_m0_min/rtl/`, listed in `arm_m0_min/list/arm_m0_min.f` | pass |
| RTL has compile evidence | `arm_m0_min/rtl/rtl_compile.json` | pass |
| RTL has DUT lint evidence | `arm_m0_min/lint/dut_lint.json` | pass |
| TB exists | `arm_m0_min/tb/cocotb/` | pass |
| Simulation ran | `arm_m0_min/sim/results.xml`, `arm_m0_min/sim/arm_m0_min.vcd` | pass |
| Scoreboard covers goals | `arm_m0_min/sim/scoreboard_events.jsonl` | pass |
| FL-vs-RTL equivalence passes | `arm_m0_min/sim/fl_rtl_compare.json` | pass, 39/39 |
| Function/cycle coverage is closed | `arm_m0_min/cov/coverage.json` `function_coverage` and `cycle_coverage` | pass: 19/19 function bins, 17/17 cycle bins |
| Human requirement approval exists | `arm_m0_min/req/arm_m0_min_requirements.md`, `arm_m0_min/req/approval_manifest.json` | pass |
| Final goal audit passes | `arm_m0_min/sim/fl_rtl_goal_audit.json` | pass, 16/16, blockers=none |
| Wiki handoff is discoverable | `doc/wiki/arm-m0-min-current-status.md`, `arm_m0_min/wiki/index.md` | pass |

## Current Machine Evidence

- Final audit command:
  `python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py arm_m0_min --root .`
- Current result: `status=pass`, `passed=16/16`, `blockers=none`.
- Fresh compile/lint/sim smoke:
  `iverilog -g2012 -o /tmp/arm_m0_min_fresh_compile.vvp -f list/arm_m0_min.f`
  passed; `verilator --lint-only -Wall -f list/arm_m0_min.f` passed with
  0 errors and 0 warnings; `COMMON_AI_AGENT_ROOT=... python3
  arm_m0_min/tb/cocotb/test_runner.py` passed with `TESTS=1 PASS=1 FAIL=0`.
- FL-vs-RTL compare: `39/39` goals pass, with no failed, blocked, or stale
  goals. No-op compare reruns now preserve raw file hash; current stable
  compare SHA256 is
  `b7f758f1ecfd3a20ecab9472ec4f53834628fd9b9f1e057aa497a30a3319a062`.
- Simulation summary: `1` test, `0` failures, `0` errors.
- Coverage summary: `arm_m0_min/cov/coverage.json` has
  `function_coverage=19/19` and `cycle_coverage=17/17` from scoreboard-backed
  RTL observations. The file-level `status` remains `blocked` only because
  structural line/branch coverage instrumentation is not part of this
  pre-approval evidence set.
- Focused regression:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_goal_audit_requirement_review.py tests/test_requirement_promotion.py tests/test_review_decisions.py tests/test_atlas_api_pipeline_state.py tests/test_wiki_query_tool.py tests/test_prompt_to_artifact_checklist_audit.py tests/test_fl_rtl_equivalence_loop.py::test_comparator_preserves_hash_on_noop_rerun -q`
- Regression result: pass in latest verification. Rerun the
  command before real promotion if any approval evidence changes.
- Wiki discovery:
  `wiki_query(topic="arm m0 handoff", depth=3)` finds
  `doc/wiki/arm-m0-min-current-status.md`; `wiki_query(ip="arm_m0_min",
  topic="CPU handoff approval req", depth=3)` finds `arm_m0_min/wiki/index.md`.
- Pipeline API smoke:
  `/api/pipeline/state?ip=arm_m0_min` returns
  `orchestrator.decisions_needed=0`, no decision items, and `goal-audit` as
  passed.
- Prompt-to-artifact checklist audit:
  `python3 workflow/req-gen/scripts/audit_prompt_to_artifact_checklist.py arm_m0_min --root . --write --json`
  returns `status=pass`, `completion_ready=true`, `blocked_items=[]`, and no
  consistency errors, and writes
  `arm_m0_min/review/prompt_to_artifact_checklist_audit.json`.
  This validates the JSON checklist against current disk evidence without
  approving the CPU.
- Temp-copy approval validation is covered by
  `tests/test_goal_audit_requirement_review.py`: promotion on a temporary copy
  reaches final audit `16/16 blockers=none`.
- Real approval promotion:
  `python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min --root . --source arm_m0_min/doc/arm_m0_min_requirement_review.md --approved-by brian --decision-note 'approved locked minimal CPU scope'`
  wrote the approved requirement artifact and approval manifest.
- Project wiki graph:
  `python3 workflow/wiki/build_graph.py --check` passed with `broken_refs=0`.

## Approval Evidence

The real repository now contains:

- `arm_m0_min/req/arm_m0_min_requirements.md`
- `arm_m0_min/req/approval_manifest.json`

The existing `arm_m0_min/req/phase1_ledger.log` remains only a phase marker and
is not the approval authority.

## Stop Condition

The locked CPU scope has been approved and promoted. If the scope is no longer
acceptable, reopen SSOT scope before regenerating downstream artifacts.
