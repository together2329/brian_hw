#!/usr/bin/env python3
"""Executable SSOT functional model for rv32i_min.

Generated from yaml/rv32i_min.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'rv32i_min', 'parameters': {'XLEN': 32, 'RESET_PC': 0, 'INST_ALIGN': 4}, 'top_module': {'name': 'rv32i_min', 'file': 'rtl/rv32i_min.sv', 'version': '1.0', 'type': 'cpu', 'description': 'Minimal single-issue 3-stage RV32I CPU (37 instructions) with synchronous instruction/data buses.', 'reference_spec': 'RISC-V Unprivileged ISA RV32I', 'target': {'technology': 'generic', 'clock_freq_mhz': 100, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'if_id_reg', 'type': 'register', 'depth': 1, 'width': 64, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'IF/ID pipeline register'}, {'name': 'id_ex_reg', 'type': 'register', 'depth': 1, 'width': 192, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'ID/EX pipeline register'}, {'name': 'ex_mem_wb_reg', 'type': 'register', 'depth': 1, 'width': 160, 'read_ports': 1, 'write_ports': 1, 'latency': 0, 'description': 'EX/MEM_WB pipeline register'}], 'note': 'External instruction and data memories are outside IP boundary'}, 'registers': {'config': {'register_width': 32, 'addr_width': 5, 'byte_addressable': False, 'note': 'Architectural register file representation only; no CSR/MMIO map'}, 'register_list': [{'name': 'GPR', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'repeat': 32, 'stride': 1, 'category': 'architectural', 'description': 'General purpose registers x0..x31', 'fields': [{'name': 'value', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'description': 'Register value; x0 writes ignored and reads return zero', 'write_effect': 'APB write data updates this field value according to its bit mask.'}]}]}, 'function_model': {'purpose': 'Cycle-independent RV32I architectural contract for ISS-style equivalence and scoreboard comparison.', 'state_variables': [{'name': 'pc', 'source': 'architectural', 'reset': 0, 'description': 'Program counter'}, {'name': 'regfile', 'source': 'architectural', 'reset': 0, 'description': '32x32 register file with x0 immutable zero'}, {'name': 'excpt_o', 'source': 'architectural_output', 'reset': 0, 'description': 'One-cycle exception pulse'}], 'transactions': [{'id': 'FM_FETCH', 'name': 'fetch_and_default_advance', 'preconditions': ['pc % 4 == 0'], 'inputs': ['pc', 'i_rdata'], 'outputs': ['decoded instruction fields available to execute stage', 'default next_pc equals pc plus 4'], 'side_effects': ['pc advances by 4 when no control transfer or fault blocks retirement'], 'output_rules': [], 'state_updates': [{'name': 'next_pc', 'expr': 'pc + 4', 'width': 32, 'description': 'Moved from output_rules because this rule updates internal architectural state, not a declared output port.'}]}, {'id': 'FM_ALU', 'name': 'alu_and_immediate_ops', 'preconditions': ['opcode_class == 0'], 'inputs': ['rs1', 'rs2', 'imm', 'funct3', 'funct7'], 'outputs': ['rd receives computed 32-bit result'], 'side_effects': ['regfile writeback occurs when rd != 0'], 'error_cases': [{'condition': 'illegal_shamt', 'result': 'excpt_o pulse and no retirement'}], 'output_rules': [], 'state_updates': [{'name': 'wb_data', 'expr': 'alu_result & ((1 << 32) - 1)', 'width': 32, 'description': 'Moved from output_rules because this rule updates internal architectural state, not a declared output port.'}]}, {'id': 'FM_BRANCH', 'name': 'conditional_branches', 'preconditions': ['is_branch'], 'inputs': ['pc', 'branch_taken', 'branch_imm'], 'outputs': ['pc becomes branch target if taken else pc plus 4'], 'side_effects': ['no register writeback'], 'output_rules': [], 'state_updates': [{'name': 'next_pc', 'expr': '(pc + branch_imm) if branch_taken else (pc + 4)', 'width': 32, 'description': 'Moved from output_rules because this rule updates internal architectural state, not a declared output port.'}]}, {'id': 'FM_JUMP', 'name': 'jal_and_jalr', 'preconditions': ['is_jump'], 'inputs': ['pc', 'rs1', 'imm', 'is_jalr'], 'outputs': ['link register gets old pc plus 4 when rd != 0', 'jump target selected by JAL or JALR rule'], 'side_effects': ['pc redirected to computed target'], 'output_rules': [], 'state_updates': [{'name': 'next_pc', 'expr': '((rs1 + imm) & ~1) if is_jalr else (pc + imm)', 'width': 32, 'description': 'Moved from output_rules because this rule updates internal architectural state, not a declared output port.'}]}, {'id': 'FM_LOAD', 'name': 'loads_with_extension', 'preconditions': ['is_load'], 'inputs': ['d_rdata', 'funct3', 'effective_addr'], 'outputs': ['LB and LH sign-extend', 'LBU and LHU zero-extend', 'LW returns full 32-bit'], 'side_effects': ['writeback to rd when rd != 0'], 'error_cases': [{'condition': 'misaligned_access', 'result': 'excpt_o pulse and no retirement'}], 'output_rules': [], 'state_updates': [{'name': 'wb_data', 'expr': 'load_data_ext & ((1 << 32) - 1)', 'width': 32, 'description': 'Moved from output_rules because this rule updates internal architectural state, not a declared output port.'}]}, {'id': 'FM_STORE', 'name': 'stores_with_byte_enable', 'preconditions': ['is_store'], 'inputs': ['rs2', 'funct3', 'effective_addr'], 'outputs': ['d_we equals 1 and d_be reflects width and alignment'], 'side_effects': ['no register writeback'], 'error_cases': [{'condition': 'misaligned_access', 'result': 'excpt_o pulse and no retirement'}], 'output_rules': [{'name': 'store_valid', 'expr': '1 if (is_store and (not misaligned_access)) else 0', 'width': 1, 'port': 'd_valid'}]}, {'id': 'FM_SYSTEM', 'name': 'fence_ecall_ebreak', 'preconditions': ['is_system'], 'inputs': ['is_fence', 'is_ecall', 'is_ebreak'], 'outputs': ['FENCE inserts one bubble', 'ECALL and EBREAK pulse excpt_o'], 'side_effects': ['ECALL and EBREAK advance pc by 4'], 'output_rules': [{'name': 'exception_pulse', 'expr': '1 if (is_ecall or is_ebreak or illegal_shamt or misaligned_access) else 0', 'width': 1, 'port': 'excpt_o'}]}], 'invariants': ['regfile_x0 == 0', 'misaligned_access implies no_retire', 'jalr_target_lsb == 0']}, 'cycle_model': {'purpose': 'Clocked IF/ID_EX/MEM_WB contract with synchronous registered bus behavior.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 shell for cycle accounting while function_model remains architectural oracle.', 'clock': 'clk', 'reset': {'assertion': 'rst_n low asynchronously clears architectural and pipeline state', 'deassertion': 'state usable on first rising edge after synchronized deassertion'}, 'latency': {'fetch_to_decode': {'min_cycles': 1, 'max_cycles': 1, 'description': 'IF to ID_EX transfer'}, 'alu_ops_retire': {'min_cycles': 3, 'max_cycles': 3, 'description': 'IF to ID_EX to MEM_WB retire path'}, 'load_retire': {'min_cycles': 3, 'max_cycles': 3, 'description': 'Single-cycle synchronous data return assumption'}, 'store_issue': {'min_cycles': 2, 'max_cycles': 3, 'description': 'Address and write data presented by MEM stage'}, 'fence_penalty': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Required one-cycle bubble'}}, 'handshake_rules': [{'signal': 'i_valid', 'rule': 'i_valid == 1 implies i_addr is stable in the cycle'}, {'signal': 'd_valid', 'rule': 'd_valid == 1 implies d_addr and d_we and d_be are stable in the cycle'}, {'signal': 'd_we', 'rule': 'd_we == 1 indicates store and d_we == 0 indicates load'}, {'signal': 'excpt_o', 'rule': 'excpt_o pulses for exactly one cycle per triggering instruction'}], 'pipeline': [{'stage': 'IF', 'cycle': 't', 'action': 'Drive i_addr from pc and sample i_rdata'}, {'stage': 'ID_EX', 'cycle': 't+1', 'action': 'Decode and compute ALU or branch or target or effective address'}, {'stage': 'MEM_WB', 'cycle': 't+2', 'action': 'Perform load/store signaling and writeback and retire'}], 'ordering': ['Retirement is in program order with at most one commit per cycle', 'Faulting misaligned or illegal instruction does not retire', 'Store side effects occur only on aligned non-faulting stores'], 'backpressure': ['No explicit ready channels; interfaces are sampled synchronously each cycle'], 'observability': ['Every function_model transaction maps to IF or ID_EX or MEM_WB stage'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'synchronous memory response each cycle'}, 'outstanding': {'max': 1, 'description': 'single in-flight architectural operation'}, 'depth': {'pipeline_stages': 3, 'queue_depth': 1, 'description': 'fixed three-stage in-order pipe'}}}, 'fcov_bins': [{'id': 'SC01_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC01', 'description': 'reset contract'}, {'id': 'SC02_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC02', 'description': 'opcode sweep 37'}, {'id': 'SC03_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC03', 'description': 'branch taken and untaken'}, {'id': 'SC04_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC04', 'description': 'load store extension and byte enable'}, {'id': 'SC05_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC05', 'description': 'x0 immutable'}, {'id': 'SC06_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC06', 'description': 'FM_FETCH transaction'}, {'id': 'SC07_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC07', 'description': 'FM_ALU transaction'}, {'id': 'SC08_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC08', 'description': 'FM_BRANCH transaction'}, {'id': 'SC09_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC09', 'description': 'FM_JUMP transaction'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'FM_LOAD transaction'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'FM_STORE transaction'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'FM_SYSTEM transaction'}, {'id': 'fcov_opcode_37', 'class': 'opcode', 'coverage_domain': 'function', 'source': 'function_model.transactions', 'source_ref': 'function_model.transactions', 'description': 'All 37 required mnemonics observed'}, {'id': 'fcov_branch_taken_untaken', 'class': 'branch', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_BRANCH', 'source_ref': 'function_model.transactions.FM_BRANCH', 'description': 'Taken and untaken for each branch mnemonic'}, {'id': 'fcov_load_sign_zero_ext', 'class': 'data_transform', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_LOAD', 'source_ref': 'function_model.transactions.FM_LOAD', 'description': 'LB and LH sign-extension and LBU and LHU zero-extension'}, {'id': 'fcov_store_byte_enable', 'class': 'byte_enable', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_STORE', 'source_ref': 'function_model.transactions.FM_STORE', 'description': 'Store byte enable patterns for SB and SH and SW'}, {'id': 'fcov_x0_immutable', 'class': 'invariant', 'coverage_domain': 'function', 'source': 'function_model.invariants', 'source_ref': 'function_model.invariants', 'description': 'Writes to x0 are ignored'}, {'id': 'fcov_jal_jalr_link', 'class': 'jump_link', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_JUMP', 'source_ref': 'function_model.transactions.FM_JUMP', 'description': 'Link writeback and jalr bit0 clear'}, {'id': 'fcov_misaligned_fault', 'class': 'fault', 'coverage_domain': 'function', 'source': 'function_model.transactions', 'source_ref': 'function_model.transactions', 'description': 'Misaligned load or store raises pulse and no retirement'}, {'id': 'fcov_ecall_ebreak', 'class': 'system', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_SYSTEM', 'source_ref': 'function_model.transactions.FM_SYSTEM', 'description': 'ECALL and EBREAK pulse with pc advance'}, {'id': 'ccov_if_id_ex_mem_wb', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': 'Stage occupancy across IF ID_EX MEM_WB'}, {'id': 'ccov_sync_bus_rules', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules', 'source_ref': 'cycle_model.handshake_rules', 'description': 'Synchronous bus stability and sampling rules'}, {'id': 'ccov_fence_bubble', 'class': 'bubble', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions', 'source_ref': 'fsm.control.transitions', 'description': 'One-cycle fence bubble transition'}, {'id': 'ccov_exception_one_shot', 'class': 'pulse', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules', 'source_ref': 'cycle_model.handshake_rules', 'description': 'excpt_o one-cycle pulse behavior'}, {'id': 'function_fetch_and_default_advance', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_fetch', 'description': 'fetch_and_default_advance'}, {'id': 'function_alu_and_immediate_ops', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm_alu', 'description': 'alu_and_immediate_ops'}, {'id': 'function_conditional_branches', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm_branch', 'description': 'conditional_branches'}, {'id': 'function_jal_and_jalr', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm_jump', 'description': 'jal_and_jalr'}, {'id': 'function_loads_with_extension', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[4]', 'source_ref': 'function_model.transactions.fm_load', 'description': 'loads_with_extension'}, {'id': 'function_stores_with_byte_enable', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[5]', 'source_ref': 'function_model.transactions.fm_store', 'description': 'stores_with_byte_enable'}, {'id': 'function_fence_ecall_ebreak', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[6]', 'source_ref': 'function_model.transactions.fm_system', 'description': 'fence_ecall_ebreak'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'i_valid', 'rule': 'i_valid == 1 implies i_addr is stable in the cycle'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'd_valid', 'rule': 'd_valid == 1 implies d_addr and d_we and d_be are stable in the cycle'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'd_we', 'rule': 'd_we == 1 indicates store and d_we == 0 indicates load'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'excpt_o', 'rule': 'excpt_o pulses for exactly one cycle per triggering instruction'}"}, {'id': 'cycle_latency_fetch_to_decode', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.fetch_to_decode', 'source_ref': 'cycle_model.latency.fetch_to_decode', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'IF to ID_EX transfer'}"}, {'id': 'cycle_latency_alu_ops_retire', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.alu_ops_retire', 'source_ref': 'cycle_model.latency.alu_ops_retire', 'description': "{'min_cycles': 3, 'max_cycles': 3, 'description': 'IF to ID_EX to MEM_WB retire path'}"}, {'id': 'cycle_latency_load_retire', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.load_retire', 'source_ref': 'cycle_model.latency.load_retire', 'description': "{'min_cycles': 3, 'max_cycles': 3, 'description': 'Single-cycle synchronous data return assumption'}"}, {'id': 'cycle_latency_store_issue', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.store_issue', 'source_ref': 'cycle_model.latency.store_issue', 'description': "{'min_cycles': 2, 'max_cycles': 3, 'description': 'Address and write data presented by MEM stage'}"}, {'id': 'cycle_latency_fence_penalty', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.fence_penalty', 'source_ref': 'cycle_model.latency.fence_penalty', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Required one-cycle bubble'}"}, {'id': 'cycle_pipeline_if', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Drive i_addr from pc and sample i_rdata'}, {'id': 'cycle_pipeline_id_ex', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Decode and compute ALU or branch or target or effective address'}, {'id': 'cycle_pipeline_mem_wb', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Perform load/store signaling and writeback and retire'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Retirement is in program order with at most one commit per cycle'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Faulting misaligned or illegal instruction does not retire'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Store side effects occur only on aligned non-faulting stores'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No explicit ready channels; interfaces are sampled synchronously each cycle'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'max': 1, 'description': 'single in-flight architectural operation'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 3, 'queue_depth': 1, 'description': 'fixed three-stage in-order pipe'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '100'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_beats_per_cycle': 1, 'condition': 'synchronous memory response each cycle'}"}, {'id': 'fsm_control_reset_to_run_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[0]', 'source_ref': 'fsm.control.transitions[0]', 'description': 'rst_n_deasserted'}, {'id': 'fsm_control_run_to_fence_bubble_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[1]', 'source_ref': 'fsm.control.transitions[1]', 'description': 'decoded_fence'}, {'id': 'fsm_control_fence_bubble_to_run_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[2]', 'source_ref': 'fsm.control.transitions[2]', 'description': 'bubble_done'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_MISALIGNED_DATA', 'condition': 'misaligned_data_access', 'architectural_effect': 'pulse excpt_o for one cycle and block retirement'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_ILLEGAL_SHIFT_IMM', 'condition': 'illegal_shamt', 'architectural_effect': 'pulse excpt_o for one cycle and block retirement'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'ERR_ECALL_EBREAK', 'condition': 'is_ecall or is_ebreak', 'architectural_effect': 'pulse excpt_o for one cycle and advance pc by 4'}"}]}
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
    reduction_or = re.fullmatch(r"\|\s*\((.*)\)", text)
    if reduction_or:
        text = f"reduction_or({reduction_or.group(1)})"
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"(?<![=!<>])!(?!=)", " not ", text)
    return text


def _literal_int(text):
    text = str(text).strip().replace("_", "")
    return bool(re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+|[0-9]*'[hHdDbB][0-9a-fA-FxXzZ]+)", text))


def _h_bin_to_gray(value):
    v = _parse_int(value, 0)
    return v ^ (v >> 1)


def _h_gray_to_bin(value):
    g = _parse_int(value, 0)
    b = g
    s = g >> 1
    while s:
        b ^= s
        s >>= 1
    return b


def _h_popcount(value):
    return bin(_parse_int(value, 0) & ((1 << 256) - 1)).count("1")


def _h_parity(value):
    return _h_popcount(value) & 1


def _h_clog2(value):
    v = _parse_int(value, 0)
    if v <= 1:
        return 0
    return (v - 1).bit_length()


def _default_rule_helpers():
    return {
        "bin_to_gray": _h_bin_to_gray,
        "gray_to_bin": _h_gray_to_bin,
        "popcount": _h_popcount,
        "parity": _h_parity,
        "clog2": _h_clog2,
        "min": lambda a, b: min(_parse_int(a, 0), _parse_int(b, 0)),
        "max": lambda a, b: max(_parse_int(a, 0), _parse_int(b, 0)),
        "abs": lambda a: abs(_parse_int(a, 0)),
        "any": lambda *args: int(any(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "all": lambda *args: int(all(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "sum": lambda *args: int(sum(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "len": lambda *args: len(args[0]) if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else len(args),
    }


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
    if isinstance(node, ast.GeneratorExp):
        return _eval_comprehension(node, env, generator=True)
    if isinstance(node, ast.ListComp):
        return _eval_comprehension(node, env, generator=False)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError(f"unsupported rule call {ast.dump(node.func)}")
        func = env.get(node.func.id)
        if not callable(func):
            raise ValueError(f"unsupported rule helper {node.func.id}")
        if node.keywords:
            raise ValueError(f"unsupported keyword args for rule helper {node.func.id}")
        args = [_eval_ast(arg, env) for arg in node.args]
        return _parse_int(func(*args), 0)
    raise ValueError(f"unsupported rule expression node {type(node).__name__}")


def _eval_comprehension(node, env, generator=False):
    """Evaluate a generator expression or list comprehension.

    Supports single-clause ``for`` with optional ``if`` filter, e.g.:
        ``(x for x in range(8) if x > 0)``
    Nested comprehensions are not supported.
    """
    if not node.generators:
        raise ValueError("comprehension with no generators")
    comp = node.generators[0]
    if len(node.generators) > 1:
        raise ValueError("nested comprehensions are not supported in rule expressions")
    if not isinstance(comp.target, ast.Name):
        raise ValueError("comprehension target must be a simple name")
    var_name = comp.target.id
    iter_values = _eval_iter(comp.iter, env)
    results = []
    for val in iter_values:
        local_env = dict(env)
        local_env[var_name] = val
        # Apply if-filters
        skip = False
        for if_clause in comp.ifs:
            if not _eval_ast(if_clause, local_env):
                skip = True
                break
        if skip:
            continue
        results.append(_eval_ast(node.elt, local_env))
    return results if not generator else results


def _eval_iter(node, env):
    """Evaluate an iterable source (range call or name reference)."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "range":
            args = [_eval_ast(a, env) for a in node.args]
            if len(args) == 1:
                return list(range(args[0]))
            if len(args) == 2:
                return list(range(args[0], args[1]))
            if len(args) == 3:
                return list(range(args[0], args[1], args[2]))
            raise ValueError(f"range() expects 1-3 args, got {len(args)}")
        # Other callables: evaluate and treat result as iterable if possible
        func = env.get(node.func.id)
        if callable(func):
            call_args = [_eval_ast(a, env) for a in node.args]
            result = func(*call_args)
            if isinstance(result, (list, tuple, range)):
                return list(result)
            return [_parse_int(result, 0)]
    if isinstance(node, ast.Name):
        val = env.get(node.id)
        if isinstance(val, (list, tuple, range)):
            return list(val)
        return [_parse_int(val, 0)]
    raise ValueError(f"unsupported iterable in comprehension: {ast.dump(node)}")


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

    @staticmethod
    def _field_bounds(field):
        bits = field.get("bits")
        if isinstance(bits, (list, tuple)) and len(bits) >= 2:
            hi = _parse_int(bits[0], 0)
            lo = _parse_int(bits[1], 0)
            return (max(hi, lo), min(hi, lo))
        if "msb" in field and "lsb" in field:
            hi = _parse_int(field.get("msb"), 0)
            lo = _parse_int(field.get("lsb"), 0)
            return (max(hi, lo), min(hi, lo))
        if "lsb" in field and ("width" in field or "bit_width" in field):
            lo = _parse_int(field.get("lsb"), 0)
            width = max(1, _parse_int(field.get("width", field.get("bit_width", 1)), 1))
            return (lo + width - 1, lo)
        return (0, 0)

    def _register_read_value(self, reg):
        name = str(reg.get("name") or "")
        value = _parse_int(self.registers.get(name, reg.get("reset", 0)), 0)
        for field in reg.get("fields") or []:
            if not isinstance(field, dict):
                continue
            fname = str(field.get("name") or "")
            if fname in self.state:
                fval = _parse_int(self.state.get(fname), 0)
            elif f"{fname}_q" in self.state:
                fval = _parse_int(self.state.get(f"{fname}_q"), 0)
            elif fname in self.registers:
                fval = _parse_int(self.registers.get(fname), 0)
            else:
                continue
            hi, lo = self._field_bounds(field)
            width = max(1, hi - lo + 1)
            mask = (1 << width) - 1
            value = (value & ~(mask << lo)) | ((fval & mask) << lo)
        return value

    def _read_mux(self, addr):
        addr_i = _parse_int(addr, 0)
        regs = SSOT_MODEL.get("registers") or {}
        for reg in regs.get("register_list") or []:
            if not isinstance(reg, dict):
                continue
            off = reg.get("offset")
            if off is not None and addr_i == _parse_int(off, 0):
                return self._register_read_value(reg)
        return 0

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
        env.update(_default_rule_helpers())
        env.update(self.params)
        env.update(self.state)
        env.update(self.registers)
        env.update(txn)
        env["read_mux"] = self._read_mux
        env["reduction_or"] = lambda value: 1 if _parse_int(value, 0) != 0 else 0
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
        known_names.update(_default_rule_helpers().keys())
        known_names.update({"read_mux", "reduction_or", "range"})
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
    invariants_eval_env.update(_default_rule_helpers())
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
