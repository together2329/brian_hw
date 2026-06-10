from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from workflow.contract_reflection.evidence_contract_json import JsonList, JsonMap, as_list, as_map, load_json, strings, text


@dataclass(frozen=True)
class OwnerRoute:
    status: str
    owner_workflow: str
    reason: str
    suggested_commands: tuple[str, ...]
    rerun_after_repair: tuple[str, ...]


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def load_report(path: Path) -> JsonMap:
    if not path.is_file():
        return {}
    return load_json(path, "contract_owner")


def route_from_reports(ip_dir: Path) -> JsonMap:
    reflection = load_report(ip_dir / "signoff" / "contract_reflection_coverage.json")
    evidence = load_report(ip_dir / "signoff" / "evidence_contract_coverage.json")
    route = classify_route(reflection, evidence)
    return {
        "generated_at": utc_now(),
        "ip": ip_dir.name,
        "owner_workflow": route.owner_workflow,
        "reason": route.reason,
        "rerun_after_repair": _json_strings(route.rerun_after_repair),
        "schema_version": 1,
        "status": route.status,
        "suggested_commands": _json_strings(route.suggested_commands),
        "type": "contract_owner_routing",
    }


def classify_route(reflection: JsonMap, evidence: JsonMap) -> OwnerRoute:
    if text(reflection.get("status")) == "pass" and text(evidence.get("status")) == "pass":
        return OwnerRoute("pass", "", "contract reflection and evidence both pass", (), ())
    issue = _first_issue(reflection, evidence)
    owner = _owner_for_issue(issue)
    return OwnerRoute("blocked", owner, issue or "contract evidence is not closed", _commands_for(owner), _rerun_for(owner))


def _first_issue(reflection: JsonMap, evidence: JsonMap) -> str:
    for issue in strings(evidence.get("issues")):
        return issue
    for item in as_list(evidence.get("obligations")):
        data = as_map(item)
        for issue in strings(data.get("issues")):
            oid = text(data.get("obligation_id"))
            return f"{oid}: {issue}" if oid else issue
    for item in as_list(reflection.get("contract_refs")):
        data = as_map(item)
        for issue in strings(data.get("issues")):
            ref = text(data.get("contract_ref"))
            return f"{ref}: {issue}" if ref else issue
    return ""


def _owner_for_issue(issue: str) -> str:
    lower = issue.lower()
    if any(term in lower for term in ("unknown requirement", "missing obligation", "missing contract_refs", "missing pass_conditions")):
        return "contract-reflection"
    if any(term in lower for term in ("missing tb", "missing monitor", "missing observable", "no matching scoreboard row")):
        return "tb-gen"
    if any(term in lower for term in ("missing rtl", "rtl observable", "scoreboard row did not pass", "expected", "never reached", "changed while")):
        return "rtl-gen"
    if any(term in lower for term in ("vcd", "wave", "results.xml", "scoreboard")):
        return "sim_debug"
    return "contract-reflection"


def _commands_for(owner: str) -> tuple[str, ...]:
    table = {
        "tb-gen": ("/wf tb-gen", "/ssot-tb-cocotb <ip>", "/ssot-sim <ip>", "/contract-check <ip>"),
        "rtl-gen": ("/wf rtl-gen", "/ssot-rtl <ip>", "/lint-ip <ip>", "/ssot-sim <ip>", "/contract-check <ip>"),
        "sim_debug": ("/wf sim_debug", "/sim-debug <ip>", "/contract-check <ip>"),
        "contract-reflection": ("/wf contract-reflection", "/contract-check <ip>"),
    }
    return table.get(owner, ("/contract-check <ip>",))


def _rerun_for(owner: str) -> tuple[str, ...]:
    table = {
        "tb-gen": ("tb", "sim", "contract-check"),
        "rtl-gen": ("rtl", "lint", "tb", "sim", "contract-check"),
        "sim_debug": ("sim-debug", "contract-check"),
        "contract-reflection": ("contract-check",),
    }
    return table.get(owner, ("contract-check",))


def _json_strings(values: tuple[str, ...]) -> JsonList:
    out: JsonList = []
    for value in values:
        out.append(value)
    return out
