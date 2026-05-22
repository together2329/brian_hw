#!/usr/bin/env python3
"""Executable SSOT functional model for gray_counter.

Generated from yaml/gray_counter.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'gray_counter', 'parameters': {'WIDTH': 4, 'CLOCK_FREQ_MHZ': 200}, 'top_module': {'name': 'gray_counter', 'file': 'rtl/gray_counter.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Synchronous parameterized Gray-code counter smoke-fixture IP with wrap pulse output.', 'reference_spec': 'gray_counter/req/gray_counter_requirements.md', 'target': {'technology': 'generic', 'clock_freq_mhz': 200, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No SRAM/FIFO/memory macros; only internal flip-flop state.'}, 'registers': {'config': {'register_width': 0, 'addr_width': 0, 'byte_addressable': False}, 'register_list': [], 'note': 'No CSR/register file by requirement; control is direct pin-level.', 'no_registers': True, 'policy': 'No firmware-visible registers are declared; add register_list before CSR behavior is implemented.'}, 'function_model': {'purpose': 'Cycle-independent architectural contract for Gray counting, clear/reset semantics, and wrap pulse behavior.', 'state_variables': [{'name': 'gray_state', 'source': 'io_list.interfaces.status.gray_value', 'reset': 0, 'description': 'Architectural Gray counter register.'}, {'name': 'bin_state', 'source': 'derived(gray_state)', 'reset': 0, 'description': 'Decoded binary state derived from gray_state.'}, {'name': 'done_state', 'source': 'io_list.interfaces.status.done', 'reset': 0, 'description': 'One-cycle completion pulse state.'}], 'transactions': [{'id': 'GC_TXN_RESET', 'name': 'asynchronous_reset_assert', 'preconditions': ['rst_n == 0'], 'inputs': ['rst_n'], 'outputs': ['gray_value == 0', 'bin_value == 0', 'done == 0'], 'side_effects': ['gray_state set to 0 immediately on reset assertion', 'done_state cleared'], 'output_rules': [{'name': 'gray_value_reset', 'expr': '0', 'width': 'WIDTH', 'port': 'gray_value'}, {'name': 'bin_value_reset', 'expr': '0', 'width': 'WIDTH', 'port': 'bin_value'}, {'name': 'done_reset', 'expr': '0', 'width': 1, 'port': 'done'}]}, {'id': 'GC_TXN_CLEAR', 'name': 'synchronous_clear', 'preconditions': ['rst_n == 1', 'clear sampled high on rising clock edge'], 'inputs': ['clear'], 'outputs': ['gray_value == 0 after edge', 'bin_value == 0 after edge', 'done == 0 after edge'], 'side_effects': ['gray_state overwritten with 0', 'done_state cleared'], 'output_rules': [{'name': 'gray_value_clear', 'expr': '0', 'width': 'WIDTH', 'port': 'gray_value'}, {'name': 'bin_value_clear', 'expr': '0', 'width': 'WIDTH', 'port': 'bin_value'}, {'name': 'done_clear', 'expr': '0', 'width': 1, 'port': 'done'}]}, {'id': 'GC_TXN_ADVANCE', 'name': 'advance_one_gray_step', 'preconditions': ['rst_n == 1', 'clear == 0 on sampled edge', 'enable == 1 on sampled edge'], 'inputs': ['enable', 'current gray_state'], 'outputs': ['next binary state equals (current bin_state + 1) mod 2^WIDTH', 'next gray_value equals bin_to_gray(next binary state)', 'bin_value equals gray_to_bin(gray_value) at all observable times'], 'side_effects': ['gray_state updates to next_gray', 'done_state set to 1 iff current bin_state is max value; else 0'], 'error_cases': [{'condition': 'WIDTH < 2', 'result': 'Configuration error; synthesis/test should fail parameter constraint checks'}], 'output_rules': [{'name': 'gray_advance', 'expr': '((bin_state + 1) ^ ((bin_state + 1) >> 1)) & ((1<<WIDTH)-1)', 'width': 'WIDTH', 'port': 'gray_value'}, {'name': 'bin_observe', 'expr': 'gray_to_bin(gray_value)', 'width': 'WIDTH', 'port': 'bin_value'}, {'name': 'done_wrap', 'expr': '(1 if bin_state == ((1<<WIDTH)-1) else 0)', 'width': 1, 'port': 'done'}]}, {'id': 'GC_TXN_HOLD', 'name': 'hold_state', 'preconditions': ['rst_n == 1', 'clear == 0 on sampled edge', 'enable == 0 on sampled edge'], 'inputs': ['enable'], 'outputs': ['gray_value remains unchanged', 'bin_value remains decode(gray_value)', 'done == 0'], 'side_effects': ['done_state forced low in non-wrap hold cycles'], 'output_rules': [{'name': 'gray_hold', 'expr': 'gray_state', 'width': 'WIDTH', 'port': 'gray_value'}, {'name': 'bin_hold', 'expr': 'gray_to_bin(gray_state)', 'width': 'WIDTH', 'port': 'bin_value'}, {'name': 'done_hold', 'expr': '0', 'width': 1, 'port': 'done'}]}], 'invariants': ['gray_value is always a legal WIDTH-bit Gray encoding of bin_state.', 'bin_value always equals gray_to_bin(gray_value) combinationally.', 'done is asserted for at most one consecutive cycle per wrap event.', 'clear has priority over enable on sampled clock edges.', 'reset dominates all synchronous controls when asserted.'], 'reference_model_hint': 'Scoreboard model maintains binary golden state, derives gray as g=b^(b>>1), decodes DUT gray_value each cycle, and checks done pulse only on max->0 wrap.'}, 'cycle_model': {'purpose': 'Cycle-accurate control/latency contract for sampled inputs and registered outputs.', 'executable': 'python', 'clock': 'clk', 'reset': {'assertion': 'rst_n low asynchronously clears gray_value and done.', 'deassertion': 'first functional sample occurs on first rising edge after rst_n returns high.'}, 'latency': {'control_to_state_update': {'min_cycles': 1, 'max_cycles': 1, 'description': 'enable/clear sampled on edge', 'new gray_value visible after that edge.': None}, 'gray_to_bin_observation': {'min_cycles': 0, 'max_cycles': 0, 'description': 'bin_value is combinational decode of current gray_value.'}, 'done_pulse_width': {'min_cycles': 1, 'max_cycles': 1, 'description': 'done pulse is exactly one cycle on wrap event.'}}, 'handshake_rules': [{'signal': 'enable', 'rule': 'Sampled only on rising clock edge; no combinational feedback obligations.'}, {'signal': 'clear', 'rule': 'If high on rising edge', 'clear transaction executes and masks enable advance for that edge.': None}, {'signal': 'rst_n', 'rule': 'Asynchronous assertion immediately clears state; synchronous behavior resumes after deassertion and next rising edge.'}], 'pipeline': [{'stage': 'S0_SAMPLE', 'cycle': 'N', 'action': 'Sample rst_n/clear/enable and current gray_state.'}, {'stage': 'S1_COMPUTE', 'cycle': 'N', 'action': 'Compute next binary/Gray and wrap flag combinationally.'}, {'stage': 'S2_COMMIT', 'cycle': 'N_to_Nplus1', 'action': 'Commit gray register and done pulse register at rising edge according to priority reset>clear>enable>hold.'}, {'stage': 'S3_OBSERVE', 'cycle': 'Nplus1', 'action': 'Observe updated gray_value and combinational bin_value decode.'}], 'ordering': ['Asynchronous reset effect precedes any synchronous clear/enable action while rst_n is low.', 'Within a rising-edge sample, clear decision is evaluated before enable advance.', 'done update is ordered with gray register commit from the same sampled edge.'], 'backpressure': ['No ready/valid interface; design is always able to sample control each clock.'], 'observability': ['Every function_model transaction maps to S0..S3 progression with deterministic one-cycle state commit.'], 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; FunctionalModel remains the behavioral oracle.', 'performance': {'frequency_mhz': 200, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}, 'depth': {'pipeline_stages': 3, 'queue_depth': 1, 'description': 'Default accept/evaluate/observe cycle model depth'}}}, 'fcov_bins': [{'id': 'SC01_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC01', 'description': 'reset contract'}, {'id': 'SC02_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC02', 'description': 'primary approved behavior'}, {'id': 'SC03_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC03', 'description': 'cycle handshake and backpressure'}, {'id': 'SC04_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC04', 'description': 'error and recovery policy'}, {'id': 'SC05_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC05', 'description': 'debug and trace observability'}, {'id': 'SC06_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC06', 'description': 'function_model transaction GC_TXN_RESET'}, {'id': 'SC07_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC07', 'description': 'function_model transaction GC_TXN_CLEAR'}, {'id': 'SC08_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC08', 'description': 'function_model transaction GC_TXN_ADVANCE'}, {'id': 'SC09_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC09', 'description': 'function_model transaction GC_TXN_HOLD'}, {'id': 'fcov_txn_reset', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.GC_TXN_RESET', 'source_ref': 'function_model.transactions.GC_TXN_RESET', 'description': 'Reset transaction observed'}, {'id': 'fcov_txn_clear', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.GC_TXN_CLEAR', 'source_ref': 'function_model.transactions.GC_TXN_CLEAR', 'description': 'Clear transaction observed'}, {'id': 'fcov_txn_advance', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.GC_TXN_ADVANCE', 'source_ref': 'function_model.transactions.GC_TXN_ADVANCE', 'description': 'Advance transaction observed'}, {'id': 'fcov_txn_hold', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.GC_TXN_HOLD', 'source_ref': 'function_model.transactions.GC_TXN_HOLD', 'description': 'Hold transaction observed'}, {'id': 'ccov_pipe_sample', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': 'Sample stage hit'}, {'id': 'ccov_pipe_commit', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline', 'source_ref': 'cycle_model.pipeline', 'description': 'Commit stage hit'}, {'id': 'ccov_order_clear_priority', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering', 'source_ref': 'cycle_model.ordering', 'description': 'Clear priority observed'}, {'id': 'ccov_done_one_cycle', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.done_pulse_width', 'source_ref': 'cycle_model.latency.done_pulse_width', 'description': 'Done pulse constrained to one cycle'}, {'id': 'function_asynchronous_reset_assert', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.gc_txn_reset', 'description': 'asynchronous_reset_assert'}, {'id': 'function_synchronous_clear', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.gc_txn_clear', 'description': 'synchronous_clear'}, {'id': 'function_advance_one_gray_step', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.gc_txn_advance', 'description': 'advance_one_gray_step'}, {'id': 'function_hold_state', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.gc_txn_hold', 'description': 'hold_state'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'enable', 'rule': 'Sampled only on rising clock edge; no combinational feedback obligations.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'clear', 'rule': 'If high on rising edge', 'clear transaction executes and masks enable advance for that edge.': None}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'rst_n', 'rule': 'Asynchronous assertion immediately clears state; synchronous behavior resumes after deassertion and next rising edge.'}"}, {'id': 'cycle_latency_control_to_state_update', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.control_to_state_update', 'source_ref': 'cycle_model.latency.control_to_state_update', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'enable/clear sampled on edge', 'new gray_value visible after that edge.': None}"}, {'id': 'cycle_latency_gray_to_bin_observation', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.gray_to_bin_observation', 'source_ref': 'cycle_model.latency.gray_to_bin_observation', 'description': "{'min_cycles': 0, 'max_cycles': 0, 'description': 'bin_value is combinational decode of current gray_value.'}"}, {'id': 'cycle_latency_done_pulse_width', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.done_pulse_width', 'source_ref': 'cycle_model.latency.done_pulse_width', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'done pulse is exactly one cycle on wrap event.'}"}, {'id': 'cycle_pipeline_s0_sample', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Sample rst_n/clear/enable and current gray_state.'}, {'id': 'cycle_pipeline_s1_compute', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Compute next binary/Gray and wrap flag combinationally.'}, {'id': 'cycle_pipeline_s2_commit', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Commit gray register and done pulse register at rising edge according to priority reset>clear>enable>hold.'}, {'id': 'cycle_pipeline_s3_observe', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Observe updated gray_value and combinational bin_value decode.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Asynchronous reset effect precedes any synchronous clear/enable action while rst_n is low.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'Within a rising-edge sample, clear decision is evaluated before enable advance.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'done update is ordered with gray register commit from the same sampled edge.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No ready/valid interface; design is always able to sample control each clock.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 3, 'queue_depth': 1, 'description': 'Default accept/evaluate/observe cycle model depth'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '200'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}"}, {'id': 'fsm_control_reset_to_idle_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[0]', 'source_ref': 'fsm.control.transitions[0]', 'description': 'rst_n deasserted and first rising edge observed'}, {'id': 'fsm_control_idle_to_cleared_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[1]', 'source_ref': 'fsm.control.transitions[1]', 'description': 'clear sampled high'}, {'id': 'fsm_control_idle_to_run_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[2]', 'source_ref': 'fsm.control.transitions[2]', 'description': 'enable sampled high and clear low'}, {'id': 'fsm_control_run_to_wrap_pulse_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[3]', 'source_ref': 'fsm.control.transitions[3]', 'description': 'advance event causes max->0 wrap'}, {'id': 'fsm_control_run_to_idle_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[4]', 'source_ref': 'fsm.control.transitions[4]', 'description': 'enable sampled low and clear low'}, {'id': 'fsm_control_wrap_pulse_to_run_5', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[5]', 'source_ref': 'fsm.control.transitions[5]', 'description': 'enable remains high after one pulse cycle'}, {'id': 'fsm_control_wrap_pulse_to_idle_6', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[6]', 'source_ref': 'fsm.control.transitions[6]', 'description': 'enable low after pulse'}, {'id': 'fsm_control_cleared_to_idle_7', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.control.transitions[7]', 'source_ref': 'fsm.control.transitions[7]', 'description': 'clear low on next edge'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_PARAM_WIDTH', 'condition': 'WIDTH < 2', 'architectural_effect': 'Build-time configuration error'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_PROTOCOL_RESET_GLITCH', 'condition': 'rst_n unknown or glitching', 'architectural_effect': 'DV protocol assertion failure'}"}]}
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
        known_names.update({"read_mux", "reduction_or"})
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
