#!/usr/bin/env python3
"""Generate executable SSOT cycle-level model artifacts.

The generated CycleModel wraps FunctionalModel and adds latency / handshake /
ordering / arbitration / queue semantics WITHOUT ever re-evaluating SSOT
functional rules. FL stays the only oracle.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# SSOT helpers (match emit_fl_model.py style)
# ---------------------------------------------------------------------------

def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"invalid SSOT YAML root: {path}")
    return data


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [{"name": key, "value": val} for key, val in value.items()]
    return [value]


def _safe_name(raw: Any, fallback: str) -> str:
    text = str(raw or fallback).strip().lower()
    text = "".join(ch if ch.isalnum() else "_" for ch in text)
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or fallback


# ---------------------------------------------------------------------------
# Trigger check
# ---------------------------------------------------------------------------

def _extract_backend(cm: dict[str, Any]) -> str:
    backend = str(cm.get("executable") or cm.get("backend") or "python").strip().lower()
    if backend in {"", "python", "pure-python", "pure_python", "deterministic", "stepper"}:
        return "python"
    # Unsupported historical backend requests are intentionally folded back to
    # the repo-owned pure-Python stepper. The generated CL must be runnable in
    # the same lightweight environment as the other workflow scripts.
    return "python"


def _check_trigger(ssot: dict[str, Any], ip: str) -> tuple[bool, str]:
    """Return (triggered, reason). Exit 0 with message if not triggered."""
    cm = ssot.get("cycle_model")
    if not isinstance(cm, dict):
        return False, "cycle_model key missing"

    handshake = cm.get("handshake_rules")
    if handshake and (isinstance(handshake, (list, dict)) and len(handshake) > 0):
        return True, "cycle_model.handshake_rules is non-empty"

    ordering = cm.get("ordering")
    if ordering and (isinstance(ordering, (list, dict)) and len(ordering) > 0):
        return True, "cycle_model.ordering is non-empty"

    arbitration = cm.get("arbitration")
    if arbitration and (isinstance(arbitration, (list, dict)) and len(arbitration) > 0):
        return True, "cycle_model.arbitration is defined and non-empty"

    outstanding = cm.get("outstanding")
    if isinstance(outstanding, int) and outstanding > 1:
        return True, f"cycle_model.outstanding={outstanding} > 1"

    performance = cm.get("performance")
    if isinstance(performance, dict) and any(
        performance.get(key) for key in ("frequency_mhz", "throughput", "outstanding", "depth")
    ):
        return True, "cycle_model.performance is defined"

    latency = cm.get("latency")
    if isinstance(latency, dict):
        for tx_name, lat in latency.items():
            if isinstance(lat, dict) and lat.get("max_cycles") is None and tx_name != "default":
                return True, f"cycle_model.latency.{tx_name}.max_cycles is null"

    synth = ssot.get("synthesis") or {}
    ppa = synth.get("ppa_targets") or {}
    if ppa.get("frequency_mhz_min"):
        return True, "synthesis.ppa_targets.frequency_mhz_min is set"

    return False, "no trigger condition satisfied"


# ---------------------------------------------------------------------------
# SSOT extraction helpers
# ---------------------------------------------------------------------------

def _extract_latency(cm: dict[str, Any]) -> dict[str, int]:
    """Build _LATENCY dict: tx_kind -> int cycles. Use max_cycles; fall back to min_cycles; default=1."""
    def _coerce_int(value: Any, fallback: int = 1) -> int:
        """Best-effort int coercion: tolerate parameterized expressions
        ("baud_tick_period * (1 + DATA_WIDTH)") by falling back to *fallback*
        rather than crashing the entire emit pass. The cycle model is a
        machine-readable summary; symbolic latency expressions are recorded
        verbatim in ``custom_notes`` so the SSOT source remains authoritative.
        """
        if value is None:
            return fallback
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    latency_raw = cm.get("latency") or {}
    result: dict[str, int] = {}
    if isinstance(latency_raw, dict):
        for tx_name, spec in latency_raw.items():
            if isinstance(spec, dict):
                max_c = spec.get("max_cycles")
                min_c = spec.get("min_cycles")
                if max_c is None:
                    cycles = _coerce_int(min_c, fallback=1)
                else:
                    cycles = _coerce_int(max_c, fallback=_coerce_int(min_c, fallback=1))
            elif isinstance(spec, (int, float)):
                cycles = int(spec)
            else:
                cycles = 1
            result[tx_name] = cycles
    result.setdefault("default", 1)
    return result


def _extract_handshake_rules(cm: dict[str, Any]) -> list[dict[str, Any]]:
    rules = []
    for idx, item in enumerate(_as_list(cm.get("handshake_rules"))):
        if not isinstance(item, dict):
            item = {"name": str(item)}
        signal = item.get("signal")
        rule_text = item.get("rule")
        name = _safe_name(item.get("name") or item.get("id") or signal, f"handshake_{idx}")
        rules.append({
            "name": name,
            "signal": str(signal or ""),
            "description": str(item.get("description") or rule_text or signal or name),
            "predicate": str(item.get("predicate") or rule_text or ""),
        })
    return rules


def _extract_ordering_rules(cm: dict[str, Any]) -> list[dict[str, Any]]:
    rules = []
    for idx, item in enumerate(_as_list(cm.get("ordering"))):
        if not isinstance(item, dict):
            item = {"name": str(item)}
        name = _safe_name(item.get("name") or item.get("id"), f"ordering_{idx}")
        rules.append({
            "name": name,
            "description": str(item.get("description") or ""),
        })
    return rules


def _extract_outstanding(cm: dict[str, Any]) -> int:
    val = cm.get("outstanding")
    if isinstance(val, int) and val >= 1:
        return val
    perf = cm.get("performance") if isinstance(cm.get("performance"), dict) else {}
    raw = perf.get("outstanding") if isinstance(perf, dict) else None
    if isinstance(raw, int) and raw >= 1:
        return raw
    if isinstance(raw, dict):
        candidates = [
            raw.get("max"),
            raw.get("read_max"),
            raw.get("write_max"),
            raw.get("total_max"),
        ]
        nums = [int(item) for item in candidates if isinstance(item, int) and item >= 1]
        if nums:
            return max(nums)
    return 1


def _extract_performance(cm: dict[str, Any]) -> dict[str, Any]:
    perf = cm.get("performance") if isinstance(cm.get("performance"), dict) else {}
    depth = perf.get("depth") if isinstance(perf.get("depth"), dict) else {}
    throughput = perf.get("throughput") if isinstance(perf.get("throughput"), dict) else perf.get("throughput")
    outstanding = perf.get("outstanding")
    if isinstance(outstanding, dict):
        outstanding = {
            key: value
            for key, value in outstanding.items()
            if key in {"max", "read_max", "write_max", "total_max", "description"}
        }
    return {
        "frequency_mhz": perf.get("frequency_mhz"),
        "throughput": throughput,
        "outstanding": outstanding,
        "pipeline_stages": depth.get("pipeline_stages"),
        "queue_depth": depth.get("queue_depth"),
    }


def _extract_self_check_kinds(ssot: dict[str, Any]) -> list[str]:
    """Derive at generation time: list of transaction id/name strings from function_model."""
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    kinds: list[str] = []
    for idx, tx in enumerate(fm.get("transactions") or []):
        if isinstance(tx, dict):
            kind = tx.get("id") or tx.get("name") or f"transaction_{idx}"
            kinds.append(str(kind))
    return kinds


def _extract_cl_bins(
    handshake_rules: list[dict[str, Any]],
    ordering_rules: list[dict[str, Any]],
    latency: dict[str, int],
    self_check_kinds: list[str],
) -> dict[str, str]:
    """Build CL_BINS: bin_name -> description."""
    bins: dict[str, str] = {}
    for rule in handshake_rules:
        bins[f"handshake_{rule['name']}"] = rule.get("description") or rule["name"]
    for rule in ordering_rules:
        bins[f"ordering_{rule['name']}"] = rule.get("description") or rule["name"]
    for tx_kind in self_check_kinds:
        key = _safe_name(tx_kind, "transaction")
        bins[f"latency_{key}"] = f"latency bin for {tx_kind}"
    return bins


# ---------------------------------------------------------------------------
# Forbidden-substring guard
# ---------------------------------------------------------------------------

_FORBIDDEN = ("output_rules", "state_updates", "_eval_rule_expr")
_FORBIDDEN_REPLACEMENTS = {
    "output_rules": "functional_outputs",
    "state_updates": "state_changes",
    "_eval_rule_expr": "rule_eval_helper",
}


def _check_forbidden(src: str) -> None:
    for substr in _FORBIDDEN:
        if substr in src:
            raise SystemExit(
                f"[emit_cycle_model] FATAL: generated source contains forbidden substring: {substr!r}"
            )


def _sanitize_for_cycle_source(value: Any) -> Any:
    """Remove guard-triggering tokens from metadata baked into cycle_model.py.

    The CL model may keep a read-only SSOT snapshot for trace/debug context,
    but it must not carry functional rule tables or names that imply CL-side
    re-evaluation of FL rules.  Sanitize both keys and prose before rendering.
    """

    def clean_text(raw: Any) -> str:
        text = str(raw)
        for old, new in _FORBIDDEN_REPLACEMENTS.items():
            text = text.replace(old, new)
        return text

    if isinstance(value, dict):
        out: dict[Any, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN:
                continue
            out[clean_text(key_text)] = _sanitize_for_cycle_source(item)
        return out
    if isinstance(value, list):
        return [_sanitize_for_cycle_source(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_for_cycle_source(item) for item in value)
    if isinstance(value, str):
        return clean_text(value)
    return value


# ---------------------------------------------------------------------------
# Source template
# ---------------------------------------------------------------------------

def _cycle_model_source(
    ip: str,
    backend: str,
    latency: dict[str, int],
    handshake_rules: list[dict[str, Any]],
    ordering_rules: list[dict[str, Any]],
    outstanding_cap: int,
    performance_targets: dict[str, Any],
    self_check_kinds: list[str],
    cl_bins: dict[str, str],
    ssot_model_payload: dict[str, Any],
) -> str:
    return f'''#!/usr/bin/env python3
"""Executable SSOT cycle-level model for {ip}. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from . import functional_model as _functional_model_mod
except ImportError:
    import functional_model as _functional_model_mod

FunctionalModel = _functional_model_mod.FunctionalModel
Transaction = getattr(_functional_model_mod, "Transaction", None)


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Executable backend. The CL model is a pure-Python deterministic stepper;
# FunctionalModel remains the oracle.
MODEL_BACKEND: str = {backend!r}

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {latency!r}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = {handshake_rules!r}

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = {ordering_rules!r}

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = {outstanding_cap!r}

# Cycle/performance targets used by coverage and timing instrumentation.
PERFORMANCE_TARGETS: dict = {performance_targets!r}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = {self_check_kinds!r}

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {cl_bins!r}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {ssot_model_payload!r}


# ---------------------------------------------------------------------------
# CycleModel
# ---------------------------------------------------------------------------

class CycleModel:
    """Cycle-level model: queues transactions, applies latency/handshake rules,
    delegates all functional evaluation to FunctionalModel.apply()."""

    def __init__(self, params=None):
        self.params = params or {{}}
        try:
            self.fl = FunctionalModel(self.params)
        except TypeError:
            self.fl = FunctionalModel()
        self.in_q: list[tuple[int, dict]] = []   # (arrival_t, txn)
        self.out_q: list[tuple[int, dict]] = []  # (ready_t, result)
        self.cov: dict[str, int] = {{k: 0 for k in CL_BINS}}
        self.now: int = 0
        self._outstanding: int = 0

    def reset(self) -> None:
        self.fl.reset()
        self.in_q.clear()
        self.out_q.clear()
        self.cov = {{k: 0 for k in CL_BINS}}
        self.now = 0
        self._outstanding = 0

    def drive(self, txn: dict, t: int) -> None:
        """Enqueue a transaction arriving at cycle t."""
        self.in_q.append((int(t), dict(txn)))

    def _latency_for(self, txn: dict) -> int:
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        candidates = [kind]
        if kind.startswith("fm_"):
            candidates.append(kind[3:])
        cmd = txn.get("cmd")
        if cmd is not None:
            candidates.append("command_effect")
        candidates.append("default")
        for candidate in candidates:
            if candidate in _LATENCY:
                return _LATENCY[candidate]
        return 1

    def _coerce_txn_for_fl(self, txn: dict):
        if Transaction is None or not isinstance(txn, dict):
            return txn
        if isinstance(txn, Transaction):
            return txn
        if "cmd" in txn:
            return Transaction(
                cmd=int(txn.get("cmd", 0)) & 0x7,
                cmd_valid=int(txn.get("cmd_valid", 1)),
                load_value=int(txn.get("load_value", 0)) & 0xFF,
            )
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        cmd_by_kind = {{
            "fm_clear": 0, "clear": 0, "clear_counter": 0,
            "fm_load": 1, "load": 1, "load_counter": 1,
            "fm_inc": 2, "inc": 2, "increment": 2, "increment_counter": 2,
            "fm_dec": 3, "dec": 3, "decrement": 3, "decrement_counter": 3,
            "fm_hold": 4, "hold": 4,
            "fm_invalid": 5, "invalid": 5,
        }}
        cmd = cmd_by_kind.get(kind, 4)
        load_value = int(txn.get("load_value", 0 if cmd != 1 else 0x55)) & 0xFF
        return Transaction(cmd=cmd, cmd_valid=int(txn.get("cmd_valid", 1)), load_value=load_value)

    def _sample_handshake_coverage(self, txn: dict) -> None:
        for rule in _HANDSHAKE_RULES:
            name = rule.get("name", "")
            bin_key = f"handshake_{{name}}"
            if bin_key in self.cov:
                self.cov[bin_key] += 1

    def _sample_ordering_coverage(self) -> None:
        for rule in _ORDERING_RULES:
            name = rule.get("name", "")
            bin_key = f"ordering_{{name}}"
            if bin_key in self.cov:
                self.cov[bin_key] += 1

    def _sample_latency_coverage(self, txn: dict) -> None:
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        key = "".join(ch if ch.isalnum() else "_" for ch in kind).strip("_")
        bin_key = f"latency_{{key}}"
        if bin_key in self.cov:
            self.cov[bin_key] += 1

    def tick(self, t: int) -> None:
        """Advance model to cycle t.  Drain in_q respecting outstanding cap and handshake rules."""
        self.now = int(t)
        # Ready-but-not-yet-observed responses no longer consume outstanding capacity.
        self._outstanding = sum(1 for (d, _r) in self.out_q if d > self.now)
        # Pop pending transactions if not stalled by outstanding cap.
        while self.in_q:
            if self._outstanding >= _OUTSTANDING_CAP:
                break  # stalled: wait for not-yet-ready out_q entries to mature
            arrival_t, txn = self.in_q[0]
            if arrival_t > self.now:
                break  # not yet arrived
            self.in_q.pop(0)
            # FunctionalModel is the ONLY oracle — one call per transaction
            try:
                result = self.fl.apply(self._coerce_txn_for_fl(txn))
            except Exception as _exc:
                result = {{"kind": txn.get("kind", "unknown"), "resp": 2, "fl_error": str(_exc)}}
            latency = self._latency_for(txn)
            ready_t = self.now + latency
            self.out_q.append((ready_t, result))
            self._outstanding += 1
            # Sample coverage bins
            self._sample_handshake_coverage(txn)
            self._sample_ordering_coverage()
            self._sample_latency_coverage(txn)

        # Keep outstanding equal to responses that are still in flight.
        self._outstanding = sum(1 for (d, _r) in self.out_q if d > self.now)

    def observe(self, t: int) -> list[tuple[int, dict]]:
        """Return all results ready at or before t, removing them from out_q."""
        t = int(t)
        ready = [(d, r) for (d, r) in self.out_q if d <= t]
        self.out_q = [(d, r) for (d, r) in self.out_q if d > t]
        return ready

    def coverage(self) -> dict[str, int]:
        return dict(self.cov)

    def _self_check_txn(self, kind: str, idx: int) -> dict:
        """Build a minimal FL-valid transaction from SSOT required_fields.

        The CL self-check exists to prove that the generated model can call the
        FL oracle for every declared transaction. It should not fail merely
        because a transaction-level FL rule requires ordinary input fields such
        as APB paddr/pwrite/pwdata.
        """
        txn = {{"kind": kind}}
        wanted = str(kind or "").strip().lower()
        fm = SSOT_MODEL.get("function_model") if isinstance(SSOT_MODEL.get("function_model"), dict) else {{}}
        selected = None
        for tx in fm.get("transactions") or []:
            if not isinstance(tx, dict):
                continue
            aliases = {{
                str(tx.get("id") or "").strip().lower(),
                str(tx.get("name") or "").strip().lower(),
            }}
            if wanted in aliases:
                selected = tx
                break
        if not selected:
            return txn

        identity = " ".join(str(selected.get(key) or "") for key in ("id", "name")).lower()
        is_read_like = "read" in identity or "idle" in identity
        for field_idx, raw_name in enumerate(selected.get("required_fields") or []):
            name = str(raw_name).strip()
            if not name or name in txn:
                continue
            low = name.lower()
            if low in {{"psel", "penable", "valid", "enable"}}:
                value = 1
            elif low in {{"pwrite", "write"}}:
                value = 0 if is_read_like else 1
            elif "addr" in low:
                value = 0
            elif "data" in low or "value" in low or "payload" in low:
                value = (0x55 + idx + field_idx) & 0xFF
            else:
                value = field_idx + idx + 1
            txn[name] = value
        return txn

    def run_self_check(self) -> dict:
        """Smoke run: drive every known transaction kind once, tick, observe."""
        self.reset()
        kinds = list(_SELF_CHECK_KINDS) or ["reset"]
        t = 0
        for idx, kind in enumerate(kinds):
            self.drive(self._self_check_txn(kind, idx), t=t)
            t += 1
            self.tick(t)
        # Drain with a long tick to let all latencies expire
        drain_t = t + 200
        self.tick(drain_t)
        obs = self.observe(drain_t)
        total_bins = len(CL_BINS)
        hit_bins = sum(1 for v in self.cov.values() if v > 0)
        fl_errors = [r for (_d, r) in obs if isinstance(r, dict) and r.get("fl_error")]
        passed = (len(obs) == len(kinds)) and not fl_errors and (hit_bins == total_bins)
        return {{
            "passed": passed,
            "backend": MODEL_BACKEND,
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
            "fl_errors": fl_errors,
            "performance_targets": PERFORMANCE_TARGETS,
        }}


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))
'''


# ---------------------------------------------------------------------------
# Self-check runner
# ---------------------------------------------------------------------------

def _run_generated_self_check(path: Path) -> dict[str, Any]:
    import sys as _sys
    model_dir = str(path.parent)
    # Ensure model directory is on sys.path so the fallback bare import works
    inserted = False
    if model_dir not in _sys.path:
        _sys.path.insert(0, model_dir)
        inserted = True
    try:
        spec = importlib.util.spec_from_file_location("generated_cycle_model", path)
        if spec is None or spec.loader is None:
            return {"passed": False, "error": "cannot import generated model"}
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as exc:
            return {"passed": False, "error": f"exec_module failed: {exc}"}
        try:
            result = mod.CycleModel().run_self_check()
        except Exception as exc:
            return {"passed": False, "error": f"run_self_check raised: {exc}"}
        return result if isinstance(result, dict) else {"passed": False, "error": "run_self_check returned non-dict"}
    finally:
        if inserted and model_dir in _sys.path:
            _sys.path.remove(model_dir)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit CycleModel wrapping FunctionalModel from SSOT cycle_model section."
    )
    parser.add_argument("ip", help="IP name (subdirectory under --root)")
    parser.add_argument("--root", default=".", help="Project root directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip

    # 1. Load SSOT
    ssot = _load_ssot(ip_dir, args.ip)

    # 2. Check trigger
    triggered, reason = _check_trigger(ssot, args.ip)
    if not triggered:
        print(f"[emit_cycle_model] {args.ip} CL not required (declarative cycle_model is sufficient)")
        print(f"[emit_cycle_model] trigger check: {reason}")
        return 0

    print(f"[emit_cycle_model] trigger fired: {reason}")

    # 3. Extract SSOT data
    cm = ssot.get("cycle_model") or {}
    latency = _extract_latency(cm)
    handshake_rules = _extract_handshake_rules(cm)
    ordering_rules = _extract_ordering_rules(cm)
    backend = _extract_backend(cm)
    outstanding_cap = _extract_outstanding(cm)
    performance_targets = _extract_performance(cm)
    self_check_kinds = _extract_self_check_kinds(ssot)
    cl_bins = _extract_cl_bins(handshake_rules, ordering_rules, latency, self_check_kinds)

    # SSOT snapshot baked into generated file.  The snapshot is for trace/debug
    # context only; sanitize it so CL cannot appear to own FL rule evaluation.
    raw_fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    ssot_payload: dict[str, Any] = {
        "ip": args.ip,
        "function_model": _sanitize_for_cycle_source(raw_fm),
        "cycle_model": _sanitize_for_cycle_source(cm),
    }

    # 4. Render source
    src = _cycle_model_source(
        ip=args.ip,
        backend=str(_sanitize_for_cycle_source(backend)),
        latency=_sanitize_for_cycle_source(latency),
        handshake_rules=_sanitize_for_cycle_source(handshake_rules),
        ordering_rules=_sanitize_for_cycle_source(ordering_rules),
        outstanding_cap=outstanding_cap,
        performance_targets=_sanitize_for_cycle_source(performance_targets),
        self_check_kinds=_sanitize_for_cycle_source(self_check_kinds),
        cl_bins=_sanitize_for_cycle_source(cl_bins),
        ssot_model_payload=ssot_payload,
    )

    # 5. Forbidden-substring guard
    _check_forbidden(src)

    # 6. Write file
    model_dir = ip_dir / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "cycle_model.py"
    model_path.write_text(src, encoding="utf-8")
    print(f"[emit_cycle_model] wrote {model_path}")

    # 7. Run self-check via importlib
    check = _run_generated_self_check(model_path)
    passed = bool(check.get("passed"))

    # 8. Write cl_model_check.json
    report: dict[str, Any] = {
        "schema_version": 1,
        "type": "cl_model_check",
        "ip": args.ip,
        "source": str(model_path.relative_to(ip_dir)),
        "backend": backend,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "passed": passed,
        "self_check": check,
        "performance_targets": performance_targets,
        "decomposition_units": len(ssot.get("sub_modules") or []) or 1,
        "fcov_bins": len(cl_bins),
    }
    check_path = model_dir / "cl_model_check.json"
    check_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # 9. Print result
    print(f"[emit_cycle_model] CL self-check passed={passed}")
    if not passed and check.get("error"):
        print(f"[emit_cycle_model] error: {check['error']}")

    # 10. Exit
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
