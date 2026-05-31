#!/usr/bin/env python3
"""Deterministic RTL mutation guard for FL-vs-RTL harness depth.

The guard never edits the source IP in place.  It copies the IP directory to a
temporary workspace, rewrites the copied TB manifest to point at copied RTL, and
then runs the existing cocotb runner against one deterministic mutant at a time.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("eq_to_ne", re.compile(r"=="), "!="),
    ("ne_to_eq", re.compile(r"!="), "=="),
    ("xor_to_and", re.compile(r"\^"), "&"),
    ("add_to_sub", re.compile(r"\+"), "-"),
    ("sub_to_add", re.compile(r"-"), "+"),
    ("one_to_zero", re.compile(r"1'b1"), "1'b0"),
    ("zero_to_one", re.compile(r"1'b0"), "1'b1"),
)

COMPILE_FAILURE_MARKERS = (
    "syntax error",
    "unable to compile",
    "compile error",
    "compilation failed",
    "malformed statement",
    "unknown module type",
)

DECLARATION_PREFIXES = (
    "input ",
    "output ",
    "inout ",
    "parameter ",
    "localparam ",
    "logic ",
    "wire ",
    "reg ",
)

CATEGORY_PRIORITY = (
    "operator_flip",
    "constant_flip",
    "comparator_flip",
    "handshake_hold_drop",
    "state_update_drop",
    "bit_order_flip",
    "serial_clock_edge_flip",
    "chip_select_polarity_flip",
    "uart_start_stop_polarity_flip",
    "serial_timing_flip",
)

SUPPORTED_MUTATION_CATEGORIES = set(CATEGORY_PRIORITY)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@dataclass(frozen=True)
class MutationCandidate:
    id: str
    relpath: str
    line: int
    column: int
    category: str
    rule: str
    before: str
    after: str
    preview: str


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _contract_mutation_obligations(ip_dir: Path) -> dict[str, Any]:
    required = _contract_required_mutations(ip_dir)
    unsupported = sorted(set(required) - SUPPORTED_MUTATION_CATEGORIES)
    return {
        "contract": "verify/ip_contract.json" if (ip_dir / "verify" / "ip_contract.json").is_file() else "",
        "required": sorted(set(required)),
        "supported_by_current_guard": sorted(set(required) & SUPPORTED_MUTATION_CATEGORIES),
        "unsupported_by_current_guard": unsupported,
        "note": "Unsupported categories are advisory follow-up obligations; supported contract-specific and generic mutants run deterministically.",
    }


def _contract_required_mutations(ip_dir: Path) -> list[str]:
    contract = _read_json(ip_dir / "verify" / "ip_contract.json")
    raw = contract.get("required_mutations") if isinstance(contract.get("required_mutations"), list) else []
    return [
        str(item.get("id") or "")
        for item in raw
        if isinstance(item, dict) and item.get("required") is not False and str(item.get("id") or "")
    ]


def _rtl_source_rels(ip_dir: Path) -> list[Path]:
    manifest = _read_json(ip_dir / "tb" / "cocotb" / "tb_manifest.json")
    rels: list[Path] = []
    seen: set[Path] = set()

    for raw in manifest.get("rtl_sources") if isinstance(manifest.get("rtl_sources"), list) else []:
        src = Path(str(raw))
        if not src.is_absolute():
            src = ip_dir / src
        try:
            rel = src.resolve().relative_to(ip_dir.resolve())
        except ValueError:
            continue
        if rel.suffix == ".sv" and rel not in seen and (ip_dir / rel).is_file():
            seen.add(rel)
            rels.append(rel)

    if rels:
        return rels

    for path in sorted((ip_dir / "rtl").glob("*.sv")):
        rel = path.relative_to(ip_dir)
        if rel not in seen:
            seen.add(rel)
            rels.append(rel)
    return rels


def _mutation_candidates(ip_dir: Path, *, max_mutants: int) -> list[MutationCandidate]:
    candidates: list[MutationCandidate] = []
    seen: set[tuple[str, int, int, str, str, str]] = set()
    required = set(_contract_required_mutations(ip_dir))
    rtl_lines = _iter_rtl_lines(ip_dir)

    for rel, line_no, line in rtl_lines:
        for category, rule, match in _contract_specific_matches(line, required):
            if _skip_structural_mutation(line, match["column"]):
                continue
            _append_candidate(
                candidates,
                seen,
                rel=rel,
                line_no=line_no,
                line=line,
                category=category,
                rule=rule,
                column=match["column"],
                before=match["before"],
                after=match["after"],
            )

    for rel, line_no, line in rtl_lines:
        for rule, pattern, replacement in RULES:
            match = pattern.search(line)
            if not match:
                continue
            if _skip_structural_mutation(line, match.start()):
                continue
            before = match.group(0)
            after = replacement
            if before == after:
                continue
            category = _generic_category(rule)
            _append_candidate(
                candidates,
                seen,
                rel=rel,
                line_no=line_no,
                line=line,
                category=category,
                rule=rule,
                column=match.start(),
                before=before,
                after=after,
            )
    return _select_candidates(candidates, max_mutants=max_mutants, required=required)


def _select_candidates(
    candidates: list[MutationCandidate],
    *,
    max_mutants: int,
    required: set[str],
) -> list[MutationCandidate]:
    if max_mutants <= 0:
        return []

    eligible = [
        candidate
        for candidate in candidates
        if not required or candidate.category in required
    ]
    if not eligible:
        eligible = candidates

    categories: list[str] = []
    for category in [item for item in CATEGORY_PRIORITY if item in required] + [candidate.category for candidate in eligible]:
        if category and category not in categories:
            categories.append(category)

    grouped: dict[str, list[MutationCandidate]] = {category: [] for category in categories}
    for candidate in eligible:
        grouped.setdefault(candidate.category, []).append(candidate)
    for bucket in grouped.values():
        bucket.sort(key=_candidate_priority_key)

    selected: list[MutationCandidate] = []
    while len(selected) < max_mutants:
        progressed = False
        for category in categories:
            bucket = grouped.get(category) or []
            if not bucket:
                continue
            selected.append(bucket.pop(0))
            progressed = True
            if len(selected) >= max_mutants:
                break
        if not progressed:
            break
    return selected


def _candidate_priority_key(candidate: MutationCandidate) -> tuple[int, int, int]:
    if candidate.category == "state_update_drop" and _looks_like_literal(candidate.before):
        return (1, candidate.line, candidate.column)
    return (0, candidate.line, candidate.column)


def _looks_like_literal(value: str) -> bool:
    text = value.strip().replace("_", "")
    return bool(
        re.fullmatch(r"\d+'[sS]?[dDhHbBoO][0-9a-fA-FxXzZ]+", text)
        or re.fullmatch(r"\d+", text)
        or re.fullmatch(r"[01]'b[01xXzZ]", text)
    )


def _iter_rtl_lines(ip_dir: Path) -> list[tuple[Path, int, str]]:
    rows: list[tuple[Path, int, str]] = []
    for rel in _rtl_source_rels(ip_dir):
        path = ip_dir / rel
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("`"):
                continue
            rows.append((rel, line_no, line))
    return rows


def _generic_category(rule: str) -> str:
    if "eq" in rule:
        return "comparator_flip"
    if "zero" in rule:
        return "constant_flip"
    return "operator_flip"


def _append_candidate(
    candidates: list[MutationCandidate],
    seen: set[tuple[str, int, int, str, str, str]],
    *,
    rel: Path,
    line_no: int,
    line: str,
    category: str,
    rule: str,
    column: int,
    before: str,
    after: str,
) -> None:
    key = (rel.as_posix(), line_no, column, before, after, category)
    if key in seen or before == after:
        return
    seen.add(key)
    mutation_id = f"MUT_{len(candidates) + 1:04d}_{rule}_{rel.stem}_{line_no}"
    candidates.append(
        MutationCandidate(
            id=mutation_id,
            relpath=rel.as_posix(),
            line=line_no,
            column=column,
            category=category,
            rule=rule,
            before=before,
            after=after,
            preview=line.strip(),
        )
    )


def _contract_specific_matches(line: str, required: set[str]) -> list[tuple[str, str, dict[str, Any]]]:
    matches: list[tuple[str, str, dict[str, Any]]] = []
    lowered = line.lower()

    if "handshake_hold_drop" in required and any(token in lowered for token in ("valid", "ready", "push", "pop", "full")):
        matches.extend(("handshake_hold_drop", "source_ready_gate_drop", item) for item in _literal_matches(line, " & m_ready_i", ""))
        matches.extend(("handshake_hold_drop", "sink_valid_gate_drop", item) for item in _literal_matches(line, "s_valid_i & ", ""))
        matches.extend(("handshake_hold_drop", "full_pop_ready_drop", item) for item in _literal_matches(line, "~full | pop", "~full"))
        matches.extend(("handshake_hold_drop", "full_pop_ready_drop", item) for item in _full_pop_matches(line))
        if "s_ready" in lowered:
            matches.extend(("handshake_hold_drop", "ready_full_pop_drop", item) for item in _literal_matches(line, "push_allowed", "~full"))

    if "state_update_drop" in required:
        matches.extend(("state_update_drop", "state_update_to_self_hold", item) for item in _state_update_matches(line))

    if "bit_order_flip" in required:
        if any(token in lowered for token in ("bit_index", "mosi", "miso", "tx", "shift", "data")):
            matches.extend(("bit_order_flip", "bit_index_decrement_to_increment", item) for item in _literal_matches(line, " - 3'd1", " + 3'd1"))
            matches.extend(("bit_order_flip", "bit_index_increment_to_decrement", item) for item in _literal_matches(line, " + 3'd1", " - 3'd1"))
            matches.extend(("bit_order_flip", "msb_index_to_lsb_index", item) for item in _literal_matches(line, "[7]", "[0]"))
            matches.extend(("bit_order_flip", "lsb_index_to_msb_index", item) for item in _literal_matches(line, "[0]", "[7]"))
            matches.extend(("bit_order_flip", "param_msb_index_to_lsb_index", item) for item in _literal_matches(line, "[DATA_WIDTH-1]", "[0]"))

    if "serial_clock_edge_flip" in required and any(token in lowered for token in ("sclk", "sck", "spi_clk", "serial_clk")):
        matches.extend(("serial_clock_edge_flip", "serial_eq_to_ne", item) for item in _literal_matches(line, "==", "!="))
        matches.extend(("serial_clock_edge_flip", "serial_ne_to_eq", item) for item in _literal_matches(line, "!=", "=="))

    if "serial_timing_flip" in required and any(token in lowered for token in ("baud", "div", "period", "bit_timer", "bit_cnt")):
        matches.extend(("serial_timing_flip", "serial_timing_eq_to_ne", item) for item in _literal_matches(line, "==", "!="))
        matches.extend(("serial_timing_flip", "serial_timing_add_to_sub", item) for item in _literal_matches(line, " + ", " - "))
        matches.extend(("serial_timing_flip", "serial_timing_sub_to_add", item) for item in _literal_matches(line, " - ", " + "))

    if "chip_select_polarity_flip" in required and any(token in lowered for token in ("cs", "ss_n", "chip_select")):
        matches.extend(("chip_select_polarity_flip", "chip_select_zero_to_one", item) for item in _literal_matches(line, "1'b0", "1'b1"))
        matches.extend(("chip_select_polarity_flip", "chip_select_one_to_zero", item) for item in _literal_matches(line, "1'b1", "1'b0"))

    if "uart_start_stop_polarity_flip" in required and any(token in lowered for token in ("tx", "uart_tx")):
        matches.extend(("uart_start_stop_polarity_flip", "uart_tx_zero_to_one", item) for item in _literal_matches(line, "1'b0", "1'b1"))
        matches.extend(("uart_start_stop_polarity_flip", "uart_tx_one_to_zero", item) for item in _literal_matches(line, "1'b1", "1'b0"))

    return matches


def _state_update_matches(line: str) -> list[dict[str, Any]]:
    code = line.split("//", 1)[0]
    match = re.match(
        r"^(?P<prefix>\s*)(?P<lhs>[A-Za-z_][A-Za-z0-9_$]*(?:\[[^\]]+\])?)\s*<=\s*(?P<rhs>[^;]+);",
        code,
    )
    if not match:
        return []
    lhs = match.group("lhs")
    rhs = match.group("rhs").strip()
    base_lhs = lhs.split("[", 1)[0]
    lowered_lhs = base_lhs.lower()
    if not (lowered_lhs.endswith("_q") or "state" in lowered_lhs or "level" in lowered_lhs):
        return []
    if rhs == base_lhs or rhs == lhs:
        return []
    column = line.find(rhs, match.start("rhs"))
    if column < 0:
        return []
    return [{"column": column, "before": rhs, "after": base_lhs}]


def _literal_matches(line: str, before: str, after: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    start = 0
    while True:
        column = line.find(before, start)
        if column < 0:
            break
        out.append({"column": column, "before": before, "after": after})
        start = column + max(len(before), 1)
    return out


def _full_pop_matches(line: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pattern = re.compile(r"~(?P<full>[A-Za-z_][A-Za-z0-9_$]*)\s*\|\s*(?P<pop>[A-Za-z_][A-Za-z0-9_$]*)")
    for match in pattern.finditer(line):
        before = match.group(0)
        out.append({"column": match.start(), "before": before, "after": f"~{match.group('full')}"})
    return out


def _inside_square_brackets(line: str, index: int) -> bool:
    depth = 0
    for char in line[:index]:
        if char == "[":
            depth += 1
        elif char == "]" and depth:
            depth -= 1
    return depth > 0


def _skip_structural_mutation(line: str, index: int) -> bool:
    if _inside_square_brackets(line, index):
        return True
    stripped = line.lstrip()
    if not stripped.startswith(DECLARATION_PREFIXES):
        return False
    assign_index = line.find("=")
    return assign_index < 0 or index < assign_index


def _apply_candidate(copy_ip: Path, candidate: MutationCandidate) -> None:
    path = copy_ip / candidate.relpath
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    idx = candidate.line - 1
    line = lines[idx]
    start = candidate.column
    end = start + len(candidate.before)
    if line[start:end] != candidate.before:
        raise RuntimeError(f"{candidate.id}: source text drifted at {candidate.relpath}:{candidate.line}")
    lines[idx] = line[:start] + candidate.after + line[end:]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _rewrite_manifest(copy_ip: Path, source_rels: list[Path]) -> None:
    manifest_path = copy_ip / "tb" / "cocotb" / "tb_manifest.json"
    if not manifest_path.is_file():
        return
    manifest = _read_json(manifest_path)
    manifest["rtl_sources"] = [str((copy_ip / rel).resolve()) for rel in source_rels]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _failed_scoreboard_rows(copy_ip: Path) -> int:
    path = copy_ip / "sim" / "scoreboard_events.jsonl"
    if not path.is_file():
        return 0
    failed = 0
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except Exception:
            continue
        if isinstance(row, dict) and row.get("passed") is False:
            failed += 1
    return failed


def _classify_result(returncode: int, output: str, failed_rows: int) -> tuple[str, str]:
    lowered = output.lower()
    if failed_rows > 0:
        return "killed", f"scoreboard failed rows={failed_rows}"
    if returncode == 0:
        return "survived", "test runner returned 0"
    if any(marker in lowered for marker in COMPILE_FAILURE_MARKERS):
        return "invalid", "mutant did not compile/elaborate"
    return "killed", f"test runner returned {returncode}"


def _category_summary(
    results: list[dict[str, Any]],
    candidates: list[MutationCandidate] | None = None,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, int]] = {}
    for result in results:
        category = str(result.get("category") or "unknown")
        row = grouped.setdefault(category, {"executed": 0, "killed": 0, "survived": 0, "invalid": 0})
        row["executed"] += 1
        status = str(result.get("status") or "")
        if status in {"killed", "survived", "invalid"}:
            row[status] += 1
    if not results and candidates:
        for candidate in candidates:
            row = grouped.setdefault(
                candidate.category,
                {"candidates": 0, "executed": 0, "killed": 0, "survived": 0, "invalid": 0},
            )
            row["candidates"] += 1

    out: list[dict[str, Any]] = []
    for category in sorted(grouped):
        row = grouped[category]
        denominator = max(row["executed"] - row["invalid"], 0)
        kill_rate = None if denominator == 0 else round(row["killed"] / denominator, 4)
        out.append(
            {
                "category": category,
                **row,
                "kill_rate": kill_rate,
            }
        )
    return out


def _baseline_blocker(ip_dir: Path) -> dict[str, Any]:
    compare = _read_json(ip_dir / "sim" / "fl_rtl_compare.json")
    if compare:
        status = str(compare.get("status") or "").lower()
        if status and status != "pass":
            return {
                "status": status,
                "source": "sim/fl_rtl_compare.json",
                "reason": "baseline FL-vs-RTL compare is not green; mutation kill-rate would be meaningless",
                "summary": compare.get("summary") if isinstance(compare.get("summary"), dict) else {},
            }

    score_path = ip_dir / "sim" / "scoreboard_events.jsonl"
    if score_path.is_file():
        failed_rows = _failed_scoreboard_rows(ip_dir)
        if failed_rows:
            return {
                "status": "fail",
                "source": "sim/scoreboard_events.jsonl",
                "reason": "baseline scoreboard already contains failing rows; mutation kill-rate would be meaningless",
                "failed_scoreboard_rows": failed_rows,
            }
    return {"status": "pass", "source": "", "reason": ""}


def _run_candidate(
    original_ip_dir: Path,
    source_rels: list[Path],
    candidate: MutationCandidate,
    *,
    timeout_sec: int,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"mutation_{original_ip_dir.name}_") as tmp:
        tmp_ip = Path(tmp) / original_ip_dir.name
        ignore = shutil.ignore_patterns("sim", "mutation", "__pycache__", ".pytest_cache")
        shutil.copytree(original_ip_dir, tmp_ip, ignore=ignore)
        _rewrite_manifest(tmp_ip, source_rels)
        _apply_candidate(tmp_ip, candidate)

        runner = tmp_ip / "tb" / "cocotb" / "test_runner.py"
        if not runner.is_file():
            return {**asdict(candidate), "status": "invalid", "reason": "missing tb/cocotb/test_runner.py"}

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["COMMON_AI_AGENT_SOURCE_ROOT"] = str(original_ip_dir.parents[1])
        try:
            proc = subprocess.run(
                ["python3", str(runner)],
                cwd=str(original_ip_dir.parents[1]),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout_sec,
            )
            output = proc.stdout or ""
            failed_rows = _failed_scoreboard_rows(tmp_ip)
            status, reason = _classify_result(proc.returncode, output, failed_rows)
            return {
                **asdict(candidate),
                "status": status,
                "reason": reason,
                "returncode": proc.returncode,
                "failed_scoreboard_rows": failed_rows,
                "output_tail": "\n".join(output.splitlines()[-20:]),
            }
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout if isinstance(exc.stdout, str) else ""
            return {
                **asdict(candidate),
                "status": "killed",
                "reason": f"test runner timed out after {timeout_sec}s",
                "returncode": None,
                "failed_scoreboard_rows": 0,
                "output_tail": "\n".join(output.splitlines()[-20:]),
            }


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    summary = report["summary"]
    obligations = report.get("contract_mutation_obligations") if isinstance(report.get("contract_mutation_obligations"), dict) else {}
    unsupported = obligations.get("unsupported_by_current_guard") if isinstance(obligations.get("unsupported_by_current_guard"), list) else []
    baseline = report.get("baseline") if isinstance(report.get("baseline"), dict) else {}
    baseline_reason = str(baseline.get("reason") or "")
    lines = [
        f"# Mutation Guard - {report['ip']}",
        "",
        f"- Status: `{report['status']}`",
        f"- Mode: `{report['mode']}`",
        f"- Candidates: `{summary['candidates']}`",
        f"- Executed: `{summary['executed']}`",
        f"- Killed: `{summary['killed']}`",
        f"- Survived: `{summary['survived']}`",
        f"- Invalid: `{summary['invalid']}`",
        f"- Kill rate: `{summary['kill_rate']}`",
        f"- Contract unsupported mutation categories: `{', '.join(unsupported) if unsupported else 'none'}`",
    ]
    if report.get("status") == "blocked_baseline" and baseline_reason:
        lines.append(f"- Baseline blocker: {baseline_reason}")
        lines.append(f"- Baseline source: `{baseline.get('source') or 'unknown'}`")
    lines.extend(
        [
            "",
            "## Category Kill Rate",
            "",
            "| Category | Executed | Killed | Survived | Invalid | Kill rate |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in report.get("category_summary", []):
        lines.append(
            f"| `{row['category']}` | {row['executed']} | {row['killed']} | {row['survived']} | {row['invalid']} | `{row['kill_rate']}` |"
        )
    lines.extend(
        [
            "",
            "## Mutants",
            "",
            "| Mutant | Status | Location | Rule | Reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for result in report.get("results", []):
        loc = f"{result['relpath']}:{result['line']}"
        lines.append(
            f"| `{result['id']}` | `{result['status']}` | `{loc}` | `{result['rule']}` | {result['reason']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--max-mutants", type=int, default=12)
    parser.add_argument("--timeout-sec", type=int, default=30)
    parser.add_argument("--threshold", type=float, default=0.70)
    parser.add_argument("--enforce-threshold", action="store_true")
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    if not ip_dir.is_dir():
        print(f"[mutation_guard] FAIL: missing IP directory {ip_dir}")
        return 1

    source_rels = _rtl_source_rels(ip_dir)
    contract_obligations = _contract_mutation_obligations(ip_dir)
    candidates = _mutation_candidates(ip_dir, max_mutants=max(args.max_mutants, 0))
    results: list[dict[str, Any]] = []
    baseline = {"status": "not_checked" if args.list_only else "pass", "source": "", "reason": ""}
    if not args.list_only:
        baseline = _baseline_blocker(ip_dir)
    if not args.list_only and baseline.get("status") == "pass":
        for candidate in candidates:
            results.append(_run_candidate(ip_dir, source_rels, candidate, timeout_sec=args.timeout_sec))

    executed = len(results)
    killed = sum(1 for result in results if result.get("status") == "killed")
    survived = sum(1 for result in results if result.get("status") == "survived")
    invalid = sum(1 for result in results if result.get("status") == "invalid")
    denominator = max(executed - invalid, 0)
    kill_rate = None if denominator == 0 else round(killed / denominator, 4)

    if args.list_only:
        status = "listed"
        mode = "list_only"
    elif baseline.get("status") != "pass":
        status = "blocked_baseline"
        mode = "baseline_blocked"
    elif args.enforce_threshold and (kill_rate is None or kill_rate < args.threshold):
        status = "fail"
        mode = "enforced"
    else:
        status = "pass"
        mode = "advisory" if not args.enforce_threshold else "enforced"

    report = {
        "schema_version": 1,
        "type": "mutation_guard",
        "generated_at": _utc(),
        "ip": args.ip,
        "status": status,
        "mode": mode,
        "threshold": args.threshold,
        "baseline": baseline,
        "source_rels": [rel.as_posix() for rel in source_rels],
        "contract_mutation_obligations": contract_obligations,
        "summary": {
            "candidates": len(candidates),
            "executed": executed,
            "killed": killed,
            "survived": survived,
            "invalid": invalid,
            "kill_rate": kill_rate,
        },
        "category_summary": _category_summary(results, candidates),
        "candidates": [asdict(candidate) for candidate in candidates],
        "results": results,
    }

    out_dir = ip_dir / "mutation"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "mutation_report.json"
    md_path = out_dir / "mutation_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(md_path, report)

    print(f"[mutation_guard] status={status} summary={report['summary']}")
    if status == "blocked_baseline":
        print(f"[mutation_guard] baseline_blocker={baseline}")
    print(f"[mutation_guard] wrote {json_path}")
    print(f"[mutation_guard] wrote {md_path}")
    return 0 if status in {"pass", "listed", "blocked_baseline"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
