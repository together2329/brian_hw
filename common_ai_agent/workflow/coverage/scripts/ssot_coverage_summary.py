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


def threshold_for_metric(value: Any, names: tuple[str, ...]) -> float | None:
    """Extract a target for one metric from combined SSOT text.

    SSOTs commonly write compact goals such as
    ``code: line >= 90%, branch >= 85%``. A plain first-number parser would
    incorrectly assign 90% to both line and branch coverage, so try a
    metric-scoped parse before falling back to the generic threshold helper.
    """
    names = tuple(name.lower() for name in names)
    aliases = {
        "line": ("line", "lines"),
        "code": ("code",),
        "branch": ("branch", "branches"),
        "fsm": ("fsm", "fsm_state", "fsm-state"),
        "function": ("function", "function_model", "function model"),
        "functional": ("functional",),
        "cycle": ("cycle", "cycle_model", "cycle model"),
        "scenario": ("scenario",),
        "transition": ("transition",),
    }
    if isinstance(value, dict):
        for key, item in value.items():
            if _metric_key_matches(key, names):
                out = threshold(item)
                if out is not None:
                    return out
        return threshold(value)
    if isinstance(value, list):
        return threshold_for_metric(" ".join(str(v) for v in value), names)
    if isinstance(value, str):
        text = value.lower()
        metric_aliases = []
        for name in names:
            metric_aliases.extend(aliases.get(name, (name,)))
        for alias in metric_aliases:
            escaped = re.escape(alias).replace(r"\ ", r"\s+")
            patterns = (
                rf"\b{escaped}\b(?:\s+coverage)?\s*(?:>=|>|at\s+least|minimum|min)?\s*(\d+(?:\.\d+)?)\s*%",
                rf"(\d+(?:\.\d+)?)\s*%\s*(?:minimum|min|target)?\s*\b{escaped}\b",
            )
            for pattern in patterns:
                m = re.search(pattern, text, re.I)
                if m:
                    return float(m.group(1))
    return threshold(value)


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


def _is_lcov_branch_source_line(lines: list[str], line_no: int) -> bool:
    if line_no <= 0 or line_no > len(lines):
        return False
    text = lines[line_no - 1].strip()
    if not text or text.startswith("//"):
        return False
    declaration_prefixes = (
        "input ",
        "output ",
        "inout ",
        "logic ",
        "wire ",
        "reg ",
        "localparam ",
        "parameter ",
    )
    if text.startswith(declaration_prefixes):
        return False
    return any(token in text for token in ("if ", "if(", "else", "case", "?", "&&", "||"))


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
    source_lines: dict[str, list[str]] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if raw.startswith("SF:"):
            current = raw[3:]
            src_path = Path(current)
            if src_path.is_file():
                source_lines[current] = src_path.read_text(encoding="utf-8", errors="replace").splitlines()
            else:
                source_lines[current] = []
            totals["files"].setdefault(
                current,
                {
                    "lines": {"hit": 0, "total": 0},
                    "branches": {"hit": 0, "total": 0},
                    "functions": {"hit": 0, "total": 0},
                    "_da": {},
                    "_brda": [],
                    "_fn": set(),
                    "_fnda": {},
                },
            )
        elif current and raw.startswith("DA:"):
            fields = raw[3:].split(",")
            if len(fields) >= 2:
                try:
                    line_no = int(fields[0])
                    count = int(fields[1])
                except ValueError:
                    continue
                totals["files"][current]["_da"][line_no] = count
        elif current and raw.startswith("BRDA:"):
            fields = raw[5:].split(",")
            if len(fields) >= 4:
                taken = fields[3].strip()
                try:
                    line_no = int(fields[0])
                except ValueError:
                    line_no = 0
                totals["files"][current]["_brda"].append((line_no, taken))
        elif current and raw.startswith("FN:"):
            fields = raw[3:].split(",", 1)
            if len(fields) == 2:
                totals["files"][current]["_fn"].add(fields[1].strip())
        elif current and raw.startswith("FNDA:"):
            fields = raw[5:].split(",", 1)
            if len(fields) == 2:
                try:
                    count = int(fields[0])
                except ValueError:
                    continue
                totals["files"][current]["_fnda"][fields[1].strip()] = count
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

    for source, file_cov in totals["files"].items():
        da = file_cov.pop("_da", {})
        brda = file_cov.pop("_brda", [])
        fn = file_cov.pop("_fn", set())
        fnda = file_cov.pop("_fnda", {})
        if da:
            file_cov["lines"] = {
                "hit": sum(1 for count in da.values() if count != 0),
                "total": len(da),
            }
        if brda:
            filtered = [
                taken
                for line_no, taken in brda
                if _is_lcov_branch_source_line(source_lines.get(source, []), line_no)
            ]
            # If source text is unavailable, keep legacy LCOV behavior. If
            # source text is available, prefer source-aware branch bins so
            # Verilator toggle/expression bins on declarations do not masquerade
            # as control-flow branch coverage.
            branch_taken = filtered if source_lines.get(source) else [taken for _line, taken in brda]
            file_cov["branches"] = {
                "hit": sum(1 for taken in branch_taken if taken not in {"", "-", "0"}),
                "total": len(branch_taken),
            }
        if fn or fnda:
            names = set(fn) | set(fnda)
            file_cov["functions"] = {
                "hit": sum(1 for name in names if int(fnda.get(name, 0) or 0) != 0),
                "total": len(names),
            }

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


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _bin_id(item: Any, idx: int, prefix: str = "planned_bin") -> str:
    if isinstance(item, dict):
        return str(item.get("id") or item.get("name") or f"{prefix}_{idx}").strip()
    return str(item or f"{prefix}_{idx}").strip()


def _norm_bin_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")


def _norm_source_ref(item: dict[str, Any]) -> str:
    for key in ("source_ref", "source", "ssot_ref"):
        value = item.get(key)
        if value:
            return _norm_bin_key(value)
    return ""


def _planned_bin_matches(a_id: str, a: dict[str, Any], b_id: str, b: dict[str, Any]) -> bool:
    if _norm_bin_key(a_id) and _norm_bin_key(a_id) == _norm_bin_key(b_id):
        return True
    a_ref = _norm_source_ref(a)
    b_ref = _norm_source_ref(b)
    return bool(a_ref and b_ref and a_ref == b_ref)


def _add_planned_bin(out: dict[str, dict[str, Any]], bid: str, item: dict[str, Any]) -> None:
    """Insert a planned bin while merging SSOT/fcov case variants.

    SSOT bins often keep human-facing IDs such as ``FCOV_RULE_DOUBLE`` while
    generated fcov/equivalence evidence normalizes them to
    ``fcov_rule_double``. They are the same coverage bin when either the ID
    matches case-insensitively or the SSOT source_ref matches.
    """
    for existing_id, existing in list(out.items()):
        if _planned_bin_matches(existing_id, existing, bid, item):
            merged = {**item, **existing, "id": existing_id}
            if not merged.get("coverage_domain") and item.get("coverage_domain"):
                merged["coverage_domain"] = item["coverage_domain"]
            out[existing_id] = merged
            return
    out[bid] = {**item, "id": bid}


def _goal_section_bins(section: Any, domain: str) -> list[dict[str, Any]]:
    """Return SSOT-declared bins from coverage_goals.function/cycle sections."""
    if not isinstance(section, dict):
        return []
    raw = (
        section.get("bins")
        or section.get("planned_bins")
        or section.get("coverage_bins")
        or section.get("points")
        or []
    )
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(_as_list(raw)):
        if isinstance(item, dict):
            bid = _bin_id(item, idx, f"{domain}_bin")
            if not bid:
                continue
            out.append(
                {
                    **item,
                    "id": bid,
                    "coverage_domain": item.get("coverage_domain") or item.get("domain") or domain,
                    "source": item.get("source")
                    or item.get("source_ref")
                    or f"test_requirements.coverage_goals.{domain}.bins[{idx}]",
                }
            )
        else:
            bid = _bin_id(item, idx, f"{domain}_bin")
            if bid:
                out.append(
                    {
                        "id": bid,
                        "coverage_domain": domain,
                        "description": str(item),
                        "source": f"test_requirements.coverage_goals.{domain}.bins[{idx}]",
                    }
                )
    return out


def planned_bin_entries(fcov_plan: dict[str, Any], goals: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    bins = fcov_plan.get("bins") if isinstance(fcov_plan.get("bins"), list) else []
    for idx, item in enumerate(bins):
        if not isinstance(item, dict):
            continue
        bid = _bin_id(item, idx)
        if bid:
            _add_planned_bin(out, bid, {**item, "id": bid})
    flat = goals.get("planned_bins") if isinstance(goals.get("planned_bins"), list) else []
    for idx, item in enumerate(flat):
        if not isinstance(item, dict):
            continue
        bid = _bin_id(item, idx)
        if bid:
            _add_planned_bin(
                out,
                bid,
                {**item, "id": bid, "source": f"test_requirements.coverage_goals.planned_bins[{idx}]"},
            )
    for key, domain in (
        ("function", "function"),
        ("function_coverage", "function"),
        ("functional_model", "function"),
        ("cycle", "cycle"),
        ("cycle_coverage", "cycle"),
        ("cycle_model", "cycle"),
    ):
        for item in _goal_section_bins(goals.get(key), domain):
            bid = str(item["id"])
            _add_planned_bin(out, bid, item)
    return out


def canonical_bin_id(
    bid: str,
    *,
    planned_meta: dict[str, dict[str, Any]],
    raw_bins: dict[str, Any],
    rtl_bins: dict[str, Any],
    existing_ids: list[str],
) -> str:
    """Resolve case/punctuation variants to the first known coverage-bin ID."""
    norm = _norm_bin_key(bid)
    for source in (existing_ids, list(planned_meta), list(raw_bins), list(rtl_bins)):
        for candidate in source:
            if norm and norm == _norm_bin_key(candidate):
                return str(candidate)
    return bid


def _is_non_signoff_route_status(value: Any) -> bool:
    text = _norm_bin_key(value)
    return text in {
        "non_signoff",
        "non_signoff_blocker",
        "owner_routed_non_signoff",
        "non_signoff_owner_routed",
    } or ("non" in text and "signoff" in text)


def _coverage_owner_routes(cov_dir: Path, missing_bins: list[str]) -> dict[str, Any]:
    path = cov_dir / "coverage_owner_routes.json"
    if not path.is_file():
        return {
            "status": "absent" if missing_bins else "not_needed",
            "source": "",
            "routes_by_bin": {},
            "routed_missing_bins": [],
            "unrouted_missing_bins": missing_bins,
            "invalid_routes": [],
        }
    try:
        doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        return {
            "status": "invalid",
            "source": str(path),
            "routes_by_bin": {},
            "routed_missing_bins": [],
            "unrouted_missing_bins": missing_bins,
            "invalid_routes": [{"row": 0, "reason": f"invalid JSON: {exc}"}],
        }
    if not isinstance(doc, dict):
        return {
            "status": "invalid",
            "source": str(path),
            "routes_by_bin": {},
            "routed_missing_bins": [],
            "unrouted_missing_bins": missing_bins,
            "invalid_routes": [{"row": 0, "reason": "root must be a JSON object"}],
        }

    raw_routes = doc.get("routes")
    routes = raw_routes if isinstance(raw_routes, list) else []
    by_norm: dict[str, dict[str, Any]] = {}
    invalid: list[dict[str, Any]] = []
    for idx, item in enumerate(routes, 1):
        if not isinstance(item, dict):
            invalid.append({"row": idx, "reason": "route must be an object"})
            continue
        bid = str(item.get("bin_id") or item.get("id") or item.get("name") or "").strip()
        owner = str(item.get("owner") or "").strip()
        status = str(item.get("status") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if not bid:
            invalid.append({"row": idx, "reason": "missing bin_id"})
            continue
        if not owner:
            invalid.append({"row": idx, "bin_id": bid, "reason": "missing owner"})
            continue
        if not _is_non_signoff_route_status(status):
            invalid.append({"row": idx, "bin_id": bid, "reason": "status must be explicit non-signoff"})
            continue
        if not reason:
            invalid.append({"row": idx, "bin_id": bid, "reason": "missing reason"})
            continue
        by_norm[_norm_bin_key(bid)] = {
            "bin_id": bid,
            "owner": owner,
            "status": status,
            "reason": reason,
        }

    routes_by_bin: dict[str, dict[str, Any]] = {}
    unrouted: list[str] = []
    for bid in missing_bins:
        route = by_norm.get(_norm_bin_key(bid))
        if route is None:
            unrouted.append(bid)
        else:
            routes_by_bin[bid] = route

    if invalid:
        status = "invalid"
    elif unrouted:
        status = "incomplete"
    else:
        status = "complete"
    return {
        "status": status,
        "source": str(path),
        "routes_by_bin": routes_by_bin,
        "routed_missing_bins": sorted(routes_by_bin),
        "unrouted_missing_bins": unrouted,
        "invalid_routes": invalid,
    }


def planned_bin_ids(fcov_plan: dict[str, Any], goals: dict[str, Any] | None = None) -> list[str]:
    entries = planned_bin_entries(fcov_plan, goals or {})
    return list(entries)


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


def _coverage_alias_refs(row: dict[str, Any]) -> list[str]:
    """Add SSOT coverage-goal aliases proven by one passing scoreboard row.

    Some SSOTs declare high-level bins such as ``FCOV_TX_LOAD_STORE`` or
    ``CCOV_PIPELINE_ORDER`` while the generated equivalence goals reference the
    lower-level planned bin that actually drove stimulus. Count the high-level
    alias only from a passing row with concrete RTL observations.
    """
    aliases: list[str] = []
    fl_expected = row.get("fl_expected") if isinstance(row.get("fl_expected"), dict) else {}
    model_result = fl_expected.get("model_result") if isinstance(fl_expected.get("model_result"), dict) else {}
    txn = fl_expected.get("transaction") if isinstance(fl_expected.get("transaction"), dict) else {}
    text = " ".join(
        str(item or "")
        for item in (
            row.get("goal_id"),
            row.get("scenario_id"),
            " ".join(str(ref) for ref in (row.get("coverage_refs") or [])),
            fl_expected.get("goal_id"),
            fl_expected.get("title"),
            fl_expected.get("goal_kind"),
            txn.get("kind"),
            txn.get("scenario_id"),
            model_result.get("transaction_id"),
            model_result.get("transaction_name"),
            " ".join(str(ref) for ref in (fl_expected.get("ssot_refs") or [])),
            " ".join(str(ref) for ref in (fl_expected.get("observables") or [])),
            " ".join(str(ref) for ref in (fl_expected.get("pass_criteria") or [])),
        )
    ).lower()
    norm = re.sub(r"[^a-z0-9]+", "_", text).strip("_")

    tx_id = str(model_result.get("transaction_id") or txn.get("kind") or "").strip()
    if tx_id:
        tx_key = _norm_bin_key(tx_id)
        alias = f"fcov_{tx_key}"
        if alias and alias not in aliases:
            aliases.append(alias)
        if tx_key.startswith("fm_"):
            ssot_key = tx_key.removeprefix("fm_")
            ssot_alias = f"fcov_{ssot_key}"
            if ssot_alias and ssot_alias not in aliases:
                aliases.append(ssot_alias)
            if ssot_key.endswith("_drop"):
                plural_alias = f"fcov_{ssot_key}s"
                if plural_alias not in aliases:
                    aliases.append(plural_alias)

    if "if_stall" in norm or "instruction_fetch_backpressure" in norm:
        aliases.append("ccov_if_stall")
    if (
        "cycle_axi_write_channels" in norm
        or "cycle_axi_read_channels" in norm
        or "axi_write_channels" in norm
        or "axi_read_channels" in norm
    ):
        aliases.append("ccov_axi_handshakes")
    if "sram_arbiter" in norm or "cycle_model_arbitration" in norm:
        aliases.append("ccov_sram_arbitration")
    if "backpressure" in norm:
        aliases.append("ccov_backpressure")
    if "fsm_context_fsm" in norm or "context_fsm" in norm:
        aliases.append("ccov_context_fsm")
    if "max_tu_4096" in norm or "max_tlp_beats" in norm:
        aliases.append("ccov_max_tlp_beats")
    if (
        "mem_stall" in norm
        or "stall_mem" in norm
        or "load_store_handshake" in norm
        or "d_hready" in norm
        or "data_transfer_wait" in norm
    ):
        aliases.append("ccov_mem_stall")
    if "pipeline_order" in norm or "ordering" in norm or "transaction_order" in norm or "in_order" in norm:
        aliases.append("ccov_pipeline_order")

    out: list[str] = []
    for alias in aliases:
        if alias and alias not in out:
            out.append(alias)
    return out


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
        if row.get("passed") is not True:
            continue
        observed = row.get("rtl_observed")
        if not isinstance(observed, dict) or not observed:
            invalid_rows.append({"row": idx, "goal_id": row.get("goal_id"), "reason": "missing rtl_observed"})
            continue
        if _looks_like_fl_copy(observed, row):
            invalid_rows.append({"row": idx, "goal_id": row.get("goal_id"), "reason": "rtl_observed copies FL/model_result"})
            continue
        refs.extend(_coverage_alias_refs(row))
        if not refs:
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
        "function": ("function coverage", "function_model", "function model", "transaction coverage"),
        "cycle": ("cycle coverage", "cycle_model", "cycle model", "handshake coverage", "latency coverage"),
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


def _norm_domain(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if text in {"function", "functional", "function_model", "functional_model", "fl", "transaction"}:
        return "function"
    if text in {"cycle", "cycle_model", "cl", "protocol", "timing", "latency", "handshake", "fsm", "performance", "throughput", "frequency", "pipeline", "depth", "outstanding"}:
        return "cycle"
    return ""


def infer_coverage_domain(bid: str, value: Any, meta: dict[str, Any] | None = None) -> str:
    parts: list[str] = [bid]
    for obj in (meta or {}, value if isinstance(value, dict) else {}):
        for key in ("coverage_domain", "domain", "model", "coverage_type", "class", "kind", "source", "source_ref", "ssot_ref"):
            domain = _norm_domain(obj.get(key))
            if domain:
                return domain
            raw = obj.get(key)
            if raw:
                parts.append(str(raw))
        refs = obj.get("refs") or obj.get("coverage_refs") or obj.get("source_refs")
        if isinstance(refs, list):
            parts.extend(str(ref) for ref in refs)
    text = " ".join(parts).lower()
    if "cycle_model" in text or re.search(r"\b(cycle|handshake|latency|backpressure|protocol|fsm|state_transition|pipeline|pipelining|performance|throughput|frequency|freq|depth|outstanding)\b", text):
        return "cycle"
    if "function_model" in text or re.search(r"\b(function|functional|transaction|scenario|datapath|error)\b", text):
        return "function"
    return "function"


def domain_coverage(functional_bins: dict[str, Any], domain: str, target: float | None) -> dict[str, Any]:
    selected = {
        bid: value
        for bid, value in functional_bins.items()
        if isinstance(value, dict) and value.get("coverage_domain") == domain
    }
    hit = sum(1 for value in selected.values() if bin_hit(value))
    total = len(selected)
    measured = {"hit": hit, "total": total, "pct": pct(hit, total)}
    return {
        **measured,
        "target_pct": target,
        "meets_target": target is None or (measured["pct"] is not None and measured["pct"] >= target),
        "bins": selected,
    }


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
    planned_meta = planned_bin_entries(fcov_plan, goals)
    planned_bins = list(planned_meta)
    raw_bins = raw_functional["functional_bins"]
    rtl_bins = rtl_cov["bins"] if isinstance(rtl_cov.get("bins"), dict) else {}
    all_bin_ids: list[str] = []
    for source in (planned_bins, list(raw_bins), list(rtl_bins), rtl_cov.get("goal_refs") or []):
        for bid in source:
            text = canonical_bin_id(
                str(bid),
                planned_meta=planned_meta,
                raw_bins=raw_bins,
                rtl_bins=rtl_bins,
                existing_ids=all_bin_ids,
            )
            if text and text not in all_bin_ids:
                all_bin_ids.append(text)

    functional_bins: dict[str, Any] = {}
    for bid in all_bin_ids:
        meta = planned_meta.get(bid, {})
        rtl_key = canonical_bin_id(
            bid,
            planned_meta={},
            raw_bins={},
            rtl_bins=rtl_bins,
            existing_ids=list(rtl_bins),
        )
        raw_key = canonical_bin_id(
            bid,
            planned_meta={},
            raw_bins=raw_bins,
            rtl_bins={},
            existing_ids=list(raw_bins),
        )
        if rtl_key in rtl_bins:
            item = dict(rtl_bins[rtl_key])
            item["raw_hit"] = bin_hit(raw_bins.get(raw_key)) if raw_key in raw_bins else None
            if meta:
                item.setdefault("plan", meta)
                for key in ("class", "coverage_domain", "domain", "description", "source", "source_ref"):
                    if key in meta and key not in item:
                        item[key] = meta[key]
            item["coverage_domain"] = infer_coverage_domain(bid, item, meta)
            functional_bins[bid] = item
            continue
        raw_value = raw_bins.get(raw_key, {"hit": False, "source": "fcov_plan"})
        item = {
            "hit": False,
            "raw_hit": bin_hit(raw_value),
            "source": "missing_rtl_observed_scoreboard_evidence",
            "raw": raw_value,
        }
        if meta:
            item["plan"] = meta
            for key in ("class", "coverage_domain", "domain", "description", "source_ref"):
                if key in meta:
                    item[key] = meta[key]
        item["coverage_domain"] = infer_coverage_domain(bid, raw_value, meta)
        functional_bins[bid] = item

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
    function_goal = metric_goal(goals, ("function", "functional", "scenario", "transaction"))
    cycle_goal = metric_goal(goals, ("cycle", "protocol", "handshake", "latency", "fsm", "transition"))
    line_target = threshold_for_metric(line_goal, ("line", "code"))
    branch_target = threshold_for_metric(branch_goal, ("branch",))
    fsm_target = threshold_for_metric(fsm_goal, ("fsm",))
    functional_target = threshold_for_metric(functional_goal, ("functional", "scenario", "transition"))
    function_target = threshold_for_metric(function_goal, ("function", "transaction"))
    cycle_target = threshold_for_metric(cycle_goal, ("cycle", "protocol", "handshake", "latency"))
    if functional_target is None and all_bin_ids:
        functional_target = 100.0

    fsm_bins = bin_coverage(functional["functional_bins"], ("fsm",))
    if fsm_goal is not None and fsm_target is None and fsm_bins["total"]:
        fsm_target = 100.0
    function_coverage = domain_coverage(functional["functional_bins"], "function", function_target)
    cycle_coverage = domain_coverage(functional["functional_bins"], "cycle", cycle_target)
    if function_goal is not None and function_coverage["target_pct"] is None and function_coverage["total"]:
        function_coverage["target_pct"] = 100.0
        function_coverage["meets_target"] = function_coverage["pct"] is not None and function_coverage["pct"] >= 100.0
    if cycle_goal is not None and cycle_coverage["target_pct"] is None and cycle_coverage["total"]:
        cycle_coverage["target_pct"] = 100.0
        cycle_coverage["meets_target"] = cycle_coverage["pct"] is not None and cycle_coverage["pct"] >= 100.0

    limitations: dict[str, Any] = {}
    waived_limitations: dict[str, Any] = {}
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
    owner_routes = _coverage_owner_routes(cov_dir, missing_rtl_bins)
    owner_routed_coverage = (
        bool(missing_rtl_bins)
        and owner_routes.get("status") == "complete"
        and not invalid_rows
    )
    owner_routed_limitations: dict[str, Any] = {}
    limitations_for_status = dict(limitations)
    if owner_routed_coverage:
        for key in ("rtl_observed_coverage", "raw_functional_only_bins"):
            if key in limitations_for_status:
                owner_routed_limitations[key] = limitations_for_status.pop(key)
    line_uninstrumented = line_goal is not None and lcov["lines"]["total"] == 0
    branch_uninstrumented = branch_goal is not None and lcov["branches"]["total"] == 0
    if line_uninstrumented:
        waived_limitations["line"] = (
            "SSOT requests line/code coverage, but this simulator run did not produce LCOV DA records; "
            "functional/cycle closure is judged from RTL-observed scoreboard coverage."
        )
    if branch_uninstrumented:
        waived_limitations["branch"] = (
            "SSOT requests branch coverage, but this simulator run did not produce LCOV BRDA/BRF records; "
            "functional/cycle closure is judged from RTL-observed scoreboard coverage."
        )
    if fsm_goal is not None and fsm_bins["total"] == 0:
        limitations["fsm_state"] = (
            "SSOT requests FSM coverage, but no SSOT-derived functional FSM bins or instrumented FSM metric was present."
        )
    for key, value in functional.get("legacy_limitations", {}).items():
        limitations.setdefault(key, value)

    line_ok = (
        line_target is None
        or line_uninstrumented
        or (lcov["lines"]["pct"] is not None and lcov["lines"]["pct"] >= line_target)
    )
    branch_ok = (
        branch_target is None
        or branch_uninstrumented
        or (lcov["branches"]["pct"] is not None and lcov["branches"]["pct"] >= branch_target)
    )
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
    function_ok = function_coverage["meets_target"]
    cycle_ok = cycle_coverage["meets_target"]
    local_metric_ok = line_ok and branch_ok and fsm_ok and checks_ok and not limitations_for_status
    if local_metric_ok and functional_ok and function_ok and cycle_ok:
        status = "pass"
    elif local_metric_ok and owner_routed_coverage:
        status = "owner_routed"
    else:
        status = "blocked"
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
        "function_coverage": function_coverage,
        "cycle_coverage": cycle_coverage,
        "coverage_model": {
            "function": {
                "source": "function_model",
                "target_pct": function_coverage["target_pct"],
                "hit": function_coverage["hit"],
                "total": function_coverage["total"],
                "pct": function_coverage["pct"],
                "meets_target": function_coverage["meets_target"],
            },
            "cycle": {
                "source": "cycle_model",
                "target_pct": cycle_coverage["target_pct"],
                "hit": cycle_coverage["hit"],
                "total": cycle_coverage["total"],
                "pct": cycle_coverage["pct"],
                "meets_target": cycle_coverage["meets_target"],
            },
        },
        "planned_bins": planned_bins,
        "functional_bins": functional["functional_bins"],
        "raw_functional": raw_functional["functional"],
        "raw_functional_bins": raw_bins,
        "rtl_observed": {
            "status": (
                "pass"
                if all_bin_ids and not missing_rtl_bins and not invalid_rows
                else "owner_routed"
                if owner_routed_coverage
                else "blocked"
            ),
            "scoreboard_events": rtl_cov.get("scoreboard_events", 0),
            "scoreboard_passed_events_with_refs": rtl_cov.get("scoreboard_passed_events_with_refs", 0),
            "goal_refs": rtl_cov.get("goal_refs", []),
            "missing_bins": missing_rtl_bins,
            "invalid_rows": invalid_rows,
        },
        "owner_routes": owner_routes,
        "lines": {
            **lcov["lines"],
            "target_pct": line_target,
            "meets_target": line_ok,
            "measured": not line_uninstrumented,
            "status": "not_instrumented" if line_uninstrumented else ("pass" if line_ok else "blocked"),
        },
        "branches": {
            **lcov["branches"],
            "target_pct": branch_target,
            "meets_target": branch_ok,
            "measured": not branch_uninstrumented,
            "status": "not_instrumented" if branch_uninstrumented else ("pass" if branch_ok else "blocked"),
        },
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
        "owner_routed_limitations": owner_routed_limitations,
        "waived_limitations": waived_limitations,
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
        f"Function coverage: {function_coverage['hit']}/{function_coverage['total']} ({function_coverage['pct']}%) target={function_coverage['target_pct']}",
        f"Cycle coverage: {cycle_coverage['hit']}/{cycle_coverage['total']} ({cycle_coverage['pct']}%) target={cycle_coverage['target_pct']}",
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
    if owner_routed_limitations:
        report.extend(["", "## Owner-routed non-signoff coverage gaps"])
        report.extend(f"- {key}: {value}" for key, value in owner_routed_limitations.items())
    if waived_limitations:
        report.extend(["", "## Waived tool metrics"])
        report.extend(f"- {key}: {value}" for key, value in waived_limitations.items())
    (sim_dir / "coverage_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(f"SSOT coverage summary: {cov_dir / 'coverage.json'}")
    print(f"SSOT coverage report : {sim_dir / 'coverage_report.md'}")
    print(f"Status               : {status}")
    return 0 if status in {"pass", "owner_routed"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
