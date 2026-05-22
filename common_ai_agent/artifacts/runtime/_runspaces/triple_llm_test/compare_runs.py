#!/usr/bin/env python3
"""Compare the three rv32i_min triple-LLM pipeline runs side-by-side.

Reads each provider's `_runspaces/triple_llm_test/<prov>/run.json` plus
the per-stage evidence inside `<prov>/rv32i_min/` and writes a
markdown comparison to `_runspaces/triple_llm_test/COMPARISON.md`.

Same SSOT input → three model providers (gpt-5.3-codex, claude-cli,
cursor-cli) → side-by-side audit. No code in the IPs is touched.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PROVIDERS = ("codex", "claude", "cursor")
MODEL_BY_PROV = {
    "codex": "gpt-5.3-codex",
    "claude": "claude-cli",
    "cursor": "cursor-cli",
}
STAGES = (
    "ssot-gen",
    "fl-model-gen",
    "cl-model-gen",
    "equiv-goals",
    "rtl-gen",
    "tb-gen",
    "sim",
    "sim-debug",
    "lint",
    "coverage",
    "goal-audit",
)


def _safe_json(path: Path) -> Any:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _stage_status(run_doc: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {s: "—" for s in STAGES}
    for stage in run_doc.get("stages", []) or []:
        name = str(stage.get("stage") or "")
        st = str(stage.get("status") or "—")
        if name in out:
            out[name] = st
    return out


def _ip_dir(prov: str) -> Path:
    return ROOT / prov / "rv32i_min"


def _llm_call_stats(prov: str) -> dict[str, str]:
    """Count LLM calls and aggregate wall-time / token usage from llm_call_trace.jsonl."""
    ip = _ip_dir(prov)
    trace = ip / "logs" / "llm_call_trace.jsonl"
    if not trace.is_file():
        return {}
    calls = 0
    by_stage: dict[str, int] = {}
    total_in = 0
    total_out = 0
    wall_ms = 0
    for line in trace.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except Exception:
            continue
        calls += 1
        stage = str(row.get("stage") or row.get("caller_tag") or "?")
        by_stage[stage] = by_stage.get(stage, 0) + 1
        usage = row.get("usage") if isinstance(row.get("usage"), dict) else {}
        total_in += int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        total_out += int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        try:
            wall_ms += int(row.get("duration_ms") or 0)
        except Exception:
            pass
    out: dict[str, str] = {
        "llm_calls_total": str(calls),
        "llm_input_tokens": str(total_in) if total_in else "—",
        "llm_output_tokens": str(total_out) if total_out else "—",
        "llm_wall_seconds": f"{wall_ms / 1000:.1f}" if wall_ms else "—",
    }
    if by_stage:
        out["llm_calls_by_stage"] = " ".join(f"{k}:{v}" for k, v in sorted(by_stage.items()))
    return out


def _stage_wall_seconds(run_doc: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for stage in run_doc.get("stages", []) or []:
        name = str(stage.get("stage") or "")
        for key in ("duration_seconds", "wall_seconds", "elapsed_seconds"):
            if key in stage and stage[key] is not None:
                try:
                    out[name] = f"{float(stage[key]):.1f}s"
                except Exception:
                    pass
                break
    return out


def _digest_artifact(prov: str) -> dict[str, str]:
    ip = _ip_dir(prov)
    out: dict[str, str] = {}
    out.update(_llm_call_stats(prov))
    ssot_path = ip / "yaml" / "rv32i_min.ssot.yaml"
    if ssot_path.is_file():
        out["ssot_size"] = f"{ssot_path.stat().st_size}B"
        out["ssot_sections"] = str(
            sum(1 for line in ssot_path.read_text(errors="replace").splitlines()
                if line and line[0].isalpha() and ":" in line and not line.startswith(" "))
        )
    fl_check = _safe_json(ip / "model" / "fl_model_check.json")
    if isinstance(fl_check, dict):
        out["fl_check"] = "pass" if fl_check.get("passed") else "fail"
    rtl_compile = _safe_json(ip / "rtl" / "rtl_compile.json")
    if isinstance(rtl_compile, dict):
        out["rtl_compile_errors"] = str(rtl_compile.get("errors", "?"))
        out["rtl_compile_warnings"] = str(rtl_compile.get("warnings", "?"))
    rtl_dir = ip / "rtl"
    if rtl_dir.is_dir():
        sv = sorted(p.name for p in rtl_dir.glob("*.sv"))
        out["rtl_files"] = str(len(sv))
    lint = _safe_json(ip / "lint" / "dut_lint.json")
    if isinstance(lint, dict):
        out["lint_errors"] = str(lint.get("errors", "?"))
        out["lint_warnings"] = str(lint.get("warnings", "?"))
    sim_compare = _safe_json(ip / "sim" / "fl_rtl_compare.json")
    if isinstance(sim_compare, dict):
        out["sim_total"] = str(sim_compare.get("total_rows", sim_compare.get("total", "?")))
        out["sim_pass"] = str(sim_compare.get("pass_rows", sim_compare.get("pass", "?")))
        out["sim_mismatch"] = str(sim_compare.get("mismatch_count", "?"))
    sim_audit = _safe_json(ip / "sim" / "fl_rtl_goal_audit.json")
    if isinstance(sim_audit, dict):
        bins = sim_audit.get("bins") if isinstance(sim_audit.get("bins"), dict) else {}
        if bins:
            out["bins_hit"] = str(bins.get("hit") or bins.get("hit_count") or "?")
            out["bins_total"] = str(bins.get("total") or "?")
        else:
            out["bins_hit"] = str(sim_audit.get("bins_hit", "?"))
            out["bins_total"] = str(sim_audit.get("bins_total", "?"))
    audit_doc = _safe_json(ip / "verify" / "equivalence_goals.json")
    if isinstance(audit_doc, dict):
        goals = audit_doc.get("goals") or []
        blocked = audit_doc.get("blocked")
        if blocked is None and isinstance(goals, list):
            blocked = sum(1 for g in goals if isinstance(g, dict) and g.get("blocked"))
        out["equiv_goals"] = str(len(goals) if isinstance(goals, list) else "?")
        out["equiv_blocked"] = str(blocked) if blocked is not None else "?"
    classification = _safe_json(ip / "sim" / "mismatch_classification.json")
    if isinstance(classification, dict):
        items = classification.get("classifications") or []
        if isinstance(items, list):
            out["mismatch_classified"] = str(len(items))
            owner_counts: dict[str, int] = {}
            for it in items:
                if isinstance(it, dict):
                    owner_counts[str(it.get("owner", "?"))] = owner_counts.get(str(it.get("owner", "?")), 0) + 1
            if owner_counts:
                out["mismatch_owners"] = " ".join(f"{k}:{v}" for k, v in sorted(owner_counts.items()))
    run_log = _safe_json(ip / "logs" / "headless_run.json")
    if isinstance(run_log, dict):
        out["run_status"] = str(run_log.get("status", "?"))
    return out


def main() -> int:
    rows: dict[str, dict[str, Any]] = {}
    for prov in PROVIDERS:
        run = _safe_json(ROOT / prov / "run.json") or {}
        rows[prov] = {
            "model": MODEL_BY_PROV[prov],
            "overall": str(run.get("status", "—")),
            "stages": _stage_status(run),
            "digest": _digest_artifact(prov),
        }

    lines: list[str] = []
    lines.append("# Triple-LLM `rv32i_min` Pipeline Comparison")
    lines.append("")
    lines.append(f"_Generated: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}_")
    lines.append("")
    lines.append("Same SSOT input (`requirements.md`, RV32I 37 instructions, 3-stage), three model providers, identical pipeline")
    lines.append("(`ssot-gen → fl-model-gen → cl-model-gen → equiv-goals → rtl-gen → tb-gen → sim → sim-debug → lint → coverage → goal-audit`).")
    lines.append("**No manual fixes between stages.**")
    lines.append("")
    lines.append("## Overall outcome")
    lines.append("")
    lines.append("| Provider | Model | Overall |")
    lines.append("|---|---|---|")
    for prov in PROVIDERS:
        lines.append(f"| {prov} | `{rows[prov]['model']}` | **{rows[prov]['overall']}** |")
    lines.append("")
    lines.append("## Per-stage status")
    lines.append("")
    header = "| Stage | " + " | ".join(PROVIDERS) + " |"
    sep = "|---|" + "---|" * len(PROVIDERS)
    lines.append(header)
    lines.append(sep)
    for stage in STAGES:
        row = [stage] + [rows[prov]["stages"].get(stage, "—") for prov in PROVIDERS]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## Artifact digests")
    lines.append("")
    digest_keys = (
        "ssot_size",
        "ssot_sections",
        "fl_check",
        "rtl_files",
        "rtl_compile_errors",
        "rtl_compile_warnings",
        "lint_errors",
        "lint_warnings",
        "sim_total",
        "sim_pass",
        "sim_mismatch",
        "bins_hit",
        "bins_total",
        "equiv_goals",
        "equiv_blocked",
        "mismatch_classified",
        "mismatch_owners",
        "run_status",
    )
    lines.append("| Metric | " + " | ".join(PROVIDERS) + " |")
    lines.append("|---|" + "---|" * len(PROVIDERS))
    for k in digest_keys:
        row = [k] + [rows[prov]["digest"].get(k, "—") for prov in PROVIDERS]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("## Reading guide")
    lines.append("")
    lines.append("- `sim_mismatch=0` and `lint_errors=0` is the smoke-test green line.")
    lines.append("- `equiv_blocked > 0` means the SSOT had at least one sub_module without function_model_refs (or another goal-level blocker).")
    lines.append("- `mismatch_owners` (when present) shows how `compare_fl_rtl_results.py` classified the failures: `tb-gen` vs `rtl-gen` vs `ssot-gen`.")
    lines.append("- `run_status` is `pass` only if every stage in this run passed its validator. `blocked` means the pipeline stopped at a human-gate; `fail` means a validator hard-failed.")
    lines.append("")
    lines.append("## Raw evidence")
    lines.append("")
    for prov in PROVIDERS:
        lines.append(f"- `{prov}/run.json` — pipeline run trace")
        lines.append(f"- `{prov}/rv32i_min/` — full IP tree (yaml/, model/, rtl/, tb/, sim/, lint/, cov/, verify/, logs/)")
        lines.append(f"- `{prov}/rv32i_min/wiki/_graph.json` — auto-generated knowledge graph (read with `wiki_query(ip='rv32i_min')`)")

    out_path = ROOT / "COMPARISON.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[compare_runs] wrote {out_path.relative_to(ROOT.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
