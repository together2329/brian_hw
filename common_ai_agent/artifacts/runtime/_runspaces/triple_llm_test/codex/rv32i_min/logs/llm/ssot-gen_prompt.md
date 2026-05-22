Generate canonical SSOT YAML for rv32i_min from rv32i_min/req/rv32i_min_requirements.md.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Valid success schema:
{
  "files": [
    {
      "path": "rv32i_min/yaml/rv32i_min.ssot.yaml",
      "kind": "ssot",
      "content": "<complete YAML document as a JSON string>"
    }
  ]
}

The YAML content must be general IP SSOT, not a fixed template workaround. It must derive semantics from the requirements and include these top-level sections: top_module, sub_modules, parameters, io_list, features, dataflow, function_model, cycle_model, clock_reset_domains, cdc_requirements, rdc_requirements, registers, memory, interrupts, fsm, timing, power, security, error_handling, debug_observability, integration, dft, synthesis, pnr, coding_rules, reuse_modules, custom, dir_structure, filelist, rtl_contract, test_requirements, quality_gates, traceability, workflow_todos, generation_flow. function_model and cycle_model are mandatory and must be substantive enough for FL-vs-RTL equivalence goals, cocotb/pyuvm scoreboard generation, coverage planning, and mismatch ownership.

The generated YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh rv32i_min` without repair. Required validator details:
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
# rv32i_min IP Requirements

## Intent

Build a minimal **RV32I base integer ISA** CPU as a triple-LLM smoke
fixture for the common_ai_agent ssot→audit pipeline. The block is
deliberately broader than the `arm_m0_min` smoke fixture (37
instructions vs 15), but still excludes M/A/F/D/C extensions, debug,
PMP, MMU, interrupts, and CSR space. The same SSOT must drive an
identical run on three different model providers so we can compare
their authoring quality on a non-trivial CPU.

## Functional Behavior

- ISA: **RV32I base, 37 instructions**, all 32-bit aligned:
  `LUI AUIPC JAL JALR BEQ BNE BLT BGE BLTU BGEU LB LH LW LBU LHU SB SH SW
   ADDI SLTI SLTIU XORI ORI ANDI SLLI SRLI SRAI ADD SUB SLL SLT SLTU XOR
   SRL SRA OR AND FENCE ECALL EBREAK`.
- Width: 32-bit datapath, 32-bit fixed instructions.
- Register file: 32 × 32-bit (`x0..x31`); `x0` is hardwired zero
  (writes ignored, reads return 0).
- Pipeline: 3-stage IF / ID-EX / MEM-WB, in-order, single-issue.
- Bus: simple synchronous instruction bus + data bus
  (`i_addr/i_rdata/i_valid` and `d_addr/d_wdata/d_rdata/d_we/d_be/d_valid`),
  no AHB/AXI handshake — registered-ready model only.
- `clk` is the only clock; `rst_n` is active-low asynchronous reset.
- On reset: `pc <= 0x00000000`, all `x[1..31] <= 0`.
- `ECALL` and `EBREAK` advance `pc` by 4 and pulse a one-cycle
  `excpt_o` strobe; no trap delegation logic in this profile.
- `FENCE` is implemented as a one-cycle pipeline bubble (no memory
  ordering hardware in this profile).
- `JAL`/`JALR` write `pc + 4` into `rd`. `JALR` clears bit 0 of the
  computed target.
- Branches use signed comparisons except `BLTU`/`BGEU`.
- Loads and stores honour the byte-enable on `d_be`. `LB`/`LH` perform
  sign-extension; `LBU`/`LHU` zero-extend.
- Misaligned data accesses raise `excpt_o` for one cycle and do not
  retire the instruction (architectural state unchanged).
- `SLLI/SRLI/SRAI` shift amounts are restricted to `0..31` per the
  RV32I encoding (`shamt[5]` must be 0; otherwise illegal).

## Non-Goals

- No interrupts, NVIC, debug, performance counters, CSR file beyond
  what `ECALL`/`EBREAK`/`FENCE` need.
- No M / A / F / D / C extension support.
- No bus transactions beyond the registered ready synchronous bus.
- No clock-domain crossing, no power gating, no DFT chains.
- No branch prediction or speculative execution.

## Verification Hints

- Stimulus must exercise every one of the 37 mnemonics at least once
  with both random operands and edge values (0, ±1, INT_MAX, INT_MIN,
  0xFFFFFFFF, register `x0`, signed/unsigned compare boundaries).
- Coverage must include: every opcode hit, taken/untaken for each
  branch, sign-extension correctness for `LB`/`LH`, byte-enable
  patterns for stores, `x0` write-to-zero, `JAL`/`JALR` link-write,
  misaligned-fault, `ECALL`/`EBREAK` strobe.
- A simple ISS-style reference model (`functional_model.py`) drives
  expected register and PC trajectories cycle-by-cycle.

## Run Plan

This requirement file is the **single shared SSOT input** for three
parallel pipeline runs:

```
_runspaces/triple_llm_test/codex/   --model gpt-5.3-codex
_runspaces/triple_llm_test/claude/  --model claude-cli
_runspaces/triple_llm_test/cursor/  --model cursor-cli
```

Each sandbox runs `ssot-gen → fl-model-gen → cl-model-gen →
equiv-goals → rtl-gen → tb-gen → sim → sim-debug → lint → coverage →
goal-audit`. No manual fixes between stages; the pipeline must
self-repair through the existing repair loops or stop at the natural
human-gate. Side-by-side comparison of the three runs will populate
`_runspaces/triple_llm_test/COMPARISON.md` after the runs complete.
