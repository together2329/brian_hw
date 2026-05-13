Generate canonical SSOT YAML for cortex_m0lite from cortex_m0lite/req/cortex_m0lite_requirements.md.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Valid success schema:
{
  "files": [
    {
      "path": "cortex_m0lite/yaml/cortex_m0lite.ssot.yaml",
      "kind": "ssot",
      "content": "<complete YAML document as a JSON string>"
    }
  ]
}

The YAML content must be general IP SSOT, not a fixed template workaround. It must derive semantics from the requirements and include these top-level sections: top_module, sub_modules, parameters, io_list, features, dataflow, function_model, cycle_model, clock_reset_domains, cdc_requirements, rdc_requirements, registers, memory, interrupts, fsm, timing, power, security, error_handling, debug_observability, integration, dft, synthesis, pnr, coding_rules, reuse_modules, custom, dir_structure, filelist, rtl_contract, test_requirements, quality_gates, traceability, workflow_todos, generation_flow. function_model and cycle_model are mandatory and must be substantive enough for FL-vs-RTL equivalence goals, cocotb/pyuvm scoreboard generation, coverage planning, and mismatch ownership.

The generated YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh cortex_m0lite` without repair. Required validator details:
- function_model.state_variables, function_model.transactions, and function_model.invariants must be non-empty lists.
- Every function_model.transactions[] item must include id, name, preconditions, outputs, and either side_effects or error_cases. If state_updates exist, also summarize them in side_effects.
- cycle_model must include clock, reset, latency, non-empty handshake_rules, non-empty pipeline, and non-empty ordering.
- timing must include target_clocks and latency_budget.
- power must include non-empty domains and power_states.
- security must include classification, non-empty assets, and non-empty threat_model.
- error_handling must include non-empty error_sources plus propagation and recovery.
- debug_observability must include waveform_must_probe and trace_events.
- integration must include bus_attachment and dependencies.
- dft must include scan_required, controllability, and observability.
- synthesis must include dialect, constraints, and required_outputs.
- every test_requirements.scenarios[] item must include id, name, stimulus, expected, checker, and coverage.
- quality_gates must be a mapping with ssot, rtl, dv, coverage, eda, and signoff; each gate must be a mapping with pass and evidence.
- If quality_gates.rtl_gen.profile is production, or the IP is DMA330/PL330-class, quality_gates.rtl_gen must include pass/evidence and every manifest-owned child module must have machine-readable integration.connections or sub_modules[].connections records with module/port/signal fields.
- traceability.yaml_to_output must be a non-empty list.

- workflow_todos.rtl-gen must be a non-empty list of LLM-authored RTL TODOs. Each item must include id, content, detail, criteria, source_refs, priority, required, and owner_module/owner_file when inferable from sub_modules. These TODOs are the downstream rtl-gen work ledger and must be specific to this IP, not fixed boilerplate.

If the requirements leave a semantic decision undefined, return exactly this JSON shape instead of files[]:
{
  "human_gate": {
    "decision_needed": "<specific RTL-engineer decision>",
    "evidence": {"requirement_refs": [], "ssot_refs": [], "tool_logs": [], "goal_ids": []},
    "options": [{"label": "<option>", "effect": "<downstream effect>"}],
    "recommended_default": {"label": "<option>", "why": "<reason>"},
    "downstream_effect": ["function_model", "cycle_model", "rtl_contract", "tb scoreboard"]
  }
}

Requirements:
# Cortex-M0-Like Microcontroller CPU Requirements

## Scope
- Build a compact Cortex-M0-like microcontroller CPU IP named `cortex_m0lite`.
- Target is a pedagogical ARMv6-M style 16-bit Thumb subset CPU, not a certified ARM core.
- Single-clock synchronous design, active-low reset.

## Top-Level Behavior
- 3-stage pipeline:
  - IF: fetch 16-bit instruction from instruction memory interface
  - ID: decode and operand read
  - EX/WB: ALU execute, load/store address generation, writeback
- In-order, single-issue execution.
- Deterministic, bounded latency for supported instructions.

## ISA Subset (Thumb-like)
- Data processing:
  - `MOVS`, `ADDS`, `SUBS`, `ANDS`, `ORRS`, `EORS`, `LSLS`, `LSRS`
- Immediate and register variants for arithmetic where practical.
- Compare/branch:
  - `CMP`, `B`, `BEQ`, `BNE`, `BGT`, `BLT`
- Return/control:
  - `BX LR` (used as software interrupt return)
- Memory access:
  - `LDR`, `STR` word access (aligned 32-bit)
- Control:
  - `NOP`
- Unsupported opcodes:
  - Must raise `illegal_instr` flag and vector to fault state.

## Register and Architectural State
- 16 architectural registers `r0..r15`:
  - `r13` = SP
  - `r14` = LR
  - `r15` = PC
- Program status flags: `N`, `Z`, `C`, `V`.
- Reset vector input for initial PC.

## External Interfaces
- Instruction memory interface:
  - request/valid handshake
  - 32-bit address output (word aligned)
  - 16-bit instruction input
- Data memory interface:
  - request/valid/ready handshake
  - address, write data, read data, byte enables, write enable
- Interrupt:
  - single external IRQ line
  - entry to parameterized fixed vector address `IRQ_VECTOR_ADDR` (default `32'h0000_0080`)
  - save return PC in LR on IRQ entry
  - return from IRQ is software-driven via `BX LR`
- Debug visibility outputs:
  - current PC, current instruction, current state, fault flag

## Microarchitecture and FSM
- Controller FSM states:
  - `RESET`, `FETCH`, `DECODE`, `EXECUTE`, `MEM_WAIT`, `WRITEBACK`, `IRQ_ENTRY`, `FAULT`
- Branches flush IF/ID and redirect PC.
- Load/store wait in `MEM_WAIT` until ready.

## Timing and Performance Targets
- 1 CPI for simple ALU ops in steady state.
- 2+ cycles for memory ops depending on data memory ready.
- Branch penalty target: <= 2 cycles.

## Safety and Error Handling
- Detect and fault on:
  - illegal opcode
  - misaligned load/store
- Fault behavior:
  - latch `fault` status
  - hold in `FAULT` state until reset

## Verification Targets
- Functional model must exist for ISA subset execution semantics.
- Cycle model must represent pipeline/control timing behavior.
- Testbench goals:
  - arithmetic correctness
  - branch decisions and PC updates
  - load/store correctness and wait-state handling
  - IRQ entry/return behavior
  - fault injection for illegal/misaligned cases

## Constraints
- Use synthesizable SystemVerilog.
- Keep implementation compact and readable with clear comments.
- Prefer shift/adder-friendly operations in datapath over expensive arithmetic where possible.
