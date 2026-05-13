RTL-GEN PACKET MODE for cortex_m0lite. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "cortex_m0lite/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "cortex_m0lite/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "cortex_m0lite/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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

Current packet: module__cortex_m0lite_core__function_model
kind: module
work queue: 1/1 active packets (9 closed packets skipped from 25 total)
batch limit: 1; deferred active packets after this batch: 15
owner_module: cortex_m0lite_core
owner_file: rtl/cortex_m0lite_core.sv

SSOT observable latency contract:
{
  "cycle_model.latency": 3,
  "cycle_model.pipeline": [
    {
      "action": "Fetch request/acceptance.",
      "cycle": 0,
      "stage": "IF"
    },
    {
      "action": "Decode + regfile read + hazard decision.",
      "cycle": 1,
      "stage": "ID"
    },
    {
      "action": "Execute/memory response/writeback/retire.",
      "cycle": 2,
      "stage": "EX_WB"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": "if_id_valid && if_id_ready or id_ex_valid && id_ex_ready or ex_wb_valid && ex_wb_ready",
  "timing.latency_budget": {
    "branch_flush": {
      "max": 2,
      "measured_from": "branch_resolved",
      "measured_to": "redirected_fetch_valid",
      "min": 1
    },
    "load_use_stall": {
      "max": 1,
      "measured_from": "load_use_detected",
      "measured_to": "dependent_instruction_reissued",
      "min": 1
    },
    "reset_release": {
      "max": 3,
      "measured_from": "raw_reset_deassert",
      "measured_to": "synchronized_reset_deassert",
      "min": 2
    }
  }
}

Locked SSOT YAML excerpt (cortex_m0lite/yaml/cortex_m0lite.ssot.yaml):
top_module:
  name: cortex_m0lite
  file: rtl/cortex_m0lite.sv
  version: "1.0"
  type: cpu
  reference_spec: "user-defined Cortex-M0-lite subset SSOT"
  description: "Cortex-M0-lite style 3-stage microcontroller core (IF/ID/EX-WB) with AHB-Lite instruction/data master ports."
  owner: ssot-manual
  quality_profile: strict
  target:
    technology: sky130
    clock_freq_mhz: 300
    bus_freq_mhz: 150
    area_um2: null
    power_mw: null

sub_modules:
  - name: cortex_m0lite
    file: rtl/cortex_m0lite.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - integration.connections
      - io_list.interfaces
      - clock_reset_domains
      - cdc_requirements
    source_sections:
      - io_list
      - internal_interfaces
      - integration
      - clock_reset_domains
      - cdc_requirements
    wiring_only: true
    description: "Top-level integration wrapper that exposes SSOT top IO and instantiates core/stage modules."
  - name: cortex_m0lite_core
    file: rtl/cortex_m0lite_core.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - function_model.transactions.FM_CPU_STEP
      - cycle_model.pipeline
      - fsm.control
      - registers.register_list
    source_sections:
      - io_list
      - parameters
      - decomposition
      - registers
      - function_model
      - cycle_model
      - fsm
      - error_handling
      - dataflow
      - coverage_tap
      - workflow_todos
    dataflow_refs:
      - dataflow.sequence
      - dataflow.ordering
      - dataflow.state_flow
    description: "Top CPU integration block that owns fetch/decode/execute/writeback and AHB transactions."
  - name: if_stage
    file: rtl/cortex_m0lite_if_stage.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - cycle_model.pipeline
      - isa_spec.decode_contract
    source_sections:
      - io_list
      - parameters
      - cycle_model
      - isa_spec
      - dataflow
    dataflow_refs:
      - dataflow.sequence
      - dataflow.ordering
    description: "Instruction fetch stage with PC sequencing and I-bus request control."
  - name: id_stage
    file: rtl/cortex_m0lite_id_stage.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - isa_spec.decode_rule_set
      - function_model.transactions.FM_CPU_STEP
    source_sections:
      - parameters
      - isa_spec
      - function_model
      - coverage_tap
      - dataflow
    dataflow_refs:
      - dataflow.sequence
      - dataflow.ordering
    description: "Instruction decode stage with operand extraction, immediate generation, and hazard detect."
  - name: ex_stage
    file: rtl/cortex_m0lite_ex_stage.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - function_model.transactions.FM_CPU_STEP
      - error_handling
    source_sections:
      - parameters
      - function_model
      - error_handling
      - coverage_tap
      - dataflow
    dataflow_refs:
      - dataflow.sequence
      - dataflow.ordering
    description: "Execute stage for ALU operations, branch target generation, and memory address generation."
  - name: wb_stage
    file: rtl/cortex_m0lite_wb_stage.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - function_model.transactions.FM_CPU_STEP
      - registers.register_list
    source_sections:
      - registers
      - function_model
      - error_handling
      - dataflow
    dataflow_refs:
      - dataflow.sequence
      - dataflow.ordering
    description: "Writeback/commit stage for register file and architectural retire/trap visibility."
  - name: regfile
    file: rtl/cortex_m0lite_regfile.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - registers.register_list
      - function_model.state_variables
    source_sections:
      - parameters
      - registers
      - function_model
    description: "16x32 register file storage and read/write arbitration."
  - name: bus_if
    file: rtl/cortex_m0lite_bus_if.sv
    ownership: manifest
    rtl_emit: true
    implements:
      - io_list.interfaces
      - error_handling
    source_sections:
      - io_list
      - parameters
      - error_handling
      - cycle_model
    description: "AHB-Lite instruction/data interface adapter with ready/resp handling."

decomposition:
  modules:
    - name: if_stage
      role: instruction fetch and PC sequencing
      owns: [pc_q, if_valid_q]
    - name: id_stage
      role: decode, immediate generation, and hazard detect
      owns: [id_instr_q, id_pc_q]
    - name: ex_stage
      role: ALU, branch decision, address generation
      owns: [ex_valid_q, ex_result_q]
    - name: wb_stage
      role: register file writeback and architectural commit
      owns: [commit_q]
    - name: regfile
      role: 16x32 architectural register file (R0-R15)
      owns: [rf_mem]
    - name: bus_if
      role: AHB-Lite I/D request and response handling
      owns: [ihold_q, dhold_q]
  ownership:
    function_model: cortex_m0lite_core
    cycle_model: cortex_m0lite_core
    rtl_contract: cortex_m0lite_core

parameters:
  - name: XLEN
    type: int
    default: 32
    user_editable: true
    description: "Datapath width."
  - name: RESET_PC
    type: int
    default: 0
    user_editable: true
    description: "Program counter reset vector."
  - name: TRAP_VECTOR
    type: int
    default: 128
    user_editable: true
    description: "Exception/trap vector base address. Must be 4-byte aligned."
  - name: STACK_RESET
    type: int
    default: 0
    user_editable: true
    description: "Reset value for architectural R13/SP."
  - name: REG_COUNT
    type: int
    default: 16
    user_editable: true
    description: "Architectural register count."
  - name: AHB_ADDR_W
    type: int
    default: 32
    user_editable: true
    description: "AHB address width."
  - name: AHB_DATA_W
    type: int
    default: 32
    user_editable: true
    description: "AHB data width."
  - name: CORE_FREQ_MHZ
    type: int
    default: 300
    user_editable: true
    description: "Core clock target frequency in MHz."
  - name: BUS_FREQ_MHZ
    type: int
    default: 150
    user_editable: true
    description: "Bus clock target frequency in MHz."
  - name: AHB_HTRANS_IDLE
    type: int
    default: 0
    user_editable: false
    description: "AHB-Lite HTRANS IDLE encoding."
  - name: AHB_HTRANS_BUSY
    type: int
    default: 1
    user_editable: false
    description: "AHB-Lite HTRANS BUSY encoding; core does not generate BUSY in this revision."
  - name: AHB_HTRANS_NONSEQ
    type: int
    default: 2
    user_editable: false
    description: "AHB-Lite HTRANS NONSEQ encoding used for every single-beat transfer."
  - name: AHB_HTRANS_SEQ
    type: int
    default: 3
    user_editable: false
    description: "AHB-Lite HTRANS SEQ encoding; reserved for future bursts."
  - name: AHB_HSIZE_WORD
    type: int
    default: 2
    user_editable: false
    description: "AHB-Lite HSIZE value for 32-bit word transfers."
  - name: AHB_HBURST_SINGLE
    type: int
    default: 0
    user_editable: false
    description: "AHB-Lite HBURST SINGLE encoding."

io_list:
  clock_domains:
    - name: core_clk
      frequency_mhz: 300
      description: "Core clock at 300 MHz."
      ports:
        - { name: clk, direction: input, width: 1, description: "Core clock." }
    - name: bus_clk
      frequency_mhz: 150
      description: "AHB bus clock at 150 MHz, synchronous 2:1 divided from core clock source."
      ports:
        - { name: hclk, direction: input, width: 1, description: "AHB bus clock." }
  resets:
    - name: core_rst_n
      active: low
      polarity: active_low
      sync_async: async_assert_sync_deassert
      ports:
        - { name: rst_n, direction: input, width: 1, description: "Async active-low reset." }
    - name: bus_rst_n
      active: low
      polarity: active_low
      sync_async: async_assert_sync_deassert
      ports:
        - { name: hresetn, direction: input, width: 1, description: "AHB bus reset, active-low." }
  reset_strategy:
    mode: "async_assert_sync_deassert"
    policy:
      - "External rst_n/hresetn may assert asynchronously."
      - "Deassertion must pass through per-domain internal reset synchronizers."
    synchronized_resets:
      - name: core_rst_n_sync
        source: rst_n
        clock: clk
        stages: 2
        fanout_domains: [core_clk]
      - name: bus_rst_n_sync
        source: hresetn
        clock: hclk
        stages: 2
        fanout_domains: [bus_clk]
    constraints:
      - "No sequential element in core_clk domain may use raw rst_n deassert directly."
      - "No sequential element in bus_clk domain may use raw hresetn deassert directly."
      - "CDC wrappers must use synchronized reset of their local domain."
  interfaces:
    - name: instr_ahb_m
      type: ahb_lite_master
      clock_domain: bus_clk
      reset_domain: bus_rst_n
      protocol:
        transfer_size: word32
        hsize_value: AHB_HSIZE_WORD
        hburst_value: AHB_HBURST_SINGLE
        generated_htrans: [AHB_HTRANS_IDLE, AHB_HTRANS_NONSEQ]
        busy_policy: "BUSY is not generated by this core. If a future bridge inserts BUSY, it is not a completed transfer."
        idle_values:
          i_htrans: AHB_HTRANS_IDLE
          i_hwrite: 0
          i_hsize: AHB_HSIZE_WORD
          i_hburst: AHB_HBURST_SINGLE
          i_hwdata: 0
        active_values:
          i_htrans: AHB_HTRANS_NONSEQ
          i_hwrite: 0
          i_hsize: AHB_HSIZE_WORD
          i_hburst: AHB_HBURST_SINGLE
        hold_rules:
          - "When i_hready=0, hold i_haddr/i_htrans/i_hwrite/i_hsize/i_hburst stable."
          - "Instruction fetch address must be halfword aligned; i_haddr[0] is 0."
          - "For 32-bit AHB fetch beat, align i_haddr[1:0] to 2'b00 and select the requested halfword from i_hrdata."
        completion_rules:
          - "i_hready=1 and i_hresp=0 completes the fetch beat."
          - "i_hready=1 and i_hresp=1 raises instruction bus fault with trap_code=2."
      ports:
        - { name: i_haddr, direction: output, width: AHB_ADDR_W, parameter_ref: AHB_ADDR_W }
        - { name: i_htrans, direction: output, width: 2 }
        - { name: i_hwrite, direction: output, width: 1 }
        - { name: i_hsize, direction: output, width: 3 }
        - { name: i_hburst, direction: output, width: 3 }
        - { name: i_hwdata, direction: output, width: AHB_DATA_W, parameter_ref: AHB_DATA_W }
        - { name: i_hrdata, direction: input, width: AHB_DATA_W, parameter_ref: AHB_DATA_W }
        - { name: i_hready, direction: input, width: 1 }
        - { name: i_hresp, direction: input, width: 1 }
    - name: data_ahb_m
      type: ahb_lite_master
      clock_domain: bus_clk
      reset_domain: bus_rst_n
      protocol:
        transfer_size: word32
        hsize_value: AHB_HSIZE_WORD
        hburst_value: AHB_HBURST_SINGLE
        generated_htrans: [AHB_HTRANS_IDLE, AHB_HTRANS_NONSEQ]
        busy_policy: "BUSY is not generated by this core. SEQ is reserved for future burst extension."
        idle_values:
          d_htrans: AHB_HTRANS_IDLE
          d_hwrite: 0
          d_hsize: AHB_HSIZE_WORD
          d_hburst: AHB_HBURST_SINGLE
          d_hwdata: 0
        active_values:
          load:
            d_htrans: AHB_HTRANS_NONSEQ
            d_hwrite: 0
            d_hsize: AHB_HSIZE_WORD
            d_hburst: AHB_HBURST_SINGLE
          store:
            d_htrans: AHB_HTRANS_NONSEQ
            d_hwrite: 1
            d_hsize: AHB_HSIZE_WORD
            d_hburst: AHB_HBURST_SINGLE
        hold_rules:
          - "When d_hready=0, hold d_haddr/d_htrans/d_hwrite/d_hsize/d_hburst/d_hwdata stable."
          - "LDR/STR word access requires d_haddr[1:0] == 2'b00 before launching the bus transfer."
          - "If misalignment is detected, suppress d_htrans=NONSEQ and raise trap_code=3."
        completion_rules:
          - "d_hready=1 and d_hresp=0 completes the load/store beat."
          - "d_hready=1 and d_hresp=1 raises data bus fault with trap_code=2."
          - "LDR writeback occurs only after successful response; STR has no register writeback."
      ports:
        - { name: d_haddr, direction: output, width: AHB_ADDR_W, parameter_ref: AHB_ADDR_W }
        - { name: d_htrans, direction: output, width: 2 }
        - { name: d_hwrite, direction: output, width: 1 }
        - { name: d_hsize, direction: output, width: 3 }
        - { name: d_hburst, direction: output, width: 3 }
        - { name: d_hwdata, direction: output, width: AHB_DATA_W, parameter_ref: AHB_DATA_W }
        - { name: d_hrdata, direction: input, width: AHB_DATA_W, parameter_ref: AHB_DATA_W }
        - { name: d_hready, direction: input, width: 1 }
        - { name: d_hresp, direction: input, width: 1 }
    - name: irq_if
      type: custom_irq
      clock_domain: core_clk
      reset_domain: core_rst_n
      protocol:
        sampling: "irq is sampled on rising edge of clk when core_rst_n_sync is deasserted."
        active_level: high
        synchronization: "External irq must pass through a 2-flop synchronizer before decode/control consumption."
        hold_requirement: "irq must remain high for at least two core_clk cycles to guarantee capture."
        response: "Interrupt request is observed for debug/coverage only in this revision; architectural interrupt entry is a future SSOT extension."
      ports:
        - { name: irq, direction: input, width: 1, description: "Single external interrupt line." }
    - name: debug_status
      type: custom_debug
      clock_domain: core_clk
      reset_domain: core_rst_n
      protocol:
        update_edge: "pc_dbg/state_dbg/retire/trap update on rising edge of clk."
        reset_values:
          pc_dbg: RESET_PC
          state_dbg: 0
          retire: 0
          trap: 0
        pulse_rules:
          - "retire is a one-core_clk-cycle pulse for a successful commit."
          - "trap is a one-core_clk-cycle pulse when trap metadata is captured."
        stability: "pc_dbg and state_dbg hold their previous values while the pipeline is stalled."
      ports:
        - { name: pc_dbg, direction: output, width: XLEN, parameter_ref: XLEN }
        - { name: state_dbg, direction: output, width: 3 }
        - { name: retire, direction: output, width: 1, description: "One-cycle retire pulse." }
        - { name: trap, direction: output, width: 1, description: "Trap/exception indicator." }

internal_interfaces:
  - name: if_to_id
    from: if_stage
    to: id_stage
    handshake: valid_ready
    signals:
      - { name: if_id_valid, width: 1, direction: output }
      - { name: if_id_ready, width: 1, direction: input }
      - { name: if_id_pc, width: XLEN, parameter_ref: XLEN, direction: output }
      - { name: if_id_instr, width: 16, direction: output }
      - { name: if_id_fault, width: 1, direction: output }
    timing:
      - "Payload is sampled on cycle where valid && ready."
      - "flush/trap clears if_id_valid in same or next cycle per pipeline control."
  - name: id_to_ex
    from: id_stage
    to: ex_stage
    handshake: valid_ready
    signals:
      - { name: id_ex_valid, width: 1, direction: output }
      - { name: id_ex_ready, width: 1, direction: input }
      - { name: id_ex_op_class, width: 3, direction: output }
      - { name: id_ex_pc, width: XLEN, parameter_ref: XLEN, direction: output }
      - { name: id_ex_rd, width: 4, direction: output }
      - { name: id_ex_rn_val, width: XLEN, parameter_ref: XLEN, direction: output }
      - { name: id_ex_rm_val, width: XLEN, parameter_ref: XLEN, direction: output }
      - { name: id_ex_imm, width: XLEN, parameter_ref: XLEN, direction: output }
      - { name: id_ex_decode_fault, width: 1, direction: output }
    timing:
      - "Hazard stall deasserts id_ex_valid and holds decode state."
      - "Branch flush kills in-flight id_ex_valid before execution commit."
  - name: ex_to_wb
    from: ex_stage
    to: wb_stage
    handshake: valid_ready
    signals:
      - { name: ex_wb_valid, width: 1, direction: output }
      - { name: ex_wb_ready, width: 1, direction: input }
      - { name: ex_wb_rd, width: 4, direction: output }
      - { name: ex_wb_result, width: XLEN, parameter_ref: XLEN, direction: output }
      - { name: ex_wb_flags, width: 4, direction: output }
      - { name: ex_wb_regwrite, width: 1, direction: output }
      - { name: ex_wb_retire_ok, width: 1, direction: output }
      - { name: ex_wb_trap, width: 1, direction: output }
      - { name: ex_wb_trap_code, width: 7, direction: output }
    timing:
      - "Retire pulse is generated by WB stage only when ex_wb_valid && ex_wb_retire_ok && !ex_wb_trap."
  - name: id_to_regfile
    from: id_stage
    to: regfile
    handshake: combinational_read
    signals:
      - { name: id_rf_raddr_a, width: 4, direction: output }
      - { name: id_rf_raddr_b, width: 4, direction: output }
      - { name: rf_id_rdata_a, width: XLEN, parameter_ref: XLEN, direction: input }
      - { name: rf_id_rdata_b, width: XLEN, parameter_ref: XLEN, direction: input }
    timing:
      - "Read data must be stable within ID stage cycle budget."
  - name: wb_to_regfile
    from: wb_stage
    to: regfile
    handshake: write_enable
    signals:
      - { name: wb_rf_we, width: 1, direction: output }
      - { name: wb_rf_waddr, width: 4, direction: output }
      - { name: wb_rf_wdata, width: XLEN, parameter_ref: XLEN, direction: output }
    timing:
      - "Writeback occurs on commit boundary only."
      - "Trap commit suppresses wb_rf_we for offending instruction."
  - name: if_to_bus
    from: if_stage
    to: bus_if
    handshake: req_ack
    clock_domain: bus_clk
    signals:
      - { name: if_bus_req, width: 1, direction: output }
      - { name: if_bus_addr, width: AHB_ADDR_W, parameter_ref: AHB_ADDR_W, direction: output }
      - { name: bus_if_ack, width: 1, direction: input }
      - { name: bus_if_rdata, width: 16, direction: input }
      - { name: bus_if_fault, width: 1, direction: input }
    timing:
      - "IF request holds until ack or fault."
      - "Fault response propagates as if_id_fault."
  - name: ex_to_bus
    from: ex_stage
    to: bus_if
    handshake: req_ack
    clock_domain: bus_clk
    signals:
      - { name: ex_bus_req, width: 1, direction: output }
      - { name: ex_bus_we, width: 1, direction: output }
      - { name: ex_bus_addr, width: AHB_ADDR_W, parameter_ref: AHB_ADDR_W, direction: output }
      - { name: ex_bus_wdata, width: XLEN, parameter_ref: XLEN, direction: output }
      - { name: bus_ex_ack, width: 1, direction: input }
      - { name: bus_ex_rdata, width: XLEN, parameter_ref: XLEN, direction: input }
      - { name: bus_ex_fault, width: 1, direction: input }
    timing:
      - "Load/store request remains asserted until ack/fault."
      - "bus_ex_fault maps to trap_code=2 unless misalign precheck already asserted trap_code=3."
  - name: global_control
    from: cortex_m0lite_core
    to: [if_stage, id_stage, ex_stage, wb_stage, bus_if]
    handshake: level_control
    signals:
      - { name: pipe_flush, width: 1, direction: output }
      - { name: trap_enter, width: 1, direction: output }
      - { name: trap_code, width: 7, direction: output }
      - { name: stall_if, width: 1, direction: output }
      - { name: stall_id, width: 1, direction: output }
    timing:
      - "trap_enter has priority over stall and normal advance."
      - "pipe_flush clears IF/ID then resumes fetch from trap/branch target."
  - name: core_bus_cdc
    from: cortex_m0lite_core
    to: bus_if
    handshake: sync_2to1
    clock_domain: crossing_core_to_bus
    signals:
      - { name: cdc_req_valid, width: 1, direction: output }
      - { name: cdc_req_ready, width: 1, direction: input }
      - { name: cdc_rsp_valid, width: 1, direction: input }
      - { name: cdc_rsp_ready, width: 1, direction: output }
    timing:
      - "Synchronous divided clocks: core_clk:bus_clk = 2:1 (300MHz:150MHz nominal)."
      - "core requests are launched on core_clk and sampled on aligned bus_clk boundaries."
      - "No combinational timing path is allowed across clock-domain boundary wrappers."
      - "Reset release for CDC boundary logic uses domain-local synchronized resets (core_rst_n_sync, bus_rst_n_sync)."

registers:
  address_unit: byte
  data_width: XLEN
  bit_order: lsb0
  bits_format: "[msb, lsb]"
  access_model: "Internal architectural/debug register map; this revision has no external CSR slave port."
  reserved_field_policy:
    read_value: 0
    write_effect: ignore
    rtl_requirement: "Reserved fields must be tied to zero on readback and must not create storage."
  register_file:
    owner: regfile
    physical_storage: rf_mem[0:14]
    pc_alias: "Architectural R15 reads pc_q; R15 is not a writable physical rf_mem entry."
    retention_policy: none
    reset_policy:
      - "R0-R12 reset to 0 on core_rst_n_sync assertion."
      - "R13/SP resets to STACK_RESET."
      - "R14/LR resets to 0."
      - "R15/PC resets through pc_q to RESET_PC."
    write_policy:
      - "Only non-trapped committing ALU/MOV/LDR instructions may assert wb_rf_we."
      - "Writes to R0-R14 update rf_mem on the commit edge."
      - "Writes targeting R15 are not supported by this subset and must raise illegal opcode trap_code=1."
      - "Trap entry suppresses rf_mem writes for the offending instruction."
    read_policy:
      - "Reads of R0-R14 return rf_mem."
      - "Reads of R15 return aligned architectural PC view with bit[0]=0."
  register_list:
    - name: XPSR
      offset: 0x00
      width: XLEN
      access: ro
      hw_access: rw
      reset: 0x00000000
      owner: wb_stage
      description: "Architectural condition flags visible for debug/scoreboard."
      write_side_effects:
        - "ADD/SUB/CMP update N/Z/C/V according to function_model.flag_formulas."
        - "AND/ORR/EOR/MOV update N/Z only and preserve C/V."
        - "Trap entry does not update XPSR for the offending instruction."
      fields:
        - { name: n, bits: [31, 31], lsb: 31, width: 1, access: ro, hw_access: rw, reset: 0, description: "Negative flag; mirrors nzcv_q[3]." }
        - { name: z, bits: [30, 30], lsb: 30, width: 1, access: ro, hw_access: rw, reset: 0, description: "Zero flag; mirrors nzcv_q[2]." }
        - { name: c, bits: [29, 29], lsb: 29, width: 1, access: ro, hw_access: rw, reset: 0, description: "Carry/not-borrow flag; mirrors nzcv_q[1]." }
        - { name: v, bits: [28, 28], lsb: 28, width: 1, access: ro, hw_access: rw, reset: 0, description: "Signed overflow flag; mirrors nzcv_q[0]." }
        - { name: reserved_27_0, bits: [27, 0], lsb: 0, width: 28, access: reserved, reset: 0, read_value: 0, write_effect: ignore, description: "Reserved; reads zero." }
    - name: PC
      offset: 0x04
      width: XLEN
      access: ro
      hw_access: rw
      reset: RESET_PC
      owner: if_stage
      description: "Architectural program counter debug view."
      write_side_effects:
        - "Normal sequential commit sets pc_q to pc_q+2."
        - "Taken branch sets pc_q to branch target and flushes IF/ID."
        - "Trap entry captures EXC_EPC then sets pc_q to TRAP_VECTOR."
        - "Exception return is not architecturally supported in this revision; reset is the only trap recovery path."
      fields:
        - { name: pc, bits: [31, 0], lsb: 0, width: XLEN, parameter_ref: XLEN, access: ro, hw_access: rw, reset: RESET_PC, alignment: 2, description: "Aligned architectural PC; bit[0] is always 0." }
    - name: EXC_CAUSE
      offset: 0x08
      width: XLEN
      access: ro
      hw_access: rw
      reset: 0x00000000
      owner: wb_stage
      description: "Precise trap cause metadata captured at trap entry."
      write_side_effects:
        - "trap_valid sets in the same commit boundary that suppresses retire."
        - "trap_code stores highest-priority error_handling.priority code."
        - "trap_stage stores the pipeline stage that detected the fault."
        - "Fields clear on reset only; exception return is reserved for a future SSOT revision."
      fields:
        - { name: trap_valid, bits: [0, 0], lsb: 0, width: 1, access: ro, hw_access: rw, reset: 0, set_by: trap_enter, clear_by: [reset], description: "Sticky trap valid until reset." }
        - { name: trap_code, bits: [7, 1], lsb: 1, width: 7, access: ro, hw_access: rw, reset: 0, enum: { illegal_opcode: 1, bus_error: 2, misaligned_word_access: 3 }, description: "Trap reason code." }
        - { name: trap_stage, bits: [10, 8], lsb: 8, width: 3, access: ro, hw_access: rw, reset: 0, enum: { if_stage: 1, id_stage: 2, ex_stage: 3, wb_stage: 4 }, description: "Stage that raised the precise trap." }
        - { name: reserved_31_11, bits: [31, 11], lsb: 11, width: 21, access: reserved, reset: 0, read_value: 0, write_effect: ignore, description: "Reserved; reads zero." }
    - name: EXC_EPC
      offset: 0x0C
      width: XLEN
      access: ro
      hw_access: rw
      reset: RESET_PC
      owner: wb_stage
      description: "Exception program counter captured from the offending instruction PC."
      write_side_effects:
        - "On trap entry, captures fault_pc before pc_q redirects to TRAP_VECTOR."
        - "Bit[0] is forced to 0 because this core executes aligned 16-bit instructions."
      fields:
        - { name: epc, bits: [31, 0], lsb: 0, width: XLEN, parameter_ref: XLEN, access: ro, hw_access: rw, reset: RESET_PC, alignment: 2, description: "Faulting instruction PC." }

features:
  - name: thumb_subset_execute
    description: "Supports a constrained Thumb-like subset: ADD/SUB/AND/ORR/EOR/MOV/CMP/LDR/STR/B/BEQ/BNE."
  - name: 3stage_pipeline
    description: "Pipeline stages IF -> ID -> EX/WB with bubble insertion and branch flush."
  - name: load_use_hazard_handling
    description: "Single-cycle stall on load-use hazard; simple forwarding for ALU-ALU dependency."
  - name: precise_trap
    description: "Trap raised at commit boundary for illegal opcode, bus error, and misaligned access."

isa_spec:
  profile: "Thumb-like subset for Cortex-M0-lite bring-up"
  mode: "16-bit instruction encoding only"
  decode_style: "rule_based_no_fixed_table"
  policy:
    - "Do not use a fixed opcode lookup table in SSOT."
    - "Decoder must be derived from class rules + field constraints + priority."
  instruction_classes:
    - name: alu_reg_imm
      instructions: [ADD, SUB, AND, ORR, EOR, MOV, CMP]
      semantics:
        - "ADD/SUB/CMP update N,Z,C,V."
        - "AND/ORR/EOR update N,Z and keep C,V unchanged."
        - "MOV updates N,Z and does not modify C,V."
      writeback_rules:
        - "CMP writes flags only, no destination register write."
        - "Other ALU ops write rd in EX/WB commit."
    - name: load_store
      instructions: [LDR, STR]
      addressing:
        - "Base + imm5<<2 for word accesses."
        - "Word alignment required: addr[1:0] must be 2'b00."
      bus_mapping:
        - "LDR issues AHB read (HTRANS=NONSEQ, HWRITE=0)."
        - "STR issues AHB write (HTRANS=NONSEQ, HWRITE=1)."
    - name: branch
      instructions: [B, BEQ, BNE]
      conditions:
        - "BEQ taken when Z==1."
        - "BNE taken when Z==0."
      pc_rule:
        - "Target = align2(PC+2) + sign_extend(offset)<<1."
  decode_contract:
    - "Unsupported opcode must raise illegal-instruction trap."
    - "Decode priority is deterministic: exact opcode match before class fallback."
    - "Class priority order: branch > load_store > alu_reg_imm > illegal."
    - "When multiple class patterns match, select the highest-priority class and raise coverage event decode_overlap_resolved."
    - "Field constraints are mandatory: rd/rn/rm must be in [0, REG_COUNT-1], immediate width/sign must match class rule."
  decode_rule_set:
    - rule: alu_reg_imm
      discriminator: "instr_word[15:13] in implementation-defined ALU class window"
      required_constraints:
        - "rd/rn/rm indices valid"
        - "immediate form matches selected ALU op variant"
      resolve:
        - "if op modifies flags -> apply nzcv policy in same commit cycle"
    - rule: load_store
      discriminator: "instr_word[15:13] in implementation-defined MEM class window"
      required_constraints:
        - "base register valid"
        - "offset scaling applied for word access"
        - "effective address word-aligned"
      resolve:
        - "misalignment check happens before bus launch"
    - rule: branch
      discriminator: "instr_word[15:13] in implementation-defined BR class window"
      required_constraints:
        - "offset sign extension follows class rule"
        - "conditional branch checks current nzcv"
      resolve:
        - "taken branch flushes IF/ID"
        - "not-taken branch commits as control-flow no-op"
  excluded_instructions:
    - "BL, BX, PUSH, POP, LDM/STM, MUL, SVC, BKPT, CPS, WFI/WFE are out of scope in this revision."

dataflow:
  sequence:
    - "IF issues instruction fetch request and captures instruction when i_hready is high."
    - "ID decodes instruction, reads regfile, and computes immediate/control."
    - "EX executes ALU/branch/address generation and launches data AHB for LDR/STR."
    - "WB commits architectural state and emits retire pulse."
  ordering:
    - "Reset dominates all control."
    - "Trap dominates writeback and starts flush sequence."
    - "Branch taken flushes IF/ID before next fetch."
  state_flow:
    - "PC -> IF fetch addr -> ID instr -> EX result -> WB regfile/flags"
    - "EX mem request -> data bus response -> WB load data commit"

function_model:
  purpose: "Architectural CPU reference for RTL equivalence and scoreboard."
  state_variables:
    - { name: pc_q, width: XLEN, reset: RESET_PC, description: "Architectural program counter." }
    - { name: rf_q, width: 32, reset: 0, description: "R0-R15 register array abstraction." }
    - { name: nzcv_q, width: 4, reset: 0, description: "Condition flags N,Z,C,V." }
    - { name: trap_q, width: 1, reset: 0, description: "Trap sticky state until handler vectoring." }
  transactions:
    - id: FM_CPU_STEP
      name: cpu_cycle_step
      required_fields: [instr_word, instr_valid, i_hready, d_hready, d_hrdata, irq]
      preconditions:
        - "core_rst_n_sync and bus_rst_n_sync are deasserted."
        - "instr_valid indicates a 16-bit instruction word is available from the IF path."
        - "Any data access waits for the declared AHB-Lite ready/response contract."
      outputs: [pc_dbg, retire, trap]
      decode_rules:
        - "Decode instr_word into opcode/rd/rn/rm/imm fields per isa_spec."
        - "If decode miss occurs, set trap_code=1 and suppress retire."
        - "If decode class overlap occurs, resolve by decode_contract class priority and emit overlap telemetry."
      memory_rules:
        - "LDR retires only when d_hready=1 and d_hresp=0."
        - "STR retires only when d_hready=1 and d_hresp=0."
        - "Any d_hresp=1 raises trap_code=2."
        - "Word misalignment on LDR/STR raises trap_code=3 before bus launch."
      branch_rules:
        - "Taken branch flushes IF/ID and redirects pc_q to target."
        - "Not-taken branch advances to sequential pc."
      operand_rules:
        - "ADD/SUB/CMP use rn (+ rm or imm) and optional rd writeback."
        - "MOV writes rd from source operand and updates N/Z only."
        - "LDR writes rd on successful bus response only."
        - "STR has no register writeback."
      flag_formulas:
        - "N := result[XLEN-1]"
        - "Z := (result == 0)"
        - "C := carry_out for ADD, not_borrow for SUB/CMP, unchanged for logical ops unless explicitly defined"
        - "V := signed overflow for ADD/SUB/CMP, unchanged for logical ops unless explicitly defined"
      output_rules:
        - name: retire_pulse
          port: retire
          width: 1
          expr: "1 when one instruction commits without trap, else 0"
        - name: trap_flag
          port: trap
          width: 1
          expr: "1 when illegal opcode, bus error, or misalignment is detected at commit boundary"
      state_updates:
        - name: pc_q
          width: XLEN
          reset: RESET_PC
          expr: "pc+2 on normal flow; branch target on taken branch; trap vector on exception"
        - name: rf_q
          width: 32
          reset: 0
          expr: "register writeback on ALU/LDR/MOV commit only"
        - name: nzcv_q
          width: 4
          reset: 0
          expr: "updated by arithmetic/compare instructions per ARM-like semantics"
      error_cases:
        - "Illegal instruction encoding -> trap_code=1"
        - "Instruction/data bus error (HRESP=1) -> trap_code=2"
        - "Misaligned word access -> trap_code=3"
      side_effects:
        - "Successful ALU/MOV/LDR instructions update the destination architectural register at commit."
        - "Arithmetic and compare instructions update NZCV according to flag_formulas."
        - "Taken branches redirect pc_q and flush IF/ID before the next fetch."
        - "Trap conditions suppress retire of the offending instruction and update exception metadata only."
  invariants:
    - "R15 reflects architectural PC view at commit."
    - "No architectural state update on trapped instruction except exception metadata."
    - "At most one retire pulse per cycle."
    - "x0-like behavior is not used; all R0-R15 are normal ARM-style architectural registers."
    - "No instruction commits while trap_q is active until trap vectoring completes."

cycle_model:
  executable: pymtl3
  backend_policy: "Use PyMTL3 cycle shell; keep FunctionModel as golden architecture model."
  clock: clk
  reset: rst_n
  latency: 3
  pipeline:
    - { stage: IF, cycle: 0, action: "Fetch request/acceptance." }
    - { stage: ID, cycle: 1, action: "Decode + regfile read + hazard decision." }
    - { stage: EX_WB, cycle: 2, action: "Execute/memory response/writeback/retire." }
  handshake_rules:
    - name: if_wait
      description: "IF holds request when i_hready=0."
    - name: dmem_wait
      description: "Load/store completion waits for d_hready=1."
    - name: hazard_stall
      description: "Load-use dependency inserts one bubble."
  ordering:
    - "Reset dominates all pipeline movement and clears valid bits before instruction retirement."
    - "Trap entry has priority over branch redirect, writeback, and normal sequential PC update."
    - "Branch taken flushes IF/ID before the redirected fetch becomes visible."
    - "Load/store bus completion gates retire; no LDR/STR commits before d_hready && !d_hresp."
    - "core_clk:bus_clk is a synchronous 2:1 relationship; bus boundary logic samples requests only on aligned bus_clk cycles."
  performance:
    target_fmax_mhz: 300
    bus_fmax_mhz: 150
    clock_ratio_core_to_bus: "2:1"
    target_cpi_typical: 1.2
    outstanding_depth:
      instruction: 1
      data: 1

fsm:
  control:
    state_bits: 3
    states:
      - { name: RESET, code: 0 }
      - { name: FETCH, code: 1 }
      - { name: DECODE, code: 2 }
      - { name: EXECUTE, code: 3 }
      - { name: MEM_WAIT, code: 4 }
      - { name: TRAP, code: 5 }
    transitions:
      - "RESET -> FETCH when rst_n=1"
      - "FETCH -> DECODE when i_hready=1 and instr_valid=1"
      - "DECODE -> EXECUTE when no stall"
      - "EXECUTE -> MEM_WAIT for load/store with d_hready=0"
      - "MEM_WAIT -> FETCH when d_hready=1"
      - "EXECUTE -> TRAP on trap condition"
      - "TRAP -> FETCH after trap PC setup"
  submodule_fsms:
    - name: if_stage_fsm
      owner: if_stage
      state_bits: 2
      states:
        - { name: IF_IDLE, code: 0 }
        - { name: IF_REQ, code: 1 }
        - { name: IF_WAIT, code: 2 }
        - { name: IF_LATCH, code: 3 }
      transitions:
        - "IF_IDLE -> IF_REQ when fetch_enable=1"
        - "IF_REQ -> IF_LATCH when i_hready=1 and i_hresp=0"
        - "IF_REQ -> IF_WAIT when i_hready=0"
        - "IF_WAIT -> IF_LATCH when i_hready=1 and i_hresp=0"
        - "IF_REQ/IF_WAIT -> IF_IDLE on trap or flush"
        - "IF_LATCH -> IF_REQ for next fetch"
    - name: id_stage_fsm
      owner: id_stage
      state_bits: 2
      states:
        - { name: ID_IDLE, code: 0 }
        - { name: ID_DECODE, code: 1 }
        - { name: ID_STALL, code: 2 }
        - { name: ID_BUBBLE, code: 3 }
      transitions:
        - "ID_IDLE -> ID_DECODE when if_valid=1"
        - "ID_DECODE -> ID_STALL on load_use_hazard"
        - "ID_DECODE -> ID_BUBBLE on branch_flush"
        - "ID_STALL -> ID_DECODE when hazard_cleared=1"
        - "ID_BUBBLE -> ID_IDLE after one cycle bubble insert"
    - name: ex_stage_fsm
      owner: ex_stage
      state_bits: 2
      states:
        - { name: EX_IDLE, code: 0 }
        - { name: EX_ALU, code: 1 }
        - { name: EX_MEM, code: 2 }
        - { name: EX_TRAP, code: 3 }
      transitions:
        - "EX_IDLE -> EX_ALU when id_valid and op_class=alu_reg_imm"
        - "EX_IDLE -> EX_MEM when id_valid and op_class=load_store"
        - "EX_ALU -> EX_IDLE after alu_result_ready"
        - "EX_MEM -> EX_IDLE when d_hready=1 and d_hresp=0"
        - "EX_MEM -> EX_TRAP when d_hresp=1 or misalign=1"
        - "EX_ALU -> EX_TRAP when illegal_decode=1"
        - "EX_TRAP -> EX_IDLE after trap_latched"
    - name: wb_stage_fsm
      owner: wb_stage
      state_bits: 2
      states:
        - { name: WB_IDLE, code: 0 }
        - { name: WB_COMMIT, code: 1 }
        - { name: WB_TRAP_COMMIT, code: 2 }
        - { name: WB_HOLD, code: 3 }
      transitions:
        - "WB_IDLE -> WB_COMMIT when ex_valid and trap=0"
        - "WB_IDLE -> WB_TRAP_COMMIT when ex_valid and trap=1"
        - "WB_COMMIT -> WB_IDLE after retire pulse"
        - "WB_TRAP_COMMIT -> WB_IDLE after exception metadata write"
        - "WB_COMMIT -> WB_HOLD when commit_blocked=1"
        - "WB_HOLD -> WB_COMMIT when commit_blocked=0"
    - name: bus_if_fsm
      owner: bus_if
      state_bits: 3
      states:
        - { name: BUS_IDLE, code: 0 }
        - { name: I_REQ, code: 1 }
        - { name: I_WAIT, code: 2 }
        - { name: D_REQ, code: 3 }
        - { name: D_WAIT, code: 4 }
        - { name: BUS_ERR, code: 5 }
      transitions:
        - "BUS_IDLE -> I_REQ when if_stage requests fetch"
        - "I_REQ -> I_WAIT when i_hready=0"
        - "I_REQ/I_WAIT -> BUS_ERR when i_hresp=1"
        - "I_REQ/I_WAIT -> BUS_IDLE when i_hready=1 and i_hresp=0"
        - "BUS_IDLE -> D_REQ when ex_stage requests load_store"
        - "D_REQ -> D_WAIT when d_hready=0"
        - "D_REQ/D_WAIT -> BUS_ERR when d_hresp=1"
        - "D_REQ/D_WAIT -> BUS_IDLE when d_hready=1 and d_hresp=0"
        - "BUS_ERR -> BUS_IDLE after trap_ack"

rtl_contract:
  clock: clk
  reset: rst_n
  reset_active: low
  transaction: FM_CPU_STEP
  sample_condition: "if_id_valid && if_id_ready or id_ex_valid && id_ex_ready or ex_wb_valid && ex_wb_ready"
  input_map:
    instruction: if_id_instr
    data_response: bus_ex_rdata
  output_map:
    pc_visible: pc_dbg
    retire_pulse: retire
    trap_flag: trap
  state_updates:
    - name: pc_q
      width: XLEN
      reset: RESET_PC
      expr: "sequential pc, branch target, or trap vector per function_model.state_updates"
    - name: rf_mem
      width: XLEN
      reset: 0
      expr: "writeback on non-trapped committing instruction only"
    - name: nzcv_q
      width: 4
      reset: 0
      expr: "flag_formulas from function_model transactions"

clock_reset_domains:
  clock_domains:
    - name: core_clk
      port: clk
      frequency_mhz: 300
      generated: false
    - name: bus_clk
      port: hclk
      frequency_mhz: 150
      generated: true
      source: core_clk
      ratio_to_source: "1:2"
  resets:
    - name: core_rst_n
      port: rst_n
      polarity: active_low
      scheme: async_assert_sync_deassert
      synchronized_signal: core_rst_n_sync
      synchronizer_stages: 2
    - name: bus_rst_n
      port: hresetn
      polarity: active_low
      scheme: async_assert_sync_deassert
      
... <truncated 25275 chars>

Base rtl-gen contract:
Prepare rtl-gen for cortex_m0lite using only cortex_m0lite/yaml/cortex_m0lite.ssot.yaml and cortex_m0lite/rtl/rtl_todo_plan.json, cortex_m0lite/rtl/rtl_authoring_plan.json, and packets under cortex_m0lite/rtl/authoring_packets. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=145e32fadb52f8c746f5a8b5245fecfa1c910e209faff81af2c0fad99738e143. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "cortex_m0lite",
        "reason": "26 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "cortex_m0lite",
        "reason": "7 owner logic structure issue(s) remain. cortex_m0lite_core: Behavior-owner module is not declared in its owner file; if_stage: Behavior-owner module is not declared in its owner file; id_stage: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "cortex_m0lite",
        "reason": "24 top IO contract issue(s) remain. hclk: SSOT top IO port is missing from RTL top declaration; hresetn: SSOT top IO port is missing from RTL top declaration; i_haddr: SSOT top IO port is missing from RTL top declaration",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "cortex_m0lite",
        "reason": "7 manifest hierarchy integration issue(s) remain. cortex_m0lite_core: SSOT manifest child module is not declared in listed RTL sources; if_stage: SSOT manifest child module is not declared in listed RTL sources; id_stage: SSOT manifest child module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "cortex_m0lite",
        "reason": "1 manifest signal-flow issue(s) remain. cortex_m0lite: None: No reachable manifest child port flow evidence was found",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "status": "open",
        "task_id": "RTL-0015"
      },
      {
        "gate_kind": "rtl_implementation_depth_evidence",
        "owner_module": "cortex_m0lite",
        "reason": "7 production RTL implementation-depth issue(s) remain. Production RTL source-file count is below the SSOT-locked target scale: actual=1 required=8; Production RTL module count is below the SSOT-locked target scale: actual=1 required=8; Production RTL procedural block count is below the SSOT-locked target scale: actual=2 required=12",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_implementation_depth_evidence",
        "status": "open",
        "task_id": "RTL-0022"
      }
    ],
    "blocked_by_locked_truth": [
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "owner_module": "cortex_m0lite",
        "reason": "40 SSOT connection contract issue(s) remain. cortex_m0lite_core: SSOT connection contract targets a module not declared in RTL; cortex_m0lite_core: SSOT connection contract targets a module not declared in RTL; cortex_m0lite_core: SSOT connection contract targets a module not declared in RTL",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      },
      {
        "gate_kind": "golden_authority_artifacts",
        "owner_module": "cortex_m0lite",
        "reason": "Missing production golden authority artifact(s): governance/authority.json, model/model_signature.json",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.golden_authority_artifacts",
        "status": "open",
        "task_id": "RTL-0020"
      },
      {
        "gate_kind": "cycle_model_artifacts",
        "owner_module": "cortex_m0lite",
        "reason": "Missing executable cycle model: model/cycle_model.py.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.cycle_model_artifacts",
        "status": "open",
        "task_id": "RTL-0023"
      }
    ],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "cortex_m0lite",
        "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/cortex_m0lite_bus_if.sv,rtl/cortex_m0lite_core.sv,rtl/cortex_m0lite_ex_stage.sv,rtl/cortex_m0lite_id_stage.sv,rtl/cortex_m0lite_if_stage.sv,rtl/cortex_m0lite_regfile.sv",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "cortex_m0lite",
        "reason": "rtl/rtl_compile.json is older than current RTL source rtl/cortex_m0lite.sv; rerun DUT compile after the final RTL edit.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "cortex_m0lite",
        "reason": "121 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "gate_kind": "protocol_assertion_evidence",
        "owner_module": "cortex_m0lite",
        "reason": "Missing protocol assertion artifact: verify/protocol_assertions.sva.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "gate_kind": "fl_rtl_goal_audit",
        "owner_module": "cortex_m0lite",
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "gate_kind": "coverage_closure",
        "owner_module": "cortex_m0lite",
        "reason": "Coverage closure report is not pass.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "status": "open",
        "task_id": "RTL-0026"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 40,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
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
    "open_required_todos": 122,
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
          "cortex_m0lite/rtl/rtl_authoring_provenance.json",
          "cortex_m0lite/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip cortex_m0lite --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "common_ai_agent_authoring",
        "prerequisites": [
          "An LLM authoring pass emitted or repaired DUT RTL files."
        ],
        "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/cortex_m0lite_bus_if.sv,rtl/cortex_m0lite_core.sv,rtl/cortex_m0lite_ex_stage.sv,rtl/cortex_m0lite_id_stage.sv,rtl/cortex_m0lite_if_stage.sv,rtl/cortex_m0lite_regfile.sv",
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
          "cortex_m0lite/rtl/rtl_compile.json",
          "cortex_m0lite/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py cortex_m0lite --top cortex_m0lite --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "cortex_m0lite/list/cortex_m0lite.f covers the current DUT RTL sources."
        ],
        "reason": "rtl/rtl_compile.json is older than current RTL source rtl/cortex_m0lite.sv; rerun DUT compile after the final RTL edit.",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "stage_sequence": [
          "ssot-rtl",
          "dut_compile"
        ],
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "artifact": "rtl/rtl_todo_plan.json",
        "artifacts": [
          "cortex_m0lite/rtl/rtl_todo_plan.json",
          "cortex_m0lite/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "121 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "artifact": "verify/protocol_assertions.sva",
        "artifacts": [
          "cortex_m0lite/verify/protocol_assertions.sva",
          "cortex_m0lite/verify/protocol_assertions.summary.json",
          "cortex_m0lite/sim/assertion_failures.jsonl"
        ],
        "closure_rule": "Generated assertions exist and latest simulation has zero assertion failure records.",
        "commands": [
          "python3 workflow/fl-model-gen/scripts/emit_protocol_assertions.py cortex_m0lite --root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "protocol_assertion_evidence",
        "prerequisites": [
          "SSOT cycle_model/protocol rules are machine-checkable.",
          "Simulation has run after RTL edits."
        ],
        "reason": "Missing protocol assertion artifact: verify/protocol_assertions.sva.",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "stage_sequence": [
          "ssot-protocol-assertions",
          "sim"
        ],
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "artifact": "sim/fl_rtl_goal_audit.json",
        "artifacts": [
          "cortex_m0lite/sim/fl_rtl_goal_audit.json"
        ],
        "closure_rule": "fl_rtl_goal_audit.json must be fresh and status=pass.",
        "commands": [
          "python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py cortex_m0lite --root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "fl_rtl_goal_audit",
        "prerequisites": [
          "FL model, equivalence goals, TB, and simulation evidence are current."
        ],
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "stage_sequence": [
          "ssot-fl-model",
          "ssot-equiv-goals",
          "ssot-tb-cocotb",
          "sim",
          "goal-audit"
        ],
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "artifact": "cov/coverage.json",
        "artifacts": [
          "cortex_m0lite/cov/coverage.json"
        ],
        "closure_rule": "coverage.json must be fresh, come from ssot_coverage_summary, and close every planned required bin.",
        "commands": [
          "python3 workflow/coverage/scripts/ssot_coverage_summary.py cortex_m0lite",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py cortex_m0lite --root . --audit-rtl"
        ],
        "gate_kind": "coverage_closure",
        "prerequisites": [
          "Simulation evidence exists and planned coverage bins are observable."
        ],
        "reason": "Coverage closure report is not pass.",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "stage_sequence": [
          "sim",
          "coverage"
        ],
        "status": "open",
        "task_id": "RTL-0026"
      }
    ]
  },
  "ip": "cortex_m0lite",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__function_model.json",
      "kind": "module",
      "llm_actionable_open_count": 28,
      "open_required_count": 28,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__function_model",
      "required_count": 28,
      "status_counts": {
        "open": 28
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 15,
      "open_required_count": 15,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__parameters",
      "required_count": 15,
      "status_counts": {
        "open": 15
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__registers.json",
      "kind": "module",
      "llm_actionable_open_count": 15,
      "open_required_count": 15,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__registers",
      "required_count": 15,
      "status_counts": {
        "open": 15
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 14,
      "open_required_count": 14,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__cycle_model",
      "required_count": 14,
      "status_counts": {
        "open": 14
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 13,
      "open_required_count": 13,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__fsm",
      "required_count": 13,
      "status_counts": {
        "open": 13
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__dataflow.json",
      "kind": "module",
      "llm_actionable_open_count": 7,
      "open_required_count": 7,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__dataflow",
      "required_count": 7,
      "status_counts": {
        "open": 7
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__workflow_todo",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__error_handling",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite_core__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "packet_id": "module__cortex_m0lite_core__equivalence",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__if_stage.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite_if_stage.sv",
      "owner_module": "if_stage",
      "packet_id": "module__if_stage",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__id_stage.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite_id_stage.sv",
      "owner_module": "id_stage",
      "packet_id": "module__id_stage",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__ex_stage.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite_ex_stage.sv",
      "owner_module": "ex_stage",
      "packet_id": "module__ex_stage",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__wb_stage.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/cortex_m0lite_wb_stage.sv",
      "owner_module": "wb_stage",
      "packet_id": "module__wb_stage",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__regfile.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/cortex_m0lite_regfile.sv",
      "owner_module": "regfile",
      "packet_id": "module__regfile",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__bus_if.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite_bus_if.sv",
      "owner_module": "bus_if",
      "packet_id": "module__bus_if",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 6,
      "open_required_count": 6,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 10,
      "status_counts": {
        "open": 6,
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 3,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 3,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 7,
      "status_counts": {
        "open": 3,
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 6,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 7,
      "status_counts": {
        "open": 6,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite__features.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "module__cortex_m0lite__features",
      "required_count": 4,
      "status_counts": {
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite__integration.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "module__cortex_m0lite__integration",
      "required_count": 10,
      "status_counts": {
        "pass": 10
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "module__cortex_m0lite__io_list",
      "required_count": 27,
      "status_counts": {
        "pass": 27
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite__rtl_flow.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "module__cortex_m0lite__rtl_flow",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite__security.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "module__cortex_m0lite__security",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite__synthesis.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "module__cortex_m0lite__synthesis",
      "required_count": 8,
      "status_counts": {
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__cortex_m0lite__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/cortex_m0lite.sv",
      "owner_module": "cortex_m0lite",
      "packet_id": "module__cortex_m0lite__test_requirements",
      "required_count": 6,
      "status_counts": {
        "pass": 6
      }
    }
  ],
  "policy": {
    "dynamic_task_rule": "Use every required task in this file as the authoritative RTL implementation/evidence ledger. Expose Atlas/UI TodoTracker items as grouped section/work-type tasks, targeting roughly 20-30 active TODOs for complex IPs, with the detailed ledger items preserved as criteria instead of one UI TODO per ledger row.",
    "fixed_template_role": "seed_only",
    "no_orphan_function_level": true,
    "reference_profile_rule": "Optional rtl_reference_profile artifacts are calibration-only scale reports; they must not be copied, transformed, or used as fixed RTL templates.",
    "rtl_gate_todo_rule": "RTL-gen quality gates are first-class rtl_gate.rtl_gen TODOs; compile/lint/static/ownership/owner-logic/placeholder-free/implementation-depth/top-io/top-output-drive/top-input-consumption/hierarchy/port-connection/signal-flow/connection-contract gates must close as TODOs before PASS.",
    "rtl_quality_profile": "production",
    "rtl_target_scale": {
      "basis": "Human-authored Cortex-M0-lite architecture decomposition.",
      "min_behavior_owner_logic_modules": 6,
      "min_depth_score": 120,
      "min_logic_modules": 7,
      "min_modules": 8,
      "min_procedural_blocks": 12,
      "min_source_files": 8,
      "min_state_updates": 10,
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
    "human_locked_tasks": 3,
    "llm_actionable_packets": 16,
    "llm_actionable_tasks": 113,
    "max_packet_required_tasks": 28,
    "module_packets": 22,
    "next_llm_packets": [
      "module__cortex_m0lite_core__function_model",
      "module__cortex_m0lite_core__parameters",
      "module__cortex_m0lite_core__registers",
      "module__cortex_m0lite_core__cycle_model",
      "module__cortex_m0lite_core__fsm",
      "module__cortex_m0lite_core__dataflow",
      "module__cortex_m0lite_core__workflow_todo",
      "module__cortex_m0lite_core__error_handling"
    ],
    "packet_task_limit": 48,
    "packets": 25,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 189,
    "sliced_module_packets": 16,
    "target_scale_present": true,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 6,
    "total_tasks": 189,
    "unowned_packets": 0
  },
  "target_scale": {
    "basis": "Human-authored Cortex-M0-lite architecture decomposition.",
    "min_behavior_owner_logic_modules": 6,
    "min_depth_score": 120,
    "min_logic_modules": 7,
    "min_modules": 8,
    "min_procedural_blocks": 12,
    "min_source_files": 8,
    "min_state_updates": 10,
    "policy": "SSOT-locked scale target. It may be calibrated from a reference profile, but rtl-gen must satisfy it through IP-specific SSOT behavior, not by copying reference RTL."
  },
  "todo_plan_sha256": "145e32fadb52f8c746f5a8b5245fecfa1c910e209faff81af2c0fad99738e143",
  "top": "cortex_m0lite",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/cortex_m0lite_core.sv):
<missing or not authored yet>

Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__cortex_m0lite_core__function_model.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 40,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 2,
      "key": "function_model",
      "module_task_count": 98,
      "rule": "Owner module cortex_m0lite_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "function_model",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/cortex_m0lite_core.sv",
      "name": "cortex_m0lite_core",
      "refs": [
        "coverage_tap",
        "cycle_model",
        "cycle_model.pipeline",
        "dataflow",
        "dataflow.ordering",
        "dataflow.sequence",
        "dataflow.state_flow",
        "decomposition",
        "error_handling",
        "fsm",
        "fsm.control",
        "function_model",
        "function_model.transactions.FM_CPU_STEP",
        "io_list",
        "parameters",
        "registers",
        "registers.register_list",
        "workflow_todos"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/cortex_m0lite.sv",
        "name": "cortex_m0lite",
        "wiring_only": true
      },
      {
        "file": "rtl/cortex_m0lite_core.sv",
        "name": "cortex_m0lite_core",
        "wiring_only": false
      },
      {
        "file": "rtl/cortex_m0lite_if_stage.sv",
        "name": "if_stage",
        "wiring_only": false
      },
      {
        "file": "rtl/cortex_m0lite_id_stage.sv",
        "name": "id_stage",
        "wiring_only": false
      },
      {
        "file": "rtl/cortex_m0lite_ex_stage.sv",
        "name": "ex_stage",
        "wiring_only": false
      },
      {
        "file": "rtl/cortex_m0lite_wb_stage.sv",
        "name": "wb_stage",
        "wiring_only": false
      },
      {
        "file": "rtl/cortex_m0lite_regfile.sv",
        "name": "regfile",
        "wiring_only": false
      },
      {
        "file": "rtl/cortex_m0lite_bus_if.sv",
        "name": "bus_if",
        "wiring_only": false
      }
    ],
    "quality_profile": "production",
    "reference_profile": null,
    "ssot_connection_contracts": [
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "clk",
        "signal": "clk",
        "signal_terms": [
          "clk"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "rst_n",
        "signal": "core_rst_n_sync",
        "signal_terms": [
          "core_rst_n_sync"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "hclk",
        "signal": "hclk",
        "signal_terms": [
          "hclk"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "hresetn",
        "signal": "bus_rst_n_sync",
        "signal_terms": [
          "bus_rst_n_sync"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "irq",
        "signal": "irq",
        "signal_terms": [
          "irq"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "pc_dbg",
        "signal": "pc_dbg",
        "signal_terms": [
          "pc_dbg"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "state_dbg",
        "signal": "state_dbg",
        "signal_terms": [
          "state_dbg"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "retire",
        "signal": "retire",
        "signal_terms": [
          "retire"
        ],
        "source_ref": "integration.connections[0]"
      },
      {
        "instance": "u_core",
        "machine_readable": true,
        "module": "cortex_m0lite_core",
        "port": "trap",
        "signal": "trap",
        "signal_terms": [
          "trap"
        ],
        "source_ref": "integration.connections[0]"
      }
    ],
    "ssot_top_io_contracts": [],
    "target_scale": {
      "basis": "Human-authored Cortex-M0-lite architecture decomposition.",
      "min_behavior_owner_logic_modules": 6,
      "min_depth_score": 120,
      "min_logic_modules": 7,
      "min_modules": 8,
      "min_procedural_blocks": 12,
      "min_source_files": 8,
      "min_state_updates": 10,
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
  "ip": "cortex_m0lite",
  "kind": "module",
  "owner_file": "rtl/cortex_m0lite_core.sv",
  "owner_module": "cortex_m0lite_core",
  "packet_id": "module__cortex_m0lite_core__function_model",
  "rules": [
    "No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.",
    "Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.",
    "Every task must satisfy content, detail, and criteria before the packet is closed.",
    "For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.",
    "Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json."
  ],
  "schema_version": 1,
  "source_plan": "rtl/rtl_todo_plan.json",
  "summary": {
    "categories": {
      "function_model.error_case": 3,
      "function_model.invariant": 5,
      "function_model.output": 3,
      "function_model.output_rule": 2,
      "function_model.precondition": 3,
      "function_model.side_effect": 4,
      "function_model.state_update": 3,
      "function_model.state_variable": 4,
      "function_model.transaction": 1
    },
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 2,
      "key": "function_model",
      "module_task_count": 98,
      "rule": "Owner module cortex_m0lite_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "function_model",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 28,
    "required_count": 28,
    "source_refs": [
      "function_model.state_variables.pc_q",
      "function_model.state_variables.rf_q",
      "function_model.state_variables.nzcv_q",
      "function_model.state_variables.trap_q",
      "function_model.transactions.FM_CPU_STEP",
      "function_model.transactions.FM_CPU_STEP.preconditions.precondition_0",
      "function_model.transactions.FM_CPU_STEP.preconditions.precondition_1",
      "function_model.transactions.FM_CPU_STEP.preconditions.precondition_2",
      "function_model.transactions.FM_CPU_STEP.outputs.output_0",
      "function_model.transactions.FM_CPU_STEP.outputs.output_1",
      "function_model.transactions.FM_CPU_STEP.outputs.output_2",
      "function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse",
      "function_model.transactions.FM_CPU_STEP.output_rules.trap_flag",
      "function_model.transactions.FM_CPU_STEP.state_updates.pc_q",
      "function_model.transactions.FM_CPU_STEP.state_updates.rf_q",
      "function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q",
      "function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0",
      "function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1",
      "function_model.transactions.FM_CPU_STEP.side_effects.side_effect_2",
      "function_model.transactions.FM_CPU_STEP.side_effects.side_effect_3",
      "function_model.transactions.FM_CPU_STEP.error_cases.error_case_0",
      "function_model.transactions.FM_CPU_STEP.error_cases.error_case_1",
      "function_model.transactions.FM_CPU_STEP.error_cases.error_case_2",
      "function_model.invariants.invariant_0"
    ],
    "status_counts": {
      "open": 28
    },
    "task_count": 28
  },
  "tasks": [
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state pc_q",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.pc_q",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "pc_q width matches SSOT value XLEN",
        "pc_q reset behavior matches SSOT value RESET_PC"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.pc_q.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=pc_q; width=XLEN; reset=RESET_PC.",
      "evidence_terms": [],
      "id": "RTL-0072",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.pc_q",
      "ssot_context": {
        "name": "pc_q",
        "reset": "RESET_PC",
        "width": "XLEN"
      },
      "ssot_refs": [
        "function_model.state_variables.pc_q"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state rf_q",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.rf_q",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "rf_q width matches SSOT value 32",
        "rf_q reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.rf_q.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=rf_q; width=32; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0073",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.rf_q",
      "ssot_context": {
        "name": "rf_q",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "function_model.state_variables.rf_q"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state nzcv_q",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.nzcv_q",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "nzcv_q width matches SSOT value 4",
        "nzcv_q reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.nzcv_q.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=nzcv_q; width=4; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0074",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.nzcv_q",
      "ssot_context": {
        "name": "nzcv_q",
        "reset": "0",
        "width": "4"
      },
      "ssot_refs": [
        "function_model.state_variables.nzcv_q"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state trap_q",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.trap_q",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "trap_q width matches SSOT value 1",
        "trap_q reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.trap_q.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=trap_q; width=1; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0075",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.trap_q",
      "ssot_context": {
        "name": "trap_q",
        "reset": "0",
        "width": "1"
      },
      "ssot_refs": [
        "function_model.state_variables.trap_q"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.transaction",
      "content": "Implement transaction FM_CPU_STEP",
      "criteria": [
        "Acceptance/precondition logic is explicit in RTL",
        "All outputs and side effects occur exactly once per accepted transaction",
        "The transaction is covered by equivalence goals and scoreboard observations downstream",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.\nSSOT ref: function_model.transactions.FM_CPU_STEP.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: id=FM_CPU_STEP; name=cpu_cycle_step.",
      "evidence_terms": [],
      "id": "RTL-0076",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP",
      "ssot_context": {
        "id": "FM_CPU_STEP",
        "name": "cpu_cycle_step"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.precondition",
      "content": "Implement precondition for FM_CPU_STEP: precondition_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_0",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_0.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=core_rst_n_sync and bus_rst_n_sync are deasserted..",
      "evidence_terms": [
        "bus",
        "bus_rst_n_sync",
        "core",
        "core_rst_n_sync",
        "rst",
        "sync"
      ],
      "id": "RTL-0077",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.preconditions.precondition_0",
      "ssot_context": {
        "value": "core_rst_n_sync and bus_rst_n_sync are deasserted."
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.preconditions.precondition_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "bus",
          "bus_rst_n_sync",
          "core",
          "core_rst_n_sync",
          "rst",
          "sync"
        ],
        "source_scope": "rtl/cortex_m0lite_core.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.precondition",
      "content": "Implement precondition for FM_CPU_STEP: precondition_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_1",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_1.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=instr_valid indicates a 16-bit instruction word is available from the IF path..",
      "evidence_terms": [
        "instr",
        "instr_valid",
        "valid"
      ],
      "id": "RTL-0078",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.preconditions.precondition_1",
      "ssot_context": {
        "value": "instr_valid indicates a 16-bit instruction word is available from the IF path."
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.preconditions.precondition_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "instr",
          "instr_valid",
          "valid"
        ],
        "source_scope": "rtl/cortex_m0lite_core.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.precondition",
      "content": "Implement precondition for FM_CPU_STEP: precondition_2",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_2",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_2.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=Any data access waits for the declared AHB-Lite ready/response contract..",
      "evidence_terms": [],
      "id": "RTL-0079",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.preconditions.precondition_2",
      "ssot_context": {
        "value": "Any data access waits for the declared AHB-Lite ready/response contract."
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.preconditions.precondition_2"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output",
      "content": "Implement output for FM_CPU_STEP: output_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_0",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_0.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=pc_dbg.",
      "evidence_terms": [
        "dbg",
        "pc",
        "pc_dbg"
      ],
      "id": "RTL-0080",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.outputs.output_0",
      "ssot_context": {
        "value": "pc_dbg"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.outputs.output_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "dbg",
          "pc",
          "pc_dbg"
        ],
        "source_scope": "rtl/cortex_m0lite_core.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output",
      "content": "Implement output for FM_CPU_STEP: output_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_1",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_1.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=retire.",
      "evidence_terms": [],
      "id": "RTL-0081",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.outputs.output_1",
      "ssot_context": {
        "value": "retire"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.outputs.output_1"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output",
      "content": "Implement output for FM_CPU_STEP: output_2",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_2",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_2.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=trap.",
      "evidence_terms": [],
      "id": "RTL-0082",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.outputs.output_2",
      "ssot_context": {
        "value": "trap"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.outputs.output_2"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output_rule",
      "content": "Implement output rule for FM_CPU_STEP: retire_pulse",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "retire_pulse width matches SSOT value 1",
        "retire_pulse RTL expression implements SSOT expression 1 when one instruction commits without trap, else 0",
        "DUT port retire is the implementation/observation point for retire_pulse",
        "retire_pulse is not implemented only in FunctionalModel or scoreboard code"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=retire_pulse; port=retire; expr=1 when one instruction commits without trap, else 0; width=1.",
      "evidence_terms": [],
      "id": "RTL-0083",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse",
      "ssot_context": {
        "expr": "1 when one instruction commits without trap, else 0",
        "name": "retire_pulse",
        "port": "retire",
        "width": "1"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.output_rule",
      "content": "Implement output rule for FM_CPU_STEP: trap_flag",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.output_rules.trap_flag",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "trap_flag width matches SSOT value 1",
        "trap_flag RTL expression implements SSOT expression 1 when illegal opcode, bus error, or misalignment is detected at commit boundary",
        "DUT port trap is the implementation/observation point for trap_flag",
        "trap_flag is not implemented only in FunctionalModel or scoreboard code"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.output_rules.trap_flag.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=trap_flag; port=trap; expr=1 when illegal opcode, bus error, or misalignment is detected at commit boundary; width=1.",
      "evidence_terms": [],
      "id": "RTL-0084",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.output_rules.trap_flag",
      "ssot_context": {
        "expr": "1 when illegal opcode, bus error, or misalignment is detected at commit boundary",
        "name": "trap_flag",
        "port": "trap",
        "width": "1"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.output_rules.trap_flag"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.state_update",
      "content": "Implement state update for FM_CPU_STEP: pc_q",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.state_updates.pc_q",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "pc_q width matches SSOT value XLEN",
        "pc_q reset behavior matches SSOT value RESET_PC",
        "pc_q RTL expression implements SSOT expression pc+2 on normal flow; branch target on taken branch; trap vector on exception",
        "pc_q updates exactly once at the SSOT-defined transaction acceptance point"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.state_updates.pc_q.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=pc_q; expr=pc+2 on normal flow; branch target on taken branch; trap vector on exception; width=XLEN; reset=RESET_PC.",
      "evidence_terms": [],
      "id": "RTL-0085",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.state_updates.pc_q",
      "ssot_context": {
        "expr": "pc+2 on normal flow; branch target on taken branch; trap vector on exception",
        "name": "pc_q",
        "reset": "RESET_PC",
        "width": "XLEN"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.state_updates.pc_q"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.state_update",
      "content": "Implement state update for FM_CPU_STEP: rf_q",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.state_updates.rf_q",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "rf_q width matches SSOT value 32",
        "rf_q reset behavior matches SSOT value 0",
        "rf_q RTL expression implements SSOT expression register writeback on ALU/LDR/MOV commit only",
        "rf_q updates exactly once at the SSOT-defined transaction acceptance point"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.state_updates.rf_q.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=rf_q; expr=register writeback on ALU/LDR/MOV commit only; width=32; reset=0.",
      "evidence_terms": [
        "ALU",
        "LDR",
        "MOV"
      ],
      "id": "RTL-0086",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.state_updates.rf_q",
      "ssot_context": {
        "expr": "register writeback on ALU/LDR/MOV commit only",
        "name": "rf_q",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.state_updates.rf_q"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "ALU",
          "LDR",
          "MOV"
        ],
        "source_scope": "rtl/cortex_m0lite_core.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.state_update",
      "content": "Implement state update for FM_CPU_STEP: nzcv_q",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv",
        "nzcv_q width matches SSOT value 4",
        "nzcv_q reset behavior matches SSOT value 0",
        "nzcv_q RTL expression implements SSOT expression updated by arithmetic/compare instructions per ARM-like semantics",
        "nzcv_q updates exactly once at the SSOT-defined transaction acceptance point"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: name=nzcv_q; expr=updated by arithmetic/compare instructions per ARM-like semantics; width=4; reset=0.",
      "evidence_terms": [
        "ARM"
      ],
      "id": "RTL-0087",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q",
      "ssot_context": {
        "expr": "updated by arithmetic/compare instructions per ARM-like semantics",
        "name": "nzcv_q",
        "reset": "0",
        "width": "4"
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "ARM"
        ],
        "source_scope": "rtl/cortex_m0lite_core.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM_CPU_STEP: side_effect_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=Successful ALU/MOV/LDR instructions update the destination architectural register at commit..",
      "evidence_terms": [],
      "id": "RTL-0088",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0",
      "ssot_context": {
        "value": "Successful ALU/MOV/LDR instructions update the destination architectural register at commit."
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0"
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
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM_CPU_STEP: side_effect_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=Arithmetic and compare instructions update NZCV according to flag_formulas..",
      "evidence_terms": [
        "flag",
        "flag_formulas",
        "formulas"
      ],
      "id": "RTL-0089",
      "owner_file": "rtl/cortex_m0lite_core.sv",
      "owner_module": "cortex_m0lite_core",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1",
      "ssot_context": {
        "value": "Arithmetic and compare instructions update NZCV according to flag_formulas."
      },
      "ssot_refs": [
        "function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "flag",
          "flag_formulas",
          "formulas"
        ],
        "source_scope": "rtl/cortex_m0lite_core.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/cortex_m0lite_core.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM_CPU_STEP: side_effect_2",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.side_effects.side_effect_2",
        "Primary implementation evidence is in rtl/cortex_m0lite_core.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_2.\nOwner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.\nSSOT item context: value=Taken branches redirect pc_q and flush IF/ID before the next fetch..",
      "evidence_terms": [
        "pc",
        "pc_q"
      ],
      "id": "RTL-0090",
      "owner_file": "rtl/cortex_m0lite_core.sv",
     
... <truncated 20032 chars>

Current packet Markdown (rtl/authoring_packets/module__cortex_m0lite_core__function_model.md):
# RTL Authoring Packet: module__cortex_m0lite_core__function_model

- Kind: module
- Owner module: cortex_m0lite_core
- Owner file: rtl/cortex_m0lite_core.sv
- Task count: 28
- Required tasks: 28

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 28
- Human-locked open tasks: 0
- Owner refs: coverage_tap, cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, dataflow.state_flow, decomposition, error_handling, fsm, fsm.control, function_model, function_model.transactions.FM_CPU_STEP, io_list, parameters, registers
- Module slice: 2/9 section=function_model task_limit=48
- Slice rule: Owner module cortex_m0lite_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])

## Tasks

### RTL-0072: Implement RTL state owner for FL state pc_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.pc_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.pc_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=pc_q; width=XLEN; reset=RESET_PC.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.pc_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - pc_q width matches SSOT value XLEN
  - pc_q reset behavior matches SSOT value RESET_PC
- SSOT refs: function_model.state_variables.pc_q

### RTL-0073: Implement RTL state owner for FL state rf_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rf_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rf_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=rf_q; width=32; reset=0.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rf_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - rf_q width matches SSOT value 32
  - rf_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.rf_q

### RTL-0074: Implement RTL state owner for FL state nzcv_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.nzcv_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.nzcv_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=nzcv_q; width=4; reset=0.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.nzcv_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - nzcv_q width matches SSOT value 4
  - nzcv_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.nzcv_q

### RTL-0075: Implement RTL state owner for FL state trap_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.trap_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.trap_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=trap_q; width=1; reset=0.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.trap_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - trap_q width matches SSOT value 1
  - trap_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.trap_q

### RTL-0076: Implement transaction FM_CPU_STEP

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_CPU_STEP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_CPU_STEP.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: id=FM_CPU_STEP; name=cpu_cycle_step.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP

### RTL-0077: Implement precondition for FM_CPU_STEP: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=core_rst_n_sync and bus_rst_n_sync are deasserted..
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.preconditions.precondition_0

### RTL-0078: Implement precondition for FM_CPU_STEP: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=instr_valid indicates a 16-bit instruction word is available from the IF path..
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.preconditions.precondition_1

### RTL-0079: Implement precondition for FM_CPU_STEP: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Any data access waits for the declared AHB-Lite ready/response contract..
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.preconditions.precondition_2

### RTL-0080: Implement output for FM_CPU_STEP: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_CPU_STEP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=pc_dbg.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.outputs.output_0

### RTL-0081: Implement output for FM_CPU_STEP: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_CPU_STEP.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=retire.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.outputs.output_1

### RTL-0082: Implement output for FM_CPU_STEP: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_CPU_STEP.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=trap.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.outputs.output_2

### RTL-0083: Implement output rule for FM_CPU_STEP: retire_pulse

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=retire_pulse; port=retire; expr=1 when one instruction commits without trap, else 0; width=1.
- Current reason: Owner RTL file is missing: rtl/cortex_m0lite_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - retire_pulse width matches SSOT value 1
  - retire_pulse RTL expression implements SSOT expression 1 when one instruction commits without trap, else 0
  - DUT port retire is the implementation/observation point for retire_pulse
  - retire_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse

### RTL-0084: Implement output rule for FM_CPU_STEP: trap_flag

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_CPU_STEP.output_rules.trap_flag
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.output_rules.trap_flag.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=trap_flag; port=trap; expr=1 when illegal opcode, bus error, or misalignment is detected at commit boundary; width=1.
- Current reason: Owner 
... <truncated 18060 chars>