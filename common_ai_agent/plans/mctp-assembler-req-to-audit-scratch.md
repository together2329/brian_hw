# MCTP Assembler Req-to-Audit Scratch Plan

## TL;DR
> **Summary**: Build a fresh `mctp_assembler_scratch` IP from the MCTP requirements, then drive it through the common_ai_agent SSOT -> FL/CL -> equivalence -> contract -> RTL -> TB -> sim -> coverage -> mutation -> signoff/audit flow. Existing `mctp_assembler/` artifacts are references only and must not be reused as evidence.
> **Deliverables**:
> - Fresh scratch IP directory: `mctp_assembler_scratch/`
> - Human-reviewable requirement approval artifact and source references
> - SSOT with executable FL/CL/equivalence/coverage/RTL/TB TODO contracts
> - RTL, cocotb/pyuvm TB, scoreboard, coverage, mutation, and signoff evidence
> - Final audit bundle proving no stale artifact contamination
> **Effort**: XL
> **Parallel**: YES - 5 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 3 -> Task 4 -> Task 5 -> Task 7 -> Task 9 -> Task 10 -> Task 12 -> Final Verification

## Context

### Original Request

The user asked for a `$omo:ulw-plan` for "SSOT to Audit", then corrected the scope:

```text
req 부터 scratch 구현이야
새로
doc/wiki workflow 참고해.
```

Interpretation: this is not a repair plan for the existing `mctp_assembler/` output. The work starts at requirements and creates a new scratch implementation while following the repo's documented common-engine workflow.

### Interview Summary

Confirmed MCTP IP requirements from the prior discussion:

- Input is AXI4 write ingress, `WDATA=256`, `WSTRB=32`.
- One AXI write transaction carries one PCIe VDM TLP.
- AXI write bursts may be multi-beat; `WLAST` terminates the TLP.
- MCTP transmission unit is programmable from 64 B through 4096 B and 4 B aligned.
- Non-final packets use the configured TU size; final/EOM packet may be shorter.
- Assembly supports interleaving by `{source_eid, tag_owner, message_tag}`.
- Each Q/context has an independent FSM and register-visible state.
- First and last 16 B TLP header snapshots are stored per completed message.
- SRAM interface is 256-bit; SRAM stores only MCTP message payload/body bytes.
- SRAM payload layout must have no alignment holes; each context preserves its own partial 32 B pack state.
- Firmware reads assembled payload through an AXI4 read path backed by the SRAM read interface.
- APB exposes Control, Status, Interrupt, Counter, Descriptor, and Debug registers.
- Packet drop and assembly drop conditions are required and counted by reason.
- Formal proof is optional future work and is excluded from first signoff closure.

### Metis Review (gaps addressed)

Metis found no contradictions but flagged scratch identity, stale evidence, source-reference copying, CL command ownership, contract stage inclusion, AXI read error policy, SRAM allocator policy, APB register map determinism, mutation threshold, and formal scope creep.

Resolved in this plan:

- New IP slug is fixed to `mctp_assembler_scratch`.
- Existing `mctp_assembler/` generated artifacts are reference/anti-pattern evidence only.
- Scratch `req/` must contain copied/derived requirements, source refs, and `approval_manifest.json`.
- CL is generated through `workflow/fl-model-gen/scripts/emit_cycle_model.py`.
- `derive_ip_contract` is required before TB/mutation/signoff.
- AXI read without completed descriptor returns `SLVERR` and zero data unless raw debug read is explicitly enabled.
- SRAM allocator is a deterministic linear bump allocator within `[sram_base, sram_limit)`, with descriptor-pop release deferred for first target.
- APB register offsets, reset values, access types, widths, and per-Q banks must be locked in SSOT.
- Mutation is required as an audit-depth artifact but advisory for local signoff unless a threshold is explicitly enforced.
- Formal proof appears only as a non-blocking future/wiki note.

## Work Objectives

### Core Objective

Create `mctp_assembler_scratch` from requirements and produce machine-checkable evidence that its SSOT, generated models, RTL, TB, simulation, coverage, mutation report, and signoff/audit artifacts are fresh and internally consistent.

### Deliverables

- `mctp_assembler_scratch/req/mctp_assembler_scratch_requirements.md`
- `mctp_assembler_scratch/req/source_references.md`
- `mctp_assembler_scratch/req/approval_manifest.json`
- `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml`
- `mctp_assembler_scratch/model/functional_model.py`
- `mctp_assembler_scratch/model/cycle_model.py`
- `mctp_assembler_scratch/model/fl_model_check.json`
- `mctp_assembler_scratch/model/cl_model_check.json`
- `mctp_assembler_scratch/verify/equivalence_goals.json`
- `mctp_assembler_scratch/verify/ip_contract.json`
- `mctp_assembler_scratch/rtl/*.sv`
- `mctp_assembler_scratch/list/mctp_assembler_scratch.f`
- `mctp_assembler_scratch/tb/cocotb/*`
- `mctp_assembler_scratch/sim/results.xml`
- `mctp_assembler_scratch/sim/scoreboard_events.jsonl`
- `mctp_assembler_scratch/cov/coverage.json`
- `mctp_assembler_scratch/mutation/mutation_report.json`
- `mctp_assembler_scratch/signoff/ip_signoff.json`
- `mctp_assembler_scratch/signoff/ip_signoff.md`

### Definition of Done

All commands below must pass from repo root unless explicitly noted:

```bash
test -d mctp_assembler_scratch
test ! -e mctp_assembler_scratch/sim/scoreboard_events.jsonl || jq empty mctp_assembler_scratch/signoff/ip_signoff.json
python3 workflow/ssot-gen/scripts/verify_ssot.py mctp_assembler_scratch --root . --mode signoff
python3 workflow/fl-model-gen/scripts/emit_fl_model.py mctp_assembler_scratch --root .
python3 workflow/fl-model-gen/scripts/emit_cycle_model.py mctp_assembler_scratch --root .
python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py mctp_assembler_scratch --root .
python3 workflow/ip-contract/scripts/derive_ip_contract.py mctp_assembler_scratch --root .
python3 workflow/tb-gen/scripts/check_tb_python_compile.py mctp_assembler_scratch --root .
python3 workflow/rtl-gen/scripts/rtl_compile_report.py mctp_assembler_scratch --root .
python3 workflow/lint/scripts/dut_lint_report.py mctp_assembler_scratch --root .
python3 mctp_assembler_scratch/tb/cocotb/test_runner.py
python3 workflow/tb-gen/scripts/check_scoreboard_events.py mctp_assembler_scratch --root . --source-check --require-events
python3 workflow/coverage/scripts/ssot_coverage_summary.py mctp_assembler_scratch --root .
python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32
python3 workflow/signoff/scripts/check_ip_signoff.py mctp_assembler_scratch --root .
```

Expected stop condition:

- `mctp_assembler_scratch/signoff/ip_signoff.json` exists and has `status`/`passed` equivalent indicating local evidence is complete, or it fails only on explicit human-production-signoff/waiver approval.
- No required evidence path under `mctp_assembler_scratch/` has a timestamp older than its authority artifact after the final implementation change.
- No final audit evidence is read from existing `mctp_assembler/`.

### Must Have

- Fresh scratch directory and evidence.
- Requirement approval manifest with SHA256 values.
- SSOT encodes exact byte/bit interpretation for accepted PCIe VDM/MCTP fields; no vague "per spec" behavior for machine-checked fields.
- SSOT declares APB register map with offsets, widths, reset values, access type, and per-Q banks.
- FL model is byte-accurate for AXI transaction to TLP to MCTP payload.
- CL model covers backpressure, context occupancy, SRAM write/read arbitration, and timeout.
- RTL filelist includes all implementation modules and no missing declared module.
- Scoreboard rows use `FunctionalModel.apply` results and equivalence goal IDs, not legacy scenario-only IDs.
- Coverage includes every `PD_*` and `AD_*` drop reason plus readback and register visibility.
- Mutation report includes category kill-rate summary; unsupported MCTP-specific categories are explicit follow-up obligations.

### Must NOT Have

- No reuse of `mctp_assembler/sim`, `mctp_assembler/cov`, `mctp_assembler/lint`, or `mctp_assembler/signoff` as proof for scratch.
- No manual edits to locked SSOT/FL/CL/coverage goals to make RTL pass.
- No hidden AXI ID support, multiple outstanding transactions, PCIe endpoint behavior, Flit Mode, ECRC checking, PnR/PPA signoff, or required formal proof in first closure.
- No static "profile" selection for monitors/mutations; obligations must derive from `io_list`, goals, and `ip_contract.json`.

## Verification Strategy

> ZERO HUMAN INTERVENTION for local checks. Human approval is represented by explicit artifacts, not prose.

- Test decision: TDD/RED-GREEN for production behavior changes. For generated-flow tasks, RED means the next required gate fails before the implementation for the expected reason; GREEN means the same gate passes after the implementation.
- QA policy: every task has at least one happy scenario and one failure/edge scenario with concrete commands.
- Evidence directory: use `evidence/mctp_assembler_scratch/` for command transcripts when commands do not already write machine-readable evidence.
- Manual/product QA channel: CLI/data-shaped tasks use `tmux` transcripts when a "real surface" scenario is needed:

```bash
tmux new-session -d -s ulw-qa-mctp-scratch '<command>'; tmux capture-pane -pt ulw-qa-mctp-scratch -S -2000; tmux kill-session -t ulw-qa-mctp-scratch
```

## Execution Strategy

### Parallel Execution Waves

Wave 1: Tasks 1-3. Requirement/source approval, scratch scaffold, SSOT authoring.

Wave 2: Tasks 4-6. FL/CL/equiv/ip-contract plus RTL architecture TODO derivation.

Wave 3: Tasks 7-9. RTL implementation, TB/scoreboard implementation, scenario suite.

Wave 4: Tasks 10-12. Simulation/debug, coverage, mutation.

Wave 5: Tasks 13-14 and Final Verification. Signoff/audit bundle and wiki handoff note.

### Dependency Matrix

| Task | Blocks | Blocked By |
| --- | --- | --- |
| 1 | 2, 3 | none |
| 2 | 3, 4 | 1 |
| 3 | 4, 5, 6 | 1, 2 |
| 4 | 5, 8 | 3 |
| 5 | 7, 8 | 4 |
| 6 | 7 | 3, 4 |
| 7 | 9, 10 | 5, 6 |
| 8 | 9, 10, 11 | 4, 5 |
| 9 | 10, 11 | 7, 8 |
| 10 | 11, 12 | 9 |
| 11 | 12 | 9, 10 |
| 12 | 13 | 9, 10, 11 |
| 13 | 14 | 12 |
| 14 | Final Verification | 13 |

## TODOs

- [x] 1. Create Fresh Scratch Requirement Package

  **What to do**: Create `mctp_assembler_scratch/req/` from the current MCTP requirement discussion. Copy or derive content from `mctp_assembler/req/mctp_assembler_requirements.md` and `mctp_assembler/req/source_references.md`, but update names and paths to the scratch IP. Create `mctp_assembler_scratch/req/approval_manifest.json` with SHA256 for requirement and source-reference files. Record that existing `mctp_assembler/` artifacts are not authority.

  **Must NOT do**: Do not copy any `yaml/`, `model/`, `rtl/`, `tb/`, `sim/`, `cov/`, `lint/`, or `signoff/` evidence from existing `mctp_assembler/`.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2,3 | Blocked By: none

  **References**:
  - Pattern: `doc/wiki/common-ai-agent-map.md` - authority stack starts with user-approved requirements.
  - Pattern: `doc/wiki/golden-todo-evidence.md` - requirement approval needs `req/approval_manifest.json`.
  - Source: `mctp_assembler/req/mctp_assembler_requirements.md` - MCTP user-approved discussion baseline.
  - Source: `mctp_assembler/req/source_references.md` - DSP0236/DSP0238 source reference record.

  **Acceptance Criteria**:
  - [ ] `mctp_assembler_scratch/req/mctp_assembler_scratch_requirements.md` exists and is over 10 KB.
  - [ ] `mctp_assembler_scratch/req/source_references.md` exists and points to `artifacts/local/standards/DSP0236_1.3.3.pdf` and `artifacts/local/standards/DSP0238_1.4.0.pdf`.
  - [ ] `mctp_assembler_scratch/req/approval_manifest.json` exists, parses as JSON, and contains SHA256 values for both req docs.
  - [ ] `find mctp_assembler_scratch -maxdepth 2 -type f` shows only fresh `req/` files at this step.

  **QA Scenarios**:
  ```text
  Scenario: Fresh req package exists
    Tool: bash
    Steps: test -f mctp_assembler_scratch/req/mctp_assembler_scratch_requirements.md && jq empty mctp_assembler_scratch/req/approval_manifest.json
    Expected: exit 0
    Evidence: evidence/mctp_assembler_scratch/task-1-req-package.txt

  Scenario: Stale artifact contamination blocked
    Tool: bash
    Steps: find mctp_assembler_scratch -path '*/sim/*' -o -path '*/rtl/*' -o -path '*/tb/*'
    Expected: no output before SSOT/implementation tasks create fresh artifacts
    Evidence: evidence/mctp_assembler_scratch/task-1-no-stale-artifacts.txt
  ```

  **Commit**: YES | Message: `docs(mctp): seed scratch assembler requirements` | Files: `mctp_assembler_scratch/req/*`

- [x] 2. Lock Executable Requirement Decisions

  **What to do**: Convert non-executable wording into locked first-target decisions inside the scratch requirement file. Use these exact defaults: no AXI IDs, no multiple outstanding AXI read/write, AXI read no-descriptor returns zero data with `RRESP=SLVERR` unless raw debug read is enabled, SRAM allocator is linear bump from `sram_base` to `sram_limit`, descriptor-pop does not reclaim space in first target, SRAM write priority over firmware read, formal proof optional.

  **Must NOT do**: Do not leave "integration-policy dependent" in first-target behavior unless it is explicitly a human gate and excluded from signoff.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 3,4 | Blocked By: 1

  **References**:
  - Source: `mctp_assembler/req/mctp_assembler_requirements.md` - current detailed MCTP behavior.
  - Pattern: `workflow/COMMON_ENGINE_FLOW.md` - human-owned semantic choices must be locked before downstream loops.

  **Acceptance Criteria**:
  - [ ] Requirement file contains the first-target defaults listed above.
  - [ ] Requirement file contains no `TBD`, `TODO`, or `integration-policy dependent` text for signoff behavior.
  - [ ] Approval manifest is refreshed after requirement edits.

  **QA Scenarios**:
  ```text
  Scenario: No unresolved requirement placeholders
    Tool: bash
    Steps: "! rg -n 'TBD|TODO|integration-policy dependent' mctp_assembler_scratch/req/mctp_assembler_scratch_requirements.md"
    Expected: exit 0
    Evidence: evidence/mctp_assembler_scratch/task-2-no-placeholders.txt

  Scenario: Defaults are present
    Tool: bash
    Steps: rg -n 'no AXI IDs|linear bump|SLVERR|formal proof optional' mctp_assembler_scratch/req/mctp_assembler_scratch_requirements.md
    Expected: all four concepts found
    Evidence: evidence/mctp_assembler_scratch/task-2-defaults.txt
  ```

  **Commit**: YES | Message: `docs(mctp): lock scratch assembler first-target decisions` | Files: `mctp_assembler_scratch/req/*`

- [x] 3. Author Scratch SSOT and Schema Gate

  **What to do**: Create `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml` from the approved req using the SSOT template and common-engine rules. Encode exact interfaces, parameters, APB register map, per-Q banks, state variables, drop IDs, SRAM packing rules, AXI read/write behavior, FL transactions, CL pipeline, coverage bins, workflow TODOs, and signoff criteria. Then run repair/verify scripts.

  **Must NOT do**: Do not paste the existing `mctp_assembler/yaml/mctp_assembler.ssot.yaml` as the new SSOT. It may be read for structure only.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 4,5,6 | Blocked By: 1,2

  **References**:
  - Pattern: `workflow/ssot-gen/rules/ssot-template.yaml` - canonical SSOT structure.
  - Pattern: `workflow/COMMON_ENGINE_FLOW.md` - SSOT owns downstream TODOs.
  - Pattern: `doc/wiki/workflow-ownership-and-boundaries.md` - SSOT is `ssot-gen` owned.
  - Command: `workflow/ssot-gen/scripts/verify_ssot.py`

  **Acceptance Criteria**:
  - [ ] `python3 workflow/ssot-gen/scripts/repair_ssot_schema.py mctp_assembler_scratch --root . --mode signoff` exits 0.
  - [ ] `python3 workflow/ssot-gen/scripts/verify_ssot.py mctp_assembler_scratch --root . --mode signoff` exits 0.
  - [ ] `mctp_assembler_scratch/req/ssot_validation.json` reports no blockers.
  - [ ] SSOT contains no repair/scaffold markers like `replace before signoff`, `expr: 0`, or `expr: 1` unless the expression is semantically justified in a named reset/default rule.

  **QA Scenarios**:
  ```text
  Scenario: SSOT validates in signoff mode
    Tool: bash
    Steps: python3 workflow/ssot-gen/scripts/verify_ssot.py mctp_assembler_scratch --root . --mode signoff
    Expected: PASS with zero blockers
    Evidence: mctp_assembler_scratch/req/ssot_validation.json

  Scenario: No scaffold markers remain
    Tool: bash
    Steps: "! rg -n 'replace before signoff|Repair marker|Auto-injected benign|Auto-injected transaction' mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml"
    Expected: exit 0
    Evidence: evidence/mctp_assembler_scratch/task-3-no-scaffold.txt
  ```

  **Commit**: YES | Message: `feat(mctp): author scratch assembler ssot` | Files: `mctp_assembler_scratch/yaml/*`, `mctp_assembler_scratch/req/ssot_validation.json`

- [x] 4. Generate FL, CL, Equivalence Goals, and IP Contract

  **What to do**: Generate deterministic FL and CL models from SSOT, then generate equivalence goals and derive the per-IP contract. Ensure the FL model exposes transactions for AXI TLP ingest, VDM parse, MCTP parse, context allocate/append/complete/drop, SRAM pack/write, descriptor publish, APB access, and AXI readback.

  **Must NOT do**: Do not hand-edit FL/CL to match RTL. If generated FL/CL is wrong, repair SSOT and regenerate.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 5,8 | Blocked By: 3

  **References**:
  - Command: `workflow/fl-model-gen/scripts/emit_fl_model.py`
  - Command: `workflow/fl-model-gen/scripts/emit_cycle_model.py`
  - Command: `workflow/fl-model-gen/scripts/emit_equivalence_goals.py`
  - Command: `workflow/ip-contract/scripts/derive_ip_contract.py`
  - Pattern: `doc/wiki/common-ai-agent-map.md` - FL/CL derive from SSOT.

  **Acceptance Criteria**:
  - [ ] `python3 workflow/fl-model-gen/scripts/emit_fl_model.py mctp_assembler_scratch --root .` exits 0.
  - [ ] `python3 workflow/fl-model-gen/scripts/emit_cycle_model.py mctp_assembler_scratch --root .` exits 0.
  - [ ] `python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py mctp_assembler_scratch --root .` exits 0.
  - [ ] `python3 workflow/ip-contract/scripts/derive_ip_contract.py mctp_assembler_scratch --root .` exits 0.
  - [ ] `model/fl_model_check.json`, `model/cl_model_check.json`, `verify/equivalence_goals.json`, and `verify/ip_contract.json` exist and parse.

  **QA Scenarios**:
  ```text
  Scenario: Model generation chain passes
    Tool: bash
    Steps: python3 workflow/fl-model-gen/scripts/emit_fl_model.py mctp_assembler_scratch --root . && python3 workflow/fl-model-gen/scripts/emit_cycle_model.py mctp_assembler_scratch --root . && python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py mctp_assembler_scratch --root . && python3 workflow/ip-contract/scripts/derive_ip_contract.py mctp_assembler_scratch --root .
    Expected: exit 0 and required JSON files exist
    Evidence: evidence/mctp_assembler_scratch/task-4-model-chain.txt

  Scenario: Contract includes AXI/APB/SRAM capabilities
    Tool: bash
    Steps: rg -n 'axi|apb|sram|packet|ready_valid|bus_transaction' mctp_assembler_scratch/verify/ip_contract.json
    Expected: relevant capability/evidence obligations found
    Evidence: evidence/mctp_assembler_scratch/task-4-contract-capabilities.txt
  ```

  **Commit**: YES | Message: `build(mctp): generate scratch assembler model contracts` | Files: `mctp_assembler_scratch/model/*`, `mctp_assembler_scratch/verify/*`, `mctp_assembler_scratch/cov/fcov_plan.json`

- [x] 5. Define RTL Architecture TODOs from SSOT

  **What to do**: Run RTL TODO derivation and verify the implementation list is complete before coding. Required module ownership:
  `mctp_assembler_scratch.sv`, `mctp_assembler_scratch_axi_write_ingress.sv`, `mctp_assembler_scratch_pcie_vdm_parser.sv`, `mctp_assembler_scratch_mctp_parser.sv`, `mctp_assembler_scratch_context_table.sv`, `mctp_assembler_scratch_sram_packer.sv`, `mctp_assembler_scratch_axi_read_egress.sv`, `mctp_assembler_scratch_sram_arbiter.sv`, `mctp_assembler_scratch_descriptor_queue.sv`, `mctp_assembler_scratch_apb_regfile.sv`, `mctp_assembler_scratch_cdc.sv`, and `mctp_assembler_scratch_param.vh`.

  **Must NOT do**: Do not omit `axi_read_egress` or collapse per-Q visibility into a selected-debug-only mirror.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 7,8 | Blocked By: 4

  **References**:
  - Command: `workflow/rtl-gen/scripts/derive_rtl_todos.py`
  - Pattern: `workflow/rtl-gen/rules/ssot-rtl-orchestration.md`
  - Pattern: `workflow/COMMON_ENGINE_FLOW.md` - RTL-gen derives TODOs from SSOT.

  **Acceptance Criteria**:
  - [ ] `python3 workflow/rtl-gen/scripts/derive_rtl_todos.py mctp_assembler_scratch --root .` exits 0.
  - [ ] `mctp_assembler_scratch/rtl/rtl_todo_plan.json` exists and includes every module above.
  - [ ] TODOs include top ports, APB map, per-Q registers, SRAM read/write, descriptor queue, and drop counters.

  **QA Scenarios**:
  ```text
  Scenario: RTL TODO plan derives from SSOT
    Tool: bash
    Steps: python3 workflow/rtl-gen/scripts/derive_rtl_todos.py mctp_assembler_scratch --root .
    Expected: exit 0
    Evidence: mctp_assembler_scratch/rtl/rtl_todo_plan.json

  Scenario: Required RTL module names present
    Tool: bash
    Steps: rg -n 'axi_read_egress|sram_arbiter|descriptor_queue|context_table|apb_regfile' mctp_assembler_scratch/rtl/rtl_todo_plan.json
    Expected: all required module obligations found
    Evidence: evidence/mctp_assembler_scratch/task-5-rtl-module-todos.txt
  ```

  **Commit**: YES | Message: `build(mctp): derive scratch assembler rtl todos` | Files: `mctp_assembler_scratch/rtl/rtl_todo_plan.json`

- [x] 6. Implement RTL Through RTL-Gen Ownership

  **What to do**: Implement RTL against the derived TODOs. Use the SSOT as binding authority. Implement AXI write burst collection, PCIe VDM/MCTP parsing, per-context FSM, per-context 32 B SRAM pack state, descriptor queue, AXI read SRAM bridge, APB register file, counters/interrupts, and CDC. Update `list/mctp_assembler_scratch.f`.

  **Must NOT do**: Do not edit SSOT/FL/CL/coverage goals to fit RTL. Do not manually copy existing `mctp_assembler/rtl` without reconciling against scratch SSOT.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 9,10 | Blocked By: 5

  **References**:
  - Pattern: `doc/wiki/workflow-ownership-and-boundaries.md` - RTL artifacts are `rtl-gen` owned.
  - Pattern: `mctp_assembler/rtl/` - prior attempt is reference only; use for naming lessons, not evidence.
  - Command: `workflow/rtl-gen/scripts/rtl_compile_report.py`
  - Command: `workflow/lint/scripts/dut_lint_report.py`

  **Acceptance Criteria**:
  - [ ] `python3 workflow/rtl-gen/scripts/rtl_compile_report.py mctp_assembler_scratch --root .` exits 0 and `rtl/rtl_compile.json` passes.
  - [ ] `python3 workflow/lint/scripts/dut_lint_report.py mctp_assembler_scratch --root .` exits 0 and `lint/dut_lint.json` passes with zero unwaived warnings/errors.
  - [ ] `list/mctp_assembler_scratch.f` includes every required RTL module exactly once.
  - [ ] Top module includes AXI write, AXI read, APB, SRAM read/write, interrupt, clock, and reset ports from SSOT.

  **QA Scenarios**:
  ```text
  Scenario: DUT-only compile passes
    Tool: bash
    Steps: python3 workflow/rtl-gen/scripts/rtl_compile_report.py mctp_assembler_scratch --root .
    Expected: rtl_compile.json has passed=true
    Evidence: mctp_assembler_scratch/rtl/rtl_compile.json

  Scenario: DUT-only lint passes
    Tool: bash
    Steps: python3 workflow/lint/scripts/dut_lint_report.py mctp_assembler_scratch --root .
    Expected: dut_lint.json has passed=true and zero unwaived diagnostics
    Evidence: mctp_assembler_scratch/lint/dut_lint.json
  ```

  **Commit**: YES | Message: `feat(mctp): implement scratch assembler rtl` | Files: `mctp_assembler_scratch/rtl/*`, `mctp_assembler_scratch/list/*`, `mctp_assembler_scratch/lint/*`

- [x] 7. Generate TB, Monitors, and Scoreboard Contract

  **What to do**: Generate or implement cocotb/pyuvm TB from equivalence goals and `ip_contract.json`. Required agents/monitors: AXI write driver, AXI read driver, APB agent, SRAM model, descriptor observer, per-Q register observer, SRAM write/read monitor, interrupt/counter monitor. Scoreboard must call `FunctionalModel.apply` and emit goal IDs from `verify/equivalence_goals.json`.

  **Must NOT do**: Do not emit legacy scenario IDs as primary `goal_id`. Do not write scoreboard expected values by hand when FL can compute them.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 9,10,11 | Blocked By: 4,5

  **References**:
  - Command: `workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py`
  - Command: `workflow/tb-gen/scripts/check_tb_python_compile.py`
  - Command: `workflow/tb-gen/scripts/check_scoreboard_events.py`
  - Pattern: `mctp_assembler/tb/cocotb/` - prior TB shows useful structure but stale scoreboard contract.

  **Acceptance Criteria**:
  - [ ] `python3 workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py mctp_assembler_scratch --root .` exits 0.
  - [ ] `python3 workflow/tb-gen/scripts/check_tb_python_compile.py mctp_assembler_scratch --root .` exits 0.
  - [ ] `tb/cocotb/tb_manifest.json` references only `mctp_assembler_scratch` paths.
  - [ ] `tb/cocotb/scoreboard.py` or equivalent imports the scratch FL model.

  **QA Scenarios**:
  ```text
  Scenario: TB Python compiles
    Tool: bash
    Steps: python3 workflow/tb-gen/scripts/check_tb_python_compile.py mctp_assembler_scratch --root .
    Expected: tb_py_compile.json has passed=true
    Evidence: mctp_assembler_scratch/tb/cocotb/tb_py_compile.json

  Scenario: TB manifest has no stale IP paths
    Tool: bash
    Steps: "! rg -n 'mctp_assembler/' mctp_assembler_scratch/tb/cocotb/tb_manifest.json"
    Expected: exit 0
    Evidence: evidence/mctp_assembler_scratch/task-7-no-stale-manifest.txt
  ```

  **Commit**: YES | Message: `test(mctp): generate scratch assembler cocotb harness` | Files: `mctp_assembler_scratch/tb/*`, `mctp_assembler_scratch/tc/*`

- [x] 8. Add Directed Scenario Suite from Requirements

  **What to do**: Add directed scenarios before final RTL debugging. Required scenario IDs: `SC_VALID_SINGLE_PACKET`, `SC_MULTI_FRAGMENT_TU64`, `SC_MAX_TU_4096_129_BEATS`, `SC_INTERLEAVE_TWO_KEYS`, `SC_UNALIGNED_SRAM_PACK_NO_HOLES`, `SC_FIRST_LAST_TLP_HEADERS`, `SC_AXI_READBACK_TRIM`, `SC_APB_REGS_PER_Q`, all packet drops `PD_DISABLED_DROP_MODE`, `PD_MALFORMED_TLP`, `PD_UNSUPPORTED_VDM`, `PD_BAD_MCTP_HEADER`, `PD_BAD_PAD_OR_ALIGNMENT`, `PD_DEST_EID_REJECT`, `PD_UNEXPECTED_MIDDLE_END`, `PD_BAD_OR_EXPIRED_TAG`, and all assembly drops `AD_DUPLICATE_SOM`, `AD_SEQUENCE_MISMATCH`, `AD_MESSAGE_OVERFLOW`, `AD_SRAM_OVERFLOW`, `AD_DESCRIPTOR_FULL`, `AD_TIMEOUT`.

  **Must NOT do**: Do not count a coverage bin hit unless a passing scoreboard row includes real `rtl_observed` data.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 9,10,11 | Blocked By: 4,7

  **References**:
  - Source: `mctp_assembler/req/mctp_assembler_requirements.md` - required drop/error scenarios.
  - Pattern: `doc/wiki/golden-todo-evidence.md` - evidence required for TODO approval.

  **Acceptance Criteria**:
  - [ ] Scenario source file exists under `mctp_assembler_scratch/tc/`.
  - [ ] Every required scenario ID appears in `verify/equivalence_goals.json`, TB scenario list, or coverage plan.
  - [ ] Negative scenarios assert no SRAM payload write and correct counters/drop reason.

  **QA Scenarios**:
  ```text
  Scenario: All required scenario IDs are declared
    Tool: bash
    Steps: rg -n 'SC_VALID_SINGLE_PACKET|SC_MULTI_FRAGMENT_TU64|SC_MAX_TU_4096_129_BEATS|PD_MALFORMED_TLP|AD_TIMEOUT' mctp_assembler_scratch
    Expected: all representative IDs found
    Evidence: evidence/mctp_assembler_scratch/task-8-scenario-ids.txt

  Scenario: Negative drop scenarios include no-write checks
    Tool: bash
    Steps: rg -n 'no_sram_write|sram_write_count.*0|payload_bytes_written.*0' mctp_assembler_scratch/tb mctp_assembler_scratch/tc
    Expected: no-write assertions found for drop cases
    Evidence: evidence/mctp_assembler_scratch/task-8-drop-no-write.txt
  ```

  **Commit**: YES | Message: `test(mctp): cover assembler drop and readback scenarios` | Files: `mctp_assembler_scratch/tb/*`, `mctp_assembler_scratch/tc/*`, `mctp_assembler_scratch/verify/*`

- [x] 9. Run Simulation and Scoreboard Schema Gate

  **What to do**: Run the real cocotb simulation from the scratch TB runner. Then validate scoreboard schema with `--source-check --require-events`. If failures classify owner first: RTL mismatch -> rtl-gen, TB observation gap -> tb-gen, FL/SSOT ambiguity -> human/ssot-gen.

  **Must NOT do**: Do not edit `scoreboard_events.jsonl`, `results.xml`, or sim logs by hand.

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: 10,11,12 | Blocked By: 6,7,8

  **References**:
  - Command: `python3 mctp_assembler_scratch/tb/cocotb/test_runner.py`
  - Command: `workflow/tb-gen/scripts/check_scoreboard_events.py`
  - Pattern: `workflow/COMMON_ENGINE_FLOW.md` - owner classification before repair.

  **Acceptance Criteria**:
  - [ ] `python3 mctp_assembler_scratch/tb/cocotb/test_runner.py` exits 0.
  - [ ] `sim/results.xml` has zero failures/errors.
  - [ ] `sim/scoreboard_events.jsonl` exists and includes required goal IDs.
  - [ ] `python3 workflow/tb-gen/scripts/check_scoreboard_events.py mctp_assembler_scratch --root . --source-check --require-events` exits 0.

  **QA Scenarios**:
  ```text
  Scenario: Simulation passes through real cocotb runner
    Tool: tmux
    Steps: tmux new-session -d -s ulw-qa-mctp-sim 'cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 mctp_assembler_scratch/tb/cocotb/test_runner.py'; tmux capture-pane -pt ulw-qa-mctp-sim -S -2000
    Expected: runner exits 0 and results.xml has zero failures/errors
    Evidence: evidence/mctp_assembler_scratch/task-9-sim-tmux.txt

  Scenario: Scoreboard rejects stale/handwritten rows
    Tool: bash
    Steps: python3 workflow/tb-gen/scripts/check_scoreboard_events.py mctp_assembler_scratch --root . --source-check --require-events
    Expected: exit 0; any legacy scenario-only goal IDs fail before repair and pass after repair
    Evidence: evidence/mctp_assembler_scratch/task-9-scoreboard-schema.txt
  ```

  **Commit**: YES | Message: `test(mctp): pass scratch assembler simulation scoreboard` | Files: `mctp_assembler_scratch/sim/*`, `mctp_assembler_scratch/tb/*`, owner-routed RTL/TB fixes

- [x] 10. Close Functional and Cycle Coverage

  **What to do**: Build coverage from passing scoreboard evidence. Ensure `coverage.json` includes functional bins, cycle/backpressure bins, drop bins, AXI read bins, APB/per-Q visibility bins, SRAM no-hole bins, and interleaving bins.

  **Must NOT do**: Do not lower SSOT coverage goals. Add stimulus or fix monitors instead.

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: 11,12 | Blocked By: 9

  **References**:
  - Command: `workflow/coverage/scripts/ssot_coverage_summary.py`
  - Pattern: `workflow/coverage/rules/README.md`

  **Acceptance Criteria**:
  - [ ] `python3 workflow/coverage/scripts/ssot_coverage_summary.py mctp_assembler_scratch --root .` exits 0.
  - [ ] `cov/coverage.json` exists.
  - [ ] Coverage report shows all required bins hit by passing scoreboard rows.
  - [ ] Missed bins are either zero or owner-routed with explicit non-signoff status.

  **QA Scenarios**:
  ```text
  Scenario: Coverage summary is generated
    Tool: bash
    Steps: python3 workflow/coverage/scripts/ssot_coverage_summary.py mctp_assembler_scratch --root .
    Expected: cov/coverage.json exists and parses
    Evidence: mctp_assembler_scratch/cov/coverage.json

  Scenario: Drop and AXI read bins are covered
    Tool: bash
    Steps: rg -n 'PD_MALFORMED_TLP|AD_SEQUENCE_MISMATCH|AXI_READBACK|SRAM_PACK_NO_HOLES|INTERLEAVE' mctp_assembler_scratch/cov/coverage.json
    Expected: all representative bins present and hit
    Evidence: evidence/mctp_assembler_scratch/task-10-coverage-bins.txt
  ```

  **Commit**: YES | Message: `test(mctp): close scratch assembler coverage` | Files: `mctp_assembler_scratch/cov/*`, any owner-routed TB stimulus fixes

- [x] 11. Run Sim-Debug Goal Audit and Mismatch Classification

  **What to do**: Run FL-vs-RTL goal audit/debug. Produce `sim/fl_rtl_compare.json`, `sim/mismatch_classification.json`, and `sim/fl_rtl_goal_audit.json` if the workflow supports all three. Classify any mismatch owner before repair.

  **Must NOT do**: Do not mark semantic mismatches waived without a human-review artifact.

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: 12,13 | Blocked By: 9,10

  **References**:
  - Command: `workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py`
  - Pattern: `workflow/COMMON_ENGINE_FLOW.md` - sim-debug owner classification.

  **Acceptance Criteria**:
  - [ ] `python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py mctp_assembler_scratch --root .` exits 0 or fails only with explicit owner-classified blockers.
  - [ ] `sim/fl_rtl_goal_audit.json` reports all local machine checks pass, excluding final human production signoff if applicable.
  - [ ] No unresolved `llm_loop_allowed` mismatch remains.

  **QA Scenarios**:
  ```text
  Scenario: Goal audit consumes fresh scratch evidence
    Tool: bash
    Steps: python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py mctp_assembler_scratch --root .
    Expected: audit status pass or only human-production gate remains
    Evidence: mctp_assembler_scratch/sim/fl_rtl_goal_audit.json

  Scenario: No stale path in audit
    Tool: bash
    Steps: "! rg -n 'mctp_assembler/' mctp_assembler_scratch/sim/fl_rtl_goal_audit.json"
    Expected: exit 0
    Evidence: evidence/mctp_assembler_scratch/task-11-no-stale-audit-path.txt
  ```

  **Commit**: YES | Message: `test(mctp): pass scratch assembler goal audit` | Files: `mctp_assembler_scratch/sim/*`

- [x] 12. Run Mutation Guard with Category Reporting

  **What to do**: Run mutation guard list-only first, then `--max-mutants 32`. Ensure report includes per-category kill-rate summary. For unsupported MCTP-specific categories, record explicit follow-up obligations rather than hiding them. Do not make mutation proof a functional correctness proof.

  **Must NOT do**: Do not mutate FL/SSOT/coverage goals. Do not claim exhaustive proof from 32 sampled mutants.

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: 13 | Blocked By: 9,10,11

  **References**:
  - Command: `workflow/mutation/scripts/mutation_guard.py`
  - Pattern: `workflow/mutation/README.md` - mutation is advisory depth signal by default.

  **Acceptance Criteria**:
  - [ ] `python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --list-only` exits 0.
  - [ ] `python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32` exits 0 or reports survived mutants with explicit harness-gap classification.
  - [ ] `mutation/mutation_report.json` and `.md` exist.
  - [ ] Report contains category kill-rate lines such as operator/comparator/handshake/state/control categories, where supported.

  **QA Scenarios**:
  ```text
  Scenario: Mutation list-only explains selected categories
    Tool: bash
    Steps: python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --list-only
    Expected: supported and unsupported obligations listed
    Evidence: evidence/mctp_assembler_scratch/task-12-mutation-list.txt

  Scenario: Mutation sample runs
    Tool: tmux
    Steps: tmux new-session -d -s ulw-qa-mctp-mut 'cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent && python3 workflow/mutation/scripts/mutation_guard.py mctp_assembler_scratch --root . --max-mutants 32'; tmux capture-pane -pt ulw-qa-mctp-mut -S -2000
    Expected: mutation_report.json produced; survived mutants classified
    Evidence: mctp_assembler_scratch/mutation/mutation_report.json
  ```

  **Commit**: YES | Message: `test(mctp): record scratch assembler mutation depth` | Files: `mctp_assembler_scratch/mutation/*`, any owner-routed TB improvements

- [ ] 13. Run Local Signoff

  **What to do**: Run final signoff against `IP_SIGNOFF.md` and `ip_contract.json`. If signoff fails, classify every blocker by owner and repair only through the owner workflow. Generate or refresh `signoff/goal_ledger.json` if required by the signoff script.

  **Must NOT do**: Do not waive missing evidence or treat mutation as required production proof unless the threshold policy was explicitly enabled.

  **Parallelization**: Can Parallel: NO | Wave 5 | Blocks: 14 | Blocked By: 12

  **References**:
  - Command: `workflow/signoff/scripts/check_ip_signoff.py`
  - Policy: `IP_SIGNOFF.md`
  - Pattern: `workflow/signoff/README.md`

  **Acceptance Criteria**:
  - [ ] `python3 workflow/signoff/scripts/check_ip_signoff.py mctp_assembler_scratch --root .` exits 0 or fails only on explicit human-production-signoff.
  - [ ] `signoff/ip_signoff.json` and `signoff/ip_signoff.md` exist.
  - [ ] Signoff report includes SSOT, FL, CL, equivalence goals, ip_contract, RTL compile, lint, TB compile, sim, scoreboard schema, coverage, mutation if present, and goal audit.

  **QA Scenarios**:
  ```text
  Scenario: Local signoff passes
    Tool: bash
    Steps: python3 workflow/signoff/scripts/check_ip_signoff.py mctp_assembler_scratch --root .
    Expected: exit 0 or only final human-production gate remains
    Evidence: mctp_assembler_scratch/signoff/ip_signoff.json

  Scenario: Signoff does not read old IP evidence
    Tool: bash
    Steps: "! rg -n 'mctp_assembler/' mctp_assembler_scratch/signoff/ip_signoff.json mctp_assembler_scratch/signoff/ip_signoff.md"
    Expected: exit 0
    Evidence: evidence/mctp_assembler_scratch/task-13-no-stale-signoff.txt
  ```

  **Commit**: YES | Message: `test(mctp): sign off scratch assembler locally` | Files: `mctp_assembler_scratch/signoff/*`, owner-routed evidence fixes

- [ ] 14. Record Wiki Handoff and Lessons

  **What to do**: Add a concise wiki page after local signoff summarizing the scratch MCTP flow, key decisions, commands, artifacts, mutation interpretation, and remaining non-blocking future work such as formal proof and PPA. Link it from `doc/wiki/index.md`.

  **Must NOT do**: Do not claim production conformance or formal proof. Do not duplicate long signoff JSON in the wiki.

  **Parallelization**: Can Parallel: NO | Wave 5 | Blocks: Final Verification | Blocked By: 13

  **References**:
  - Pattern: `doc/wiki/wiki-curation-policy.md` - update wiki when a workflow lesson is reusable.
  - Pattern: `doc/wiki/index.md` - fast context link map.
  - Command: `python3 workflow/wiki/build_graph.py --check`

  **Acceptance Criteria**:
  - [ ] `doc/wiki/mctp-assembler-scratch-flow-YYYYMMDD.md` exists.
  - [ ] `doc/wiki/index.md` links the page.
  - [ ] `python3 workflow/wiki/build_graph.py --check` exits 0.

  **QA Scenarios**:
  ```text
  Scenario: Wiki graph validates
    Tool: bash
    Steps: python3 workflow/wiki/build_graph.py --check
    Expected: exit 0
    Evidence: evidence/mctp_assembler_scratch/task-14-wiki-graph.txt

  Scenario: Wiki does not overclaim
    Tool: bash
    Steps: "! rg -n 'formal proof complete|DMTF conformance certified|PPA signoff complete' doc/wiki/mctp-assembler-scratch-flow-*.md"
    Expected: exit 0
    Evidence: evidence/mctp_assembler_scratch/task-14-no-overclaim.txt
  ```

  **Commit**: YES | Message: `docs(mctp): record scratch assembler audit flow` | Files: `doc/wiki/*`, `evidence/mctp_assembler_scratch/*`

## Final Verification Wave

> ALL must approve or produce owner-classified blockers. Present consolidated results to user before claiming completion.

- [ ] F1. Plan Compliance Audit
  - Command: `rg -n 'mctp_assembler_scratch|approval_manifest|verify_ssot|emit_fl_model|emit_cycle_model|derive_ip_contract|mutation_guard|check_ip_signoff' plans/mctp-assembler-req-to-audit-scratch.md`
  - Expected: all required terms found.

- [ ] F2. Evidence Freshness Audit
  - Command: `find mctp_assembler_scratch -maxdepth 3 -type f | sort`
  - Expected: only fresh scratch files appear; no proof path comes from `mctp_assembler/`.

- [ ] F3. Full Local Gate Replay
  - Command: run the Definition of Done command block sequentially.
  - Expected: all local evidence gates pass or only explicit human-production gate remains.

- [ ] F4. Scope Fidelity Check
  - Command: `rg -n 'Flit Mode|ECRC checking|formal proof complete|PnR|DMTF conformance certified' mctp_assembler_scratch doc/wiki/mctp-assembler-scratch-flow-*.md`
  - Expected: these are absent or marked out-of-scope/future, not completed.

## Commit Strategy

- Commit 1: requirements and approval artifacts.
- Commit 2: SSOT and validation.
- Commit 3: FL/CL/equivalence/ip-contract.
- Commit 4: RTL implementation and compile/lint.
- Commit 5: TB/scenarios/scoreboard.
- Commit 6: sim/coverage/mutation/signoff evidence.
- Commit 7: wiki handoff.

Do not auto-commit unless explicitly requested. If committing later, use the repo's Lore protocol where required by `AGENTS.md`, or conventional commit format if the active execution mode requires it.

## Success Criteria

- Fresh scratch IP exists under `mctp_assembler_scratch/`.
- Requirement approval is represented by `req/approval_manifest.json`.
- SSOT validates in signoff mode with no blockers.
- FL/CL/equivalence/ip-contract artifacts exist and pass self-checks.
- RTL compiles and lints cleanly.
- TB compiles, sim passes, and scoreboard rows satisfy equivalence goals.
- Coverage closes against RTL-observed scoreboard evidence.
- Mutation guard runs and reports category kill-rate/advisory gaps.
- Goal audit/signoff artifacts exist and do not depend on stale `mctp_assembler/` evidence.
- Wiki handoff records the workflow and avoids overclaiming formal/PPA/DMTF conformance.
