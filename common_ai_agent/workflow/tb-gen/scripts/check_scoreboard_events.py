#!/usr/bin/env python3
"""Validate the generic FL-vs-RTL scoreboard evidence contract.

This is deliberately IP-agnostic.  The only authority is the generated
equivalence-goals artifact, and each scoreboard event must point back to one
of those goals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"[check_scoreboard_events] FAIL: cannot parse {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise SystemExit(f"[check_scoreboard_events] FAIL: {path} root must be a JSON object")
    return doc


def _goal_ids(goals_path: Path) -> tuple[set[str], set[str]]:
    doc = _load_json(goals_path)
    goals = doc.get("goals")
    if not isinstance(goals, list):
        raise SystemExit(f"[check_scoreboard_events] FAIL: {goals_path} has no goals[] list")
    all_ids: set[str] = set()
    required_ids: set[str] = set()
    for idx, goal in enumerate(goals):
        if not isinstance(goal, dict):
            raise SystemExit(f"[check_scoreboard_events] FAIL: goals[{idx}] is not an object")
        gid = str(goal.get("goal_id") or "").strip()
        if not gid:
            raise SystemExit(f"[check_scoreboard_events] FAIL: goals[{idx}] missing goal_id")
        if gid in all_ids:
            raise SystemExit(f"[check_scoreboard_events] FAIL: duplicate goal_id {gid}")
        all_ids.add(gid)
        if goal.get("blocked") is not True:
            required_ids.add(gid)
    return all_ids, required_ids


def _goal_map(goals_path: Path) -> dict[str, dict[str, Any]]:
    doc = _load_json(goals_path)
    out: dict[str, dict[str, Any]] = {}
    for goal in doc.get("goals") if isinstance(doc.get("goals"), list) else []:
        if not isinstance(goal, dict):
            continue
        gid = str(goal.get("goal_id") or "").strip()
        if gid:
            out[gid] = goal
    return out


def _tb_sources(ip_dir: Path) -> str:
    roots = [ip_dir / "tb" / "cocotb", ip_dir / "tb", ip_dir / "sim"]
    suffixes = {".py", ".sv", ".svh", ".v", ".vh"}
    chunks: list[str] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in suffixes:
                continue
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def _validate_source_contract(ip_dir: Path) -> list[str]:
    text = _tb_sources(ip_dir)
    if not text:
        return ["no TB source files found under tb/ or sim/"]
    uses_runtime_helper = "EquivalenceScoreboard" in text or "equivalence_scoreboard" in text
    if uses_runtime_helper and "EquivalenceScoreboard(" not in text:
        return ["TB imports equivalence_scoreboard but does not instantiate EquivalenceScoreboard"]
    if uses_runtime_helper:
        return []
    checks = {
        "equivalence_goals.json": "TB must load the generated equivalence goals",
        "scoreboard_events.jsonl": "TB must emit structured scoreboard evidence",
        "goal_id": "scoreboard rows must include goal_id",
        "fl_expected": "scoreboard rows must include FL expected values",
        "rtl_observed": "scoreboard rows must include RTL observed values",
        "passed": "scoreboard rows must include pass/fail result",
        "mismatch": "scoreboard rows must include mismatch text",
        "coverage_refs": "scoreboard rows must include linked coverage refs",
    }
    errors = [msg for needle, msg in checks.items() if needle not in text]
    model_markers = ("FunctionalModel", "functional_model", "fl_model", "reference_model", "model_adapter")
    if not any(marker in text for marker in model_markers):
        errors.append("TB must source expected behavior from the generated FunctionalModel or model adapter")
    return errors


def _row_errors(
    row: dict[str, Any],
    known_goal_ids: set[str],
    line_no: int,
    goals: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    errors: list[str] = []
    required = [
        "goal_id",
        "scenario_id",
        "cycle",
        "stimulus",
        "fl_expected",
        "rtl_observed",
        "passed",
        "mismatch",
        "coverage_refs",
    ]
    for key in required:
        if key not in row:
            errors.append(f"line {line_no}: missing {key}")

    gid = str(row.get("goal_id") or "").strip()
    if not gid:
        errors.append(f"line {line_no}: empty goal_id")
    elif gid not in known_goal_ids:
        errors.append(f"line {line_no}: unknown goal_id {gid}")
    else:
        goal = (goals or {}).get(gid, {})
        scope = goal.get("scope") if isinstance(goal.get("scope"), dict) else {}
        if scope.get("level") == "module":
            row_scope = row.get("scope") if isinstance(row.get("scope"), dict) else {}
            if row_scope.get("level") != "module":
                errors.append(f"line {line_no}: module goal {gid} must record scope.level=module")
            if row_scope.get("rtl_module") != scope.get("rtl_module"):
                errors.append(f"line {line_no}: module goal {gid} must record rtl_module={scope.get('rtl_module')!r}")

    if not str(row.get("scenario_id") or "").strip():
        errors.append(f"line {line_no}: empty scenario_id")

    cycle = row.get("cycle")
    if isinstance(cycle, bool) or not isinstance(cycle, (int, float)):
        errors.append(f"line {line_no}: cycle must be numeric")

    if not isinstance(row.get("passed"), bool):
        errors.append(f"line {line_no}: passed must be boolean")

    mismatch = row.get("mismatch")
    if not isinstance(mismatch, str):
        errors.append(f"line {line_no}: mismatch must be a string")
    elif row.get("passed") is True and mismatch.strip():
        errors.append(f"line {line_no}: passed row must not carry mismatch text")
    elif row.get("passed") is False and not mismatch.strip():
        errors.append(f"line {line_no}: failing row must explain mismatch")

    if not isinstance(row.get("coverage_refs"), list):
        errors.append(f"line {line_no}: coverage_refs must be a list")

    observed = row.get("rtl_observed")
    if not isinstance(observed, dict) or not observed:
        errors.append(f"line {line_no}: rtl_observed must be a non-empty dictionary of DUT signals")
    else:
        fl_expected = row.get("fl_expected") if isinstance(row.get("fl_expected"), dict) else {}
        if set(observed) == {"model_result"}:
            errors.append(f"line {line_no}: rtl_observed must not be copied from FunctionalModel model_result")
        elif observed == fl_expected:
            errors.append(f"line {line_no}: rtl_observed must be DUT-observed signals, not the whole fl_expected payload")
    fl_expected = row.get("fl_expected")
    if isinstance(fl_expected, dict) and fl_expected.get("model_api") != "FunctionalModel.apply":
        errors.append(f"line {line_no}: fl_expected must come from FunctionalModel.apply")

    return errors


def _validate_events(
    path: Path,
    known_goal_ids: set[str],
    goals: dict[str, dict[str, Any]],
) -> tuple[list[str], set[str], int]:
    errors: list[str] = []
    covered: set[str] = set()
    rows = 0
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        rows += 1
        try:
            row = json.loads(line)
        except Exception as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: row must be a JSON object")
            continue
        errors.extend(_row_errors(row, known_goal_ids, line_no, goals))
        gid = str(row.get("goal_id") or "").strip()
        if gid in known_goal_ids:
            covered.add(gid)
    return errors, covered, rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-check", action="store_true")
    parser.add_argument("--require-events", action="store_true")
    parser.add_argument("--require-all-goals", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    goals_path = ip_dir / "verify" / "equivalence_goals.json"
    events_path = ip_dir / "sim" / "scoreboard_events.jsonl"

    if not ip_dir.is_dir():
        print(f"[check_scoreboard_events] FAIL: missing IP directory {ip_dir}")
        return 1
    if not goals_path.is_file():
        print(f"[check_scoreboard_events] SKIP: missing {goals_path.relative_to(root)}")
        return 0 if not args.require_events and not args.require_all_goals else 1

    known_goal_ids, required_goal_ids = _goal_ids(goals_path)
    goals = _goal_map(goals_path)

    errors: list[str] = []
    if args.source_check:
        errors.extend(_validate_source_contract(ip_dir))

    covered: set[str] = set()
    rows = 0
    if events_path.is_file():
        event_errors, covered, rows = _validate_events(events_path, known_goal_ids, goals)
        errors.extend(event_errors)
    elif args.require_events:
        errors.append(f"missing {events_path.relative_to(root)}")

    if args.require_events and rows <= 0:
        errors.append(f"{events_path.relative_to(root)} has no scoreboard rows")

    if args.require_all_goals:
        missing = sorted(required_goal_ids - covered)
        if missing:
            preview = ", ".join(missing[:12])
            suffix = "" if len(missing) <= 12 else f", ... +{len(missing) - 12}"
            errors.append(f"missing scoreboard rows for required goals: {preview}{suffix}")

    if errors:
        for error in errors:
            print(f"[check_scoreboard_events] FAIL: {error}")
        return 1

    print(
        "[check_scoreboard_events] PASS: "
        f"goals={len(known_goal_ids)} required={len(required_goal_ids)} "
        f"scoreboard_rows={rows} goals_with_rows={len(covered)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
