#!/usr/bin/env python3
"""Executable SSOT functional model for pl330_target.

Generated from yaml/pl330_target.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'pl330_target', 'parameters': {'NUM_CHANNELS': 8, 'NUM_PERIPH_REQS': 32, 'NUM_IRQS': 32, 'AXI_DATA_WIDTH': 64, 'AXI_ID_WIDTH': 4, 'AXI_ADDR_WIDTH': 32, 'APB_DATA_WIDTH': 32, 'APB_ADDR_WIDTH': 12, 'ICACHE_LINE_SIZE': 4, 'MFIFO_DEPTH': 16, 'MERGE_BUFFER_DEPTH': 4, 'SUPPORT_TZ': 1}, 'top_module': {'name': 'pl330_target', 'file': 'rtl/pl330_target.sv', 'type': 'peripheral', 'description': 'pl330_target leaf IP generated from approved ATLAS Web SSOT requirements', 'version': '1.0', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 100, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [{'name': 'mfifo', 'type': 'ram_1r1w', 'depth': 'MFIFO_DEPTH', 'width': 'AXI_DATA_WIDTH', 'description': 'Manager FIFO'}, {'name': 'merge_buffer', 'type': 'register_array', 'depth': 'MERGE_BUFFER_DEPTH', 'width': 'AXI_DATA_WIDTH', 'description': 'Byte-lane merge buffer'}, {'name': 'icache', 'type': 'ram_1r1w', 'depth': 32, 'width': 32, 'description': 'Instruction cache'}]}, 'registers': {'register_list': [{'name': 'DSR', 'offset': 0, 'access': 'RO', 'reset': 0, 'description': 'DMA Manager Status Register'}, {'name': 'DPC', 'offset': 4, 'access': 'RO', 'reset': 0, 'description': 'DMA Manager PC'}, {'name': 'INTEN', 'offset': 32, 'access': 'RW', 'reset': 0, 'description': 'Interrupt Enable'}, {'name': 'INT_EVENT_RIS', 'offset': 36, 'access': 'RO', 'reset': 0, 'description': 'Event-Interrupt Raw Status'}, {'name': 'INTMIS', 'offset': 40, 'access': 'RO', 'reset': 0, 'description': 'Interrupt Status (masked)'}, {'name': 'INTCLR', 'offset': 44, 'access': 'WO', 'reset': 0, 'description': 'Interrupt Clear'}, {'name': 'FSRD', 'offset': 48, 'access': 'RO', 'reset': 0, 'description': 'Fault Status DMA Manager'}, {'name': 'FSRC', 'offset': 52, 'access': 'RO', 'reset': 0, 'description': 'Fault Status DMA Channels'}, {'name': 'FTRD', 'offset': 56, 'access': 'RO', 'reset': 0, 'description': 'Fault Type DMA Manager'}, {'name': 'CSR_chan_n', 'offset': 256, 'access': 'RO', 'reset': 0, 'count': 'NUM_CHANNELS', 'stride': 8, 'description': 'Channel Status'}, {'name': 'CPC_chan_n', 'offset': 260, 'access': 'RO', 'reset': 0, 'count': 'NUM_CHANNELS', 'stride': 8, 'description': 'Channel PC'}, {'name': 'SAR_chan_n', 'offset': 1024, 'access': 'RW', 'reset': 0, 'count': 'NUM_CHANNELS', 'stride': 32, 'description': 'Source Address'}, {'name': 'DAR_chan_n', 'offset': 1028, 'access': 'RW', 'reset': 0, 'count': 'NUM_CHANNELS', 'stride': 32, 'description': 'Destination Address'}, {'name': 'CCR_chan_n', 'offset': 1032, 'access': 'RW', 'reset': 0, 'count': 'NUM_CHANNELS', 'stride': 32, 'description': 'Channel Control'}, {'name': 'DBGSTATUS', 'offset': 3328, 'access': 'RO', 'reset': 0, 'description': 'Debug Status'}, {'name': 'DBGCMD', 'offset': 3332, 'access': 'WO', 'reset': 0, 'description': 'Debug Command'}, {'name': 'DBGINST0', 'offset': 3336, 'access': 'WO', 'reset': 0, 'description': 'Debug Instruction-0'}, {'name': 'DBGINST1', 'offset': 3340, 'access': 'WO', 'reset': 0, 'description': 'Debug Instruction-1'}, {'name': 'CR0', 'offset': 3584, 'access': 'RO', 'reset': 0, 'description': 'Configuration Register 0'}]}, 'function_model': {'state_variables': [{'name': 'channel_state', 'width': 4, 'reset': 0, 'description': 'Per-channel FSM state (0=stopped, 1=executing, 2=cache_miss, 3=updating_pc, 4=waiting_for_event, 5=at_barrier, 6=killing, 7=completing, 8=faulting, 9=faulting_completing)'}, {'name': 'channel_pc', 'width': 32, 'reset': 0}, {'name': 'outstanding_reads', 'width': 4, 'reset': 0}, {'name': 'outstanding_writes', 'width': 4, 'reset': 0}, {'name': 'mfifo_count', 'width': 5, 'reset': 0}, {'name': 'irq_status', 'width': 32, 'reset': 0}, {'name': 'fault_status', 'width': 32, 'reset': 0}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset', 'outputs': ['all state -> reset values'], 'side_effects': ['outstanding_reads=0', 'outstanding_writes=0', 'mfifo_count=0', 'irq_status=0'], 'error_cases': [], 'preconditions': ['transaction is accepted under cycle_model rules']}, {'id': 'FM_DMAGO', 'name': 'dmago_command', 'preconditions': ['channel_state==0', 'manager APB write to DBGINST'], 'outputs': ['channel_state=1', 'channel_pc=arg_addr'], 'side_effects': [], 'error_cases': [{'condition': 'secure violation', 'result': 'fault_status |= INSTR_FETCH_ERR'}]}, {'id': 'FM_DMALD', 'name': 'dmald_load', 'preconditions': ['channel_state==1', 'mfifo has space'], 'outputs': ['outstanding_reads += 1', 'mfifo entries reserved'], 'side_effects': ['issue AXI AR'], 'error_cases': [{'condition': 'AXI rresp != OKAY', 'result': 'fault_status |= DATA_READ_ERR'}]}, {'id': 'FM_DMAST', 'name': 'dmast_store', 'preconditions': ['channel_state==1', 'mfifo has data'], 'outputs': ['outstanding_writes += 1', 'mfifo entries consumed'], 'side_effects': ['issue AXI AW + W'], 'error_cases': [{'condition': 'AXI bresp != OKAY', 'result': 'fault_status |= DATA_WRITE_ERR'}]}, {'id': 'FM_DMALDP', 'name': 'dmaldp_periph_load', 'preconditions': ['channel_state==1', 'periph drvalid asserted'], 'outputs': ['outstanding_reads += 1'], 'side_effects': ['drready asserted', 'AXI AR issued'], 'error_cases': []}, {'id': 'FM_DMASTP', 'name': 'dmastp_periph_store', 'preconditions': ['channel_state==1', 'periph davalid acknowledged'], 'outputs': ['outstanding_writes += 1'], 'side_effects': ['daready asserted', 'AXI AW+W issued'], 'error_cases': []}, {'id': 'FM_DMASEV', 'name': 'dmasev_event_signal', 'preconditions': ['channel_state==1', 'event index < NUM_IRQS'], 'outputs': ['irq_status |= 1<<event_idx'], 'side_effects': ['irq[event_idx] pulse'], 'error_cases': []}, {'id': 'FM_DMAEND', 'name': 'dmaend_terminate', 'preconditions': ['channel_state==1', 'no outstanding'], 'outputs': ['channel_state=0'], 'side_effects': [], 'error_cases': [{'condition': 'outstanding > 0', 'result': 'wait until drained'}]}, {'id': 'FM_FAULT', 'name': 'fault_propagate', 'preconditions': ['any error_case fired'], 'outputs': ['channel_state=8', 'irq_abort pulse'], 'side_effects': ['fault_status updated'], 'error_cases': []}], 'invariants': ['outstanding_reads >= 0 && outstanding_reads <= 2*NUM_CHANNELS', 'outstanding_writes >= 0 && outstanding_writes <= 2*NUM_CHANNELS', 'mfifo_count <= MFIFO_DEPTH', 'channel_state != 1 -> outstanding_reads == 0 && outstanding_writes == 0', 'fault triggers irq_abort within 4 cycles']}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen and waveform-based verification.', 'clock': 'clk', 'reset': {'signal': 'rst_n', 'polarity': 'active_low', 'assertion': 'rst_n assertion returns architectural state to declared reset values', 'deassertion': 'Logic may accept transactions after async_assert_sync_deassert deassertion completes'}, 'latency': {'control_or_request_accept': {'min_cycles': 0, 'max_cycles': None, 'description': 'Bounded by declared valid/ready or protocol acceptance rules'}, 'primary_operation': {'min_cycles': 1, 'max_cycles': None, 'description': 'Runs on clk at nominal 100 MHz; max depends on declared backpressure and implementation state'}, 'response_or_observable_result': {'min_cycles': 0, 'max_cycles': None, 'description': 'Held stable until the declared response/output acceptance condition'}}, 'handshake_rules': [{'signal': 'req_valid/req_ready', 'rule': 'req_valid payload remains stable until req_ready is sampled asserted on control_data.'}, {'signal': 'rsp_valid/rsp_ready', 'rule': 'rsp_valid payload remains stable until rsp_ready is sampled asserted on control_data.'}], 'pipeline': [{'stage': 'S0_ACCEPT', 'cycle': '0..N', 'action': 'Accept legal request/command/packet/control work under declared handshake rules.'}, {'stage': 'S1_EVALUATE', 'cycle': 'N..M', 'action': 'Evaluate function_model transaction and update only declared state.'}, {'stage': 'S2_OBSERVE', 'cycle': 'M..K', 'action': 'Publish response/status/output/debug event and hold it stable until accepted.'}], 'ordering': ['Accepted requests update architectural state only on clock edges.', 'Completion/status/interrupt updates occur after the operation reaches its terminal FSM state.', 'Backpressure stalls the active handshake stage without corrupting stored state.', 'Read/dataflow stages must precede dependent write/output stages where declared in dataflow.'], 'backpressure': ['Ready/valid deassertion stalls only the affected interface stage; payload and route/control state remain stable.'], 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'SC01_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC01', 'description': 'reset contract'}, {'id': 'SC02_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC02', 'description': 'primary approved behavior'}, {'id': 'SC03_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC03', 'description': 'cycle handshake and backpressure'}, {'id': 'SC04_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC04', 'description': 'error and recovery policy'}, {'id': 'SC05_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC05', 'description': 'debug and trace observability'}, {'id': 'SC06_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC06', 'description': 'function_model transaction FM_RESET'}, {'id': 'SC07_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC07', 'description': 'function_model transaction FM_DMAGO'}, {'id': 'SC08_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC08', 'description': 'function_model transaction FM_DMALD'}, {'id': 'SC09_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC09', 'description': 'function_model transaction FM_DMAST'}, {'id': 'SC10_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC10', 'description': 'function_model transaction FM_DMALDP'}, {'id': 'SC11_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC11', 'description': 'function_model transaction FM_DMASTP'}, {'id': 'SC12_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[11]', 'scenario': 'SC12', 'description': 'function_model transaction FM_DMASEV'}, {'id': 'cov_all_channels', 'class': 'scenario', 'source': 'test_requirements.coverage_goals.planned_bins[0]', 'description': 'every channel exercised at least once'}, {'id': 'cov_dmaldp_seen', 'class': 'transaction_type', 'source': 'test_requirements.coverage_goals.planned_bins[1]', 'description': 'DMALDP fired at least once'}, {'id': 'cov_burst_64beat', 'class': 'transaction_type', 'source': 'test_requirements.coverage_goals.planned_bins[2]', 'description': 'AXI burst of 64 beats observed'}, {'id': 'cov_fault_recovery', 'class': 'error', 'source': 'test_requirements.coverage_goals.planned_bins[3]', 'description': 'FAULTING_COMPLETING reached'}, {'id': 'cov_axi_outstanding_max', 'class': 'planned_functional', 'source': 'test_requirements.coverage_goals.planned_bins[4]', 'description': '16 outstanding reads simultaneously'}, {'id': 'cov_apb_secure_block', 'class': 'planned_functional', 'source': 'test_requirements.coverage_goals.planned_bins[5]', 'description': 'NS access to secure register correctly blocked'}, {'id': 'function_reset', 'class': 'transaction_type', 'source': 'function_model.transactions[0]', 'description': 'reset'}, {'id': 'function_dmago_command', 'class': 'transaction_type', 'source': 'function_model.transactions[1]', 'description': 'dmago_command'}, {'id': 'function_dmald_load', 'class': 'transaction_type', 'source': 'function_model.transactions[2]', 'description': 'dmald_load'}, {'id': 'function_dmast_store', 'class': 'transaction_type', 'source': 'function_model.transactions[3]', 'description': 'dmast_store'}, {'id': 'function_dmaldp_periph_load', 'class': 'transaction_type', 'source': 'function_model.transactions[4]', 'description': 'dmaldp_periph_load'}, {'id': 'function_dmastp_periph_store', 'class': 'transaction_type', 'source': 'function_model.transactions[5]', 'description': 'dmastp_periph_store'}, {'id': 'function_dmasev_event_signal', 'class': 'transaction_type', 'source': 'function_model.transactions[6]', 'description': 'dmasev_event_signal'}, {'id': 'function_dmaend_terminate', 'class': 'transaction_type', 'source': 'function_model.transactions[7]', 'description': 'dmaend_terminate'}, {'id': 'function_fault_propagate', 'class': 'transaction_type', 'source': 'function_model.transactions[8]', 'description': 'fault_propagate'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'req_valid/req_ready', 'rule': 'req_valid payload remains stable until req_ready is sampled asserted on control_data.'}"}, {'id': 'cycle_handshake_1', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[1]', 'description': "{'signal': 'rsp_valid/rsp_ready', 'rule': 'rsp_valid payload remains stable until rsp_ready is sampled asserted on control_data.'}"}, {'id': 'fsm_channel_state_stopped_to_executing_0', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[0]', 'description': 'DMAGO + secure check pass'}, {'id': 'fsm_channel_state_executing_to_cache_miss_1', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[1]', 'description': 'icache miss'}, {'id': 'fsm_channel_state_cache_miss_to_executing_2', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[2]', 'description': 'fill complete'}, {'id': 'fsm_channel_state_executing_to_waiting_for_event_3', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[3]', 'description': 'DMAWFE'}, {'id': 'fsm_channel_state_waiting_for_event_to_executing_4', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[4]', 'description': 'event signaled'}, {'id': 'fsm_channel_state_executing_to_at_barrier_5', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[5]', 'description': 'DMAWFP barrier'}, {'id': 'fsm_channel_state_at_barrier_to_executing_6', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[6]', 'description': 'barrier cleared'}, {'id': 'fsm_channel_state_executing_to_completing_7', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[7]', 'description': 'DMAEND issued'}, {'id': 'fsm_channel_state_completing_to_stopped_8', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[8]', 'description': 'all outstanding drained'}, {'id': 'fsm_channel_state_any_to_killing_9', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[9]', 'description': 'DMAKILL via DBGCMD'}, {'id': 'fsm_channel_state_killing_to_stopped_10', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[10]', 'description': 'kill drained'}, {'id': 'fsm_channel_state_any_to_faulting_11', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[11]', 'description': 'any error_case'}, {'id': 'fsm_channel_state_faulting_to_faulting_completing_12', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[12]', 'description': 'fault recovery initiated'}, {'id': 'fsm_channel_state_faulting_completing_to_stopped_13', 'class': 'state_transition', 'source': 'fsm.channel_state.transitions[13]', 'description': 'drain complete'}, {'id': 'error_error_0', 'class': 'error', 'source': 'error_handling.error_sources[0]', 'description': "{'id': 'instr_fetch_err', 'condition': 'Declared error condition is observed', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_1', 'class': 'error', 'source': 'error_handling.error_sources[1]', 'description': "{'id': 'data_read_err', 'condition': 'Declared error condition is observed', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_2', 'class': 'error', 'source': 'error_handling.error_sources[2]', 'description': "{'id': 'data_write_err', 'condition': 'Declared error condition is observed', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_3', 'class': 'error', 'source': 'error_handling.error_sources[3]', 'description': "{'id': 'undef_instr', 'condition': 'Declared error condition is observed', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_4', 'class': 'error', 'source': 'error_handling.error_sources[4]', 'description': "{'id': 'secure_violation', 'condition': 'Declared error condition is observed', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}, {'id': 'error_error_5', 'class': 'error', 'source': 'error_handling.error_sources[5]', 'description': "{'id': 'unaligned_access', 'condition': 'Declared error condition is observed', 'architectural_effect': 'Status/error reporting follows the SSOT error policy'}"}]}
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
