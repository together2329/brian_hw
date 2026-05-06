# SSOT Generation Plan

You are planning a leaf IP YAML SSOT generation project.

The ssot-gen workflow owns the SSOT contract only. It must not generate
production RTL, testbenches, or simulations. Those are downstream rtl-gen,
tb-gen, and sim workflow responsibilities.

## Phase 1: Requirements Gathering
1. Read any existing requirement files in the current directory
2. Extract IP name, top-level type, purpose, clock/reset, interfaces, parameters, memories, registers, interrupts, function behavior, cycle/latency behavior, debug visibility, security/safety behavior, timing/performance constraints, power intent, reset defaults, error behavior, DFT/testability assumptions, synthesis/PPA targets, and verification intent
3. Build a requirements ledger before writing YAML:
   - `decided`: concrete facts from user/files
   - `assumed`: conservative assumptions with rationale
   - `blocking_questions`: only items that prevent a correct SSOT
   - `deferred`: non-blocking future enhancements
4. Ask user only for blocking gaps. If a reasonable safe assumption is enough, record it in `custom.assumptions` instead of stopping.
5. Confirm the leaf IP boundary: what this SSOT owns, what is external, and which submodules are manifest-owned versus child SSOTs.

## Phase 2: Leaf YAML Authoring
1. Scaffold `<ip>/` if it does not exist
2. Write exactly one canonical leaf SSOT at `<ip>/yaml/<ip>.ssot.yaml`
3. Fill all production canonical sections, including required `function_model`, `cycle_model`, `timing`, `power`, `security`, `error_handling`, `debug_observability`, `integration`, `dft`, `synthesis`, and `quality_gates`
4. Express internal implementation hierarchy in `sub_modules`, but do not prescribe implementation code
5. Use `ownership: manifest` for internal blocks described by this YAML
6. Use `ownership: child_ssot` only for reusable or independently verified child IPs
7. Put enough detail in `features`, `dataflow`, `function_model`, `cycle_model`, `fsm`, `memory`, `registers`, `timing`, `power`, `security`, `error_handling`, `debug_observability`, `integration`, `dft`, `synthesis`, `test_requirements`, and `quality_gates` for downstream workflows to implement and verify without hidden tribal knowledge.
8. Avoid IP-specific fixed templates. The SSOT must describe behavior, interfaces, constraints, and acceptance criteria; downstream workflows generate implementation from those facts.

## Phase 3: Validation Gate
- Parse `<ip>/yaml/<ip>.ssot.yaml` as YAML
- Check the file is substantive, has the canonical sections, and has no live `<TBD>` markers unless the user explicitly left them
- Check every interface port has name, width, direction, and description
- Check every feature has trigger, datapath/control behavior, observable output, and reset/error expectations where applicable
- Check `function_model` defines cycle-independent state variables, transactions, preconditions, outputs, side effects, error cases, invariants, and scoreboard/reference-model guidance
- Check `cycle_model` defines clock/reset timing, latency bounds, handshake rules, pipeline stages, ordering/backpressure, and observability
- Check timing, power, security, error_handling, debug_observability, integration, dft, and synthesis sections are explicit even when the answer is "not required" or "external owner"
- Check every `test_requirements.scenarios[]` item has stimulus, expected result, and coverage/scoreboard intent
- Check `quality_gates` gives concrete pass criteria and evidence for SSOT, RTL, DV, coverage, EDA, and signoff
- Check every assumption that affects RTL behavior is recorded under `custom.assumptions`
- Run `workflow/ssot-gen/scripts/check_ssot_disk.sh <ip>` or an equivalent YAML parse/structure check
- Fix validation errors before handoff

## Phase 4: Handoff
- Output a compact `[SSOT HANDOFF]` block for rtl-gen
- Include IP name, SSOT path, top module, interfaces, parameters, memories, registers, sub_modules, function_model, cycle_model, timing/power/security/error/integration/DFT/synthesis assumptions, reset/clock, verification scenarios, quality gates, and known constraints
- Include a downstream definition of done:
  - rtl-gen must write RTL + filelist and compile with zero errors
  - tb-gen must write cocotb or SV TB, run simulation, emit coverage artifacts, and pass all SSOT scenarios
  - sim_debug must inspect VCD/coverage and report waveform evidence or a precise handoff
  - EDA workflows must provide synthesis/STA/DFT evidence when quality_gates require it
- Do not claim RTL, lint, or sim passed unless a downstream workflow actually ran

## Phase 5: Completion
- Report exact files created/changed
- Report validation commands and results
- Tell the user rtl-gen is the next workflow
