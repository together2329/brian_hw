#!/usr/bin/env python3
"""Executable SSOT functional model for lfsr.

Generated from yaml/lfsr.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'lfsr', 'parameters': {'LFSR_WIDTH': 32, 'POLY_DEGREE': 32, 'APB_ADDR_WIDTH': 8, 'APB_DATA_WIDTH': 32, 'DEFAULT_POLY': '0x80000057', 'DEFAULT_SEED': '0x1', 'CLOCK_FREQ_MHZ': 50, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'lfsr', 'file': 'rtl/lfsr.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'LFSR PRBS generator with APB-lite register interface', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No SRAM/FIFO in LFSR. All state is in flip-flops (registers).'}, 'registers': {'config': {'register_width': 32, 'addr_width': 8, 'byte_addressable': True, 'alignment_bytes': 4}, 'bit_order': 'lsb0', 'bits_format': '[msb, lsb]', 'reserved_field_policy': {'read_value': 0, 'write_effect': 'ignore', 'rtl_requirement': 'Reserved fields read as zero and do not allocate storage.'}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Control Register', 'write_side_effects': ['Writing enable=1 starts PRBS generation from current lfsr_state.', 'Writing enable=0 halts PRBS generation; state holds.', 'auto_reload controls lockup behavior.'], 'fields': [{'name': 'enable', 'bits': [0, 0], 'access': 'rw', 'reset': 0, 'write_effect': '1=run, 0=halt', 'description': 'PRBS enable'}, {'name': 'auto_reload', 'bits': [1, 1], 'access': 'rw', 'reset': 0, 'write_effect': '1=reload DEFAULT_SEED on lockup, 0=halt on lockup', 'description': 'Auto-reload on lockup'}, {'name': 'reserved_31_2', 'bits': [31, 2], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'POLY', 'offset': 4, 'width': 32, 'access': 'rw', 'reset': 'DEFAULT_POLY', 'category': 'config', 'description': 'Polynomial Register', 'write_side_effects': ['Writable only when CTRL.enable == 0.'], 'fields': [{'name': 'poly', 'bits': [31, 0], 'access': 'rw', 'reset': 'DEFAULT_POLY', 'write_effect': 'Update polynomial tap mask', 'description': 'Feedback polynomial (taps)'}]}, {'name': 'SEED', 'offset': 8, 'width': 32, 'access': 'rw', 'reset': 'DEFAULT_SEED', 'category': 'config', 'description': 'Seed Register', 'write_side_effects': ['Direct load of LFSR state; takes effect immediately on PREADY.'], 'fields': [{'name': 'seed', 'bits': [31, 0], 'access': 'rw', 'reset': 'DEFAULT_SEED', 'write_effect': 'Load LFSR state', 'description': 'LFSR seed value'}]}, {'name': 'STATUS', 'offset': 12, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Status Register', 'fields': [{'name': 'running', 'bits': [0, 0], 'access': 'ro', 'reset': 0, 'description': '1=LFSR is stepping, 0=halted'}, {'name': 'lockup', 'bits': [1, 1], 'access': 'ro', 'reset': 0, 'description': '1=lockup detected (all-zero state)'}, {'name': 'reserved_31_2', 'bits': [31, 2], 'access': 'reserved', 'reset': 0, 'read_value': 0, 'write_effect': 'ignore', 'description': 'Reserved; reads zero'}]}, {'name': 'PRBS', 'offset': 16, 'width': 32, 'access': 'ro', 'reset': 'DEFAULT_SEED', 'category': 'status', 'description': 'Current PRBS Value (read-only copy of lfsr_state)', 'fields': [{'name': 'prbs', 'bits': [31, 0], 'access': 'ro', 'reset': 'DEFAULT_SEED', 'description': 'Current LFSR state value'}]}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes the LFSR computation independent of cycle timing.', 'state_variables': [{'name': 'lfsr_state', 'source': 'registers.PRBS / SEED', 'reset': 'DEFAULT_SEED', 'description': 'Current LFSR shift-register value'}, {'name': 'poly_reg', 'source': 'registers.POLY', 'reset': 'DEFAULT_POLY', 'description': 'Programmable polynomial tap mask'}, {'name': 'ctrl_reg', 'source': 'registers.CTRL', 'reset': 0, 'description': 'Control register {auto_reload, enable}'}, {'name': 'status_reg', 'source': 'registers.STATUS', 'reset': 0, 'description': 'Status register {lockup, running}'}], 'transactions': [{'id': 'FM1', 'name': 'single_step_prbs', 'preconditions': ['ctrl_reg.enable == 1', 'lfsr_state != 0'], 'inputs': ['lfsr_state (current)', 'poly_reg (tap mask)'], 'outputs': [{'name': 'prbs_out', 'expr': 'lfsr_state', 'width': 'LFSR_WIDTH', 'port': 'prbs_out'}, {'name': 'prbs_bit', 'expr': 'lfsr_state[0]', 'width': 1, 'port': 'prbs_bit'}], 'state_updates': [{'name': 'lfsr_state', 'reset': 'DEFAULT_SEED', 'expr': '{feedback_bit, lfsr_state[LFSR_WIDTH-1:1]} where feedback_bit = ^(lfsr_state & poly_reg)'}], 'side_effects': ['status_reg.running set to 1']}, {'id': 'FM2', 'name': 'load_seed', 'preconditions': ['APB write to SEED register (offset 0x08)'], 'inputs': ['PWDATA[APB_DATA_WIDTH-1:0]'], 'outputs': [], 'state_updates': [{'name': 'lfsr_state', 'reset': 'DEFAULT_SEED', 'expr': 'PWDATA truncated to LFSR_WIDTH bits'}], 'side_effects': ['prbs_valid deasserted for one cycle after load']}, {'id': 'FM3', 'name': 'load_polynomial', 'preconditions': ['APB write to POLY register (offset 0x04)', 'ctrl_reg.enable == 0 (polynomial change only when halted)'], 'inputs': ['PWDATA[APB_DATA_WIDTH-1:0]'], 'outputs': [], 'state_updates': [{'name': 'poly_reg', 'reset': 'DEFAULT_POLY', 'expr': 'PWDATA truncated to LFSR_WIDTH bits'}], 'side_effects': []}, {'id': 'FM4', 'name': 'lockup_recovery', 'preconditions': ['lfsr_state == 0 after a step'], 'inputs': [], 'outputs': [{'name': 'prbs_valid', 'expr': '0', 'width': 1, 'port': 'prbs_valid'}], 'state_updates': [{'name': 'lfsr_state', 'reset': 'DEFAULT_SEED', 'expr': 'DEFAULT_SEED if ctrl_reg.auto_reload else 0'}], 'side_effects': ['status_reg.lockup set to 1', 'status_reg.running cleared to 0']}], 'invariants': ['LFSR state never changes when ctrl_reg.enable == 0 except via APB write to SEED or reset.', 'Polynomial register is writable only when enable == 0.', 'All-zero state is detected and either auto-reloaded or held.'], 'reference_model_hint': 'tb-gen should implement a Python LFSR model from this section and compare expected/got for every scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when state, valid/ready, outputs, and status may change.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; keep FunctionalModel as the behavioral oracle and run direct Python smoke checks instead of relying on pytest-pymtl3.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state to reset values', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB-lite read data and pready timing'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB-lite write acceptance timing'}, 'prbs_output': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Single-cycle LFSR step latency'}}, 'handshake_rules': [{'signal': 'PSEL/PENABLE', 'rule': 'Standard APB4: setup phase (PSEL=1,PENABLE=0) followed by access phase (PSEL=1,PENABLE=1); PREADY completes the transfer.'}], 'pipeline': [{'stage': 'S0_IDLE', 'cycle': 0, 'action': 'Hold state; sample APB decode and enable'}, {'stage': 'S1_STEP', 'cycle': 1, 'action': 'Compute next LFSR state if enabled; update prbs_out/prbs_bit/prbs_valid'}], 'ordering': ['APB write to SEED takes effect on the same cycle as the completing PREADY.', 'LFSR state update occurs on the rising edge after enable is sampled high.'], 'backpressure': ['No backpressure on PRBS output; downstream must sample prbs_out/prbs_bit on appropriate cycles.'], 'performance': {'frequency_mhz': 50, 'throughput': {'sustained_prbs_per_cycle': 1, 'condition': 'CTRL.enable == 1 and no lockup'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single APB transaction at a time'}, 'depth': {'pipeline_stages': 1, 'queue_depth': 0, 'description': 'Single-stage combinational feedback with registered output'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}, 'fcov_bins': [{'id': 'function_single_step_prbs', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm1', 'description': 'single_step_prbs'}, {'id': 'function_load_seed', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm2', 'description': 'load_seed'}, {'id': 'function_load_polynomial', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm3', 'description': 'load_polynomial'}, {'id': 'function_lockup_recovery', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[3]', 'source_ref': 'function_model.transactions.fm4', 'description': 'lockup_recovery'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'PSEL/PENABLE', 'rule': 'Standard APB4: setup phase (PSEL=1,PENABLE=0) followed by access phase (PSEL=1,PENABLE=1); PREADY completes the transfer.'}"}, {'id': 'cycle_latency_register_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_read', 'source_ref': 'cycle_model.latency.register_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB-lite read data and pready timing'}"}, {'id': 'cycle_latency_register_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.register_write', 'source_ref': 'cycle_model.latency.register_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB-lite write acceptance timing'}"}, {'id': 'cycle_latency_prbs_output', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.prbs_output', 'source_ref': 'cycle_model.latency.prbs_output', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Single-cycle LFSR step latency'}"}, {'id': 'cycle_pipeline_s0_idle', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Hold state; sample APB decode and enable'}, {'id': 'cycle_pipeline_s1_step', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Compute next LFSR state if enabled; update prbs_out/prbs_bit/prbs_valid'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'APB write to SEED takes effect on the same cycle as the completing PREADY.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'LFSR state update occurs on the rising edge after enable is sampled high.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No backpressure on PRBS output; downstream must sample prbs_out/prbs_bit on appropriate cycles.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'read_max': 1, 'write_max': 1, 'description': 'Single APB transaction at a time'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 1, 'queue_depth': 0, 'description': 'Single-stage combinational feedback with registered output'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '50'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_prbs_per_cycle': 1, 'condition': 'CTRL.enable == 1 and no lockup'}"}, {'id': 'fsm_lfsr_control_idle_to_running_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.lfsr_control.transitions[0]', 'source_ref': 'fsm.lfsr_control.transitions[0]', 'description': 'CTRL.enable == 1 && lfsr_state != 0'}, {'id': 'fsm_lfsr_control_running_to_idle_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.lfsr_control.transitions[1]', 'source_ref': 'fsm.lfsr_control.transitions[1]', 'description': 'CTRL.enable == 0'}, {'id': 'fsm_lfsr_control_running_to_lockup_2', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.lfsr_control.transitions[2]', 'source_ref': 'fsm.lfsr_control.transitions[2]', 'description': 'lfsr_state == 0'}, {'id': 'fsm_lfsr_control_lockup_to_idle_3', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.lfsr_control.transitions[3]', 'source_ref': 'fsm.lfsr_control.transitions[3]', 'description': 'CTRL.enable == 0'}, {'id': 'fsm_lfsr_control_lockup_to_running_4', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.lfsr_control.transitions[4]', 'source_ref': 'fsm.lfsr_control.transitions[4]', 'description': 'CTRL.enable == 1 && CTRL.auto_reload == 1'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_APB', 'condition': 'APB access to undefined address or write to POLY while enabled', 'architectural_effect': 'PSLVERR asserted with PREADY'}"}, {'id': 'error_error_1', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[1]', 'source_ref': 'error_handling.error_sources[1]', 'description': "{'id': 'ERR_LOCKUP', 'condition': 'lfsr_state becomes all-zero', 'architectural_effect': 'STATUS.lockup=1, prbs_valid=0, auto-reload or halt per CTRL.auto_reload'}"}]}
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
