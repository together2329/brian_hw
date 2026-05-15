#!/usr/bin/env python3
"""Executable SSOT functional model for clkdiv.

Generated from yaml/clkdiv.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'clkdiv', 'parameters': {'DIV_WIDTH': 16, 'RESET_POLARITY': 'active_low', 'CLOCK_FREQ_MHZ': 100}, 'top_module': {'name': 'clkdiv', 'file': 'rtl/clkdiv.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Programmable integer clock divider with APB4 control, glitchless enable, status, and optional terminal interrupt.', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 100, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No RAM, ROM, FIFO, or SRAM macros required; divider uses flops for registers and counter.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 8, 'byte_addressable': True}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and writes have no effect.'}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Divider control register.', 'write_side_effects': ['enable controls whether clk_o toggles; disabling forces clk_o low and clears locked_o.', 'irq_enable gates terminal event interrupt generation.'], 'fields': [{'name': 'enable', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': '1 enables divider, 0 disables and clears active output', 'description': 'Divider enable'}, {'name': 'irq_enable', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': '1 enables irq_o when STATUS.irq_pending is set', 'description': 'Interrupt enable'}, {'name': 'reserved_31_2', 'bits': [31, 2], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'DIVISOR', 'offset': 4, 'width': 32, 'access': 'rw', 'reset': 2, 'category': 'configuration', 'description': 'Programmable divide ratio.', 'write_side_effects': ['Writing divisor stores pending_divisor; value 0 is coerced to 1 for safe behavior.', 'New divisor takes effect on the next counter reload boundary.'], 'fields': [{'name': 'divisor', 'bits': [15, 0], 'access': 'rw', 'reset': 2, 'write_effect': 'Program divide ratio; 0 coerces to 1', 'description': 'Integer divisor value'}, {'name': 'reserved_31_16', 'bits': [31, 16], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'STATUS', 'offset': 8, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Divider status.', 'fields': [{'name': 'running', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': '1 when divider is enabled'}, {'name': 'locked', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': '1 after first valid reload while enabled'}, {'name': 'irq_pending', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'description': 'Terminal-toggle event pending until INTCLR write'}, {'name': 'reserved_31_3', 'bits': [31, 3], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}, {'name': 'INTCLR', 'offset': 12, 'width': 32, 'access': 'wo', 'reset': 0, 'category': 'interrupt', 'description': 'Interrupt clear register.', 'write_side_effects': ['Writing bit0=1 clears STATUS.irq_pending.'], 'fields': [{'name': 'clear_irq', 'bits': [0, 0], 'access': 'wo', 'reset': 0, 'write_effect': 'W1C clear of terminal event pending status', 'description': 'Clear interrupt pending'}, {'name': 'reserved_31_1', 'bits': [31, 1], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved'}]}]}, 'function_model': {'purpose': 'Behavioral contract for programmable clock division independent of APB cycle timing.', 'state_variables': [{'name': 'enable', 'source': 'registers.CTRL.enable', 'reset': 0, 'description': 'Divider enable state'}, {'name': 'pending_divisor', 'source': 'registers.DIVISOR.divisor', 'reset': 2, 'description': 'Software-programmed divisor, with write value 0 coerced to 1'}, {'name': 'active_divisor', 'source': 'clkdiv_core.active_divisor', 'reset': 2, 'description': 'Divisor currently used by the counter'}, {'name': 'counter', 'source': 'clkdiv_core.counter', 'reset': 0, 'description': 'Counts input clock cycles toward terminal count'}, {'name': 'clk_state', 'source': 'clk_o', 'reset': 0, 'description': 'Current divided clock output state'}, {'name': 'irq_pending', 'source': 'registers.STATUS.irq_pending', 'reset': 0, 'description': 'Sticky terminal event interrupt pending bit'}], 'transactions': [{'id': 'FM_DIVIDE', 'name': 'integer_clock_divide', 'preconditions': ['rst_ni is deasserted', 'CTRL.enable == 1', 'active_divisor >= 1'], 'inputs': ['clk_i rising edge', 'active_divisor', 'CTRL.irq_enable'], 'outputs': ['clk_o toggles exactly when counter reaches active_divisor-1', 'locked_o is 1 after the first terminal reload while enabled', 'irq_o is 1 when irq_pending and CTRL.irq_enable are both 1'], 'output_rules': [{'name': 'divided_clock', 'expr': 'terminal_count ? ~clk_state : clk_state', 'width': 1, 'port': 'clk_o'}, {'name': 'lock_indicator', 'expr': 'enable && first_reload_seen', 'width': 1, 'port': 'locked_o'}, {'name': 'interrupt', 'expr': 'irq_pending && irq_enable', 'width': 1, 'port': 'irq_o'}], 'side_effects': ['If counter == active_divisor-1, counter resets to 0 and clk_state toggles.', 'If counter != active_divisor-1, counter increments by one and clk_state is stable.', 'At terminal count, active_divisor loads pending_divisor for the next half-period.', 'At terminal count, irq_pending is set when CTRL.irq_enable=1.', 'When enable=0, counter=0, clk_state=0, locked_o=0.'], 'error_cases': [{'condition': 'APB write to DIVISOR with value 0', 'result': 'pending_divisor is coerced to 1; no pslverr'}, {'condition': 'APB access to unsupported address', 'result': 'pslverr asserted for the access and state is unchanged'}]}], 'invariants': ['clk_o changes only on clk_i rising edges while rst_ni is deasserted.', 'DIVISOR writes do not directly toggle clk_o.', 'Reserved register fields read as zero and ignore writes.', 'irq_pending remains set until INTCLR.clear_irq is written as 1.'], 'reference_model_hint': 'tb-gen should model counter, active_divisor, pending_divisor, clk_state, locked, and irq_pending in Python and compare outputs cycle-by-cycle.'}, 'cycle_model': {'purpose': 'Cycle and handshake contract for APB register access and divider output timing.', 'executable': 'pymtl3', 'backend_policy': 'Use a clocked PyMTL3 model as cycle reference and direct Python smoke checks for divider timing.', 'clock': 'clk_i', 'reset': {'assertion': 'rst_ni low asynchronously clears registers, counter, clk_o, locked_o, and irq_pending to reset values.', 'deassertion': 'State is usable on the first rising edge after synchronized deassertion.'}, 'latency': {'register_read': {'min_cycles': 1, 'max_cycles': 1, 'description': 'APB access completes with pready in the access phase.'}, 'register_write': {'min_cycles': 1, 'max_cycles': 1, 'description': 'APB writes update register storage on completing access phase.'}, 'divisor_update': {'min_cycles': 1, 'max_cycles': None, 'description': 'A new divisor applies at the next terminal count boundary.'}, 'output_toggle': {'min_cycles': 1, 'max_cycles': None, 'description': 'clk_o toggles after active_divisor input clock rising edges while enabled.'}}, 'handshake_rules': [{'signal': 'pready', 'rule': 'pready is asserted for every selected APB access phase; no wait states in baseline.'}, {'signal': 'pslverr', 'rule': 'pslverr is asserted only with pready for unsupported address or illegal access.'}, {'signal': 'prdata', 'rule': 'prdata is stable in the APB read completing access phase.'}, {'signal': 'clk_o', 'rule': 'clk_o toggles only at terminal count on clk_i rising edge and is held low when disabled.'}, {'signal': 'irq_o', 'rule': 'irq_o is combinational/registered reflection of irq_pending && irq_enable and deasserts after INTCLR clear.'}], 'pipeline': [{'stage': 'S0_APB_SETUP', 'cycle': 0, 'action': 'Capture paddr/pwrite context when psel=1 and penable=0.'}, {'stage': 'S1_APB_ACCESS', 'cycle': 1, 'action': 'Complete APB read/write; update CTRL/DIVISOR/INTCLR effects.'}, {'stage': 'S2_COUNT', 'cycle': 'each enabled clk_i edge', 'action': 'Increment counter while counter < active_divisor-1.'}, {'stage': 'S3_TERMINAL', 'cycle': 'terminal edge', 'action': 'Reset counter, toggle clk_o, load pending_divisor, set locked and optional irq_pending.'}, {'stage': 'S4_DISABLE', 'cycle': 'first edge after enable=0', 'action': 'Force counter and clk_o low and clear locked.'}], 'ordering': ['APB DIVISOR writes update pending_divisor before the next core reload boundary.', 'active_divisor changes only in S3_TERMINAL or reset.', 'INTCLR.clear_irq write clears irq_pending no later than the completing APB access edge.'], 'backpressure': ['No backpressure exists on divided_clock outputs; APB baseline has no wait states.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_register_accesses_per_cycle': 0.5, 'condition': 'APB requires setup and access phases'}, 'divider_range': {'min_divisor': 1, 'max_divisor': 65535, 'description': 'DIV_WIDTH=16 baseline'}, 'output_rate': {'half_period_input_cycles': 'active_divisor', 'full_period_input_cycles': '2*active_divisor'}}, 'observability': ['Every function_model transaction maps to S2_COUNT/S3_TERMINAL and a test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC_APB_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_APB', 'description': 'APB register access'}, {'id': 'SC_DIV2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_DIV2', 'description': 'Divide by two baseline'}, {'id': 'SC_DIV_UPDATE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_DIV_UPDATE', 'description': 'Glitchless divisor update'}, {'id': 'SC_IRQ_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_IRQ', 'description': 'Terminal interrupt set and clear'}, {'id': 'SC_DIV_ZERO_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_DIV_ZERO', 'description': 'DIVISOR zero write policy'}, {'id': 'fcov_fm_divide', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DIVIDE', 'source_ref': 'function_model.transactions.FM_DIVIDE', 'description': 'Primary divide transaction observed'}, {'id': 'fcov_div_zero', 'class': 'error_case', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DIVIDE.error_cases.WARN_DIV_ZERO', 'source_ref': 'function_model.transactions.FM_DIVIDE.error_cases.WARN_DIV_ZERO', 'description': 'Zero divisor coercion observed'}, {'id': 'fcov_irq', 'class': 'interrupt', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_DIVIDE.side_effects.terminal_irq', 'source_ref': 'function_model.transactions.FM_DIVIDE.side_effects.terminal_irq', 'description': 'Terminal event interrupt set and clear observed'}, {'id': 'ccov_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_APB_ACCESS', 'source_ref': 'cycle_model.pipeline.S1_APB_ACCESS', 'description': 'APB access completion observed'}, {'id': 'ccov_count', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S2_COUNT', 'source_ref': 'cycle_model.pipeline.S2_COUNT', 'description': 'Counter increment stage observed'}, {'id': 'ccov_terminal', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S3_TERMINAL', 'source_ref': 'cycle_model.pipeline.S3_TERMINAL', 'description': 'Terminal toggle/reload observed'}, {'id': 'ccov_clk_toggle_rule', 'class': 'output_timing', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.clk_o', 'source_ref': 'cycle_model.handshake_rules.clk_o', 'description': 'clk_o toggles only at terminal count'}, {'id': 'ccov_fsm_transitions', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.divider_fsm.transitions', 'source_ref': 'fsm.divider_fsm.transitions', 'description': 'Declared FSM transitions observed'}, {'id': 'function_integer_clock_divide', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_divide', 'description': 'integer_clock_divide'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'pready', 'rule': 'pready is asserted for every selected APB access phase; no wait states in baseline.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'pslverr', 'rule': 'pslverr is asserted only with pready for unsupported address or illegal access.'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'prdata', 'rule': 'prdata is stable in the APB read completing access phase.'}"}, {'id': 'cycle_handshake_3', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[3]', 'source_ref': 'cycle_model.handshake_rules[3]', 'description': "{'signal': 'clk_o', 'rule': 'clk_o toggles only at terminal count on clk_i rising edge and is held low when disabled.'}"}, {'id': 'cycle_handshake_4', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[4]', 'source_ref': 'cycle_model.handshake_rules[4]', 'description': "{'signal': 'irq_o', 'rule': 'irq_o is combinational/registered reflection of irq_pending && irq_enable and deasserts after INTCLR clear.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'APB access completes with pready in the access phase.'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'APB writes update register storage on completing access phase.'}"}, {'id': 'cycle_latency_divisor_update', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.divisor_update', 'source_ref': 'cycle_model.latency.divisor_update', 'description': "{'min_cycles': 1, 'max_cycles': None, 'description': 'A new divisor applies at the next terminal count boundary.'}"}, {'id': 'cycle_latency_output_toggle', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.output_toggle', 'source_ref': 'cycle_model.latency.output_toggle', 'description': "{'min_cycles': 1, 'max_cycles': None, 'description': 'clk_o toggles after active_divisor input clock rising edges while enabled.'}"}, {'id': 'cycle_pipeline_s0_apb_setup', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Capture paddr/pwrite context when psel=1 and penable=0.'}, {'id': 'cycle_pipeline_s1_apb_access', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Complete APB read/write; update CTRL/DIVISOR/INTCLR effects.'}, {'id': 'cycle_pipeline_s2_count', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'Increment counter while counter < active_divisor-1.'}, {'id': 'cycle_pipeline_s3_terminal', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[3]', 'source_ref': 'cycle_model.pipeline[3]', 'description': 'Reset counter, toggle clk_o, load pending_divisor, set locked and optional irq_pending.'}, {'id': 'cycle_pipeline_s4_disable', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[4]', 'source_ref': 'cycle_model.pipeline[4]', 'description': 'Force counter and clk_o low and clear locked.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'APB DIVISOR writes update pending_divisor before the next core reload boundary.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'active_divisor changes only in S3_TERMINAL or reset.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'INTCLR.clear_irq write clears irq_pending no later than the completing APB access edge.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No backpressure exists on divided_clock outputs; APB baseline has no wait states.'}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '100'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_register_accesses_per_cycle': 0.5, 'condition': 'APB requires setup and access phases'}"}, {'id': 'fsm_divider_fsm_disabled_to_running_low_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.divider_fsm.transitions[0]', 'source_ref': 'fsm.divider_fsm.transitions[0]', 'description': 'CTRL.enable=1'}, {'id': 'fsm_divider_fsm_running_low_to_running_high_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.divider_fsm.transitions[1]', 'source_ref': 'fsm.divider_fsm.transitions[1]', 'description': 'counter reaches terminal count'}, {'id': 'fsm_divider_fsm_running_high_to_running_low_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.divider_fsm.transitions[2]', 'source_ref': 'fsm.divider_fsm.transitions[2]', 'description': 'counter reaches terminal count'}, {'id': 'fsm_divider_fsm_running_low_to_disabled_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.divider_fsm.transitions[3]', 'source_ref': 'fsm.divider_fsm.transitions[3]', 'description': 'CTRL.enable=0 or reset asserted'}, {'id': 'fsm_divider_fsm_running_high_to_disabled_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.divider_fsm.transitions[4]', 'source_ref': 'fsm.divider_fsm.transitions[4]', 'description': 'CTRL.enable=0 or reset asserted'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_APB_ADDR', 'condition': 'APB access to unsupported offset', 'architectural_effect': 'pslverr=1 for access; no register state change on illegal write'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_APB_WRITE_RO', 'condition': 'APB write to read-only STATUS', 'architectural_effect': 'pslverr=1 for access; no status mutation'}"}, {'id': 'error_error_2', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[2]', 'source_ref': 'error_handling.error_sources[2]', 'description': "{'id': 'WARN_DIV_ZERO', 'condition': 'DIVISOR write data divisor field is 0', 'architectural_effect': 'pending_divisor coerced to 1 without pslverr'}"}]}
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
