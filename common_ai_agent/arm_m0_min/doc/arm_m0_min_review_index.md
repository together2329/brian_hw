# arm_m0_min Review Index

Status: review aid only. The requirement approval artifact now lives under
`arm_m0_min/req/`.

This page is the shortest path for reviewing the current `arm_m0_min` CPU
artifact after approval of the locked minimal CPU scope.

## Current State

- CPU artifact exists: `arm_m0_min`
- Machine evidence status: green
- Final audit status: pass
- Real final audit today: 16 / 16, blockers none
- Real approval promotion: `arm_m0_min/req/arm_m0_min_requirements.md` plus
  `arm_m0_min/req/approval_manifest.json`

The resolved review decision remains as historical evidence of the approval.

## Review Order

1. Read `arm_m0_min/review/approval_request.md`.
2. Check the prompt-to-artifact readiness map:
   `arm_m0_min/review/completion_readiness_checklist.md`.
3. If a tool needs the same audit in JSON form, read
   `arm_m0_min/review/prompt_to_artifact_checklist.json`.
4. If a tool needs the latest checklist consistency result, read
   `arm_m0_min/review/prompt_to_artifact_checklist_audit.json`.
5. For project-level wiki discovery and future-agent handoff, read
   `doc/wiki/arm-m0-min-current-status.md`.
6. For use and verification commands, read
   `arm_m0_min/doc/arm_m0_min_user_handoff.md`.
7. If more detail is needed, read
   `arm_m0_min/doc/arm_m0_min_requirement_review.md`.
8. Inspect RTL structure:
   `arm_m0_min/doc/arm_m0_min_rtl_inventory.md`.
9. Inspect ISA/decode mapping:
   `arm_m0_min/doc/arm_m0_min_isa_decode_inventory.md`.
10. Check machine audit mapping:
   `arm_m0_min/doc/arm_m0_min_completion_audit.md`.

## What Approval Means

Approval means accepting this locked scope:

- Minimal ARMv6-M-like teaching/reference CPU.
- 15 Thumb-style operations: `ADD`, `SUB`, `AND`, `ORR`, `EOR`, `MOV`,
  `CMP`, `LDR`, `STR`, `B`, `BEQ`, `BNE`, `LSL`, `LSR`, `ASR`.
- 3-stage in-order IF / ID / EX-WB pipeline.
- Separate AHB-Lite-like instruction and data master interfaces.
- No interrupts, exception return, privilege, debug, MPU/MMU/cache, NVIC, or
  SysTick.

That scope was approved with `approve_locked_scope`. If it is no longer
correct, reopen SSOT scope before downstream stages are rerun.

For historical preflight or re-approval on a copy, the same guard checks can be
run without writing `req/` artifacts. In dry-run output, `target_sha256` is a
preview for the printed `approved_at_utc`, `approved_by`, and `decision_note`;
real approval may produce a different target hash.

```sh
python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min \
  --root . \
  --source arm_m0_min/doc/arm_m0_min_requirement_review.md \
  --approved-by dryrun \
  --decision-note "dry-run approval validation" \
  --dry-run \
  --json
```

## Evidence Locations

| Evidence | Path |
|---|---|
| SSOT | `arm_m0_min/yaml/arm_m0_min.ssot.yaml` |
| RTL filelist | `arm_m0_min/list/arm_m0_min.f` |
| RTL modules | `arm_m0_min/rtl/*.sv` |
| TB | `arm_m0_min/tb/cocotb/test_arm_m0_min.py` |
| Simulation result | `arm_m0_min/sim/results.xml` |
| Scoreboard rows | `arm_m0_min/sim/scoreboard_events.jsonl` |
| FL-vs-RTL compare | `arm_m0_min/sim/fl_rtl_compare.json` |
| Coverage | `arm_m0_min/cov/coverage.json` |
| Final audit | `arm_m0_min/sim/fl_rtl_goal_audit.json` |
| User handoff | `arm_m0_min/doc/arm_m0_min_user_handoff.md` |
| Completion readiness checklist | `arm_m0_min/review/completion_readiness_checklist.md` |
| Machine-readable prompt checklist | `arm_m0_min/review/prompt_to_artifact_checklist.json` |
| Prompt checklist consistency audit | `arm_m0_min/review/prompt_to_artifact_checklist_audit.json` |
| Project wiki current status | `doc/wiki/arm-m0-min-current-status.md` |
| Resolved review decision | `arm_m0_min/review/decision_needed_req_requirement_approval.json` |
| Approved requirements | `arm_m0_min/req/arm_m0_min_requirements.md` |
| Approval manifest | `arm_m0_min/req/approval_manifest.json` |

## Guardrail

Do not treat this index, the approval request, or the review packet as the
approval authority. The approved authority is the promoted `req/` artifact plus
`approval_manifest.json`, and the final audit must pass after promotion.

For real promotion, `--approved-by` must be a real human approver name.
Placeholder values such as `dryrun`, `test`, `unknown`, or `n/a` are allowed
only for `--dry-run` preflight and are rejected by the promotion script.

`arm_m0_min/req/phase1_ledger.log` is only a phase marker from earlier evidence
refresh work. It is not a requirement markdown file, has no approval manifest,
and must not be interpreted as human requirement approval.

For tool-driven consistency checking, run:

```sh
python3 workflow/req-gen/scripts/audit_prompt_to_artifact_checklist.py arm_m0_min --root . --json
```

Expected post-approval result is `status=pass`, `completion_ready=true`, no
consistency errors, and no blocked items.
