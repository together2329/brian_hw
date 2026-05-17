# arm_m0_min Approval Request

Status: approved and promoted.

This file is the human-facing summary for the final `req` gate. The user
approved the locked scope with `approve_locked_scope`, and
`workflow/req-gen/scripts/promote_requirement_review.py` promoted the approved
requirement packet into `arm_m0_min/req/`.

Quick review index: `arm_m0_min/doc/arm_m0_min_review_index.md`.
Completion readiness checklist:
`arm_m0_min/review/completion_readiness_checklist.md`.
User handoff and verification commands:
`arm_m0_min/doc/arm_m0_min_user_handoff.md`.

## Decision

Approved locked `arm_m0_min` minimal CPU scope.

Selected option: `approve_locked_scope`.

## Korean Summary

승인 대상은 production Cortex-M 호환 CPU가 아니라, common_ai_agent
workflow 검증용 minimal CPU IP입니다.

승인하면 다음 scope가 requirement로 고정됩니다:

- IP 이름: `arm_m0_min`
- 용도: 교육용 / reference용 ARMv6-M-like minimal CPU
- 명령어: `ADD`, `SUB`, `AND`, `ORR`, `EOR`, `MOV`, `CMP`, `LDR`, `STR`,
  `B`, `BEQ`, `BNE`, `LSL`, `LSR`, `ASR`
- 구조: 3-stage in-order IF / ID / EX-WB pipeline
- 버스: instruction/data 분리 AHB-Lite-like master
- 제외: interrupt, exception return, privilege, debug, MPU/MMU/cache, NVIC,
  SysTick

이 범위는 채팅의 `approve_locked_scope`로 승인되었고, promotion script가
review packet hash와 machine evidence hash를 검증한 뒤 `req/` artifact를
생성했습니다. 이후 final audit은 16/16으로 통과했습니다.

Approve only if this is the intended scope:

- Minimal ARMv6-M-like teaching/reference CPU.
- 15 Thumb-style operations: `ADD`, `SUB`, `AND`, `ORR`, `EOR`, `MOV`, `CMP`,
  `LDR`, `STR`, `B`, `BEQ`, `BNE`, `LSL`, `LSR`, `ASR`.
- 3-stage in-order IF / ID / EX-WB pipeline.
- Separate AHB-Lite-like instruction and data master interfaces.
- No interrupts, exception return, privilege, debug, MPU/MMU/cache, NVIC, or
  SysTick.

Reject and reopen SSOT scope if production ARM compatibility or any excluded
feature is required.

## Pinned Approval Target Used At Promotion

These hashes are the pre-promotion evidence snapshot that was validated before
writing `arm_m0_min/req/`.

| Item | Value |
|---|---|
| Review packet | `arm_m0_min/doc/arm_m0_min_requirement_review.md` |
| Review packet SHA256 | `e0b6e6a3d2078930bb046fd241a2422712af3155b4e823b2ec2da1bd64942a07` |
| Completion audit SHA256 | `a4d6ab7670a86ef355893425d1dc9f002ce985373185bca4f91879ecb852e69a` |
| SSOT SHA256 | `e51bbfba2a76b06e76af0c3ac503043171014bd48d50cf5a9239137ab09e18ef` |
| FL-vs-RTL compare SHA256 | `b7f758f1ecfd3a20ecab9472ec4f53834628fd9b9f1e057aa497a30a3319a062` |
| Coverage SHA256 | `2c24f41bc8fa8ecc67054d8776d51483f56ac992f9f8adbafe63cbf14644f4ed` |

## Current Evidence

- SSOT validator: pass, 36 sections, 0 TBDs.
- Review index: `arm_m0_min/doc/arm_m0_min_review_index.md`.
- RTL: 8 SystemVerilog modules.
- RTL inventory: `arm_m0_min/doc/arm_m0_min_rtl_inventory.md`.
- ISA/decode inventory: `arm_m0_min/doc/arm_m0_min_isa_decode_inventory.md`.
- RTL compile: pass, `iverilog`.
- DUT lint: pass, `pyslang+verilator`, 0 errors, 0 warnings.
- cocotb simulation: pass, 1 test, 0 failures/errors.
- FL-vs-RTL: 39 / 39 goals pass.
- Function coverage: 19 / 19 through RTL-observed scoreboard rows.
- Cycle coverage: 17 / 17 through RTL-observed scoreboard rows.
- Focused approval/audit/API regression: pass in latest verification.
- Temp-copy approval promotion regression: promotion of a copied `arm_m0_min`
  artifact reaches final audit 16 / 16.
- Final audit: 16 / 16 pass; blockers none.
- Approved requirement artifact: `arm_m0_min/req/arm_m0_min_requirements.md`.
- Approval manifest: `arm_m0_min/req/approval_manifest.json`.
- Existing `arm_m0_min/req/phase1_ledger.log` is only a phase marker. It is not
  the approval authority.

## Promotion Command Used

Historical preflight, which verifies the pinned review/evidence hashes without
writing `req/` artifacts:

```sh
python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min \
  --root . \
  --source arm_m0_min/doc/arm_m0_min_requirement_review.md \
  --approved-by dryrun \
  --decision-note "dry-run approval validation" \
  --dry-run \
  --json
```

Real promotion command:

```sh
python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min \
  --root . \
  --source arm_m0_min/doc/arm_m0_min_requirement_review.md \
  --approved-by brian \
  --decision-note "approved locked minimal CPU scope"

python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py arm_m0_min --root .
```

Observed result after approval: final audit `pass`, 16 / 16.

Use the real human approver name for `--approved-by`. Placeholder values such
as `dryrun`, `test`, `unknown`, or `n/a` are accepted only with `--dry-run` and
are rejected for real promotion.

## If Scope Is Later Rejected

Reopen the SSOT scope, then rerun downstream workflow stages from the changed
authority point.
