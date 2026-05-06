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
#   MIN_SECTIONS — minimum top-level section count (default 33)
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
MIN_SECTIONS="${MIN_SECTIONS:-33}"

SZ=$(wc -c < "$YAML" | tr -d ' ')
[ "$SZ" -lt "$MIN_YAML" ] && { echo "[check_ssot_disk] FAIL: $YAML = ${SZ}B (need ≥${MIN_YAML})"; exit 1; }

# Required canonical keys (spelling matches ssot-template.yaml).
REQUIRED='top_module|sub_modules|parameters|io_list|features|dataflow|function_model|cycle_model|clock_reset_domains|cdc_requirements|rdc_requirements|registers|memory|interrupts|fsm|timing|power|security|error_handling|debug_observability|integration|dft|synthesis|coding_rules|reuse_modules|custom|dir_structure|filelist|test_requirements|quality_gates|traceability|workflow_todos|generation_flow'
HITS=$(grep -cE "^($REQUIRED):" "$YAML" || echo 0)
if [ "$HITS" -lt "$MIN_SECTIONS" ]; then
    echo "[check_ssot_disk] FAIL: $YAML only has $HITS top-level section keys (need ≥$MIN_SECTIONS)"
    exit 1
fi

# YAML parseability via python.
if command -v python3 >/dev/null 2>&1; then
    python3 - "$YAML" <<'PY' 2>/tmp/_ssot_yaml.err
import sys
import yaml

path = sys.argv[1]
doc = yaml.safe_load(open(path, encoding="utf-8"))
if not isinstance(doc, dict):
    raise SystemExit("top-level YAML must be a mapping")

required = "top_module sub_modules parameters io_list features dataflow function_model cycle_model clock_reset_domains cdc_requirements rdc_requirements registers memory interrupts fsm timing power security error_handling debug_observability integration dft synthesis coding_rules reuse_modules custom dir_structure filelist test_requirements quality_gates traceability workflow_todos generation_flow".split()
missing = [key for key in required if key not in doc]
if missing:
    raise SystemExit("missing required sections: " + ", ".join(missing))

fm = doc.get("function_model")
if not isinstance(fm, dict):
    raise SystemExit("function_model must be a mapping")
for key in ("state_variables", "transactions", "invariants"):
    if not isinstance(fm.get(key), list) or not fm.get(key):
        raise SystemExit(f"function_model.{key} must be a non-empty list")
for idx, tx in enumerate(fm.get("transactions") or []):
    if not isinstance(tx, dict):
        raise SystemExit(f"function_model.transactions[{idx}] must be a mapping")
    for key in ("id", "name", "preconditions", "outputs"):
        if not tx.get(key):
            raise SystemExit(f"function_model.transactions[{idx}].{key} is required")
    if not (tx.get("side_effects") or tx.get("error_cases")):
        raise SystemExit(f"function_model.transactions[{idx}] needs side_effects or error_cases")

cm = doc.get("cycle_model")
if not isinstance(cm, dict):
    raise SystemExit("cycle_model must be a mapping")
for key in ("clock", "reset", "latency", "handshake_rules", "pipeline", "ordering"):
    if not cm.get(key):
        raise SystemExit(f"cycle_model.{key} is required")
for key in ("handshake_rules", "pipeline", "ordering"):
    if not isinstance(cm.get(key), list) or not cm.get(key):
        raise SystemExit(f"cycle_model.{key} must be a non-empty list")

def require_mapping(section: str, keys: tuple[str, ...] = ()) -> dict:
    value = doc.get(section)
    if not isinstance(value, dict) or not value:
        raise SystemExit(f"{section} must be a non-empty mapping")
    for key in keys:
        item = value.get(key)
        if item is None or item == "" or item == [] or item == {}:
            raise SystemExit(f"{section}.{key} is required")
    return value

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
