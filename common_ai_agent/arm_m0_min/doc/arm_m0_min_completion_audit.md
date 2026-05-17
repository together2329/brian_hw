# arm_m0_min Completion Audit

Status: complete; machine evidence and human requirement approval are green.

This audit maps the user objective, "CPU 하나 만들어줘 안되면 니가 도움좀 주고. wiki 참고",
to concrete artifacts and evidence. The human-approved requirement authority now
lives under `arm_m0_min/req/`.

## Deliverable Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Create one CPU IP | `arm_m0_min/yaml/arm_m0_min.ssot.yaml` declares `top_module.name=arm_m0_min` and CPU scope | pass |
| Follow wiki/common workflow authority | `doc/wiki/arm-m0-min-pipeline-run.md` records the reference run and limitations | pass |
| Produce SSOT | `workflow/ssot-gen/scripts/check_ssot_disk.sh arm_m0_min` reports signoff-mode pass, 36 sections, 0 TBDs | pass |
| Produce executable FL/cycle model evidence | `arm_m0_min/model/functional_model.py`, `arm_m0_min/model/fl_model_check.json`, `arm_m0_min/model/decomposition.json` | pass |
| Generate SSOT-derived equivalence goals | `arm_m0_min/verify/equivalence_goals.json`, 39 required goals, 0 blocked | pass |
| Produce RTL CPU implementation | 8 RTL files under `arm_m0_min/rtl/` plus `arm_m0_min/list/arm_m0_min.f` | pass |
| Compile RTL with real HDL tool | `arm_m0_min/rtl/rtl_compile.json`, `passed=true`, `errors=0`, tool `iverilog` | pass |
| Lint RTL with real HDL lint/parser tool | `arm_m0_min/lint/dut_lint.json`, `passed=true`, `errors=0`, `warnings=0`, tool `pyslang+verilator` | pass |
| Produce generated TB/sim evidence | `arm_m0_min/sim/results.xml`, `arm_m0_min/sim/scoreboard_events.jsonl`, `arm_m0_min/sim/arm_m0_min.vcd` | pass |
| Prove FL-vs-RTL goals | `arm_m0_min/sim/fl_rtl_compare.json`, 39 checked, 39 passed, 0 failed, 0 blocked | pass |
| Link function/cycle coverage to RTL-observed scoreboard rows | `arm_m0_min/cov/coverage.json`, function domain 19/19 and cycle domain 17/17 through RTL-observed evidence | pass |
| Avoid pass-for-pass signoff | `arm_m0_min/sim/fl_rtl_goal_audit.json` passes only after approved `req/` evidence exists | pass |
| Resolve human blocker in UI/orchestrator review queue | `arm_m0_min/review/decision_needed_req_requirement_approval.json` is resolved and `/api/pipeline/state` reports no open decisions | pass |
| Human-approved requirement contract | `arm_m0_min/req/arm_m0_min_requirements.md` and `arm_m0_min/req/approval_manifest.json` exist and are hash-checked by the final audit | pass |

## Current Stop Condition

`arm_m0_min/sim/fl_rtl_goal_audit.json` reports all checks passing, including
`req_ok=true`. The approved requirement source packet is:

- `arm_m0_min/doc/arm_m0_min_requirement_review.md`

The resolved review queue item is:

- `arm_m0_min/review/decision_needed_req_requirement_approval.json`
- `arm_m0_min/review/approval_request.md` is the short human-facing summary
  with the approval target hash, evidence hashes, approve/reject criteria, and
  promotion command.

That packet was approved by the user with `approve_locked_scope` and promoted
into `arm_m0_min/req/` with the command below. Promotion also resolved the
review queue item so the UI/orchestrator no longer reports the human approval
blocker.

```sh
python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min \
  --root . \
  --source arm_m0_min/doc/arm_m0_min_requirement_review.md \
  --approved-by brian \
  --decision-note "approved locked minimal CPU scope"
```

After promotion, rerun:

```sh
python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py arm_m0_min --root .
```

The final audit now passes.

## Approval Dry Run

The approval path was tested on a temporary copy of `arm_m0_min`, without
modifying the real IP artifact:

```sh
tmp=$(mktemp -d /tmp/arm_m0_min_approval_dryrun.XXXXXX)
cp -R arm_m0_min "$tmp/arm_m0_min"
python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min \
  --root "$tmp" \
  --source "$tmp/arm_m0_min/doc/arm_m0_min_requirement_review.md" \
  --approved-by dryrun \
  --decision-note "approval dry run"
python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py arm_m0_min --root "$tmp"
```

Dry-run result:

- final audit: `pass`, 16 / 16
- `req_ok`: `true`
- `signoff_evidence_backed`: `true`
- review decision status: `resolved`
- `req/approval_manifest.json`: present, with matching `target_sha256` and
  `source_sha256`
- review decision `evidence.approval_target.sha256`: checked before promotion,
  so stale review-packet edits cannot be promoted accidentally
- review decision `evidence.machine_evidence_snapshot`: checked before
  promotion for pinned SSOT, FL-vs-RTL compare, coverage, and completion-audit
  files, so stale machine evidence cannot be silently approved
- approved requirement body: review-only `pending user review` / `not a
  human-approved requirement artifact` status text is removed during promotion

The real `arm_m0_min` has been approved and promoted with the same guard path.

## Focused Regression

Latest focused regression for the approval/audit/review-queue path:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_goal_audit_requirement_review.py \
  tests/test_requirement_promotion.py \
  tests/test_review_decisions.py \
  tests/test_atlas_api_pipeline_state.py \
  tests/test_wiki_query_tool.py \
  tests/test_prompt_to_artifact_checklist_audit.py \
  tests/test_fl_rtl_equivalence_loop.py::test_comparator_preserves_hash_on_noop_rerun \
  -q
```

Result: pass in latest verification.

Focused promotion-guard regression:

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_requirement_promotion.py -q
```

Result: `10 passed`.

Additional live UI/API state check on the real `arm_m0_min` artifact:

- `/api/pipeline/state?ip=arm_m0_min`: HTTP 200
- `orchestrator.enabled=true`
- `orchestrator.decisions_needed=0`
- `orchestrator.decision_items=[]`
- `stages.goal-audit.state=passed`
- `stages.goal-audit.source=fs`
- `stages.goal-audit.error_summary=""`

## Known Limits

- `arm_m0_min` is a minimal ARMv6-M-like teaching/reference CPU, not a
  production Cortex-M compatible implementation.
- Interrupts, exception return, privilege, debug, MPU/MMU/cache, and system
  peripherals are outside the locked scope.
- Structural line/branch coverage is not claimed; function and cycle coverage
  are claimed through RTL-observed scoreboard evidence.
