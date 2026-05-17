RTL-GEN PACKET MODE for dma_real. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "dma_real/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "dma_real/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "dma_real/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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
- Gate/tool-evidence packets may edit any declared RTL file implicated by the audit digest, compile diagnostics, lint diagnostics, or static-evidence gaps; current owner_file is the gate coordinator, not an edit restriction.
- Keep generated RTL lint-clean: eliminate Verilator warnings, unused evidence-only helper signals, unused parameters, and the no_parameterized_part_select_in_procedural_block style violation by adding real helper wires or real signal consumption.
- Treat lint.repair_hints as mandatory repair guidance. For UNUSED* diagnostics, prefer narrowing/removing helper declarations or real functional connections; do not add marker-only reductions, lint suppressions, or evidence-only consumes.
- If lint.repair_hints names a signal, the emitted RTL must make that exact reported diagnostic disappear; renaming or copying the signal while leaving the same unused upper-bit pattern open is a failed repair.
- For narrower GPIO/output consumers, connect from the full producer slice, such as producer[GPIO_WIDTH-1:0], or use a GPIO_WIDTH helper; do not create another DATA_WIDTH masked/full helper whose upper bits remain unused.
- Static evidence terms are search/audit hints, not required signal names. Do not declare a wire/reg whose only purpose is to spell a TODO term; implement the behavior with real protocol/datapath/control logic and remove marker signals that lint reports unused.
- For rtl_gate_contract_blocked, return human_gate only; missing SSOT connection contracts block correct top integration semantics.
- For rtl_gate_human_closure, return human_gate only; do not invent or edit human-locked authority.
- The headless runner will refresh filelist/provenance from LLM-authored artifacts after each packet.

Current packet: module__dma_real_engine
kind: module
work queue: 1/1 active packets (9 closed packets skipped from 25 total)
batch limit: 1; deferred active packets after this batch: 15
owner_module: dma_real_engine
owner_file: rtl/dma_real_engine.sv

SSOT observable latency contract:
{
  "cycle_model.latency": 5,
  "cycle_model.pipeline": [
    {
      "action": "wait for valid start/config from CDC bridge",
      "cycle": 0,
      "stage": "IDLE"
    },
    {
      "action": "latch src_addr, dst_addr, remaining, stride from CDC config registers",
      "cycle": 1,
      "stage": "CFG"
    },
    {
      "action": "request AHB bus via arbiter, clock gating cell enables hclk to channel",
      "cycle": 2,
      "stage": "REQUEST"
    },
    {
      "action": "AHB read burst from source address into pointer-based FIFO, timeout counter active",
      "cycle": 3,
      "stage": "READ"
    },
    {
      "action": "AHB write burst from FIFO to destination address, FIFO read pointer advances",
      "cycle": 4,
      "stage": "WRITE"
    },
    {
      "action": "update remaining count (decrement), src_addr (+= stride), dst_addr (+= stride), perf counters increment",
      "cycle": 5,
      "stage": "UPDATE"
    },
    {
      "action": "assert done pulse, update status, trigger IRQ, clock gating cell may disable hclk",
      "cycle": 6,
      "stage": "DONE"
    },
    {
      "action": "assert error pulse, latch error code, return to IDLE, clock gating cell may disable hclk",
      "cycle": 2,
      "stage": "ERROR"
    }
  ],
  "latency_1_required_rtl_shape": "When cycle_model.latency is 1, compute output_rules from the current accepted inputs inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later S1_RESULT clock edge; that is a forbidden latency-2 implementation.",
  "observable_latency_rule": "For valid/ready transactions, latency is counted from the accepting clock edge to the first ReadOnly observation of matching result/output_valid. latency=1 means registered outputs for the accepted transaction are visible after that one edge; an input-register stage followed by a result-register stage is latency=2.",
  "rtl_contract.output_valid": null,
  "rtl_contract.sample_condition": "ch_start or ch_busy or ch_done or ch_error or irq",
  "timing.latency_budget": {
    "apb_access": 2,
    "burst_read_latency": "BURST_MAX",
    "burst_write_latency": "BURST_MAX",
    "cdc_config_crossing": 3,
    "channel_start_to_first_read": 5,
    "completion_to_irq": 3,
    "timeout_default": "TIMEOUT_DEFAULT"
  }
}

SSOT bus/byte-lane policy:
{
  "guidance": "condition=none means upper byte lanes are not an APB error for legal offsets; consume otherwise-unused pwdata/pstrb upper bits through explicit legal ignore, byte-strobe masking, reserved-zero readback, or coverage/trace behavior while keeping pslverr deasserted for legal writes.",
  "illegal_byte_access_pattern_condition": "<not declared>",
  "upper_byte_lane_error_allowed": false
}

Locked SSOT YAML excerpt (dma_real/yaml/dma_real.ssot.yaml):
top_module:
  name: dma_real_top
  description: Production-grade multi-channel DMA controller with dual-clock architecture
    (pclk for APB configuration, hclk for AHB-Lite data transfer), CDC async FIFO
    bridge, full AHB-Lite master protocol with RETRY/SPLIT support, per-channel
    programmable stride, bus timeout detection, performance counters, and clock gating.
    N_CHANNELS parameterized via generate blocks.
  file: rtl/dma_real_top.sv
  owner: ssot-manual
  quality_profile: standard
sub_modules:
- name: dma_real_apb_cfg
  file: rtl/dma_real_apb_cfg.sv
  ownership: manifest
  rtl_emit: true
  implements:
  - registers.register_list
  - io_list.interfaces.apb_slave
  source_sections:
  - registers
  - io_list
  function_model_refs:
  - function_model.state_variables
  register_refs:
  - registers.register_list
  description: APB slave register decode in pclk domain. Writes latched into sync
    registers, crossed to hclk domain via CDC.
  dataflow_refs:
  - dataflow.sequence.sequence_0
  - dataflow.sequence.sequence_1
  - dataflow.ordering.ordering_0
- name: dma_real_arbiter
  file: rtl/dma_real_arbiter.sv
  ownership: manifest
  rtl_emit: true
  implements:
  - function_model.transactions.FM_ARB_GRANT
  source_sections:
  - function_model
  - cycle_model
  function_model_refs:
  - function_model.transactions.FM_ARB_GRANT
  cycle_model_refs:
  - cycle_model.handshake_rules
  - cycle_model.performance
  description: Round-robin priority arbiter in hclk domain. Grants AHB bus access
    to one requesting channel per burst cycle.
  dataflow_refs:
  - dataflow.sequence.sequence_2
  - dataflow.ordering.ordering_1
- name: dma_real_channel
  file: rtl/dma_real_channel.sv
  ownership: manifest
  rtl_emit: true
  implements:
  - function_model.transactions.FM_DMA_STEP
  - function_model.transactions.FM_DMA_START
  - function_model.transactions.FM_DMA_COMPLETE
  - function_model.transactions.FM_DMA_ERROR
  - fsm.per_channel
  source_sections:
  - io_list
  - parameters
  - registers
  - function_model
  - cycle_model
  - fsm
  - error_handling
  function_model_refs:
  - function_model.transactions.FM_DMA_STEP
  - function_model.transactions.FM_DMA_START
  - function_model.state_variables
  - function_model.invariants
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.handshake_rules
  - cycle_model.performance
  register_refs:
  - registers.register_list
  fsm_refs:
  - fsm.per_channel
  description: Per-channel FSM with pointer-based FIFO, address counters with programmable
    stride, burst controller, timeout counter, and performance counters. Instantiated
    N_CHANNELS times via generate block.
  dataflow_refs:
  - dataflow.sequence.sequence_3
  - dataflow.sequence.sequence_4
  - dataflow.sequence.sequence_5
  - dataflow.sequence.sequence_6
  - dataflow.sequence.sequence_7
  - dataflow.sequence.sequence_8
  - dataflow.sequence.sequence_9
  - dataflow.sequence.sequence_10
  - dataflow.sequence.sequence_11
  - dataflow.ordering.ordering_1
  - dataflow.ordering.ordering_2
  - dataflow.ordering.ordering_3
  - dataflow.ordering.ordering_4
- name: dma_real_ahb_master
  file: rtl/dma_real_ahb_master.sv
  ownership: manifest
  rtl_emit: true
  implements:
  - io_list.interfaces.ahb_master
  - cycle_model.pipeline
  source_sections:
  - io_list
  - cycle_model
  function_model_refs:
  - function_model.transactions.FM_DMA_STEP
  cycle_model_refs:
  - cycle_model.pipeline
  - cycle_model.handshake_rules
  description: Full AHB-Lite master protocol engine in hclk domain. Supports INCR4/8/16/INCR
    and WRAP4/8/16 bursts, hprot/hmaster/hmastlock, 2-bit hresp (OKAY/ERROR/RETRY/SPLIT),
    dynamic hsize, and 1KB boundary crossing detection.
  dataflow_refs:
  - dataflow.sequence.sequence_5
  - dataflow.sequence.sequence_6
  - dataflow.ordering.ordering_2
- name: dma_real_irq
  file: rtl/dma_real_irq.sv
  ownership: manifest
  rtl_emit: true
  implements:
  - io_list.interfaces.irq_outputs
  - interrupts
  source_sections:
  - interrupts
  - registers
  function_model_refs:
  - function_model.state_variables
  register_refs:
  - registers.register_list
  description: Interrupt aggregation in pclk domain. Sticky latch per channel for
    done/error with INT_CLEAR write-1-to-clear. Combined IRQ output.
- name: dma_real_engine
  file: rtl/dma_real_engine.sv
  ownership: manifest
  rtl_emit: true
  implements:
  - function_model.transactions.FM_DMA_STEP
  - cycle_model.pipeline
  source_sections:
  - function_model
  - cycle_model
  - fsm
  function_model_refs:
  - function_model.transactions.FM_DMA_STEP
  cycle_model_refs:
  - cycle_model.pipeline
  description: hclk-domain top module connecting arbiter, N_CHANNELS channel instances,
    shared AHB master, and per-channel clock gating cells. Config from pclk domain
    received via CDC async FIFO.
decomposition:
  units:
  - id: apb_decode
    kind: control
    source_refs:
    - registers.register_list
    - io_list.interfaces.apb_slave
    rtl_candidates:
    - dma_real_apb_cfg
  - id: cdc_bridge
    kind: cdc
    source_refs:
    - clock_reset_domains
    - cdc_requirements
    rtl_candidates:
    - dma_real_top
  - id: channel_config
    kind: control
    source_refs:
    - registers.register_list
    - function_model.transactions.FM_DMA_START
    rtl_candidates:
    - dma_real_apb_cfg
    - dma_real_channel
  - id: arbitration
    kind: control
    source_refs:
    - function_model.transactions.FM_ARB_GRANT
    - cycle_model.performance
    rtl_candidates:
    - dma_real_arbiter
  - id: transfer_control
    kind: datapath_control
    source_refs:
    - function_model.transactions.FM_DMA_STEP
    - fsm.per_channel
    rtl_candidates:
    - dma_real_channel
  - id: ahb_protocol
    kind: datapath
    source_refs:
    - io_list.interfaces.ahb_master
    - cycle_model.pipeline
    rtl_candidates:
    - dma_real_ahb_master
  - id: fifo_buffer
    kind: datapath
    source_refs:
    - memory.internal
    rtl_candidates:
    - dma_real_channel
  - id: completion_status
    kind: status
    source_refs:
    - function_model.transactions.FM_DMA_COMPLETE
    - function_model.transactions.FM_DMA_ERROR
    - function_model.invariants
    rtl_candidates:
    - dma_real_channel
    - dma_real_irq
  - id: irq_aggregation
    kind: status
    source_refs:
    - interrupts
    - registers.register_list
    rtl_candidates:
    - dma_real_irq
  - id: clock_gating
    kind: power
    source_refs:
    - power.domains
    rtl_candidates:
    - dma_real_engine
  - id: perf_counter
    kind: status
    source_refs:
    - registers.register_list
    rtl_candidates:
    - dma_real_channel
parameters:
- name: ADDR_WIDTH
  type: int
  default: 32
  description: Address bus width for APB and AHB-Lite interfaces
  user_editable: true
- name: DATA_WIDTH
  type: int
  default: 32
  description: Data bus width (must be 32 for this revision)
  user_editable: false
- name: N_CHANNELS
  type: int
  default: 4
  description: Number of independent DMA channels (instantiated via generate)
  user_editable: true
- name: BURST_MAX
  type: int
  default: 16
  description: Maximum burst length per AHB beat (1..16)
  user_editable: true
- name: FIFO_DEPTH
  type: int
  default: 16
  description: Per-channel async FIFO depth in words (must be power of 2)
  user_editable: true
- name: TIMEOUT_DEFAULT
  type: int
  default: 1024
  description: Default bus timeout in hclk cycles (0 = disabled)
  user_editable: true
io_list:
  clock_domains:
  - name: pclk_domain
    ports:
    - name: pclk
      direction: input
      width: 1
      description: APB configuration clock
  - name: hclk_domain
    ports:
    - name: hclk
      direction: input
      width: 1
      description: AHB data transfer clock (may be async to pclk)
  resets:
  - name: presetn_domain
    active: low
    ports:
    - name: presetn
      direction: input
      width: 1
      description: Active-low reset for pclk domain
  - name: hresetn_domain
    active: low
    ports:
    - name: hresetn
      direction: input
      width: 1
      description: Active-low reset for hclk domain (async to presetn)
  interfaces:
  - name: apb_slave
    type: apb
    clock_domain: pclk_domain
    ports:
    - name: psel
      direction: input
      width: 1
      description: APB select
    - name: penable
      direction: input
      width: 1
      description: APB enable
    - name: pwrite
      direction: input
      width: 1
      description: APB write direction
    - name: paddr
      direction: input
      width: 12
      description: APB address bus
    - name: pwdata
      direction: input
      width: 32
      description: APB write data
    - name: prdata
      direction: output
      width: 32
      description: APB read data
    - name: pready
      direction: output
      width: 1
      description: APB ready (always 1, no wait states)
    - name: pslverr
      direction: output
      width: 1
      description: APB slave error on unmapped address
    protocol:
      timing: two-phase (setup + access)
      rules:
      - psel asserted before penable
      - write data sampled when penable and pwrite are high
      - pready always high (no wait states)
      - pslverr asserted when paddr targets unmapped register space
  - name: ahb_master
    type: ahb_lite
    clock_domain: hclk_domain
    ports:
    - name: haddr
      direction: output
      width: ADDR_WIDTH
      parameter_ref: ADDR_WIDTH
      description: AHB-Lite address bus
    - name: hwrite
      direction: output
      width: 1
      description: AHB-Lite write indicator
    - name: htrans
      direction: output
      width: 2
      description: AHB-Lite transfer type (00=IDLE, 10=NONSEQ, 11=SEQ)
    - name: hsize
      direction: output
      width: 3
      description: AHB-Lite transfer size (000=byte, 001=halfword, 010=word, 011=doubleword)
    - name: hburst
      direction: output
      width: 3
      description: AHB-Lite burst type (000=SINGLE, 001=INCR4, 010=INCR8, 011=INCR16,
        101=WRAP4, 110=WRAP8, 111=WRAP16)
    - name: hprot
      direction: output
      width: 4
      description: AHB-Lite protection control (bit3=cacheable, bit2=bufferable,
        bit1=privileged, bit0=data/opcode)
    - name: hmaster
      direction: output
      width: 4
      description: AHB-Lite master ID for bus matrix decode
    - name: hmastlock
      direction: output
      width: 1
      description: AHB-Lite locked transfer (atomic burst)
    - name: hwdata
      direction: output
      width: DATA_WIDTH
      parameter_ref: DATA_WIDTH
      description: AHB-Lite write data (driven in data phase)
    - name: hrdata
      direction: input
      width: DATA_WIDTH
      parameter_ref: DATA_WIDTH
      description: AHB-Lite read data (sampled in data phase)
    - name: hready
      direction: input
      width: 1
      description: AHB-Lite transfer done from slave
    - name: hresp
      direction: input
      width: 2
      description: AHB-Lite response (00=OKAY, 01=ERROR, 10=RETRY, 11=SPLIT)
    - name: hbusreq
      direction: output
      width: 1
      description: AHB-Lite bus request to arbiter
    - name: hgrant
      direction: input
      width: 1
      description: AHB-Lite bus grant from arbiter
    protocol:
      timing: address phase then data phase, pipelined, 1KB boundary rules
      rules:
      - haddr and control signals valid during address phase
      - hwdata valid during data phase (one cycle after address phase)
      - htrans=NONSEQ for first beat of burst, SEQ for subsequent beats
      - hburst encodes burst type; INCR4/8/16 for linear, WRAP4/8/16 for wrapping
      - hsize set per CHx_CTRL.hsize field (byte/halfword/word/doubleword)
      - hprot default 0011 (data, non-privileged, non-bufferable, non-cacheable)
      - hmaster set to channel ID of current transfer owner
      - hmastlock asserted for locked sequential transfers
      - "hresp 2-bit: OKAY=normal, ERROR=abort transfer, RETRY=retry same transfer, SPLIT=released bus and re-request"
      - Burst crossing 1KB boundary starts new NONSEQ beat with updated hburst
      - hresp=ERROR triggers transfer abort and error latch with code 3
      - hresp=RETRY causes master to release bus and re-request same transfer
      - hresp=SPLIT causes master to release bus and wait for HSPLIT signal
  - name: irq_outputs
    type: irq
    clock_domain: pclk_domain
    ports:
    - name: irq
      direction: output
      width: N_CHANNELS
      parameter_ref: N_CHANNELS
      description: Per-channel interrupt (done or error, level-sensitive active-high)
    - name: irq_combined
      direction: output
      width: 1
      description: Combined interrupt (OR of all enabled channel IRQs)
    protocol:
      timing: level-sensitive, active-high
      rules:
      - irq[ch] asserted when (done_q[ch] OR error_q[ch]) AND int_enable[ch]
      - irq_combined is OR of all per-channel IRQ outputs
      - IRQ deasserted when INT_CLEAR written and condition clears
  - name: dma_status
    type: status
    clock_domain: hclk_domain
    ports:
    - name: ch_busy
      direction: output
      width: N_CHANNELS
      parameter_ref: N_CHANNELS
      description: Per-channel busy flag (1 = channel FSM not IDLE)
    - name: ch_done
      direction: output
      width: N_CHANNELS
      parameter_ref: N_CHANNELS
      description: Per-channel done pulse (1 cycle, latched by IRQ module)
    - name: ch_error
      direction: output
      width: N_CHANNELS
      parameter_ref: N_CHANNELS
      description: Per-channel error pulse (1 cycle, latched by IRQ module)
    - name: ch_err_code
      direction: output
      width: 8
      description: Packed per-channel 3-bit error code (bits [3*ch+2:3*ch])
    - name: arb_grant
      direction: output
      width: 3
      description: Current arbiter grant channel index
    protocol:
      timing: registered on hclk edge, synchronized to pclk for readback
      rules:
      - ch_busy[ch] reflects per-channel FSM not in IDLE state
      - ch_done[ch] pulses for one hclk cycle on transfer completion
      - ch_error[ch] pulses for one hclk cycle on error detection
      - ch_err_code packed 3-bit code per channel (0=none, 1=align, 2=zero_len,
        3=bus_err, 4=timeout, 5=fifo_overflow)
      - arb_grant shows current round-robin grant target
features:
- id: multi_channel
  description: N_CHANNELS independent DMA channels with separate configuration, status,
    stride, and performance counters. Instantiated via generate block.
  source_refs:
  - parameters.N_CHANNELS
  - registers.register_list
- id: dual_clock_cdc
  description: Dual-clock architecture with pclk for APB configuration and hclk for
    AHB data transfer. Async FIFO and gray-code pointer synchronization bridge the
    domains.
  source_refs:
  - clock_reset_domains
  - cdc_requirements
  - memory.internal
- id: round_robin_arb
  description: Round-robin arbitration among active channels requesting AHB access.
    Starvation-free guarantee.
  source_refs:
  - function_model.transactions.FM_ARB_GRANT
  - cycle_model.performance
- id: full_ahb_lite
  description: Full AHB-Lite master with INCR4/8/16/INCR and WRAP4/8/16 bursts,
    2-bit hresp (OKAY/ERROR/RETRY/SPLIT), hprot, hmaster, hmastlock, dynamic hsize,
    and 1KB boundary crossing detection.
  source_refs:
  - io_list.interfaces.ahb_master
  - parameters.BURST_MAX
- id: per_channel_irq
  description: Per-channel done/error interrupt with mask and combined output. Sticky
    latches cleared by INT_CLEAR write-1-to-clear.
  source_refs:
  - interrupts
  - io_list.interfaces.irq_outputs
- id: error_detection
  description: Alignment, zero-length, bus error, timeout, and FIFO overflow detection
    per channel with 3-bit error codes.
  source_refs:
  - error_handling
  - function_model.transactions.FM_DMA_ERROR
- id: programmable_stride
  description: Per-channel CHx_STRIDE register controls address increment per beat.
    Default 4 (word), set to 0 for fixed-address peripheral access.
  source_refs:
  - registers.register_list
- id: bus_timeout
  description: Configurable GLOBAL_TIMEOUT register sets max hclk cycles to wait for
    hready. Timeout error (code 4) if exceeded. 0 disables timeout.
  source_refs:
  - registers.register_list
  - error_handling
- id: performance_counters
  description: Per-channel CHx_PERF_WORDS and CHx_PERF_CYCLES registers track transfer
    volume and active time.
  source_refs:
  - registers.register_list
- id: clock_gating
  description: Per-channel integrated clock-gating cell in hclk domain. Auto-gates
    when channel FSM is IDLE to reduce dynamic power.
  source_refs:
  - power.domains
dataflow:
  sequence:
  - Software configures channel registers via APB in pclk domain (SRC, DST, LEN,
    STRIDE, CTRL).
  - APB config written to CDC async FIFO for crossing to hclk domain.
  - Software sets CTRL.ch_start to initiate transfer.
  - Channel FSM (hclk) transitions IDLE to CFG, latches config from CDC bridge.
  - Channel requests AHB bus via arbiter (hclk).
  - Arbiter grants bus round-robin among active channels.
  - AHB master drives read burst from source address into pointer-based FIFO.
  - AHB master drives write burst from FIFO to destination address.
  - Addresses increment by CHx_STRIDE per beat (default 4).
  - Timeout counter monitors hready latency; error code 4 on expiry.
  - Performance counters increment (PERF_WORDS per word, PERF_CYCLES per active
    cycle).
  - Repeat read/write bursts until remaining count reaches zero.
  - Channel asserts done pulse (1 hclk cycle), IRQ module latches sticky in pclk
    domain.
  - IRQ asserted if enabled.
  ordering:
  - Configuration (APB write in pclk) must cross CDC before hclk channel FSM reads
    it.
  - Arbiter grant must precede AHB address phase.
  - Read burst completion must precede write burst for same data.
  - Address update must precede next burst request.
  - Transfer completion (DONE) precedes done pulse observation.
  - 1KB boundary crossing starts new NONSEQ beat.
function_model:
  purpose: Behavioral DMA reference model independent of dual-clock microarchitecture.
    Models single-logical-cycle semantics; CDC and clock domain details are implementation
    concerns.
  state_variables:
  - name: ch_busy_q
    width: N_CHANNELS
    reset: 0
    description: Per-channel busy flag
  - name: ch_done_q
    width: N_CHANNELS
    reset: 0
    description: Per-channel done sticky latch
  - name: ch_error_q
    width: N_CHANNELS
    reset: 0
    description: Per-channel error sticky latch
  - name: ch_remaining_q
    width: 32
    reset: 0
    description: Per-channel remaining word count
  - name: ch_src_addr_q
    width: ADDR_WIDTH
    reset: 0
    description: Per-channel current source address
  - name: ch_dst_addr_q
    width: ADDR_WIDTH
    reset: 0
    description: Per-channel current destination address
  - name: ch_stride_q
    width: ADDR_WIDTH
    reset: 4
    description: Per-channel address increment per beat (default 4 for word)
  - name: dma_en_q
    width: 1
    reset: 0
    description: Global DMA enable
  - name: int_enable_q
    width: N_CHANNELS
    reset: 0
    description: Per-channel interrupt enable mask
  - name: arb_ptr_q
    width: 3
    reset: 0
    description: Round-robin arbiter pointer
  - name: timeout_q
    width: 16
    reset: 0
    description: Bus timeout threshold in hclk cycles
  - name: perf_words_q
    width: 32
    reset: 0
    description: Per-channel total words transferred
  - name: perf_cycles_q
    width: 32
    reset: 0
    description: Per-channel total active cycles
  transactions:
  - id: FM_DMA_START
    name: dma_start
    required_fields:
    - ch_id
    - src_addr
    - dst_addr
    - length
    - stride
    preconditions:
    - presetn and hresetn are deasserted
    - dma_en_q == 1
    - ch_busy_q[ch_id] == 0
    outputs:
    - ch_busy
    - ch_error
    - ch_err_code
    output_rules:
    - name: ch_busy_next
      port: ch_busy
      width: 1
      expr: 1 if (dma_en_q and not ch_busy_q[ch_id] and length > 0 and (src_addr
        % 4 == 0) and (dst_addr % 4 == 0)) else 0
    - name: ch_error_flag
      port: ch_error
      width: 1
      expr: 1 if (length == 0 or src_addr % 4 != 0 or dst_addr % 4 != 0) else 0
    - name: ch_err_code_val
      port: ch_err_code
      width: 3
      expr: 2 if (length == 0) else 1 if (src_addr % 4 != 0 or dst_addr % 4 != 0)
        else 0
    side_effects:
    - ch_remaining_q[ch_id] set to length on valid start
    - ch_src_addr_q[ch_id] set to src_addr on valid start
    - ch_dst_addr_q[ch_id] set to dst_addr on valid start
    - ch_stride_q[ch_id] set to stride on valid start
    - perf_cycles_q[ch_id] reset to 0 on valid start
    - perf_words_q[ch_id] reset to 0 on valid start
    error_cases:
    - zero length (length == 0, error code 2)
    - misaligned source address (src_addr % 4 != 0, error code 1)
    - misaligned destination address (dst_addr % 4 != 0, error code 1)
    - start while busy (ignored, preserves state)
  - id: FM_DMA_STEP
    name: dma_step
    required_fields:
    - ch_id
    - burst_len
    preconditions:
    - ch_busy_q[ch_id] == 1
    - arbiter has granted bus to ch_id
    outputs:
    - ch_busy
    - ch_done
    output_rules:
    - name: busy_next
      port: ch_busy
      width: 1
      expr: 1 if (ch_remaining_q[ch_id] > burst_len) else 0
    - name: done_pulse
      port: ch_done
      width: 1
      expr: 1 if (ch_remaining_q[ch_id] <= burst_len and ch_remaining_q[ch_id]
        > 0) else 0
    state_updates:
    - name: remaining_next
      expr: ch_remaining_q[ch_id] - burst_len if ch_remaining_q[ch_id] > burst_len
        else 0
      width: 32
    - name: src_addr_next
      expr: ch_src_addr_q[ch_id] + burst_len * ch_stride_q[ch_id]
      width: ADDR_WIDTH
    - name: dst_addr_next
      expr: ch_dst_addr_q[ch_id] + burst_len * ch_stride_q[ch_id]
      width: ADDR_WIDTH
    - name: perf_words_next
      expr: perf_words_q[ch_id] + burst_len
      width: 32
    - name: perf_cycles_next
      expr: perf_cycles_q[ch_id] + burst_len + 4
      width: 32
    side_effects:
    - ch_remaining_q decrements by burst_len
    - ch_src_addr_q increments by burst_len * ch_stride_q[ch_id]
    - ch_dst_addr_q increments by burst_len * ch_stride_q[ch_id]
    - perf_words_q increments by burst_len
    - perf_cycles_q increments by burst_len plus pipeline overhead
    - done pulses on terminal step
    error_cases:
    - bus error during AHB transfer (hresp == ERROR, code 3)
    - timeout waiting for hready (code 4)
  - id: FM_DMA_COMPLETE
    name: dma_complete
    required_fields:
    - ch_id
    preconditions:
    - ch_remaining_q[ch_id] == 0
    - ch_busy_q[ch_id] == 1
    outputs:
    - ch_busy
    - ch_done
    - irq
    output_rules:
    - name: busy_clear
      port: ch_busy
      width: 1
      expr: 0
    - name: done_assert
      port: ch_done
      width: 1
      expr: 1
    - name: irq_assert
      port: irq
      width: 1
      expr: 1 if (int_enable_q[ch_id]) else 0
    side_effects:
    - ch_done_q[ch_id] set to 1
    - ch_busy_q[ch_id] cleared
    - IRQ asserted if enabled
    error_cases: []
  - id: FM_DMA_ERROR
    name: dma_error
    required_fields:
    - ch_id
    - error_code
    preconditions:
    - error condition detected (alignment, zero-length, bus error, timeout, or FIFO
      overflow)
    outputs:
    - ch_error
    - ch_err_code
    - irq
    output_rules:
    - name: error_assert
      port: ch_error
      width: 1
      expr: 1
    - name: error_code_out
      port: ch_err_code
      width: 3
      expr: error_code
    - name: irq_error
      port: irq
      width: 1
      expr: 1 if (int_enable_q[ch_id]) else 0
    side_effects:
    - ch_error_q[ch_id] set to 1
    - ch_busy_q[ch_id] cleared
    - Error code latched in status register
    error_cases:
    - alignment error (code 1)
    - zero length (code 2)
    - bus error (code 3)
    - timeout (code 4)
    - FIFO overflow (code 5)
  - id: FM_ARB_GRANT
    name: arb_grant
    required_fields:
    - requester_mask
    preconditions:
    - at least one channel is requesting bus access
    outputs:
    - arb_grant
    output_rules:
    - name: grant_next
      port: arb_grant
      width: 3
      expr: (arb_ptr_q + 1) % N_CHANNELS if requester_mask[arb_ptr_q] == 0 else
        arb_ptr_q
    state_updates:
    - name: arb_ptr_update
      expr: (grant_ch + 1) % N_CHANNELS
      width: 3
    side_effects:
    - arb_ptr_q updated to next channel after grant
    - granted channel gains AHB bus access
    error_cases: []
  invariants:
  - ch_busy and ch_done are not asserted together for the same channel.
  - ch_error is asserted only for invalid requests, bus errors, timeouts, or FIFO
    overflows.
  - ch_remaining_q never underflows below zero.
  - irq[ch] reflects (done_q[ch] OR error_q[ch]) AND int_enable_q[ch].
  - irq_combined reflects OR of all per-channel irq outputs.
  - Each FIFO operates as circular buffer with gray-code synchronized pointers across
    clock domains.
  - htrans transitions IDLE only when no channel has an active grant.
  - Performance counters saturate at 32'hFFFFFFFF and do not wrap.
cycle_model:
  executable: pymtl3
  backend_policy: Use PyMTL3 shell for cycle behavior. FunctionalModel remains oracle.
  clock: hclk
  reset: hresetn
  latency: 5
  handshake_rules:
  - name: apb_access
    description: APB accesses sample on pclk with psel and penable. No wait states.
      Config data crosses CDC to hclk domain via async FIFO.
  - name: cdc_config
    description: APB write data pushed into pclk-side FIFO write port. hclk-side
      read port pops config. Gray-code pointer synchronization prevents metastability.
  - name: ahb_address_phase
    description: AHB address phase drives haddr, htrans, hsize, hburst, hprot, hmaster,
      hmastlock for one hclk cycle.
  - name: ahb_data_phase
    description: AHB data phase follows address phase by one hclk cycle with hwdata
      or hrdata.
  - name: ahb_1kb_boundary
    description: Burst crossing 1KB address boundary starts new NONSEQ beat. hburst
      recalculated for remaining beats.
  - name: ahb_error_response
    description: hresp=ERROR (01) completes current beat and aborts burst. hresp=RETRY
      (10) releases bus and re-requests. hresp=SPLIT (11) releases bus and waits.
  - name: arb_grant_rule
    description: Arbiter evaluates requests every hclk cycle and grants to next round-robin
      contender.
  - name: start_accept
    description: ch_start accepted only when ch_busy is low and dma_en is high and
      CDC config has arrived.
  - name: timeout_rule
    description: Timeout counter increments each hclk cycle while waiting for hready.
      Resets on hready assertion. Error code 4 when counter reaches GLOBAL_TIMEOUT.
  pipeline:
  - stage: IDLE
    cycle: 0
    action: wait for valid start/config from CDC bridge
  - stage: CFG
    cycle: 1
    action: latch src_addr, dst_addr, remaining, stride from CDC config registers
  - stage: REQUEST
    cycle: 2
    action: request AHB bus via arbiter, clock gating cell enables hclk to channel
  - stage: READ
    cycle: 3
    action: AHB read burst from source address into pointer-based FIFO, timeout counter
      active
  - stage: WRITE
    cycle: 4
    action: AHB write burst from FIFO to destination address, FIFO read pointer advances
  - stage: UPDATE
    cycle: 5
    action: update remaining count (decrement), src_addr (+= stride), dst_addr (+=
      stride), perf counters increment
  - stage: DONE
    cycle: 6
    action: assert done pulse, update status, trigger IRQ, clock gating cell may
      disable hclk
  - stage: ERROR
    cycle: 2
    action: assert error pulse, latch error code, return to IDLE, clock gating cell
      may disable hclk
  ordering:
  - Configuration (APB pclk) must cross CDC before hclk channel FSM reads it.
  - Read burst completion must precede write burst for same data.
  - Address update (UPDATE) must precede next burst request.
  - Transfer completion (DONE) precedes done pulse observation.
  - 1KB boundary crossing recalculates burst parameters before next address phase.
  backpressure:
  - New starts blocked while channel busy.
  - AHB transfers stall when hready is low.
  - Arbiter queues requests when bus is occupied.
  - FIFO almost_full back-pressures read burst.
  - CDC FIFO full back-pressures APB writes (pslverr or pready deassert).
  performance:
    outstanding_limit: N_CHANNELS
    throughput: one burst per channel per arbiter round
    cdc_latency: 3 hclk cycles for config to cross from pclk domain
    fifo_depth: FIFO_DEPTH words per channel
clock_reset_domains:
  domains:
  - name: pclk_domain
    clock: pclk
    reset: presetn
    reset_active: low
    description: APB configuration clock domain. apb_cfg and irq modules operate
      here.
  - name: hclk_domain
    clock: hclk
    reset: hresetn
    reset_active: low
    description: AHB data transfer clock domain. arbiter, channels, ahb_master, engine
      operate here. May be async to pclk.
cdc_requirements:
  policy: gray_code_async_fifo
  description: Config data from pclk domain crosses to hclk domain via dual-clock
    async FIFO with gray-code pointer synchronization. Status signals (ch_busy, ch_done,
    ch_error) cross from hclk to pclk via 2-stage synchronizer.
  crossings:
  - name: config_cdc
    source_clock: pclk
    dest_clock: hclk
    data_width: ADDR_WIDTH + ADDR_WIDTH + 16 + ADDR_WIDTH + 3
    description: Channel config (src_addr + dst_addr + len + stride + ctrl) packed
      and pushed on APB write, popped by hclk channel FSM.
    protocol: async FIFO with gray-code rd_ptr and wr_ptr, 2-stage sync
  - name: status_cdc
    source_clock: hclk
    dest_clock: pclk
    data_width: N_CHANNELS * 4
    description: Per-channel status (busy, done_pulse, error_pulse, err_code) synchronized
      for APB readback.
    protocol: 2-stage flip-flop synchronizer with pulse-to-level converter
  - name: irq_cdc
    source_clock: hclk
    dest_clock: pclk
    data_width: N_CHANNELS * 2
    description: Per-channel done and error pulses cross to pclk for IRQ module sticky
      latch.
    protocol: pulse synchronizer (toggle + 2-stage sync + edge detect)
rdc_requirements:
  policy: async_reset_deassert_sync
  description: presetn and hresetn are async assert, sync deassert. Each domain has
    its own reset synchronizer. Cross-domain reset ordering not guaranteed.
registers:
  register_list:
  - name: GLOBAL_CTRL
    offset: 0
    width: 32
    access: rw
    reset: 0x00000000
    description: Global DMA control register
    fields:
    - name: dma_en
      lsb: 0
      width: 1
      access: rw
      reset: 0
      description: Global DMA enable
      write_effect: enables or disables DMA globally
    - name: reserved_31_1
      lsb: 1
      width: 31
      access: rw
      reset: 0
      description: Reserved
      write_effect: no side effect
  - name: INT_STATUS
    offset: 4
    width: 32
    access: ro
    reset: 0x00000000
    description: Per-channel interrupt status (bit per channel)
    fields:
    - name: ch_status
      lsb: 0
      width: 4
      access: ro
      reset: 0
      description: Bit[ch] is 1 when channel ch has pending interrupt
      write_effect: read-only
  - name: INT_ENABLE
    offset: 8
    width: 32
    access: rw
    reset: 0x00000000
    description: Per-channel interrupt enable mask
    fields:
    - name: ch_enable
      lsb: 0
      width: 4
      access: rw
      reset: 0
      description: Bit[ch] = 1 enables interrupt for channel ch
      write_effect: updates interrupt mask
  - name: INT_CLEAR
    offset: 12
    width: 32
    access: wo
    reset: 0x00000000
    description: Write-1-to-clear per-channel interrupt
    fields:
    - name: ch_clear
      lsb: 0
      width: 4
      access: wo
      reset: 0
      description: Writing 1 to bit[ch] clears done_q and error_q for channel ch
      write_effect: clears latched done and error status
  - name: GLOBAL_TIMEOUT
    offset: 16
    width: 32
    access: rw
    reset: 0x00000400
    description: Bus timeout threshold in hclk cycles. 0 disables timeout.
    fields:
    - name: timeout_val
      lsb: 0
      width: 16
      access: rw
      reset: 1024
      description: Max hclk cycles to wait for hready. 0 = disabled.
      write_effect: updates timeout threshold for all channels
    - name: reserved_31_16
      lsb: 16
      width: 16
      access: rw
      reset: 0
      description: Reserved
      write_effect: no side effect
  - name: CH0_CTRL
    offset: 256
    width: 32
    access: rw
    reset: 0x00000000
    description: Channel 0 control register
    fields:
    - name: ch_en
      lsb: 0
      width: 1
      access: rw
      reset: 0
      description: Channel enable
      write_effect: enables or disables the channel
    - name: ch_start
      lsb: 1
      width: 1
      access: rw
      reset: 0
      description: Write 1 to start transfer (self-clearing)
      write_effect: initiates DMA transfer if ch_en and dma_en are set
    - name: hsize
      lsb: 2
      width: 2
      access: rw
      reset: 0
      description: Transfer size (00=byte, 01=halfword, 10=word)
      write_effect: sets hsize for AHB transfers
    - name: burst_mode
      lsb: 4
      width: 2
      access: rw
      reset: 0
      description: Burst mode (00=INCR, 01=INCR4, 10=INCR8, 11=INCR16)
      write_effect: selects burst type for AHB
    - name: reserved_31_6
      lsb: 6
      width: 26
      access: rw
      reset: 0
      description: Reserved
      write_effect: no side effect
  - name: CH0_SRC_ADDR
    offset: 260
    width: 32
    access: rw
    reset: 0x00000000
    description: Channel 0 source start address (must be word-aligned for word transfers)
    fields:
    - name: src_addr
      lsb: 0
      width: 32
      access: rw
      reset: 0
      description: Source address
      write_effect: latches source address for transfer
  - name: CH0_DST_ADDR
    offset: 264
    width: 32
    access: rw
    reset: 0x00000000
    description: Channel 0 destination start address
    fields:
    - name: dst_addr
      lsb: 0
      width: 32
      access: rw
      reset: 0
      description: Destination address
      write_effect: latches destination address for transfer
  - name: CH0_LEN
    offset: 268
    width: 32
    access: rw
    reset: 0x00000000
    description: Channel 0 transfer length in words (1..65536). 0 is invalid.
    fields:
    - name: length
      lsb: 0
      width: 16
      access: rw
      reset: 0
      description: Transfer length in words
      write_effect: sets number of words to transfer
    - name: reserved_31_16
      lsb: 16
      width: 16
      access: rw
      reset: 0
      description: Reserved
      write_effect: no side effect
  - name: CH0_STATUS
    offset: 272
    width: 32
    access: ro
    reset: 0x00000000
    description: Channel 0 status register
    fields:
    - name: busy
      lsb: 0
      width: 1
      access: ro
      reset: 0
      description: Channel is actively transferring
      write_effect: read-only
    - name: done
      lsb: 1
      width: 1
      access: ro
      reset: 0
      description: Transfer completed (sticky, cleared by INT_CLEAR)
      write_effect: read-only
    - name: error
      lsb: 2
      width: 1
      access: ro
      reset: 0
      description: Error occurred (sticky, cleared by INT_CLEAR)
      write_effect: read-only
    - name: err_code
      lsb: 3
      width: 3
      access: ro
      reset: 0
      description: Error code (0=none, 1=align, 2=zero_len, 3=bus_err, 4=timeout,
        5=fifo_overflow)
      write_effect: read-only
    - name: reserved_31_6
      lsb: 6
      width: 26
      access: ro
      reset: 0
      description: Reserved
      write_effect: read-only
  - name: CH0_STRIDE
    offset: 276
    width: 32
    access: rw
    reset: 0x00000004
    description: Channel 0 address stride per beat. Default 4 (word). Set 0 for fixed-address
      peripheral.
    fields:
    - name: stride
      lsb: 0
      width: 32
      access: rw
      reset: 4
      description: Address increment per beat
      write_effect: sets address stride for transfer
  - name: CH0_PERF_WORDS
    offset: 284
    width: 32
    access: ro
    reset: 0x00000000
    description: Channel 0 total words transferred (saturating counter)
    fields:
    - name: word_count
      lsb: 0
      width: 32
      access: ro
      reset: 0
      description: Cumulative words transferred
      write_effect: read-only
  - name: CH0_PERF_CYCLES
    offset: 288
    width: 32
    access: ro
    reset: 0x00000000
    description: Channel 0 total active cycles (saturating counter)
    fields:
    - name: cycle_count
      lsb: 0
      width: 32
      access: ro
      reset: 0
      description: Cumulative active hclk cycles
      write_effect: read-only
  - name: CH1_CTRL
    offset: 320
    width: 32
    access: rw
    reset: 0x00000000
    description: Channel 1 control register
    fields:
    - name: ch_en
      lsb: 0
      width: 1
      access: rw
      reset: 0
      description: Channel enable
      write_effect: enables or disables the channel
    - name: ch_start
      lsb: 1
      width: 1
      access: rw
      reset: 0
      description: Write 1 to start transfer
      write_effect: initiates DMA transfer
    - name: hsize
      lsb: 2
      width: 2
      access: rw
      reset: 0
      description: Transfer size
      write_effect: sets hsize for AHB transfers
    - name: burst_mode
      lsb: 4
      width: 2
      access: rw
      reset: 0
      description: Burst mode
      write_effect: selects burst type
    - name: reserved_31_6
      lsb: 6
      width: 26
      access: rw
      reset: 0
      description: Reserved
      write_effect: no side effect
  - name: CH1_SRC_ADDR
    offset: 324
    width: 32
    access: rw
    reset: 0x00000000
    description: Channel 1 source start address
    fields:
    - name: src_addr
      lsb: 0
      width: 32
      access: rw
      reset: 0
      description: Source address
      write_effect: latches source address
  - name: CH1_DST_ADDR
    offset: 328
    width: 32
    access: rw
    reset: 0x00000000
    description: Channel 1 destination start address
    fields:
    - name: dst_addr
      lsb: 0
      width: 32
      access: rw
      reset: 0
      description: Destination address
      write_effect: latches destination address
  - name: CH1_LEN
    offset: 332
    width: 32
    access: rw
    reset: 0x00000000
    description: Channel 1 transfer length in words
    fields:
    - name: length
      lsb: 0
      width: 16
      access: rw
      reset: 0
      description: Transfer length
      write_effect: sets transfer length
    - name: reserved_31_16
      lsb: 16
      width: 16
      access: rw
      reset: 0
      description: Reserved
      write_effect: no side effect
  - name: CH1_STATUS
    offset: 336
    width: 32
    access: ro
    reset: 0x00000000
    description: Channel 1 status register
    fields:
    - name: busy
      lsb: 0
      width: 1
      access: ro
      reset: 0
      description: Channel busy
      write_effect: read-only
    - name: done
      lsb: 1
      width: 1
      access: ro
      reset: 0
      description: Transfer done
      write_effect: read-only
    - name: error
      lsb: 2
      width: 1
      access: ro
      reset: 0
      description: Error flag
      write_effect: read-only
    - name: err_code
      lsb: 3
      width: 3
      access: ro
      reset: 0
      description: Error code
      write_effect: read-only
    - name: reserved_31_6
      lsb: 6
      width: 26
      access: ro
      reset: 0
      description: Reserved
      write_effect: read-only
  - name: CH1_STRIDE
    offset: 340
    width: 32
    access: rw
    reset: 0x00000004
    description: Channel 1 address stride per beat
    fields:
    - name: strid
... <truncated 38450 chars>

Base rtl-gen contract:
Prepare rtl-gen for dma_real using only dma_real/yaml/dma_real.ssot.yaml and dma_real/rtl/rtl_todo_plan.json, dma_real/rtl/rtl_authoring_plan.json, and packets under dma_real/rtl/authoring_packets. Return exactly one JSON object and nothing else. Success schema: {"files":[{"path":"dma_real/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"},{"path":"dma_real/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"},{"path":"dma_real/list/dma_real.f","kind":"filelist","content":"<filelist>"}]}. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=08a17cccf5914d45200fe4745d1e515b35dfeed4fddb483eb6daaabc71eaacf3. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "owner_module": "dma_real_top",
        "reason": "64 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "dma_real_top",
        "reason": "1 owner logic structure issue(s) remain. dma_real_engine: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "rtl_placeholder_free_evidence",
        "owner_module": "dma_real_top",
        "reason": "6 RTL placeholder/policy issue(s) remain. rtl/dma_real_apb_cfg.sv:81: for ( (RTL source uses a for loop); rtl/dma_real_apb_cfg.sv:96: for ( (RTL source uses a for loop); rtl/dma_real_apb_cfg.sv:117: for ( (RTL source uses a for loop)",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "status": "open",
        "task_id": "RTL-0009"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "dma_real_top",
        "reason": "6 top IO contract issue(s) remain. hclk: SSOT top IO port is missing from RTL top declaration; hresetn: SSOT top IO port is missing from RTL top declaration; hprot: SSOT top IO port is missing from RTL top declaration",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "top_output_drive_evidence",
        "owner_module": "dma_real_top",
        "reason": "2 top output drive issue(s) remain. ch_done: RTL top output has no nonconstant assignment or declared child-output drive evidence; ch_error: RTL top output has no nonconstant assignment or declared child-output drive evidence",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
        "status": "open",
        "task_id": "RTL-0011"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "dma_real_top",
        "reason": "1 manifest hierarchy integration issue(s) remain. dma_real_engine: SSOT manifest child module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      },
      {
        "gate_kind": "manifest_port_connection_evidence",
        "owner_module": "dma_real_top",
        "reason": "1 manifest port connection issue(s) remain. dma_real_channel: Reachable child instance has missing or empty named port connections",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_port_connection_evidence",
        "status": "open",
        "task_id": "RTL-0014"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "dma_real_top",
        "reason": "1 manifest signal-flow issue(s) remain. dma_real_ahb_master: write_data: Manifest child output does not feed a top output, parent RTL logic, or another child input/inout",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "status": "open",
        "task_id": "RTL-0015"
      }
    ],
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "dma_real_top",
        "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/dma_real_engine.sv",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "dma_real_top",
        "reason": "DUT compile report does not list rtl_files for current filelist coverage.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "dma_real_top",
        "reason": "DUT lint artifact is not clean.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "dma_real_top",
        "reason": "76 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
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
    "open_required_todos": 77,
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
          "dma_real/rtl/rtl_authoring_provenance.json",
          "dma_real/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip dma_real --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py dma_real --root . --audit-rtl"
        ],
        "gate_kind": "common_ai_agent_authoring",
        "prerequisites": [
          "An LLM authoring pass emitted or repaired DUT RTL files."
        ],
        "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/dma_real_engine.sv",
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
          "dma_real/rtl/rtl_compile.json",
          "dma_real/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py dma_real --top dma_real_top --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py dma_real --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "dma_real/list/dma_real.f covers the current DUT RTL sources."
        ],
        "reason": "DUT compile report does not list rtl_files for current filelist coverage.",
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
          "dma_real/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py dma_real --top dma_real_top",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py dma_real --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "dma_real/list/dma_real.f covers the current DUT RTL/header sources."
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
          "dma_real/rtl/rtl_todo_plan.json",
          "dma_real/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py dma_real --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "76 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      }
    ]
  },
  "ip": "dma_real",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_engine.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/dma_real_engine.sv",
      "owner_module": "dma_real_engine",
      "packet_id": "module__dma_real_engine",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_apb_cfg__registers_02.json",
      "kind": "module",
      "llm_actionable_open_count": 16,
      "open_required_count": 16,
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "owner_module": "dma_real_apb_cfg",
      "packet_id": "module__dma_real_apb_cfg__registers_02",
      "required_count": 48,
      "status_counts": {
        "open": 16,
        "pass": 32
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_apb_cfg__registers_01.json",
      "kind": "module",
      "llm_actionable_open_count": 14,
      "open_required_count": 14,
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "owner_module": "dma_real_apb_cfg",
      "packet_id": "module__dma_real_apb_cfg__registers_01",
      "required_count": 48,
      "status_counts": {
        "open": 14,
        "pass": 34
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_apb_cfg__function_model.json",
      "kind": "module",
      "llm_actionable_open_count": 7,
      "open_required_count": 7,
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "owner_module": "dma_real_apb_cfg",
      "packet_id": "module__dma_real_apb_cfg__function_model",
      "required_count": 13,
      "status_counts": {
        "open": 7,
        "pass": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_apb_cfg__registers_03.json",
      "kind": "module",
      "llm_actionable_open_count": 5,
      "open_required_count": 5,
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "owner_module": "dma_real_apb_cfg",
      "packet_id": "module__dma_real_apb_cfg__registers_03",
      "required_count": 16,
      "status_counts": {
        "open": 5,
        "pass": 11
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_apb_cfg__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "owner_module": "dma_real_apb_cfg",
      "packet_id": "module__dma_real_apb_cfg__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_arbiter.json",
      "kind": "module",
      "llm_actionable_open_count": 7,
      "open_required_count": 7,
      "owner_file": "rtl/dma_real_arbiter.sv",
      "owner_module": "dma_real_arbiter",
      "packet_id": "module__dma_real_arbiter",
      "required_count": 28,
      "status_counts": {
        "open": 7,
        "pass": 21
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__dataflow.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__dataflow",
      "required_count": 12,
      "status_counts": {
        "open": 2,
        "pass": 10
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__error_handling",
      "required_count": 5,
      "status_counts": {
        "open": 2,
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__workflow_todo",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__function_model_02",
      "required_count": 28,
      "status_counts": {
        "open": 1,
        "pass": 27
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_ahb_master.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/dma_real_ahb_master.sv",
      "owner_module": "dma_real_ahb_master",
      "packet_id": "module__dma_real_ahb_master",
      "required_count": 19,
      "status_counts": {
        "open": 3,
        "pass": 16
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_irq.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/dma_real_irq.sv",
      "owner_module": "dma_real_irq",
      "packet_id": "module__dma_real_irq",
      "required_count": 6,
      "status_counts": {
        "open": 1,
        "pass": 5
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_top.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/dma_real_top.sv",
      "owner_module": "dma_real_top",
      "packet_id": "module__dma_real_top",
      "required_count": 43,
      "status_counts": {
        "open": 3,
        "pass": 40
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 8,
      "open_required_count": 8,
      "owner_file": "rtl/dma_real_top.sv",
      "owner_module": "dma_real_top",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 9,
      "status_counts": {
        "open": 8,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 4,
      "owner_file": "rtl/dma_real_top.sv",
      "owner_module": "dma_real_top",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_apb_cfg__dataflow.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "owner_module": "dma_real_apb_cfg",
      "packet_id": "module__dma_real_apb_cfg__dataflow",
      "required_count": 8,
      "status_counts": {
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_apb_cfg__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "owner_module": "dma_real_apb_cfg",
      "packet_id": "module__dma_real_apb_cfg__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_apb_cfg__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "owner_module": "dma_real_apb_cfg",
      "packet_id": "module__dma_real_apb_cfg__io_list",
      "required_count": 17,
      "status_counts": {
        "pass": 17
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__cycle_model",
      "required_count": 8,
      "status_counts": {
        "pass": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__fsm",
      "required_count": 20,
      "status_counts": {
        "pass": 20
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__function_model_01.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__function_model_01",
      "required_count": 48,
      "status_counts": {
        "pass": 48
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__dma_real_channel__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_channel.sv",
      "owner_module": "dma_real_channel",
      "packet_id": "module__dma_real_channel__parameters",
      "required_count": 6,
      "status_counts": {
        "pass": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/dma_real_top.sv",
      "owner_module": "dma_real_top",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 4,
      "status_counts": {
        "pass": 4
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
    "rtl_target_scale": {},
    "rtl_target_scale_waiver": {},
    "single_source_of_truth": "SSOT YAML is the only authority for function_model, cycle_model, RTL ownership, DV plan, and coverage.",
    "ssot_workflow_todo_rule": "workflow_todos.rtl-gen[] entries are first-class downstream tasks; content/detail/criteria must be preserved and satisfied by RTL evidence.",
    "target_scale_rule": "Optional quality_gates.rtl_gen.target_scale is SSOT-locked human policy. It can be calibrated from a reference profile, but it is enforced as generic structural depth evidence, not as copied reference RTL."
  },
  "reference_profile": {},
  "sim_debug_repair_evidence": {
    "items": 0,
    "owner_workflow": "rtl-gen",
    "source": "dma_real/sim/mismatch_classification.json"
  },
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 0,
    "human_locked_tasks": 0,
    "llm_actionable_packets": 15,
    "llm_actionable_tasks": 73,
    "max_packet_required_tasks": 48,
    "module_packets": 22,
    "next_llm_packets": [
      "module__dma_real_engine",
      "module__dma_real_apb_cfg__registers_02",
      "module__dma_real_apb_cfg__registers_01",
      "module__dma_real_apb_cfg__function_model",
      "module__dma_real_apb_cfg__registers_03",
      "module__dma_real_apb_cfg__workflow_todo",
      "module__dma_real_arbiter",
      "module__dma_real_channel__dataflow"
    ],
    "packet_task_limit": 48,
    "packets": 25,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 396,
    "sliced_module_packets": 17,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 4,
    "total_tasks": 396,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "08a17cccf5914d45200fe4745d1e515b35dfeed4fddb483eb6daaabc71eaacf3",
  "top": "dma_real_top",
  "type": "rtl_authoring_plan"
}

Current sim-debug owner repair evidence:
{
  "items": [],
  "owner_workflow": "rtl-gen",
  "source": "dma_real/sim/mismatch_classification.json",
  "status": "none"
}

Current owner RTL file (rtl/dma_real_engine.sv):
<missing or not authored yet>

Current RTL module interface digest (all manifest RTL files):
### rtl/dma_real_apb_cfg.sv
module dma_real_apb_cfg #(
    parameter integer ADDR_WIDTH  = 32,
    parameter integer DATA_WIDTH  = 32,
    parameter integer N_CHANNELS  = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // APB slave interface
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [11:0]           paddr,
    input  logic [DATA_WIDTH-1:0] pwdata,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    // Global control
    output logic                  dma_en,
    // Per-channel config outputs
    output logic [N_CHANNELS-1:0] ch_en,
    output logic [N_CHANNELS-1:0] ch_start_pulse,
    // Per-channel address/length config (individual wires)
    output logic [ADDR_WIDTH-1:0] cfg_src_addr_0, cfg_src_addr_1, cfg_src_addr_2, cfg_src_addr_3,
    output logic [ADDR_WIDTH-1:0] cfg_dst_addr_0, cfg_dst_addr_1, cfg_dst_addr_2, cfg_dst_addr_3,
    output logic [15:0]           cfg_len_0, cfg_len_1, cfg_len_2, cfg_len_3,
    // Per-channel status inputs (from channel FSM)
    input  logic [N_CHANNELS-1:0] ch_busy,
    input  logic [N_CHANNELS-1:0] ch_done,
    input  logic [N_CHANNELS-1:0] ch_error,
    input  logic [7:0]            ch_err_code,
    // NEW: IRQ-latched done/error for STATUS readback
    input  logic [N_CHANNELS-1:0] int_done,
    input  logic [N_CHANNELS-1:0] int_error,
    // IRQ module interface
    output logic [N_CHANNELS-1:0] int_enable_wr,
    output logic [N_CHANNELS-1:0] int_enable_wdata,
    output logic [N_CHANNELS-1:0] int_clear_wr,
    input  logic [N_CHANNELS-1:0] int_status,
    input  logic [N_CHANNELS-1:0] int_enable_rd
);

### rtl/dma_real_arbiter.sv
module dma_real_arbiter #(
    parameter integer N_CHANNELS = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // Channel requests
    input  logic [N_CHANNELS-1:0] ch_request,
    // Current grant
    output logic [2:0]            arb_grant,
    output logic [N_CHANNELS-1:0] ch_grant,
    // Bus status
    input  logic                  ahb_busy
);

### rtl/dma_real_channel.sv
module owns the sticky state.

module dma_real_channel #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer BURST_MAX  = 16,
    parameter integer FIFO_DEPTH = 8,
    parameter integer CH_ID      = 0
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // Configuration (from apb_cfg)
    input  logic                  ch_en,
    input  logic                  ch_start,
    input  logic                  dma_en,
    input  logic [ADDR_WIDTH-1:0] cfg_src_addr,
    input  logic [ADDR_WIDTH-1:0] cfg_dst_addr,
    input  logic [15:0]           cfg_len,
    // Arbiter interface
    output logic                  ch_request,
    input  logic                  ch_grant,
    // AHB master interface
    output logic                  ahb_start,
    output logic                  ahb_write,
    output logic [ADDR_WIDTH-1:0] ahb_addr,
    output logic [15:0]           ahb_len,
    input  logic                  ahb_done,
    input  logic                  ahb_error,
    input  logic [DATA_WIDTH-1:0] ahb_rdata,
    output logic [DATA_WIDTH-1:0] ahb_wdata,
    // Status outputs (1-cycle pulses to IRQ module)
    output logic                  status_busy,
    output logic                  status_done,
    output logic                  status_error,
    output logic [1:0]            status_err_code,
    // FIFO data
    output logic [DATA_WIDTH-1:0] fifo_wdata,
    output logic                  fifo_wen,
    input  logic [DATA_WIDTH-1:0] fifo_rdata,
    output logic                  fifo_ren,
    input  logic                  fifo_empty,
    input  logic                  fifo_full
);

module which latches sticky)
    logic done_pulse_q;
    logic error_pulse_q;

    // Status outputs
    assign status_busy     = (state_q != IDLE);

### rtl/dma_real_ahb_master.sv
module dma_real_ahb_master #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer BURST_MAX  = 16
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // Control from channel
    input  logic                  xfer_start,
    input  logic                  xfer_write,
    input  logic [ADDR_WIDTH-1:0] xfer_addr,
    input  logic [15:0]           xfer_len,
    output logic                  xfer_done,
    output logic                  xfer_error,
    // Data interface
    output logic [DATA_WIDTH-1:0] write_data,
    input  logic [DATA_WIDTH-1:0] read_data,
    // AHB-Lite master interface
    output logic [ADDR_WIDTH-1:0] haddr,
    output logic                  hwrite,
    output logic [1:0]            htrans,
    output logic [2:0]            hsize,
    output logic [2:0]            hburst,
    output logic [DATA_WIDTH-1:0] hwdata,
    input  logic [DATA_WIDTH-1:0] hrdata,
    input  logic                  hready,
    input  logic                  hresp,
    output logic                  hbusreq,
    input  logic                  hgrant
);

### rtl/dma_real_irq.sv
module dma_real_irq #(
    parameter integer N_CHANNELS = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // Per-channel done/error inputs from channel modules
    input  logic [N_CHANNELS-1:0] ch_done,
    input  logic [N_CHANNELS-1:0] ch_error,
    // APB register interface (from apb_cfg)
    input  logic [N_CHANNELS-1:0] int_enable_wr,
    input  logic [N_CHANNELS-1:0] int_enable_wdata,
    input  logic [N_CHANNELS-1:0] int_clear_wr,
    // Status readback
    output logic [N_CHANNELS-1:0] int_status,
    output logic [N_CHANNELS-1:0] int_enable_rd,
    // NEW: separate done/error for APB CHx_STATUS readback
    output logic [N_CHANNELS-1:0] int_done,
    output logic [N_CHANNELS-1:0] int_error,
    // IRQ outputs
    output logic [N_CHANNELS-1:0] irq,
    output logic                  irq_combined
);

### rtl/dma_real_engine.sv
<missing>

### rtl/dma_real_top.sv
module dma_real_top #(
    parameter integer ADDR_WIDTH  = 32,
    parameter integer DATA_WIDTH  = 32,
    parameter integer N_CHANNELS  = 4,
    parameter integer BURST_MAX   = 16,
    parameter integer FIFO_DEPTH  = 8
) (
    // Clock and reset
    input  logic                  pclk,
    input  logic                  presetn,
    // APB slave interface
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [11:0]           paddr,
    input  logic [DATA_WIDTH-1:0] pwdata,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    // AHB-Lite master interface
    output logic [ADDR_WIDTH-1:0] haddr,
    output logic                  hwrite,
    output logic [1:0]            htrans,
    output logic [2:0]            hsize,
    output logic [2:0]            hburst,
    output logic [DATA_WIDTH-1:0] hwdata,
    input  logic [DATA_WIDTH-1:0] hrdata,
    input  logic                  hready,
    input  logic                  hresp,
    output logic                  hbusreq,
    input  logic                  hgrant,
    // IRQ outputs
    output logic [N_CHANNELS-1:0] irq,
    output logic                  irq_combined,
    // DMA status (observable debug outputs)
    output logic [N_CHANNELS-1:0] ch_busy,
    output logic [N_CHANNELS-1:0] ch_done,
    output logic [N_CHANNELS-1:0] ch_error,
    output logic [7:0]            ch_err_code,
    output logic [2:0]            arb_grant
);

### rtl/dma_real_async_fifo.sv
<missing>

### rtl/dma_real_cdc_sync.sv
<missing>

### rtl/dma_real_cg_cell.sv
<missing>

Current mandatory lint repair directives:
<none>

Current RTL gate audit digest:
{
  "compile": {
    "diagnostics": null,
    "errors": 0,
    "passed": true,
    "present": true,
    "returncode": null,
    "source": "dma_real/rtl/rtl_compile.json",
    "style_violation_details": [],
    "style_violations": null
  },
  "gate": {
    "all_required_todos_pass": false,
    "audit_rtl": true,
    "blocking_questions": 0,
    "criteria": [
      "Gate: SSOT function_model and cycle_model are present before RTL generation",
      "Gate: SSOT-authored rtl-gen workflow TODOs are well formed",
      "Gate: every SSOT-derived RTL behavior has an owner module",
      "Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits",
      "Gate: required SSOT behavior has static DUT RTL evidence after audit",
      "Gate: behavior-owner RTL modules contain real implementation structure",
      "Gate: RTL sources contain no placeholder markers or disallowed generated-RTL constructs",
      "Gate: SSOT top IO contracts match the RTL top module",
      "Gate: SSOT top outputs are driven by real RTL logic",
      "Gate: SSOT top inputs are consumed by RTL logic or child inputs",
      "Gate: manifest-owned RTL modules are integrated into the top hierarchy",
      "Gate: manifest-owned child instances have machine-checkable port connections",
      "Gate: manifest child port connections carry live RTL signal flow",
      "Gate: SSOT connection contracts match RTL child port maps",
      "Gate: DUT-only RTL compile report passes after the final RTL edit",
      "Gate: DUT-only lint report passes after the final RTL edit",
      "Gate: every required rtl_todo_plan item is closed before rtl-gen PASS"
    ],
    "open_required_todos": 77,
    "orphan_tasks": 0,
    "static_missing": 64,
    "status": "fail"
  },
  "lint": {
    "diagnostics": [
      {
        "file": "dma_real/rtl/dma_real_top.sv",
        "line": 102,
        "message": "implicit conversion truncates from 20 to 8 bits",
        "severity": "warning"
      },
      {
        "file": "dma_real/rtl/dma_real_apb_cfg.sv",
        "line": 197,
        "message": "implicit conversion expands from 29 to 32 bits",
        "severity": "warning"
      },
      {
        "file": "dma_real/rtl/dma_real_apb_cfg.sv",
        "line": 209,
        "message": "implicit conversion expands from 29 to 32 bits",
        "severity": "warning"
      },
      {
        "file": "dma_real/rtl/dma_real_apb_cfg.sv",
        "line": 221,
        "message": "implicit conversion expands from 29 to 32 bits",
        "severity": "warning"
      },
      {
        "file": "dma_real/rtl/dma_real_apb_cfg.sv",
        "line": 233,
        "message": "implicit conversion expands from 29 to 32 bits",
        "severity": "warning"
      },
      {
        "file": "dma_real/rtl/dma_real_channel.sv",
        "line": 126,
        "message": "arithmetic between operands of different types ('logic[31:0]' and 'logic[15:0]')",
        "severity": "warning"
      },
      {
        "file": "dma_real/rtl/dma_real_channel.sv",
        "line": 131,
        "message": "arithmetic between operands of different types ('logic[31:0]' and 'logic[15:0]')",
        "severity": "warning"
      },
      {
        "column": 40,
        "file": "rtl/dma_real_top.sv",
        "line": 193,
        "message": "Instance pin connected by name with empty reference: 'ahb_wdata'",
        "rule": "PINCONNECTEMPTY",
        "severity": "warning",
        "source": "        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),"
      },
      {
        "column": 10,
        "file": "rtl/dma_real_top.sv",
        "line": 197,
        "message": "Instance pin connected by name with empty reference: 'fifo_rdata'",
        "rule": "PINCONNECTEMPTY",
        "severity": "warning",
        "source": "        .fifo_rdata(), .fifo_ren(fifo_ren_0),"
      },
      {
        "column": 40,
        "file": "rtl/dma_real_top.sv",
        "line": 238,
        "message": "Instance pin connected by name with empty reference: 'ahb_wdata'",
        "rule": "PINCONNECTEMPTY",
        "severity": "warning",
        "source": "        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),"
      },
      {
        "column": 10,
        "file": "rtl/dma_real_top.sv",
        "line": 242,
        "message": "Instance pin connected by name with empty reference: 'fifo_rdata'",
        "rule": "PINCONNECTEMPTY",
        "severity": "warning",
        "source": "        .fifo_rdata(), .fifo_ren(fifo_ren_1),"
      },
      {
        "column": 40,
        "file": "rtl/dma_real_top.sv",
        "line": 283,
        "message": "Instance pin connected by name with empty reference: 'ahb_wdata'",
        "rule": "PINCONNECTEMPTY",
        "severity": "warning",
        "source": "        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),"
      },
      {
        "column": 10,
        "file": "rtl/dma_real_top.sv",
        "line": 287,
        "message": "Instance pin connected by name with empty reference: 'fifo_rdata'",
        "rule": "PINCONNECTEMPTY",
        "severity": "warning",
        "source": "        .fifo_rdata(), .fifo_ren(fifo_ren_2),"
      },
      {
        "column": 40,
        "file": "rtl/dma_real_top.sv",
        "line": 328,
        "message": "Instance pin connected by name with empty reference: 'ahb_wdata'",
        "rule": "PINCONNECTEMPTY",
        "severity": "warning",
        "source": "        .ahb_rdata(ahb_master_rdata), .ahb_wdata(),"
      },
      {
        "column": 10,
        "file": "rtl/dma_real_top.sv",
        "line": 332,
        "message": "Instance pin connected by name with empty reference: 'fifo_rdata'",
        "rule": "PINCONNECTEMPTY",
        "severity": "warning",
        "source": "        .fifo_rdata(), .fifo_ren(fifo_ren_3),"
      }
    ],
    "errors": 0,
    "passed": true,
    "present": true,
    "repair_hints": [],
    "returncode": 1,
    "source": "dma_real/lint/dut_lint.json",
    "style_violation_count": 6,
    "suppression_violation_count": 0,
    "warnings": 15
  },
  "manifest_hierarchy_issues": [
    {
      "file": "rtl/dma_real_engine.sv",
      "issue": "SSOT manifest child module is not declared in listed RTL sources",
      "module": "dma_real_engine"
    }
  ],
  "manifest_signal_flow_issues": [
    {
      "expr": "mux_ahb_wdata",
      "instance": "u_ahb_master",
      "issue": "Manifest child output does not feed a top output, parent RTL logic, or another child input/inout",
      "module": "dma_real_ahb_master",
      "parent": "dma_real_top",
      "port": "write_data"
    }
  ],
  "open_required_tasks": [
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/dma_real_engine.sv",
      "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
      "task_id": "RTL-0006"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "64 static-evidence-required task(s) still lack DUT RTL evidence.",
      "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
      "task_id": "RTL-0007"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 owner logic structure issue(s) remain. dma_real_engine: Behavior-owner module is not declared in its owner file",
      "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
      "task_id": "RTL-0008"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "6 RTL placeholder/policy issue(s) remain. rtl/dma_real_apb_cfg.sv:81: for ( (RTL source uses a for loop); rtl/dma_real_apb_cfg.sv:96: for ( (RTL source uses a for loop); rtl/dma_real_apb_cfg.sv:117: for ( (RTL source uses a for loop)",
      "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
      "task_id": "RTL-0009"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "6 top IO contract issue(s) remain. hclk: SSOT top IO port is missing from RTL top declaration; hresetn: SSOT top IO port is missing from RTL top declaration; hprot: SSOT top IO port is missing from RTL top declaration",
      "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
      "task_id": "RTL-0010"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "2 top output drive issue(s) remain. ch_done: RTL top output has no nonconstant assignment or declared child-output drive evidence; ch_error: RTL top output has no nonconstant assignment or declared child-output drive evidence",
      "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
      "task_id": "RTL-0011"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 manifest hierarchy integration issue(s) remain. dma_real_engine: SSOT manifest child module is not declared in listed RTL sources",
      "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "task_id": "RTL-0013"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 manifest port connection issue(s) remain. dma_real_channel: Reachable child instance has missing or empty named port connections",
      "source_ref": "quality_gates.rtl_gen.manifest_port_connection_evidence",
      "task_id": "RTL-0014"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "1 manifest signal-flow issue(s) remain. dma_real_ahb_master: write_data: Manifest child output does not feed a top output, parent RTL logic, or another child input/inout",
      "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
      "task_id": "RTL-0015"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "DUT compile report does not list rtl_files for current filelist coverage.",
      "source_ref": "quality_gates.rtl_gen.dut_compile",
      "task_id": "RTL-0017"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "DUT lint artifact is not clean.",
      "source_ref": "quality_gates.rtl_gen.dut_lint",
      "task_id": "RTL-0018"
    },
    {
      "category": "rtl_gate.rtl_gen",
      "reason": "76 required non-closure TODO(s) remain open.",
      "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
      "task_id": "RTL-0019"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[0]",
      "task_id": "RTL-0020"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[1]",
      "task_id": "RTL-0021"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[2]",
      "task_id": "RTL-0022"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[3]",
      "task_id": "RTL-0023"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[4]",
      "task_id": "RTL-0024"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[5]",
      "task_id": "RTL-0025"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[6]",
      "task_id": "RTL-0026"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[7]",
      "task_id": "RTL-0027"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "workflow_todos.rtl-gen[8]",
      "task_id": "RTL-0028"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.state_variables.ch_error_q",
      "task_id": "RTL-0070"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.state_variables.ch_remaining_q",
      "task_id": "RTL-0071"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.state_variables.ch_stride_q",
      "task_id": "RTL-0074"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.state_variables.arb_ptr_q",
      "task_id": "RTL-0077"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.state_variables.timeout_q",
      "task_id": "RTL-0078"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.state_variables.perf_words_q",
      "task_id": "RTL-0079"
    },
    {
      "category": "function_model.state_variable",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.state_variables.perf_cycles_q",
      "task_id": "RTL-0080"
    },
    {
      "category": "function_model.output_rule",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "function_model.transactions.FM_DMA_ERROR.output_rules.error_assert",
      "task_id": "RTL-0138"
    },
    {
      "category": "cycle_model.handshake_rules",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "cycle_model.handshake_rules.apb_access",
      "task_id": "RTL-0167"
    },
    {
      "category": "cycle_model.handshake_rules",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "cycle_model.handshake_rules.cdc_config",
      "task_id": "RTL-0168"
    },
    {
      "category": "cycle_model.handshake_rules",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "cycle_model.handshake_rules.ahb_address_phase",
      "task_id": "RTL-0169"
    },
    {
      "category": "cycle_model.handshake_rules",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "cycle_model.handshake_rules.ahb_1kb_boundary",
      "task_id": "RTL-0171"
    },
    {
      "category": "cycle_model.handshake_rules",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "cycle_model.handshake_rules.ahb_error_response",
      "task_id": "RTL-0172"
    },
    {
      "category": "cycle_model.handshake_rules",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "cycle_model.handshake_rules.start_accept",
      "task_id": "RTL-0174"
    },
    {
      "category": "cycle_model.handshake_rules",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "cycle_model.handshake_rules.timeout_rule",
      "task_id": "RTL-0175"
    },
    {
      "category": "cycle_model.backpressure",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "cycle_model.backpressure.backpressure_rule_3",
      "task_id": "RTL-0192"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.GLOBAL_CTRL.fields.reserved_31_1",
      "task_id": "RTL-0196"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.GLOBAL_TIMEOUT.fields.timeout_val",
      "task_id": "RTL-0204"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.GLOBAL_TIMEOUT.fields.reserved_31_16",
      "task_id": "RTL-0205"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.CH0_CTRL.fields.hsize",
      "task_id": "RTL-0209"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.CH0_CTRL.fields.burst_mode",
      "task_id": "RTL-0210"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.CH0_CTRL.fields.reserved_31_6",
      "task_id": "RTL-0211"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.CH0_LEN.fields.length",
      "task_id": "RTL-0217"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.CH0_LEN.fields.reserved_31_16",
      "task_id": "RTL-0218"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.CH0_STATUS.fields.reserved_31_6",
      "task_id": "RTL-0224"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.CH0_PERF_WORDS.fields.word_count",
      "task_id": "RTL-0228"
    },
    {
      "category": "registers.field",
      "reason": "Required RTL static evidence is missing.",
      "source_ref": "registers.register_list.CH0_PERF_CYCLES.fields.cycle_count",
      "task_id": "RTL-0230"
    }
  ],
  "source": "dma_real/rtl/rtl_todo_plan.json",
  "static_missing_tasks": [
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_top.sv",
      "required_match_count": 3,
      "required_terms": [
        "cdc",
        "cdc_requirements",
        "io",
        "io_list",
        "list",
        "modules",
        "requirements",
        "sub"
      ],
      "source_ref": "workflow_todos.rtl-gen[0]",
      "source_scope": "rtl/dma_real_top.sv",
      "task_id": "RTL-0020"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 1,
      "matched_terms": [
        "apb"
      ],
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "required_match_count": 3,
      "required_terms": [
        "apb",
        "apb_slave",
        "cdc",
        "cdc_requirements",
        "io",
        "io_list",
        "list",
        "requirements"
      ],
      "source_ref": "workflow_todos.rtl-gen[1]",
      "source_scope": "rtl/dma_real_apb_cfg.sv",
      "task_id": "RTL-0021"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 2,
      "matched_terms": [
        "ARB",
        "GRANT"
      ],
      "owner_file": "rtl/dma_real_arbiter.sv",
      "required_match_count": 3,
      "required_terms": [
        "ARB",
        "FM",
        "FM_ARB_GRANT",
        "GRANT"
      ],
      "source_ref": "workflow_todos.rtl-gen[2]",
      "source_scope": "rtl/dma_real_arbiter.sv",
      "task_id": "RTL-0022"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 1,
      "matched_terms": [
        "channel"
      ],
      "owner_file": "rtl/dma_real_channel.sv",
      "required_match_count": 3,
      "required_terms": [
        "channel",
        "error_handling",
        "handling",
        "per",
        "per_channel"
      ],
      "source_ref": "workflow_todos.rtl-gen[3]",
      "source_scope": "rtl/dma_real_channel.sv",
      "task_id": "RTL-0023"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 1,
      "matched_terms": [
        "ahb"
      ],
      "owner_file": "rtl/dma_real_arbiter.sv",
      "required_match_count": 3,
      "required_terms": [
        "ahb",
        "ahb_master",
        "io",
        "io_list",
        "list",
        "master"
      ],
      "source_ref": "workflow_todos.rtl-gen[4]",
      "source_scope": "rtl/dma_real_arbiter.sv",
      "task_id": "RTL-0024"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 1,
      "matched_terms": [
        "irq"
      ],
      "owner_file": "rtl/dma_real_irq.sv",
      "required_match_count": 3,
      "required_terms": [
        "cdc",
        "cdc_requirements",
        "io",
        "io_list",
        "irq",
        "irq_outputs",
        "list",
        "requirements"
      ],
      "source_ref": "workflow_todos.rtl-gen[5]",
      "source_scope": "rtl/dma_real_irq.sv",
      "task_id": "RTL-0025"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_top.sv",
      "required_match_count": 3,
      "required_terms": [
        "cdc",
        "cdc_requirements",
        "requirements"
      ],
      "source_ref": "workflow_todos.rtl-gen[6]",
      "source_scope": "rtl/dma_real_top.sv",
      "task_id": "RTL-0026"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_top.sv",
      "required_match_count": 3,
      "required_terms": [
        "cdc",
        "cdc_requirements",
        "requirements"
      ],
      "source_ref": "workflow_todos.rtl-gen[7]",
      "source_scope": "rtl/dma_real_top.sv",
      "task_id": "RTL-0027"
    },
    {
      "category": "workflow_todo.rtl_gen",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_channel.sv",
      "required_match_count": 3,
      "required_terms": [
        "modules",
        "sub",
        "sub_modules"
      ],
      "source_ref": "workflow_todos.rtl-gen[8]",
      "source_scope": "rtl/dma_real_channel.sv",
      "task_id": "RTL-0028"
    },
    {
      "category": "function_model.state_variable",
      "matched_count": 1,
      "matched_terms": [
        "ch"
      ],
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "required_match_count": 2,
      "required_terms": [
        "ch",
        "ch_error_q"
      ],
      "source_ref": "function_model.state_variables.ch_error_q",
      "source_scope": "rtl/dma_real_apb_cfg.sv",
      "task_id": "RTL-0070"
    },
    {
      "category": "function_model.state_variable",
      "matched_count": 1,
      "matched_terms": [
        "ch"
      ],
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "required_match_count": 2,
      "required_terms": [
        "ch",
        "ch_remaining_q",
        "remaining"
      ],
      "source_ref": "function_model.state_variables.ch_remaining_q",
      "source_scope": "rtl/dma_real_apb_cfg.sv",
      "task_id": "RTL-0071"
    },
    {
      "category": "function_model.state_variable",
      "matched_count": 1,
      "matched_terms": [
        "ch"
      ],
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "required_match_count": 2,
      "required_terms": [
        "ch",
        "ch_stride_q",
        "stride"
      ],
      "source_ref": "function_model.state_variables.ch_stride_q",
      "source_scope": "rtl/dma_real_apb_cfg.sv",
      "task_id": "RTL-0074"
    },
    {
      "category": "function_model.state_variable",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "required_match_count": 2,
      "required_terms": [
        "arb",
        "arb_ptr_q",
        "ptr"
      ],
      "source_ref": "function_model.state_variables.arb_ptr_q",
      "source_scope": "rtl/dma_real_apb_cfg.sv",
      "task_id": "RTL-0077"
    },
    {
      "category": "function_model.state_variable",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "required_match_count": 2,
      "required_terms": [
        "timeout",
        "timeout_q"
      ],
      "source_ref": "function_model.state_variables.timeout_q",
      "source_scope": "rtl/dma_real_apb_cfg.sv",
      "task_id": "RTL-0078"
    },
    {
      "category": "function_model.state_variable",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "required_match_count": 2,
      "required_terms": [
        "perf",
        "perf_words_q",
        "words"
      ],
      "source_ref": "function_model.state_variables.perf_words_q",
      "source_scope": "rtl/dma_real_apb_cfg.sv",
      "task_id": "RTL-0079"
    },
    {
      "category": "function_model.state_variable",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_apb_cfg.sv",
      "required_match_count": 2,
      "required_terms": [
        "cycles",
        "perf",
        "perf_cycles_q"
      ],
      "source_ref": "function_model.state_variables.perf_cycles_q",
      "source_scope": "rtl/dma_real_apb_cfg.sv",
      "task_id": "RTL-0080"
    },
    {
      "category": "function_model.output_rule",
      "matched_count": 1,
      "matched_terms": [
        "ch"
      ],
      "owner_file": "rtl/dma_real_channel.sv",
      "required_match_count": 2,
      "required_terms": [
        "assert",
        "ch",
        "ch_error",
        "error_assert"
      ],
      "source_ref": "function_model.transactions.FM_DMA_ERROR.output_rules.error_assert",
      "source_scope": "rtl/dma_real_channel.sv",
      "task_id": "RTL-0138"
    },
    {
      "category": "cycle_model.handshake_rules",
      "matched_count": 0,
      "matched_terms": [],
      "owner_file": "rtl/dma_real_arbiter.sv",
      "required_match_count": 2,
      "required_terms": [
        "apb",
        "apb_access"
      ],
      "source_ref": "cycle_model.handshake_rules.apb_access",
      "source_scope": "rtl/dma_real_arbiter.sv",
      "task_id": "RTL-0167"
    },
    {
      "category": "cycle_model.handshake_rules",
      "matched_count": 0,
      "matched_terms": [],
      "owner_fil
... <truncated 12585 chars>

Current RTL file snapshots for gate/tool-evidence repair:
<included only for gate/tool-evidence packets>

Current tool evidence artifacts referenced by this packet:
<none>

Current packet JSON (rtl/authoring_packets/module__dma_real_engine.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
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
      "module_task_count": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/dma_real_engine.sv",
      "name": "dma_real_engine",
      "refs": [
        "cycle_model",
        "cycle_model.pipeline",
        "fsm",
        "function_model",
        "function_model.transactions.FM_DMA_STEP"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/dma_real_apb_cfg.sv",
        "name": "dma_real_apb_cfg",
        "wiring_only": false
      },
      {
        "file": "rtl/dma_real_arbiter.sv",
        "name": "dma_real_arbiter",
        "wiring_only": false
      },
      {
        "file": "rtl/dma_real_channel.sv",
        "name": "dma_real_channel",
        "wiring_only": false
      },
      {
        "file": "rtl/dma_real_ahb_master.sv",
        "name": "dma_real_ahb_master",
        "wiring_only": false
      },
      {
        "file": "rtl/dma_real_irq.sv",
        "name": "dma_real_irq",
        "wiring_only": false
      },
      {
        "file": "rtl/dma_real_engine.sv",
        "name": "dma_real_engine",
        "wiring_only": false
      },
      {
        "file": "rtl/dma_real_top.sv",
        "name": "dma_real_top",
        "wiring_only": false
      }
    ],
    "quality_profile": "standard",
    "reference_profile": null,
    "ssot_connection_contracts": [],
    "ssot_top_io_contracts": [],
    "target_scale": null
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
    "llm_actionable_open_count": 1,
    "open_required_count": 1,
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
  "ip": "dma_real",
  "kind": "module",
  "owner_file": "rtl/dma_real_engine.sv",
  "owner_module": "dma_real_engine",
  "packet_id": "module__dma_real_engine",
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
      "equivalence.module": 1
    },
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 1,
      "task_limit": 48
    },
    "open_required_count": 1,
    "required_count": 1,
    "source_refs": [
      "sub_modules.dma_real_engine.module_equivalence"
    ],
    "status_counts": {
      "open": 1
    },
    "task_count": 1
  },
  "tasks": [
    {
      "category": "equivalence.module",
      "content": "Prove module dma_real_engine is functionally equivalent to FL",
      "criteria": [
        "verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module",
        "cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff",
        "scoreboard row fl_expected.model_api is FunctionalModel.apply",
        "scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data",
        "Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong",
        "Traceability keeps source_ref sub_modules.dma_real_engine.module_equivalence",
        "Primary implementation evidence is in rtl/dma_real_engine.sv"
      ],
      "detail": "This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.\nSSOT ref: sub_modules.dma_real_engine.module_equivalence.\nOwner: dma_real_engine in rtl/dma_real_engine.sv via module_equivalence.",
      "evidence_terms": [],
      "id": "RTL-0381",
      "owner_file": "rtl/dma_real_engine.sv",
      "owner_module": "dma_real_engine",
      "priority": "high",
      "required": true,
      "source_ref": "sub_modules.dma_real_engine.module_equivalence",
      "ssot_context": {},
      "ssot_refs": [
        "sub_modules.dma_real_engine.module_equivalence"
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
        "reason": "Owner RTL file is missing: rtl/dma_real_engine.sv.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "08a17cccf5914d45200fe4745d1e515b35dfeed4fddb483eb6daaabc71eaacf3",
  "top": "dma_real_top",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__dma_real_engine.md):
# RTL Authoring Packet: module__dma_real_engine

- Kind: module
- Owner module: dma_real_engine
- Owner file: rtl/dma_real_engine.sv
- Task count: 1
- Required tasks: 1

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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, fsm, function_model, function_model.transactions.FM_DMA_STEP

## Tasks

### RTL-0381: Prove module dma_real_engine is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.dma_real_engine.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.dma_real_engine.module_equivalence.
Owner: dma_real_engine in rtl/dma_real_engine.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/dma_real_engine.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.dma_real_engine.module_equivalence
  - Primary implementation evidence is in rtl/dma_real_engine.sv
- SSOT refs: sub_modules.dma_real_engine.module_equivalence
