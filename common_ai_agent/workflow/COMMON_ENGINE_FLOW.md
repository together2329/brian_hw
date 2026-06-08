# Common Engine IP Flow

This is the canonical flow for hardware IP generation in common_ai_agent.
ATLAS Web UI, Textual UI, and headless TDD must call the same engine path.

Todo approval and cross-stage evidence policy are defined in
[`doc/golden_todo_evidence_flow.md`](../doc/golden_todo_evidence_flow.md).
In short: LLMs author artifacts, TodoTracker owns execution state, validators
approve evidence, and human review owns product/spec decisions.
The user-facing end-to-end operating model is
[`doc/ai_driven_ip_development_guide.md`](../doc/ai_driven_ip_development_guide.md).
The cross-linked wiki entry point for LLM/agent navigation is
[`../doc/wiki/index.md`](../doc/wiki/index.md).

## Control Surfaces

| Surface | Responsibility | Must not own |
| --- | --- | --- |
| ATLAS Web UI | Render state, collect human-gate answers, queue repair prompts | Stage execution logic |
| Textual UI | Register slash commands and display stage output | Stage execution logic |
| Headless | TDD/CI adapter for the same flow without UI | Separate product behavior |

## Engine Boundary

- `src/workflow_stage_engine.py` owns deterministic stage execution, artifact paths, validators, return status, and run logs.
- `src/workflow_stage_surface.py` owns UI-neutral adapter policy: workflow/session names, repair prompt routing, and human-gate signals.
- UI files may call the surface adapter and render its result. They may not reimplement RTL/TB/sim validators.
- During pipeline tests, agents must not manually patch generated IP artifacts to make a stage pass. They must classify owner, route repair through the owning workflow, and rerun the common-engine validator.

## Canonical Flow

1. Requirement and contract capture
   - Input: `req/*.json` review candidate or imported requirement evidence.
   - Mandatory locked authority, once approved: `req/requirements_index.json`, `req/obligations.json`, `req/structural_contracts.json`, `req/behavioral_contracts.json`, `req/evidence_plan.json`, and `req/approval_manifest.json`.
   - `contract_refs.json` is an index/anchor layer only; each required obligation must be backed by structural and/or behavioral contracts.
   - Behavioral contracts must carry function semantics plus cycle/timing semantics, or an explicit cycle waiver. Executable Function/Cycle Model files are optional projections, not the authority.
   - Gate: `python3 workflow/req-gen/scripts/check_contract_bundle.py <ip> --root <ip-parent>` writes `req/contract_authority_report.json` and `req/contract_closure.json`.
   - Human owns product intent, undefined behavior, protocol choices, waivers, and acceptance criteria.

2. SSOT generation and approval
   - Output: `<ip>/yaml/<ip>.ssot.yaml`.
   - SSOT is the Design Spec projection used by downstream generators. When locked req contracts exist, req/ is the authority and SSOT must project it without inventing replacement intent.
   - `ssot-gen` LLM must author `workflow_todos.<stage>[]` when downstream work needs explicit decomposition. For `rtl-gen`, each item must include `content`, `detail`, `criteria`, and `source_refs`.
   - For full-flow smoke tests, `/mode auto-select` lets `ask_user` choose the explicit `Suggest:` answer, recommended/default option, or first safe option and record the QA card as approved with source `llm-ssot-qna.auto_select`.
   - For existing IP material, run `/import --ip <ip> <doc_or_rtl_paths...>` before `/grill-me` or `/to-ssot`. Import writes evidence under `<ip>/req/imports/`, `<ip>/req/import_manifest.json`, `<ip>/req/extracted_decisions.json`, and `<ip>/wiki/import-evidence.md`; `/to-ssot` still writes the canonical YAML.
   - `workflow_todos.<stage>[]` is the executable handoff ledger. Each executable item carries `command`, `script`, `instructions`, `content`, `detail`, `criteria`, and `source_refs`.
   - Missing semantics must produce a human gate, not a fixed template workaround.

3. Functional model generation
   - Command: `/ssot-fl-model <ip>`.
   - Engine stage: `ssot-fl-model`.
   - Output: executable `model/functional_model.py`, `model/decomposition.json`, `model/fl_model_check.json`, and `cov/fcov_plan.json`.

4. FL-vs-RTL equivalence goal generation
   - Command: `/ssot-equiv-goals <ip>`.
   - Engine stage: `ssot-equiv-goals`.
   - Output: `verify/equivalence_goals.json`.
   - Goals define what the LLM repair loop can prove and what must remain human-owned.

5. RTL generation and DUT-only approval
   - Command: `/ssot-rtl <ip>`.
   - Engine stage: `ssot-rtl`.
   - Output: RTL, filelist, `rtl/rtl_todo_plan.json`, `rtl/rtl_traceability.json`, `rtl/rtl_contract.json`, `rtl/rtl_compile.json`, and `lint/dut_lint.json`.
   - Internal order: when `req/approval_manifest.json` exists, command handler `stage:ssot-rtl` first runs `check_contract_bundle.py`. It then runs `python3 "$ATLAS_WORKFLOW_ROOT/rtl-gen/scripts/derive_rtl_todos.py" <ip> --root "$ATLAS_PROJECT_ROOT"`, writes `rtl/rtl_todo_plan.json`, `rtl/rtl_todo_tracker.json`, and `todo/rtl_todo_tracker.json`, then loads that dynamic tracker into the existing TodoTracker.
   - RTL-gen must treat the current SSOT as a binding contract for top ports, submodule files, filelist, registers, function/cycle behavior, timing, synthesis, and quality gates. Existing RTL is reuse evidence only; stale/generic RTL is repaired by rtl-gen, not accepted downstream.
   - `rtl-gen` must derive its active TODOs from SSOT, including all `workflow_todos.rtl-gen[]` items, and continue generation/repair until every required TODO has `todo_completion.status=pass`.
   - DUT-only compile/lint evidence is mandatory. Sim/TB logs are not lint approval.

6. Testbench generation
   - Default command: `/ssot-tb <ip>` or `/ssot-tb-cocotb <ip>`.
   - Engine stage: `ssot-tb-cocotb`.
   - Output: pyuvm/cocotb-style environment, goal-driven scoreboard, TB manifest, and generation report.
   - When locked req contracts exist, `check_contract_bundle.py` must pass before TB generation starts.
   - The scoreboard must compare RTL observations against FunctionalModel results.

7. Simulation
   - Command: `/sim <ip>`.
   - Engine stage: `sim`.
   - Output: simulation result, scoreboard events, coverage evidence, and report artifacts.

8. Sim debug and ownership classification
   - Command: `/sim-debug <ip>`.
   - Engine stage: `sim-debug`.
   - Output: `sim/fl_rtl_compare.json` and `sim/mismatch_classification.json`.
   - LLM may repair only classifications with `llm_loop_allowed: true`.
   - Human gate is required for semantic decisions, waivers, or undefined behavior.

9. Goal audit and signoff
   - Command: `/goal-audit <ip>`.
   - Engine stage: `goal-audit`.
   - Output: `sim/fl_rtl_goal_audit.json`.
   - Signoff requires SSOT, FL model, cycle model, RTL compile/lint, TB, sim, coverage, sim-debug, and goal audit evidence.

## General Evaluation And Human-Gate Contract

LLM loops are allowed where a general criterion has objective evidence:
PASS/FAIL/DIFF, coverage gap, lint/compile diagnostic, protocol assertion,
traceability gap, stale evidence, waveform/probe gap, or measured performance
gap. Exact FL-vs-RTL behavior is the most important criterion, but it is not the
only criterion.

General criteria:

- Traceability: every generated artifact traces to SSOT refs.
- TODO closure: every required SSOT-derived TODO, including `workflow_todos.rtl-gen[]`, passes its content/detail/criteria gate.
- Functional equivalence: RTL observables match FunctionalModel results.
- Module equivalence: behavior-owning modules pass module-boundary checks before top signoff.
- Coverage closure: SSOT coverage goals are hit by passing RTL-observed scoreboard evidence.
- Interface/protocol correctness: ports, reset, handshakes, ordering, backpressure, and errors obey SSOT.
- DUT-only compile/lint quality: zero unwaived errors, warnings, and style diagnostics.
- Simulation evidence quality: results, scoreboard rows, coverage, and waveforms are fresh and structured.
- Performance/cycle evidence: cycle_model/timing targets are measured or escalated.
- Debug observability: waveforms/probes can explain reset, interface activity, state, outputs, and failures.
- Maintainability: no fixed IP workaround; RTL/TB stays SSOT-owned, modular, and reviewable.
- Human decisions: intent, semantic rule changes, waivers, interface changes, tradeoffs, and signoff remain human-owned.

Loopable points:

- Traceability gap: add missing artifact refs/ownership or open a human gate if ownership is undefined.
- FL expected vs RTL actual: patch RTL, rerun module/top cocotb, and compare again.
- Module FL expected vs RTL module boundary actual: patch only the owning RTL module.
- Coverage goal vs coverage result: add stimulus/tests/vectors; do not change the goal.
- Lint/compile rule vs diagnostic: patch syntax, width, driver, and coding style issues.
- Interface/cycle assertion vs failure: patch the classified RTL/TB owner against the locked contract.
- CL target vs measured performance: sweep candidates and report tradeoffs; do not change the target.
- Regression minimization: reduce a failing random sequence to the smallest reproducer.
- Report/root-cause: write expected/actual/waveform/coverage evidence and the owner-specific repair prompt.

Locked human-approved artifacts:

- Requirement intent/scope/priority and acceptance criteria.
- SSOT behavior/spec, interface contract, coverage goals, waivers, and performance targets.
- FunctionalModel golden semantics.
- Final signoff.

LLM-editable artifacts:

- RTL, cocotb/pyuvm TB, test vectors, scoreboard implementation, lint/style fixes, reports, and generated evidence.

Hard rule: if RTL does not match FL, the loop repairs RTL or reports a human gate.
It must not change FL, coverage goals, interface rules, or performance targets just
to make the run pass.

Approval rule: default todo approval is evidence-based across pipeline, CI, and
interactive chat. LLM `reason` explains the attempted work; it is not the
default authority for `approved`. If deterministic evidence cannot exist for a
semantic decision, the item should move to `human_review_needed`, not `rejected`.

## TDD Contract

Headless tests are the first regression line:

- They drive the common engine without ATLAS Web or Textual UI.
- They validate prompt contracts, SSOT gates, engine stage logs, and full fake-provider flow.
- They prevent duplicated UI logic from becoming the source of truth.

Required checks for common-flow changes:

```bash
python3 -m py_compile src/workflow_stage_engine.py src/workflow_stage_surface.py src/headless_workflow.py src/atlas_ui.py workflow/loader.py
python3 -m pytest tests/test_workflow_stage_engine.py tests/test_workflow_stage_surface.py tests/test_workflow/test_loader_unit.py::TestMakeCommandHandler -q
python3 -m pytest tests/test_headless_llm_contracts.py tests/test_headless_workflow_runner.py -q
```

## Removed Legacy Entry Points

The old direct/MAS-era commands are intentionally not registered:

- `/new-ip-rtl`
- `/legacy-ip-rtl`
- `/new-ip-tb`
- `/legacy-ip-tb`
- `/legacy-ip`

Use the SSOT/common-engine commands instead. Historical todo templates may remain only as reference material until their tests are migrated or deleted; they must not be user-visible command entry points.
