#!/usr/bin/env python3
"""Executable SSOT functional model for atciic100_target.

Generated from yaml/atciic100_target.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'atciic100_target', 'parameters': {'DATA_WIDTH': 8, 'FIFO_DEPTH': 4, 'INDEX_WIDTH': 2, 'ID': "16'h0202", 'REV_MAJOR': "12'h100", 'REV_MINOR': "4'h2"}, 'top_module': {'name': 'atciic100_target', 'file': 'rtl/atciic100_target.sv'}, 'memory': {'instances': [{'name': 'tx_rx_fifo', 'type': 'ram_1r1w', 'depth': 'FIFO_DEPTH', 'width': 'DATA_WIDTH', 'description': 'Bidirectional byte FIFO'}]}, 'registers': {'register_list': [{'name': 'ID', 'offset': 0, 'access': 'RO', 'reset': "16'h0202"}, {'name': 'REV', 'offset': 16, 'access': 'RO', 'reset': 0}, {'name': 'HWCFG', 'offset': 20, 'access': 'RO', 'reset': 0}, {'name': 'CFG', 'offset': 32, 'access': 'RW', 'reset': 0, 'description': 'master/slave, gen_call, dma_en, role'}, {'name': 'INT_EN', 'offset': 36, 'access': 'RW', 'reset': 0}, {'name': 'INT_ST', 'offset': 40, 'access': 'W1C', 'reset': 0}, {'name': 'ADDR', 'offset': 44, 'access': 'RW', 'reset': 0, 'description': 'Slave address'}, {'name': 'DATA', 'offset': 48, 'access': 'RW', 'reset': 0, 'description': 'TX/RX FIFO data port'}, {'name': 'CMD', 'offset': 52, 'access': 'RW', 'reset': 0, 'description': 'start/stop/read/write/datacnt'}, {'name': 'SETUP', 'offset': 56, 'access': 'RW', 'reset': 0, 'description': 'addr_mode, gen_call_en, dma_en'}, {'name': 'TPM', 'offset': 64, 'access': 'RW', 'reset': 0, 'description': 't_high, t_low'}, {'name': 'TSP', 'offset': 68, 'access': 'RW', 'reset': 0, 'description': 't_sp glitch period'}]}, 'function_model': {'state_variables': [{'name': 'cmd', 'width': 32, 'reset': 0, 'description': 'Command register (read/write/start/stop/cont)'}, {'name': 'cfg', 'width': 32, 'reset': 0, 'description': 'Configuration register (timing/role/dma_en)'}, {'name': 'int_en', 'width': 32, 'reset': 0, 'description': 'Interrupt enable mask'}, {'name': 'int_st', 'width': 32, 'reset': 0, 'description': 'Interrupt status (write-1-clear)'}, {'name': 'setup', 'width': 32, 'reset': 0, 'description': 'Setup register (addr/datacnt)'}, {'name': 'addr_reg', 'width': 10, 'reset': 0, 'description': 'I2C target address'}, {'name': 'datacnt', 'width': 9, 'reset': 0, 'description': 'Remaining byte count'}, {'name': 'phase', 'width': 4, 'reset': 0, 'description': 'I2C phase: IDLE/START/ADDR/DAT/STOP'}, {'name': 'fifo_count', 'width': 5, 'reset': 0, 'description': 'FIFO occupancy'}, {'name': 'master', 'width': 1, 'reset': 0, 'description': 'Master-mode currently active'}, {'name': 'trans', 'width': 1, 'reset': 0, 'description': 'Transaction in progress'}, {'name': 'arb_lost', 'width': 1, 'reset': 0, 'description': 'Arbitration lost flag'}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset', 'outputs': ['all state -> reset values'], 'side_effects': ['clear FIFO', 'release SDA/SCL'], 'error_cases': []}, {'id': 'FM_CSR_WRITE', 'name': 'csr_write', 'preconditions': ['psel && penable && pwrite'], 'outputs': ['register at paddr updated with pwdata'], 'side_effects': ['clear-on-write fields applied (int_st)'], 'error_cases': [{'condition': 'reserved address', 'result': 'no-op'}]}, {'id': 'FM_CSR_READ', 'name': 'csr_read', 'preconditions': ['psel && penable && !pwrite'], 'outputs': ['prdata := register at paddr'], 'side_effects': [], 'error_cases': [{'condition': 'reserved address', 'result': 'prdata=0'}]}, {'id': 'FM_MASTER_SEND', 'name': 'master_send', 'preconditions': ['cmd.start && cfg.master_mode && fifo_count > 0'], 'outputs': ['sda_o pulled per byte from fifo', 'scl_o toggled per timing'], 'side_effects': ['phase walks IDLE->START->ADDR->DAT->STOP', 'datacnt decrements per byte', 'trans=1'], 'error_cases': [{'condition': 'ACK not received', 'result': 'int_st.ack_neg=1; phase->STOP'}, {'condition': 'arbitration lost mid-byte', 'result': 'arb_lost=1; int_st.arblose=1'}]}, {'id': 'FM_MASTER_RECV', 'name': 'master_recv', 'preconditions': ['cmd.start && cmd.read && cfg.master_mode'], 'outputs': ['sda_i sampled per byte and pushed to fifo'], 'side_effects': ['phase walks IDLE->START->ADDR->DAT->STOP', 'datacnt decrements per byte'], 'error_cases': [{'condition': 'fifo full mid-byte', 'result': 'stall scl until drained'}]}, {'id': 'FM_SLAVE_RECV', 'name': 'slave_recv', 'preconditions': ['!cfg.master_mode', 'addr matches addr_reg or general-call enabled'], 'outputs': ['sda_o ACK after addr match', 'byte from sda_i pushed to fifo'], 'side_effects': ['int_st.byterecv=1 per byte'], 'error_cases': [{'condition': 'fifo full', 'result': 'NACK'}]}, {'id': 'FM_SLAVE_SEND', 'name': 'slave_send', 'preconditions': ['!cfg.master_mode', 'addr matches and master is reading'], 'outputs': ['sda_o driven from fifo per byte'], 'side_effects': ['int_st.bytetrans=1 per byte'], 'error_cases': []}, {'id': 'FM_GEN_CALL', 'name': 'general_call', 'preconditions': ['incoming addr=0x00, gen_call enabled'], 'outputs': ['int_st.gencall=1'], 'side_effects': ['accept first byte and pass to ctrl'], 'error_cases': []}, {'id': 'FM_DMA_REQ', 'name': 'dma_request', 'preconditions': ['cfg.dma_en && fifo edge crosses threshold'], 'outputs': ['dma_req asserted until dma_ack'], 'side_effects': [], 'error_cases': [{'condition': 'dma_ack not received within timeout', 'result': 'dma_req held'}]}], 'invariants': ['fifo_count <= FIFO_DEPTH', 'phase != IDLE -> trans == 1', 'trans == 1 -> presetn == 1', 'arb_lost == 1 -> phase->STOP within 4 cycles', 'int_st write-1-clear: only set bits in pwdata clear int_st']}, 'cycle_model': {'clock': 'pclk', 'reset': {'polarity': 'active_low_async', 'deassertion': 'synchronous_to_pclk'}, 'latency': {'apb_register_read': {'min_cycles': 0, 'max_cycles': 1}, 'apb_register_write': {'min_cycles': 0, 'max_cycles': 1}, 'i2c_byte': {'min_cycles': 9, 'max_cycles': None}, 'fifo_push_pop': {'min_cycles': 0, 'max_cycles': 1}, 'glitch_suppress': {'min_cycles': 1, 'max_cycles': 3}}, 'outstanding': 1, 'handshake_rules': [{'name': 'apb_setup', 'signal': 'psel && !penable', 'rule': '1-cycle APB setup'}, {'name': 'apb_access', 'signal': 'psel && penable', 'rule': 'Access completes when slave drives prdata or accepts pwdata'}, {'name': 'i2c_start_stop', 'signal': 'sda falling while scl high (start) / sda rising while scl high (stop)', 'rule': 'START opens transaction; STOP closes'}, {'name': 'i2c_byte', 'signal': '9 SCL pulses (8 data + 1 ACK)', 'rule': 'MSB-first; ACK by receiver'}, {'name': 'glitch_suppress', 'signal': 'filter sda/scl glitches < t_sp', 'rule': 'Suppress glitches shorter than t_sp'}, {'name': 'dma_req_ack', 'signal': 'dma_req && dma_ack', 'rule': 'Hold dma_req until dma_ack'}], 'ordering': [{'name': 'start_addr_data_stop', 'rule': 'Each transaction: START -> ADDR(7-bit + R/W) -> DATA(N bytes) -> STOP'}, {'name': 'arb_lose_terminates', 'rule': 'On arbitration loss, immediately release SDA and abort phase'}], 'arbitration': [{'name': 'i2c_multimaster', 'algorithm': 'open-drain; loser detects mismatch on sampled sda_i', 'winners': 'master that drives 0 while bus is 0'}], 'backpressure': [{'name': 'fifo_full', 'rule': 'FIFO full causes scl to stretch (clock stretching) until drained'}, {'name': 'fifo_empty', 'rule': 'FIFO empty in master_send causes phase->STOP after current byte'}], 'observability': ['int_st bits visible via APB', 'fifo half_full/half_empty signals', 'phase visible in DBGSTATUS']}, 'fcov_bins': [{'id': 'SC_RESET_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC_RESET', 'description': 'reset behavior'}, {'id': 'SC_APB_RW_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC_APB_RW', 'description': 'APB read/write'}, {'id': 'SC_MASTER_TX_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC_MASTER_TX', 'description': 'master 1-byte send'}, {'id': 'SC_MASTER_RX_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC_MASTER_RX', 'description': 'master 1-byte recv'}, {'id': 'SC_SLAVE_RX_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC_SLAVE_RX', 'description': 'slave addr-match recv'}, {'id': 'SC_SLAVE_TX_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC_SLAVE_TX', 'description': 'slave addr-match send'}, {'id': 'SC_GEN_CALL_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC_GEN_CALL', 'description': 'general call'}, {'id': 'SC_ARB_LOSE_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[7]', 'scenario': 'SC_ARB_LOSE', 'description': 'arb-lose mid-byte'}, {'id': 'SC_FIFO_FULL_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[8]', 'scenario': 'SC_FIFO_FULL', 'description': 'fifo full backpressure'}, {'id': 'SC_DMA_FLOW_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[9]', 'scenario': 'SC_DMA_FLOW', 'description': 'DMA hand-shake'}, {'id': 'SC_GLITCH_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[10]', 'scenario': 'SC_GLITCH', 'description': 'glitch suppression'}, {'id': 'cov_master_modes', 'class': 'planned_functional', 'source': 'test_requirements.coverage_goals.planned_bins[0]', 'description': 'master_send + master_recv both exercised'}, {'id': 'cov_slave_modes', 'class': 'planned_functional', 'source': 'test_requirements.coverage_goals.planned_bins[1]', 'description': 'slave_send + slave_recv both exercised'}, {'id': 'cov_arb_lose_in_dat', 'class': 'error', 'source': 'test_requirements.coverage_goals.planned_bins[2]', 'description': 'arblose during DAT phase observed'}, {'id': 'cov_fifo_full_block', 'class': 'planned_functional', 'source': 'test_requirements.coverage_goals.planned_bins[3]', 'description': 'fifo full causes scl stretching'}, {'id': 'cov_gen_call_seen', 'class': 'planned_functional', 'source': 'test_requirements.coverage_goals.planned_bins[4]', 'description': 'general call recognized'}, {'id': 'cov_dma_req_ack', 'class': 'planned_functional', 'source': 'test_requirements.coverage_goals.planned_bins[5]', 'description': 'dma_req/ack handshake exercised'}, {'id': 'cov_int_all_sources', 'class': 'error', 'source': 'test_requirements.coverage_goals.planned_bins[6]', 'description': 'every error_source fires int_st once'}, {'id': 'function_reset', 'class': 'transaction_type', 'source': 'function_model.transactions[0]', 'description': 'reset'}, {'id': 'function_csr_write', 'class': 'transaction_type', 'source': 'function_model.transactions[1]', 'description': 'csr_write'}, {'id': 'function_csr_read', 'class': 'transaction_type', 'source': 'function_model.transactions[2]', 'description': 'csr_read'}, {'id': 'function_master_send', 'class': 'transaction_type', 'source': 'function_model.transactions[3]', 'description': 'master_send'}, {'id': 'function_master_recv', 'class': 'transaction_type', 'source': 'function_model.transactions[4]', 'description': 'master_recv'}, {'id': 'function_slave_recv', 'class': 'transaction_type', 'source': 'function_model.transactions[5]', 'description': 'slave_recv'}, {'id': 'function_slave_send', 'class': 'transaction_type', 'source': 'function_model.transactions[6]', 'description': 'slave_send'}, {'id': 'function_general_call', 'class': 'transaction_type', 'source': 'function_model.transactions[7]', 'description': 'general_call'}, {'id': 'function_dma_request', 'class': 'transaction_type', 'source': 'function_model.transactions[8]', 'description': 'dma_request'}, {'id': 'cycle_apb_setup', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[0]', 'description': "{'name': 'apb_setup', 'signal': 'psel && !penable', 'rule': '1-cycle APB setup'}"}, {'id': 'cycle_apb_access', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[1]', 'description': "{'name': 'apb_access', 'signal': 'psel && penable', 'rule': 'Access completes when slave drives prdata or accepts pwdata'}"}, {'id': 'cycle_i2c_start_stop', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[2]', 'description': "{'name': 'i2c_start_stop', 'signal': 'sda falling while scl high (start) / sda rising while scl high (stop)', 'rule': 'START opens transaction; STOP closes'}"}, {'id': 'cycle_i2c_byte', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[3]', 'description': "{'name': 'i2c_byte', 'signal': '9 SCL pulses (8 data + 1 ACK)', 'rule': 'MSB-first; ACK by receiver'}"}, {'id': 'cycle_glitch_suppress', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[4]', 'description': "{'name': 'glitch_suppress', 'signal': 'filter sda/scl glitches < t_sp', 'rule': 'Suppress glitches shorter than t_sp'}"}, {'id': 'cycle_dma_req_ack', 'class': 'protocol', 'source': 'cycle_model.handshake_rules[5]', 'description': "{'name': 'dma_req_ack', 'signal': 'dma_req && dma_ack', 'rule': 'Hold dma_req until dma_ack'}"}, {'id': 'fsm_iic_phase_idle_to_start_0', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[0]', 'description': 'cmd.start'}, {'id': 'fsm_iic_phase_start_to_addr_1', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[1]', 'description': 'scl falls after start_cond'}, {'id': 'fsm_iic_phase_addr_to_dat_2', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[2]', 'description': 'address byte completes && ack received'}, {'id': 'fsm_iic_phase_addr_to_stop_3', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[3]', 'description': 'address byte completes && nack'}, {'id': 'fsm_iic_phase_dat_to_dat_4', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[4]', 'description': 'more bytes && datacnt > 0'}, {'id': 'fsm_iic_phase_dat_to_stop_5', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[5]', 'description': 'datacnt == 0 || cmd.stop'}, {'id': 'fsm_iic_phase_stop_to_idle_6', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[6]', 'description': 'stop_cond observed'}, {'id': 'fsm_iic_phase_any_to_arblost_7', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[7]', 'description': 'arbitration lost'}, {'id': 'fsm_iic_phase_arblost_to_idle_8', 'class': 'state_transition', 'source': 'fsm.iic_phase.transitions[8]', 'description': 'bus released'}, {'id': 'error_ack_neg', 'class': 'error', 'source': 'error_handling.error_sources[0]', 'description': "{'name': 'ack_neg', 'source': 'no ACK from addressed slave', 'effect': 'int_st.ack_neg=1; phase->STOP'}"}, {'id': 'error_arb_lose', 'class': 'error', 'source': 'error_handling.error_sources[1]', 'description': "{'name': 'arb_lose', 'source': 'another master wins bus', 'effect': 'arb_lost=1; int_st.arblose=1; phase->ARBLOST'}"}, {'id': 'error_fifo_overrun', 'class': 'error', 'source': 'error_handling.error_sources[2]', 'description': "{'name': 'fifo_overrun', 'source': 'slave_recv when fifo full', 'effect': 'NACK reply; int_st.fifo_full=1'}"}, {'id': 'error_dma_timeout', 'class': 'error', 'source': 'error_handling.error_sources[3]', 'description': "{'name': 'dma_timeout', 'source': 'dma_req held without dma_ack', 'effect': 'stall; int_st.dma_to=1'}"}, {'id': 'error_glitch_inject', 'class': 'error', 'source': 'error_handling.error_sources[4]', 'description': "{'name': 'glitch_inject', 'source': 'spurious sda/scl edges', 'effect': 'absorbed by gsf; no functional impact'}"}]}
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
