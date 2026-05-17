#!/usr/bin/env python3
"""Executable SSOT functional model for simple_pwm.

Generated from yaml/simple_pwm.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {'ip': 'simple_pwm', 'parameters': {'COUNTER_WIDTH': 8}, 'top_module': {'name': 'simple_pwm', 'file': 'rtl/simple_pwm.sv', 'version': '1.0', 'type': 'peripheral', 'description': 'Configurable PWM output generator with duty-cycle and period inputs', 'reference_spec': 'user-defined', 'target': {'technology': 'generic', 'clock_freq_mhz': 100, 'area_um2': None, 'power_mw': None}}, 'memory': {'instances': [], 'note': 'No internal memory — counter is a simple register'}, 'registers': {'config': {'register_width': 0, 'addr_width': 0, 'byte_addressable': False, 'note': 'No register map — all inputs are direct ports'}, 'no_registers': True, 'reason': 'Educational PWM IP uses direct input ports instead of a register map; no bus interface required', 'register_list': []}, 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen', 'state_variables': [{'name': 'counter', 'source': 'internal', 'reset': 0, 'description': 'Free-running counter, wraps at period'}], 'transactions': [{'id': 'FM1', 'name': 'pwm_active_high', 'preconditions': ['enable == 1', 'counter < duty_cycle'], 'inputs': ['duty_cycle', 'period'], 'outputs': [{'name': 'pwm_out', 'value': 1}], 'output_rules': [{'name': 'pwm_out_high', 'expr': '1', 'width': 1, 'port': 'pwm_out'}], 'state_updates': [{'name': 'counter_next', 'expr': 'counter + 1 if (counter + 1) < period else 0', 'width': 'COUNTER_WIDTH'}], 'side_effects': ['counter increments by 1'], 'error_cases': []}, {'id': 'FM2', 'name': 'pwm_active_low', 'preconditions': ['enable == 1', 'counter >= duty_cycle'], 'inputs': ['duty_cycle', 'period'], 'outputs': [{'name': 'pwm_out', 'value': 0}], 'output_rules': [{'name': 'pwm_out_low', 'expr': '0', 'width': 1, 'port': 'pwm_out'}], 'state_updates': [{'name': 'counter_next', 'expr': 'counter + 1 if (counter + 1) < period else 0', 'width': 'COUNTER_WIDTH'}], 'side_effects': ['counter increments by 1'], 'error_cases': []}, {'id': 'FM3', 'name': 'pwm_idle', 'preconditions': ['enable == 0'], 'inputs': [], 'outputs': [{'name': 'pwm_out', 'value': 0}], 'output_rules': [{'name': 'pwm_out_off', 'expr': '0', 'width': 1, 'port': 'pwm_out'}], 'state_updates': [{'name': 'counter_next', 'expr': '0', 'width': 'COUNTER_WIDTH'}], 'side_effects': ['counter resets to 0'], 'error_cases': []}], 'invariants': ['pwm_out is 0 whenever enable is 0', 'counter resets to 0 when it reaches period', 'counter is 0 whenever enable is 0']}, 'cycle_model': {'purpose': 'Cycle-accurate contract for rtl-gen', 'executable': 'python', 'clock': 'clk', 'reset': {'assertion': 'rst_n low asynchronously clears counter to 0 and pwm_out to 0', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'latency': {'counter_update': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Counter increments or wraps every clock edge when enabled'}, 'pwm_output': {'min_cycles': 1, 'max_cycles': 1, 'description': 'pwm_out reflects counter vs duty_cycle comparison on same edge'}}, 'handshake_rules': [{'signal': 'pwm_out', 'rule': 'Combinational output derived from counter vs duty_cycle comparison; no valid/ready handshake'}], 'pipeline': [{'stage': 'S0_COUNTER_UPDATE', 'cycle': 1, 'action': 'Increment counter or wrap to 0 when enable=1; hold at 0 when enable=0'}, {'stage': 'S1_COMPARE_OUTPUT', 'cycle': 1, 'action': 'Compare counter with duty_cycle; drive pwm_out accordingly'}], 'ordering': ['Counter update and output comparison occur in the same clock cycle.'], 'backpressure': [], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_operations_per_cycle': 1, 'condition': 'enable asserted and period > 0'}, 'outstanding': {'max': 1, 'description': 'Single-cycle counter operation'}, 'depth': {'pipeline_stages': 1, 'description': 'Single-stage counter and compare'}}, 'observability': ['counter value is observable via internal state', 'pwm_out is the primary observable output']}, 'fcov_bins': [{'id': 'SC1_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[0]', 'scenario': 'SC1', 'description': 'Basic PWM generation'}, {'id': 'SC2_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[1]', 'scenario': 'SC2', 'description': 'Duty cycle variation'}, {'id': 'SC3_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[2]', 'scenario': 'SC3', 'description': 'Period rollover'}, {'id': 'SC4_executed', 'class': 'scenario', 'source': 'test_requirements.scenarios[3]', 'scenario': 'SC4', 'description': 'Disable behavior'}, {'id': 'fcov_pwm_high', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM1', 'source_ref': 'function_model.transactions.FM1', 'description': 'FM1 pwm_active_high observed: pwm_out=1 when counter < duty_cycle'}, {'id': 'fcov_pwm_low', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM2', 'source_ref': 'function_model.transactions.FM2', 'description': 'FM2 pwm_active_low observed: pwm_out=0 when counter >= duty_cycle'}, {'id': 'fcov_pwm_idle', 'class': 'transaction', 'coverage_domain': 'function', 'source': 'function_model.transactions.FM3', 'source_ref': 'function_model.transactions.FM3', 'description': 'FM3 pwm_idle observed: pwm_out=0 and counter=0 when enable=0'}, {'id': 'ccov_counter_increment', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S0_COUNTER_UPDATE', 'source_ref': 'cycle_model.pipeline.S0_COUNTER_UPDATE', 'description': 'Counter increments when enabled'}, {'id': 'ccov_counter_rollover', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S0_COUNTER_UPDATE', 'source_ref': 'cycle_model.pipeline.S0_COUNTER_UPDATE', 'description': 'Counter wraps to 0 when reaching period'}, {'id': 'ccov_compare_high', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_COMPARE_OUTPUT', 'source_ref': 'cycle_model.pipeline.S1_COMPARE_OUTPUT', 'description': 'Comparison produces pwm_out=1'}, {'id': 'ccov_compare_low', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline.S1_COMPARE_OUTPUT', 'source_ref': 'cycle_model.pipeline.S1_COMPARE_OUTPUT', 'description': 'Comparison produces pwm_out=0'}, {'id': 'ccov_fsm_idle_to_running', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pwm_fsm.transitions', 'source_ref': 'fsm.pwm_fsm.transitions', 'description': 'IDLE to RUNNING transition observed'}, {'id': 'ccov_fsm_running_to_idle', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pwm_fsm.transitions', 'source_ref': 'fsm.pwm_fsm.transitions', 'description': 'RUNNING to IDLE transition observed'}, {'id': 'function_pwm_active_high', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[0]', 'source_ref': 'function_model.transactions.fm1', 'description': 'pwm_active_high'}, {'id': 'function_pwm_active_low', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[1]', 'source_ref': 'function_model.transactions.fm2', 'description': 'pwm_active_low'}, {'id': 'function_pwm_idle', 'class': 'transaction_type', 'coverage_domain': 'function', 'source': 'function_model.transactions[2]', 'source_ref': 'function_model.transactions.fm3', 'description': 'pwm_idle'}, {'id': 'cycle_handshake_0', 'class': 'protocol', 'coverage_domain': 'cycle', 'source': 'cycle_model.handshake_rules[0]', 'source_ref': 'cycle_model.handshake_rules[0]', 'description': "{'signal': 'pwm_out', 'rule': 'Combinational output derived from counter vs duty_cycle comparison; no valid/ready handshake'}"}, {'id': 'cycle_latency_counter_update', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.counter_update', 'source_ref': 'cycle_model.latency.counter_update', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'Counter increments or wraps every clock edge when enabled'}"}, {'id': 'cycle_latency_pwm_output', 'class': 'latency', 'coverage_domain': 'cycle', 'source': 'cycle_model.latency.pwm_output', 'source_ref': 'cycle_model.latency.pwm_output', 'description': "{'min_cycles': 1, 'max_cycles': 1, 'description': 'pwm_out reflects counter vs duty_cycle comparison on same edge'}"}, {'id': 'cycle_pipeline_s0_counter_update', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[0]', 'source_ref': 'cycle_model.pipeline[0]', 'description': 'Increment counter or wrap to 0 when enable=1; hold at 0 when enable=0'}, {'id': 'cycle_pipeline_s1_compare_output', 'class': 'pipeline_stage', 'coverage_domain': 'cycle', 'source': 'cycle_model.pipeline[1]', 'source_ref': 'cycle_model.pipeline[1]', 'description': 'Compare counter with duty_cycle; drive pwm_out accordingly'}, {'id': 'cycle_ordering_0', 'class': 'ordering', 'coverage_domain': 'cycle', 'source': 'cycle_model.ordering[0]', 'source_ref': 'cycle_model.ordering[0]', 'description': 'Counter update and output comparison occur in the same clock cycle.'}, {'id': 'cycle_perf_outstanding', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.outstanding', 'source_ref': 'cycle_model.performance.outstanding', 'description': "{'max': 1, 'description': 'Single-cycle counter operation'}"}, {'id': 'cycle_perf_depth', 'class': 'performance', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.depth', 'source_ref': 'cycle_model.performance.depth', 'description': "{'pipeline_stages': 1, 'description': 'Single-stage counter and compare'}"}, {'id': 'cycle_perf_frequency_mhz', 'class': 'frequency', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.frequency_mhz', 'source_ref': 'cycle_model.performance.frequency_mhz', 'description': '100'}, {'id': 'cycle_perf_throughput', 'class': 'throughput', 'coverage_domain': 'cycle', 'source': 'cycle_model.performance.throughput', 'source_ref': 'cycle_model.performance.throughput', 'description': "{'sustained_operations_per_cycle': 1, 'condition': 'enable asserted and period > 0'}"}, {'id': 'fsm_pwm_fsm_idle_to_running_0', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pwm_fsm.transitions[0]', 'source_ref': 'fsm.pwm_fsm.transitions[0]', 'description': 'enable == 1'}, {'id': 'fsm_pwm_fsm_running_to_idle_1', 'class': 'state_transition', 'coverage_domain': 'cycle', 'source': 'fsm.pwm_fsm.transitions[1]', 'source_ref': 'fsm.pwm_fsm.transitions[1]', 'description': 'enable == 0'}, {'id': 'error_error_0', 'class': 'error', 'coverage_domain': 'function', 'source': 'error_handling.error_sources[0]', 'source_ref': 'error_handling.error_sources[0]', 'description': "{'id': 'ERR_NONE', 'condition': 'No error sources in this minimal IP', 'architectural_effect': 'N/A'}"}]}
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
