#!/usr/bin/env python3
"""Emit sim/scenario_e2e_summary.json from GENUINE run evidence.

NO FABRICATION: this counts only directed scenarios that genuinely executed and
passed, derived from the real artifacts a sim run leaves behind:

  * SSOT yaml/<ip>.ssot.yaml test_requirements.scenarios — the REQUIRED directed
    scenario set (missing_scenarios = any SSOT scenario with no passing evidence).
  * sim/scoreboard_datapath_rows.jsonl — the IP-specific FL-vs-RTL datapath test's
    real rows (one per scenario/goal); a scenario is "passed" only if it appears
    with passed=true and never passed=false.
  * sim/scoreboard_events.jsonl — the generic goal harness rows (covers
    SC_PRIORITY / SC_REG and the per-register EQ_REGISTER_* goals the datapath
    test does not drive).
  * tb/cocotb/results.xml — the cocotb testcase verdicts; the content-readback
    (test_pl_readback sc_rb_*), SRAM-write monitor, and APB-readback testcases
    each contribute their directed scenario ONLY if their testcase passed.

A scenario_id like "SC_SINGLE_single_packet" is normalized to its canonical
SC_* token so sub-variants are not double-counted. failed_scenarios collects any
scenario that has a genuine failing row / failing testcase. The emitter does NOT
invent scenarios or pad the count; if <26 genuinely passed it reports the true
number and the gate stays red.

Usage: python3 emit_scenario_e2e_summary.py            (paths inferred)
"""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
IP_DIR = HERE.parent.parent
IP = IP_DIR.name

SSOT_PATH = IP_DIR / "yaml" / f"{IP}.ssot.yaml"
DATAPATH_ROWS = IP_DIR / "sim" / "scoreboard_datapath_rows.jsonl"
EVENTS_ROWS = IP_DIR / "sim" / "scoreboard_events.jsonl"
RESULTS_XML = IP_DIR / "tb" / "cocotb" / "results.xml"
OUT_PATH = IP_DIR / "sim" / "scenario_e2e_summary.json"

# A DIRECTED scenario id is a named SC_<NAME> token (e.g. SC_SINGLE, SC_RB_4096,
# SC_PD_MCTP) — NOT the generic goal-harness row id form `SC_<digits>_EQ_...`
# (those are one auto-generated row PER equivalence goal, e.g.
# "SC_001_EQ_TRANSACTION_FM_INGEST_TLP", and must NOT be counted as directed
# scenarios — that would pad the count). The named-directed token starts with a
# non-numeric segment after "SC_". When a generic-goal row's id embeds a real
# SSOT scenario (e.g. "SC_025_EQ_SCENARIO_SC_PRIORITY" embeds SC_PRIORITY), the
# SSOT-substring match below still credits the embedded directed scenario.
_DIRECTED_RE = re.compile(r"\bSC_[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\b")
_GENERIC_GOAL_RE = re.compile(r"^SC_\d+_")


def _ssot_scenarios() -> list[str]:
    import yaml  # PyYAML is available in the sim runtime env
    doc = yaml.safe_load(SSOT_PATH.read_text(encoding="utf-8"))
    tr = doc.get("test_requirements") or {}
    out: list[str] = []
    for s in tr.get("scenarios") or []:
        sid = s.get("id") or s.get("scenario_id") or s.get("name") if isinstance(s, dict) else s
        if sid:
            out.append(str(sid))
    return out


def _canon(sid: str, ssot_ids: set[str]) -> str | None:
    """Map a raw scenario_id to the directed scenario it evidences, or None if it
    is only a generic per-goal harness row (not a directed scenario).

    Priority: (1) if it embeds an SSOT scenario id, credit that (longest first,
    so SC_FW_READ_SLVERR beats SC_FW_READ); (2) else, if it is the generic-goal
    row form SC_<digits>_EQ_... with no embedded SSOT scenario, return None (NOT
    a directed scenario — never counted); (3) else, return the named SC_<NAME>
    directed token (an extra directed scenario the IP-specific tests drove)."""
    if not sid:
        return None
    s = str(sid)
    for cand in sorted(ssot_ids, key=len, reverse=True):
        if cand in s:
            return cand
    if _GENERIC_GOAL_RE.match(s):
        return None
    m = _DIRECTED_RE.search(s)
    if not m:
        return None
    tok = m.group(0)
    # Reject a bare generic token that slipped through (e.g. SC_123).
    if _GENERIC_GOAL_RE.match(tok + "_"):
        return None
    return tok


def _scan_jsonl(path: Path, ssot_ids: set[str]) -> tuple[dict[str, bool], dict[str, bool]]:
    """Return (passed_map, failed_map) keyed by canonical scenario id. A scenario
    is failed if ANY of its rows has passed=false."""
    passed: dict[str, bool] = {}
    failed: dict[str, bool] = {}
    if not path.is_file():
        return passed, failed
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        sid = row.get("scenario_id") or (row.get("stimulus") or {}).get("scenario_id")
        cid = _canon(sid, ssot_ids)
        if not cid:
            continue
        if row.get("passed") is True:
            passed[cid] = True
        elif row.get("passed") is False:
            failed[cid] = True
    return passed, failed


def _scan_results_xml(path: Path, ssot_ids: set[str]) -> tuple[dict[str, bool], dict[str, bool]]:
    """Directed scenarios contributed by cocotb testcases (content readback,
    SRAM-write monitor, APB readback). A testcase contributes its scenarios only
    if it has no failure/error node. We map known testcase names to the directed
    scenario ids they prove."""
    # testcase name -> directed scenario ids that testcase genuinely proves
    case_scenarios = {
        "sc_rb_single": ["SC_RB_SINGLE"],
        "sc_rb_64": ["SC_RB_64"],
        "sc_rb_frag": ["SC_RB_FRAG"],
        "sc_rb_4096": ["SC_RB_4096"],
        "sram_write_monitor": ["SC_SRAM_WRITE_MON"],
        "apb_per_q_descriptor_readback": ["SC_APB_DESC_READBACK"],
    }
    passed: dict[str, bool] = {}
    failed: dict[str, bool] = {}
    if not path.is_file():
        return passed, failed
    root = ET.parse(path).getroot()
    for tc in root.findall(".//testcase"):
        name = tc.attrib.get("name") or ""
        ids = case_scenarios.get(name)
        if not ids:
            continue
        is_fail = bool(tc.findall("failure") or tc.findall("error"))
        for sid in ids:
            (failed if is_fail else passed)[sid] = True
    return passed, failed


def main() -> int:
    ssot = _ssot_scenarios()
    ssot_ids = set(ssot)

    dp_pass, dp_fail = _scan_jsonl(DATAPATH_ROWS, ssot_ids)
    ev_pass, ev_fail = _scan_jsonl(EVENTS_ROWS, ssot_ids)
    xml_pass, xml_fail = _scan_results_xml(RESULTS_XML, ssot_ids)

    failed: dict[str, bool] = {}
    for m in (dp_fail, ev_fail, xml_fail):
        failed.update(m)

    passed: dict[str, bool] = {}
    for m in (dp_pass, ev_pass, xml_pass):
        for k in m:
            passed[k] = True

    # A scenario only counts as genuinely passing if it passed and is not in the
    # failed set (any failing row disqualifies it).
    passing_scenarios = sorted(s for s in passed if s not in failed)
    failed_scenarios = sorted(failed)
    missing_scenarios = sorted(s for s in ssot if s not in passing_scenarios)

    total = len(passing_scenarios)
    status = "pass" if (total >= 26 and not missing_scenarios and not failed_scenarios) else "fail"

    payload = {
        "ip": IP,
        "status": status,
        "total_directed_scenarios": total,
        "ssot_scenarios": ssot,
        "ssot_scenario_count": len(ssot),
        "passing_scenarios": passing_scenarios,
        "missing_scenarios": missing_scenarios,
        "failed_scenarios": failed_scenarios,
        "evidence": {
            "datapath_rows": str(DATAPATH_ROWS.relative_to(IP_DIR)),
            "events_rows": str(EVENTS_ROWS.relative_to(IP_DIR)),
            "results_xml": str(RESULTS_XML.relative_to(IP_DIR)),
            "datapath_passing": sorted(dp_pass),
            "events_passing": sorted(ev_pass),
            "cocotb_passing": sorted(xml_pass),
        },
        "note": ("Directed scenarios that genuinely executed and passed, derived "
                 "from real scoreboard rows + cocotb testcase verdicts. Not padded."),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[emit_scenario_e2e_summary] status={status} "
          f"total_directed_scenarios={total} missing={missing_scenarios} "
          f"failed={failed_scenarios} -> {OUT_PATH.relative_to(IP_DIR.parent)}")
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
