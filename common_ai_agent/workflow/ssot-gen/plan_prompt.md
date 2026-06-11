# SSOT Generation Plan

You are planning a leaf IP YAML SSOT generation project.

The ssot-gen workflow owns the SSOT contract only. It must not generate
production RTL, testbenches, or simulations. Those are downstream rtl-gen,
tb-gen, and sim workflow responsibilities.

## Phase 1: Requirements Gathering
1. Read any existing requirement files in the current directory. If `req/approval_manifest.json` exists, treat the locked truth bundle under `req/` as authority and treat the YAML SSOT as a generator-ready Design Spec projection.
2. Extract IP name, top-level type, purpose, clock/reset, interfaces, parameters, memories, registers, interrupts, function behavior, cycle/latency behavior, debug visibility, security/safety behavior, timing/performance constraints, power intent, reset defaults, error behavior, DFT/testability assumptions, synthesis/PPA targets, and verification intent
3. Build a requirements ledger before writing YAML:
   - `decided`: concrete facts from user/files
   - `assumed`: conservative assumptions with rationale
   - `blocking_questions`: only items that prevent a correct SSOT
   - `deferred`: non-blocking future enhancements
4. Ask user only for blocking gaps. If locked truth exists, first derive missing SSOT validation fields from `requirements_index.json`, `obligations.json`, `contract_refs.json`, `structural_contracts.json`, `behavioral_contracts.json`, and `evidence_plan.json`; a missing YAML field is a projection gap, not automatically a missing truth gap. If a reasonable safe assumption is enough, record it in `custom.assumptions` instead of stopping.
5. Confirm the leaf IP boundary: what this SSOT owns, what is external, and which submodules are manifest-owned versus child SSOTs.
6. Do not write or modify canonical `req/*.json` authority files from ssot-gen. If locked truth is missing, stop with a lock/approval gap or proceed only as an unlocked draft when the user explicitly requested that.

## Phase 1B: Downstream RTL Feedback Enrichment

When the input contains `[SSOT TBD REPORT] -> ssot-gen`, switch from new-IP planning to targeted SSOT enrichment:

1. Parse each `Missing` row into `yaml_path`, `needed_for`, `question`, and `current_rtl_action`.
2. Read the existing `<ip>/yaml/<ip>.ssot.yaml` once and map each `yaml_path` to the smallest YAML section that must be patched.
3. Resolve each row from explicit user context, imported requirements/specs, existing SSOT facts, or approved Q&A answers. Do not infer RTL semantics from common IP patterns.
4. If a row cannot be resolved, create a section-scoped QA item with the original `question`; include `yaml_path`, `needed_for`, and the downstream RTL file/signal/task in metadata.
5. The edit plan must list:
   - `resolved_rows`: rows that will be patched now
   - `pending_qa_rows`: rows that remain pending user/SSOT answer
   - exact YAML fields to change
6. After patching, validate the SSOT and emit a refreshed `[SSOT HANDOFF]` to rtl-gen only when all requested rows are resolved or explicitly recorded as pending QA.

## Phase 2: Leaf YAML Authoring
1. Scaffold `<ip>/` if it does not exist
2. Write exactly one canonical leaf SSOT at `<ip>/yaml/<ip>.ssot.yaml`
3. Fill all production canonical sections, including required `function_model`, `cycle_model`, `timing`, `power`, `security`, `error_handling`, `debug_observability`, `integration`, `dft`, `synthesis`, and `quality_gates`
4. Express internal implementation hierarchy in `sub_modules`, but do not prescribe implementation code
5. Use `ownership: manifest` for internal blocks described by this YAML
6. Use `ownership: child_ssot` only for reusable or independently verified child IPs
7. Put enough detail in `features`, `dataflow`, `function_model`, `cycle_model`, `fsm`, `memory`, `registers`, `timing`, `power`, `security`, `error_handling`, `debug_observability`, `integration`, `dft`, `synthesis`, `pnr`, `test_requirements`, and `quality_gates` for downstream workflows to implement and verify without hidden tribal knowledge.
8. Avoid IP-specific fixed templates. The SSOT must describe behavior, interfaces, constraints, and acceptance criteria; downstream workflows generate implementation from those facts.
9. If locked truth exists, put authority metadata under `custom.locked_truth_authority` and put projection coverage under `traceability.locked_truth_projection`. Do not add a new top-level `authority:` key because the canonical top-level section set is fixed.
10. Attach `source_refs`, `contract_refs`, and where useful `evidence_refs` to important Design Spec items such as interfaces, register fields, function_model transactions, cycle_model rules, test scenarios, coverage bins, and quality gates. When `req/structural_contracts.json` exists, project its generic signals into `io_list` exactly: signal names, direction, width, clock/reset domain, and sync/async timing policy must match the structural contract. When `req/behavioral_contracts.json` exists, project its decision tables, transactions/state rules, and stage checks into `function_model`, `cycle_model`, `fsm`/register behavior, `test_requirements`, and `quality_gates`.
11. If the user explicitly wants to skip FL/CL and go directly to RTL, record that as SSOT policy under `quality_gates.rtl_gen.direct_rtl_allowed` with `approved: true` and a rationale. This policy skips executable model artifacts only; locked req contracts, SSOT Function/Cycle projection, and RTL evidence gates still apply.
12. When locked truth is silent about memory, FSM, child submodules, DFT, power, security, or another optional capability, write an explicit no-feature/external-owner/non-goal policy with source_refs instead of leaving TBD placeholders.

## Phase 3: Validation Gate
- Parse `<ip>/yaml/<ip>.ssot.yaml` as YAML
- Check the file is substantive, has the canonical sections, and has no live `<TBD>` markers unless the user explicitly left them
- Check every interface port has name, width, direction, and description
- Check every feature has trigger, datapath/control behavior, observable output, and reset/error expectations where applicable
- Check `function_model` defines cycle-independent state variables, transactions, preconditions, outputs, side effects, error cases, invariants, and scoreboard/reference-model guidance
- Check `cycle_model` defines clock/reset timing, latency bounds, handshake rules, pipeline stages, ordering/backpressure, and observability
- If locked behavioral contracts exist, check every `req/behavioral_contracts.json` ID is attached to a concrete `function_model` row with machine-readable semantics and a concrete `cycle_model` row with timing/protocol semantics, or has an explicit `cycle_model_waiver`; traceability lists alone are not enough
- When **all** locked behavioral contracts are cycle-waived/combinational (every contract is `cycle_model_waiver` or its locked decision table carries no clock/cycle/reset/handshake/state vocabulary), the IP is purely combinational: author **no** `fsm` block (no states/transitions), **no** `function_model.state_variables`, and **no** `function_model.transactions[*].state_updates`. Keep transactions purely combinational (decision_table when/then + output_rules). `verify_ssot` rejects a state-control FSM or architectural state for a combinational IP.
- Check timing, power, security, error_handling, debug_observability, integration, dft, and synthesis sections are explicit even when the answer is "not required" or "external owner"
- Check PnR/floorplan/route constraints and STA IO delay/exception/corner policies are explicit; downstream EDA workflows must not invent defaults
- Check every `test_requirements.scenarios[]` item has stimulus, expected result, and coverage/scoreboard intent
- Check `quality_gates` gives concrete pass criteria and evidence for SSOT, RTL, DV, coverage, EDA, and signoff
- Check every assumption that affects RTL behavior is recorded under `custom.assumptions`
- Run `python3 "$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py" <ip> --root "$ATLAS_PROJECT_ROOT" --mode engineering` or an equivalent YAML parse/structure check
- If locked truth exists, run `python3 "$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/check_design_spec_trace.py" <ip> --root "$ATLAS_PROJECT_ROOT"` and fix missing requirement/contract reflections before handoff
- Fix validation errors before handoff

## Phase 4: Handoff
- Output a compact `[SSOT HANDOFF]` block for rtl-gen
- Include IP name, SSOT path, locked truth authority status, top module, interfaces, parameters, memories, registers, sub_modules, function_model, cycle_model, timing/power/security/error/integration/DFT/synthesis assumptions, reset/clock, verification scenarios, quality gates, and known constraints
- Include a downstream definition of done:
  - fl-model-gen must write FunctionalModel, decomposition, coverage plan, and equivalence goals from SSOT only
  - rtl-gen must write RTL + filelist and compile with zero errors
  - tb-gen must write cocotb or SV TB, run simulation, emit coverage artifacts, and pass all SSOT scenarios
  - coverage must measure SSOT-declared coverage targets or emit precise gaps
  - syn/pnr/sta/sta-post must use only SSOT-declared EDA constraints and emit timing/physical evidence
  - sim_debug must inspect VCD/coverage and report waveform evidence or a precise handoff
  - EDA workflows must provide synthesis/STA/DFT evidence when quality_gates require it
- Do not claim RTL, lint, or sim passed unless a downstream workflow actually ran

## Phase 5: Completion
- Report exact files created/changed
- Report validation commands and results
- Tell the user rtl-gen is the next workflow
