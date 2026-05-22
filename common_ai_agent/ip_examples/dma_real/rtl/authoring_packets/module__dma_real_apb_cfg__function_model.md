# RTL Authoring Packet: module__dma_real_apb_cfg__function_model

- Kind: module
- Owner module: dma_real_apb_cfg
- Owner file: rtl/dma_real_apb_cfg.sv
- Task count: 13
- Required tasks: 13

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
- LLM-actionable open tasks: 7
- Human-locked open tasks: 0
- Owner refs: dataflow.ordering.ordering_0, dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, function_model.state_variables, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 2/8 section=function_model task_limit=48
- Slice rule: Owner module dma_real_apb_cfg is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0068: Implement RTL state owner for FL state ch_busy_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ch_busy_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ch_busy_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=ch_busy_q; width=N_CHANNELS; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ch_busy_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_busy_q width matches SSOT value N_CHANNELS
  - ch_busy_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ch_busy_q

### RTL-0069: Implement RTL state owner for FL state ch_done_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ch_done_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ch_done_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=ch_done_q; width=N_CHANNELS; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ch_done_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_done_q width matches SSOT value N_CHANNELS
  - ch_done_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ch_done_q

### RTL-0070: Implement RTL state owner for FL state ch_error_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ch_error_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ch_error_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=ch_error_q; width=N_CHANNELS; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ch_error_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_error_q width matches SSOT value N_CHANNELS
  - ch_error_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ch_error_q

### RTL-0071: Implement RTL state owner for FL state ch_remaining_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ch_remaining_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ch_remaining_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=ch_remaining_q; width=32; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ch_remaining_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_remaining_q width matches SSOT value 32
  - ch_remaining_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ch_remaining_q

### RTL-0072: Implement RTL state owner for FL state ch_src_addr_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ch_src_addr_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ch_src_addr_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=ch_src_addr_q; width=ADDR_WIDTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ch_src_addr_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_src_addr_q width matches SSOT value ADDR_WIDTH
  - ch_src_addr_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ch_src_addr_q

### RTL-0073: Implement RTL state owner for FL state ch_dst_addr_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ch_dst_addr_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ch_dst_addr_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=ch_dst_addr_q; width=ADDR_WIDTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ch_dst_addr_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_dst_addr_q width matches SSOT value ADDR_WIDTH
  - ch_dst_addr_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ch_dst_addr_q

### RTL-0074: Implement RTL state owner for FL state ch_stride_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ch_stride_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ch_stride_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=ch_stride_q; width=ADDR_WIDTH; reset=4.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ch_stride_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_stride_q width matches SSOT value ADDR_WIDTH
  - ch_stride_q reset behavior matches SSOT value 4
- SSOT refs: function_model.state_variables.ch_stride_q

### RTL-0075: Implement RTL state owner for FL state dma_en_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.dma_en_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.dma_en_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=dma_en_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.dma_en_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - dma_en_q width matches SSOT value 1
  - dma_en_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.dma_en_q

### RTL-0076: Implement RTL state owner for FL state int_enable_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.int_enable_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.int_enable_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=int_enable_q; width=N_CHANNELS; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.int_enable_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - int_enable_q width matches SSOT value N_CHANNELS
  - int_enable_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.int_enable_q

### RTL-0077: Implement RTL state owner for FL state arb_ptr_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.arb_ptr_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.arb_ptr_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=arb_ptr_q; width=3; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.arb_ptr_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - arb_ptr_q width matches SSOT value 3
  - arb_ptr_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.arb_ptr_q

### RTL-0078: Implement RTL state owner for FL state timeout_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.timeout_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.timeout_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=timeout_q; width=16; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.timeout_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - timeout_q width matches SSOT value 16
  - timeout_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.timeout_q

### RTL-0079: Implement RTL state owner for FL state perf_words_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.perf_words_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.perf_words_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=perf_words_q; width=32; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.perf_words_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - perf_words_q width matches SSOT value 32
  - perf_words_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.perf_words_q

### RTL-0080: Implement RTL state owner for FL state perf_cycles_q

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.perf_cycles_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.perf_cycles_q.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via function_model.state_variables.
SSOT item context: name=perf_cycles_q; width=32; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.perf_cycles_q
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - perf_cycles_q width matches SSOT value 32
  - perf_cycles_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.perf_cycles_q
