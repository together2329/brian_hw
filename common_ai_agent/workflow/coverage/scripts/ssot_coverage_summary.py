#!/usr/bin/env python3
"""Summarize SSOT-driven coverage evidence for any leaf IP.

Inputs:
  <ip>/yaml/<ip>.ssot.yaml      SSOT authority for scenarios/goals
  <ip>/cov/coverage.info        LCOV from verilator_coverage --write-info
  <ip>/cov/coverage*.json       Functional bins/checks from TB runs

Outputs:
  <ip>/cov/coverage.json        UI-facing combined coverage snapshot
  <ip>/cov/coverage_ssot.json   Same payload, explicitly SSOT-scoped
  <ip>/sim/coverage_report.md   Human-readable sim_debug report
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - tool env issue is reported at runtime
    yaml = None


def pct(hit: int, total: int) -> float | None:
    return round((hit / total) * 100.0, 2) if total else None


def threshold(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        for key in ("target", "pct", "percent", "minimum", "min"):
            out = threshold(value.get(key))
            if out is not None:
                return out
        return threshold(" ".join(str(v) for v in value.values()))
    if isinstance(value, list):
        return threshold(" ".join(str(v) for v in value))
    if isinstance(value, str):
        m = re.search(r"(?:>=|>|at\s+least|minimum|min)?\s*(\d+(?:\.\d+)?)\s*%", value, re.I)
        if m:
            return float(m.group(1))
        m = re.search(r"\b(\d+(?:\.\d+)?)\b", value)
        if m:
            return float(m.group(1))
    return None


def find_ssot(ip_dir: Path) -> Path | None:
    preferred = [
        ip_dir / "yaml" / f"{ip_dir.name}.ssot.yaml",
        ip_dir / "yaml" / f"{ip_dir.name}_ssot.yaml",
        ip_dir / "yaml" / f"{ip_dir.name}_config.yaml",
    ]
    for path in preferred:
        if path.is_file():
            return path
    yaml_dir = ip_dir / "yaml"
    if yaml_dir.is_dir():
        matches = sorted(yaml_dir.glob("*.yaml"))
        return matches[0] if matches else None
    return None


def load_ssot(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    if yaml is None:
        raise SystemExit("ERROR: PyYAML is required to parse SSOT YAML")
    data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    return data if isinstance(data, dict) else {}


def parse_lcov(path: Path) -> dict[str, Any]:
    totals = {
        "lines": {"hit": 0, "total": 0, "pct": None},
        "branches": {"hit": 0, "total": 0, "pct": None},
        "functions": {"hit": 0, "total": 0, "pct": None},
        "files": {},
    }
    if not path.is_file():
        return totals

    current: str | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("SF:"):
            current = raw[3:]
            totals["files"].setdefault(
                current,
                {
                    "lines": {"hit": 0, "total": 0},
                    "branches": {"hit": 0, "total": 0},
                    "functions": {"hit": 0, "total": 0},
                },
            )
        elif current and raw.startswith("LF:"):
            val = int(raw[3:] or 0)
            totals["files"][current]["lines"]["total"] = val
        elif current and raw.startswith("LH:"):
            val = int(raw[3:] or 0)
            totals["files"][current]["lines"]["hit"] = val
        elif current and raw.startswith("BRF:"):
            val = int(raw[4:] or 0)
            totals["files"][current]["branches"]["total"] = val
        elif current and raw.startswith("BRH:"):
            val = int(raw[4:] or 0)
            totals["files"][current]["branches"]["hit"] = val
        elif current and raw.startswith("FNF:"):
            val = int(raw[4:] or 0)
            totals["files"][current]["functions"]["total"] = val
        elif current and raw.startswith("FNH:"):
            val = int(raw[4:] or 0)
            totals["files"][current]["functions"]["hit"] = val

    for metric in ("lines", "branches", "functions"):
        hit = sum(f[metric]["hit"] for f in totals["files"].values())
        total = sum(f[metric]["total"] for f in totals["files"].values())
        totals[metric] = {"hit": hit, "total": total, "pct": pct(hit, total)}
    return totals


def load_fcov_plan(cov_dir: Path) -> dict[str, Any]:
    path = cov_dir / "fcov_plan.json"
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def planned_bin_ids(fcov_plan: dict[str, Any]) -> list[str]:
    out: list[str] = []
    bins = fcov_plan.get("bins") if isinstance(fcov_plan.get("bins"), list) else []
    for idx, item in enumerate(bins):
        if not isinstance(item, dict):
            continue
        bid = str(item.get("id") or item.get("name") or f"planned_bin_{idx}").strip()
        if bid and bid not in out:
            out.append(bid)
    return out


def bin_hit(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        return bool(value.get("hit") or value.get("passed") or value.get("covered") or value.get("count", 0))
    if isinstance(value, (int, float)):
        return value > 0
    return bool(value)


def extract_functional_bins(doc: dict[str, Any]) -> dict[str, Any]:
    bins: dict[str, Any] = {}
    raw_bins = doc.get("functional_bins")
    if isinstance(raw_bins, dict):
        bins.update(raw_bins)
    functional = doc.get("functional") if isinstance(doc.get("functional"), dict) else {}
    nested = functional.get("bins") if isinstance(functional.get("bins"), dict) else {}
    bins.update(nested)
    return bins


def load_json_obj(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _looks_like_fl_copy(observed: dict[str, Any], row: dict[str, Any]) -> bool:
    """Reject coverage evidence that copied FL payload instead of DUT signals."""
    if set(observed) == {"model_result"}:
        return True
    fl_expected = row.get("fl_expected") if isinstance(row.get("fl_expected"), dict) else {}
    if observed == fl_expected:
        return True
    return False


def scoreboard_coverage(ip_dir: Path) -> dict[str, Any]:
    """Return coverage refs proven by passing FL-vs-RTL scoreboard events.

    This is intentionally stricter than raw functional-bin sampling. A bin is
    covered only when a scoreboard row passed and carried concrete RTL-observed
    signal values. The FL model can define expected values, but it cannot be
    counted as the observed side of coverage.
    """
    goals_doc = load_json_obj(ip_dir / "verify" / "equivalence_goals.json")
    goal_refs = {
        str(ref)
        for goal in goals_doc.get("goals", []) if isinstance(goal, dict) and goal.get("blocked") is not True
        for ref in (goal.get("coverage_refs") or [])
        if str(ref).strip()
    }
    rows = load_jsonl_rows(ip_dir / "sim" / "scoreboard_events.jsonl")
    bins: dict[str, Any] = {}
    invalid_rows: list[dict[str, Any]] = []
    passed_rows = 0
    for idx, row in enumerate(rows, 1):
        refs = [str(ref) for ref in (row.get("coverage_refs") or []) if str(ref).strip()]
        if not refs:
            continue
        if row.get("passed") is not True:
            continue
        observed = row.get("rtl_observed")
        if not isinstance(observed, dict) or not observed:
            invalid_rows.append({"row": idx, "goal_id": row.get("goal_id"), "reason": "missing rtl_observed"})
            continue
        if _looks_like_fl_copy(observed, row):
            invalid_rows.append({"row": idx, "goal_id": row.get("goal_id"), "reason": "rtl_observed copies FL/model_result"})
            continue
        passed_rows += 1
        for ref in refs:
            bins[ref] = {
                "hit": True,
                "source": "scoreboard_events",
                "goal_id": row.get("goal_id"),
                "scenario_id": row.get("scenario_id"),
                "rtl_observed_keys": sorted(str(key) for key in observed),
            }
    return {
        "bins": bins,
        "goal_refs": sorted(goal_refs),
        "scoreboard_events": len(rows),
        "scoreboard_passed_events_with_refs": passed_rows,
        "invalid_rows": invalid_rows,
    }


def merge_functional_cov(cov_dir: Path) -> dict[str, Any]:
    bins: dict[str, Any] = {}
    escalations: list[dict[str, Any]] = []
    passed = failed = total_checks = 0
    limitations: dict[str, Any] = {}
    for path in sorted(cov_dir.glob("coverage*.json")) if cov_dir.is_dir() else []:
        try:
            doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        if path.name in {"coverage_ssot.json", "coverage_instrumented.json"}:
            continue
        if path.name == "coverage.json" and doc.get("source") == "ssot_coverage_summary":
            continue
        bins.update(extract_functional_bins(doc))
        for src, dst in (("passed", "passed"), ("failed", "failed"), ("total_checks", "total_checks")):
            try:
                val = int(doc.get(src, 0) or 0)
            except Exception:
                val = 0
            if dst == "passed":
                passed += val
            elif dst == "failed":
                failed += val
            else:
                total_checks += val
        raw_escalations = doc.get("escalations")
        if isinstance(raw_escalations, list):
            escalations.extend(e for e in raw_escalations if isinstance(e, dict))
        raw_limits = doc.get("static_universe_not_instrumented")
        if isinstance(raw_limits, dict):
            limitations.update(raw_limits)
    hit = sum(1 for value in bins.values() if bin_hit(value))
    total = len(bins)
    return {
        "functional_bins": bins,
        "functional": {"hit": hit, "total": total, "pct": pct(hit, total)},
        "passed": passed,
        "failed": failed,
        "total_checks": total_checks,
        "escalations": escalations,
        "legacy_limitations": limitations,
    }


def goal_map(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        out: dict[str, Any] = {}
        for idx, item in enumerate(raw):
            if isinstance(item, dict):
                key = str(item.get("metric") or item.get("name") or f"goal_{idx}")
                out[key] = item
            else:
                out[f"goal_{idx}"] = item
        return out
    return {}


def _metric_tokens(raw: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(raw).lower()))


def _metric_key_matches(raw: Any, names: tuple[str, ...]) -> bool:
    text = str(raw).lower().replace("-", "_")
    if text in names:
        return True
    tokens = _metric_tokens(text)
    return any(name in tokens for name in names)


def _metric_text_matches(raw: Any, names: tuple[str, ...]) -> bool:
    text = str(raw).lower()
    phrases = {
        "line": ("line coverage", "line >=", "lines >=", "line >"),
        "code": ("code coverage", "code >=", "structural code coverage"),
        "branch": ("branch coverage", "branch >=", "branches >=", "branch >"),
        "fsm": ("fsm coverage", "fsm-state", "fsm state", "fsm >=", "fsm >"),
        "functional": ("functional coverage", "functional bins", "functional >="),
        "scenario": ("scenario coverage", "scenarios pass", "scenario bins"),
        "transition": ("transition coverage", "transition bins"),
    }
    return any(phrase in text for name in names for phrase in phrases.get(name, ()))


def metric_goal(goals: dict[str, Any], names: tuple[str, ...]) -> Any:
    names = tuple(name.lower() for name in names)
    for key, value in goals.items():
        if _metric_key_matches(key, names):
            return value
        if isinstance(value, dict):
            for field in ("metric", "name", "type", "coverage_type"):
                if _metric_key_matches(value.get(field), names):
                    return value
            text = " ".join(str(value.get(field) or "") for field in ("goal", "description", "target", "criteria"))
        else:
            text = value
        if _metric_text_matches(text, names):
            return value
    return None


def bin_coverage(functional_bins: dict[str, Any], names: tuple[str, ...]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    for bid, value in functional_bins.items():
        text = bid
        if isinstance(value, dict):
            text = " ".join([bid, str(value.get("class") or ""), str(value.get("source") or "")])
        if _metric_key_matches(text, names):
            selected[bid] = value
    hit = sum(1 for value in selected.values() if bin_hit(value))
    total = len(selected)
    return {"hit": hit, "total": total, "pct": pct(hit, total), "bins": selected}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: ssot_coverage_summary.py <ip>", file=sys.stderr)
        return 2
    ip_dir = Path(sys.argv[1]).resolve()
    cov_dir = ip_dir / "cov"
    sim_dir = ip_dir / "sim"
    cov_dir.mkdir(parents=True, exist_ok=True)
    sim_dir.mkdir(parents=True, exist_ok=True)

    ssot_path = find_ssot(ip_dir)
    ssot = load_ssot(ssot_path)
    tr = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    scenarios = tr.get("scenarios") if isinstance(tr.get("scenarios"), list) else []
    goals = goal_map(tr.get("coverage_goals"))
    scoreboard_checks = tr.get("scoreboard_checks")

    lcov_path = cov_dir / "coverage.info"
    lcov = parse_lcov(lcov_path)
    raw_functional = merge_functional_cov(cov_dir)
    rtl_cov = scoreboard_coverage(ip_dir)
    fcov_plan = load_fcov_plan(cov_dir)
    planned_bins = planned_bin_ids(fcov_plan)
    raw_bins = raw_functional["functional_bins"]
    rtl_bins = rtl_cov["bins"] if isinstance(rtl_cov.get("bins"), dict) else {}
    all_bin_ids: list[str] = []
    for source in (planned_bins, list(raw_bins), list(rtl_bins), rtl_cov.get("goal_refs") or []):
        for bid in source:
            text = str(bid)
            if text and text not in all_bin_ids:
                all_bin_ids.append(text)

    functional_bins: dict[str, Any] = {}
    for bid in all_bin_ids:
        if bid in rtl_bins:
            item = dict(rtl_bins[bid])
            item["raw_hit"] = bin_hit(raw_bins.get(bid)) if bid in raw_bins else None
            functional_bins[bid] = item
            continue
        raw_value = raw_bins.get(bid, {"hit": False, "source": "fcov_plan"})
        functional_bins[bid] = {
            "hit": False,
            "raw_hit": bin_hit(raw_value),
            "source": "missing_rtl_observed_scoreboard_evidence",
            "raw": raw_value,
        }

    functional = {
        **raw_functional,
        "functional_bins": functional_bins,
        "functional": {
            "hit": sum(1 for value in functional_bins.values() if bin_hit(value)),
            "total": len(functional_bins),
            "pct": pct(sum(1 for value in functional_bins.values() if bin_hit(value)), len(functional_bins)),
        },
    }

    line_goal = metric_goal(goals, ("line", "code"))
    branch_goal = metric_goal(goals, ("branch",))
    fsm_goal = metric_goal(goals, ("fsm",))
    functional_goal = metric_goal(goals, ("functional", "scenario", "transition"))
    line_target = threshold(line_goal)
    branch_target = threshold(branch_goal)
    fsm_target = threshold(fsm_goal)
    functional_target = threshold(functional_goal)
    if functional_target is None and all_bin_ids:
        functional_target = 100.0

    fsm_bins = bin_coverage(functional["functional_bins"], ("fsm",))
    if fsm_goal is not None and fsm_target is None and fsm_bins["total"]:
        fsm_target = 100.0

    limitations: dict[str, Any] = {}
    if not planned_bins:
        limitations["fcov_plan"] = "No planned functional coverage bins found in cov/fcov_plan.json."
    missing_rtl_bins = sorted(bid for bid in all_bin_ids if not bin_hit(functional_bins.get(bid)))
    raw_hit_without_rtl = sorted(
        bid
        for bid, value in raw_bins.items()
        if bin_hit(value) and bid not in rtl_bins
    )
    if all_bin_ids and not rtl_cov.get("scoreboard_events"):
        limitations["rtl_observed_coverage"] = (
            "Functional coverage requires passing scoreboard_events.jsonl rows with concrete rtl_observed signals; "
            "no scoreboard rows were found."
        )
    elif missing_rtl_bins:
        limitations["rtl_observed_coverage"] = (
            "Functional bins are not covered until a passing scoreboard row with real rtl_observed signals hits them: "
            + ", ".join(missing_rtl_bins[:12])
            + ("" if len(missing_rtl_bins) <= 12 else f", ... +{len(missing_rtl_bins) - 12}")
        )
    if raw_hit_without_rtl:
        limitations["raw_functional_only_bins"] = (
            "Raw functional hits are debug evidence only and did not count because no RTL-observed scoreboard row proved them: "
            + ", ".join(raw_hit_without_rtl[:12])
            + ("" if len(raw_hit_without_rtl) <= 12 else f", ... +{len(raw_hit_without_rtl) - 12}")
        )
    invalid_rows = rtl_cov.get("invalid_rows") if isinstance(rtl_cov.get("invalid_rows"), list) else []
    if invalid_rows:
        limitations["invalid_scoreboard_coverage_rows"] = invalid_rows[:12]
    if line_goal is not None and lcov["lines"]["total"] == 0:
        limitations["line"] = "SSOT requests line/code coverage, but coverage.info has no DA records."
    if branch_goal is not None and lcov["branches"]["total"] == 0:
        limitations["branch"] = "SSOT requests branch coverage, but coverage.info has no BRDA/BRF records for this tool flow."
    if fsm_goal is not None and fsm_bins["total"] == 0:
        limitations["fsm_state"] = (
            "SSOT requests FSM coverage, but no SSOT-derived functional FSM bins or instrumented FSM metric was present."
        )
    for key, value in functional.get("legacy_limitations", {}).items():
        limitations.setdefault(key, value)

    line_ok = line_target is None or (lcov["lines"]["pct"] is not None and lcov["lines"]["pct"] >= line_target)
    branch_ok = branch_target is None or (lcov["branches"]["pct"] is not None and lcov["branches"]["pct"] >= branch_target)
    fsm_ok = fsm_goal is None or (
        fsm_bins["pct"] is not None and (fsm_target is None or fsm_bins["pct"] >= fsm_target)
    )
    checks_ok = functional["failed"] == 0
    functional_ok = (
        functional_target is None
        or (
            functional["functional"]["pct"] is not None
            and functional["functional"]["pct"] >= functional_target
        )
    )
    status = "pass" if (line_ok and branch_ok and fsm_ok and checks_ok and functional_ok and not limitations) else "blocked"
    if functional["failed"] > 0:
        status = "fail"

    payload = {
        "source": "ssot_coverage_summary",
        "status": status,
        "ssot": str(ssot_path.relative_to(ip_dir.parent)) if ssot_path else "",
        "module": ip_dir.name,
        "dv_plan": {
            "scenarios": len(scenarios),
            "scoreboard_checks": scoreboard_checks,
            "coverage_goals": goals,
        },
        "functional": functional["functional"],
        "planned_bins": planned_bins,
        "functional_bins": functional["functional_bins"],
        "raw_functional": raw_functional["functional"],
        "raw_functional_bins": raw_bins,
        "rtl_observed": {
            "status": "pass" if all_bin_ids and not missing_rtl_bins and not invalid_rows else "blocked",
            "scoreboard_events": rtl_cov.get("scoreboard_events", 0),
            "scoreboard_passed_events_with_refs": rtl_cov.get("scoreboard_passed_events_with_refs", 0),
            "goal_refs": rtl_cov.get("goal_refs", []),
            "missing_bins": missing_rtl_bins,
            "invalid_rows": invalid_rows,
        },
        "lines": {**lcov["lines"], "target_pct": line_target, "meets_target": line_ok},
        "branches": {**lcov["branches"], "target_pct": branch_target, "meets_target": branch_ok},
        "functions": lcov["functions"],
        "fsm_state": {
            "target_pct": fsm_target,
            "hit": fsm_bins["hit"],
            "total": fsm_bins["total"],
            "pct": fsm_bins["pct"],
            "meets_target": fsm_ok,
            "source": "SSOT functional coverage bins" if fsm_bins["total"] else "not automatically measured by generic LCOV parser",
        },
        "files": lcov["files"],
        "limitations": limitations,
        "static_universe_not_instrumented": limitations,
        "total_checks": functional["total_checks"],
        "passed": functional["passed"],
        "failed": functional["failed"],
        "escalations": functional["escalations"],
    }

    (cov_dir / "coverage_ssot.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (cov_dir / "coverage.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    report = [
        f"# {ip_dir.name} SSOT coverage report",
        "",
        f"SSOT: `{payload['ssot'] or 'missing'}`",
        f"Status: `{status}`",
        "",
        f"DV scenarios: {len(scenarios)}",
        f"Scoreboard checks: {scoreboard_checks}",
        f"Functional bins: {functional['functional']['hit']}/{functional['functional']['total']}",
        (
            "RTL-observed coverage events: "
            f"{rtl_cov.get('scoreboard_passed_events_with_refs', 0)}/{rtl_cov.get('scoreboard_events', 0)}"
        ),
        f"Line coverage: {lcov['lines']['hit']}/{lcov['lines']['total']} ({lcov['lines']['pct']}%) target={line_target}",
        f"Branch coverage: {lcov['branches']['hit']}/{lcov['branches']['total']} ({lcov['branches']['pct']}%) target={branch_target}",
        f"FSM-state coverage: {fsm_bins['hit']}/{fsm_bins['total']} ({fsm_bins['pct']}%) target={fsm_target}",
        "",
        "## Limitations",
    ]
    if limitations:
        report.extend(f"- {key}: {value}" for key, value in limitations.items())
    else:
        report.append("- none")
    (sim_dir / "coverage_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"SSOT coverage summary: {cov_dir / 'coverage.json'}")
    print(f"SSOT coverage report : {sim_dir / 'coverage_report.md'}")
    print(f"Status               : {status}")
    return 0 if status == "pass" else 3


if __name__ == "__main__":
    raise SystemExit(main())
