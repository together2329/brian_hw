#!/usr/bin/env python3
"""Executable SSOT functional model for edge_detector.

Generated from yaml/edge_detector.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'edge_detector', 'parameters': {'SYNC_STAGES': 2, 'EDGE_MODE': 'both', 'WIDTH': 1, 'CLOCK_FREQ_MHZ': 50, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'edge_detector', 'file': 'rtl/edge_detector.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Parameterized edge detector with synchronization, APB-lite CSR interface, single PCLK domain.', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No SRAM/FIFO in edge detector. All state is in registers (sync_chain, prev_sync, CONTROL, STATUS, RAW_STATUS).'}, 'registers': {'config': {'register_width': 32, 'addr_width': 12, 'byte_addressable': True, 'num_channels': 1}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'CONTROL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 2, 'category': 'control', 'description': 'Edge detection control register', 'write_side_effects': ['Writing edge_mode updates detection polarity immediately.', 'Writing enable gates edge_o generation when 0.'], 'fields': [{'name': 'edge_mode', 'bits': [1, 0], 'access': 'rw', 'reset': 2, 'write_effect': '0=rising, 1=falling, 2=both, 3=reserved', 'description': 'Edge polarity mode'}, {'name': 'enable', 'bits': [2, 2], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable edge detection, 0=disable', 'description': 'Global edge detection enable'}, {'name': 'irq_enable', 'bits': [3, 3], 'access': 'rw', 'reset': 0, 'write_effect': '1=enable interrupt on edge detection', 'description': 'Interrupt enable'}, {'name': 'reserved_31_4', 'bits': [31, 4], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'STATUS', 'offset': 4, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'status', 'description': 'Edge detection status register', 'write_side_effects': ['Writing 1 to a sticky bit clears it (W1C).'], 'fields': [{'name': 'edge_sticky', 'bits': [7, 0], 'access': 'w1c', 'reset': 0, 'write_effect': 'Write-1 clears sticky bit per WIDTH lane', 'description': 'Sticky edge detected flags (up to 8 bits)'}, {'name': 'overflow', 'bits': [8, 8], 'access': 'w1c', 'reset': 0, 'write_effect': 'Write-1 clears overflow flag', 'description': 'Edge detected while previous sticky not cleared'}, {'name': 'reserved_31_9', 'bits': [31, 9], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'RAW_STATUS', 'offset': 8, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Raw edge detection status (non-sticky, current cycle)', 'fields': [{'name': 'edge_raw', 'bits': [7, 0], 'access': 'ro', 'reset': 0, 'description': 'Current-cycle edge detection flags'}, {'name': 'reserved_31_8', 'bits': [31, 8], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the IP computes independent of cycle timing.', 'state_variables': [{'name': 'sync_chain', 'source': 'rtl_contract.state_updates.sync_chain', 'reset': 0, 'description': 'Synchronizer shift register of width WIDTH*SYNC_STAGES'}, {'name': 'prev_sync', 'source': 'rtl_contract.state_updates.prev_sync', 'reset': 0, 'description': 'Previous-cycle synced sample for edge comparison'}, {'name': 'control_reg', 'source': 'registers.CONTROL', 'reset': 2, 'description': 'Edge mode, enable, irq_enable configuration'}, {'name': 'status_sticky', 'source': 'registers.STATUS.edge_sticky', 'reset': 0, 'description': 'Sticky edge-detected flags (W1C clear)'}, {'name': 'status_overflow', 'source': 'registers.STATUS.overflow', 'reset': 0, 'description': 'Overflow flag set when edge occurs before sticky cleared'}], 'transactions': [{'id': 'DETECT', 'name': 'edge_detect', 'preconditions': ['enable == 1', 'sync_chain has propagated at least SYNC_STAGES cycles since reset deassertion'], 'inputs': ['signal_i at PCLK domain (after sync)'], 'outputs': ['edge_o[width-1:0] = 1 for one cycle per detected edge matching EDGE_MODE', 'status_sticky |= edge_o', 'status_overflow |= edge_o & status_sticky', 'irq_o = |edge_o && irq_enable'], 'side_effects': ['sync_chain shifts every PCLK cycle', 'prev_sync updates to last stage of sync_chain'], 'error_cases': [], 'output_rules': [{'name': 'edge_o', 'expr': '(curr_sync ^ prev_sync) & mode_mask & enable', 'width': 'WIDTH', 'port': 'edge_o', 'description': 'One-cycle pulse per detected edge, masked by mode and enable'}, {'name': 'irq_o', 'expr': 'edge_o and irq_enable', 'width': 1, 'port': 'irq_o', 'description': 'Interrupt asserted when any edge detected and irq_enable set'}]}], 'invariants': ['edge_o is asserted for exactly one PCLK cycle per qualifying edge transition.', 'No edge_o pulse occurs when enable == 0.', 'status_sticky persists until software W1C clear.'], 'reference_model_hint': 'tb-gen should implement a Python scoreboard model from this section and compare expected/got for every scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when state, outputs, and interrupts may change.', 'executable': 'python', 'backend_policy': 'Use direct Python cycle model with BehavioralModel as oracle; run smoke checks without pytest-pymtl3 dependency.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'latency': {'sync_latency': {'min_cycles': 'SYNC_STAGES', 'max_cycles': 'SYNC_STAGES', 'description': 'Input synchronizer delay'}, 'edge_detect_latency': {'min_cycles': 1, 'max_cycles': 1, 'description': 'One-cycle combinational decode after sync'}, 'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}, 'interrupt_latency': {'min_cycles': 0, 'max_cycles': 1, 'description': 'irq_o asserts same cycle as edge_o when irq_enable set'}}, 'handshake_rules': [{'signal': 'PSEL', 'rule': 'PSEL must be asserted before PENABLE rises; transaction begins in SETUP phase (PSEL=1, PENABLE=0).'}, {'signal': 'PENABLE', 'rule': 'PENABLE rises one cycle after PSEL to enter ACCESS phase; sampled with PREADY to complete.'}, {'signal': 'PREADY', 'rule': 'PREADY must be asserted by slave to complete the ACCESS phase; PREADY may deassert to extend wait states.'}], 'pipeline': [{'stage': 'S0_SYNC', 'cycle': '0..SYNC_STAGES-1', 'action': 'Propagate signal_i through sync_chain flops'}, {'stage': 'S1_EDGE_DECODE', 'cycle': 'SYNC_STAGES', 'action': 'Compare prev_sync vs curr_sync; decode per EDGE_MODE'}, {'stage': 'S2_OUTPUT', 'cycle': 'SYNC_STAGES+1', 'action': 'Assert edge_o pulse; update sticky/overflow/irq'}], 'ordering': ['edge_o for cycle N reflects signal_i transition captured at cycle N-SYNC_STAGES-1.', 'Interrupt updates occur on the same rising edge as edge_o assertion.'], 'backpressure': ['No backpressure on edge_o; downstream must accept or drop the one-cycle pulse.'], 'performance': {'frequency_mhz': 50, 'throughput': {'sustained_edges_per_cycle': 1, 'condition': 'No missed edges when input changes slower than PCLK period'}, 'outstanding': {'read_max': 0, 'write_max': 0, 'description': 'No outstanding transactions; purely register/pipeline IP'}, 'depth': {'pipeline_stages': 'SYNC_STAGES + 1', 'queue_depth': 0, 'description': 'Sync chain plus decode stage'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Basic rising edge detection'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'Basic falling edge detection'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'Both-edge detection'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'Synchronizer latency'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'Sticky and overflow behavior'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'W1C clear'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'Enable gating'}, {'id': 'SC8_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC8', 'description': 'Reserved mode safety'}, {'id': 'SC9_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC9', 'description': 'Interrupt generation'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'APB register read/write'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'Illegal APB address'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'Multi-bit WIDTH operation'}, {'id': 'fcov_rising_edge', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.DETECT', 'source_ref': 'function_model.transactions.DETECT', 'description': 'Rising edge detected'}, {'id': 'fcov_falling_edge', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.DETECT', 'source_ref': 'function_model.transactions.DETECT', 'description': 'Falling edge detected'}, {'id': 'fcov_both_edge', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.DETECT', 'source_ref': 'function_model.transactions.DETECT', 'description': 'Both-edge detection'}, {'id': 'fcov_sticky_set', 'class': 'state', 'coverage_domain': 'function', 'source': 'function_model.state_variables.status_sticky', 'source_ref': 'function_model.state_variables.status_sticky', 'description': 'Sticky flag set'}, {'id': 'fcov_overflow_set', 'class': 'state', 'coverage_domain': 'function', 'source': 'function_model.state_variables.status_overflow', 'source_ref': 'function_model.state_variables.status_overflow', 'description': 'Overflow flag set'}, {'id': 'fcov_w1c_clear', 'class': 'register', 'coverage_domain': 'function', 'source': 'function_model.state_variables.status_sticky', 'source_ref': 'function_model.state_variables.status_sticky', 'description': 'W1C clear of sticky/overflow'}, {'id': 'fcov_enable_gate', 'class': 'output', 'coverage_domain': 'function', 'source': 'function_model.output_rules.edge_o', 'source_ref': 'function_model.output_rules.edge_o', 'description': 'Enable gating verified'}, {'id': 'fcov_reserved_mode', 'class': 'error', 'coverage_domain': 'function', 'source': 'function_model.state_variables.control_reg', 'source_ref': 'function_model.state_variables.control_reg', 'description': 'Reserved mode safely ignored'}, {'id': 'ccov_sync_latency', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.sync_latency', 'source_ref': 'cycle_model.latency.sync_latency', 'description': 'Synchronizer delay observed'}, {'id': 'ccov_edge_decode', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_EDGE_DECODE', 'source_ref': 'cycle_model.pipeline.S1_EDGE_DECODE', 'description': 'Edge decode stage observed'}, {'id': 'ccov_irq_same_cycle', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.interrupt_latency', 'source_ref': 'cycle_model.latency.interrupt_latency', 'description': 'Interrupt same-cycle assertion'}, {'id': 'ccov_apb_read', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules', 'source_ref': 'cycle_model.handshake_rules', 'description': 'APB read transaction observed'}, {'id': 'ccov_apb_write', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules', 'source_ref': 'cycle_model.handshake_rules', 'description': 'APB write transaction observed'}, {'id': 'function_edge_detect', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.detect', 'description': 'edge_detect'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'PSEL', 'rule': 'PSEL must be asserted before PENABLE rises; transaction begins in SETUP phase (PSEL=1, PENABLE=0).'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'PENABLE', 'rule': 'PENABLE rises one cycle after PSEL to enter ACCESS phase; sampled with PREADY to complete.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'PREADY', 'rule': 'PREADY must be asserted by slave to complete the ACCESS phase; PREADY may deassert to extend wait states.'}"}, {'id': 'cycle_latency_sync_latency', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.sync_latency', 'source_ref': 'cycle_model.latency.sync_latency', 'description': "{'min_cycles': 'SYNC_STAGES', 'max_cycles': 'SYNC_STAGES', 'description': 'Input synchronizer delay'}"}, {'id': 'cycle_latency_edge_detect_latency', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.edge_detect_latency', 'source_ref': 'cycle_model.latency.edge_detect_latency', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'One-cycle combinational decode after sync'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}"}, {'id': 'cycle_latency_interrupt_latency', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.interrupt_latency', 'source_ref': 'cycle_model.latency.interrupt_latency', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'irq_o asserts same cycle as edge_o when irq_enable set'}"}, {'id': 'cycle_pipeline_s0_sync', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Propagate signal_i through sync_chain flops'}, {'id': 'cycle_pipeline_s1_edge_decode', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Compare prev_sync vs curr_sync; decode per EDGE_MODE'}, {'id': 'cycle_pipeline_s2_output', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Assert edge_o pulse; update sticky/overflow/irq'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'edge_o for cycle N reflects signal_i transition captured at cycle N-SYNC_STAGES-1.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Interrupt updates occur on the same rising edge as edge_o assertion.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No backpressure on edge_o; downstream must accept or drop the one-cycle pulse.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 0, 'write_max': 0, 'description': 'No outstanding transactions; purely register/pipeline IP'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 'SYNC_STAGES + 1', 'queue_depth': 0, 'description': 'Sync chain plus decode stage'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_edges_per_cycle': 1, 'condition': 'No missed edges when input changes slower than PCLK period'}"}, {'id': 'fsm_note_sync_sample_to_edge_decode_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.note.transitions[0]', 'source_ref': 'fsm.note.transitions[0]', 'description': 'every PCLK rising edge'}, {'id': 'fsm_note_edge_decode_to_output_pulse_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.note.transitions[1]', 'source_ref': 'fsm.note.transitions[1]', 'description': 'edge_decode matches EDGE_MODE and enable==1'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_ILLEGAL_ACCESS', 'condition': 'APB access to unmapped address', 'architectural_effect': 'PSLVERR=1, no register state change'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_RESERVED_MODE', 'condition': 'EDGE_MODE=3 (reserved)', 'architectural_effect': 'No edge detection; edge_o remains zero regardless of input'}"}]}
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
        self._declared_state_names = set(self.state_defaults)
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

    def _state_name_for_register(self, reg):
        name = str(reg.get("name") or "").strip()
        if not name:
            return ""
        fm = SSOT_MODEL.get("function_model") or {}
        for row in fm.get("state_variables") or []:
            if not isinstance(row, dict):
                continue
            source = str(row.get("source") or "").strip().lower()
            state_name = str(row.get("name") or "").strip()
            if state_name and source == f"registers.{name}".lower():
                return state_name
        norm = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        candidates = [
            norm,
            f"{norm}_reg",
            f"{norm}_q",
            f"{norm}_r",
            f"{norm}_value",
        ]
        for field in reg.get("fields") or []:
            if isinstance(field, dict):
                fname = re.sub(r"[^a-z0-9]+", "_", str(field.get("name") or "").lower()).strip("_")
                if fname:
                    candidates.extend([fname, f"{fname}_reg", f"{fname}_q", f"{fname}_r"])
        for candidate in candidates:
            if candidate in self.state:
                return candidate
        return ""

    def _register_read_value(self, reg):
        name = str(reg.get("name") or "")
        state_name = self._state_name_for_register(reg)
        if state_name:
            value = _parse_int(self.state.get(state_name), 0)
        else:
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

    def _derived_signal_items(self):
        fm = SSOT_MODEL.get("function_model") or {}
        return _rule_items(fm.get("derived_signals"))

    def _resolve_derived_signals(self, env):
        pending = []
        for idx, item in enumerate(self._derived_signal_items()):
            name = str(
                item.get("name")
                or item.get("signal")
                or item.get("output")
                or item.get("port")
                or f"derived_{idx}"
            )
            expr = item.get("expr", item.get("expression", item.get("value", "")))
            if name and expr not in (None, ""):
                pending.append((name, expr, item.get("width") or item.get("bits")))

        unresolved_errors = {}
        for _pass in range(max(len(pending), 1) + 1):
            progressed = False
            next_pending = []
            for name, expr, width in pending:
                try:
                    value = _eval_rule_expr(expr, env)
                except KeyError as exc:
                    unresolved_errors[name] = str(exc)
                    next_pending.append((name, expr, width))
                    continue
                if width is not None:
                    width_i = _parse_int(width, 0)
                    value &= (1 << max(width_i, 0)) - 1 if width_i > 0 else value
                env[name] = value
                unresolved_errors.pop(name, None)
                progressed = True
            pending = next_pending
            if not pending or not progressed:
                break
        return unresolved_errors

    @staticmethod
    def _norm_state_token(value):
        text = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
        for suffix in ("_reg", "_q", "_r", "_ff"):
            if text.endswith(suffix):
                text = text[: -len(suffix)]
                break
        return text

    def _state_update_target(self, update_name):
        name = str(update_name or "").strip()
        if name in self._declared_state_names:
            return name
        norm_name = self._norm_state_token(name)
        best = ""
        best_len = 0
        for state_name in self._declared_state_names:
            norm_state = self._norm_state_token(state_name)
            if not norm_state:
                continue
            if norm_name == norm_state or norm_name.endswith("_" + norm_state) or f"_{norm_state}_" in norm_name:
                if len(norm_state) > best_len:
                    best = state_name
                    best_len = len(norm_state)
        return best

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
        self._resolve_derived_signals(env)
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
                target = self._state_update_target(name)
                if target and target != name:
                    updates[target] = value
                    env[target] = value
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
            commit_updates = {}
            for update_name, value in updates.items():
                target = self._state_update_target(update_name)
                if target:
                    commit_updates[target] = value
                else:
                    commit_updates[update_name] = value
            self.state.update(commit_updates)
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
        tx = self._find_transaction(kind)
        if tx is not None:
            if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {"reset", "fm_reset"}:
                self.reset()
                return self._record(kind or "reset", txn, {"kind": "reset", "resp": RESP_OKAY, "state": dict(self.state)})
            return self._record(kind, txn, self._apply_primary(tx, txn))
        reg_result = self._apply_register_access(txn)
        if reg_result is not None:
            return self._record(kind or "register_access", txn, reg_result)
        if tx is None:
            return self._record(kind or "unknown", txn, {"kind": kind or "unknown", "resp": RESP_SLVERR, "error": "unsupported_transaction"})

    def _eval_precondition(self, expr, env):
        """Evaluate a single precondition string against env.

        SSOT preconditions are mostly Python-evaluable but occasionally carry
        a trailing natural-language clause in parentheses (e.g.
        '(req_i & req_mask) != 0 (at least one unmasked active request)').
        Normalize SQL-style OR/AND/NOT to Python operators, strip trailing
        natural-language parentheticals, and try progressively shorter
        prefixes until ast.parse succeeds. Unparseable preconditions are
        treated as True so they don't block transaction matching.
        """
        text = str(expr or "").strip()
        if not text:
            return True
        # Normalize boolean operators (SSOT prose sometimes uses uppercase).
        text = re.sub(r"\bOR\b", " or ",  text)
        text = re.sub(r"\bAND\b", " and ", text)
        text = re.sub(r"\bNOT\b", " not ", text)
        # Drop trailing parenthesized natural-language comments
        # ('something words ...'). Detect by alpha-majority content.
        def _strip_nl_tail(s):
            # Find a trailing " (...)" where contents are mostly alphabetic.
            depth = 0
            best_end = len(s)
            i = len(s) - 1
            # Walk from the right, capture the last balanced "(...)" tail.
            while i >= 0:
                ch = s[i]
                if ch == ")":
                    depth += 1
                elif ch == "(":
                    depth -= 1
                    if depth == 0:
                        inner = s[i + 1:best_end - 1]
                        alpha = sum(1 for c in inner if c.isalpha())
                        if alpha >= max(3, len(inner) // 2) and " " in inner:
                            # Natural language tail.
                            return s[:i].rstrip()
                        break
                i -= 1
            return s
        text = _strip_nl_tail(text)
        # Try ast.parse on the full string, then on progressively shorter
        # prefixes ending at a comparison/logical operator.
        candidates = [text]
        for tok in (" and ", " or "):
            for piece in text.split(tok):
                candidates.append(piece.strip())
        for cand in candidates:
            if not cand:
                continue
            try:
                tree = ast.parse(cand, mode="eval")
            except Exception:
                continue
            try:
                return bool(eval(compile(tree, "<precond>", mode="eval"), {"__builtins__": {}}, dict(env)))
            except Exception:
                continue
        return True

    def _select_transaction(self, inputs):
        """Pick the transaction whose preconditions all hold given inputs.

        Mutually-exclusive preconditions (typical SSOT pattern) yield a single
        active transaction. If multiple match, the first declared wins.
        Returns (tx, txn_payload) or (None, None) if none match.
        """
        env = dict(self.state)
        env.update(self.registers)
        env.update(inputs or {})
        for tx in self._transactions():
            if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {"reset", "fm_reset"}:
                continue
            preconds = [p for p in (tx.get("preconditions") or []) if isinstance(p, str)]
            if all(self._eval_precondition(p, env) for p in preconds):
                txn = {"kind": tx.get("id") or tx.get("name")}
                txn.update(inputs or {})
                return tx, txn
        return None, None

    def step(self, inputs=None):
        """Cycle-accurate step: select active transaction from preconditions,
        apply its output_rules and state_updates against current state and
        inputs, register the result. Mirrors the RTL's per-cycle behaviour
        when cocotb drives the same inputs cycle-by-cycle.

        Returns the structured result dict (same shape as apply()).
        """
        inputs = inputs or {}
        tx, txn = self._select_transaction(inputs)
        if tx is None:
            # No transaction matched preconditions: hold state, emit zero outputs.
            return {"kind": "idle", "resp": RESP_OKAY, "state": dict(self.state)}
        try:
            return self._record(tx.get("id") or "", txn, self._apply_primary(tx, txn))
        except KeyError as exc:
            # output_rule references a signal that's neither SSOT state, FL
            # register, nor caller-provided input (e.g. decoded combinational
            # signals: branch_taken, is_store). Surface a partial idle result
            # rather than crash — the per-cycle co-sim path treats this as
            # 'no comparable expected at this cycle for this IP'.
            return {
                "kind": "step_unresolved",
                "resp": RESP_OKAY,
                "transaction_id": tx.get("id"),
                "transaction_name": tx.get("name"),
                "step_unresolved": str(exc),
            }

    def csr_write(self, offset, data):
        """Apply an APB-style CSR write via _apply_register_access. Drives
        the registers dict + any state_variables sourced from those register
        fields (e.g. arb_enabled <- CTRL.enable)."""
        result = self._apply_register_access({"kind": "csr_write", "op": "write", "addr": offset, "reg": offset, "data": data, "value": data})
        # Mirror register field reset/source mapping into state_variables when
        # state_variables.source is a register field path.
        regs = SSOT_MODEL.get("registers") or {}
        reg_list = regs.get("register_list") or []
        fm = SSOT_MODEL.get("function_model") or {}
        state_vars = fm.get("state_variables") or []
        # Find which register matched the offset.
        matched_reg = None
        for r in reg_list:
            if r.get("offset") == offset:
                matched_reg = r
                break
        if matched_reg is None:
            return result
        for sv in state_vars:
            src = str(sv.get("source") or "")
            if not src.startswith("registers."):
                continue
            parts = src.split(".")
            if len(parts) >= 2 and parts[1] != matched_reg.get("name"):
                continue
            if len(parts) >= 3:
                field_name = parts[2]
                for f in matched_reg.get("fields") or []:
                    if f.get("name") == field_name:
                        bits = f.get("bits") or [0, 0]
                        hi, lo = (int(bits[0]), int(bits[1])) if len(bits) >= 2 else (0, 0)
                        mask = (1 << (hi - lo + 1)) - 1
                        self.state[sv.get("name")] = (data >> lo) & mask
                        break
            else:
                self.state[sv.get("name")] = data
        return result

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
        derived_signals = _rule_items((SSOT_MODEL.get("function_model") or {}).get("derived_signals"))
        rule_names = set()
        rule_names.update(_expr_names(tx.get("sample_condition", "")))
        for rule in output_rules + state_updates:
            rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        for rule in derived_signals:
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
        derived_names = {
            str(rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port"))
            for rule in derived_signals
            if rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port")
        }
        known_names = set(model.params) | set(model.state) | set(model.registers) | output_names | update_names
        known_names.update(derived_names)
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
