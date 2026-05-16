Repair the SSOT YAML artifact for rv32i_min. This is repair attempt 1.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "rv32i_min/yaml/rv32i_min.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}
  ]
}

Repair rules:
- Do not use a fixed IP template or hardcoded workaround.
- Preserve product semantics from the requirement and current SSOT wherever they are valid.
- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.
- Fix the concrete parse/validator failures below, and also check for sibling contract defects.
- The repaired YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh rv32i_min`.
- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.

Failure summary:
human_gate: SSOT disk validator failed: [check_ssot_disk] FAIL: rv32i_min/yaml/rv32i_min.ssot.yaml failed YAML/model validation

Blocker artifact:


Validator log:
cmd: bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh rv32i_min
cwd: /Users/brian/Desktop/Project/brian_hw/common_ai_agent/_runspaces/triple_llm_test/codex
returncode: 1
stdout:
[check_ssot_disk] FAIL: rv32i_min/yaml/rv32i_min.ssot.yaml failed YAML/model validation
  function_model.transactions[] must include at least one executable output_rules entry with name/expr/width/port


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


Current SSOT YAML:
top_module:
  name: rv32i_min
  file: rtl/rv32i_min.sv
  version: '1.0'
  type: cpu
  description: Minimal single-issue 3-stage RV32I CPU (37 instructions) with synchronous instruction/data buses.
  reference_spec: RISC-V Unprivileged ISA RV32I
  target:
    technology: generic
    clock_freq_mhz: 100
    area_um2: null
    power_mw: null
sub_modules:
- name: rv32i_min_if
  file: rtl/rv32i_min_if.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - cycle_model.pipeline.IF
  - io_list.interfaces.instr_bus
  - function_model.transactions.FM_FETCH
  source_sections: &id001
  - cycle_model
  - io_list
  - function_model
  function_model_refs:
  - function_model.transactions.FM_FETCH
  - function_model.transactions.FM_BRANCH
  - function_model.transactions.FM_JUMP
  cycle_model_refs:
  - cycle_model.pipeline
  ssot_refs:
  - io_list.interfaces
  description: Instruction fetch stage and PC update mux front-end
- name: rv32i_min_idex
  file: rtl/rv32i_min_idex.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - function_model.transactions.FM_ALU
  - function_model.transactions.FM_BRANCH
  - function_model.transactions.FM_JUMP
  - function_model.transactions.FM_SYSTEM
  - cycle_model.pipeline.ID_EX
  - fsm.control
  source_sections:
  - function_model
  - cycle_model
  - fsm
  - features
  - registers
  function_model_refs:
  - function_model.transactions.FM_ALU
  - function_model.transactions.FM_BRANCH
  - function_model.transactions.FM_JUMP
  - function_model.transactions.FM_SYSTEM
  - function_model.state_variables
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model
  fsm_refs:
  - fsm.control
  - fsm
  description: Decode/execute stage including ALU, branch compare, immediate decode, and control
  feature_refs:
  - features
  register_refs:
  - registers.register_list
- name: rv32i_min_memwb
  file: rtl/rv32i_min_memwb.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - function_model.transactions.FM_LOAD
  - function_model.transactions.FM_STORE
  - cycle_model.pipeline.MEM_WB
  - error_handling
  source_sections: &id002
  - function_model
  - cycle_model
  - error_handling
  function_model_refs:
  - function_model.transactions.FM_LOAD
  - function_model.transactions.FM_STORE
  cycle_model_refs:
  - cycle_model.pipeline
  dataflow_refs:
  - dataflow
  description: Load/store data path, byte-enable application, sign/zero extension, and writeback
- name: rv32i_min_regfile
  file: rtl/rv32i_min_regfile.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - function_model.state_variables.regfile
  - function_model.invariants
  source_sections: &id003
  - function_model
  function_model_refs:
  - function_model.state_variables
  - function_model.invariants
  description: 32x32 register file with hard-wired x0 behavior
- name: rv32i_min_core
  file: rtl/rv32i_min_core.sv
  ownership: manifest
  ssot_gen: false
  implements:
  - function_model
  - cycle_model
  - dataflow
  - rtl_contract
  source_sections:
  - function_model
  - cycle_model
  - dataflow
  - rtl_contract
  - decomposition
  - test_requirements
  function_model_refs:
  - function_model.transactions
  - function_model.state_variables
  - function_model.transactions.FM_SYSTEM
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.handshake_rules
  dataflow_refs:
  - dataflow
  description: Top behavioral owner integrating IF/ID-EX/MEM-WB stages and architectural retirement
  decomposition_refs:
  - decomposition
  test_refs:
  - test_requirements
- name: rv32i_min
  file: rtl/rv32i_min.sv
  ownership: manifest
  ssot_gen: true
  description: Top-level integration module matching SSOT top_module
decomposition:
  units:
  - id: fetch
    kind: control/datapath
    source_refs:
    - function_model.transactions.FM_FETCH
    - cycle_model.pipeline
    rtl_candidates:
    - rv32i_min_if
    verification_impact:
    - test_requirements.scenarios.SC_FETCH_FLOW
  - id: execute
    kind: control/datapath
    source_refs:
    - function_model.transactions.FM_ALU
    - function_model.transactions.FM_BRANCH
    - function_model.transactions.FM_JUMP
    rtl_candidates:
    - rv32i_min_idex
    verification_impact:
    - test_requirements.scenarios.SC_ALU_BRANCH_JUMP
  - id: memory_writeback
    kind: datapath
    source_refs:
    - function_model.transactions.FM_LOAD
    - function_model.transactions.FM_STORE
    rtl_candidates:
    - rv32i_min_memwb
    verification_impact:
    - test_requirements.scenarios.SC_LOAD_STORE
  strategy: manifest_owned_leaf_decomposition
  owners:
  - module: rv32i_min_if
    file: rtl/rv32i_min_if.sv
    responsibility: Instruction fetch stage and PC update mux front-end
    source_sections: *id001
  - module: rv32i_min_idex
    file: rtl/rv32i_min_idex.sv
    responsibility: Decode/execute stage including ALU, branch compare, immediate decode, and control
    source_sections:
    - function_model
    - cycle_model
    - fsm
  - module: rv32i_min_memwb
    file: rtl/rv32i_min_memwb.sv
    responsibility: Load/store data path, byte-enable application, sign/zero extension, and writeback
    source_sections: *id002
  - module: rv32i_min_regfile
    file: rtl/rv32i_min_regfile.sv
    responsibility: 32x32 register file with hard-wired x0 behavior
    source_sections: *id003
  - module: rv32i_min_core
    file: rtl/rv32i_min_core.sv
    responsibility: Top behavioral owner integrating IF/ID-EX/MEM-WB stages and architectural retirement
    source_sections:
    - function_model
    - cycle_model
    - dataflow
    - rtl_contract
  - module: rv32i_min
    file: rtl/rv32i_min.sv
    responsibility: Top-level integration module matching SSOT top_module
    source_sections:
    - function_model
    - cycle_model
    - io_list
  integration_policy: Top-level wiring must be backed by integration.connections or sub_modules[].connections before signoff.
  source_refs:
  - sub_modules
  - function_model
  - cycle_model
  - integration
parameters:
- name: XLEN
  default: 32
  type: int
  description: Architectural register and ALU width
  drives:
  - rtl/rv32i_min_core.sv
  - rtl/rv32i_min_regfile.sv
- name: RESET_PC
  default: 0
  type: int
  description: Reset vector
  drives:
  - rtl/rv32i_min_if.sv
  - rtl/rv32i_min_core.sv
- name: INST_ALIGN
  default: 4
  type: int
  description: Instruction alignment in bytes
  drives:
  - rtl/rv32i_min_if.sv
io_list:
  clock_domains:
  - name: clk
    frequency_mhz: 100
    description: CPU core clock
    ports:
    - name: clk
      width: 1
      direction: input
      description: Main clock
  resets:
  - name: rst_n
    polarity: active_low
    sync_async: async_assert_sync_deassert
    description: Core reset
    ports:
    - name: rst_n
      width: 1
      direction: input
      description: Active-low reset
  interfaces:
  - name: instr_bus
    type: custom_sync
    role: master_addr_slave_data
    description: Synchronous instruction fetch bus
    ports:
    - name: i_addr
      width: 32
      direction: output
      description: Instruction address
    - name: i_rdata
      width: 32
      direction: input
      description: Instruction data
    - name: i_valid
      width: 1
      direction: output
      description: Instruction request valid
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: data_bus
    type: custom_sync
    role: master
    description: Synchronous data bus
    ports:
    - name: d_addr
      width: 32
      direction: output
      description: Data address
    - name: d_wdata
      width: 32
      direction: output
      description: Store data
    - name: d_rdata
      width: 32
      direction: input
      description: Load data
    - name: d_we
      width: 1
      direction: output
      description: Write enable
    - name: d_be
      width: 4
      direction: output
      description: Byte enable
    - name: d_valid
      width: 1
      direction: output
      description: Data transaction valid
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
  - name: exception
    type: custom
    role: output
    description: One-cycle exception strobe
    ports:
    - name: excpt_o
      width: 1
      direction: output
      description: Exception pulse
    clock_domain: clk
    reset_domain: rst_n
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
features:
- name: RV32I_37_instruction_support
  trigger: Legal RV32I opcodes in supported 37-mnemonic subset
  datapath: IF fetches 32-bit instruction, ID-EX decodes/executes, MEM-WB performs memory and commit
  control: In-order, single-issue IF/ID-EX/MEM-WB sequencing
  output: Architectural PC/regfile updates and data bus traffic
- name: x0_hardwired_zero
  trigger: Any writeback with rd==0
  datapath: Write suppressed in regfile
  control: Commit stage masks x0 writes
  output: x0 always reads as 0
- name: exception_pulse_profile
  trigger: ECALL/EBREAK or misaligned data access or illegal shift-immediate encoding
  datapath: No architectural commit for misaligned/illegal cases
  control: Single-cycle excpt_o strobe generation
  output: excpt_o pulse and defined PC behavior
dataflow:
  instruction_path:
    source: Instruction memory
    sequence: pc -> i_addr/i_valid -> i_rdata -> decode
  execute_path:
    source: regfile + immediate decoder
    sequence: ID decode -> ALU/compare/target -> control decision
  memory_path:
    load: effective_addr -> d_addr/d_valid/d_we=0 -> d_rdata -> sign/zero extension -> wb
    store: effective_addr + rs2 -> d_addr/d_wdata/d_be/d_we=1/d_valid=1
  commit_path:
    sequence: MEM-WB selects wb_data -> write rd unless rd==x0 -> update pc
function_model:
  purpose: Cycle-independent RV32I architectural contract for ISS-style equivalence and scoreboard comparison.
  state_variables:
  - name: pc
    source: architectural
    reset: 0
    description: Program counter
  - name: regfile
    source: architectural
    reset: x0..x31 all zero
    description: General-purpose register file; x0 immutable zero
  - name: excpt_o
    source: architectural_output
    reset: 0
    description: One-cycle exception pulse
  transactions:
  - id: FM_FETCH
    name: fetch_and_default_advance
    preconditions:
    - instr_word is available for current pc
    - pc % 4 == 0
    inputs:
    - pc
    - i_rdata
    outputs:
    - decoded instruction fields available to execute stage
    - default next_pc = pc + 4
    side_effects:
    - pc advances by 4 when no control-transfer override or fault blocks retirement
    output_rules: []
  - id: FM_ALU
    name: alu_and_immediate_ops
    preconditions:
    - opcode in {OP, OP-IMM, LUI, AUIPC}
    inputs:
    - rs1
    - rs2
    - imm
    - funct3
    - funct7
    outputs:
    - rd receives computed 32-bit result
    side_effects:
    - register writeback updates regfile[rd] when rd != 0
    error_cases:
    - condition: SLLI/SRLI/SRAI has shamt bit[5] == 1
      result: illegal instruction pulse on excpt_o; no register or pc retirement side effect beyond defined next_pc policy
    output_rules: []
  - id: FM_BRANCH
    name: conditional_branches
    preconditions:
    - opcode is BRANCH
    inputs:
    - rs1
    - rs2
    - branch_imm
    - funct3
    outputs:
    - pc becomes pc + branch_imm if condition true else pc + 4
    side_effects:
    - no register writeback
    output_rules: []
  - id: FM_JUMP
    name: jal_and_jalr
    preconditions:
    - opcode in {JAL, JALR}
    inputs:
    - pc
    - rs1
    - imm
    - rd
    outputs:
    - regfile[rd] gets old pc + 4 when rd != 0
    - JAL target = pc + imm
    - JALR target = (rs1 + imm) & ~1
    side_effects:
    - pc redirected to computed target
    output_rules: []
  - id: FM_LOAD
    name: loads_with_extension
    preconditions:
    - opcode is LOAD
    - effective address alignment matches size
    inputs:
    - d_rdata
    - funct3
    - effective_addr
    outputs:
    - LB/LH sign-extend
    - LBU/LHU zero-extend
    - LW returns full 32-bit
    side_effects:
    - writeback to rd when rd != 0
    error_cases:
    - condition: misaligned address for access size
      result: excpt_o pulse for one cycle; architectural state unchanged
    output_rules: []
  - id: FM_STORE
    name: stores_with_byte_enable
    preconditions:
    - opcode is STORE
    - effective address alignment matches size
    inputs:
    - rs2
    - funct3
    - effective_addr
    outputs:
    - d_we=1 and d_be reflects store width/address
    side_effects:
    - no register writeback
    error_cases:
    - condition: misaligned address for access size
      result: excpt_o pulse for one cycle; no architectural state change
    output_rules: []
  - id: FM_SYSTEM
    name: fence_ecall_ebreak
    preconditions:
    - opcode in {FENCE, ECALL, EBREAK}
    inputs:
    - opcode
    outputs:
    - FENCE inserts one bubble then proceeds
    - ECALL/EBREAK pulse excpt_o
    side_effects:
    - ECALL/EBREAK pc advances by 4
    - FENCE has no architectural register modification
    output_rules: []
  invariants:
  - regfile[0] == 0 at all times
  - Only retired valid instructions modify architectural state
  - Misaligned data access leaves pc and regfile unchanged for that instruction
  - JALR target least-significant bit is always zero
cycle_model:
  purpose: Clocked IF/ID-EX/MEM-WB contract with synchronous registered-ready bus behavior.
  executable: pymtl3
  clock: clk
  reset:
    assertion: rst_n low asynchronously clears architectural and pipeline state
    deassertion: state usable on first rising edge after synchronized deassertion
  latency:
    fetch_to_decode:
      min_cycles: 1
      max_cycles: 1
      description: IF to ID-EX register transfer
    alu_ops_retire:
      min_cycles: 3
      max_cycles: 3
      description: IF->ID-EX->MEM-WB for non-memory ops
    load_retire:
      min_cycles: 3
      max_cycles: 3
      description: Assumes single-cycle synchronous data return
    store_issue:
      min_cycles: 2
      max_cycles: 3
      description: Address/data presented in MEM stage
    fence_penalty:
      min_cycles: 1
      max_cycles: 1
      description: One-cycle bubble
  handshake_rules:
  - signal: i_valid
    rule: When high, i_addr must be stable for the cycle and i_rdata is sampled on rising edge.
  - signal: d_valid
    rule: When high, d_addr/d_we/d_be and (if d_we) d_wdata are stable for the cycle.
  - signal: d_we
    rule: d_we=1 indicates store; d_we=0 indicates load; no additional ready handshake exists.
  - signal: excpt_o
    rule: excpt_o may only pulse for one cycle per triggering instruction class.
  pipeline:
  - stage: IF
    cycle: t
    action: Drive i_addr=pc and i_valid=1; latch i_rdata into IF/ID register
  - stage: ID_EX
    cycle: t+1
    action: Decode opcode, read rs1/rs2, compute ALU result/branch condition/target/effective address
  - stage: MEM_WB
    cycle: t+2
    action: Perform load/store bus drive or writeback result and commit pc update
  ordering:
  - Instructions retire in program order, one architectural commit slot per cycle max.
  - A faulting instruction does not retire and must not modify regfile or pc (except defined ECALL/EBREAK advance semantics).
  - Store side effects occur only for non-faulting aligned store instructions.
  backpressure:
  - No explicit ready/valid backpressure channels; memory model is synchronous and sampled each cycle.
  observability:
  - Every function_model transaction maps to one or more of IF/ID_EX/MEM_WB stages.
  backend_policy: Use PyMTL3 for the clocked cycle model shell; FunctionalModel remains the behavioral oracle.
  performance:
    frequency_mhz: 100
    throughput:
      sustained_beats_per_cycle: 1
      condition: No backpressure on the active interface
    outstanding:
      max: 1
      description: Default one accepted operation until the SSOT declares deeper buffering
    depth:
      pipeline_stages: 3
      queue_depth: 1
      description: Default accept/evaluate/observe cycle model depth
clock_reset_domains:
  domains:
  - name: clk
    frequency_mhz: 100
    description: Single core clock
  reset_scheme:
    signal: rst_n
    polarity: active_low
    type: async_assert_sync_deassert
cdc_requirements:
  crossings: []
  synchronizers: []
  note: Single clock domain
rdc_requirements:
  crossings: []
  synchronizers: []
  note: Single reset domain
registers:
  config:
    register_width: 32
    addr_width: 5
    byte_addressable: false
    note: Architectural register file only; no CSR/control MMIO map in this profile
  register_list:
  - name: GPR
    offset: 0
    width: 32
    access: rw
    reset: 0
    repeat: 32
    stride: 1
    category: architectural
    description: General purpose registers x0..x31
    fields:
    - name: value
      bits:
      - 31
      - 0
      access: rw
      reset: 0
      description: Register value; x0 writes ignored, reads return zero
      write_effect: APB write data updates this field value according to its bit mask.
memory:
  instances:
  - name: if_id_reg
    type: register
    depth: 1
    width: 64
    read_ports: 1
    write_ports: 1
    latency: 0
    description: Instruction and PC pipeline register
  - name: id_ex_reg
    type: register
    depth: 1
    width: 192
    read_ports: 1
    write_ports: 1
    latency: 0
    description: Decoded control/data pipeline register
  - name: ex_mem_wb_reg
    type: register
    depth: 1
    width: 160
    read_ports: 1
    write_ports: 1
    latency: 0
    description: MEM/WB pipeline register
  note: External instruction/data memories are outside IP boundary
interrupts:
  sources: []
  output:
    signal: excpt_o
    polarity: active_high
    type: pulse
    description: Exception strobe only; not an interrupt controller interface
fsm:
  control:
    states:
    - RESET
    - RUN
    - FENCE_BUBBLE
    transitions:
    - from: RESET
      to: RUN
      condition: rst_n deasserted and first clk edge
    - from: RUN
      to: FENCE_BUBBLE
      condition: decoded instruction is FENCE
    - from: FENCE_BUBBLE
      to: RUN
      condition: one cycle elapsed
    note: Pipeline normally streams in RUN; FENCE introduces exactly one bubble
timing:
  target_clocks:
  - domain: clk
    target_mhz: 100
    uncertainty_ns: 0.2
  latency_budget:
    instruction_retire_cycles: 3
    branch_resolution_stage: ID_EX
    fence_extra_cycles: 1
  throughput:
    ipc_peak: 1.0
    ipc_sustained_notes: Single issue in-order, no speculation
  sta_expectations:
    setup_wns_ns_min: 0.0
    hold_wns_ns_min: 0.0
    required_reports:
    - sta/out/timing.rpt
    - sta/out/wns.json
power:
  domains:
  - name: PD_CORE
    supply: vdd
    elements:
    - rv32i_min core logic and regfile
  power_states:
  - name: 'ON'
    description: Normal execution
  - name: RESET
    description: Reset asserted; state cleared
  clock_gating: Not implemented in minimal profile
  upf_required: false
security:
  classification: non-secure minimal compute core
  assets:
  - Architectural register state
  - Program counter control flow integrity
  - Load/store data correctness
  threat_model:
  - Malformed instruction encodings causing undefined state transitions
  - Misaligned memory accesses corrupting architectural state
  - x0 corruption by unintended writeback
  assumptions:
  - Trusted instruction/data memory in this profile
  - No privilege separation or PMP/MMU
  privilege_model: System-level access control is owned by the integrating bus/firewall unless explicitly declared here.
error_handling:
  error_sources:
  - id: ERR_PROTOCOL
    condition: Downstream protocol response is non-OKAY or invalid
    architectural_effect: Set error status and block signoff until handled
  propagation:
  - Drive excpt_o high for one cycle on detection edge
  - Block architectural retirement for misaligned/illegal encoding
  recovery:
  - Continue execution on next instruction after one-cycle pulse for ECALL/EBREAK
  - For misaligned/illegal, architectural state remains unchanged and fetch continues per control policy
debug_observability:
  waveform_must_probe:
  - pc
  - instr_word
  - decoded_opcode
  - rs1_idx/rs2_idx/rd_idx
  - regfile_wen/regfile_wdata
  - d_addr/d_we/d_be/d_valid/d_wdata/d_rdata
  - excpt_o
  - pipeline_stage_valids
  trace_events:
  - instruction_retire
  - branch_taken
  - branch_not_taken
  - jal_or_jalr
  - misaligned_fault
  - ecall_ebreak_pulse
  status_outputs:
  - status/debug signals declared in io_list or registers
integration:
  bus_attachment:
    instruction_bus: custom synchronous fetch interface i_*
    data_bus: custom synchronous load/store interface d_*
  dependencies:
  - External instruction memory returns i_rdata each cycle for i_addr
  - External data memory observes d_valid/d_we/d_be and provides d_rdata for loads
  connections:
  - module: rv32i_min_if
    port: i_addr
    signal: i_addr
  - module: rv32i_min_if
    port: i_valid
    signal: i_valid
  - module: rv32i_min_if
    port: i_rdata
    signal: i_rdata
  - module: rv32i_min_memwb
    port: d_addr
    signal: d_addr
  - module: rv32i_min_memwb
    port: d_wdata
    signal: d_wdata
  - module: rv32i_min_memwb
    port: d_rdata
    signal: d_rdata
  - module: rv32i_min_memwb
    port: d_we
    signal: d_we
  - module: rv32i_min_memwb
    port: d_be
    signal: d_be
  - module: rv32i_min_memwb
    port: d_valid
    signal: d_valid
  - module: rv32i_min_core
    port: excpt_o
    signal: excpt_o
  connection_contract_status: missing machine-readable module wiring; child RTL drafts may proceed from owner packets, but top integration/signoff
    must stay blocked until SSOT authors integration.connections or sub_modules[].connections with module/port/signal records
  integration_notes:
  - Integrator must connect every declared io_list port and honor timing/reset assumptions.
dft:
  scan_required: false
  controllability: Primary-input control via clk/rst_n/bus stimulus is sufficient for smoke profile
  observability: Primary-output observation plus waveform probes listed in debug_observability
  mbist: Not applicable; no internal SRAM macros
  mbist_required: true
synthesis:
  dialect: systemverilog_2012
  constraints:
  - Single clock clk with async active-low reset
  - No inferred latches
  - Keep 3-stage pipeline boundaries explicit
  required_outputs:
  - gate-level netlist
  - timing report
  - area report
  top_module: rv32i_min
pnr:
  utilization_pct: 55
  aspect_ratio: 1.0
  core_space_um: 5.0
  global_density: 0.6
  io_layers:
    horizontal: met3
    vertical: met2
  cts:
    buf_list:
    - generic_clkbuf_small
    - generic_clkbuf_med
  routing:
    signal_layers:
      min: met1
      max: met5
    drc_waivers: []
  cts_buf_list:
  - sky130_fd_sc_hd__clkbuf_4
  - sky130_fd_sc_hd__clkbuf_8
coding_rules:
  verilog_style: systemverilog_2012
  file_extension: .sv
  parameter_header: rtl/rv32i_min_param.vh
  conventions:
  - Use nonblocking assignments in sequential blocks
  - Use blocking assignments in combinational blocks
  - x0 register writes must be explicitly masked
  - No speculative execution logic
  - No extension opcodes beyond RV32I 37 listed mnemonics
reuse_modules: []
custom:
  assumptions:
  - Instruction and data memory respond synchronously without ready/stall handshake
  - No interrupt/trap vector subsystem
  run_context: Triple-LLM smoke fixture for ssot->audit comparison
dir_structure:
  template_dirs:
    rtl: templates/rtl/
    sim: templates/sim/
  output_dirs:
    rtl: rtl/
    sim: sim/
    firmware: firmware/
    docs: docs/
  yaml_dir: yaml/
  generators_dir: generators/
filelist:
  headers:
  - rtl/rv32i_min_param.vh
  rtl:
  - rtl/rv32i_min_if.sv
  - rtl/rv32i_min_idex.sv
  - rtl/rv32i_min_memwb.sv
  - rtl/rv32i_min_regfile.sv
  - rtl/rv32i_min_core.sv
  - rtl/rv32i_min.sv
  sim:
  - sim/tb_top.sv
  - sim/rv32i_min_ref_model.py
  - sim/tb_program.sv
  docs:
  - docs/rv32i_min_microarch.md
  - docs/rv32i_min_isa_coverage.md
  tb:
  - tb/cocotb/test_rv32i_min.py
  - tb/cocotb/test_runner.py
  - tb/cocotb/scoreboard.py
  coverage:
  - cov/coverage.json
test_requirements:
  scenarios:
  - id: SC01
    name: reset contract
    stimulus: Assert and release the declared reset while all external interfaces remain idle.
    expected: Architectural state, status, outputs, and debug observability match function_model reset outputs.
    checker: Reset checker compares all declared reset-visible state against function_model and cycle_model reset rules.
    coverage:
    - function_model.reset
    - cycle_model.reset
  - id: SC02
    name: primary approved behavior
    stimulus: Drive a legal request, transaction, command, packet, or CSR operation from function_model primary preconditions.
    expected: Externally observable result/status/side effects match the function_model primary transaction.
    checker: FL-vs-RTL scoreboard compares observable outputs and state updates from the locked function_model.
    coverage:
    - function_model.primary
    - features
    - dataflow
  - id: SC03
    name: cycle handshake and backpressure
    stimulus: Apply legal stalls or delayed handshakes on every declared cycle_model interface phase.
    expected: Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules.
    checker: Protocol monitor and scoreboard check cycle_model.handshake_rules, ordering, and latency budget.
    coverage:
    - cycle_model.handshake_rules
    - cycle_model.ordering
    - backpressure
  - id: SC04
    name: error and recovery policy
    stimulus: Inject each declared error_handling.error_sources condition where the interface can represent it.
    expected: Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state.
    checker: Negative checker compares error result and recovery state against function_model error_cases.
    coverage:
    - error_handling.error_sources
    - function_model.error_cases
  - id: SC05
    name: debug and trace observability
    stimulus: Run nominal and error flows while sampling every debug_observability waveform/status/trace point.
    expected: Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior.
    checker: Waveform/trace checker validates debug_observability entries and traceability.yaml_to_output rows.
    coverage:
    - debug_observability
    - traceability
  - id: SC06
    name: function_model transaction FM_FETCH
    stimulus: Drive preconditions for function_model transaction `FM_FETCH`.
    expected: Outputs and side effects match `FM_FETCH` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_FETCH
  - id: SC07
    name: function_model transaction FM_ALU
    stimulus: Drive preconditions for function_model transaction `FM_ALU`.
    expected: Outputs and side effects match `FM_ALU` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_ALU
  - id: SC08
    name: function_model transaction FM_BRANCH
    stimulus: Drive preconditions for function_model transaction `FM_BRANCH`.
    expected: Outputs and side effects match `FM_BRANCH` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_BRANCH
  - id: SC09
    name: function_model transaction FM_JUMP
    stimulus: Drive preconditions for function_model transaction `FM_JUMP`.
    expected: Outputs and side effects match `FM_JUMP` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_JUMP
  - id: SC10
    name: function_model transaction FM_LOAD
    stimulus: Drive preconditions for function_model transaction `FM_LOAD`.
    expected: Outputs and side effects match `FM_LOAD` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_LOAD
  - id: SC11
    name: function_model transaction FM_STORE
    stimulus: Drive preconditions for function_model transaction `FM_STORE`.
    expected: Outputs and side effects match `FM_STORE` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_STORE
  - id: SC12
    name: function_model transaction FM_SYSTEM
    stimulus: Drive preconditions for function_model transaction `FM_SYSTEM`.
    expected: Outputs and side effects match `FM_SYSTEM` exactly.
    checker: Transaction scoreboard compares RTL observations against the locked function_model transaction.
    coverage:
    - function_model.transactions.FM_SYSTEM
  scoreboard_checks: 20
  coverage_goals:
    function:
      target_pct: 100
      model: function_model
      bins:
      - id: FCOV_OPCODE_37
        source_ref: function_model.transactions
        class: opcode
        description: All 37 required opcodes executed
      - id: FCOV_X0_IMMUTABLE
        source_ref: function_model.invariants
        c
... <truncated 10857 chars>