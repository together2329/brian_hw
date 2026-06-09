from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


JsonMap = dict[str, Any]
JsonList = list[Any]


@dataclass(frozen=True)
class Obligation:
    oid: str
    category: str
    source: str
    required: bool
    aliases: tuple[str, ...]


TOKEN_RE = re.compile(r"[^a-z0-9]+")
SCENARIO_WRAPPED_RE = re.compile(r"^sc_[0-9]+_eq_scenario_(.+)$")
TRANSACTION_WRAPPED_RE = re.compile(r"^eq_transaction_(.+)$")
SCENARIO_GOAL_RE = re.compile(r"^eq_scenario_(.+)$")
PREFIX_STRIPS = (
    "eq_register_",
    "eq_interrupt_",
    "eq_irq_",
    "eq_coverage_",
)
SUFFIX_STRIPS = (
    "_count_increment",
    "_increment",
    "_nonzero",
)
ARTIFACT_TOKENS = (
    ("model/fl_model_check.json", "model/fl_model_check.json_passed"),
    ("cov/fcov_plan.json", "cov/fcov_plan.json_created"),
    ("req/approval_manifest.json", "approval_manifest_hash_refreshed"),
)
PASS_GATE_TOKENS = {
    "ssot": ("verify_ssot_signoff_passes",),
    "rtl_compile": ("rtl_compile_passes",),
    "lint": ("lint_passes",),
    "tb_python_compile": ("check_tb_python_compile_passes",),
    "scoreboard": ("scoreboard_events_have_goal_ids",),
    "coverage": ("all_drop_scenarios_pass", "rtl_observed_keys_cover_expected_contract"),
}
RTL_TODO_PASS_TOKENS = (
    "axi_write_module_present",
    "all_required_modules_in_filelist",
    "no_missing_declared_module",
    "per_q_state_visible",
)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _norm(value: str) -> str:
    return TOKEN_RE.sub("_", value.strip().lower()).strip("_")


def _variants(value: str) -> set[str]:
    raw = value.strip()
    if not raw:
        return set()
    parts = {raw}
    if "." in raw:
        parts.add(raw.rsplit(".", 1)[-1])
    out = {_norm(part) for part in parts if _norm(part)}
    for item in list(out):
        if item.endswith("_executed"):
            out.add(item.removesuffix("_executed"))
        if item.endswith("_passes"):
            out.add(item.removesuffix("_passes"))
        if item.endswith("_observed"):
            out.add(item.removesuffix("_observed"))
        for prefix in PREFIX_STRIPS:
            if item.startswith(prefix):
                out.add(item.removeprefix(prefix))
        for suffix in SUFFIX_STRIPS:
            if item.endswith(suffix):
                out.add(item.removesuffix(suffix))
        scenario = SCENARIO_WRAPPED_RE.match(item)
        if scenario:
            out.add(scenario.group(1))
        transaction = TRANSACTION_WRAPPED_RE.match(item)
        if transaction:
            out.add(transaction.group(1))
        scenario_goal = SCENARIO_GOAL_RE.match(item)
        if scenario_goal:
            out.add(scenario_goal.group(1))
    return out


def _as_map(value: Any) -> JsonMap:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> JsonList:
    return value if isinstance(value, list) else []


def _load_json(path: Path) -> JsonMap:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return _as_map(data)


def _load_yaml(path: Path) -> JsonMap:
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    loaded = _as_map(data)
    if not loaded:
        raise SystemExit(f"invalid or empty SSOT YAML: {path}")
    return loaded


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _truthy_zero(value: Any) -> bool:
    return value is False or value == 0 or value == "0" or value == "0x0"


def _required(value: JsonMap) -> bool:
    if value.get("required") is False:
        return False
    if value.get("optional") is True or value.get("deferred") is True:
        return False
    status = _text(value.get("status")).lower()
    return status not in {"deferred", "optional", "future", "out_of_scope"}


def _obligation(oid: str, category: str, source: str, required: bool, aliases: set[str]) -> Obligation:
    merged = set(_variants(oid))
    for alias in aliases:
        merged.update(_variants(alias))
    return Obligation(oid=oid, category=category, source=source, required=required, aliases=tuple(sorted(merged)))


def _iter_named(items: Any, key: str) -> list[JsonMap]:
    out: list[JsonMap] = []
    for item in _as_list(items):
        data = _as_map(item)
        if _text(data.get(key)):
            out.append(data)
    return out


def _coverage_bins(test_reqs: JsonMap) -> list[JsonMap]:
    goals = _as_map(test_reqs.get("coverage_goals"))
    out: list[JsonMap] = []
    for value in goals.values():
        bins = _as_list(_as_map(value).get("bins"))
        for item in bins:
            data = _as_map(item)
            if _text(data.get("id")):
                out.append(data)
    return out


def _source_ref_aliases(test_reqs: JsonMap) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for item in _coverage_bins(test_reqs):
        bin_id = _text(item.get("id"))
        source_ref = _text(item.get("source_ref"))
        if not bin_id or not source_ref:
            continue
        for variant in _variants(source_ref):
            out.setdefault(variant, set()).add(bin_id)
    return out


def _ssot_obligations(ssot: JsonMap) -> list[Obligation]:
    out: list[Obligation] = []
    test_reqs = _as_map(ssot.get("test_requirements"))
    source_aliases = _source_ref_aliases(test_reqs)
    function_model = _as_map(ssot.get("function_model"))
    for item in _iter_named(function_model.get("transactions"), "id"):
        oid = _text(item.get("id"))
        out.append(_obligation(oid, "function_transaction", "function_model.transactions", _required(item), source_aliases.get(_norm(oid), set())))
    errors = _as_map(ssot.get("error_handling"))
    for item in _iter_named(errors.get("error_sources"), "id"):
        oid = _text(item.get("id"))
        out.append(_obligation(oid, "error_source", "error_handling.error_sources", _required(item), source_aliases.get(_norm(oid), set())))
    registers = _as_map(ssot.get("registers"))
    for item in _iter_named(registers.get("register_list"), "name"):
        oid = _text(item.get("name"))
        out.append(_obligation(oid, "register", "registers.register_list", _required(item), set()))
    interrupts = _as_map(ssot.get("interrupts"))
    for item in _iter_named(interrupts.get("sources"), "id"):
        oid = _text(item.get("id"))
        aliases = {_text(item.get("cause")), _text(item.get("enable"))}
        out.append(_obligation(oid, "interrupt", "interrupts.sources", _required(item), aliases))
    for item in _iter_named(test_reqs.get("scenarios"), "id"):
        oid = _text(item.get("id"))
        aliases = {_text(ref) for ref in _as_list(item.get("coverage")) if isinstance(ref, str)}
        out.append(_obligation(oid, "scenario", "test_requirements.scenarios", _required(item), aliases))
    for item in _coverage_bins(test_reqs):
        oid = _text(item.get("id"))
        aliases = {_text(item.get("source_ref"))}
        out.append(_obligation(oid, "coverage_bin", "test_requirements.coverage_goals", _required(item), aliases))
    workflow_todos = _as_map(ssot.get("workflow_todos"))
    for owner, items in workflow_todos.items():
        for idx, item in enumerate(_as_list(items)):
            data = _as_map(item)
            refs = {_text(ref) for ref in _as_list(data.get("source_refs")) if isinstance(ref, str)}
            for criterion in _as_list(data.get("criteria")):
                if isinstance(criterion, str) and criterion.strip():
                    out.append(_obligation(criterion, "acceptance_criterion", f"workflow_todos.{owner}[{idx}]", _required(data), refs))
    return out


def _ledger_obligations(path: Path) -> list[Obligation]:
    doc = _load_json(path)
    out: list[Obligation] = []
    for item in _as_list(doc.get("requirements")):
        data = _as_map(item)
        oid = _text(data.get("id"))
        if not oid:
            continue
        refs = {_text(ref) for ref in _as_list(data.get("evidence_refs")) if isinstance(ref, str)}
        out.append(_obligation(oid, "req_ledger", path.as_posix(), _required(data), refs))
    return out


def _add_tokens(tokens: set[str], value: str) -> None:
    tokens.update(_variants(value))


def _evidence_tokens(ip_dir: Path) -> set[str]:
    tokens: set[str] = set()
    sim_path = ip_dir / "sim" / "scoreboard_events.jsonl"
    # cov/coverage.json is only authoritative when a real sim actually ran, i.e.
    # there is >=1 PASSING scoreboard event. Without this provenance, a hand-written
    # coverage.json with obligation-named hit:true bins and a deleted sim/ silently
    # "covers" every required obligation.
    has_passing_event = False
    if sim_path.is_file():
        for raw in sim_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not raw.strip():
                continue
            row = _as_map(json.loads(raw))
            if row.get("passed") is not True:
                continue
            has_passing_event = True
            _add_tokens(tokens, _text(row.get("goal_id")))
            _add_tokens(tokens, _text(row.get("scenario_id")))
            for ref in _as_list(row.get("coverage_refs")):
                if isinstance(ref, str):
                    _add_tokens(tokens, ref)
            for key in _as_map(row.get("rtl_observed")):
                _add_tokens(tokens, key)
            stimulus = _as_map(row.get("stimulus"))
            for key, value in stimulus.items():
                _add_tokens(tokens, key)
                _add_tokens(tokens, _text(value))
            fl_expected = _as_map(row.get("fl_expected"))
            result = _as_map(fl_expected.get("model_result"))
            for key in _as_map(result.get("state_updates")):
                _add_tokens(tokens, key)
            observed = _as_map(row.get("rtl_observed"))
            row_text = " ".join(
                _norm(_text(value))
                for value in (row.get("goal_id"), row.get("scenario_id"), stimulus.get("kind"))
            )
            if any(marker in row_text for marker in ("packet_drop", "assembly_drop", "pd_", "ad_")):
                _add_tokens(tokens, "all_drop_scenarios_pass")
                if _truthy_zero(observed.get("sram_wr_valid")) or _truthy_zero(observed.get("sram_write_valid")):
                    _add_tokens(tokens, "no_sram_write_on_drop")
    coverage = _load_json(ip_dir / "cov" / "coverage.json") if has_passing_event else {}
    for section in ("function_coverage", "cycle_coverage"):
        bins = _as_map(_as_map(coverage.get(section)).get("bins"))
        for name, item in bins.items():
            data = _as_map(item)
            if data.get("hit") is not True:
                continue
            _add_tokens(tokens, name)
            _add_tokens(tokens, _text(data.get("goal_id")))
            _add_tokens(tokens, _text(data.get("scenario_id")))
            plan = _as_map(data.get("plan"))
            _add_tokens(tokens, _text(plan.get("source")))
    rtl_todo = _load_json(ip_dir / "rtl" / "rtl_todo_plan.json")
    gate = _as_map(rtl_todo.get("gate"))
    if gate.get("status") == "pass":
        for item in RTL_TODO_PASS_TOKENS:
            _add_tokens(tokens, item)
        for item in _as_list(gate.get("criteria")):
            if isinstance(item, str):
                _add_tokens(tokens, item)
    rtl_compile = _load_json(ip_dir / "rtl" / "rtl_compile.json")
    if rtl_compile.get("passed") is True and rtl_compile.get("dut_only") is True:
        for item in ("rtl_compile_passes", "all_required_modules_in_filelist", "no_missing_declared_module"):
            _add_tokens(tokens, item)
    dut_lint = _load_json(ip_dir / "lint" / "dut_lint.json")
    if dut_lint.get("passed") is True and dut_lint.get("dut_only") is True:
        _add_tokens(tokens, "lint_passes")
    monitor = _load_json(ip_dir / "sim" / "monitor_evidence.json")
    monitor_checks = _as_map(monitor.get("checks"))
    if monitor.get("status") == "pass" and monitor_checks.get("apb_per_q_readback_pass") is True:
        _add_tokens(tokens, "per_q_state_visible")
    for rel_path, token in ARTIFACT_TOKENS:
        if (ip_dir / rel_path).is_file():
            _add_tokens(tokens, token)
    signoff = _load_json(ip_dir / "signoff" / "ip_signoff.json")
    for gate_item in _as_list(signoff.get("gates")):
        data = _as_map(gate_item)
        if data.get("status") != "pass":
            continue
        gate_name = _text(data.get("name"))
        _add_tokens(tokens, gate_name)
        for token in PASS_GATE_TOKENS.get(gate_name, ()):
            _add_tokens(tokens, token)
    return tokens


def _dedupe(obligations: list[Obligation]) -> list[Obligation]:
    by_key: dict[tuple[str, str, str], Obligation] = {}
    for item in obligations:
        by_key[(item.category, item.oid, item.source)] = item
    return list(by_key.values())


def _report(ip: str, ip_dir: Path) -> JsonMap:
    ssot = _load_yaml(ip_dir / "yaml" / f"{ip}.ssot.yaml")
    ledger_path = ip_dir / "req" / "requirement_coverage.json"
    obligations = _ssot_obligations(ssot)
    source_mode = "direct_ssot"
    if ledger_path.is_file():
        obligations.extend(_ledger_obligations(ledger_path))
        source_mode = "ssot_plus_req_ledger"
    obligations = _dedupe(obligations)
    tokens = _evidence_tokens(ip_dir)
    covered = [item for item in obligations if set(item.aliases) & tokens]
    uncovered = [item for item in obligations if item.required and not (set(item.aliases) & tokens)]
    status = "fail" if uncovered else "pass"
    return {
        "schema_version": 1,
        "type": "truth_coverage",
        "generated_at": _utc(),
        "ip": ip,
        "status": status,
        "source_mode": source_mode,
        "summary": {
            "obligations": len(obligations),
            "covered": len(covered),
            "uncovered_required": len(uncovered),
            "evidence_tokens": len(tokens),
        },
        "uncovered_required": [
            {"id": item.oid, "category": item.category, "source": item.source, "aliases": list(item.aliases)}
            for item in uncovered
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    ip_dir = Path(args.root).resolve() / args.ip
    report = _report(args.ip, ip_dir)
    signoff_dir = ip_dir / "signoff"
    signoff_dir.mkdir(parents=True, exist_ok=True)
    json_path = signoff_dir / "truth_coverage.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[check_truth_coverage] status={report['status']} summary={report['summary']}")
    print(f"[check_truth_coverage] wrote {json_path}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
