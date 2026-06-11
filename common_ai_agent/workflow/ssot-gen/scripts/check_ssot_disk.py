#!/usr/bin/env python3
"""check_ssot_disk.py — Disk-truth validator for ssot-gen tasks.

Python port of check_ssot_disk.sh for native-Windows portability.

Verifies the SSOT YAML actually exists on disk with all required
top-level sections. Replaces "trust the LLM's reason text" approval
with concrete file inspection.

Inputs (env):
  IP_NAME — IP slug (auto-detected from cwd if missing)
  ATLAS_RUN_MODE — starter | engineering | signoff
  ATLAS_PROJECT_ROOT — parent directory containing <ip> directories
  ATLAS_IP_ROOT — optional active IP directory; parent becomes project root
  MIN_YAML — minimum bytes for <ip>.ssot.yaml (mode default)
  MIN_SECTIONS — minimum top-level section count (mode default)

Exit 0 = real SSOT YAML exists, has section keys, parses as YAML.
Exit 1 = file missing / too small / sections missing / not valid YAML.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


# ── Mode-specific REQUIRED key alternations (spelling matches ssot-template.yaml).
_REQUIRED_STARTER = "top_module|io_list|function_model"
_REQUIRED_ENGINEERING = (
    "top_module|sub_modules|decomposition|rtl_contract|parameters|io_list|features|"
    "dataflow|function_model|cycle_model|clock_reset_domains|cdc_requirements|"
    "rdc_requirements|registers|memory|interrupts|fsm|timing|power|security|"
    "error_handling|debug_observability|integration|synthesis|coding_rules|"
    "reuse_modules|custom|dir_structure|filelist|test_requirements|quality_gates|"
    "traceability|workflow_todos|generation_flow"
)
_REQUIRED_SIGNOFF = (
    "top_module|sub_modules|decomposition|rtl_contract|parameters|io_list|features|"
    "dataflow|function_model|cycle_model|clock_reset_domains|cdc_requirements|"
    "rdc_requirements|registers|memory|interrupts|fsm|timing|power|security|"
    "error_handling|debug_observability|integration|dft|synthesis|pnr|coding_rules|"
    "reuse_modules|custom|dir_structure|filelist|test_requirements|quality_gates|"
    "traceability|workflow_todos|generation_flow"
)


class _Fail(Exception):
    """Mirrors the embedded heredoc's SystemExit(message) — validation failure."""


def _combinational_locked_truth(ssot_path: "Path") -> bool:
    """True when EVERY locked behavioral contract is cycle-waived (combinational).

    Finding 23 (2026-06-11, add8_cin_v1): this script demanded a non-empty
    ``function_model.state_variables`` while the combinational gate
    (verify_ssot + repair_ssot_schema) demands it be EMPTY for cycle-waived
    IPs — a validator deadlock the authoring loop could never converge out of.
    Same predicate as verify_ssot._combinational_state_issues."""
    try:
        req = Path(ssot_path).resolve().parent.parent / "req" / "behavioral_contracts.json"
        if not req.is_file():
            return False
        workflow_root = Path(__file__).resolve().parents[2]
        if str(workflow_root) not in sys.path:
            sys.path.insert(0, str(workflow_root))
        import json as _json

        from behavioral_contracts import (  # type: ignore
            behavioral_contract_map,
            _cycle_model_waived,
        )

        doc = _json.loads(req.read_text(encoding="utf-8"))
        contracts = behavioral_contract_map(doc)
        return bool(contracts) and all(
            _cycle_model_waived(contract) for contract in contracts.values()
        )
    except Exception:
        return False


def _validate_yaml(path: str, run_mode: str) -> None:
    """Faithful port of the embedded python heredoc in check_ssot_disk.sh.

    Raises _Fail(message) where the shell raised SystemExit(message); returns
    normally where the shell exited 0 (sys.exit(0) or fall-through)."""
    import yaml

    run_mode = (run_mode or "signoff").strip().lower().replace("_", "-")
    ip = Path(path).parents[1].name
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    if not isinstance(doc, dict):
        raise _Fail("top-level YAML must be a mapping")

    def ci_get(item, *keys):
        if not isinstance(item, dict):
            return None
        lowered = {str(key).lower().replace("-", "_"): key for key in item}
        for key in keys:
            actual = lowered.get(str(key).lower().replace("-", "_"))
            if actual is not None:
                return item[actual]
        return None

    def present(value):
        if value is None or value is False:
            return False
        if isinstance(value, str):
            return bool(value.strip()) and value.strip().lower() not in {
                "none",
                "n/a",
                "na",
                "tbd",
                "todo",
                "<tbd>",
            }
        if isinstance(value, (list, tuple, set, dict)):
            return bool(value)
        return True

    def as_list(value):
        if isinstance(value, list):
            return value
        return []

    def rule_items(value):
        return [item for item in as_list(value) if isinstance(item, dict)]

    def norm_token(value):
        return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value or "")).strip("_")

    def collect_ports():
        io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
        ports = []
        for iface in io.get("interfaces") or []:
            if not isinstance(iface, dict):
                continue
            for port in iface.get("ports") or []:
                if isinstance(port, dict) and port.get("name"):
                    ports.append(port)
        return ports

    def rtl_quality_profile():
        qg = doc.get("quality_gates") if isinstance(doc.get("quality_gates"), dict) else {}
        rtl_gen = ci_get(qg, "rtl_gen", "rtl-gen", "rtl_gate")
        if not isinstance(rtl_gen, dict):
            rtl_gen = {}
        top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
        raw = (
            ci_get(rtl_gen, "profile", "quality_profile", "level", "signoff_profile")
            or ci_get(qg, "rtl_quality_profile", "quality_profile")
            or ci_get(top, "quality_profile", "rtl_quality_profile")
            or ""
        )
        norm = norm_token(raw)
        if norm in {"prod", "production", "signoff", "pl330", "pl330_level", "dma330", "dma330_level"}:
            return "production"
        name_text = f"{ip} {ci_get(top, 'name') or ''}".lower()
        if any(token in name_text for token in ("pl330", "dma330", "dma_330")):
            return "production"
        return "standard"

    def machine_connection_count(raw, default_module=""):
        count = 0
        if isinstance(raw, list):
            for item in raw:
                count += machine_connection_count(item, default_module)
            return count
        if not isinstance(raw, dict):
            return 0

        module = ci_get(raw, "module", "child", "target_module", "sink_module") or default_module
        for map_key in ("ports", "port_map", "connections"):
            nested = ci_get(raw, map_key)
            if isinstance(nested, dict):
                for port, signal in nested.items():
                    if str(module or "").strip() and str(port or "").strip() and str(signal or "").strip():
                        count += 1
                return count
            if isinstance(nested, list):
                for item in nested:
                    count += machine_connection_count(item, str(module or ""))
                return count

        port = ci_get(raw, "port", "child_port", "target_port", "sink_port", "to_port", "dst_port")
        signal = ci_get(raw, "signal", "expr", "expression", "source_signal", "from_signal", "top_signal")
        if str(module or "").strip() and str(port or "").strip() and str(signal or "").strip():
            return 1

        ignored = {
            "id",
            "name",
            "description",
            "note",
            "notes",
            "type",
            "rule",
            "module",
            "child",
            "target_module",
            "sink_module",
            "instance",
            "inst",
        }
        for key, value in raw.items():
            if str(key).lower() in ignored or isinstance(value, (dict, list)):
                continue
            if str(default_module or "").strip() and str(key or "").strip() and str(value or "").strip():
                count += 1
        return count

    def explicit_connection_contract_todo(items):
        for item in as_list(items):
            if not isinstance(item, dict):
                continue
            text = " ".join(
                [
                    str(item.get("id") or ""),
                    str(item.get("content") or ""),
                    str(item.get("detail") or ""),
                    " ".join(str(ref) for ref in as_list(item.get("source_refs"))),
                ]
            ).lower()
            if "connection" in text and ("integration" in text or "sub_modules" in text or "module" in text):
                return True
        return False

    def require_present(value, dpath):
        if not present(value):
            raise _Fail(f"{dpath} is required")
        return value

    def require_top_sub_module_consistency(doc, ip):
        top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
        top_name = str(ci_get(top, "name") or "").strip()
        top_file = str(ci_get(top, "file") or "").strip()
        if not top_name:
            raise _Fail("top_module.name is required")
        if not top_file and run_mode == "signoff":
            raise _Fail("top_module.file is required")
        subs = as_list(doc.get("sub_modules"))
        for idx, sub in enumerate(subs):
            if not isinstance(sub, dict):
                continue
            sname = str(ci_get(sub, "name") or "").strip()
            sfile = str(ci_get(sub, "file") or "").strip()
            wiring_only = bool(ci_get(sub, "wiring_only"))
            spath = f"sub_modules[{idx}]"
            if sname and sname == ip and not wiring_only:
                raise _Fail(
                    f"{spath}.name='{sname}' duplicates the IP name; rename, drop, "
                    "or mark wiring_only:true so rtl-gen can tell it from the top wrapper"
                )
            if sname and sname == top_name and top_name != ip:
                raise _Fail(
                    f"{spath}.name='{sname}' duplicates top_module.name; the top is "
                    "declared by top_module and must not appear as a sub_module entry"
                )
            if sfile and sfile == top_file and not wiring_only:
                raise _Fail(
                    f"{spath}.file='{sfile}' collides with top_module.file; mark this "
                    "entry wiring_only:true or change its file path"
                )

    def require_bit_range(field, fpath):
        bits = ci_get(field, "bits", "bit_range", "range")
        if isinstance(bits, list) and len(bits) == 2 and all(present(v) for v in bits):
            return
        if isinstance(bits, str) and re.search(r"\d+\s*[:,-]\s*\d+", bits):
            return
        if present(ci_get(field, "msb")) and present(ci_get(field, "lsb")):
            return
        if present(ci_get(field, "lsb")) and present(ci_get(field, "width", "bit_width")):
            return
        raise _Fail(f"{fpath} requires bits [msb, lsb] or lsb+width")

    def require_register_contract(regs):
        reg_list = as_list(regs.get("register_list"))
        no_reg_policy = ci_get(regs, "no_registers", "no_csr", "no_register_map")
        if not reg_list:
            if no_reg_policy and present(ci_get(regs, "reason", "policy", "access_model", "description")):
                return
            raise _Fail(
                "registers.register_list must be non-empty, or registers.no_registers/no_csr "
                "must state the no-register policy"
            )

        for ridx, reg in enumerate(reg_list):
            if not isinstance(reg, dict):
                raise _Fail(f"registers.register_list[{ridx}] must be a mapping")
            rname = require_present(ci_get(reg, "name"), f"registers.register_list[{ridx}].name")
            rpath = f"registers.register_list.{rname}"
            for key in ("offset", "width", "access", "reset"):
                require_present(ci_get(reg, key), f"{rpath}.{key}")
            fields = as_list(reg.get("fields"))
            if not fields:
                raise _Fail(f"{rpath}.fields must be a non-empty list with bit-level definitions")
            for fidx, field in enumerate(fields):
                if not isinstance(field, dict):
                    raise _Fail(f"{rpath}.fields[{fidx}] must be a mapping")
                fname = require_present(ci_get(field, "name"), f"{rpath}.fields[{fidx}].name")
                fpath = f"{rpath}.fields.{fname}"
                require_bit_range(field, fpath)
                for key in ("access", "reset", "description"):
                    require_present(ci_get(field, key), f"{fpath}.{key}")
                access = str(ci_get(field, "access") or "").lower()
                if access == "reserved":
                    require_present(ci_get(field, "read_value"), f"{fpath}.read_value")
                    require_present(ci_get(field, "write_effect"), f"{fpath}.write_effect")
                elif "w" in access:
                    write_semantics = ci_get(
                        field, "write_effect", "write_behavior", "write_side_effects", "side_effects"
                    ) or ci_get(reg, "write_effect", "write_behavior", "write_side_effects", "side_effects")
                    require_present(write_semantics, f"{fpath}.write_effect or {rpath}.write_side_effects")

    def require_interface_contract(io):
        for group_key in ("clock_domains", "resets", "interfaces"):
            if not isinstance(io.get(group_key), list) or not io[group_key]:
                raise _Fail(f"io_list.{group_key} must be a non-empty list")

        for idx, iface in enumerate(io.get("interfaces") or []):
            if not isinstance(iface, dict):
                raise _Fail(f"io_list.interfaces[{idx}] must be a mapping")
            name = require_present(ci_get(iface, "name"), f"io_list.interfaces[{idx}].name")
            ipath = f"io_list.interfaces.{name}"
            require_present(ci_get(iface, "type", "protocol_type"), f"{ipath}.type")
            require_present(ci_get(iface, "clock_domain", "clock"), f"{ipath}.clock_domain")
            ports = as_list(iface.get("ports"))
            if not ports:
                raise _Fail(f"{ipath}.ports must be a non-empty list")
            for pidx, port in enumerate(ports):
                if not isinstance(port, dict):
                    raise _Fail(f"{ipath}.ports[{pidx}] must be a mapping")
                pname = require_present(ci_get(port, "name"), f"{ipath}.ports[{pidx}].name")
                ppath = f"{ipath}.ports.{pname}"
                for key in ("direction", "width"):
                    require_present(ci_get(port, key), f"{ppath}.{key}")
            protocol = ci_get(iface, "protocol", "timing", "handshake", "transaction_rules", "transfer_rules")
            if not present(protocol):
                raise _Fail(
                    f"{ipath} requires protocol/timing/handshake rules; port declarations alone are not enough"
                )

    def require_coverage_contract(tr):
        goals = tr.get("coverage_goals")
        if not isinstance(goals, dict):
            raise _Fail("test_requirements.coverage_goals must be a mapping")
        for domain, model in (("function", "function_model"), ("cycle", "cycle_model")):
            section = ci_get(goals, domain, f"{domain}_coverage")
            if not isinstance(section, dict):
                raise _Fail(f"test_requirements.coverage_goals.{domain} must be a mapping")
            require_present(
                ci_get(section, "target_pct", "target", "minimum_pct"),
                f"test_requirements.coverage_goals.{domain}.target_pct",
            )
            require_present(ci_get(section, "model"), f"test_requirements.coverage_goals.{domain}.model")
            bins = as_list(section.get("bins") or section.get("planned_bins") or section.get("coverage_bins"))
            if not bins:
                raise _Fail(f"test_requirements.coverage_goals.{domain}.bins must be a non-empty list")
            for bidx, item in enumerate(bins):
                if not isinstance(item, dict):
                    raise _Fail(f"test_requirements.coverage_goals.{domain}.bins[{bidx}] must be a mapping")
                bpath = f"test_requirements.coverage_goals.{domain}.bins[{bidx}]"
                for key in ("id", "source_ref", "class", "description"):
                    require_present(ci_get(item, key), f"{bpath}.{key}")
                source_ref = str(ci_get(item, "source_ref") or "")
                if model not in source_ref and not (domain == "cycle" and source_ref.startswith("fsm.")):
                    raise _Fail(f"{bpath}.source_ref must trace to {model} or a declared FSM for cycle coverage")

    required_by_mode = {
        "starter": "top_module io_list function_model".split(),
        "engineering": (
            "top_module sub_modules decomposition rtl_contract parameters io_list features "
            "dataflow function_model cycle_model clock_reset_domains cdc_requirements "
            "rdc_requirements registers memory interrupts fsm timing power security "
            "error_handling debug_observability integration synthesis coding_rules "
            "reuse_modules custom dir_structure filelist test_requirements quality_gates "
            "traceability workflow_todos generation_flow"
        ).split(),
        "signoff": (
            "top_module sub_modules decomposition rtl_contract parameters io_list features "
            "dataflow function_model cycle_model clock_reset_domains cdc_requirements "
            "rdc_requirements registers memory interrupts fsm timing power security "
            "error_handling debug_observability integration dft synthesis pnr coding_rules "
            "reuse_modules custom dir_structure filelist test_requirements quality_gates "
            "traceability workflow_todos generation_flow"
        ).split(),
    }
    required = required_by_mode.get(run_mode, required_by_mode["signoff"])
    missing = [key for key in required if key not in doc]
    if "decomposition" in missing and "rtl_contract" in doc:
        missing.remove("decomposition")
    if missing:
        raise _Fail("missing required sections: " + ", ".join(missing))

    if run_mode == "starter":
        top = require_present(doc.get("top_module"), "top_module")
        if not isinstance(top, dict):
            raise _Fail("top_module must be a mapping")
        io_min = require_present(doc.get("io_list"), "io_list")
        if not isinstance(io_min, dict):
            raise _Fail("io_list must be a mapping")
        fm_min = require_present(doc.get("function_model"), "function_model")
        if not isinstance(fm_min, dict):
            raise _Fail("function_model must be a mapping")
        if not any(
            present(fm_min.get(key))
            for key in ("transactions", "invariants", "state_variables", "description", "rules")
        ):
            raise _Fail("function_model needs transactions, invariants, state_variables, description, or rules")
        return  # sys.exit(0)

    fm = doc.get("function_model")
    if not isinstance(fm, dict):
        raise _Fail("function_model must be a mapping")
    combinational = _combinational_locked_truth(Path(path))
    for key in ("state_variables", "transactions", "invariants"):
        value = fm.get(key)
        if key == "state_variables" and combinational:
            # Cycle-waived combinational locked truth: the combinational gate
            # requires state_variables to be EMPTY; demanding non-empty here
            # deadlocked SSOT authoring (finding 23). Absent or any list is
            # legal for these IPs.
            if value is None or isinstance(value, list):
                continue
            raise _Fail("function_model.state_variables must be a list")
        if not isinstance(value, list) or not value:
            raise _Fail(f"function_model.{key} must be a non-empty list")
    all_ports = collect_ports()
    output_ports = {
        str(port.get("name"))
        for port in all_ports
        if str(port.get("direction") or "").lower() in {"output", "inout"}
    }
    contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
    contract_output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}
    has_machine_output_rule = False
    for idx, tx in enumerate(fm.get("transactions") or []):
        if not isinstance(tx, dict):
            raise _Fail(f"function_model.transactions[{idx}] must be a mapping")
        for key in ("id", "name", "preconditions", "outputs"):
            if not tx.get(key):
                raise _Fail(f"function_model.transactions[{idx}].{key} is required")
        if not (tx.get("side_effects") or tx.get("error_cases")):
            raise _Fail(f"function_model.transactions[{idx}] needs side_effects or error_cases")
        has_tx_output_rule = False
        for ridx, rule in enumerate(rule_items(tx.get("output_rules"))):
            base = f"function_model.transactions[{idx}].output_rules[{ridx}]"
            name = ci_get(rule, "name", "output")
            expr = ci_get(rule, "expr", "expression", "value")
            width = ci_get(rule, "width", "bit_width")
            port = ci_get(rule, "port", "output_port")
            if not present(port) and present(name):
                port = contract_output_map.get(str(name))
            for key, value in (("name", name), ("expr", expr), ("width", width), ("port", port)):
                require_present(value, f"{base}.{key}")
            if output_ports and str(port) not in output_ports:
                raise _Fail(f"{base}.port must name a declared output port")
            has_machine_output_rule = True
            has_tx_output_rule = True
        has_tx_state_update = False
        for uidx, update in enumerate(rule_items(tx.get("state_updates"))):
            base = f"function_model.transactions[{idx}].state_updates[{uidx}]"
            name = ci_get(update, "name", "state", "target")
            expr = ci_get(update, "expr", "expression", "value", "next_value")
            width = ci_get(update, "width", "bit_width")
            for key, value in (("name", name), ("expr", expr), ("width", width)):
                require_present(value, f"{base}.{key}")
            has_tx_state_update = True
        tx_token = norm_token(f"{ci_get(tx, 'id') or ''} {ci_get(tx, 'name') or ''}")
        tx_parts = {part for part in tx_token.split("_") if part}
        is_reset_tx = "reset" in tx_parts or tx_token in {"fm_reset", "reset_behavior", "reset_sequence"}
        if not is_reset_tx and not (has_tx_output_rule or has_tx_state_update):
            raise _Fail(
                f"function_model.transactions[{idx}] must include executable output_rules or state_updates; "
                "prose outputs/side_effects are not scoreboard-comparable"
            )
    if not has_machine_output_rule:
        raise _Fail(
            "function_model.transactions[] must include at least one executable output_rules entry "
            "with name/expr/width/port"
        )

    cm = doc.get("cycle_model")
    if not isinstance(cm, dict):
        raise _Fail("cycle_model must be a mapping")
    for key in ("clock", "reset", "latency", "handshake_rules", "pipeline", "ordering"):
        if not cm.get(key):
            raise _Fail(f"cycle_model.{key} is required")
    for key in ("handshake_rules", "pipeline", "ordering"):
        if not isinstance(cm.get(key), list) or not cm.get(key):
            raise _Fail(f"cycle_model.{key} must be a non-empty list")
    if not isinstance(cm.get("performance"), dict) or not cm["performance"]:
        raise _Fail("cycle_model.performance must be a non-empty mapping for cycle/performance coverage")

    def require_mapping(section, keys=()):
        value = doc.get(section)
        if not isinstance(value, dict) or not value:
            raise _Fail(f"{section} must be a non-empty mapping")
        for key in keys:
            item = value.get(key)
            if item is None or item == "" or item == [] or item == {}:
                raise _Fail(f"{section}.{key} is required")
        return value

    require_top_sub_module_consistency(doc, ip)

    io = require_mapping("io_list", ("clock_domains", "resets", "interfaces"))
    require_interface_contract(io)

    regs = require_mapping("registers")
    require_register_contract(regs)

    require_mapping("rtl_contract", ("transaction", "input_map", "output_map"))

    timing = require_mapping("timing", ("target_clocks", "latency_budget"))
    if not isinstance(timing.get("target_clocks"), list) or not timing["target_clocks"]:
        raise _Fail("timing.target_clocks must be a non-empty list")

    power = require_mapping("power", ("domains", "power_states"))
    if not isinstance(power.get("domains"), list) or not power["domains"]:
        raise _Fail("power.domains must be a non-empty list")

    security = require_mapping("security", ("classification", "assets", "threat_model"))
    if not isinstance(security.get("assets"), list) or not security["assets"]:
        raise _Fail("security.assets must be a non-empty list")
    if not isinstance(security.get("threat_model"), list) or not security["threat_model"]:
        raise _Fail("security.threat_model must be a non-empty list")

    errors = require_mapping("error_handling", ("error_sources", "propagation", "recovery"))
    if not isinstance(errors.get("error_sources"), list) or not errors["error_sources"]:
        raise _Fail("error_handling.error_sources must be a non-empty list")

    debug = require_mapping("debug_observability", ("waveform_must_probe", "trace_events"))
    if not isinstance(debug.get("waveform_must_probe"), list) or not debug["waveform_must_probe"]:
        raise _Fail("debug_observability.waveform_must_probe must be a non-empty list")

    require_mapping("integration", ("bus_attachment", "dependencies"))
    if run_mode == "signoff":
        require_mapping("dft", ("scan_required", "controllability", "observability"))
    require_mapping("synthesis", ("dialect", "constraints", "required_outputs"))

    tr = require_mapping("test_requirements", ("scenarios", "scoreboard_checks", "coverage_goals"))
    if not isinstance(tr.get("scenarios"), list) or not tr["scenarios"]:
        raise _Fail("test_requirements.scenarios must be a non-empty list")
    require_coverage_contract(tr)
    for idx, sc in enumerate(tr.get("scenarios") or []):
        if not isinstance(sc, dict):
            raise _Fail(f"test_requirements.scenarios[{idx}] must be a mapping")
        for key in ("id", "name", "stimulus", "expected", "checker", "coverage"):
            if not sc.get(key):
                raise _Fail(f"test_requirements.scenarios[{idx}].{key} is required")

    qg = require_mapping("quality_gates")
    quality_gate_names = (
        ("ssot", "rtl", "dv", "coverage", "eda", "signoff")
        if run_mode == "signoff"
        else ("ssot", "rtl", "dv", "coverage")
    )
    for gate in quality_gate_names:
        item = qg.get(gate)
        if not isinstance(item, dict) or not item.get("pass") or not item.get("evidence"):
            raise _Fail(f"quality_gates.{gate}.pass and .evidence are required")

    profile = rtl_quality_profile()
    if profile == "production":
        rtl_gen_gate = ci_get(qg, "rtl_gen", "rtl-gen")
        if not isinstance(rtl_gen_gate, dict) or not rtl_gen_gate.get("pass") or not rtl_gen_gate.get("evidence"):
            raise _Fail("quality_gates.rtl_gen.pass and .evidence are required for production RTL-GEN")

        top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
        top_names = {str(ip).lower(), str(ci_get(top, "name") or "").lower()}
        active_manifest_children = []
        for idx, item in enumerate(as_list(doc.get("sub_modules"))):
            if not isinstance(item, dict):
                continue
            ownership = str(item.get("ownership") or "manifest").lower()
            if ownership in {"child_ssot", "external", "blackbox"}:
                continue
            name = str(item.get("name") or "").lower()
            if name in top_names:
                continue
            if bool(item.get("wiring_only")):
                continue
            active_manifest_children.append((idx, item))

        if active_manifest_children:
            machine_contracts = 0
            integration = doc.get("integration") if isinstance(doc.get("integration"), dict) else {}
            for key in ("connections", "internal_connections", "port_connections", "wiring"):
                machine_contracts += machine_connection_count(integration.get(key), "")
            for _, item in active_manifest_children:
                machine_contracts += machine_connection_count(item.get("connections"), str(item.get("name") or ""))
            workflow_todos = doc.get("workflow_todos") if isinstance(doc.get("workflow_todos"), dict) else {}
            if machine_contracts <= 0 and not explicit_connection_contract_todo(workflow_todos.get("rtl-gen")):
                raise _Fail(
                    "production multi-module SSOT requires machine-readable integration.connections "
                    "or sub_modules[].connections with module/port/signal records, or an explicit "
                    "workflow_todos.rtl-gen blocker that defers only top integration/signoff"
                )

    trace = require_mapping("traceability", ("yaml_to_output",))
    if not isinstance(trace.get("yaml_to_output"), list) or not trace["yaml_to_output"]:
        raise _Fail("traceability.yaml_to_output must be a non-empty list")

    workflow_todos = require_mapping("workflow_todos", ("rtl-gen",))
    rtl_todos = workflow_todos.get("rtl-gen")
    if not isinstance(rtl_todos, list) or not rtl_todos:
        raise _Fail("workflow_todos.rtl-gen must be a non-empty list")
    for idx, item in enumerate(rtl_todos):
        if not isinstance(item, dict):
            raise _Fail(f"workflow_todos.rtl-gen[{idx}] must be a mapping")
        for key in ("content", "detail", "criteria", "source_refs"):
            if not item.get(key):
                raise _Fail(f"workflow_todos.rtl-gen[{idx}].{key} is required")
        if not isinstance(item.get("criteria"), list) or not item["criteria"]:
            raise _Fail(f"workflow_todos.rtl-gen[{idx}].criteria must be a non-empty list")
        if not isinstance(item.get("source_refs"), list) or not item["source_refs"]:
            raise _Fail(f"workflow_todos.rtl-gen[{idx}].source_refs must be a non-empty list")


def _auto_detect_ip() -> str:
    """Replicate: find . -maxdepth 3 -type f -name '*.ssot.yaml'
    | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}'."""
    root = Path(".")
    matches: list[str] = []
    for pat in ("*/*/*.ssot.yaml", "*/*.ssot.yaml", "*.ssot.yaml"):
        for path in root.glob(pat):
            matches.append("./" + path.as_posix())

    def sort_key(item: str) -> str:
        parts = item.split("/")
        return parts[1] if len(parts) > 1 else ""

    matches.sort(key=sort_key)
    if not matches:
        return ""
    fields = matches[0].split("/")
    return fields[-3] if len(fields) >= 3 else ""


def _parse_args(argv: list[str]):
    """Port of the bash while/case CLI loop."""
    run_mode = os.environ.get("ATLAS_RUN_MODE", "signoff")
    project_root = os.environ.get("ATLAS_PROJECT_ROOT", "")
    ip_root = os.environ.get("ATLAS_IP_ROOT", "")
    ip = os.environ.get("IP_NAME", "")

    args = list(argv)
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("--root", "--project-root"):
            project_root = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        elif arg.startswith("--root=") or arg.startswith("--project-root="):
            project_root = arg.split("=", 1)[1]
            i += 1
        elif arg in ("--ip-root", "--ip_root"):
            ip_root = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        elif arg.startswith("--ip-root=") or arg.startswith("--ip_root="):
            ip_root = arg.split("=", 1)[1]
            i += 1
        elif arg == "--mode":
            run_mode = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        elif arg.startswith("--mode="):
            run_mode = arg[len("--mode="):]
            i += 1
        elif arg == "--run-mode":
            run_mode = args[i + 1] if i + 1 < len(args) else ""
            i += 2
        elif arg.startswith("--run-mode="):
            run_mode = arg[len("--run-mode="):]
            i += 1
        else:
            if not ip:
                ip = arg
            i += 1
    return run_mode, project_root, ip_root, ip


def main(argv: list[str]) -> int:
    run_mode, project_root, ip_root, ip = _parse_args(argv)

    # RUN_MODE=$(printf '%s' "$RUN_MODE" | tr '[:upper:]_' '[:lower:]-')
    run_mode = run_mode.lower().replace("_", "-")
    if run_mode in ("starter", "engineering", "signoff"):
        pass
    elif run_mode == "eng":
        run_mode = "engineering"
    elif run_mode == "sign-off":
        run_mode = "signoff"
    else:
        print("[check_ssot_disk] FAIL: --mode must be starter, engineering, or signoff")
        return 1

    if ip_root:
        if not Path(ip_root).is_dir():
            print(f"[check_ssot_disk] FAIL: --ip-root not found: {ip_root}")
            return 1
        ip_root = str(Path(ip_root).resolve())
        if not ip:
            ip = Path(ip_root).name
        if not project_root:
            project_root = str(Path(ip_root).parent)
    if project_root:
        if not Path(project_root).is_dir():
            print(f"[check_ssot_disk] FAIL: --root not found: {project_root}")
            return 1
        try:
            os.chdir(project_root)
        except OSError:
            print(f"[check_ssot_disk] FAIL: cannot cd to root: {project_root}")
            return 1

    if not ip:
        ip = _auto_detect_ip()

    # [ -z "$IP" ] || [ ! -d "$IP" ] && {...}  →  (empty OR not-dir) → fail
    if not ip or not Path(ip).is_dir():
        print("[check_ssot_disk] FAIL: IP dir not found")
        return 1

    # Locate the SSOT YAML (two naming conventions exist in the codebase).
    yaml_path = ""
    for cand in (
        f"{ip}/yaml/{ip}.ssot.yaml",
        f"{ip}/yaml/{ip}_ssot.yaml",
        f"{ip}/yaml/{ip}.ssot.yml",
    ):
        if Path(cand).is_file():
            yaml_path = cand
            break
    if not yaml_path:
        print(f"[check_ssot_disk] FAIL: no SSOT YAML at {ip}/yaml/{ip}.ssot.yaml or _ssot.yaml")
        return 1

    if run_mode == "starter":
        min_yaml = int(os.environ.get("MIN_YAML", "120"))
        min_sections = int(os.environ.get("MIN_SECTIONS", "3"))
        required = _REQUIRED_STARTER
    elif run_mode == "engineering":
        min_yaml = int(os.environ.get("MIN_YAML", "3000"))
        min_sections = int(os.environ.get("MIN_SECTIONS", "30"))
        required = _REQUIRED_ENGINEERING
    else:  # signoff
        min_yaml = int(os.environ.get("MIN_YAML", "4000"))
        min_sections = int(os.environ.get("MIN_SECTIONS", "34"))
        required = _REQUIRED_SIGNOFF

    yaml_file = Path(yaml_path)
    size = yaml_file.stat().st_size
    if size < min_yaml:
        print(f"[check_ssot_disk] FAIL: {yaml_path} = {size}B (need ≥{min_yaml})")
        return 1

    # Required canonical keys (spelling matches ssot-template.yaml).
    # HITS=$(grep -cE "^($REQUIRED):" "$YAML")
    yaml_text = yaml_file.read_text(encoding="utf-8", errors="replace")
    hits_re = re.compile(rf"^({required}):")
    hits = sum(1 for line in yaml_text.splitlines() if hits_re.search(line))
    if hits < min_sections:
        print(
            f"[check_ssot_disk] FAIL: {yaml_path} only has {hits} top-level section keys "
            f"(need ≥{min_sections})"
        )
        return 1

    # YAML parseability + model validation via the embedded validator.
    try:
        _validate_yaml(yaml_path, run_mode)
    except _Fail as exc:
        print(f"[check_ssot_disk] FAIL: {yaml_path} failed YAML/model validation")
        # cat /tmp/_ssot_yaml.err | head -10 | sed 's/^/  /'
        for line in str(exc).splitlines()[:10]:
            print(f"  {line}")
        return 1
    except Exception as exc:  # noqa: BLE001 — yaml.YAMLError etc. → stderr in shell
        print(f"[check_ssot_disk] FAIL: {yaml_path} failed YAML/model validation")
        for line in str(exc).splitlines()[:10]:
            print(f"  {line}")
        return 1

    # No live <TBD> markers in non-comment lines (template placeholders).
    # grep -vE '^\s*#' | grep -cE '<TBD>|<placeholder>|TODO: confirm'
    comment_re = re.compile(r"^\s*#")
    tbd_re = re.compile(r"<TBD>|<placeholder>|TODO: confirm")
    non_comment = [line for line in yaml_text.splitlines() if not comment_re.search(line)]
    tbd_count = sum(1 for line in non_comment if tbd_re.search(line))

    if run_mode == "starter":
        tbd_limit = int(os.environ.get("TBD_LIMIT", "25"))
    elif run_mode == "engineering":
        tbd_limit = int(os.environ.get("TBD_LIMIT", "10"))
    else:
        tbd_limit = int(os.environ.get("TBD_LIMIT", "5"))

    if tbd_count > tbd_limit:
        print(
            f"[check_ssot_disk] FAIL: {yaml_path} has {tbd_count} live TBD markers "
            f"(limit {tbd_limit} — resolve via /grill-me)"
        )
        return 1

    print(
        f"[check_ssot_disk] PASS: {yaml_path} = {size}B, {hits} sections, "
        f"{tbd_count} TBDs, mode={run_mode}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
