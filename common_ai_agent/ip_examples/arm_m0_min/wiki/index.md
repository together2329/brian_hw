# arm_m0_min CPU README Handoff Wiki Index

Status: this CPU README handoff index points to `arm_m0_min/README.md` as the
root README entry point and shows that generated artifacts are present, but
final signoff is blocked on the human-owned `req` approval gate.

Use this page as the IP-local starting point for reviewing the CPU. The root
README entry point is `arm_m0_min/README.md`. Neither this page nor the README
is a requirement approval artifact.

## Current Result

- CPU scope: minimal ARMv6-M-like teaching/reference CPU.
- Machine evidence: SSOT, FL/CL models, RTL, filelist, TB, sim, scoreboard,
  FL-vs-RTL compare, lint, and coverage artifacts exist.
- Current final audit before approval: `status=fail passed=15/16 blockers=req`.
- Missing approval artifacts:
  - `arm_m0_min/req/arm_m0_min_requirements.md`
  - `arm_m0_min/req/approval_manifest.json`

## Start Here

1. Root README entry point:
   `arm_m0_min/README.md`
2. User handoff and verification commands:
   `arm_m0_min/doc/arm_m0_min_user_handoff.md`
3. Human approval request:
   `arm_m0_min/review/approval_request.md`
4. Prompt-to-artifact checklist:
   `arm_m0_min/review/completion_readiness_checklist.md`
5. Review order and evidence map:
   `arm_m0_min/doc/arm_m0_min_review_index.md`

## Artifact Map

| Area | Path |
|---|---|
| SSOT | `arm_m0_min/yaml/arm_m0_min.ssot.yaml` |
| Functional model | `arm_m0_min/model/functional_model.py` |
| Cycle model | `arm_m0_min/model/cycle_model.py` |
| RTL | `arm_m0_min/rtl/*.sv` |
| Filelist | `arm_m0_min/list/arm_m0_min.f` |
| TB | `arm_m0_min/tb/cocotb/test_arm_m0_min.py` |
| Sim result | `arm_m0_min/sim/results.xml` |
| Scoreboard | `arm_m0_min/sim/scoreboard_events.jsonl` |
| FL-vs-RTL compare | `arm_m0_min/sim/fl_rtl_compare.json` |
| Coverage | `arm_m0_min/cov/coverage.json` |
| Final audit | `arm_m0_min/sim/fl_rtl_goal_audit.json` |

## Approval Rule

Do not manually create files under `arm_m0_min/req/`. If the locked scope is
accepted, the human decision is `approve_locked_scope`; then use
`workflow/req-gen/scripts/promote_requirement_review.py` to promote the reviewed
packet and rerun the final audit.
