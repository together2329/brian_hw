#!/usr/bin/env python3
"""Executable SSOT functional model for priority_enc.

Generated from yaml/priority_enc.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'priority_enc', 'parameters': {'N': 8, 'INDEX_WIDTH': '$clog2(N)', 'PCLK_FREQ_MHZ': 50, 'RESET_POLARITY': 'active_low'}, 'top_module': {'name': 'priority_enc', 'file': 'rtl/priority_enc.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Parameterized N-input priority encoder with APB-lite CSR', 'reference_spec': 'Internal', 'target': {'technology': 'generic', 'clock_freq_mhz': 50, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No SRAM/FIFO. Register file only in priority_enc_regs.'}, 'registers': {'config': {'register_width': 32, 'addr_width': 12, 'byte_addressable': True}, 'register_list': [{'name': 'CTRL', 'offset': 0, 'width': 32, 'access': 'rw', 'reset': 1, 'category': 'control', 'description': 'Control register', 'fields': [{'name': 'enable', 'bits': [0, 0], 'access': 'rw', 'reset': 1, 'write_effect': 'Updates enable bit; when cleared, forces index_out/valid_out to 0 on next PCLK', 'description': '1=encoder enabled, 0=outputs forced to zero'}, {'name': 'rsvd', 'bits': [31, 1], 'access': 'ro', 'reset': 0, 'read_effect': 'Read as zero; writes ignored', 'description': 'Reserved, read as zero'}]}, {'name': 'MASK', 'offset': 4, 'width': 32, 'access': 'rw', 'reset': 0, 'category': 'control', 'description': 'Input mask register', 'fields': [{'name': 'mask', 'bits': ['N-1', 0], 'access': 'rw', 'reset': 0, 'write_effect': 'Updates mask register; applied to data_in on next PCLK cycle', 'description': '1=input bit is masked (ignored), 0=input is active'}, {'name': 'rsvd', 'bits': [31, 'N'], 'access': 'ro', 'reset': 0, 'read_effect': 'Read as zero; writes ignored', 'description': 'Reserved, read as zero'}]}, {'name': 'STATUS', 'offset': 8, 'width': 32, 'access': 'ro', 'reset': 0, 'category': 'status', 'description': 'Current encoder output status', 'fields': [{'name': 'index', 'bits': ['INDEX_WIDTH-1', 0], 'access': 'ro', 'reset': 0, 'description': 'Current encoded index'}, {'name': 'valid', 'bits': ['INDEX_WIDTH', 'INDEX_WIDTH'], 'access': 'ro', 'reset': 0, 'description': 'Current valid indicator'}, {'name': 'rsvd', 'bits': [31, 'INDEX_WIDTH+1'], 'access': 'ro', 'reset': 0, 'description': 'Reserved, read as zero'}], 'side_effects': ['Updates every PCLK cycle from core datapath when CTRL.enable==1; read-only to APB']}]}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes priority encoder computation independent of cycle timing.', 'state_variables': [{'name': 'enable', 'source': 'registers.CTRL.enable', 'reset': 1, 'description': 'Encoder enable'}, {'name': 'mask', 'source': 'registers.MASK.mask', 'reset': 0, 'description': 'Input mask vector'}, {'name': 'index', 'source': 'registers.STATUS.index', 'reset': 0, 'description': 'Registered encoded index'}, {'name': 'valid', 'source': 'registers.STATUS.valid', 'reset': 0, 'description': 'Registered valid indicator'}], 'state_updates': [{'name': 'index', 'reset': 0, 'expr': 'if (enable) priority_index(data_in & ~mask) else 0', 'description': 'Index of highest-priority unmasked input bit, or 0 when disabled'}, {'name': 'valid', 'reset': 0, 'expr': 'if (enable) |(data_in & ~mask) else 0', 'description': 'Valid when any unmasked input is asserted and enabled'}], 'transactions': [{'id': 'FM_ENCODE', 'name': 'priority_encode', 'preconditions': ['CTRL.enable == 1'], 'inputs': ['data_in[N-1:0]'], 'outputs': [{'name': 'index_out', 'expr': 'priority_index(data_in & ~MASK.mask)', 'width': 'INDEX_WIDTH', 'port': 'index_out'}, {'name': 'valid_out', 'expr': '|(data_in & ~MASK.mask)', 'width': 1, 'port': 'valid_out'}], 'output_rules': [{'name': 'index_out', 'expr': 'for i=N-1 downto 0: if ((data_in[i] & ~mask[i]) == 1) return i; return 0', 'width': 'INDEX_WIDTH', 'port': 'index_out', 'description': 'Index of highest-priority asserted unmasked bit'}, {'name': 'valid_out', 'expr': '|(data_in & ~mask)', 'width': 1, 'port': 'valid_out', 'description': 'Any unmasked input asserted'}], 'side_effects': ['STATUS.index updates to current index_out', 'STATUS.valid updates to current valid_out'], 'error_cases': [{'condition': 'PADDR accesses undefined register offset', 'result': 'APB PSLVERR=1, PRDATA=0'}, {'condition': 'Write to read-only STATUS field', 'result': 'Write ignored, no PSLVERR'}]}], 'invariants': ['When enable==0, index_out and valid_out are both 0 regardless of inputs.', 'When multiple inputs are asserted, index_out always reflects the highest-numbered (highest-priority) bit.'], 'reference_model_hint': 'tb-gen should implement a Python reference model from state_updates and compare expected/got for every stimulus.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when state, outputs, and APB interface may change.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state (registers, outputs)', 'deassertion': 'State is usable on the first rising edge after synchronized deassertion'}, 'latency': {'input_to_output': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Registered 1-cycle latency from data_in change to index_out/valid_out update'}, 'apb_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and pready timing'}, 'apb_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}}, 'handshake_rules': [{'signal': 'apb_csr', 'rule': 'Standard APB-lite: PSEL -> PENABLE sample on PCLK rising edge. PREADY may be tied high.'}], 'pipeline': [{'stage': 'S0_COMB', 'cycle': 0, 'action': 'Combinational priority encode: masked_data = data_in & ~MASK; find highest set bit'}, {'stage': 'S1_REG', 'cycle': 1, 'action': 'Register index_out and valid_out on PCLK rising edge when CTRL.enable==1'}], 'ordering': ['Output register update occurs on PCLK rising edge after combinational priority logic settles.', 'APB register writes take effect on the PCLK cycle after PENABLE handshake completes.'], 'backpressure': ['No backpressure on priority inputs; outputs are always valid or zero.'], 'performance': {'throughput': '1 result per PCLK cycle when enabled', 'max_latency_cycles': 1, 'min_latency_cycles': 1, 'note': 'Combinational encode + registered output gives deterministic 1-cycle throughput.'}, 'observability': ['Every function_model transaction maps to cycle_model pipeline stages S0_COMB and S1_REG.']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Basic priority encode'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'Multiple inputs priority resolution'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'Mask functionality'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'Enable gating'}, {'id': 'SC5_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[4]', 'scenario': 'SC5', 'description': 'APB CSR read/write'}, {'id': 'SC6_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[5]', 'scenario': 'SC6', 'description': 'Reset behavior'}, {'id': 'SC7_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[6]', 'scenario': 'SC7', 'description': 'APB bad address'}, {'id': 'fcov_single_bit', 'class': 'single_bit', 'coverage_domain': 'function', 'source': 'test_requirements.scenarios.SC1', 'source_ref': 'test_requirements.scenarios.SC1', 'description': 'Each input bit asserted individually'}, {'id': 'fcov_multi_bit', 'class': 'multi_bit', 'coverage_domain': 'function', 'source': 'test_requirements.scenarios.SC2', 'source_ref': 'test_requirements.scenarios.SC2', 'description': 'Multiple bits asserted simultaneously'}, {'id': 'fcov_masked', 'class': 'mask', 'coverage_domain': 'function', 'source': 'test_requirements.scenarios.SC3', 'source_ref': 'test_requirements.scenarios.SC3', 'description': 'Mask disables selected inputs'}, {'id': 'fcov_disabled', 'class': 'disable', 'coverage_domain': 'function', 'source': 'test_requirements.scenarios.SC4', 'source_ref': 'test_requirements.scenarios.SC4', 'description': 'Enable=0 forces zero outputs'}, {'id': 'fcov_csr_rw', 'class': 'csr', 'coverage_domain': 'function', 'source': 'test_requirements.scenarios.SC5', 'source_ref': 'test_requirements.scenarios.SC5', 'description': 'APB read/write to all registers'}, {'id': 'fcov_reset', 'class': 'reset', 'coverage_domain': 'function', 'source': 'test_requirements.scenarios.SC6', 'source_ref': 'test_requirements.scenarios.SC6', 'description': 'Reset clears all state'}, {'id': 'fcov_apb_err', 'class': 'apb_error', 'coverage_domain': 'function', 'source': 'test_requirements.scenarios.SC7', 'source_ref': 'test_requirements.scenarios.SC7', 'description': 'APB bad-address error response'}, {'id': 'ccov_pipeline_comb', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S0_COMB', 'source_ref': 'cycle_model.pipeline.S0_COMB', 'description': 'Combinational priority stage observed'}, {'id': 'ccov_pipeline_reg', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_REG', 'source_ref': 'cycle_model.pipeline.S1_REG', 'description': 'Registered output stage observed'}, {'id': 'ccov_apb_handshake', 'class': 'handshake', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules', 'source_ref': 'cycle_model.handshake_rules', 'description': 'APB-lite handshake observed'}, {'id': 'function_priority_encode', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm_encode', 'description': 'priority_encode'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'apb_csr', 'rule': 'Standard APB-lite: PSEL -> PENABLE sample on PCLK rising edge. PREADY may be tied high.'}"}, {'id': 'cycle_latency_input_to_output', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.input_to_output', 'source_ref': 'cycle_model.latency.input_to_output', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Registered 1-cycle latency from data_in change to index_out/valid_out update'}"}, {'id': 'cycle_latency_apb_read', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.apb_read', 'source_ref': 'cycle_model.latency.apb_read', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and pready timing'}"}, {'id': 'cycle_latency_apb_write', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.apb_write', 'source_ref': 'cycle_model.latency.apb_write', 'description': "{'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}"}, {'id': 'cycle_pipeline_s0_comb', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Combinational priority encode: masked_data = data_in & ~MASK; find highest set bit'}, {'id': 'cycle_pipeline_s1_reg', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Register index_out and valid_out on PCLK rising edge when CTRL.enable==1'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Output register update occurs on PCLK rising edge after combinational priority logic settles.'}, {'id': 'cycle_ordering_1', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[1]', 'source_ref': 'cycle_model.ordering[1]', 'description': 'APB register writes take effect on the PCLK cycle after PENABLE handshake completes.'}, {'id': 'cycle_backpressure_0', 'class': 'backpressure', 'coverage_domain': 'cycle', 'source': 'cycle_model.backpressure[0]', 'source_ref': 'cycle_model.backpressure[0]', 'description': 'No backpressure on priority inputs; outputs are always valid or zero.'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': '1 result per PCLK cycle when enabled'}, {'id': 'fsm_encoder_fsm_idle_to_active_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.encoder_fsm.transitions[0]', 'source_ref': 'fsm.encoder_fsm.transitions[0]', 'description': 'CTRL.enable == 1'}, {'id': 'fsm_encoder_fsm_active_to_idle_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.encoder_fsm.transitions[1]', 'source_ref': 'fsm.encoder_fsm.transitions[1]', 'description': 'CTRL.enable == 0'}, {'id': 'error_apb_bad_addr', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'name': 'APB_BAD_ADDR', 'source': 'APB access to undefined offset', 'severity': 'warning', 'effect': 'PSLVERR=1', 'recovery': 'Software must use valid offsets'}"}]}
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
