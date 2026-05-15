#!/usr/bin/env python3
"""Executable SSOT functional model for arbiter_rr.

Generated from yaml/arbiter_rr.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'arbiter_rr', 'parameters': {'NUM_REQ': 4, 'IDX_WIDTH': 2, 'APB_ADDR_WIDTH': 8, 'APB_DATA_WIDTH': 32}, 'top_module': {'name': 'arbiter_rr', 'file': 'rtl/arbiter_rr.sv', 'version': '1.0', 'type': 'bus', 'description': 'Parameterized N-input round-robin arbiter with 1-cycle latency, configurable request masking, and APB-lite CSR for runtime control.', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No internal memory or FIFO — purely combinational + registered arbitration logic.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 8, 'byte_addressable': True, 'num_channels': 1}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 1, 'category': 'control', 'description': 'Arbiter control register', 'write_side_effects': ['enable=0 freezes last_winner and forces all grant outputs to zero.', 'enable=1 resumes normal arbitration.'], 'fields': [{'name': 'enable', 'bits': [0, 0], 'access': 'rw', 'reset': 1, 'write_effect': '0=disable arbiter, 1=enable arbiter', 'description': 'Global arbiter enable'}, {'name': 'reserved_31_1', 'bits': [31, 1], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'REQ_MASK', 'offset': 4, 'width': 32, 'access': 'rw', 'reset': 15, 'category': 'control', 'description': 'Per-request enable mask (bit i=1 enables requestor i)', 'write_side_effects': ['Masked requests (bit=0) are excluded from arbitration on the next cycle.'], 'fields': [{'name': 'mask', 'bits': [3, 0], 'access': 'rw', 'reset': 15, 'write_effect': 'Update request mask; only lower NUM_REQ bits are active', 'description': 'Request enable mask (default all enabled)'}, {'name': 'reserved_31_4', 'bits': [31, 4], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'STATUS', 'offset': 8, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Arbiter status (read-only)', 'fields': [{'name': 'winner', 'bits': [3, 0], 'access': 'ro', 'reset': 0, 'description': 'Last granted requestor index (one-hot representation of last_winner)'}, {'name': 'active_req', 'bits': [7, 4], 'access': 'ro', 'reset': 0, 'description': 'Current unmasked active requests snapshot (req_i & mask)'}, {'name': 'reserved_31_8', 'bits': [31, 8], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the arbiter computes independent of cycle timing.', 'state_variables': [{'name': 'last_winner', 'source': 'registers.STATUS.winner', 'reset': 0, 'description': 'Index of the last granted requestor; used as priority rotation base'}, {'name': 'arb_enabled', 'source': 'registers.CTRL.enable', 'reset': 1, 'description': 'Global arbiter enable from CSR'}, {'name': 'req_mask', 'source': 'registers.REQ_MASK', 'reset': 'all-ones', 'description': 'Per-request enable mask (1=enabled, 0=masked)'}], 'transactions': [{'id': 'FM1', 'name': 'arbitrate_grant', 'preconditions': ['arb_enabled == 1', '(req_i & req_mask) != 0 (at least one unmasked active request)'], 'inputs': ['req_i: N-bit request vector', 'req_mask: N-bit mask from CSR', 'last_winner: priority rotation base index'], 'outputs': ['gnt_o is one-hot with exactly one bit set at selected_index', 'gnt_valid_o == 1', 'gnt_idx_o == selected_index (binary)', 'last_winner updated to selected_index'], 'output_rules': [{'name': 'grant_index', 'expr': '1 if ((last_winner == 0) and (((req_i & req_mask) & 2) != 0)) else (2 if ((last_winner == 0) and (((req_i & req_mask) & 2) == 0) and (((req_i & req_mask) & 4) != 0)) else (3 if ((last_winner == 0) and (((req_i & req_mask) & 2) == 0) and (((req_i & req_mask) & 4) == 0) and (((req_i & req_mask) & 8) != 0)) else (0 if (last_winner == 0) else (2 if ((last_winner == 1) and (((req_i & req_mask) & 4) != 0)) else (3 if ((last_winner == 1) and (((req_i & req_mask) & 4) == 0) and (((req_i & req_mask) & 8) != 0)) else (0 if ((last_winner == 1) and (((req_i & req_mask) & 4) == 0) and (((req_i & req_mask) & 8) == 0) and (((req_i & req_mask) & 1) != 0)) else (1 if (last_winner == 1) else (3 if ((last_winner == 2) and (((req_i & req_mask) & 8) != 0)) else (0 if ((last_winner == 2) and (((req_i & req_mask) & 8) == 0) and (((req_i & req_mask) & 1) != 0)) else (1 if ((last_winner == 2) and (((req_i & req_mask) & 8) == 0) and (((req_i & req_mask) & 1) == 0) and (((req_i & req_mask) & 2) != 0)) else (2 if (last_winner == 2) else (0 if (((req_i & req_mask) & 1) != 0) else (1 if (((req_i & req_mask) & 2) != 0) else (2 if (((req_i & req_mask) & 4) != 0) else 3))))))))))))))', 'width': 'IDX_WIDTH', 'port': 'gnt_idx_o', 'description': 'Binary index of the first active request in the circular scan for NUM_REQ=4 default'}, {'name': 'grant', 'expr': '1 << grant_index', 'width': 'NUM_REQ', 'port': 'gnt_o', 'description': 'One-hot grant to selected requestor'}, {'name': 'grant_valid', 'expr': '1', 'width': 1, 'port': 'gnt_valid_o', 'description': 'Indicates a valid grant is being asserted'}], 'state_updates': [{'name': 'last_winner', 'reset': 0, 'expr': 'grant_index'}], 'side_effects': ['last_winner rotates to current winner so it gets lowest priority next cycle', 'Only one requestor is granted per cycle (one-hot invariant)'], 'error_cases': []}, {'id': 'FM2', 'name': 'no_grant_idle', 'preconditions': ['arb_enabled == 0 OR (req_i & req_mask) == 0'], 'inputs': ['req_i: N-bit request vector', 'req_mask: N-bit mask'], 'outputs': ['gnt_o == 0', 'gnt_valid_o == 0', 'gnt_idx_o == 0', 'last_winner unchanged'], 'output_rules': [{'name': 'grant', 'expr': '0', 'width': 'NUM_REQ', 'port': 'gnt_o', 'description': 'No grant asserted'}, {'name': 'grant_valid', 'expr': '0', 'width': 1, 'port': 'gnt_valid_o', 'description': 'No valid grant'}, {'name': 'grant_index', 'expr': '0', 'width': 'IDX_WIDTH', 'port': 'gnt_idx_o', 'description': 'Index zero (meaningless when grant_valid=0)'}], 'state_updates': [{'name': 'last_winner', 'reset': 0, 'expr': 'last_winner'}], 'side_effects': ['last_winner is preserved unchanged when no grant is issued'], 'error_cases': []}], 'invariants': ['At most one bit in gnt_o is asserted per cycle (one-hot invariant).', 'gnt_valid_o == 0 implies gnt_o == 0.', 'gnt_valid_o == 1 implies exactly one bit in gnt_o is set and gnt_idx_o equals the index of that bit.', 'Masked requests never receive a grant regardless of req_i state.', 'When arb_enabled == 0, all outputs are zero and last_winner is frozen.', 'Round-robin fairness: a requestor that was granted in the previous cycle has the lowest priority in the current cycle.'], 'reference_model_hint': 'tb-gen should implement a Python reference model that replicates the circular priority scan and compare expected/got gnt_o, gnt_valid_o, gnt_idx_o for every scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when arbitration outputs and state may change.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; keep FunctionalModel as the behavioral oracle.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state (last_winner=0, gnt_o=0, gnt_valid_o=0, gnt_idx_o=0)', 'deassertion': 'State is usable on the first rising edge after synchronized deassertion'}, 'latency': {'arbitration': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Request sampled on cycle N produces registered grant on cycle N+1'}, 'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}}, 'handshake_rules': [{'signal': 'req_i', 'rule': 'Sampled on rising PCLK; requesters must hold req_i stable until corresponding gnt_o is seen.'}, {'signal': 'gnt_o', 'rule': 'Registered output — reflects arbitration decision from the previous cycle. At most one bit high.'}, {'signal': 'gnt_valid_o', 'rule': 'Registered — high when a valid grant is being asserted this cycle.'}, {'signal': 'gnt_idx_o', 'rule': 'Registered — valid binary index when gnt_valid_o is high; zero otherwise.'}], 'pipeline': [{'stage': 'S0_SAMPLE_REQ', 'cycle': 0, 'action': 'Latch req_i, apply mask (req_i & req_mask), read last_winner'}, {'stage': 'S1_GRANT', 'cycle': 1, 'action': 'Priority encoder evaluates; gnt_o, gnt_idx_o, gnt_valid_o registered and driven to outputs; last_winner updated'}], 'ordering': ['Grant outputs reflect the arbitration decision from the previous cycle (1-stage pipeline).', 'last_winner update occurs on the same rising edge as the grant output registration.', 'CSR writes to REQ_MASK or CTRL take effect on the next arbitration cycle (registered config).'], 'backpressure': ['No backpressure mechanism — the arbiter produces a grant every cycle when enabled and requests are present. Requesters must accept the grant immediately.'], 'performance': {'frequency_mhz': 50, 'throughput': {'grants_per_cycle': 1, 'condition': 'At least one unmasked request active and arbiter enabled'}, 'outstanding': {'read_max': 0, 'write_max': 0, 'description': 'No outstanding AXI-style transactions — simple combinatorial arbiter'}, 'depth': {'pipeline_stages': 1, 'queue_depth': 0, 'description': 'Single-stage registered output pipeline'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Single requestor grant'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'Round-robin fairness'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'Request masking'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'Enable/disable'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'No requests idle'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'Last winner persistence across disable'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'APB CSR read/write'}, {'id': 'SC8_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC8', 'description': 'APB illegal offset'}, {'id': 'SC9_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC9', 'description': 'One-hot grant invariant under all input combinations'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'Reset behavior'}, {'id': 'fcov_grant_single', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM1', 'source_ref': 'function_model.transactions.FM1', 'description': 'Single requestor grant observed'}, {'id': 'fcov_grant_all_rotation', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM1', 'source_ref': 'function_model.transactions.FM1', 'description': 'All 4 requestors granted in round-robin rotation'}, {'id': 'fcov_mask_each_bit', 'class': 'register_field', 'coverage_domain': 'function', 'source': 'function_model.state_variables.req_mask', 'source_ref': 'function_model.state_variables.req_mask', 'description': 'Each mask bit exercised enabled and disabled'}, {'id': 'fcov_enable_toggle', 'class': 'register_field', 'coverage_domain': 'function', 'source': 'function_model.state_variables.arb_enabled', 'source_ref': 'function_model.state_variables.arb_enabled', 'description': 'Enable toggled 1→0 and 0→1'}, {'id': 'fcov_no_grant_idle', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM2', 'source_ref': 'function_model.transactions.FM2', 'description': 'No-grant idle path observed'}, {'id': 'ccov_sample_stage', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S0_SAMPLE_REQ', 'source_ref': 'cycle_model.pipeline.S0_SAMPLE_REQ', 'description': 'Request sample stage observed'}, {'id': 'ccov_grant_stage', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_GRANT', 'source_ref': 'cycle_model.pipeline.S1_GRANT', 'description': 'Grant output stage observed'}, {'id': 'ccov_1cycle_latency', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.arbitration', 'source_ref': 'cycle_model.latency.arbitration', 'description': '1-cycle arbitration latency measured and confirmed'}, {'id': 'ccov_req_stability', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.req_i', 'source_ref': 'cycle_model.handshake_rules.req_i', 'description': 'Request stability rule exercised'}, {'id': 'ccov_gnt_onehot_assertion', 'class': 'assertion', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.gnt_o', 'source_ref': 'cycle_model.handshake_rules.gnt_o', 'description': 'One-hot grant invariant assertion triggered'}, {'id': 'ccov_reset_clean', 'class': 'reset', 'coverage_domain': 'cycle', 'source': 'cycle_model.reset', 'source_ref': 'cycle_model.reset', 'description': 'Reset clears all outputs and state'}, {'id': 'function_arbitrate_grant', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm1', 'description': 'arbitrate_grant'}, {'id': 'function_no_grant_idle', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm2', 'description': 'no_grant_idle'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'req_i', 'rule': 'Sampled on rising PCLK; requesters must hold req_i stable until corresponding gnt_o is seen.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'gnt_o', 'rule': 'Registered output — reflects arbitration decision from the previous cycle. At most one bit high.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'gnt_valid_o', 'rule': 'Registered — high when a valid grant is being asserted this cycle.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'gnt_idx_o', 'rule': 'Registered — valid binary index when gnt_valid_o is high; zero otherwise.'}"}, {'id': 'cycle_latency_arbitration', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.arbitration', 'source_ref': 'cycle_model.latency.arbitration', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Request sampled on cycle N produces registered grant on cycle N+1'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}"}, {'id': 'cycle_pipeline_s0_sample_req', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Latch req_i, apply mask (req_i & req_mask), read last_winner'}, {'id': 'cycle_pipeline_s1_grant', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Priority encoder evaluates; gnt_o, gnt_idx_o, gnt_valid_o registered and driven to outputs; last_winner updated'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Grant outputs reflect the arbitration decision from the previous cycle (1-stage pipeline).'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'last_winner update occurs on the same rising edge as the grant output registration.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'CSR writes to REQ_MASK or CTRL take effect on the next arbitration cycle (registered config).'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No backpressure mechanism — the arbiter produces a grant every cycle when enabled and requests are present. Requesters must accept the grant immediately.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 0, 'write_max': 0, 'description': 'No outstanding AXI-style transactions — simple combinatorial arbiter'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 1, 'queue_depth': 0, 'description': 'Single-stage registered output pipeline'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'grants_per_cycle': 1, 'condition': 'At least one unmasked request active and arbiter enabled'}"}, {'id': 'fsm_arb_fsm_idle_to_eval_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.arb_fsm.transitions[0]', 'source_ref': 'fsm.arb_fsm.transitions[0]', 'description': 'arb_enabled==1 && (req_i & mask) != 0'}, {'id': 'fsm_arb_fsm_eval_to_grant_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.arb_fsm.transitions[1]', 'source_ref': 'fsm.arb_fsm.transitions[1]', 'description': 'always (1-cycle combinational eval)'}, {'id': 'fsm_arb_fsm_grant_to_idle_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.arb_fsm.transitions[2]', 'source_ref': 'fsm.arb_fsm.transitions[2]', 'description': 'next cycle: re-evaluate with updated last_winner'}, {'id': 'fsm_arb_fsm_idle_to_idle_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.arb_fsm.transitions[3]', 'source_ref': 'fsm.arb_fsm.transitions[3]', 'description': 'arb_enabled==0 || (req_i & mask) == 0'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_APB_ILLEGAL', 'condition': 'APB access to undefined register offset', 'architectural_effect': 'PSLVERR=1 for that transfer, PRDATA=0'}"}]}
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
