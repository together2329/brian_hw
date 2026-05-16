#!/usr/bin/env bash
# check_ssot_disk.sh — Disk-truth validator for ssot-gen tasks.
#
# Verifies the SSOT YAML actually exists on disk with all required
# top-level sections. Replaces "trust the LLM's reason text" approval
# with concrete file inspection.
#
# Inputs (env):
#   IP_NAME — IP slug (auto-detected from cwd if missing)
#   MIN_YAML — minimum bytes for <ip>.ssot.yaml (default 4000)
#   MIN_SECTIONS — minimum top-level section count (default 34)
#
# Exit 0 = real SSOT YAML exists, has section keys, parses as YAML.
# Exit 1 = file missing / too small / sections missing / not valid YAML.

set -u

IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi
[ -z "$IP" ] || [ ! -d "$IP" ] && { echo "[check_ssot_disk] FAIL: IP dir not found"; exit 1; }

# Locate the SSOT YAML (two naming conventions exist in the codebase).
YAML=""
for cand in "$IP/yaml/$IP.ssot.yaml" "$IP/yaml/${IP}_ssot.yaml" "$IP/yaml/$IP.ssot.yml"; do
    [ -f "$cand" ] && { YAML="$cand"; break; }
done
[ -z "$YAML" ] && { echo "[check_ssot_disk] FAIL: no SSOT YAML at $IP/yaml/${IP}.ssot.yaml or _ssot.yaml"; exit 1; }

MIN_YAML="${MIN_YAML:-4000}"
MIN_SECTIONS="${MIN_SECTIONS:-34}"

SZ=$(wc -c < "$YAML" | tr -d ' ')
[ "$SZ" -lt "$MIN_YAML" ] && { echo "[check_ssot_disk] FAIL: $YAML = ${SZ}B (need ≥${MIN_YAML})"; exit 1; }

# Required canonical keys (spelling matches ssot-template.yaml).
REQUIRED='top_module|sub_modules|decomposition|rtl_contract|parameters|io_list|features|dataflow|function_model|cycle_model|clock_reset_domains|cdc_requirements|rdc_requirements|registers|memory|interrupts|fsm|timing|power|security|error_handling|debug_observability|integration|dft|synthesis|pnr|coding_rules|reuse_modules|custom|dir_structure|filelist|test_requirements|quality_gates|traceability|workflow_todos|generation_flow'
HITS=$(grep -cE "^($REQUIRED):" "$YAML" || echo 0)
if [ "$HITS" -lt "$MIN_SECTIONS" ]; then
    echo "[check_ssot_disk] FAIL: $YAML only has $HITS top-level section keys (need ≥$MIN_SECTIONS)"
    exit 1
fi

# YAML parseability via python.
if command -v python3 >/dev/null 2>&1; then
    python3 - "$YAML" <<'PY' 2>/tmp/_ssot_yaml.err
import re
import sys
from pathlib import Path
import yaml

path = sys.argv[1]
ip = Path(path).parents[1].name
doc = yaml.safe_load(open(path, encoding="utf-8"))
if not isinstance(doc, dict):
    raise SystemExit("top-level YAML must be a mapping")

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
        return bool(value.strip()) and value.strip().lower() not in {"none", "n/a", "na", "tbd", "todo", "<tbd>"}
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

    ignored = {"id", "name", "description", "note", "notes", "type", "rule", "module", "child", "target_module", "sink_module", "instance", "inst"}
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

def require_present(value, path):
    if not present(value):
        raise SystemExit(f"{path} is required")
    return value

def require_bit_range(field, path):
    bits = ci_get(field, "bits", "bit_range", "range")
    if isinstance(bits, list) and len(bits) == 2 and all(present(v) for v in bits):
        return
    if isinstance(bits, str) and re.search(r"\d+\s*[:,-]\s*\d+", bits):
        return
    if present(ci_get(field, "msb")) and present(ci_get(field, "lsb")):
        return
    if present(ci_get(field, "lsb")) and present(ci_get(field, "width", "bit_width")):
        return
    raise SystemExit(f"{path} requires bits [msb, lsb] or lsb+width")

def require_register_contract(regs):
    reg_list = as_list(regs.get("register_list"))
    no_reg_policy = ci_get(regs, "no_registers", "no_csr", "no_register_map")
    if not reg_list:
        if no_reg_policy and present(ci_get(regs, "reason", "policy", "access_model", "description")):
            return
        raise SystemExit("registers.register_list must be non-empty, or registers.no_registers/no_csr must state the no-register policy")

    for ridx, reg in enumerate(reg_list):
        if not isinstance(reg, dict):
            raise SystemExit(f"registers.register_list[{ridx}] must be a mapping")
        rname = require_present(ci_get(reg, "name"), f"registers.register_list[{ridx}].name")
        rpath = f"registers.register_list.{rname}"
        for key in ("offset", "width", "access", "reset"):
            require_present(ci_get(reg, key), f"{rpath}.{key}")
        fields = as_list(reg.get("fields"))
        if not fields:
            raise SystemExit(f"{rpath}.fields must be a non-empty list with bit-level definitions")
        for fidx, field in enumerate(fields):
            if not isinstance(field, dict):
                raise SystemExit(f"{rpath}.fields[{fidx}] must be a mapping")
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
                write_semantics = (
                    ci_get(field, "write_effect", "write_behavior", "write_side_effects", "side_effects")
                    or ci_get(reg, "write_effect", "write_behavior", "write_side_effects", "side_effects")
                )
                require_present(write_semantics, f"{fpath}.write_effect or {rpath}.write_side_effects")

def require_interface_contract(io):
    for group_key in ("clock_domains", "resets", "interfaces"):
        if not isinstance(io.get(group_key), list) or not io[group_key]:
            raise SystemExit(f"io_list.{group_key} must be a non-empty list")

    for idx, iface in enumerate(io.get("interfaces") or []):
        if not isinstance(iface, dict):
            raise SystemExit(f"io_list.interfaces[{idx}] must be a mapping")
        name = require_present(ci_get(iface, "name"), f"io_list.interfaces[{idx}].name")
        ipath = f"io_list.interfaces.{name}"
        require_present(ci_get(iface, "type", "protocol_type"), f"{ipath}.type")
        require_present(ci_get(iface, "clock_domain", "clock"), f"{ipath}.clock_domain")
        ports = as_list(iface.get("ports"))
        if not ports:
            raise SystemExit(f"{ipath}.ports must be a non-empty list")
        for pidx, port in enumerate(ports):
            if not isinstance(port, dict):
                raise SystemExit(f"{ipath}.ports[{pidx}] must be a mapping")
            pname = require_present(ci_get(port, "name"), f"{ipath}.ports[{pidx}].name")
            ppath = f"{ipath}.ports.{pname}"
            for key in ("direction", "width"):
                require_present(ci_get(port, key), f"{ppath}.{key}")
        protocol = ci_get(iface, "protocol", "timing", "handshake", "transaction_rules", "transfer_rules")
        if not present(protocol):
            raise SystemExit(f"{ipath} requires protocol/timing/handshake rules; port declarations alone are not enough")

def require_coverage_contract(tr):
    goals = tr.get("coverage_goals")
    if not isinstance(goals, dict):
        raise SystemExit("test_requirements.coverage_goals must be a mapping")
    for domain, model in (("function", "function_model"), ("cycle", "cycle_model")):
        section = ci_get(goals, domain, f"{domain}_coverage")
        if not isinstance(section, dict):
            raise SystemExit(f"test_requirements.coverage_goals.{domain} must be a mapping")
        require_present(ci_get(section, "target_pct", "target", "minimum_pct"), f"test_requirements.coverage_goals.{domain}.target_pct")
        require_present(ci_get(section, "model"), f"test_requirements.coverage_goals.{domain}.model")
        bins = as_list(section.get("bins") or section.get("planned_bins") or section.get("coverage_bins"))
        if not bins:
            raise SystemExit(f"test_requirements.coverage_goals.{domain}.bins must be a non-empty list")
        for bidx, item in enumerate(bins):
            if not isinstance(item, dict):
                raise SystemExit(f"test_requirements.coverage_goals.{domain}.bins[{bidx}] must be a mapping")
            bpath = f"test_requirements.coverage_goals.{domain}.bins[{bidx}]"
            for key in ("id", "source_ref", "class", "description"):
                require_present(ci_get(item, key), f"{bpath}.{key}")
            source_ref = str(ci_get(item, "source_ref") or "")
            if model not in source_ref and not (domain == "cycle" and source_ref.startswith("fsm.")):
                raise SystemExit(f"{bpath}.source_ref must trace to {model} or a declared FSM for cycle coverage")

required = "top_module sub_modules decomposition rtl_contract parameters io_list features dataflow function_model cycle_model clock_reset_domains cdc_requirements rdc_requirements registers memory interrupts fsm timing power security error_handling debug_observability integration dft synthesis pnr coding_rules reuse_modules custom dir_structure filelist test_requirements quality_gates traceability workflow_todos generation_flow".split()
missing = [key for key in required if key not in doc]
if "decomposition" in missing and "rtl_contract" in doc:
    missing.remove("decomposition")
if missing:
    raise SystemExit("missing required sections: " + ", ".join(missing))

fm = doc.get("function_model")
if not isinstance(fm, dict):
    raise SystemExit("function_model must be a mapping")
for key in ("state_variables", "transactions", "invariants"):
    if not isinstance(fm.get(key), list) or not fm.get(key):
        raise SystemExit(f"function_model.{key} must be a non-empty list")
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
        raise SystemExit(f"function_model.transactions[{idx}] must be a mapping")
    for key in ("id", "name", "preconditions", "outputs"):
        if not tx.get(key):
            raise SystemExit(f"function_model.transactions[{idx}].{key} is required")
    if not (tx.get("side_effects") or tx.get("error_cases")):
        raise SystemExit(f"function_model.transactions[{idx}] needs side_effects or error_cases")
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
            raise SystemExit(f"{base}.port must name a declared output port")
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
        raise SystemExit(
            f"function_model.transactions[{idx}] must include executable output_rules or state_updates; "
            "prose outputs/side_effects are not scoreboard-comparable"
        )
if not has_machine_output_rule:
    raise SystemExit("function_model.transactions[] must include at least one executable output_rules entry with name/expr/width/port")

cm = doc.get("cycle_model")
if not isinstance(cm, dict):
    raise SystemExit("cycle_model must be a mapping")
for key in ("clock", "reset", "latency", "handshake_rules", "pipeline", "ordering"):
    if not cm.get(key):
        raise SystemExit(f"cycle_model.{key} is required")
for key in ("handshake_rules", "pipeline", "ordering"):
    if not isinstance(cm.get(key), list) or not cm.get(key):
        raise SystemExit(f"cycle_model.{key} must be a non-empty list")
if not isinstance(cm.get("performance"), dict) or not cm["performance"]:
    raise SystemExit("cycle_model.performance must be a non-empty mapping for cycle/performance coverage")

def require_mapping(section: str, keys: tuple[str, ...] = ()) -> dict:
    value = doc.get(section)
    if not isinstance(value, dict) or not value:
        raise SystemExit(f"{section} must be a non-empty mapping")
    for key in keys:
        item = value.get(key)
        if item is None or item == "" or item == [] or item == {}:
            raise SystemExit(f"{section}.{key} is required")
    return value

io = require_mapping("io_list", ("clock_domains", "resets", "interfaces"))
require_interface_contract(io)

regs = require_mapping("registers")
require_register_contract(regs)

require_mapping("rtl_contract", ("transaction", "input_map", "output_map"))

timing = require_mapping("timing", ("target_clocks", "latency_budget"))
if not isinstance(timing.get("target_clocks"), list) or not timing["target_clocks"]:
    raise SystemExit("timing.target_clocks must be a non-empty list")

power = require_mapping("power", ("domains", "power_states"))
if not isinstance(power.get("domains"), list) or not power["domains"]:
    raise SystemExit("power.domains must be a non-empty list")

security = require_mapping("security", ("classification", "assets", "threat_model"))
if not isinstance(security.get("assets"), list) or not security["assets"]:
    raise SystemExit("security.assets must be a non-empty list")
if not isinstance(security.get("threat_model"), list) or not security["threat_model"]:
    raise SystemExit("security.threat_model must be a non-empty list")

errors = require_mapping("error_handling", ("error_sources", "propagation", "recovery"))
if not isinstance(errors.get("error_sources"), list) or not errors["error_sources"]:
    raise SystemExit("error_handling.error_sources must be a non-empty list")

debug = require_mapping("debug_observability", ("waveform_must_probe", "trace_events"))
if not isinstance(debug.get("waveform_must_probe"), list) or not debug["waveform_must_probe"]:
    raise SystemExit("debug_observability.waveform_must_probe must be a non-empty list")

require_mapping("integration", ("bus_attachment", "dependencies"))
require_mapping("dft", ("scan_required", "controllability", "observability"))
require_mapping("synthesis", ("dialect", "constraints", "required_outputs"))

tr = require_mapping("test_requirements", ("scenarios", "scoreboard_checks", "coverage_goals"))
if not isinstance(tr.get("scenarios"), list) or not tr["scenarios"]:
    raise SystemExit("test_requirements.scenarios must be a non-empty list")
require_coverage_contract(tr)
for idx, sc in enumerate(tr.get("scenarios") or []):
    if not isinstance(sc, dict):
        raise SystemExit(f"test_requirements.scenarios[{idx}] must be a mapping")
    for key in ("id", "name", "stimulus", "expected", "checker", "coverage"):
        if not sc.get(key):
            raise SystemExit(f"test_requirements.scenarios[{idx}].{key} is required")

qg = require_mapping("quality_gates")
for gate in ("ssot", "rtl", "dv", "coverage", "eda", "signoff"):
    item = qg.get(gate)
    if not isinstance(item, dict) or not item.get("pass") or not item.get("evidence"):
        raise SystemExit(f"quality_gates.{gate}.pass and .evidence are required")

profile = rtl_quality_profile()
if profile == "production":
    rtl_gen_gate = ci_get(qg, "rtl_gen", "rtl-gen")
    if not isinstance(rtl_gen_gate, dict) or not rtl_gen_gate.get("pass") or not rtl_gen_gate.get("evidence"):
        raise SystemExit("quality_gates.rtl_gen.pass and .evidence are required for production RTL-GEN")

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
            raise SystemExit(
                "production multi-module SSOT requires machine-readable integration.connections "
                "or sub_modules[].connections with module/port/signal records, or an explicit "
                "workflow_todos.rtl-gen blocker that defers only top integration/signoff"
            )

trace = require_mapping("traceability", ("yaml_to_output",))
if not isinstance(trace.get("yaml_to_output"), list) or not trace["yaml_to_output"]:
    raise SystemExit("traceability.yaml_to_output must be a non-empty list")

workflow_todos = require_mapping("workflow_todos", ("rtl-gen",))
rtl_todos = workflow_todos.get("rtl-gen")
if not isinstance(rtl_todos, list) or not rtl_todos:
    raise SystemExit("workflow_todos.rtl-gen must be a non-empty list")
for idx, item in enumerate(rtl_todos):
    if not isinstance(item, dict):
        raise SystemExit(f"workflow_todos.rtl-gen[{idx}] must be a mapping")
    for key in ("content", "detail", "criteria", "source_refs"):
        if not item.get(key):
            raise SystemExit(f"workflow_todos.rtl-gen[{idx}].{key} is required")
    if not isinstance(item.get("criteria"), list) or not item["criteria"]:
        raise SystemExit(f"workflow_todos.rtl-gen[{idx}].criteria must be a non-empty list")
    if not isinstance(item.get("source_refs"), list) or not item["source_refs"]:
        raise SystemExit(f"workflow_todos.rtl-gen[{idx}].source_refs must be a non-empty list")
PY
    if [ $? -ne 0 ]; then
        echo "[check_ssot_disk] FAIL: $YAML failed YAML/model validation"
        cat /tmp/_ssot_yaml.err | head -10 | sed 's/^/  /'
        exit 1
    fi
fi

# No live <TBD> markers in non-comment lines (template placeholders).
TBD_COUNT=$(grep -vE '^\s*#' "$YAML" | grep -cE '<TBD>|<placeholder>|TODO: confirm' | head -1 | tr -d '[:space:]')
TBD_COUNT="${TBD_COUNT:-0}"
if [ "$TBD_COUNT" -gt 5 ]; then
    echo "[check_ssot_disk] FAIL: $YAML has $TBD_COUNT live TBD markers (limit 5 — resolve via /grill-me)"
    exit 1
fi

echo "[check_ssot_disk] PASS: $YAML = ${SZ}B, ${HITS} sections, ${TBD_COUNT} TBDs"
exit 0
