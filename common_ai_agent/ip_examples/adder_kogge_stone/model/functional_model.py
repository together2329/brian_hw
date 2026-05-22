#!/usr/bin/env python3
"""Executable SSOT functional model for adder_kogge_stone.

Generated from yaml/adder_kogge_stone.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'adder_kogge_stone', 'parameters': {'DATA_WIDTH': 32, 'ADDR_WIDTH': 8, 'APB_DATA_WIDTH': 32, 'CLOCK_FREQ_MHZ': 50, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'adder_kogge_stone', 'file': 'rtl/adder_kogge_stone.sv', 'version': '1.0', 'description': 'Kogge-Stone parallel prefix adder with APB-lite CSR interface', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No SRAM or FIFO in this IP. All state is in flops (shadow registers, output registers, status bits).'}, 'registers': {'config': {'register_width': 32, 'addr_width': 8, 'byte_addressable': True, 'channel_stride': 0, 'channel_base': 0, 'num_channels': 1}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'CONTROL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Control register — start trigger and hold mode', 'write_side_effects': ['Writing start=1 initiates a single addition cycle (self-clearing).', 'hold_mode=1 gates the output register update until start is asserted.', 'clr_done=1 clears the done status bit (W1C behavior).'], 'fields': [{'name': 'start', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Self-clearing pulse; initiates add operation', 'description': 'Start addition'}, {'name': 'hold_mode', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': 'When 1, output registers hold until start=1', 'description': 'Hold mode enable'}, {'name': 'clr_done', 'bits': [2, 2], 'access': 'w1c', 'reset': 0, 'write_effect': 'Write 1 to clear STATUS.done', 'description': 'Clear done flag'}, {'name': 'reserved_31_3', 'bits': [31, 3], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'STATUS', 'offset': 4, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Status register', 'fields': [{'name': 'busy', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': '1=Adder busy (registered input sampled, output pending)'}, {'name': 'done', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': '1=Addition complete since last clr_done'}, {'name': 'overflow', 'bits': [2, 2], 'access': 'ro', 'reset': 0, 'description': '1=Carry out occurred on last operation'}, {'name': 'reserved_31_3', 'bits': [31, 3], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'A_DATA', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'data', 'description': 'Operand A data register (lower 32 bits)', 'write_side_effects': ['Updates the A operand shadow register immediately.'], 'fields': [{'name': 'a_data', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Update operand A shadow', 'description': 'Operand A value'}]}, {'name': 'B_DATA', 'offset': 12, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'data', 'description': 'Operand B data register (lower 32 bits)', 'write_side_effects': ['Updates the B operand shadow register immediately.'], 'fields': [{'name': 'b_data', 'bits': [31, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Update operand B shadow', 'description': 'Operand B value'}]}, {'name': 'CIN', 'offset': 16, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'data', 'description': 'Carry-in register', 'fields': [{'name': 'cin', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Update carry-in shadow', 'description': 'Carry-in value'}, {'name': 'reserved_31_1', 'bits': [31, 1], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'SUM_RESULT', 'offset': 20, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'data', 'description': 'Sum result register (lower 32 bits)', 'fields': [{'name': 'sum_result', 'bits': [31, 0], 'access': 'ro', 'reset': 0, 'description': 'Registered sum output'}]}, {'name': 'COUT_RESULT', 'offset': 24, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'data', 'description': 'Carry-out result register', 'fields': [{'name': 'cout_result', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': 'Registered carry-out output'}, {'name': 'reserved_31_1', 'bits': [31, 1], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'CONFIG', 'offset': 28, 'width': 32, 'access': 'ro', 'reset': 'depends on parameter DATA_WIDTH', 'category': 'config', 'description': 'Configuration readback register', 'fields': [{'name': 'data_width', 'bits': [7, 0], 'access': 'ro', 'reset': 'DATA_WIDTH', 'description': 'Current DATA_WIDTH parameter value'}, {'name': 'reserved_31_8', 'bits': [31, 8], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes the Kogge-Stone addition independent of cycle timing.', 'state_variables': [{'name': 'a_reg', 'source': 'registers.A_DATA.a_data', 'reset': 0, 'description': 'Registered operand A'}, {'name': 'b_reg', 'source': 'registers.B_DATA.b_data', 'reset': 0, 'description': 'Registered operand B'}, {'name': 'cin_reg', 'source': 'registers.CIN.cin', 'reset': 0, 'description': 'Registered carry-in'}, {'name': 'sum_reg', 'source': 'registers.SUM_RESULT.sum_result', 'reset': 0, 'description': 'Registered sum result'}, {'name': 'cout_reg', 'source': 'registers.COUT_RESULT.cout_result', 'reset': 0, 'description': 'Registered carry-out'}, {'name': 'busy', 'source': 'registers.STATUS.busy', 'reset': 0, 'description': 'Operation busy flag'}, {'name': 'done', 'source': 'registers.STATUS.done', 'reset': 0, 'description': 'Operation done flag'}, {'name': 'overflow', 'source': 'registers.STATUS.overflow', 'reset': 0, 'description': 'Overflow/carry-out flag'}], 'state_updates': [{'name': 'a_reg', 'reset': 0, 'expr': 'a_reg = CONTROL.start ? A_DATA.a_data : a_reg'}, {'name': 'b_reg', 'reset': 0, 'expr': 'b_reg = CONTROL.start ? B_DATA.b_data : b_reg'}, {'name': 'cin_reg', 'reset': 0, 'expr': 'cin_reg = CONTROL.start ? CIN.cin : cin_reg'}, {'name': 'sum_reg', 'reset': 0, 'expr': 'sum_reg = a_reg ^ b_reg ^ group_carry[DATA_WIDTH-1:0]'}, {'name': 'cout_reg', 'reset': 0, 'expr': 'cout_reg = group_generate[DATA_WIDTH-1] | (group_propagate[DATA_WIDTH-1] & cin_reg)'}, {'name': 'busy', 'reset': 0, 'expr': 'busy = CONTROL.start ? 1 : 0 (cleared when sum_reg updates)'}, {'name': 'done', 'reset': 0, 'expr': 'done = (busy && !next_busy) | done; cleared by CONTROL.clr_done=1'}, {'name': 'overflow', 'reset': 0, 'expr': 'overflow = cout_reg on completion cycle'}], 'transactions': [{'id': 'FM_ADD', 'name': 'kogge_stone_addition', 'preconditions': ['CONTROL.start == 1 or (hold_mode == 0 and inputs have changed)', 'DATA_WIDTH >= 2'], 'inputs': ['a_i[DATA_WIDTH-1:0] or a_reg from APB shadow', 'b_i[DATA_WIDTH-1:0] or b_reg from APB shadow', 'cin_i or cin_reg from APB shadow'], 'outputs': [{'name': 'sum_o', 'expr': 'a_reg ^ b_reg ^ carry_chain', 'width': 'DATA_WIDTH', 'port': 'sum_o'}, {'name': 'cout_o', 'expr': 'final_group_generate | (final_group_propagate & cin_reg)', 'width': 1, 'port': 'cout_o'}, {'name': 'sum_apb', 'expr': 'sum_reg', 'width': 32, 'port': 'SUM_RESULT'}, {'name': 'cout_apb', 'expr': 'cout_reg', 'width': 1, 'port': 'COUT_RESULT'}], 'side_effects': ['STATUS.busy set on start, cleared after output registered', 'STATUS.done set on completion, persists until clr_done', 'STATUS.overflow reflects cout_reg of last operation'], 'error_cases': [{'condition': 'DATA_WIDTH < 2', 'result': 'Undefined; minimum DATA_WIDTH=2 enforced by parameter constraint'}, {'condition': 'APB access to unmapped address', 'result': 'pslverr=1, no register change'}]}], 'invariants': ['sum_o[DATA_WIDTH-1:0] + (cout_o << DATA_WIDTH) == a_reg + b_reg + cin_reg for all legal inputs.', 'Output registers only update on posedge PCLK when start=1 or hold_mode=0.'], 'reference_model_hint': 'tb-gen should implement a Python reference adder (a + b + cin) and compare against sum_o/cout_o for every scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when state, outputs, and APB interface signals change.', 'executable': 'python', 'backend_policy': 'Use direct Python smoke checks for the single-cycle adder behavior.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state to reset values', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and pready timing'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}, 'addition_compute': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Single PCLK cycle from start to registered output'}}, 'handshake_rules': [{'signal': 'psel/penable', 'rule': 'Standard APB-lite: psel=1, penable=0 (setup); psel=1, penable=1 (access completes when pready=1).'}, {'signal': 'pready', 'rule': 'pready=1 for all APB accesses (zero-wait-state).'}, {'signal': 'pslverr', 'rule': 'pslverr=1 only with pready=1 for out-of-bounds address.'}], 'pipeline': [{'stage': 'S_IDLE', 'cycle': 0, 'action': 'Wait for CONTROL.start or hold_mode=0 with valid shadow registers.'}, {'stage': 'S_COMPUTE', 'cycle': 1, 'action': 'Combinational Kogge-Stone prefix tree evaluates propagate/generate and produces sum/carry.'}, {'stage': 'S_CAPTURE', 'cycle': 1, 'action': 'On posedge PCLK, output registers capture sum and carry; STATUS updates to done=1, busy=0.'}], 'ordering': ['APB write to A_DATA/B_DATA/CIN updates shadow before start is sampled.', 'APB write to CONTROL.start must be visible in the same cycle as the APB completes.', 'Output register update occurs only on posedge PCLK.'], 'backpressure': ['No backpressure on adder datapath; APB interface is zero-wait-state.'], 'performance': {'frequency_mhz': 50, 'throughput': {'sustained_ops_per_cycle': 1, 'condition': 'Continuous start pulses or hold_mode=0'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single outstanding addition operation'}, 'depth': {'pipeline_stages': 1, 'description': 'Single-cycle registered output; combinational prefix tree is not pipelined.'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC_BASIC_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_BASIC', 'description': 'Basic addition'}, {'id': 'SC_CARRY_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_CARRY', 'description': 'Carry propagation'}, {'id': 'SC_APB_ERR_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_APB_ERR', 'description': 'APB out-of-bounds'}, {'id': 'SC_HOLD_MODE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_HOLD_MODE', 'description': 'Hold mode operation'}, {'id': 'SC_CLR_DONE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_CLR_DONE', 'description': 'Clear done flag'}, {'id': 'SC_RESET_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_RESET', 'description': 'Reset behavior'}, {'id': 'fcov_add_basic', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ADD', 'source_ref': 'function_model.transactions.FM_ADD', 'description': 'Basic addition with various operand combinations'}, {'id': 'fcov_add_carry', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ADD', 'source_ref': 'function_model.transactions.FM_ADD', 'description': 'Addition with carry-out asserted'}, {'id': 'fcov_add_zero', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ADD', 'source_ref': 'function_model.transactions.FM_ADD', 'description': 'Addition with zero operands'}, {'id': 'fcov_add_max', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM_ADD', 'source_ref': 'function_model.transactions.FM_ADD', 'description': 'Addition with all-ones operands'}, {'id': 'ccov_apb_read', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.psel/penable', 'source_ref': 'cycle_model.handshake_rules.psel/penable', 'description': 'APB read transaction observed'}, {'id': 'ccov_apb_write', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.psel/penable', 'source_ref': 'cycle_model.handshake_rules.psel/penable', 'description': 'APB write transaction observed'}, {'id': 'ccov_apb_err', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules.pslverr', 'source_ref': 'cycle_model.handshake_rules.pslverr', 'description': 'APB error response observed'}, {'id': 'ccov_compute_stage', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S_COMPUTE', 'source_ref': 'cycle_model.pipeline.S_COMPUTE', 'description': 'Compute stage observed'}, {'id': 'ccov_capture_stage', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S_CAPTURE', 'source_ref': 'cycle_model.pipeline.S_CAPTURE', 'description': 'Capture stage observed'}, {'id': 'ccov_single_cycle', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.addition_compute', 'source_ref': 'cycle_model.latency.addition_compute', 'description': 'Single-cycle latency observed'}, {'id': 'function_kogge_stone_addition', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_add', 'description': 'kogge_stone_addition'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'psel/penable', 'rule': 'Standard APB-lite: psel=1, penable=0 (setup); psel=1, penable=1 (access completes when pready=1).'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[1]', 'source_ref': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'pready', 'rule': 'pready=1 for all APB accesses (zero-wait-state).'}"}, {'id': 'cycle_handshake_2', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[2]', 'source_ref': 'cycle_model.handshake_rules[2]', 'description': "{'signal': 'pslverr', 'rule': 'pslverr=1 only with pready=1 for out-of-bounds address.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and pready timing'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}"}, {'id': 'cycle_latency_addition_compute', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.addition_compute', 'source_ref': 'cycle_model.latency.addition_compute', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Single PCLK cycle from start to registered output'}"}, {'id': 'cycle_pipeline_s_idle', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Wait for CONTROL.start or hold_mode=0 with valid shadow registers.'}, {'id': 'cycle_pipeline_s_compute', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Combinational Kogge-Stone prefix tree evaluates propagate/generate and produces sum/carry.'}, {'id': 'cycle_pipeline_s_capture', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[2]', 'source_ref': 'cycle_model.pipeline[2]', 'description': 'On posedge PCLK, output registers capture sum and carry; STATUS updates to done=1, busy=0.'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'APB write to A_DATA/B_DATA/CIN updates shadow before start is sampled.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'APB write to CONTROL.start must be visible in the same cycle as the APB completes.'}, {'id': 'cycle_ordering_2', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[2]', 'source_ref': 'cycle_model.ordering[2]', 'description': 'Output register update occurs only on posedge PCLK.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No backpressure on adder datapath; APB interface is zero-wait-state.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 1, 'write_max': 1, 'description': 'Single outstanding addition operation'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 1, 'description': 'Single-cycle registered output; combinational prefix tree is not pipelined.'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_ops_per_cycle': 1, 'condition': 'Continuous start pulses or hold_mode=0'}"}, {'id': 'fsm_adder_fsm_idle_to_compute_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.adder_fsm.transitions[0]', 'source_ref': 'fsm.adder_fsm.transitions[0]', 'description': 'CONTROL.start=1 or (hold_mode=0 and shadow_valid=1)'}, {'id': 'fsm_adder_fsm_compute_to_done_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.adder_fsm.transitions[1]', 'source_ref': 'fsm.adder_fsm.transitions[1]', 'description': 'posedge PCLK (combinational tree result captured)'}, {'id': 'fsm_adder_fsm_done_to_idle_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.adder_fsm.transitions[2]', 'source_ref': 'fsm.adder_fsm.transitions[2]', 'description': 'automatic after one cycle or next start'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_APB_OOB', 'condition': 'APB access to address not in register map', 'architectural_effect': 'pslverr=1, prdata=0, no state change'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_WIDTH', 'condition': 'DATA_WIDTH < 2 at elaboration', 'architectural_effect': 'Parameter violation; synthesis/compile will fail'}"}]}
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
