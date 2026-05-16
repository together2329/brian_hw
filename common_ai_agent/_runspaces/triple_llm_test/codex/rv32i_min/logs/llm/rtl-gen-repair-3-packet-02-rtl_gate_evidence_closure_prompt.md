RTL-GEN PACKET MODE for rv32i_min. Packet attempt 3.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "rv32i_min/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "rv32i_min/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "rv32i_min/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
  ]
}

If this packet exposes a missing locked-truth decision, return a human_gate object instead of inventing SSOT, FL, coverage, interface, or performance semantics.

Packet execution rules:
- Author only RTL-owned artifacts for the current packet, plus local notes/contract metadata when useful.
- Do not edit SSOT YAML, FunctionalModel, coverage goals, protocol assertions, performance targets, or requirements.
- You cannot read files from the repo during this turn. The required locked SSOT facts are embedded below; do not return requires/missing-file JSON for those paths.
- Do not emit placeholder, heartbeat-only, alive-only, or tie-off-only RTL to satisfy a manifest.
- For production-profile packets, add real SSOT-scaled implementation depth: state/control/data movement, nonconstant logic, and child wiring must be proportional to the packet tasks.
- For a module packet, focus on owner_file and every task content/detail/criteria/source_ref in the packet.
- If current owner_file content is provided, preserve prior slice logic and merge the new behavior; do not replace the file with a partial slice-only module.
- For mixed packets with locked-truth blockers, keep authoring LLM-actionable RTL/test/evidence work and leave the locked-truth tasks open.
- Return human_gate only when no LLM-actionable open work remains or the missing locked-truth decision blocks correct RTL authoring.
- For rtl_gate_evidence_closure, repair only LLM-actionable evidence gaps revealed by compile/lint/audit output; do not claim PASS.
- If rtl_gate_evidence_closure includes pending connection_contract_suggestions, you may use them as draft RTL wiring candidates to instantiate child modules and close hierarchy/signal-flow evidence, but they remain pending QA and must not be treated as SSOT authority.
- For rtl_gate_tool_evidence, do not fabricate compile/lint/sim/coverage artifacts. If compile/lint evidence already exists and is not clean, repair the owner RTL that caused the diagnostics; the runner will rerun tools afterward.
- For rtl_gate_contract_blocked, return human_gate only; missing SSOT connection contracts block correct top integration semantics.
- For rtl_gate_human_closure, return human_gate only; do not invent or edit human-locked authority.
- The headless runner will refresh filelist/provenance from LLM-authored artifacts after each packet.

Current packet: rtl_gate_evidence_closure
kind: gate
work queue: 3/3 active packets (11 closed packets skipped from 15 total)
batch limit: 4; deferred active packets after this batch: 1
owner_module: rv32i_min
owner_file: rtl/rv32i_min.sv

SSOT observable latency contract:
{
  "cycle_model.latency": {
    "alu_ops_retire": {
      "description": "IF to ID_EX to MEM_WB retire path",
      "max_cycles": 3,
      "min_cycles": 3
    },
    "fence_penalty": {
      "description": "Required one-cycle bubble",
      "max_cycles": 1,
      "min_cycles": 1
    },
    "fetch_to_decode": {
      "description": "IF to ID_EX transfer",
      "max_cycles": 1,
      "min_cycles": 1
    },
    "load_retire": {
      "description": "Single-cycle synchronous data return assumption",
      "max_cycles": 3,
      "min_cycles": 3
    },
    "store_issue": {
      "description": "Address and write data presented by MEM stage",
      "max_cycles": 3,
      "min_cycles": 2
    }
  },
  "cycle_model.pipeline": [
    {
      "action": "Drive i_addr from pc and sample i_rdata",
      "cycle": "t",
      "stage": "IF"
    },
    {
      "action": "Decode and compute ALU or branch or target or effective address",
      "cycle": "t+1",
      "stage": "ID_EX"
    },
    {
      "action": "Perform load/store signaling and writeback and retire",
      "cycle": "t+2",
      "stage": "MEM_WB"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": "i_valid",
  "rtl_contract.sample_condition": "1",
  "timing.latency_budget": {
    "branch_resolution_stage": "ID_EX",
    "fence_extra_cycles": 1,
    "instruction_retire_cycles": 3
  }
}

Locked SSOT YAML excerpt (rv32i_min/yaml/rv32i_min.ssot.yaml):
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
  - function_model.transactions.FM_FETCH
  - function_model.transactions.FM_BRANCH
  - function_model.transactions.FM_JUMP
  - cycle_model.pipeline
  - io_list.interfaces.instr_bus
  source_sections: &id001
  - function_model
  - cycle_model
  - io_list
  function_model_refs:
  - function_model.transactions.FM_FETCH
  - function_model.transactions.FM_BRANCH
  - function_model.transactions.FM_JUMP
  - function_model.transactions.FM_SYSTEM
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.handshake_rules
  ssot_refs:
  - io_list.interfaces.instr_bus
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
  - cycle_model.pipeline
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
  feature_refs:
  - features
  description: Decode/execute stage including ALU, branch compare, immediate decode, and control
  register_refs:
  - registers.register_list
- name: rv32i_min_memwb
  file: rtl/rv32i_min_memwb.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - function_model.transactions.FM_LOAD
  - function_model.transactions.FM_STORE
  - cycle_model.pipeline
  - error_handling
  source_sections:
  - function_model
  - cycle_model
  - error_handling
  - dataflow
  function_model_refs:
  - function_model.transactions.FM_LOAD
  - function_model.transactions.FM_STORE
  cycle_model_refs:
  - cycle_model.pipeline
  dataflow_refs:
  - dataflow
  description: Load/store datapath, byte-enable application, sign or zero extension, and writeback
- name: rv32i_min_regfile
  file: rtl/rv32i_min_regfile.sv
  ownership: manifest
  ssot_gen: true
  implements:
  - function_model.state_variables.regfile
  - function_model.invariants
  source_sections: &id002
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
  - integration.connections
  source_sections:
  - function_model
  - cycle_model
  - dataflow
  - rtl_contract
  - integration
  - decomposition
  - test_requirements
  function_model_refs:
  - function_model.transactions
  - function_model.state_variables
  - function_model.invariants
  - function_model.transactions.FM_ALU
  - function_model.transactions.FM_BRANCH
  - function_model.transactions.FM_JUMP
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.handshake_rules
  - cycle_model.ordering
  dataflow_refs:
  - dataflow
  decomposition_refs:
  - decomposition.units
  - decomposition
  description: Top behavioral owner integrating IF, ID_EX, MEM_WB, and architectural retirement
  test_refs:
  - test_requirements
- name: rv32i_min
  file: rtl/rv32i_min.sv
  ownership: manifest
  ssot_gen: true
  wiring_only: true
  implements:
  - io_list
  - integration.connections
  source_sections: &id003
  - io_list
  - integration
  ssot_refs:
  - io_list
  - integration.connections
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
    - test_requirements.scenarios.SC06
  - id: execute
    kind: control/datapath
    source_refs:
    - function_model.transactions.FM_ALU
    - function_model.transactions.FM_BRANCH
    - function_model.transactions.FM_JUMP
    rtl_candidates:
    - rv32i_min_idex
    verification_impact:
    - test_requirements.scenarios.SC07
    - test_requirements.scenarios.SC08
    - test_requirements.scenarios.SC09
  - id: memory_writeback
    kind: datapath
    source_refs:
    - function_model.transactions.FM_LOAD
    - function_model.transactions.FM_STORE
    rtl_candidates:
    - rv32i_min_memwb
    verification_impact:
    - test_requirements.scenarios.SC10
    - test_requirements.scenarios.SC11
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
    - features
  - module: rv32i_min_memwb
    file: rtl/rv32i_min_memwb.sv
    responsibility: Load/store datapath, byte-enable application, sign or zero extension, and writeback
    source_sections:
    - function_model
    - cycle_model
    - error_handling
    - dataflow
  - module: rv32i_min_regfile
    file: rtl/rv32i_min_regfile.sv
    responsibility: 32x32 register file with hard-wired x0 behavior
    source_sections: *id002
  - module: rv32i_min_core
    file: rtl/rv32i_min_core.sv
    responsibility: Top behavioral owner integrating IF, ID_EX, MEM_WB, and architectural retirement
    source_sections:
    - function_model
    - cycle_model
    - dataflow
    - rtl_contract
    - integration
    - decomposition
  - module: rv32i_min
    file: rtl/rv32i_min.sv
    responsibility: Top-level integration module matching SSOT top_module
    source_sections: *id003
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
    clock_domain: clk
    reset_domain: rst_n
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
    - name: alu_result
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''alu_result'' (repair_ssot_schema rule_expr_completeness pass; advisory: TB
        drives this signal from FL transaction intent).'
    - name: branch_imm
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''branch_imm'' (repair_ssot_schema rule_expr_completeness pass; advisory: TB
        drives this signal from FL transaction intent).'
    - name: branch_taken
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''branch_taken'' (repair_ssot_schema rule_expr_completeness pass; advisory:
        TB drives this signal from FL transaction intent).'
    - name: illegal_shamt
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''illegal_shamt'' (repair_ssot_schema rule_expr_completeness pass; advisory:
        TB drives this signal from FL transaction intent).'
    - name: imm
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''imm'' (repair_ssot_schema rule_expr_completeness pass; advisory: TB drives
        this signal from FL transaction intent).'
    - name: is_ebreak
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''is_ebreak'' (repair_ssot_schema rule_expr_completeness pass; advisory: TB
        drives this signal from FL transaction intent).'
    - name: is_ecall
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''is_ecall'' (repair_ssot_schema rule_expr_completeness pass; advisory: TB drives
        this signal from FL transaction intent).'
    - name: is_jalr
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''is_jalr'' (repair_ssot_schema rule_expr_completeness pass; advisory: TB drives
        this signal from FL transaction intent).'
    - name: is_store
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''is_store'' (repair_ssot_schema rule_expr_completeness pass; advisory: TB drives
        this signal from FL transaction intent).'
    - name: load_data_ext
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''load_data_ext'' (repair_ssot_schema rule_expr_completeness pass; advisory:
        TB drives this signal from FL transaction intent).'
    - name: misaligned_access
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''misaligned_access'' (repair_ssot_schema rule_expr_completeness pass; advisory:
        TB drives this signal from FL transaction intent).'
    - name: rs1
      width: 1
      direction: input
      description: 'Auto-derived 1-bit input from rule expression ''rs1'' (repair_ssot_schema rule_expr_completeness pass; advisory: TB drives
        this signal from FL transaction intent).'
    protocol:
      acceptance: Request is sampled each cycle where i_valid is 1.
      stability: i_addr remains stable for the active cycle when i_valid is 1.
      response: i_rdata is sampled on rising edge with one-cycle registered memory model.
  - name: data_bus
    type: custom_sync
    role: master
    description: Synchronous data load or store bus
    clock_domain: clk
    reset_domain: rst_n
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
      description: Store enable
    - name: d_be
      width: 4
      direction: output
      description: Byte enable
    - name: d_valid
      width: 1
      direction: output
      description: Data request valid
    protocol:
      acceptance: Transaction is sampled each cycle where d_valid is 1.
      stability: d_addr, d_we, d_be, and d_wdata (for stores) remain stable for the active cycle.
      response: d_rdata sampled on rising edge for loads.
  - name: exception
    type: custom
    role: output
    description: One-cycle exception strobe
    clock_domain: clk
    reset_domain: rst_n
    ports:
    - name: excpt_o
      width: 1
      direction: output
      description: Exception pulse
    protocol:
      acceptance: Transfer acceptance follows the declared valid/ready or protocol phase rule.
      stability: Payload/control fields remain stable until accepted.
      response: Observable response timing follows cycle_model latency and ordering.
features:
- name: RV32I_37_instruction_support
  trigger: Legal RV32I opcode in required 37-mnemonic subset
  datapath: IF fetches 32-bit instruction, ID_EX decodes and executes, MEM_WB performs memory and commit
  control: In-order single-issue IF/ID_EX/MEM_WB sequencing
  output: Architectural pc and regfile updates with load-store bus traffic
- name: x0_hardwired_zero
  trigger: Any writeback where rd equals x0
  datapath: Write is suppressed in regfile block
  control: Commit masks x0 writes
  output: x0 reads as zero always
- name: exception_pulse_profile
  trigger: ECALL, EBREAK, misaligned data access, or illegal shift-immediate encoding
  datapath: Faulting instructions do not commit architectural updates
  control: Single-cycle excpt_o pulse
  output: excpt_o pulse with defined pc behavior
dataflow:
  instruction_path:
    source: Instruction memory
    sequence: pc -> i_addr and i_valid -> i_rdata -> decode
  execute_path:
    source: regfile and immediate decoder
    sequence: decode -> ALU or compare or target generation
  memory_path:
    load: effective_addr -> d_addr and d_valid and d_we=0 -> d_rdata -> extension -> wb
    store: effective_addr and rs2 -> d_addr and d_wdata and d_be and d_we=1 and d_valid=1
  commit_path:
    sequence: wb select -> write rd if rd != 0 -> update pc
function_model:
  purpose: Cycle-independent RV32I architectural contract for ISS-style equivalence and scoreboard comparison.
  state_variables:
  - name: pc
    source: architectural
    reset: 0
    description: Program counter
  - name: regfile
    source: architectural
    reset: 0
    description: 32x32 register file with x0 immutable zero
  - name: excpt_o
    source: architectural_output
    reset: 0
    description: One-cycle exception pulse
  transactions:
  - id: FM_FETCH
    name: fetch_and_default_advance
    preconditions:
    - pc % 4 == 0
    inputs:
    - pc
    - i_rdata
    outputs:
    - decoded instruction fields available to execute stage
    - default next_pc equals pc plus 4
    side_effects:
    - pc advances by 4 when no control transfer or fault blocks retirement
    output_rules: []
    state_updates:
    - name: next_pc
      expr: pc + 4
      width: 32
      description: Moved from output_rules because this rule updates internal architectural state, not a declared output port.
  - id: FM_ALU
    name: alu_and_immediate_ops
    preconditions:
    - opcode_class == 0
    inputs:
    - rs1
    - rs2
    - imm
    - funct3
    - funct7
    outputs:
    - rd receives computed 32-bit result
    side_effects:
    - regfile writeback occurs when rd != 0
    error_cases:
    - condition: illegal_shamt
      result: excpt_o pulse and no retirement
    output_rules: []
    state_updates:
    - name: wb_data
      expr: alu_result & ((1 << 32) - 1)
      width: 32
      description: Moved from output_rules because this rule updates internal architectural state, not a declared output port.
  - id: FM_BRANCH
    name: conditional_branches
    preconditions:
    - is_branch
    inputs:
    - pc
    - branch_taken
    - branch_imm
    outputs:
    - pc becomes branch target if taken else pc plus 4
    side_effects:
    - no register writeback
    output_rules: []
    state_updates:
    - name: next_pc
      expr: (pc + branch_imm) if branch_taken else (pc + 4)
      width: 32
      description: Moved from output_rules because this rule updates internal architectural state, not a declared output port.
  - id: FM_JUMP
    name: jal_and_jalr
    preconditions:
    - is_jump
    inputs:
    - pc
    - rs1
    - imm
    - is_jalr
    outputs:
    - link register gets old pc plus 4 when rd != 0
    - jump target selected by JAL or JALR rule
    side_effects:
    - pc redirected to computed target
    output_rules: []
    state_updates:
    - name: next_pc
      expr: ((rs1 + imm) & ~1) if is_jalr else (pc + imm)
      width: 32
      description: Moved from output_rules because this rule updates internal architectural state, not a declared output port.
  - id: FM_LOAD
    name: loads_with_extension
    preconditions:
    - is_load
    inputs:
    - d_rdata
    - funct3
    - effective_addr
    outputs:
    - LB and LH sign-extend
    - LBU and LHU zero-extend
    - LW returns full 32-bit
    side_effects:
    - writeback to rd when rd != 0
    error_cases:
    - condition: misaligned_access
      result: excpt_o pulse and no retirement
    output_rules: []
    state_updates:
    - name: wb_data
      expr: load_data_ext & ((1 << 32) - 1)
      width: 32
      description: Moved from output_rules because this rule updates internal architectural state, not a declared output port.
  - id: FM_STORE
    name: stores_with_byte_enable
    preconditions:
    - is_store
    inputs:
    - rs2
    - funct3
    - effective_addr
    outputs:
    - d_we equals 1 and d_be reflects width and alignment
    side_effects:
    - no register writeback
    error_cases:
    - condition: misaligned_access
      result: excpt_o pulse and no retirement
    output_rules:
    - name: store_valid
      expr: 1 if (is_store and (not misaligned_access)) else 0
      width: 1
      port: d_valid
  - id: FM_SYSTEM
    name: fence_ecall_ebreak
    preconditions:
    - is_system
    inputs:
    - is_fence
    - is_ecall
    - is_ebreak
    outputs:
    - FENCE inserts one bubble
    - ECALL and EBREAK pulse excpt_o
    side_effects:
    - ECALL and EBREAK advance pc by 4
    output_rules:
    - name: exception_pulse
      expr: 1 if (is_ecall or is_ebreak or illegal_shamt or misaligned_access) else 0
      width: 1
      port: excpt_o
  invariants:
  - regfile_x0 == 0
  - misaligned_access implies no_retire
  - jalr_target_lsb == 0
cycle_model:
  purpose: Clocked IF/ID_EX/MEM_WB contract with synchronous registered bus behavior.
  executable: pymtl3
  backend_policy: Use PyMTL3 shell for cycle accounting while function_model remains architectural oracle.
  clock: clk
  reset:
    assertion: rst_n low asynchronously clears architectural and pipeline state
    deassertion: state usable on first rising edge after synchronized deassertion
  latency:
    fetch_to_decode:
      min_cycles: 1
      max_cycles: 1
      description: IF to ID_EX transfer
    alu_ops_retire:
      min_cycles: 3
      max_cycles: 3
      description: IF to ID_EX to MEM_WB retire path
    load_retire:
      min_cycles: 3
      max_cycles: 3
      description: Single-cycle synchronous data return assumption
    store_issue:
      min_cycles: 2
      max_cycles: 3
      description: Address and write data presented by MEM stage
    fence_penalty:
      min_cycles: 1
      max_cycles: 1
      description: Required one-cycle bubble
  handshake_rules:
  - signal: i_valid
    rule: i_valid == 1 implies i_addr is stable in the cycle
  - signal: d_valid
    rule: d_valid == 1 implies d_addr and d_we and d_be are stable in the cycle
  - signal: d_we
    rule: d_we == 1 indicates store and d_we == 0 indicates load
  - signal: excpt_o
    rule: excpt_o pulses for exactly one cycle per triggering instruction
  pipeline:
  - stage: IF
    cycle: t
    action: Drive i_addr from pc and sample i_rdata
  - stage: ID_EX
    cycle: t+1
    action: Decode and compute ALU or branch or target or effective address
  - stage: MEM_WB
    cycle: t+2
    action: Perform load/store signaling and writeback and retire
  ordering:
  - Retirement is in program order with at most one commit per cycle
  - Faulting misaligned or illegal instruction does not retire
  - Store side effects occur only on aligned non-faulting stores
  backpressure:
  - No explicit ready channels; interfaces are sampled synchronously each cycle
  observability:
  - Every function_model transaction maps to IF or ID_EX or MEM_WB stage
  performance:
    frequency_mhz: 100
    throughput:
      sustained_beats_per_cycle: 1
      condition: synchronous memory response each cycle
    outstanding:
      max: 1
      description: single in-flight architectural operation
    depth:
      pipeline_stages: 3
      queue_depth: 1
      description: fixed three-stage in-order pipe
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
    note: Architectural register file representation only; no CSR/MMIO map
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
      description: Register value; x0 writes ignored and reads return zero
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
    description: IF/ID pipeline register
  - name: id_ex_reg
    type: register
    depth: 1
    width: 192
    read_ports: 1
    write_ports: 1
    latency: 0
    description: ID/EX pipeline register
  - name: ex_mem_wb_reg
    type: register
    depth: 1
    width: 160
    read_ports: 1
    write_ports: 1
    latency: 0
    description: EX/MEM_WB pipeline register
  note: External instruction and data memories are outside IP boundary
interrupts:
  sources: []
  output:
    signal: excpt_o
    polarity: active_high
    type: pulse
    description: Exception strobe only; no interrupt controller
fsm:
  control:
    states:
    - RESET
    - RUN
    - FENCE_BUBBLE
    transitions:
    - from: RESET
      to: RUN
      condition: rst_n_deasserted
    - from: RUN
      to: FENCE_BUBBLE
      condition: decoded_fence
    - from: FENCE_BUBBLE
      to: RUN
      condition: bubble_done
    note: Pipeline streams in RUN; FENCE inserts exactly one bubble
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
    ipc_sustained_notes: Single issue in-order no speculation
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
  - name: true
    description: Normal execution
  - name: RESET
    description: Reset asserted and architectural state cleared
  clock_gating: Not implemented in minimal profile
  upf_required: false
security:
  classification: non-secure minimal compute core
  assets:
  - Architectural register state
  - Program counter control flow integrity
  - Load/store data correctness
  threat_model:
  - Malformed instruction encodings causing undefined transitions
  - Misaligned memory accesses corrupting architectural state
  - x0 corruption by unintended writeback
  assumptions:
  - Trusted instruction and data memory in this smoke profile
  - No privilege separation and no PMP/MMU
  privilege_model: System-level protection is owned by integrator
error_handling:
  error_sources:
  - id: ERR_MISALIGNED_DATA
    condition: misaligned_data_access
    architectural_effect: pulse excpt_o for one cycle and block retirement
  - id: ERR_ILLEGAL_SHIFT_IMM
    condition: illegal_shamt
    architectural_effect: pulse excpt_o for one cycle and block retirement
  - id: ERR_ECALL_EBREAK
    condition: is_ecall or is_ebreak
    architectural_effect: pulse excpt_o for one cycle and advance pc by 4
  propagation:
  - excpt_o asserted for one cycle on detection edge
  recovery:
  - Continue fetch on next instruction after pulse according to control policy
debug_observability:
  waveform_must_probe:
  - pc
  - instr_word
  - decoded_opcode
  - rs1_idx
  - rs2_idx
  - rd_idx
  - regfile_wen
  - regfile_wdata
  - d_addr
  - d_we
  - d_be
  - d_valid
  - d_wdata
  - d_rdata
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
  - excpt_o
integration:
  bus_attachment:
    instruction_bus: custom synchronous interface i_*
    data_bus: custom synchronous interface d_*
  dependencies:
  - External instruction memory returns i_rdata for i_addr every cycle
  - External data memory observes d_valid and d_we and d_be and provides d_rdata for loads
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
  controllability: Primary inputs clk, rst_n, i_rdata, d_rdata and stimulus provide smoke controllability
  observability: Primary outputs and declared waveform probes provide observability
  mbist: Not applicable; no internal SRAM macros
  mbist_required: false
synthesis:
  dialect: systemverilog_2012
  constraints:
  - Single clock clk with async active-low reset rst_n
  - No inferred latches
  - Preserve explicit three-stage pipeline boundaries
  required_outputs:
  - gate-level netlist
  - timing report
  - area report
  top_module: rv32i_min
pnr:
  utilization_pct: 60
  aspect_ratio: 1.0
  core_space_um: 2.0
  global_density: 0.65
  io_layers:
    horizontal: met3
    vertical: met2
  cts_buf_list:
  - sky130_fd_sc_hd__clkbuf_4
  - sky130_fd_sc_hd__clkbuf_8
  routing:
    signal_layers:
      min: met1
      max: met5
    drc_waivers: []
coding_rules:
  verilog_style: systemverilog_2012
  file_extension: .sv
  parameter_header: rtl/rv32i_min_param.vh
  conventions:
  - Use nonblocking assignments in sequential blocks
  - Use blocking assignments in combinational blocks
  - x0 register writes must be explicitly masked
  - No speculative execution logic
  - No extension opcodes beyond required RV32I subset
reuse_modules: []
custom:
  assumptions:
  - Instruction and data memory respond synchronously without ready or stall handshake
  - No interrupt or trap vector subsystem
  run_context: Triple-LLM smoke fixture for ssot to audit comparison
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
    stimulus: Assert rst_n low then release and observe first active cycle
    expected: pc and regfile and excpt_o reset values match function_model and rtl_contract
    checker: Reset checker compares observed state against function_model.reset and cycle_model.reset
    coverage:
    - function_model
    - cycle_model.reset
  - id: SC02
    name: opcode sweep 37
    stimulus: Execute all 37 required RV32I mnemonics with random and edge operands
    expected: pc and regfile trajectory match reference model for each opcode
    checker: ISS scoreboard compares per-instruction commit results
    coverage:
    - function_model.transactions
  - id: SC03
    name: branch taken and untaken
    stimulus: Drive BEQ BNE BLT BGE BLTU BGEU in both taken and untaken forms
    expected: next pc behavior matches signed and unsigned branch rules
    checker: branch checker compares target and fall-through path
    coverage:
    - function_model.transactions.FM_BRANCH
    - cycle_model.ordering
  - id: SC04
    name: load store extension and byte enable
    stimulus: Exercise LB LH LW LBU LHU and SB SH SW across address offsets
    expected: extension and d_be patterns match function_model contract
    checker: memory monitor and scoreboard
    coverage:
    - function_model.transactions.FM_LOAD
    - function_model.transactions.FM_STORE
  - id: SC05
    name: x0 immutable
    stimulus: Attempt writes to rd zero from ALU load jump link paths
    expected: regfile x0 remains zero
    checker: architectural invariant checker
    coverage:
    - function_model.invariants
  - id: SC06
    name: FM_FETCH transaction
    stimulus: Legal fetch flow with aligned pc
    expected: next_pc default rule and fetch outputs hold
    checker: transaction scoreboard
    coverage:
    - function_model.transactions.FM_FETCH
  - id: SC07
    name: FM_ALU transaction
    stimulus: OP and OP_IMM with random and edge operands
    expected: wb_data_alu equals model result
    checker: transaction scoreboard
    coverage:
    - function_model.transactions.FM_ALU
  - id: SC08
    name: FM_BRANCH transaction
    stimulus: Branch opcode sweep with signed and unsigned boundaries
    expected: branch_next_pc rule matches taken and untaken outcomes
    checker: transaction scoreboard
    coverage:
    - function_model.transactions.FM_BRANCH
  - id: SC09
    name: FM_JUMP transaction
    stimulus: JAL and JALR with varied imm and rd values
    expected: link writeback and jalr lsb clear behavior match model
    checker: transaction scoreboard
    coverage:
    - function_model.transactions.FM_JUMP
  - id: SC10
    name: FM_LOAD transaction
    stimulus: Load widths and signed unsigned variants with aligned addresses
    expected: wb_data_load rule and extension behavior match model
    checker: transaction scoreboard
    coverage:
    - function_model.transactions.FM_LOAD
  - id: SC11
    name: FM_STORE transaction
    stimulus: Store widths and offsets for byte enables
    expected: d_valid and d_be and d_we behavior match model
    checker: transaction scoreboard
    coverage:
    - function_model.transactions.FM_STORE
  - id: SC12
    name: FM_SYSTEM transaction
    stimulus: FENCE ECALL EBREAK and illegal shift immediate and misaligned accesses
    expected: exception pulse and fence bubble rules match model
    checker: transaction scoreboard
    coverage:
    - function_model.transactions.FM_SYSTEM
    - error_handling
  scoreboard_checks: 20
  coverage_goals:
    function:
      target_pct: 100
      model: function_model
      description: Behavioral coverage across all required RV32I architectural transactions
      bins:
      - id: FCOV_OPCODE_37
        source_ref: function_model.transactions
        class: opcode
        description: All 37 required mnemonics observed
      - id: FCOV_BRANCH_TAKEN_UNTAKEN
        source_ref: function_model.transactions.FM_BRANCH
        class: branch
        description: Taken and untaken for each branch mnemonic
      - id: FCOV_LOAD_SIGN_ZERO_EXT
        source_ref: function_model.transactions.FM_LOAD
        class: data_transform
        description: LB and LH sign-extension and LBU and LHU zero-extension
      - id: FCOV_STORE_BYTE_ENABLE
        source_ref: function_model.transactions.FM_STORE
        class: byte_enable
        description: Store byte enable patterns for SB and SH and SW
      - id: FCOV_X0_IMMUTABLE
        source_ref: function_model.invariants
        class: invariant
        description: Writes to x0 are ignored
      - id: FCOV_JAL_JALR_LINK
        source_ref: function_model.transactions.FM_JUMP
        class: jump_link
        description: Link writeback and jalr bit0 clear
      - id: FCOV_MISALIGNED_FAULT
        source_ref: function_model.transactions
        class: fault
        description: Misaligned load or store raises pulse and no retirement
      - id: FCOV_ECALL_EBREAK
        source_ref: function_model.transactions.FM_SYSTEM
        class: system
        description: ECALL and EBREAK pulse with pc advance
    cycle:
      target_pct: 100
      model: cycle_model
      description: Pipeline and protocol timing coverage
      bins:
      - id: CCOV_IF_ID_EX_MEM_WB
        source_ref: cycle_model.pipeline
        class: pipeline_stage
        description: Stage occupancy across IF ID_EX MEM_WB
      - id: CCOV_SYNC_BUS_RULES
        source_ref: cycle_model.handshake_rules
        class: handshake
        description: Synchronous bus stability and sampling rules
      - id: CCOV_FENCE_BUBBLE
        source_ref: fsm.control.transitions
        class: bubble
        description: One-cycle fence bubble transition
      - id: CCOV_EXCEPTION_ONE_SHOT
        source_ref: cycle_model.handshake_rules
        class: pulse
        description: excpt_o one-cycle pulse behavior
    code: line >= 90%, branch >= 85%
    scenario: All SSOT scenarios pass with executable cocotb/pyuvm checkers and FL-vs-RTL scoreboard evidence
quality_gates:
  ssot:
    pass: check_ssot_disk.sh exits 0 and ATLAS SSOT progress is fully approved
    evidence:
    - check_ssot_disk.sh PASS
    - ATLAS /api/progress ssot all sections approved
  rtl:
    pass: RTL implements function_model and cycle_model and compiles and matches FL scoreboard
    evidence:
    - rtl compile report
    - lint report
    - fl vs rtl scoreboard report
  rtl_gen:
    profile: standard
    pass: All SSOT-derived rtl_gen TODO items close with evidence and no unresolved behavioral ownership gaps
    evidence:
    - rtl/rtl_todo_plan.json
    - rtl/rtl_authoring_provenance.json
    target_scale:
      basis: smoke fixture CPU with explicit behavioral ownership
      source_files_min: 6
      modules_min: 6
      procedural_blocks_min: 8
      state_updates_min: 8
      depth_score_min: 20
      logic_modules_min: 4
      behavior_owner_logic_modules_min: 4
    target_scale_waiver:
      approved: false
      reason: ''
      owner: ''
  dv:
    pass: Every SSOT test_requirements scenario has an executable checker and FL-vs-RTL equivalence goal
    evidence:
    - verify/equivalence_goals.json
    - sim/scoreboard_events.jsonl
    - tb/cocotb tests
    - scenario implementation map
  coverage:
    pass: function and cycle coverage goals close or have approved SSOT waivers
    evidence:
    - cov/coverage.json
    - sim/coverage_report.md
  eda:
    pass: synthesis and sta meet declared timing or have approved waiver
    evidence:
    - syn report
    - sta report
  signoff:
    pass: SSOT, FL/equivalence, RTL, lint, DV, sim, coverage, and EDA gates pass with fresh artifacts
    evidence:
    - ATLAS progress signoff PASS
traceability:
  yaml_to_output:
  - yaml: top_module.name
    output: module naming across rtl files
  - yaml: parameters
    output: rtl/rv32i_min_param.vh and consuming rtl modules
  - yaml: io_list.interfaces
    output: rtl/rv32i_min.sv top ports and bus wiring
  - yaml: function_model
    output: rtl behavior and functional reference model checks
  - yaml: cycle_model
    output: pipeline timing behavior and protocol checks
  - yaml: registers.register_list
    output: architectural register model and scoreboard visibility
  - yaml: error_handling
    output: fault path logic and negative tests
  - yaml: test_requirements.scenarios
    output: tb scenarios and coverage bins
  - yaml: function_model/cycle_model/test_requirements
    output: verify/equivalence_goals.json and FL-vs-RTL scoreboard contracts
  - yaml: timing
    output: STA constraints and latency pass/fail criteria
  - yaml: security
    output: Threat mitigations and negative tests
  - yaml: debug_observability
    output: VCD probes and sim_debug inspection
  - yaml: quality_gates
    output: ATLAS progress/signoff criteria
workflow_todos:
  fl-model-gen:
  - id: FL_RV32I_REF_MODEL
    content: Implement RV32I functional reference trajectory model
    detail: Build executable model from function_model transactions and invariants for all 37 opcodes
    criteria:
    - Model predicts pc and regfile state per committed instruction
    - Error cases match function_model error_cases
    source_refs:
    - function_model
    - error_handling
    owner_module: rv32i_min_core
    owner_file: rtl/rv32i_min_core.sv
    priority: high
    required: true
  rtl-gen:
  - id: RTL_IF_STAGE
    content: Implement IF stage request and pc sequencing
    detail: Drive i_addr and i_valid and IF register updates according to cycle_model IF stage and FM_FETCH
    criteria:
    - i_valid and i_addr comply with handshake_rules
    - next_pc logic matches FM_FETCH FM_BRANCH FM_JUMP
    source_refs:
    - function_model.transactions.FM_FETCH
    - function_model.transactions.FM_BRANCH
    - function_model.transactions.FM_JUMP
    - cycle_model.pipeline
    - cycle_model.handshake_rules
    owner_module: rv32i_min_if
    owner_file: rtl/rv32i_min_if.sv
    priority: high
    required: true
  - id: RTL_IDEX_STAGE
    content: Implement decode execute and system instruction control
    detail: Decode RV32I subset and produce ALU compare jump target and system behavior including FENCE bubble and illegal shamt detect
    criteria:
    - All 37 opcodes decode to declared function_model transaction classes
    - Illegal shamt triggers exception path with no retirement
    source_refs:
    - function_model.transactions.FM_ALU
    - function_model.transactions.FM_BRANCH
    - function_model.transactions.FM_JUMP
    - function_model.transactions.FM_SYSTEM
    - fsm.control
    owner_module: rv32i_min_idex
    owner_file: rtl/rv32i_min_idex.sv
    priority: high
    required: true
  - id: RTL_MEMWB_STAGE
    content: Implement load store formatting and writeback commit gates
    detail: Generate d_addr d_we d_be d_wdata and load extension paths and retirement gating on faults
    criteria:
    - Store byte enables align with SB SH SW rules
    - LB LH LBU LHU LW results match extension policy
    - Misaligned access blocks retirement
    source_refs:
    - function_model.transactions.FM_LOAD
    - function_model.transactions.FM_STORE
   
... <truncated 3482 chars>

Base rtl-gen contract:
Prepare rtl-gen for rv32i_min using only rv32i_min/yaml/rv32i_min.ssot.yaml and rv32i_min/rtl/rtl_todo_plan.json, rv32i_min/rtl/rtl_authoring_plan.json, and packets under rv32i_min/rtl/authoring_packets. Return exactly one JSON object and nothing else. Success schema: {"files":[{"path":"rv32i_min/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"},{"path":"rv32i_min/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"},{"path":"rv32i_min/list/rv32i_min.f","kind":"filelist","content":"<filelist>"}]}. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=10c4be796cd0d74fe7574b57a60327afb02cfecb9c550522c1e714ec8a08eb01. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

Authoring plan overview:
{
  "execution_policy": {
    "allowed_draft_work": [
      "Author module RTL from SSOT-derived TODO packets.",
      "Add tests, vectors, assertions, reports, and repair RTL under LLM-editable surfaces.",
      "Leave unresolved locked-truth decisions as human_gate/change-request records instead of changing SSOT authority."
    ],
    "blocked_by_llm_work": [
      {
        "gate_kind": "static_rtl_evidence",
        "owner_module": "rv32i_min",
        "reason": "2 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "top_input_consumption_evidence",
        "owner_module": "rv32i_min",
        "reason": "10 top input consumption issue(s) remain. alu_result: RTL top input is connected only to child ports without declared input/inout direction; branch_imm: RTL top input is connected only to child ports without declared input/inout direction; branch_taken: RTL top input is connected only to child ports without declared input/inout direction",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
        "status": "open",
        "task_id": "RTL-0012"
      },
      {
        "gate_kind": "manifest_port_connection_evidence",
        "owner_module": "rv32i_min",
        "reason": "5 manifest port connection issue(s) remain. rv32i_min_if: Reachable child instance has missing or empty named port connections; rv32i_min_idex: Reachable child instance has missing or empty named port connections; rv32i_min_memwb: Reachable child instance has missing or empty named port connections",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_port_connection_evidence",
        "status": "open",
        "task_id": "RTL-0014"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "rv32i_min",
        "reason": "27 manifest signal-flow issue(s) remain. rv32i_min_idex: alu_result: Named port-map entry targets a port not declared by the child module; rv32i_min_idex: branch_imm: Named port-map entry targets a port not declared by the child module; rv32i_min_idex: branch_taken: Named port-map entry targets a port not declared by the child module",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "status": "open",
        "task_id": "RTL-0015"
      }
    ],
    "blocked_by_locked_truth": [
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "owner_module": "rv32i_min",
        "reason": "8 SSOT connection contract issue(s) remain. rv32i_min_if: RTL named port-map expression does not match SSOT connection signal terms; rv32i_min_if: RTL named port-map expression does not match SSOT connection signal terms; rv32i_min_memwb: RTL named port-map expression does not match SSOT connection signal terms",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      }
    ],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "dut_compile",
        "owner_module": "rv32i_min",
        "reason": "DUT compile artifact is not clean.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "rv32i_min",
        "reason": "DUT lint artifact is not clean.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "rv32i_min",
        "reason": "11 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 10,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {
      "path": "rtl/connection_contract_suggestions.json",
      "rule": "Suggestions are emitted only when production connection contracts are missing.",
      "sample_rows": [],
      "summary": {
        "applied_to_ssot": false,
        "pending_review": 0,
        "status": "not_required",
        "suggested_rows": 0
      }
    },
    "deferred_human_qa_allowed": true,
    "draft_allowed": true,
    "gate_status": "fail",
    "hard_blockers": [],
    "open_required_todos": 12,
    "pass_allowed": false,
    "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
    "stop_conditions": [
      "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
      "Do not claim rtl-gen PASS while pass_allowed is false.",
      "Do not sign off top integration while required connection contracts are missing."
    ],
    "tool_evidence_plan": [
      {
        "artifact": "rtl/rtl_compile.json",
        "artifacts": [
          "rv32i_min/rtl/rtl_compile.json",
          "rv32i_min/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py rv32i_min --top rv32i_min --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py rv32i_min --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "rv32i_min/list/rv32i_min.f covers the current DUT RTL sources."
        ],
        "reason": "DUT compile artifact is not clean.",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "stage_sequence": [
          "ssot-rtl",
          "dut_compile"
        ],
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "artifact": "lint/dut_lint.json",
        "artifacts": [
          "rv32i_min/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py rv32i_min --top rv32i_min",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py rv32i_min --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "rv32i_min/list/rv32i_min.f covers the current DUT RTL/header sources."
        ],
        "reason": "DUT lint artifact is not clean.",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "stage_sequence": [
          "lint",
          "dut_lint"
        ],
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "artifact": "rtl/rtl_todo_plan.json",
        "artifacts": [
          "rv32i_min/rtl/rtl_todo_plan.json",
          "rv32i_min/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py rv32i_min --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "11 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ]
  },
  "ip": "rv32i_min",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_if__function_model.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/rv32i_min_if.sv",
      "owner_module": "rv32i_min_if",
      "packet_id": "module__rv32i_min_if__function_model",
      "required_count": 35,
      "status_counts": {
        "open": 2,
        "pass": 33
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/unowned_tasks.json",
      "kind": "unowned",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "",
      "owner_module": "",
      "packet_id": "unowned_tasks",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 9,
      "status_counts": {
        "open": 4,
        "pass": 5
      }
    },
    {
      "human_locked_open_count": 1,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 1,
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 4,
      "status_counts": {
        "open": 1,
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 3,
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 3,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_if__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_if.sv",
      "owner_module": "rv32i_min_if",
      "packet_id": "module__rv32i_min_if__cycle_model",
      "required_count": 12,
      "status_counts": {
        "pass": 12
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_if__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_if.sv",
      "owner_module": "rv32i_min_if",
      "packet_id": "module__rv32i_min_if__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_if__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_if.sv",
      "owner_module": "rv32i_min_if",
      "packet_id": "module__rv32i_min_if__io_list",
      "required_count": 24,
      "status_counts": {
        "pass": 24
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_if__memory.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_if.sv",
      "owner_module": "rv32i_min_if",
      "packet_id": "module__rv32i_min_if__memory",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_if__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_if.sv",
      "owner_module": "rv32i_min_if",
      "packet_id": "module__rv32i_min_if__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_idex.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_idex.sv",
      "owner_module": "rv32i_min_idex",
      "packet_id": "module__rv32i_min_idex",
      "required_count": 26,
      "status_counts": {
        "pass": 26
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_memwb.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_memwb.sv",
      "owner_module": "rv32i_min_memwb",
      "packet_id": "module__rv32i_min_memwb",
      "required_count": 23,
      "status_counts": {
        "pass": 23
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_regfile.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_regfile.sv",
      "owner_module": "rv32i_min_regfile",
      "packet_id": "module__rv32i_min_regfile",
      "required_count": 6,
      "status_counts": {
        "pass": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_core.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "packet_id": "module__rv32i_min_core",
      "required_count": 28,
      "status_counts": {
        "pass": 28
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "packet_id": "module__rv32i_min",
      "required_count": 11,
      "status_counts": {
        "pass": 11
      }
    }
  ],
  "policy": {
    "dynamic_task_rule": "Use every required task in this file as the authoritative RTL implementation/evidence ledger. Expose Atlas/UI TodoTracker items as a flat one-to-one projection of this ledger so the existing flat TodoTracker executes one SSOT-derived RTL task at a time.",
    "fixed_template_role": "seed_only",
    "no_orphan_function_level": true,
    "reference_profile_rule": "Optional rtl_reference_profile artifacts are calibration-only scale reports; they must not be copied, transformed, or used as fixed RTL templates.",
    "rtl_gate_todo_rule": "RTL-gen quality gates are first-class rtl_gate.rtl_gen TODOs; compile/lint/static/ownership/owner-logic/placeholder-free/implementation-depth/top-io/top-output-drive/top-input-consumption/hierarchy/port-connection/signal-flow/connection-contract gates must close as TODOs before PASS.",
    "rtl_quality_profile": "standard",
    "rtl_target_scale": {
      "basis": "smoke fixture CPU with explicit behavioral ownership",
      "min_behavior_owner_logic_modules": 4,
      "min_depth_score": 20,
      "min_logic_modules": 4,
      "min_modules": 6,
      "min_procedural_blocks": 8,
      "min_source_files": 6,
      "min_state_updates": 8,
      "policy": "SSOT-locked scale target. It may be calibrated from a reference profile, but rtl-gen must satisfy it through IP-specific SSOT behavior, not by copying reference RTL."
    },
    "rtl_target_scale_waiver": {},
    "single_source_of_truth": "SSOT YAML is the only authority for function_model, cycle_model, RTL ownership, DV plan, and coverage.",
    "ssot_workflow_todo_rule": "workflow_todos.rtl-gen[] entries are first-class downstream tasks; content/detail/criteria must be preserved and satisfied by RTL evidence.",
    "target_scale_rule": "Optional quality_gates.rtl_gen.target_scale is SSOT-locked human policy. It can be calibrated from a reference profile, but it is enforced as generic structural depth evidence, not as copied reference RTL."
  },
  "reference_profile": {},
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 1,
    "human_locked_tasks": 1,
    "llm_actionable_packets": 3,
    "llm_actionable_tasks": 8,
    "max_packet_required_tasks": 35,
    "module_packets": 11,
    "next_llm_packets": [
      "module__rv32i_min_if__function_model",
      "unowned_tasks",
      "rtl_gate_evidence_closure"
    ],
    "packet_task_limit": 48,
    "packets": 15,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 187,
    "sliced_module_packets": 6,
    "target_scale_present": true,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 3,
    "total_tasks": 187,
    "unowned_packets": 1
  },
  "target_scale": {
    "basis": "smoke fixture CPU with explicit behavioral ownership",
    "min_behavior_owner_logic_modules": 4,
    "min_depth_score": 20,
    "min_logic_modules": 4,
    "min_modules": 6,
    "min_procedural_blocks": 8,
    "min_source_files": 6,
    "min_state_updates": 8,
    "policy": "SSOT-locked scale target. It may be calibrated from a reference profile, but rtl-gen must satisfy it through IP-specific SSOT behavior, not by copying reference RTL."
  },
  "todo_plan_sha256": "10c4be796cd0d74fe7574b57a60327afb02cfecb9c550522c1e714ec8a08eb01",
  "top": "rv32i_min",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/rv32i_min.sv):
module rv32i_min #(
    parameter integer XLEN = 32,
    parameter integer RESET_PC = 0,
    parameter integer INST_ALIGN = 4
) (
    input  logic             clk,
    input  logic             rst_n,
    output logic [XLEN-1:0]  i_addr,
    input  logic [XLEN-1:0]  i_rdata,
    output logic             i_valid,
    input  logic             alu_result,
    input  logic             branch_imm,
    input  logic             branch_taken,
    input  logic             illegal_shamt,
    input  logic             imm,
    input  logic             is_ebreak,
    input  logic             is_ecall,
    input  logic             is_jalr,
    input  logic             is_store,
    input  logic             load_data_ext,
    input  logic             misaligned_access,
    input  logic             rs1,
    output logic [XLEN-1:0]  d_addr,
    output logic [XLEN-1:0]  d_wdata,
    input  logic [XLEN-1:0]  d_rdata,
    output logic             d_we,
    output logic [3:0]       d_be,
    output logic             d_valid,
    output logic             excpt_o
);

    logic [XLEN-1:0] if_i_addr;
    logic            if_i_valid;

    logic [XLEN-1:0] mem_d_addr;
    logic [XLEN-1:0] mem_d_wdata;
    logic            mem_d_we;
    logic [3:0]      mem_d_be;
    logic            mem_d_valid;

    logic            core_excpt_o;

    assign i_addr  = if_i_addr;
    assign i_valid = if_i_valid;

    assign d_addr  = mem_d_addr;
    assign d_wdata = mem_d_wdata;
    assign d_we    = mem_d_we;
    assign d_be    = mem_d_be;
    assign d_valid = mem_d_valid;

    assign excpt_o = core_excpt_o;

    rv32i_min_if #(
        .XLEN(XLEN),
        .RESET_PC(RESET_PC),
        .INST_ALIGN(INST_ALIGN)
    ) u_rv32i_min_if (
        .clk(clk),
        .rst_n(rst_n),
        .i_addr(if_i_addr),
        .i_valid(if_i_valid),
        .i_rdata(i_rdata)
    );

    rv32i_min_idex #(
        .XLEN(XLEN)
    ) u_rv32i_min_idex (
        .clk(clk),
        .rst_n(rst_n),
        .alu_result(alu_result),
        .branch_imm(branch_imm),
        .branch_taken(branch_taken),
        .illegal_shamt(illegal_shamt),
        .imm(imm),
        .is_ebreak(is_ebreak),
        .is_ecall(is_ecall),
        .is_jalr(is_jalr),
        .is_store(is_store),
        .load_data_ext(load_data_ext),
        .misaligned_access(misaligned_access),
        .rs1(rs1)
    );

    rv32i_min_memwb #(
        .XLEN(XLEN)
    ) u_rv32i_min_memwb (
        .clk(clk),
        .rst_n(rst_n),
        .d_addr(mem_d_addr),
        .d_wdata(mem_d_wdata),
        .d_rdata(d_rdata),
        .d_we(mem_d_we),
        .d_be(mem_d_be),
        .d_valid(mem_d_valid),
        .misaligned_access(misaligned_access),
        .is_store(is_store),
        .load_data_ext(load_data_ext)
    );

    rv32i_min_regfile #(
        .XLEN(XLEN)
    ) u_rv32i_min_regfile (
        .clk(clk),
        .rst_n(rst_n)
    );

    rv32i_min_core #(
        .XLEN(XLEN),
        .RESET_PC(RESET_PC),
        .INST_ALIGN(INST_ALIGN)
    ) u_rv32i_min_core (
        .clk(clk),
        .rst_n(rst_n),
        .excpt_o(core_excpt_o),
        .alu_result(alu_result),
        .branch_imm(branch_imm),
        .branch_taken(branch_taken),
        .illegal_shamt(illegal_shamt),
        .imm(imm),
        .is_ebreak(is_ebreak),
        .is_ecall(is_ecall),
        .is_jalr(is_jalr),
        .is_store(is_store),
        .load_data_ext(load_data_ext),
        .misaligned_access(misaligned_access),
        .rs1(rs1),
        .i_rdata(i_rdata),
        .d_rdata(d_rdata)
    );

endmodule


Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/rtl_gate_evidence_closure.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 10,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "owner": {
      "file": "rtl/rv32i_min.sv",
      "name": "rv32i_min",
      "refs": [
        "integration",
        "integration.connections",
        "io_list"
      ],
      "wiring_only": true
    },
    "peer_modules": [
      {
        "file": "rtl/rv32i_min_if.sv",
        "name": "rv32i_min_if",
        "wiring_only": false
      },
      {
        "file": "rtl/rv32i_min_idex.sv",
        "name": "rv32i_min_idex",
        "wiring_only": false
      },
      {
        "file": "rtl/rv32i_min_memwb.sv",
        "name": "rv32i_min_memwb",
        "wiring_only": false
      },
      {
        "file": "rtl/rv32i_min_regfile.sv",
        "name": "rv32i_min_regfile",
        "wiring_only": false
      },
      {
        "file": "rtl/rv32i_min_core.sv",
        "name": "rv32i_min_core",
        "wiring_only": false
      },
      {
        "file": "rtl/rv32i_min.sv",
        "name": "rv32i_min",
        "wiring_only": true
      }
    ],
    "quality_profile": "standard",
    "reference_profile": null,
    "ssot_connection_contracts": [
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_if",
        "port": "i_addr",
        "signal": "i_addr",
        "signal_terms": [
          "i_addr"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_if",
        "port": "i_valid",
        "signal": "i_valid",
        "signal_terms": [
          "i_valid"
        ],
        "source_ref": "integration.connections[1]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_if",
        "port": "i_rdata",
        "signal": "i_rdata",
        "signal_terms": [
          "i_rdata"
        ],
        "source_ref": "integration.connections[2]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_memwb",
        "port": "d_addr",
        "signal": "d_addr",
        "signal_terms": [
          "d_addr"
        ],
        "source_ref": "integration.connections[3]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_memwb",
        "port": "d_wdata",
        "signal": "d_wdata",
        "signal_terms": [
          "d_wdata"
        ],
        "source_ref": "integration.connections[4]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_memwb",
        "port": "d_rdata",
        "signal": "d_rdata",
        "signal_terms": [
          "d_rdata"
        ],
        "source_ref": "integration.connections[5]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_memwb",
        "port": "d_we",
        "signal": "d_we",
        "signal_terms": [
          "d_we"
        ],
        "source_ref": "integration.connections[6]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_memwb",
        "port": "d_be",
        "signal": "d_be",
        "signal_terms": [
          "d_be"
        ],
        "source_ref": "integration.connections[7]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_memwb",
        "port": "d_valid",
        "signal": "d_valid",
        "signal_terms": [
          "d_valid"
        ],
        "source_ref": "integration.connections[8]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "rv32i_min_core",
        "port": "excpt_o",
        "signal": "excpt_o",
        "signal_terms": [
          "excpt_o"
        ],
        "source_ref": "integration.connections[9]"
      }
    ],
    "ssot_top_io_contracts": [
      {
        "aliases": [
          "clk"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "clk",
        "source_ref": "io_list.clock_domains[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "rst_n"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "rst_n",
        "source_ref": "io_list.resets[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "i_addr",
          "instr_bus_i_addr"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "i_addr",
        "source_ref": "io_list.interfaces[0].ports[0]",
        "width": "32"
      },
      {
        "aliases": [
          "i_rdata",
          "instr_bus_i_rdata"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "i_rdata",
        "source_ref": "io_list.interfaces[0].ports[1]",
        "width": "32"
      },
      {
        "aliases": [
          "i_valid",
          "instr_bus_i_valid"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "i_valid",
        "source_ref": "io_list.interfaces[0].ports[2]",
        "width": "1"
      },
      {
        "aliases": [
          "alu_result",
          "instr_bus_alu_result"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "alu_result",
        "source_ref": "io_list.interfaces[0].ports[3]",
        "width": "1"
      },
      {
        "aliases": [
          "branch_imm",
          "instr_bus_branch_imm"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "branch_imm",
        "source_ref": "io_list.interfaces[0].ports[4]",
        "width": "1"
      },
      {
        "aliases": [
          "branch_taken",
          "instr_bus_branch_taken"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "branch_taken",
        "source_ref": "io_list.interfaces[0].ports[5]",
        "width": "1"
      },
      {
        "aliases": [
          "illegal_shamt",
          "instr_bus_illegal_shamt"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "illegal_shamt",
        "source_ref": "io_list.interfaces[0].ports[6]",
        "width": "1"
      },
      {
        "aliases": [
          "imm",
          "instr_bus_imm"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "imm",
        "source_ref": "io_list.interfaces[0].ports[7]",
        "width": "1"
      },
      {
        "aliases": [
          "instr_bus_is_ebreak",
          "is_ebreak"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "is_ebreak",
        "source_ref": "io_list.interfaces[0].ports[8]",
        "width": "1"
      },
      {
        "aliases": [
          "instr_bus_is_ecall",
          "is_ecall"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "is_ecall",
        "source_ref": "io_list.interfaces[0].ports[9]",
        "width": "1"
      },
      {
        "aliases": [
          "instr_bus_is_jalr",
          "is_jalr"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "is_jalr",
        "source_ref": "io_list.interfaces[0].ports[10]",
        "width": "1"
      },
      {
        "aliases": [
          "instr_bus_is_store",
          "is_store"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "is_store",
        "source_ref": "io_list.interfaces[0].ports[11]",
        "width": "1"
      },
      {
        "aliases": [
          "instr_bus_load_data_ext",
          "load_data_ext"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "load_data_ext",
        "source_ref": "io_list.interfaces[0].ports[12]",
        "width": "1"
      },
      {
        "aliases": [
          "instr_bus_misaligned_access",
          "misaligned_access"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "misaligned_access",
        "source_ref": "io_list.interfaces[0].ports[13]",
        "width": "1"
      },
      {
        "aliases": [
          "instr_bus_rs1",
          "rs1"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "rs1",
        "source_ref": "io_list.interfaces[0].ports[14]",
        "width": "1"
      },
      {
        "aliases": [
          "d_addr",
          "data_bus_d_addr"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "d_addr",
        "source_ref": "io_list.interfaces[1].ports[0]",
        "width": "32"
      },
      {
        "aliases": [
          "d_wdata",
          "data_bus_d_wdata"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "d_wdata",
        "source_ref": "io_list.interfaces[1].ports[1]",
        "width": "32"
      },
      {
        "aliases": [
          "d_rdata",
          "data_bus_d_rdata"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "d_rdata",
        "source_ref": "io_list.interfaces[1].ports[2]",
        "width": "32"
      },
      {
        "aliases": [
          "d_we",
          "data_bus_d_we"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "d_we",
        "source_ref": "io_list.interfaces[1].ports[3]",
        "width": "1"
      },
      {
        "aliases": [
          "d_be",
          "data_bus_d_be"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "d_be",
        "source_ref": "io_list.interfaces[1].ports[4]",
        "width": "4"
      },
      {
        "aliases": [
          "d_valid",
          "data_bus_d_valid"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "d_valid",
        "source_ref": "io_list.interfaces[1].ports[5]",
        "width": "1"
      },
      {
        "aliases": [
          "exception_excpt_o",
          "excpt_o"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "excpt_o",
        "source_ref": "io_list.interfaces[2].ports[0]",
        "width": "1"
      }
    ],
    "target_scale": {
      "basis": "smoke fixture CPU with explicit behavioral ownership",
      "min_behavior_owner_logic_modules": 4,
      "min_depth_score": 20,
      "min_logic_modules": 4,
      "min_modules": 6,
      "min_procedural_blocks": 8,
      "min_source_files": 6,
      "min_state_updates": 8,
      "policy": "SSOT-locked scale target. It may be calibrated from a reference profile, but rtl-gen must satisfy it through IP-specific SSOT behavior, not by copying reference RTL."
    }
  },
  "execution_policy": {
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [],
    "contract_blocked_open_count": 0,
    "deferred_human_qa_allowed": true,
    "draft_allowed": false,
    "evidence_closure_allowed": true,
    "human_locked_open_count": 0,
    "integration_signoff_allowed": true,
    "llm_actionable": true,
    "llm_actionable_open_count": 4,
    "open_required_count": 4,
    "pass_allowed": false,
    "stop_conditions": [
      "Close this packet only after every required task in the packet has pass status.",
      "Return human_gate/change-request JSON when locked truth is missing instead of inventing semantics.",
      "Never use a fixed RTL template as the implementation."
    ],
    "tool_evidence_open_count": 0,
    "tool_evidence_plan": [],
    "work_allowed": true
  },
  "ip": "rv32i_min",
  "kind": "gate",
  "owner_file": "rtl/rv32i_min.sv",
  "owner_module": "rv32i_min",
  "packet_id": "rtl_gate_evidence_closure",
  "rules": [
    "No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.",
    "Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.",
    "Every task must satisfy content, detail, and criteria before the packet is closed.",
    "For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.",
    "Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.",
    "Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.",
    "Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json."
  ],
  "schema_version": 1,
  "source_plan": "rtl/rtl_todo_plan.json",
  "summary": {
    "categories": {
      "rtl_gate.rtl_gen": 9
    },
    "module_slice": {},
    "open_required_count": 4,
    "required_count": 9,
    "source_refs": [
      "quality_gates.rtl_gen.static_rtl_evidence",
      "quality_gates.rtl_gen.owner_logic_structure_evidence",
      "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
      "quality_gates.rtl_gen.top_io_contract_evidence",
      "quality_gates.rtl_gen.top_output_drive_evidence",
      "quality_gates.rtl_gen.top_input_consumption_evidence",
      "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "quality_gates.rtl_gen.manifest_port_connection_evidence",
      "quality_gates.rtl_gen.manifest_signal_flow_evidence"
    ],
    "status_counts": {
      "open": 4,
      "pass": 5
    },
    "task_count": 9
  },
  "tasks": [
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: required SSOT behavior has static DUT RTL evidence after audit",
      "criteria": [
        "derive_rtl_todos.py --audit-rtl ran after the final RTL edit",
        "rtl_todo_plan.json static_rtl_evidence.missing is zero",
        "Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token",
        "No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code",
        "Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.\nSSOT ref: quality_gates.rtl_gen.static_rtl_evidence.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "static_rtl_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0007",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.static_rtl_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "2 static-evidence-required task(s) still lack DUT RTL evidence.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: behavior-owner RTL modules contain real implementation structure",
      "criteria": [
        "Every active behavior-owner module is declared in its owner file",
        "Behavior-owner modules contain non-placeholder assign/procedural implementation logic",
        "State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions",
        "Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.\nSSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "owner_logic_structure_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0008",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.owner_logic_structure_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "Behavior-owner RTL modules contain real implementation structure.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: RTL sources contain no placeholder markers or disallowed generated-RTL constructs",
      "criteria": [
        "Listed RTL source files contain no TODO/TBD/FIXME/HACK markers",
        "Listed RTL source files contain no placeholder/stub/dummy/not-implemented implementation text",
        "Listed RTL source files and rtl/<ip>_param.vh contain no banned package/function/task/loop constructs",
        "Default generated RTL uses input/output logic ports and portable always @ syntax",
        "FSMs use the conventional explicit style by default, unless SSOT/user specifies another synthesizable style",
        "Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments",
        "Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "Production RTL cannot carry TODO/TBD/FIXME/stub/dummy/not-implemented markers in source code or comments. Generated RTL uses the project SystemVerilog subset: ANSI ports default to input/output logic, with no package/import/interface/modport, no function/task, no for/while, and no typedef/enum/always_ff/always_comb. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.\nSSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "rtl_placeholder_free_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0009",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.rtl_placeholder_free_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "RTL sources contain no placeholder markers or disallowed default-policy constructs.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top IO contracts match the RTL top module",
      "criteria": [
        "SSOT clock/reset names are declared on the RTL top module",
        "Explicit io_list ports/signals are declared on the RTL top module",
        "Known SSOT directions and simple widths match RTL declarations",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.\nSSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_io_contract_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0010",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_io_contract_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "SSOT top IO contracts match the RTL top declaration.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top outputs are driven by real RTL logic",
      "criteria": [
        "Every SSOT output/inout top contract has drive evidence in the RTL top",
        "Non-waived output constants are rejected as placeholder tieoffs",
        "Child-instance drive evidence uses a declared child output/inout port, not an unknown direction",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.\nSSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_output_drive_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0011",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_output_drive_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "SSOT top outputs have non-placeholder RTL drive evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top inputs are consumed by RTL logic or child inputs",
      "criteria": [
        "Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top",
        "Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction",
        "Unused or reserved inputs are accepted only when explicitly waived by SSOT",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.\nSSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_input_consumption_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0012",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_input_consumption_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "10 top input consumption issue(s) remain. alu_result: RTL top input is connected only to child ports without declared input/inout direction; branch_imm: RTL top input is connected only to child ports without declared input/inout direction; branch_taken: RTL top input is connected only to child ports without declared input/inout direction",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest-owned RTL modules are integrated into the top hierarchy",
      "criteria": [
        "Every manifest-owned non-top submodule is declared in listed DUT RTL sources",
        "Each child module is reachable from the SSOT top module through SystemVerilog instantiation",
        "A disconnected child file or flattened top cannot close the manifest hierarchy gate",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.\nSSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_hierarchy_integration",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0013",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_hierarchy_integration"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "Every SSOT manifest-owned child module is declared and reachable from the top RTL hierarchy.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest-owned child instances have machine-checkable port connections",
      "criteria": [
        "Each reachable manifest child instance uses named port mapping",
        "Every declared child port is connected by name on at least one reachable instance",
        "No child port connection is empty unless represented by an explicit SSOT waiver",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.\nSSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_port_connection_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0014",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_port_connection_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_port_connection_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "5 manifest port connection issue(s) remain. rv32i_min_if: Reachable child instance has missing or empty named port connections; rv32i_min_idex: Reachable child instance has missing or empty named port connections; rv32i_min_memwb: Reachable child instance has missing or empty named port connections",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest child port connections carry live RTL signal flow",
      "criteria": [
        "Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance",
        "Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts",
        "Named port-map entries reference ports declared by the child module",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "Primary implementation evidence is in rtl/rv32i_min.sv"
      ],
      "detail": "Named port maps prove that ports are connected, but not that the connected signals are useful. Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and child outputs must feed a top output, parent logic, or another declared child input/inout.\nSSOT ref: quality_gates.rtl_gen.manifest_signal_flow_evidence.\nOwner: rv32i_min in rtl/rv32i_min.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_signal_flow_evidence",
        "profile": "standard",
        "stage": "rtl-gen"
      },
      "id": "RTL-0015",
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_signal_flow_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "27 manifest signal-flow issue(s) remain. rv32i_min_idex: alu_result: Named port-map entry targets a port not declared by the child module; rv32i_min_idex: branch_imm: Named port-map entry targets a port not declared by the child module; rv32i_min_idex: branch_taken: Named port-map entry targets a port not declared by the child module",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "10c4be796cd0d74fe7574b57a60327afb02cfecb9c550522c1e714ec8a08eb01",
  "top": "rv32i_min",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/rtl_gate_evidence_closure.md):
# RTL Authoring Packet: rtl_gate_evidence_closure

- Kind: gate
- Owner module: rv32i_min
- Owner file: rtl/rv32i_min.sv
- Task count: 9
- Required tasks: 9

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: integration, integration.connections, io_list
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])
  - rv32i_min_memwb.d_addr <= d_addr (integration.connections[3])
  - rv32i_min_memwb.d_wdata <= d_wdata (integration.connections[4])
  - rv32i_min_memwb.d_rdata <= d_rdata (integration.connections[5])
  - rv32i_min_memwb.d_we <= d_we (integration.connections[6])
  - rv32i_min_memwb.d_be <= d_be (integration.connections[7])
  - rv32i_min_memwb.d_valid <= d_valid (integration.connections[8])
  - rv32i_min_core.excpt_o <= excpt_o (integration.connections[9])
- SSOT top IO contracts: 24

## Tasks

### RTL-0007: Gate: required SSOT behavior has static DUT RTL evidence after audit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.static_rtl_evidence
- Detail: After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.
SSOT ref: quality_gates.rtl_gen.static_rtl_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: 2 static-evidence-required task(s) still lack DUT RTL evidence.
- Criteria:
  - derive_rtl_todos.py --audit-rtl ran after the final RTL edit
  - rtl_todo_plan.json static_rtl_evidence.missing is zero
  - Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token
  - No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code
  - Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.static_rtl_evidence

### RTL-0008: Gate: behavior-owner RTL modules contain real implementation structure

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_logic_structure_evidence
- Detail: Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.
SSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: Behavior-owner RTL modules contain real implementation structure.
- Criteria:
  - Every active behavior-owner module is declared in its owner file
  - Behavior-owner modules contain non-placeholder assign/procedural implementation logic
  - State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_logic_structure_evidence

### RTL-0009: Gate: RTL sources contain no placeholder markers or disallowed generated-RTL constructs

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence
- Detail: Production RTL cannot carry TODO/TBD/FIXME/stub/dummy/not-implemented markers in source code or comments. Generated RTL uses the project SystemVerilog subset: ANSI ports default to input/output logic, with no package/import/interface/modport, no function/task, no for/while, and no typedef/enum/always_ff/always_comb. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.
SSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: RTL sources contain no placeholder markers or disallowed default-policy constructs.
- Criteria:
  - Listed RTL source files contain no TODO/TBD/FIXME/HACK markers
  - Listed RTL source files contain no placeholder/stub/dummy/not-implemented implementation text
  - Listed RTL source files and rtl/<ip>_param.vh contain no banned package/function/task/loop constructs
  - Default generated RTL uses input/output logic ports and portable always @ syntax
  - FSMs use the conventional explicit style by default, unless SSOT/user specifies another synthesizable style
  - Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments
  - Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.rtl_placeholder_free_evidence

### RTL-0010: Gate: SSOT top IO contracts match the RTL top module

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_io_contract_evidence
- Detail: The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.
SSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: SSOT top IO contracts match the RTL top declaration.
- Criteria:
  - SSOT clock/reset names are declared on the RTL top module
  - Explicit io_list ports/signals are declared on the RTL top module
  - Known SSOT directions and simple widths match RTL declarations
  - Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_io_contract_evidence

### RTL-0011: Gate: SSOT top outputs are driven by real RTL logic

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_output_drive_evidence
- Detail: Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.
SSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: SSOT top outputs have non-placeholder RTL drive evidence.
- Criteria:
  - Every SSOT output/inout top contract has drive evidence in the RTL top
  - Non-waived output constants are rejected as placeholder tieoffs
  - Child-instance drive evidence uses a declared child output/inout port, not an unknown direction
  - Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_output_drive_evidence

### RTL-0012: Gate: SSOT top inputs are consumed by RTL logic or child inputs

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_input_consumption_evidence
- Detail: Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.
SSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: 10 top input consumption issue(s) remain. alu_result: RTL top input is connected only to child ports without declared input/inout direction; branch_imm: RTL top input is connected only to child ports without declared input/inout direction; branch_taken: RTL top input is connected only to child ports without declared input/inout direction
- Criteria:
  - Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top
  - Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction
  - Unused or reserved inputs are accepted only when explicitly waived by SSOT
  - Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_input_consumption_evidence

### RTL-0013: Gate: manifest-owned RTL modules are integrated into the top hierarchy

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_hierarchy_integration
- Detail: File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.
SSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: Every SSOT manifest-owned child module is declared and reachable from the top RTL hierarchy.
- Criteria:
  - Every manifest-owned non-top submodule is declared in listed DUT RTL sources
  - Each child module is reachable from the SSOT top module through SystemVerilog instantiation
  - A disconnected child file or flattened top cannot close the manifest hierarchy gate
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_hierarchy_integration

### RTL-0014: Gate: manifest-owned child instances have machine-checkable port connections

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_port_connection_evidence
- Detail: Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.
SSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: 5 manifest port connection issue(s) remain. rv32i_min_if: Reachable child instance has missing or empty named port connections; rv32i_min_idex: Reachable child instance has missing or empty named port connections; rv32i_min_memwb: Reachable child instance has missing or empty named port connections
- Criteria:
  - Each reachable manifest child instance uses named port mapping
  - Every declared child port is connected by name on at least one reachable instance
  - No child port connection is empty unless represented by an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_port_connection_evidence

### RTL-0015: Gate: manifest child port connections carry live RTL signal flow

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_signal_flow_evidence
- Detail: Named port maps prove that ports are connected, but not that the connected signals are useful. Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and child outputs must feed a top output, parent logic, or another declared child input/inout.
SSOT ref: quality_gates.rtl_gen.manifest_signal_flow_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: 27 manifest signal-flow issue(s) remain. rv32i_min_idex: alu_result: Named port-map entry targets a port not declared by the child module; rv32i_min_idex: branch_imm: Named port-map entry targets a port not declared by the child module; rv32i_min_idex: branch_taken: Named port-map entry targets a port not declared by the child module
- Criteria:
  - Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance
  - Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts
  - Named port-map entries reference ports declared by the child module
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_signal_flow_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_signal_flow_evidence
