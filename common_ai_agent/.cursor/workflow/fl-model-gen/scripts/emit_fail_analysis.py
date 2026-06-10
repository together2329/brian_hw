#!/usr/bin/env python3
"""Synthesize a Markdown root-cause report from a scoreboard diff.

L9 of the human-LLM authority manifest. Reads a JSONL diff file (each
line = one comparison row with goal_id, expected, actual, optional
context fields) plus optional log/coverage hints, and writes
<ip>/reports/fail_analysis.md with a structured root-cause skeleton that
the LLM can edit to add specific RTL-patch suggestions.

Usage:
  python3 workflow/fl-model-gen/scripts/emit_fail_analysis.py <ip> \
      --diff <ip>/sim/scoreboard_diff.jsonl --root .
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise SystemExit(f"missing diff JSONL: {path}")
    out: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            obj = json.loads(line)
        except Exception as exc:
            raise SystemExit(f"{path}:{line_no} invalid JSON: {exc}")
        if not isinstance(obj, dict):
            raise SystemExit(f"{path}:{line_no} expected JSON object")
        out.append(obj)
    return out


def _classify_owner(row: dict[str, Any]) -> str:
    # Owner heuristic — never authoritative; LLM can override in the report.
    expected = row.get("expected")
    actual = row.get("actual")
    goal_id = str(row.get("goal_id") or "")
    if expected == actual:
        return "tb"  # diff row but values match — likely a stimulus/timing issue
    if "PROTOCOL" in goal_id or "TIMING" in goal_id:
        return "rtl|tb"
    if "MODULE" in goal_id:
        return "rtl"
    if "COVERAGE" in goal_id:
        return "tb"
    if "ERROR" in goal_id:
        return "rtl"
    return "rtl"


def _format_row(row: dict[str, Any]) -> str:
    goal = row.get("goal_id") or row.get("goal") or "<unknown_goal>"
    expected = row.get("expected")
    actual = row.get("actual")
    context = row.get("context") or row.get("note") or ""
    likely = row.get("likely_cause") or "[LLM TODO] inspect FL trace + RTL waveform around this goal"
    patch = row.get("suggested_patch") or "[LLM TODO] propose minimal RTL patch in the owning module"
    owner = row.get("owner_on_fail") or _classify_owner(row)
    lines = [
        f"### {goal}",
        f"- **Owner-on-fail (heuristic, LLM can override)**: `{owner}`",
        f"- **Expected**: `{json.dumps(expected, sort_keys=True) if expected is not None else '<none>'}`",
        f"- **Actual**:   `{json.dumps(actual, sort_keys=True) if actual is not None else '<none>'}`",
    ]
    if context:
        lines.append(f"- **Context**: {context}")
    lines.append(f"- **Likely cause**: {likely}")
    lines.append(f"- **Suggested RTL patch**: {patch}")
    if row.get("trace"):
        lines.append("- **Trace excerpt**:")
        lines.append("  ```")
        for entry in (row.get("trace") or [])[:8]:
            lines.append(f"  {json.dumps(entry, sort_keys=True)}")
        lines.append("  ```")
    return "\n".join(lines)


def _summary_block(rows: list[dict[str, Any]]) -> str:
    by_owner: dict[str, int] = {}
    for r in rows:
        o = r.get("owner_on_fail") or _classify_owner(r)
        by_owner[o] = by_owner.get(o, 0) + 1
    parts = [f"- Total failing rows: **{len(rows)}**"]
    for owner, n in sorted(by_owner.items()):
        parts.append(f"- Owner-on-fail `{owner}`: {n}")
    return "\n".join(parts)


def _build_markdown(ip: str, rows: list[dict[str, Any]], extra: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# Fail analysis — {ip}")
    lines.append("")
    lines.append("> Auto-generated skeleton. The LLM is expected to fill in `[LLM TODO]` slots")
    lines.append("> with specific patch proposals. **Cardinal rule**: do NOT modify FL/spec/coverage")
    lines.append("> to make the test pass — only RTL/TB/vectors are LLM-editable.")
    lines.append("")
    lines.append("## Summary")
    lines.append(_summary_block(rows))
    if extra.get("failing_test"):
        lines.append(f"- Failing test: `{extra['failing_test']}`")
    if extra.get("seed"):
        lines.append(f"- Seed: `{extra['seed']}`")
    if extra.get("log"):
        lines.append(f"- Sim log: `{extra['log']}`")
    lines.append("")
    lines.append("## Detail")
    for row in rows:
        lines.append(_format_row(row))
        lines.append("")
    lines.append("## Next steps (LLM owned)")
    lines.append("1. Pick the highest-priority owner-on-fail entry (rtl > rtl|tb > tb).")
    lines.append("2. Look at the corresponding RTL module + the FL trace around the failing transaction.")
    lines.append("3. Propose the smallest RTL patch that closes the diff. Do NOT touch FL.")
    lines.append("4. Re-run cocotb harness (`make fl_cl_rtl` in `<ip>/verify/`).")
    lines.append("5. If still failing, run `emit_regression_min.py` to bisect the seed first.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--diff", required=True, help="Path to scoreboard diff JSONL")
    parser.add_argument("--failing-test", default="")
    parser.add_argument("--seed", default="")
    parser.add_argument("--log", default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    diff_path = (root / args.diff).resolve() if not Path(args.diff).is_absolute() else Path(args.diff).resolve()

    rows = _load_jsonl(diff_path)
    if not rows:
        raise SystemExit(f"diff JSONL is empty: {diff_path}")

    extra = {"failing_test": args.failing_test, "seed": args.seed, "log": args.log}
    md = _build_markdown(args.ip, rows, extra)

    reports_dir = ip_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = Path(args.out).resolve() if args.out else reports_dir / "fail_analysis.md"
    out_path.write_text(md, encoding="utf-8")

    summary = {
        "schema_version": 1,
        "type": "fail_analysis_summary",
        "ip": args.ip,
        "diff_source": str(diff_path),
        "rows": len(rows),
        "failing_test": args.failing_test,
        "output": str(out_path.relative_to(ip_dir)) if str(out_path).startswith(str(ip_dir)) else str(out_path),
    }
    (reports_dir / "fail_analysis.summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    print(f"[emit_fail_analysis] {args.ip} rows={len(rows)} -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
