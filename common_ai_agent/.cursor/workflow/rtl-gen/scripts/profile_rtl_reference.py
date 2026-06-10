#!/usr/bin/env python3
"""Profile a reference RTL tree for scale calibration only.

This script never imports or transforms reference RTL into the generated IP.
It emits coarse structural metrics so rtl-gen can understand the expected
implementation scale without treating the reference as a fixed template.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any


RTL_SUFFIXES = (".sv", ".svh", ".v", ".vh", ".sv.xsl", ".v.xsl")
TARGET_EXCLUDE_PARTS = {
    "assertion",
    "assertions",
    "coverage",
    "cov",
    "sim",
    "simulation",
    "stim",
    "stimulus",
    "tb",
    "test",
    "tests",
    "testbench",
    "validation",
    "verify",
    "verification",
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _is_rtl_file(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in RTL_SUFFIXES)


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//.*", "", text)


def _count_instance_candidates(text: str) -> int:
    count = 0
    for match in re.finditer(
        r"(?m)^\s*([A-Za-z_][A-Za-z0-9_$]*)\s+(?:#\s*\(|[A-Za-z_][A-Za-z0-9_$]*\s*\()",
        text,
    ):
        cell = match.group(1)
        if cell in {
            "assign",
            "always",
            "always_comb",
            "always_ff",
            "always_latch",
            "begin",
            "case",
            "else",
            "end",
            "endcase",
            "endmodule",
            "for",
            "function",
            "generate",
            "if",
            "initial",
            "module",
            "task",
            "typedef",
        }:
            continue
        count += 1
    return count


def _count_state_updates(text: str) -> int:
    """Count state-like nonblocking updates without treating assigns as state."""
    return len(re.findall(r"\b[A-Za-z_][A-Za-z0-9_$]*(?:\[[^\]]+\])?\s*<=", text))


def _is_constant_expr(expr: str) -> bool:
    value = re.sub(r"\s+", "", expr.strip())
    if not value:
        return False
    if re.fullmatch(r"[0-9]+", value):
        return True
    if re.fullmatch(r"[0-9]*'[sS]?[bBoOdDhH][0-9a-fA-F_xXzZ?]+", value):
        return True
    if re.fullmatch(r"\{[0-9]+\{(?:1'b[01xXzZ]|1'h[0-9a-fA-FxXzZ])\}\}", value):
        return True
    return value in {"1'b0", "1'b1", "1'bx", "1'bz", "'0", "'1"}


def _count_nonconstant_assigns(text: str) -> int:
    count = 0
    for match in re.finditer(r"\bassign\b\s+[^=;]+=\s*([^;]+);", text, flags=re.S):
        if not _is_constant_expr(match.group(1)):
            count += 1
    return count


def _profile_bucket(rel: str) -> str:
    parts = [part.lower() for part in Path(rel).parts]
    if any(part in TARGET_EXCLUDE_PARTS for part in parts):
        return "verification_collateral"
    if any(part in {"bin", "scripts", "tools"} for part in parts):
        return "tooling"
    if any(part in {"include", "includes", "xsl_include"} for part in parts):
        return "include_support"
    return "design_candidate"


def _add_file_metrics(summary: Counter[str], raw: str, text: str, *, line_count: int) -> None:
    summary["lines"] += line_count
    summary["modules"] += len(re.findall(r"\bmodule\s+[A-Za-z_][A-Za-z0-9_$]*", text))
    summary["always_blocks"] += len(re.findall(r"\balways(?:_ff|_comb|_latch)?\b", text))
    summary["assigns"] += len(re.findall(r"\bassign\b", text))
    summary["nonconstant_assigns"] += _count_nonconstant_assigns(text)
    summary["case_blocks"] += len(re.findall(r"\bcase[zx]?\s*\(", text))
    summary["instance_candidates"] += _count_instance_candidates(text)
    summary["state_updates"] += _count_state_updates(text)
    summary["file_count"] += 1


def _suggested_ssot_target_scale(summary: Counter[str]) -> dict[str, Any]:
    """Return a human-review candidate for quality_gates.rtl_gen.target_scale."""
    target = {
        "basis": "candidate structural scale from rtl_reference_profile; review and lock in SSOT before enforcement",
        "source_files_min": int(summary.get("file_count") or 0),
        "modules_min": int(summary.get("modules") or 0),
        "lines_min": int(summary.get("lines") or 0),
        "procedural_blocks_min": int(summary.get("always_blocks") or 0),
        "nonconstant_assigns_min": int(summary.get("nonconstant_assigns") or 0),
        "control_flow_min": int(summary.get("case_blocks") or 0),
        "instances_min": int(summary.get("instance_candidates") or 0),
        "state_updates_min": int(summary.get("state_updates") or 0),
    }
    target["depth_score_min"] = (
        target["nonconstant_assigns_min"]
        + target["procedural_blocks_min"] * 3
        + target["state_updates_min"] * 2
        + target["control_flow_min"]
        + target["instances_min"] * 2
    )
    return {key: value for key, value in target.items() if key == "basis" or int(value) > 0}


def profile_reference(reference_root: Path, *, label: str = "", max_top_files: int = 20) -> dict[str, Any]:
    root = reference_root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"reference root does not exist: {root}")
    files = sorted(path for path in root.rglob("*") if path.is_file() and _is_rtl_file(path))
    summary: Counter[str] = Counter()
    target_summary: Counter[str] = Counter()
    bucket_summaries: dict[str, Counter[str]] = {}
    extension_counts: Counter[str] = Counter()
    top_by_lines: list[dict[str, Any]] = []

    for path in files:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        text = _strip_comments(raw)
        line_count = raw.count("\n") + (1 if raw and not raw.endswith("\n") else 0)
        rel = str(path.relative_to(root))
        bucket = _profile_bucket(rel)
        bucket_summary = bucket_summaries.setdefault(bucket, Counter())
        extension_counts["".join(path.suffixes[-2:]) if path.name.lower().endswith(".xsl") else path.suffix] += 1
        top_by_lines.append({"path": rel, "lines": line_count, "bucket": bucket})
        _add_file_metrics(summary, raw, text, line_count=line_count)
        _add_file_metrics(bucket_summary, raw, text, line_count=line_count)
        if bucket == "design_candidate":
            _add_file_metrics(target_summary, raw, text, line_count=line_count)

    top_by_lines.sort(key=lambda item: int(item["lines"]), reverse=True)
    target_basis = "design_candidate"
    if not target_summary.get("file_count"):
        target_basis = "all"
        target_summary = Counter(summary)
    return {
        "schema_version": 1,
        "type": "rtl_reference_profile",
        "label": label or root.name,
        "generated_at": _utc(),
        "reference_root": str(root),
        "summary": dict(summary),
        "target_candidate_summary": dict(target_summary),
        "target_candidate_basis": target_basis,
        "bucket_summaries": {
            key: dict(bucket_summaries[key])
            for key in sorted(bucket_summaries)
        },
        "file_extension_counts": dict(sorted(extension_counts.items())),
        "top_by_lines": top_by_lines[:max_top_files],
        "suggested_ssot_target_scale": _suggested_ssot_target_scale(target_summary),
        "guidance": {
            "calibration_only": True,
            "do_not_copy_reference_rtl": True,
            "target_candidate_rule": (
                "suggested_ssot_target_scale is derived from design_candidate files when available, "
                "excluding validation/testbench/simulation collateral by path bucket."
            ),
            "rule": (
                "Use this profile only to calibrate implementation scale, review depth gaps, "
                "and plan decomposition. It is not a template, source artifact, or PASS gate."
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("reference_root")
    ap.add_argument("--label", default="")
    ap.add_argument("--output", default="")
    ap.add_argument("--max-top-files", type=int, default=20)
    ns = ap.parse_args()

    profile = profile_reference(Path(ns.reference_root), label=ns.label, max_top_files=max(0, ns.max_top_files))
    text = json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if ns.output:
        output = Path(ns.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
