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
    if backend in {"pymtl", "pymtl3", "pymtl_3"}:
        return "pymtl3"
    return backend or "python"


def _check_trigger(ssot: dict[str, Any], ip: str) -> tuple[bool, str]:
    """Return (triggered, reason). Exit 0 with message if not triggered."""
    cm = ssot.get("cycle_model")
    if not isinstance(cm, dict):
        return False, "cycle_model key missing"

    if _extract_backend(cm) == "pymtl3":
        return True, "cycle_model.executable=pymtl3"

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
    latency_raw = cm.get("latency") or {}
    result: dict[str, int] = {}
    if isinstance(latency_raw, dict):
        for tx_name, spec in latency_raw.items():
            if isinstance(spec, dict):
                max_c = spec.get("max_cycles")
                min_c = spec.get("min_cycles")
                if max_c is None:
                    cycles = int(min_c) if min_c is not None else 1
                else:
                    cycles = int(max_c)
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
        name = _safe_name(item.get("name") or item.get("id"), f"handshake_{idx}")
        rules.append({
            "name": name,
            "description": str(item.get("description") or ""),
            "predicate": str(item.get("predicate") or ""),
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


def _check_forbidden(src: str) -> None:
    for substr in _FORBIDDEN:
        if substr in src:
            raise SystemExit(
                f"[emit_cycle_model] FATAL: generated source contains forbidden substring: {substr!r}"
            )


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
    from .functional_model import FunctionalModel
except ImportError:
    from functional_model import FunctionalModel

try:
    from pymtl3 import Bits1, Bits32, Component, InPort, OutPort, update_ff
    HAS_PYMTL3 = True
except Exception:
    Bits1 = Bits32 = Component = InPort = OutPort = update_ff = None
    HAS_PYMTL3 = False


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Requested executable backend.  PyMTL3 is the default CL shell; FunctionalModel remains the oracle.
MODEL_BACKEND: str = {backend!r}

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {latency!r}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = {handshake_rules!r}

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = {ordering_rules!r}

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = {outstanding_cap!r}

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
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
        self.fl = FunctionalModel(params)
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
        return _LATENCY.get(kind, _LATENCY.get("default", 1))

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
        # Pop one pending transaction if not stalled by outstanding cap
        while self.in_q:
            if self._outstanding >= _OUTSTANDING_CAP:
                break  # stalled: wait for out_q drain
            arrival_t, txn = self.in_q[0]
            if arrival_t > self.now:
                break  # not yet arrived
            self.in_q.pop(0)
            # FunctionalModel is the ONLY oracle — one call per transaction
            try:
                result = self.fl.apply(txn)
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

        # Release completed transactions from outstanding count
        completed = [r for (d, r) in self.out_q if d <= self.now]
        self._outstanding = max(0, self._outstanding - len(completed))

    def observe(self, t: int) -> list[tuple[int, dict]]:
        """Return all results ready at or before t, removing them from out_q."""
        t = int(t)
        ready = [(d, r) for (d, r) in self.out_q if d <= t]
        self.out_q = [(d, r) for (d, r) in self.out_q if d > t]
        return ready

    def coverage(self) -> dict[str, int]:
        return dict(self.cov)

    def run_self_check(self) -> dict:
        """Smoke run: drive every known transaction kind once, tick, observe."""
        self.reset()
        kinds = list(_SELF_CHECK_KINDS) or ["reset"]
        t = 0
        for kind in kinds:
            self.drive({{"kind": kind}}, t=t)
            t += 1
            self.tick(t)
        # Drain with a long tick to let all latencies expire
        drain_t = t + 200
        self.tick(drain_t)
        obs = self.observe(drain_t)
        total_bins = len(CL_BINS)
        hit_bins = sum(1 for v in self.cov.values() if v > 0)
        return {{
            "passed": bool(obs),
            "backend": MODEL_BACKEND,
            "pymtl3_available": HAS_PYMTL3,
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
            "performance_targets": PERFORMANCE_TARGETS,
        }}


if HAS_PYMTL3:
    class CycleModelPyMTL(Component):
        """PyMTL3 cycle shell around CycleModel for cycle/performance validation.

        The wrapper intentionally delegates behavioral results to CycleModel,
        which delegates function evaluation to FunctionalModel.  PyMTL owns the
        clocked shell and observable counters used by CL coverage.
        """

        def construct(s):
            s.reset_in = InPort(Bits1)
            s.valid = InPort(Bits1)
            s.ready = OutPort(Bits1)
            s.cycle_count = OutPort(Bits32)
            s.outstanding = OutPort(Bits32)
            s.queue_depth = OutPort(Bits32)
            s._model = CycleModel()

            @update_ff
            def cl_tick():
                if s.reset_in:
                    s._model.reset()
                    s.ready <<= 1
                    s.cycle_count <<= 0
                    s.outstanding <<= 0
                    s.queue_depth <<= 0
                else:
                    next_cycle = s._model.now + 1
                    s._model.tick(next_cycle)
                    s.ready <<= int(s._model._outstanding < _OUTSTANDING_CAP)
                    s.cycle_count <<= next_cycle
                    s.outstanding <<= s._model._outstanding
                    s.queue_depth <<= len(s._model.in_q)
else:
    CycleModelPyMTL = None


def make_pymtl_cycle_model():
    """Return the PyMTL3 cycle shell.  Use direct Python smoke, not pytest-pymtl3."""
    if not HAS_PYMTL3:
        raise RuntimeError("pymtl3 is not importable in this Python environment")
    return CycleModelPyMTL()


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

    # SSOT snapshot baked into generated file.
    # Strip all forbidden keys from function_model transactions so the repr
    # cannot contain 'output_rules', 'state_updates', or '_eval_rule_expr'.
    _STRIP_KEYS = {"output_rules", "state_updates", "_eval_rule_expr"}

    def _strip_fm(fm: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of function_model with forbidden transaction keys removed."""
        fm = dict(fm)
        txns = []
        for tx in fm.get("transactions") or []:
            if isinstance(tx, dict):
                tx = {k: v for k, v in tx.items() if k not in _STRIP_KEYS}
            txns.append(tx)
        fm["transactions"] = txns
        return fm

    raw_fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    ssot_payload: dict[str, Any] = {
        "ip": args.ip,
        "function_model": _strip_fm(raw_fm),
        "cycle_model": cm,
    }

    # 4. Render source
    src = _cycle_model_source(
        ip=args.ip,
        backend=backend,
        latency=latency,
        handshake_rules=handshake_rules,
        ordering_rules=ordering_rules,
        outstanding_cap=outstanding_cap,
        performance_targets=performance_targets,
        self_check_kinds=self_check_kinds,
        cl_bins=cl_bins,
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
        "pymtl3_available": bool(check.get("pymtl3_available")),
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
