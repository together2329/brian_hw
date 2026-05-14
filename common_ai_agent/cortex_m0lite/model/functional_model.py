#!/usr/bin/env python3
"""Executable SSOT functional model for cortex_m0lite.

Generated from yaml/cortex_m0lite.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'cortex_m0lite', 'parameters': {'XLEN': 32, 'RESET_PC': 0, 'TRAP_VECTOR': 128, 'STACK_RESET': 0, 'REG_COUNT': 16, 'AHB_ADDR_W': 32, 'AHB_DATA_W': 32, 'CORE_FREQ_MHZ': 300, 'BUS_FREQ_MHZ': 150, 'AHB_HTRANS_IDLE': 0, 'AHB_HTRANS_BUSY': 1, 'AHB_HTRANS_NONSEQ': 2, 'AHB_HTRANS_SEQ': 3, 'AHB_HSIZE_WORD': 2, 'AHB_HBURST_SINGLE': 0}, 'top_module': {'name': 'cortex_m0lite', 'file': 'rtl/cortex_m0lite.sv', 'version': '1.0', 'type': 'cpu', 'reference_spec': 'user-defined Cortex-M0-lite subset SSOT', 'description': 'Cortex-M0-lite style 3-stage microcontroller core (IF/ID/EX-WB) with AHB-Lite instruction/data master ports.', 'owner': 'ssot-manual', 'quality_profile': 'strict', 'target': {'technology': 'sky130', 'clock_freq_mhz': 300, 'bus_freq_mhz': 150, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'regfile_storage', 'type': 'register_array', 'depth': 'REG_COUNT', 'width': 'XLEN', 'owner': 'regfile', 'reset': 'implementation_defined_zero_or_retained_by_architectural_rule'}], 'external_memories': [{'name': 'instruction_memory', 'interface': 'instr_ahb_m', 'ownership': 'external'}, {'name': 'data_memory', 'interface': 'data_ahb_m', 'ownership': 'external'}]}, 'registers': {'address_unit': 'byte', 'data_width': 'XLEN', 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'access_model': 'Internal architectural/debug register map; this revision has no external CSR slave port.', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields must be tied to zero on readback and must not create storage.'}, 'register_file': {'owner': 'regfile', 'physical_storage': 'rf_mem[0:14]', 'pc_alias': 'Architectural R15 reads pc_q; R15 is not a writable physical rf_mem entry.', 'retention_policy': 'none', 'reset_policy': ['R0-R12 reset to 0 on core_rst_n_sync assertion.', 'R13/SP resets to STACK_RESET.', 'R14/LR resets to 0.', 'R15/PC resets through pc_q to RESET_PC.'], 'write_policy': ['Only non-trapped committing ALU/MOV/LDR instructions may assert wb_rf_we.', 'Writes to R0-R14 update rf_mem on the commit edge.', 'Writes targeting R15 are not supported by this subset and must raise illegal opcode trap_code=1.', 'Trap entry suppresses rf_mem writes for the offending instruction.'], 'read_policy': ['Reads of R0-R14 return rf_mem.', 'Reads of R15 return aligned architectural PC view with bit[0]=0.']}, 'register_list': [{'name': 'XPSR', 'offset': 0, 'width': 'XLEN', 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'owner': 'wb_stage', 'description': 'Architectural condition flags visible for debug/scoreboard.', 'write_side_effects': ['ADD/SUB/CMP update N/Z/C/V according to function_model.flag_formulas.', 'AND/ORR/EOR/MOV update N/Z only and preserve C/V.', 'Trap entry does not update XPSR for the offending instruction.'], 'fields': [{'name': 'n', 'bits': [31, 31], 'lsb': 31, 'width': 1, 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'description': 'Negative flag; mirrors nzcv_q[3].'}, {'name': 'z', 'bits': [30, 30], 'lsb': 30, 'width': 1, 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'description': 'Zero flag; mirrors nzcv_q[2].'}, {'name': 'c', 'bits': [29, 29], 'lsb': 29, 'width': 1, 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'description': 'Carry/not-borrow flag; mirrors nzcv_q[1].'}, {'name': 'v', 'bits': [28, 28], 'lsb': 28, 'width': 1, 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'description': 'Signed overflow flag; mirrors nzcv_q[0].'}, {'name': 'reserved_27_0', 'bits': [27, 0], 'lsb': 0, 'width': 28, 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'PC', 'offset': 4, 'width': 'XLEN', 'access': 'ro', 'hw_access': 'rw', 'reset': 'RESET_PC', 'owner': 'if_stage', 'description': 'Architectural program counter debug view.', 'write_side_effects': ['Normal sequential commit sets pc_q to pc_q+2.', 'Taken branch sets pc_q to branch target and flushes IF/ID.', 'Trap entry captures EXC_EPC then sets pc_q to TRAP_VECTOR.', 'Exception return is not architecturally supported in this revision; reset is the only trap recovery path.'], 'fields': [{'name': 'pc', 'bits': [31, 0], 'lsb': 0, 'width': 'XLEN', 'parameter_ref': 'XLEN', 'access': 'ro', 'hw_access': 'rw', 'reset': 'RESET_PC', 'alignment': 2, 'description': 'Aligned architectural PC; bit[0] is always 0.'}]}, {'name': 'EXC_CAUSE', 'offset': 8, 'width': 'XLEN', 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'owner': 'wb_stage', 'description': 'Precise trap cause metadata captured at trap entry.', 'write_side_effects': ['trap_valid sets in the same commit boundary that suppresses retire.', 'trap_code stores highest-priority error_handling.priority code.', 'trap_stage stores the pipeline stage that detected the fault.', 'Fields clear on reset only; exception return is reserved for a future SSOT revision.'], 'fields': [{'name': 'trap_valid', 'bits': [0, 0], 'lsb': 0, 'width': 1, 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'set_by': 'trap_enter', 'clear_by': ['reset'], 'description': 'Sticky trap valid until reset.'}, {'name': 'trap_code', 'bits': [7, 1], 'lsb': 1, 'width': 7, 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'enum': {'illegal_opcode': 1, 'bus_error': 2, 'misaligned_word_access': 3}, 'description': 'Trap reason code.'}, {'name': 'trap_stage', 'bits': [10, 8], 'lsb': 8, 'width': 3, 'access': 'ro', 'hw_access': 'rw', 'reset': 0, 'enum': {'if_stage': 1, 'id_stage': 2, 'ex_stage': 3, 'wb_stage': 4}, 'description': 'Stage that raised the precise trap.'}, {'name': 'reserved_31_11', 'bits': [31, 11], 'lsb': 11, 'width': 21, 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero.'}]}, {'name': 'EXC_EPC', 'offset': 12, 'width': 'XLEN', 'access': 'ro', 'hw_access': 'rw', 'reset': 'RESET_PC', 'owner': 'wb_stage', 'description': 'Exception program counter captured from the offending instruction PC.', 'write_side_effects': ['On trap entry, captures fault_pc before pc_q redirects to TRAP_VECTOR.', 'Bit[0] is forced to 0 because this core executes aligned 16-bit instructions.'], 'fields': [{'name': 'epc', 'bits': [31, 0], 'lsb': 0, 'width': 'XLEN', 'parameter_ref': 'XLEN', 'access': 'ro', 'hw_access': 'rw', 'reset': 'RESET_PC', 'alignment': 2, 'description': 'Faulting instruction PC.'}]}]}, 'function_model': {'purpose': 'Architectural CPU reference for RTL equivalence and scoreboard.', 'state_variables': [{'name': 'pc_q', 'width': 'XLEN', 'reset': 'RESET_PC', 'description': 'Architectural program counter.'}, {'name': 'rf_q', 'width': 32, 'reset': 0, 'description': 'R0-R15 register array abstraction.'}, {'name': 'nzcv_q', 'width': 4, 'reset': 0, 'description': 'Condition flags N,Z,C,V.'}, {'name': 'trap_q', 'width': 1, 'reset': 0, 'description': 'Trap sticky state until handler vectoring.'}], 'transactions': [{'id': 'FM_CPU_STEP', 'name': 'cpu_cycle_step', 'required_fields': ['instr_word', 'instr_valid', 'i_hready', 'd_hready', 'd_hrdata', 'irq'], 'preconditions': ['core_rst_n_sync and bus_rst_n_sync are deasserted.', 'instr_valid indicates a 16-bit instruction word is available from the IF path.', 'Any data access waits for the declared AHB-Lite ready/response contract.'], 'outputs': ['pc_dbg', 'retire', 'trap'], 'decode_rules': ['Decode instr_word into opcode/rd/rn/rm/imm fields per isa_spec.', 'If decode miss occurs, set trap_code=1 and suppress retire.', 'If decode class overlap occurs, resolve by decode_contract class priority and emit overlap telemetry.'], 'memory_rules': ['LDR retires only when d_hready=1 and d_hresp=0.', 'STR retires only when d_hready=1 and d_hresp=0.', 'Any d_hresp=1 raises trap_code=2.', 'Word misalignment on LDR/STR raises trap_code=3 before bus launch.'], 'branch_rules': ['Taken branch flushes IF/ID and redirects pc_q to target.', 'Not-taken branch advances to sequential pc.'], 'operand_rules': ['ADD/SUB write rd when the decoded instruction form contains an rd destination; CMP updates flags only and never writes rd. Operand source selection between rm and imm is controlled by decode_rule_set.', 'MOV writes rd from source operand and updates N/Z only.', 'LDR writes rd on successful bus response only.', 'STR has no register writeback.'], 'flag_formulas': ['N := result[XLEN-1]', 'Z := (result == 0)', 'C := carry_out for ADD, not_borrow for SUB/CMP, unchanged for logical ops unless explicitly defined', 'V := signed overflow for ADD/SUB/CMP, unchanged for logical ops unless explicitly defined'], 'output_rules': [{'name': 'retire_pulse', 'port': 'retire', 'width': 1, 'expr': '1 when one instruction commits without trap, else 0'}, {'name': 'trap_flag', 'port': 'trap', 'width': 1, 'expr': '1 when illegal opcode, bus error, or misalignment is detected at commit boundary'}], 'state_updates': [{'name': 'pc_q', 'width': 'XLEN', 'reset': 'RESET_PC', 'expr': 'pc+2 on normal flow; branch target on taken branch; trap vector on exception'}, {'name': 'rf_q', 'width': 32, 'reset': 0, 'expr': 'register writeback on ALU/LDR/MOV commit only'}, {'name': 'nzcv_q', 'width': 4, 'reset': 0, 'expr': 'updated by arithmetic/compare instructions per ARM-like semantics'}], 'error_cases': ['Illegal instruction encoding -> trap_code=1', 'Instruction/data bus error (HRESP=1) -> trap_code=2', 'Misaligned word access -> trap_code=3'], 'side_effects': ['Successful ALU/MOV/LDR instructions update the destination architectural register at commit.', 'Arithmetic and compare instructions update NZCV according to flag_formulas.', 'Taken branches redirect pc_q and flush IF/ID before the next fetch.', 'Trap conditions suppress retire of the offending instruction and update exception metadata only.']}], 'invariants': ['R15 reflects architectural PC view at commit.', 'No architectural state update on trapped instruction except exception metadata.', 'At most one retire pulse per cycle.', 'x0-like behavior is not used; all R0-R15 are normal ARM-style architectural registers.', 'No instruction commits while trap_q is active until trap vectoring completes.']}, 'cycle_model': {'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 cycle shell; keep FunctionModel as golden architecture model.', 'clock': 'clk', 'reset': 'rst_n', 'latency': 3, 'pipeline': [{'stage': 'IF', 'cycle': 0, 'action': 'Fetch request/acceptance.'}, {'stage': 'ID', 'cycle': 1, 'action': 'Decode + regfile read + hazard decision.'}, {'stage': 'EX_WB', 'cycle': 2, 'action': 'Execute/memory response/writeback/retire.'}], 'handshake_rules': [{'name': 'if_wait', 'description': 'IF holds request when i_hready=0.'}, {'name': 'dmem_wait', 'description': 'Load/store completion waits for d_hready=1.'}, {'name': 'hazard_stall', 'description': 'Load-use dependency inserts one bubble.'}], 'ordering': ['Reset dominates all pipeline movement and clears valid bits before instruction retirement.', 'Trap entry has priority over branch redirect, writeback, and normal sequential PC update.', 'Branch taken flushes IF/ID before the redirected fetch becomes visible.', 'Load/store bus completion gates retire; no LDR/STR commits before d_hready && !d_hresp.', 'core_clk:bus_clk is a synchronous 2:1 relationship; bus boundary logic samples requests only on aligned bus_clk cycles.'], 'performance': {'target_fmax_mhz': 300, 'bus_fmax_mhz': 150, 'clock_ratio_core_to_bus': '2:1', 'target_cpi_typical': 1.2, 'outstanding_depth': {'instruction': 1, 'data': 1}}}, 'fcov_bins': [{'id': 'SC_RESET_FETCH_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_RESET_FETCH', 'description': 'Reset vector fetch'}, {'id': 'SC_ALU_FLAGS_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_ALU_FLAGS', 'description': 'ALU operation and NZCV update'}, {'id': 'SC_BRANCH_FLUSH_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_BRANCH_FLUSH', 'description': 'Conditional branch flush'}, {'id': 'SC_LOAD_STORE_AHB_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_LOAD_STORE_AHB', 'description': 'Load/store AHB access'}, {'id': 'SC_TRAP_PATHS_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_TRAP_PATHS', 'description': 'Trap and precise exception paths'}, {'id': 'SC_HAZARD_FORWARD_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_HAZARD_FORWARD', 'description': 'RAW hazard and forwarding'}, {'id': 'alu_ops_all', 'class': 'instruction_class', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_CPU_STEP.operand_rules', 'source_ref': 'function_model.transactions.FM_CPU_STEP.operand_rules', 'description': 'All ALU/MOV/CMP operation families execute and match architectural writeback/flag behavior.'}, {'id': 'alu_flag_update_matrix', 'class': 'flag_behavior', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_CPU_STEP.flag_formulas', 'source_ref': 'function_model.transactions.FM_CPU_STEP.flag_formulas', 'description': 'N/Z/C/V formulas are observed for arithmetic, compare, logical, and move cases.'}, {'id': 'branch_taken_not_taken', 'class': 'control_flow', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_CPU_STEP.branch_rules', 'source_ref': 'function_model.transactions.FM_CPU_STEP.branch_rules', 'description': 'Taken and not-taken branch paths update PC and flush behavior as specified.'}, {'id': 'load_store_word', 'class': 'memory_behavior', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_CPU_STEP.memory_rules', 'source_ref': 'function_model.transactions.FM_CPU_STEP.memory_rules', 'description': 'Aligned LDR/STR word behavior updates registers or memory side effects correctly.'}, {'id': 'trap_illegal_opcode', 'class': 'trap', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_CPU_STEP.error_cases', 'source_ref': 'function_model.transactions.FM_CPU_STEP.error_cases', 'description': 'Illegal decode raises trap_code=1 and suppresses retire.'}, {'id': 'trap_bus_error', 'class': 'trap', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_CPU_STEP.error_cases', 'source_ref': 'function_model.transactions.FM_CPU_STEP.error_cases', 'description': 'Instruction/data HRESP error raises trap_code=2 and suppresses retire.'}, {'id': 'trap_misaligned', 'class': 'trap', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_CPU_STEP.error_cases', 'source_ref': 'function_model.transactions.FM_CPU_STEP.error_cases', 'description': 'Misaligned word access raises trap_code=3 before data bus launch.'}, {'id': 'pipeline_state_occupancy', 'class': 'pipeline', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': 'IF, ID, and EX/WB pipeline stages all become active under directed tests.'}, {'id': 'if_wait_cycles', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.if_wait', 'source_ref': 'cycle_model.handshake_rules.if_wait', 'description': 'Instruction fetch wait-state hold behavior is observed.'}, {'id': 'dmem_wait_cycles', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.dmem_wait', 'source_ref': 'cycle_model.handshake_rules.dmem_wait', 'description': 'Data memory wait-state hold behavior is observed.'}, {'id': 'hazard_stall_cycles', 'class': 'hazard', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.hazard_stall', 'source_ref': 'cycle_model.handshake_rules.hazard_stall', 'description': 'Load-use one-bubble stall behavior is observed.'}, {'id': 'branch_flush_cycles', 'class': 'flush', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering', 'source_ref': 'cycle_model.ordering', 'description': 'Taken branch flush timing is observed.'}, {'id': 'trap_entry_cycles', 'class': 'trap_timing', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions', 'source_ref': 'fsm.control.transitions', 'description': 'Trap-entry FSM transition and flush timing are observed.'}, {'id': 'outstanding_instruction_depth', 'class': 'outstanding', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding_depth.instruction', 'source_ref': 'cycle_model.performance.outstanding_depth.instruction', 'description': 'Instruction side single-outstanding request limit is exercised.'}, {'id': 'outstanding_data_depth', 'class': 'outstanding', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding_depth.data', 'source_ref': 'cycle_model.performance.outstanding_depth.data', 'description': 'Data side single-outstanding request limit is exercised.'}, {'id': 'cpi_nominal_stream', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.target_cpi_typical', 'source_ref': 'cycle_model.performance.target_cpi_typical', 'description': 'Nominal instruction stream CPI target is measured or explicitly waived.'}, {'id': 'core_bus_frequency_ratio', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.clock_ratio_core_to_bus', 'source_ref': 'cycle_model.performance.clock_ratio_core_to_bus', 'description': '2:1 core_clk to bus_clk cycle relationship is represented in coverage evidence.'}, {'id': 'function_cpu_cycle_step', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_cpu_step', 'description': 'cpu_cycle_step'}, {'id': 'cycle_if_wait', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': 'IF holds request when i_hready=0.'}, {'id': 'cycle_dmem_wait', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': 'Load/store completion waits for d_hready=1.'}, {'id': 'cycle_hazard_stall', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': 'Load-use dependency inserts one bubble.'}, {'id': 'cycle_pipeline_if', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Fetch request/acceptance.'}, {'id': 'cycle_pipeline_id', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Decode + regfile read + hazard decision.'}, {'id': 'cycle_pipeline_ex_wb', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Execute/memory response/writeback/retire.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Reset dominates all pipeline movement and clears valid bits before instruction retirement.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Trap entry has priority over branch redirect, writeback, and normal sequential PC update.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Branch taken flushes IF/ID before the redirected fetch becomes visible.'}, {'id': 'cycle_ordering_3', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[3]', 'source_ref': 'cycle_model.ordering[3]', 'description': 'Load/store bus completion gates retire; no LDR/STR commits before d_hready && !d_hresp.'}, {'id': 'cycle_ordering_4', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[4]', 'source_ref': 'cycle_model.ordering[4]', 'description': 'core_clk:bus_clk is a synchronous 2:1 relationship; bus boundary logic samples requests only on aligned bus_clk cycles.'}, {'id': 'error_illegal_opcode', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'name': 'illegal_opcode', 'condition': 'decode miss or unsupported instruction class', 'architectural_effect': 'trap_code=1, retire suppressed'}"}, {'id': 'error_bus_error', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'name': 'bus_error', 'condition': 'i_hresp=1 or d_hresp=1', 'architectural_effect': 'trap_code=2, retire suppressed'}"}, {'id': 'error_misaligned_word_access', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': '{\'name\': \'misaligned_word_access\', \'condition\': "LDR/STR effective_address[1:0] != 2\'b00", \'architectural_effect\': \'trap_code=3, bus launch suppressed, retire suppressed\'}'}]}
RESP_OKAY = 0
RESP_SLVERR = 2


def _parse_int(value, default=0):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip().replace("_", "")
    if not text:
        return default
    literal = text.lower()
    if "'" in literal:
        try:
            base_tag = literal.split("'", 1)[1][0]
            digits = literal.split(base_tag, 1)[1]
            digits = digits.replace("x", "0").replace("z", "0")
            base = {"h": 16, "d": 10, "b": 2}.get(base_tag, 10)
            return int(digits, base)
        except Exception:
            return default
    if text.startswith("0x"):
        return int(text, 16)
    try:
        return int(text, 10)
    except ValueError:
        return default


_BINOPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Div: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.LShift: lambda a, b: a << b,
    ast.RShift: lambda a, b: a >> b,
    ast.BitAnd: lambda a, b: a & b,
    ast.BitOr: lambda a, b: a | b,
    ast.BitXor: lambda a, b: a ^ b,
}
_UNARYOPS = {
    ast.UAdd: lambda a: a,
    ast.USub: lambda a: -a,
    ast.Invert: lambda a: ~a,
    ast.Not: lambda a: 0 if a else 1,
}
_CMPOPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
}


def _normal_expr(text):
    text = str(text or "").strip()
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"(?<![=!<>])!(?!=)", " not ", text)
    return text


def _literal_int(text):
    text = str(text).strip().replace("_", "")
    return bool(re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+|[0-9]*'[hHdDbB][0-9a-fA-FxXzZ]+)", text))


def _eval_ast(node, env):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, env)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return int(node.value)
        if isinstance(node.value, int):
            return node.value
        if isinstance(node.value, str):
            return _parse_int(node.value, 0)
        raise ValueError(f"unsupported constant {node.value!r}")
    if isinstance(node, ast.Name):
        if node.id in env:
            return _parse_int(env[node.id], 0)
        raise KeyError(f"unknown rule name {node.id}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval_ast(node.left, env), _eval_ast(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_ast(node.operand, env))
    if isinstance(node, ast.BoolOp):
        values = [_eval_ast(v, env) for v in node.values]
        if isinstance(node.op, ast.And):
            return int(all(values))
        if isinstance(node.op, ast.Or):
            return int(any(values))
    if isinstance(node, ast.Compare):
        left = _eval_ast(node.left, env)
        verdicts = []
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_ast(comparator, env)
            if type(op) not in _CMPOPS:
                raise ValueError(f"unsupported comparison {type(op).__name__}")
            verdicts.append(_CMPOPS[type(op)](left, right))
            left = right
        return int(all(verdicts))
    if isinstance(node, ast.IfExp):
        return _eval_ast(node.body if _eval_ast(node.test, env) else node.orelse, env)
    if isinstance(node, ast.Subscript):
        base = _eval_ast(node.value, env)
        sl = node.slice
        if isinstance(sl, ast.Index):
            sl = sl.value
        if isinstance(sl, ast.Slice):
            hi = _eval_ast(sl.lower, env) if sl.lower is not None else 0
            lo = _eval_ast(sl.upper, env) if sl.upper is not None else 0
            if hi < lo:
                hi, lo = lo, hi
            width = hi - lo + 1
            mask = (1 << width) - 1
            return (base >> lo) & mask
        idx = _eval_ast(sl, env)
        return (base >> idx) & 1
    raise ValueError(f"unsupported rule expression node {type(node).__name__}")


def _eval_rule_expr(expr, env):
    if isinstance(expr, bool):
        return int(expr)
    if isinstance(expr, int):
        return expr
    text = _normal_expr(expr)
    if not text:
        return 0
    if _literal_int(text):
        return _parse_int(text, 0)
    return _eval_ast(ast.parse(text, mode="eval"), env)


def _expr_names(expr):
    try:
        node = ast.parse(_normal_expr(expr), mode="eval")
    except Exception:
        return set()
    return {item.id for item in ast.walk(node) if isinstance(item, ast.Name)}


def _rule_items(value):
    if isinstance(value, dict):
        return [{"name": k, "expr": v} for k, v in value.items()]
    return [item for item in value or [] if isinstance(item, dict)]


class FunctionalModel:
    def __init__(self, params=None):
        self.params = dict(SSOT_MODEL.get("parameters") or {})
        if params:
            self.params.update(params)
        self.state_defaults = self._state_defaults()
        self.state = dict(self.state_defaults)
        self.registers = self._register_defaults()
        self.trace = []

    @staticmethod
    def _norm(value):
        text = str(value or "").strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        return text.strip("_")

    def _state_defaults(self):
        defaults = {}
        fm = SSOT_MODEL.get("function_model") or {}
        for idx, item in enumerate(fm.get("state_variables") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"state_{idx}")
            defaults[name] = item.get("reset", 0)
        defaults.setdefault("busy", 0)
        defaults.setdefault("error", 0)
        return defaults

    def _register_defaults(self):
        defaults = {}
        regs = SSOT_MODEL.get("registers") or {}
        for idx, item in enumerate(regs.get("register_list") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"REG{idx}")
            defaults[name] = item.get("reset", 0)
            off = item.get("offset")
            if off is not None:
                defaults[str(off)] = item.get("reset", 0)
        return defaults

    def reset(self):
        self.state = dict(self.state_defaults)
        self.registers = self._register_defaults()
        self.trace.clear()

    def _looks_like_register_access(self, txn):
        kind = self._norm(txn.get("kind") or txn.get("transaction") or "")
        return (
            kind in {"csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr"}
            or "reg" in txn
            or "addr_or_name" in txn
        )

    def _transactions(self):
        fm = SSOT_MODEL.get("function_model") or {}
        return [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]

    def _find_transaction(self, kind):
        wanted = self._norm(kind)
        for tx in self._transactions():
            aliases = [
                tx.get("id"),
                tx.get("name"),
                self._norm(tx.get("id")),
                self._norm(tx.get("name")),
            ]
            if wanted in {self._norm(x) for x in aliases if x}:
                return tx
        if wanted in {"reset", "rst"}:
            return {"id": "RESET", "name": "reset", "outputs": ["state reset"], "side_effects": ["reset"]}
        return None

    def _record(self, kind, txn, result):
        entry = {
            "kind": kind,
            "scenario_id": txn.get("scenario_id", ""),
            "result": result,
            "state": dict(self.state),
        }
        self.trace.append(entry)
        return result

    def _rule_env(self, txn):
        env = {}
        env.update(self.params)
        env.update(self.state)
        env.update(self.registers)
        env.update(txn)
        env.setdefault("true", 1)
        env.setdefault("false", 0)
        return env

    def _apply_structured_rules(self, tx, txn):
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        if not output_rules and not state_updates:
            return None

        env = self._rule_env(txn)
        result = {
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "sample_accepted": 0,
        }
        pending_outputs = []
        for idx, rule in enumerate(output_rules):
            name = str(rule.get("name") or rule.get("output") or rule.get("port") or f"output_{idx}")
            aliases = [
                str(v)
                for v in (rule.get("output"), rule.get("port"))
                if v is not None and str(v).strip() and str(v).strip() != name
            ]
            pending_outputs.append((
                name,
                rule.get("expr", rule.get("expression", rule.get("value", 0))),
                rule.get("width") or rule.get("bits"),
                aliases,
            ))

        def _resolve_pending_outputs(required_names=None):
            nonlocal pending_outputs
            required = set(required_names or [])
            unresolved_errors = {}
            for _pass in range(max(len(pending_outputs), 1) + 1):
                progressed = False
                next_pending = []
                for name, expr, width, aliases in pending_outputs:
                    try:
                        value = _eval_rule_expr(expr, env)
                    except KeyError as exc:
                        unresolved_errors[name] = str(exc)
                        next_pending.append((name, expr, width, aliases))
                        continue
                    if width is not None:
                        value &= (1 << max(_parse_int(width, 0), 0)) - 1 if _parse_int(width, 0) > 0 else value
                    result[name] = value
                    env[name] = value
                    for alias in aliases:
                        result.setdefault(alias, value)
                        env[alias] = value
                    unresolved_errors.pop(name, None)
                    progressed = True
                pending_outputs = next_pending
                if not pending_outputs:
                    break
                if required and required.issubset(env):
                    break
                if not progressed:
                    break
            if required:
                unresolved_required = sorted(name for name in required if name not in env)
                if unresolved_required:
                    detail = ", ".join(
                        f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}"
                        for name in unresolved_required
                    )
                    raise KeyError(f"unresolved sample condition dependencies: {detail}")
            return unresolved_errors

        output_names = set()
        for name, _expr, _width, aliases in pending_outputs:
            output_names.add(name)
            output_names.update(aliases)
        sample_expr = tx.get("sample_condition")
        sample_accepted = True
        if sample_expr not in (None, ""):
            needed_outputs = _expr_names(sample_expr) & output_names
            if needed_outputs:
                _resolve_pending_outputs(needed_outputs)
            sample_accepted = bool(_eval_rule_expr(sample_expr, env))
        result["sample_accepted"] = int(sample_accepted)

        unresolved_errors = _resolve_pending_outputs()
        if pending_outputs:
            missing = ", ".join(f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}" for name, _expr, _width, _aliases in pending_outputs)
            raise KeyError(f"unresolved output rule dependencies: {missing}")

        updates = {}
        pending_updates = []
        if sample_accepted:
            for idx, rule in enumerate(state_updates):
                pending_updates.append((
                    str(rule.get("name") or rule.get("state") or f"state_{idx}"),
                    rule.get("expr", rule.get("expression", rule.get("value", 0))),
                ))
        unresolved_errors = {}
        for _pass in range(max(len(pending_updates), 1) + 1):
            progressed = False
            next_pending = []
            for name, expr in pending_updates:
                try:
                    value = _eval_rule_expr(expr, env)
                except KeyError as exc:
                    unresolved_errors[name] = str(exc)
                    next_pending.append((name, expr))
                    continue
                updates[name] = value
                env[name] = value
                unresolved_errors.pop(name, None)
                progressed = True
            pending_updates = next_pending
            if not pending_updates:
                break
            if not progressed:
                break
        if pending_updates:
            missing = ", ".join(f"{name}: {unresolved_errors.get(name, 'unresolved dependency')}" for name, _expr in pending_updates)
            raise KeyError(f"unresolved state update dependencies: {missing}")
        if updates:
            self.state.update(updates)
            result["state_updates"] = dict(updates)
        return result

    def _apply_register_access(self, txn):
        if not self._looks_like_register_access(txn):
            return None
        op = self._norm(txn.get("op") or txn.get("kind"))
        key = txn.get("reg", txn.get("addr", txn.get("name", "")))
        key = str(key)
        if op in {"write", "wr", "csr_write", "control_status_access"}:
            self.registers[key] = txn.get("data", txn.get("value", 0))
            return {"resp": RESP_OKAY, "write": True, "reg": key, "value": self.registers[key]}
        if op in {"read", "rd", "csr_read"}:
            return {"resp": RESP_OKAY, "read": True, "reg": key, "value": self.registers.get(key, 0)}
        return None

    def _apply_primary(self, tx, txn):
        structured = self._apply_structured_rules(tx, txn)
        if structured is not None:
            return structured
        # T1 #1 — Cardinal rule enforcement:
        # When SSOT does not declare structured output_rules/state_updates for
        # this transaction, do NOT fabricate state via name heuristics. Return
        # an SSOT-question-annotated result so the gap surfaces in the trace
        # and downstream validators can escalate to ssot-gen / human.
        return {
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "outputs_spec": tx.get("outputs") or [],
            "side_effects_spec": tx.get("side_effects") or [],
            "ssot_question": (
                "[SSOT QUESTION] structured output_rules/state_updates undefined "
                "for transaction " + str(tx.get("id") or tx.get("name") or "<unknown>")
            ),
            "fabricated_state": False,
        }

    def apply(self, txn):
        txn = dict(txn or {})
        kind = self._norm(txn.get("kind") or txn.get("op") or txn.get("transaction") or "")
        reg_result = self._apply_register_access(txn)
        if reg_result is not None:
            return self._record(kind or "register_access", txn, reg_result)
        tx = self._find_transaction(kind)
        if tx is None:
            return self._record(kind or "unknown", txn, {"kind": kind or "unknown", "resp": RESP_SLVERR, "error": "unsupported_transaction"})
        if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {"reset", "fm_reset"}:
            self.reset()
            return self._record(kind or "reset", txn, {"kind": "reset", "resp": RESP_OKAY, "state": dict(self.state)})
        return self._record(kind, txn, self._apply_primary(tx, txn))

    def coverage_seed_bins(self):
        return {item["id"]: False for item in SSOT_MODEL.get("fcov_bins", [])}


def run_self_check():
    model = FunctionalModel()
    txs = SSOT_MODEL.get("function_model", {}).get("transactions", [])
    results = []
    for idx, tx in enumerate(txs):
        if not isinstance(tx, dict):
            continue
        kind = tx.get("id") or tx.get("name") or f"transaction_{idx}"
        txn = {"kind": kind, "scenario_id": f"self_{kind}"}
        for field_idx, field in enumerate(tx.get("required_fields") or []):
            name = str(field)
            if name and name not in txn:
                txn[name] = field_idx + idx + 1
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        rule_names = set()
        rule_names.update(_expr_names(tx.get("sample_condition", "")))
        for rule in output_rules + state_updates:
            rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        output_names = {
            str(rule.get("name") or rule.get("output") or rule.get("port"))
            for rule in output_rules
            if rule.get("name") or rule.get("output") or rule.get("port")
        }
        update_names = {
            str(rule.get("name") or rule.get("state"))
            for rule in state_updates
            if rule.get("name") or rule.get("state")
        }
        known_names = set(model.params) | set(model.state) | set(model.registers) | output_names | update_names
        known_names.update({"true", "false", "True", "False", "and", "or", "not"})
        for name in sorted(rule_names - known_names):
            if name and name not in txn:
                txn[name] = idx + len(txn) + 1
        result = model.apply(txn)
        results.append({
            "id": tx.get("id"),
            "name": tx.get("name"),
            "kind": kind,
            "passed": result.get("resp") == RESP_OKAY,
            "result": result,
        })
    unsupported = model.apply({"kind": "__unsupported_self_check__"})
    checks = [item["passed"] for item in results]
    checks.append(unsupported.get("resp") == RESP_SLVERR)

    # T1 #5 — invariants / reset / error_case coverage
    fm_block = SSOT_MODEL.get("function_model", {}) or {}
    invariants_raw = fm_block.get("invariants") or []
    if isinstance(invariants_raw, dict):
        invariants_raw = [{"name": k, "expr": v} for k, v in invariants_raw.items()]
    invariants = []
    for inv in invariants_raw:
        if isinstance(inv, str):
            invariants.append({"name": inv[:40], "expr": inv})
        elif isinstance(inv, dict):
            expr = inv.get("expr") or inv.get("expression") or inv.get("rule") or inv.get("invariant")
            if expr is None and len(inv) == 1:
                k, v = next(iter(inv.items())); expr = v if isinstance(v, str) else None
                inv = {"name": str(k), "expr": expr}
            if expr is not None:
                invariants.append({"name": inv.get("name") or str(expr)[:40], "expr": expr})
    invariants_eval_env = {}
    invariants_eval_env.update(model.params)
    invariants_eval_env.update(model.state)
    invariants_eval_env.update(model.registers)
    invariants_evaluated = 0
    invariants_failed = []
    invariants_skipped = []
    for inv in invariants:
        try:
            ok = bool(_eval_rule_expr(inv["expr"], invariants_eval_env))
            invariants_evaluated += 1
            if not ok:
                invariants_failed.append({"name": inv["name"], "expr": inv["expr"]})
        except Exception as exc:
            invariants_skipped.append({"name": inv["name"], "expr": inv["expr"], "reason": str(exc)[:80]})

    reset_consistency = True
    reset_diff = {}
    try:
        baseline_defaults = dict(model.state_defaults)
        snapshot_model = FunctionalModel()
        snapshot_model.reset()
        for k, v in baseline_defaults.items():
            actual = snapshot_model.state.get(k)
            if actual != v:
                reset_consistency = False
                reset_diff[k] = {"expected": v, "actual": actual}
    except Exception as exc:
        reset_consistency = False
        reset_diff["__error__"] = str(exc)[:80]

    error_cases_total = 0
    error_cases_planned = 0
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        cases = tx.get("error_cases") or []
        if isinstance(cases, list):
            error_cases_total += len(cases)
            error_cases_planned += sum(1 for c in cases if isinstance(c, dict) and c.get("condition"))

    overall_pass = all(checks) and not invariants_failed and reset_consistency

    return {
        "passed": overall_pass,
        "checks": len(checks),
        "failed": checks.count(False),
        "transactions": len(txs),
        "transaction_results": results,
        "unsupported_transaction_check": unsupported.get("resp") == RESP_SLVERR,
        "trace_entries": len(model.trace),
        "coverage_bins": len(SSOT_MODEL.get("fcov_bins", [])),
        "invariants_total": len(invariants),
        "invariants_evaluated": invariants_evaluated,
        "invariants_failed": invariants_failed,
        "invariants_skipped": invariants_skipped,
        "reset_consistency": reset_consistency,
        "reset_diff": reset_diff,
        "error_cases_total": error_cases_total,
        "error_cases_planned": error_cases_planned,
    }


if __name__ == "__main__":
    print(json.dumps(run_self_check(), indent=2))
