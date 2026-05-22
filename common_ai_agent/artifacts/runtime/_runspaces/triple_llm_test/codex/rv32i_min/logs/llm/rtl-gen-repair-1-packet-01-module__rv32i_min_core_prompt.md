RTL-GEN PACKET MODE for rv32i_min. Packet attempt 1.

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

Current packet: module__rv32i_min_core
kind: module
work queue: 2/4 active packets (10 closed packets skipped from 15 total)
batch limit: 4; deferred active packets after this batch: 1
owner_module: rv32i_min_core
owner_file: rtl/rv32i_min_core.sv

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
        "reason": "4 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "rv32i_min",
        "reason": "1 owner logic structure issue(s) remain. rv32i_min_core: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "rv32i_min",
        "reason": "1 top IO contract issue(s) remain. rv32i_min: SSOT top module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "top_output_drive_evidence",
        "owner_module": "rv32i_min",
        "reason": "1 top output drive issue(s) remain. rv32i_min: SSOT top module is not declared, so output drive evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
        "status": "open",
        "task_id": "RTL-0011"
      },
      {
        "gate_kind": "top_input_consumption_evidence",
        "owner_module": "rv32i_min",
        "reason": "1 top input consumption issue(s) remain. rv32i_min: SSOT top module is not declared, so input consumption evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
        "status": "open",
        "task_id": "RTL-0012"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "rv32i_min",
        "reason": "6 manifest hierarchy integration issue(s) remain. rv32i_min: SSOT top module is not declared in listed RTL sources; rv32i_min_if: SSOT manifest child module is declared but not reachable from the top RTL hierarchy; rv32i_min_idex: SSOT manifest child module is declared but not reachable from the top RTL hierarchy",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "rv32i_min",
        "reason": "1 manifest signal-flow issue(s) remain. rv32i_min: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
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
        "reason": "10 SSOT connection contract issue(s) remain. rv32i_min_if: SSOT connection contract targets a module not reachable from top RTL hierarchy; rv32i_min_if: SSOT connection contract targets a module not reachable from top RTL hierarchy; rv32i_min_if: SSOT connection contract targets a module not reachable from top RTL hierarchy",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      }
    ],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "rv32i_min",
        "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/rv32i_min.sv,rtl/rv32i_min_core.sv",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "rv32i_min",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "rv32i_min",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "rv32i_min",
        "reason": "55 required non-closure TODO(s) remain open.",
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
    "open_required_todos": 56,
    "pass_allowed": false,
    "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
    "stop_conditions": [
      "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
      "Do not claim rtl-gen PASS while pass_allowed is false.",
      "Do not sign off top integration while required connection contracts are missing."
    ],
    "tool_evidence_plan": [
      {
        "artifact": "rtl/rtl_authoring_provenance.json",
        "artifacts": [
          "rv32i_min/rtl/rtl_authoring_provenance.json",
          "rv32i_min/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip rv32i_min --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py rv32i_min --root . --audit-rtl"
        ],
        "gate_kind": "common_ai_agent_authoring",
        "prerequisites": [
          "An LLM authoring pass emitted or repaired DUT RTL files."
        ],
        "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/rv32i_min.sv,rtl/rv32i_min_core.sv",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "stage_sequence": [
          "ssot-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0006"
      },
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
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
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
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
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
        "reason": "55 required non-closure TODO(s) remain open.",
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
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/rv32i_min_if.sv",
      "owner_module": "rv32i_min_if",
      "packet_id": "module__rv32i_min_if__function_model",
      "required_count": 35,
      "status_counts": {
        "open": 4,
        "pass": 31
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min_core.json",
      "kind": "module",
      "llm_actionable_open_count": 28,
      "open_required_count": 28,
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "packet_id": "module__rv32i_min_core",
      "required_count": 28,
      "status_counts": {
        "open": 28
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__rv32i_min.json",
      "kind": "module",
      "llm_actionable_open_count": 10,
      "open_required_count": 10,
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "packet_id": "module__rv32i_min",
      "required_count": 11,
      "status_counts": {
        "open": 10,
        "pass": 1
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
      "llm_actionable_open_count": 7,
      "open_required_count": 7,
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 9,
      "status_counts": {
        "open": 7,
        "pass": 2
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
      "open_required_count": 4,
      "owner_file": "rtl/rv32i_min.sv",
      "owner_module": "rv32i_min",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 4
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
    "llm_actionable_packets": 5,
    "llm_actionable_tasks": 51,
    "max_packet_required_tasks": 35,
    "module_packets": 11,
    "next_llm_packets": [
      "module__rv32i_min_if__function_model",
      "module__rv32i_min_core",
      "module__rv32i_min",
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
    "tool_evidence_tasks": 4,
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

Current owner RTL file (rtl/rv32i_min_core.sv):
<missing or not authored yet>

Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__rv32i_min_core.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 10,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": false,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 28,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/rv32i_min_core.sv",
      "name": "rv32i_min_core",
      "refs": [
        "cycle_model",
        "cycle_model.handshake_rules",
        "cycle_model.ordering",
        "cycle_model.pipeline",
        "dataflow",
        "decomposition",
        "decomposition.units",
        "function_model",
        "function_model.invariants",
        "function_model.state_variables",
        "function_model.transactions",
        "function_model.transactions.FM_ALU",
        "function_model.transactions.FM_BRANCH",
        "function_model.transactions.FM_JUMP",
        "integration",
        "integration.connections",
        "rtl_contract",
        "test_requirements"
      ],
      "wiring_only": false
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
        "module": "rv32i_min_core",
        "port": "excpt_o",
        "signal": "excpt_o",
        "signal_terms": [
          "excpt_o"
        ],
        "source_ref": "integration.connections[9]"
      }
    ],
    "ssot_top_io_contracts": [],
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
    "draft_allowed": true,
    "evidence_closure_allowed": false,
    "human_locked_open_count": 0,
    "integration_signoff_allowed": true,
    "llm_actionable": true,
    "llm_actionable_open_count": 28,
    "open_required_count": 28,
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
  "kind": "module",
  "owner_file": "rtl/rv32i_min_core.sv",
  "owner_module": "rv32i_min_core",
  "packet_id": "module__rv32i_min_core",
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
      "cycle_model.ordering": 3,
      "equivalence.module": 1,
      "integration.connections": 10,
      "integration.dependencies": 2,
      "test_requirements.scenario": 12
    },
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 28,
      "task_limit": 48
    },
    "open_required_count": 28,
    "required_count": 28,
    "source_refs": [
      "cycle_model.ordering.ordering_rule_0",
      "cycle_model.ordering.ordering_rule_1",
      "cycle_model.ordering.ordering_rule_2",
      "integration.dependencies.dependencie_0",
      "integration.dependencies.dependencie_1",
      "integration.connections.i_addr",
      "integration.connections.i_valid",
      "integration.connections.i_rdata",
      "integration.connections.d_addr",
      "integration.connections.d_wdata",
      "integration.connections.d_rdata",
      "integration.connections.d_we",
      "integration.connections.d_be",
      "integration.connections.d_valid",
      "integration.connections.excpt_o",
      "sub_modules.rv32i_min_core.module_equivalence",
      "test_requirements.scenarios.SC01",
      "test_requirements.scenarios.SC02",
      "test_requirements.scenarios.SC03",
      "test_requirements.scenarios.SC04",
      "test_requirements.scenarios.SC05",
      "test_requirements.scenarios.SC06",
      "test_requirements.scenarios.SC07",
      "test_requirements.scenarios.SC08"
    ],
    "status_counts": {
      "open": 28
    },
    "task_count": 28
  },
  "tasks": [
    {
      "category": "cycle_model.ordering",
      "content": "Implement ordering rule: ordering_rule_0",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.ordering.ordering_rule_0",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.ordering.ordering_rule_0.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.\nSSOT item context: value=Retirement is in program order with at most one commit per cycle.",
      "evidence_terms": [],
      "id": "RTL-0133",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.ordering.ordering_rule_0",
      "ssot_context": {
        "value": "Retirement is in program order with at most one commit per cycle"
      },
      "ssot_refs": [
        "cycle_model.ordering.ordering_rule_0"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.ordering",
      "content": "Implement ordering rule: ordering_rule_1",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.ordering.ordering_rule_1",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.ordering.ordering_rule_1.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.\nSSOT item context: value=Faulting misaligned or illegal instruction does not retire.",
      "evidence_terms": [],
      "id": "RTL-0134",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.ordering.ordering_rule_1",
      "ssot_context": {
        "value": "Faulting misaligned or illegal instruction does not retire"
      },
      "ssot_refs": [
        "cycle_model.ordering.ordering_rule_1"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.ordering",
      "content": "Implement ordering rule: ordering_rule_2",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.ordering.ordering_rule_2",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.ordering.ordering_rule_2.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.\nSSOT item context: value=Store side effects occur only on aligned non-faulting stores.",
      "evidence_terms": [],
      "id": "RTL-0135",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.ordering.ordering_rule_2",
      "ssot_context": {
        "value": "Store side effects occur only on aligned non-faulting stores"
      },
      "ssot_refs": [
        "cycle_model.ordering.ordering_rule_2"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.dependencies",
      "content": "Implement integration item dependencie_0",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.dependencies.dependencie_0",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv"
      ],
      "detail": "This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.dependencies.dependencie_0.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.\nSSOT item context: value=External instruction memory returns i_rdata for i_addr every cycle.",
      "evidence_terms": [
        "addr",
        "i_addr",
        "i_rdata",
        "rdata"
      ],
      "id": "RTL-0156",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.dependencies.dependencie_0",
      "ssot_context": {
        "value": "External instruction memory returns i_rdata for i_addr every cycle"
      },
      "ssot_refs": [
        "integration.dependencies.dependencie_0"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.dependencies",
      "content": "Implement integration item dependencie_1",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.dependencies.dependencie_1",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv"
      ],
      "detail": "This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.dependencies.dependencie_1.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.\nSSOT item context: value=External data memory observes d_valid and d_we and d_be and provides d_rdata for loads.",
      "evidence_terms": [
        "d_be",
        "d_rdata",
        "d_valid",
        "d_we",
        "rdata",
        "valid",
        "we"
      ],
      "id": "RTL-0157",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.dependencies.dependencie_1",
      "ssot_context": {
        "value": "External data memory observes d_valid and d_we and d_be and provides d_rdata for loads"
      },
      "ssot_refs": [
        "integration.dependencies.dependencie_1"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item i_addr",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.i_addr",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port i_addr is the implementation/observation point for i_addr"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.i_addr.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=i_addr; signal=i_addr.",
      "evidence_terms": [
        "addr",
        "i_addr"
      ],
      "id": "RTL-0158",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.i_addr",
      "ssot_context": {
        "port": "i_addr",
        "signal": "i_addr"
      },
      "ssot_refs": [
        "integration.connections.i_addr"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item i_valid",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.i_valid",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port i_valid is the implementation/observation point for i_valid"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.i_valid.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=i_valid; signal=i_valid.",
      "evidence_terms": [
        "i_valid",
        "valid"
      ],
      "id": "RTL-0159",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.i_valid",
      "ssot_context": {
        "port": "i_valid",
        "signal": "i_valid"
      },
      "ssot_refs": [
        "integration.connections.i_valid"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item i_rdata",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.i_rdata",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port i_rdata is the implementation/observation point for i_rdata"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.i_rdata.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=i_rdata; signal=i_rdata.",
      "evidence_terms": [
        "i_rdata",
        "rdata"
      ],
      "id": "RTL-0160",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.i_rdata",
      "ssot_context": {
        "port": "i_rdata",
        "signal": "i_rdata"
      },
      "ssot_refs": [
        "integration.connections.i_rdata"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item d_addr",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.d_addr",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port d_addr is the implementation/observation point for d_addr"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.d_addr.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=d_addr; signal=d_addr.",
      "evidence_terms": [
        "addr",
        "d_addr"
      ],
      "id": "RTL-0161",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.d_addr",
      "ssot_context": {
        "port": "d_addr",
        "signal": "d_addr"
      },
      "ssot_refs": [
        "integration.connections.d_addr"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item d_wdata",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.d_wdata",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port d_wdata is the implementation/observation point for d_wdata"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.d_wdata.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=d_wdata; signal=d_wdata.",
      "evidence_terms": [
        "d_wdata",
        "wdata"
      ],
      "id": "RTL-0162",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.d_wdata",
      "ssot_context": {
        "port": "d_wdata",
        "signal": "d_wdata"
      },
      "ssot_refs": [
        "integration.connections.d_wdata"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item d_rdata",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.d_rdata",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port d_rdata is the implementation/observation point for d_rdata"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.d_rdata.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=d_rdata; signal=d_rdata.",
      "evidence_terms": [
        "d_rdata",
        "rdata"
      ],
      "id": "RTL-0163",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.d_rdata",
      "ssot_context": {
        "port": "d_rdata",
        "signal": "d_rdata"
      },
      "ssot_refs": [
        "integration.connections.d_rdata"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item d_we",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.d_we",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port d_we is the implementation/observation point for d_we"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.d_we.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=d_we; signal=d_we.",
      "evidence_terms": [
        "d_we",
        "we"
      ],
      "id": "RTL-0164",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.d_we",
      "ssot_context": {
        "port": "d_we",
        "signal": "d_we"
      },
      "ssot_refs": [
        "integration.connections.d_we"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item d_be",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.d_be",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port d_be is the implementation/observation point for d_be"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.d_be.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=d_be; signal=d_be.",
      "evidence_terms": [
        "d_be"
      ],
      "id": "RTL-0165",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.d_be",
      "ssot_context": {
        "port": "d_be",
        "signal": "d_be"
      },
      "ssot_refs": [
        "integration.connections.d_be"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item d_valid",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.d_valid",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port d_valid is the implementation/observation point for d_valid"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.d_valid.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=d_valid; signal=d_valid.",
      "evidence_terms": [
        "d_valid",
        "valid"
      ],
      "id": "RTL-0166",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.d_valid",
      "ssot_context": {
        "port": "d_valid",
        "signal": "d_valid"
      },
      "ssot_refs": [
        "integration.connections.d_valid"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "integration.connections",
      "content": "Implement integration item excpt_o",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref integration.connections.excpt_o",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "DUT port excpt_o is the implementation/observation point for excpt_o"
      ],
      "detail": "This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: integration.connections.excpt_o.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.\nSSOT item context: port=excpt_o; signal=excpt_o.",
      "evidence_terms": [
        "excpt",
        "excpt_o"
      ],
      "id": "RTL-0167",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "integration.connections.excpt_o",
      "ssot_context": {
        "port": "excpt_o",
        "signal": "excpt_o"
      },
      "ssot_refs": [
        "integration.connections.excpt_o"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "equivalence.module",
      "content": "Prove module rv32i_min_core is functionally equivalent to FL",
      "criteria": [
        "verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module",
        "cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff",
        "scoreboard row fl_expected.model_api is FunctionalModel.apply",
        "scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data",
        "Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong",
        "Traceability keeps source_ref sub_modules.rv32i_min_core.module_equivalence",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv"
      ],
      "detail": "This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.\nSSOT ref: sub_modules.rv32i_min_core.module_equivalence.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via module_equivalence.",
      "evidence_terms": [],
      "id": "RTL-0175",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "high",
      "required": true,
      "source_ref": "sub_modules.rv32i_min_core.module_equivalence",
      "ssot_context": {},
      "ssot_refs": [
        "sub_modules.rv32i_min_core.module_equivalence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC01",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC01",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "Downstream checker compares RTL-observed behavior against expected result: pc and regfile and excpt_o reset values match function_model and rtl_contract"
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC01.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.\nSSOT item context: id=SC01; name=reset contract; expected=pc and regfile and excpt_o reset values match function_model and rtl_contract.",
      "evidence_terms": [],
      "id": "RTL-0176",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC01",
      "ssot_context": {
        "expected": "pc and regfile and excpt_o reset values match function_model and rtl_contract",
        "id": "SC01",
        "name": "reset contract"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC01"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC02",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC02",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "Downstream checker compares RTL-observed behavior against expected result: pc and regfile trajectory match reference model for each opcode"
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC02.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.\nSSOT item context: id=SC02; name=opcode sweep 37; expected=pc and regfile trajectory match reference model for each opcode.",
      "evidence_terms": [],
      "id": "RTL-0177",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC02",
      "ssot_context": {
        "expected": "pc and regfile trajectory match reference model for each opcode",
        "id": "SC02",
        "name": "opcode sweep 37"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC02"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC03",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC03",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "Downstream checker compares RTL-observed behavior against expected result: next pc behavior matches signed and unsigned branch rules"
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC03.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.\nSSOT item context: id=SC03; name=branch taken and untaken; expected=next pc behavior matches signed and unsigned branch rules.",
      "evidence_terms": [],
      "id": "RTL-0178",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC03",
      "ssot_context": {
        "expected": "next pc behavior matches signed and unsigned branch rules",
        "id": "SC03",
        "name": "branch taken and untaken"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC03"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC04",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC04",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "Downstream checker compares RTL-observed behavior against expected result: extension and d_be patterns match function_model contract"
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC04.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.\nSSOT item context: id=SC04; name=load store extension and byte enable; expected=extension and d_be patterns match function_model contract.",
      "evidence_terms": [],
      "id": "RTL-0179",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC04",
      "ssot_context": {
        "expected": "extension and d_be patterns match function_model contract",
        "id": "SC04",
        "name": "load store extension and byte enable"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC04"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC05",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC05",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "Downstream checker compares RTL-observed behavior against expected result: regfile x0 remains zero"
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC05.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.\nSSOT item context: id=SC05; name=x0 immutable; expected=regfile x0 remains zero.",
      "evidence_terms": [],
      "id": "RTL-0180",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC05",
      "ssot_context": {
        "expected": "regfile x0 remains zero",
        "id": "SC05",
        "name": "x0 immutable"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC05"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC06",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC06",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "Downstream checker compares RTL-observed behavior against expected result: next_pc default rule and fetch outputs hold"
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC06.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.\nSSOT item context: id=SC06; name=FM_FETCH transaction; expected=next_pc default rule and fetch outputs hold.",
      "evidence_terms": [],
      "id": "RTL-0181",
      "owner_file": "rtl/rv32i_min_core.sv",
      "owner_module": "rv32i_min_core",
      "priority": "normal",
      "required": true,
      "source_ref": "test_requirements.scenarios.SC06",
      "ssot_context": {
        "expected": "next_pc default rule and fetch outputs hold",
        "id": "SC06",
        "name": "FM_FETCH transaction"
      },
      "ssot_refs": [
        "test_requirements.scenarios.SC06"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/rv32i_min_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "test_requirements.scenario",
      "content": "Keep RTL observable for scenario SC07",
      "criteria": [
        "RTL exposes enough signals/status/outputs for the scenario checker",
        "FunctionalModel expected result and RTL observed result can be compared",
        "Scenario has coverage refs or a precise SSOT reason for exclusion",
        "Traceability keeps source_ref test_requirements.scenarios.SC07",
        "Primary implementation evidence is in rtl/rv32i_min_core.sv",
        "Downstream checker compares RTL-observed behavior against expected result: wb_data_alu equals model result"
      ],
      "detail": "Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.\nSSOT ref: test_requirements.scenarios.SC07.\nOwner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.\nSSOT ite
... <truncated 11543 chars>

Current packet Markdown (rtl/authoring_packets/module__rv32i_min_core.md):
# RTL Authoring Packet: module__rv32i_min_core

- Kind: module
- Owner module: rv32i_min_core
- Owner file: rtl/rv32i_min_core.sv
- Task count: 28
- Required tasks: 28

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
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 28
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, decomposition.units, function_model, function_model.invariants, function_model.state_variables, function_model.transactions, function_model.transactions.FM_ALU, function_model.transactions.FM_BRANCH, function_model.transactions.FM_JUMP, integration, integration.connections
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_core.excpt_o <= excpt_o (integration.connections[9])

## Tasks

### RTL-0133: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.
SSOT item context: value=Retirement is in program order with at most one commit per cycle.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0134: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.
SSOT item context: value=Faulting misaligned or illegal instruction does not retire.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0135: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.
SSOT item context: value=Store side effects occur only on aligned non-faulting stores.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0156: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.
SSOT item context: value=External instruction memory returns i_rdata for i_addr every cycle.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0157: Implement integration item dependencie_1

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_1
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_1.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.
SSOT item context: value=External data memory observes d_valid and d_we and d_be and provides d_rdata for loads.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_1
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
- SSOT refs: integration.dependencies.dependencie_1

### RTL-0158: Implement integration item i_addr

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.i_addr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.i_addr.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=i_addr; signal=i_addr.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.i_addr
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port i_addr is the implementation/observation point for i_addr
- SSOT refs: integration.connections.i_addr

### RTL-0159: Implement integration item i_valid

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.i_valid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.i_valid.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=i_valid; signal=i_valid.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.i_valid
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port i_valid is the implementation/observation point for i_valid
- SSOT refs: integration.connections.i_valid

### RTL-0160: Implement integration item i_rdata

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.i_rdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.i_rdata.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=i_rdata; signal=i_rdata.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.i_rdata
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port i_rdata is the implementation/observation point for i_rdata
- SSOT refs: integration.connections.i_rdata

### RTL-0161: Implement integration item d_addr

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.d_addr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_addr.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_addr; signal=d_addr.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_addr
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_addr is the implementation/observation point for d_addr
- SSOT refs: integration.connections.d_addr

### RTL-0162: Implement integration item d_wdata

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.d_wdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_wdata.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_wdata; signal=d_wdata.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_wdata
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_wdata is the implementation/observation point for d_wdata
- SSOT refs: integration.connections.d_wdata

### RTL-0163: Implement integration item d_rdata

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.d_rdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_rdata.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_rdata; signal=d_rdata.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_rdata
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_rdata is the implementation/observation point for d_rdata
- SSOT refs: integration.connections.d_rdata

### RTL-0164: Implement integration item d_we

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.d_we
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_we.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_we; signal=d_we.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_we
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_we is the implementation/observation point for d_we
- SSOT refs: integration.connections.d_we

### RTL-0165: Implement integration item d_be

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.d_be
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_be.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_be; signal=d_be.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_be
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_be is the implementation/observation point for d_be
- SSOT refs: integration.connections.d_be

### RTL-0166: Implement integration item d_valid

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.d_valid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_valid.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_valid; signal=d_valid.
- Current reason: Owner RTL file is missing: rtl/rv32i_min_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_valid
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_valid is the implementation/observation point for d_valid
- SSOT refs: integration.connections.d_valid

### RTL-0167: Implement integration item excpt_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connectio
... <truncated 15761 chars>