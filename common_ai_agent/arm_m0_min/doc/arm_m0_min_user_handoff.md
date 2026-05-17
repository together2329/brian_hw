# arm_m0_min User Handoff

Status: CPU artifacts are generated, the locked scope is approved, and final
signoff passes.

This page is for using and reviewing the generated CPU without mutating the
pinned approval packet.

## What Was Built

- IP: `arm_m0_min`
- Scope: minimal ARMv6-M-like teaching/reference CPU
- ISA subset: `ADD`, `SUB`, `AND`, `ORR`, `EOR`, `MOV`, `CMP`, `LDR`, `STR`,
  `B`, `BEQ`, `BNE`, `LSL`, `LSR`, `ASR`
- Microarchitecture: 3-stage in-order IF / ID / EX-WB pipeline
- Bus: separate AHB-Lite-like instruction and data master interfaces
- Excluded: interrupts, exception return, privilege, debug, MPU/MMU/cache,
  NVIC, SysTick, production ARM compatibility

## Main Artifacts

| Area | Path |
|---|---|
| SSOT | `arm_m0_min/yaml/arm_m0_min.ssot.yaml` |
| Functional model | `arm_m0_min/model/functional_model.py` |
| Cycle model | `arm_m0_min/model/cycle_model.py` |
| RTL | `arm_m0_min/rtl/*.sv` |
| Filelist | `arm_m0_min/list/arm_m0_min.f` |
| Cocotb TB | `arm_m0_min/tb/cocotb/test_arm_m0_min.py` |
| Simulation result | `arm_m0_min/sim/results.xml` |
| Scoreboard rows | `arm_m0_min/sim/scoreboard_events.jsonl` |
| FL-vs-RTL compare | `arm_m0_min/sim/fl_rtl_compare.json` |
| Coverage | `arm_m0_min/cov/coverage.json` |
| Approval request | `arm_m0_min/review/approval_request.md` |
| Approved requirements | `arm_m0_min/req/arm_m0_min_requirements.md` |
| Approval manifest | `arm_m0_min/req/approval_manifest.json` |

## Fresh Status Commands

Run from `common_ai_agent/`.

```sh
python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py arm_m0_min --root .
```

Current expected result:

```text
status=pass passed=16/16 blockers=none
```

The approved requirement packet lives under `arm_m0_min/req/`.

Focused regression:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_goal_audit_requirement_review.py \
  tests/test_requirement_promotion.py \
  tests/test_review_decisions.py \
  tests/test_atlas_api_pipeline_state.py -q
```

Latest verified result: pass in latest verification. Rerun this command before
real promotion if any approval evidence changes.

Historical approval preflight command:

```sh
python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min \
  --root . \
  --source arm_m0_min/doc/arm_m0_min_requirement_review.md \
  --approved-by dryrun \
  --decision-note "dry-run approval validation" \
  --dry-run \
  --json
```

## Approval Boundary

Do not manually edit `arm_m0_min/req/arm_m0_min_requirements.md`. The real
approval went through:

```sh
python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min \
  --root . \
  --source arm_m0_min/doc/arm_m0_min_requirement_review.md \
  --approved-by brian \
  --decision-note "approved locked minimal CPU scope"
```

After real promotion, the final audit result is:

```text
status=pass passed=16/16 blockers=none
```

## Korean Review Checklist

승인된 범위는 다음입니다.

- 이 CPU는 production Cortex-M 호환 코어가 아니라 workflow 검증용
  minimal ARMv6-M-like reference CPU입니다.
- 승인되는 명령어 범위는 `ADD`, `SUB`, `AND`, `ORR`, `EOR`, `MOV`, `CMP`,
  `LDR`, `STR`, `B`, `BEQ`, `BNE`, `LSL`, `LSR`, `ASR`입니다.
- 구조는 3-stage IF / ID / EX-WB in-order pipeline입니다.
- interrupt, exception return, privilege, debug, MPU/MMU/cache, NVIC,
  SysTick은 scope 밖입니다.
- 이 범위가 부족하면 승인 상태를 그대로 두지 말고 SSOT scope를 다시 열어야 합니다.

## Review Path

1. Read `arm_m0_min/review/approval_request.md`.
2. Read `arm_m0_min/review/completion_readiness_checklist.md`.
3. Read `arm_m0_min/doc/arm_m0_min_review_index.md`.
4. Inspect RTL details in `arm_m0_min/doc/arm_m0_min_rtl_inventory.md`.
5. Inspect ISA/decode details in `arm_m0_min/doc/arm_m0_min_isa_decode_inventory.md`.

The current CPU is approved for this locked teaching/reference scope. It is not
approved production ARM IP.
