"""Coverage report API — extracted from src/atlas_ui.py.

Hosts GET /api/coverage/report — emits the per-IP coverage summary
consumed by the Coverage workflow panel. Was a 202-line nested route
inside create_app() before Phase 17.

Phase 17 of refactor/atlas-modular (backend extraction).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse


def register_coverage_report_routes(
    app, *,
    PROJECT_ROOT,
    _safe,
    _parse_lcov_summary,
    _choose_coverage_ip_dir,
    _coverage_card,
    _coverage_metric,
    _domain_coverage_from_report,
    _normalize_toggle_report,
    _read_json_artifact,
    _static_rtl_coverage,
) -> None:
    """Register GET /api/coverage/report on `app`.

    9 closure captures from the original create_app() nesting — all coverage
    helper functions that parse/normalize/render the per-IP coverage payload.
    """
    @app.get("/reports/cov")
    @app.get("/api/reports/cov")
    @app.get("/api/reports/coverage")
    @app.get("/api/coverage/report")
    async def api_coverage_report(ip: str, top: str = "", refresh: int = 0, vcd: int = 0):
        """Return a consolidated coverage report for Atlas.

        The endpoint intentionally aggregates existing workflow artifacts
        instead of inventing a second coverage format:
        Verilator LCOV, SSOT FL/CL coverage, VCD toggle coverage, and a
        pyslang/static RTL source universe.
        """
        ip_dir = _choose_coverage_ip_dir(ip)
        if ip_dir is None:
            return JSONResponse({"error": "IP directory not found", "ip": ip}, status_code=404)

        rel_ip = ip_dir.relative_to(PROJECT_ROOT).as_posix()
        cov_dir = ip_dir / "cov"
        sim_dir = ip_dir / "sim"
        run_info: dict[str, Any] = {}

        if refresh:
            script = WORKFLOW_ROOT / "coverage" / "scripts" / "ssot_coverage_summary.py"
            cmd = [_python_cmd(), str(script), rel_ip]

            def _run_summary():
                return subprocess.run(
                    cmd,
                    cwd=PROJECT_ROOT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                )

            try:
                proc = await asyncio.to_thread(_run_summary)
                run_info["summary"] = {
                    "command": shlex.join(cmd),
                    "returncode": proc.returncode,
                    "output": proc.stdout[-12000:] if proc.stdout else "",
                }
            except subprocess.TimeoutExpired as exc:
                run_info["summary"] = {"command": shlex.join(cmd), "returncode": 124, "output": str(exc)}
            except Exception as exc:
                run_info["summary"] = {"command": shlex.join(cmd), "returncode": 1, "output": str(exc)}

        if vcd:
            script = WORKFLOW_ROOT / "coverage" / "scripts" / "coverage_vcd_toggle.sh"
            cmd = ["bash", str(script), rel_ip, "--json"]
            if top:
                cmd.extend(["--top", top])

            def _run_vcd_toggle():
                return subprocess.run(
                    cmd,
                    cwd=PROJECT_ROOT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                )

            try:
                proc = await asyncio.to_thread(_run_vcd_toggle)
                run_info["vcd"] = {
                    "command": shlex.join(cmd),
                    "returncode": proc.returncode,
                    "output": proc.stdout[-12000:] if proc.stdout else "",
                }
            except subprocess.TimeoutExpired as exc:
                run_info["vcd"] = {"command": shlex.join(cmd), "returncode": 124, "output": str(exc)}
            except Exception as exc:
                run_info["vcd"] = {"command": shlex.join(cmd), "returncode": 1, "output": str(exc)}

        coverage_json_path = cov_dir / "coverage.json"
        coverage_ssot_path = cov_dir / "coverage_ssot.json"
        coverage_info_path = cov_dir / "coverage.info"
        toggle_path = cov_dir / "toggle.json"
        report_md_path = sim_dir / "coverage_report.md"

        coverage_doc, coverage_error = _read_json_artifact(coverage_json_path)
        ssot_doc, ssot_error = _read_json_artifact(coverage_ssot_path)
        if not coverage_doc and ssot_doc:
            coverage_doc = ssot_doc
        lcov = _parse_lcov_summary(coverage_info_path)
        toggle_doc, toggle_error = _read_json_artifact(toggle_path)
        toggle_report = _normalize_toggle_report(toggle_doc, toggle_path)
        static_report = _static_rtl_coverage(ip_dir, rel_ip)
        function_cov = _domain_coverage_from_report(coverage_doc, "function")
        cycle_cov = _domain_coverage_from_report(coverage_doc, "cycle")

        ver_lines = coverage_doc.get("lines") if isinstance(coverage_doc.get("lines"), dict) else lcov["lines"]
        ver_branches = coverage_doc.get("branches") if isinstance(coverage_doc.get("branches"), dict) else lcov["branches"]
        ver_functions = coverage_doc.get("functions") if isinstance(coverage_doc.get("functions"), dict) else lcov["functions"]
        verilator_available = lcov["available"] or bool(coverage_doc.get("lines") or coverage_doc.get("branches"))
        static_metrics = static_report["metrics"]

        tools = [
            _coverage_card(
                "verilator",
                "Verilator code coverage",
                verilator_available,
                "available" if verilator_available else "missing",
                [
                    {"label": "line", **_coverage_metric(ver_lines.get("hit"), ver_lines.get("total"), ver_lines.get("target_pct"))},
                    {"label": "branch", **_coverage_metric(ver_branches.get("hit"), ver_branches.get("total"), ver_branches.get("target_pct"))},
                    {"label": "function", **_coverage_metric(ver_functions.get("hit"), ver_functions.get("total"))},
                ],
                path=lcov.get("path") or coverage_info_path.relative_to(PROJECT_ROOT).as_posix(),
                files=lcov.get("files", []),
                note="Runtime code coverage from Verilator LCOV / coverage.info.",
            ),
            _coverage_card(
                "pyslang",
                "pyslang static/elab coverage",
                bool(static_report["rtl_files"]),
                "pass" if static_report["passed"] else "blocked",
                [
                    {"label": "rtl files", "hit": static_metrics["files"], "total": static_metrics["listed_files"], "pct": round(100.0 * static_metrics["files"] / static_metrics["listed_files"], 2) if static_metrics["listed_files"] else None},
                    {"label": "modules", "value": static_metrics["modules"]},
                    {"label": "source lines", "value": static_metrics["lines"]},
                    {"label": "always", "value": static_metrics["always_blocks"]},
                ],
                diagnostics=static_report["diagnostics"],
                files=static_report["files"],
                missing=static_report["missing"],
                note="Static RTL universe plus pyslang parse/elaboration diagnostics. This is not runtime hit coverage.",
            ),
            _coverage_card(
                "sim-vcd",
                "Simulation VCD toggle coverage",
                toggle_report["available"],
                "available" if toggle_report["available"] else "missing",
                [
                    {"label": "toggle", **toggle_report["metrics"]},
                    {"label": "nets", "value": toggle_report["nets"]},
                ],
                path=toggle_report["path"],
                vcd=toggle_report["vcd"],
                scopes=toggle_report["scopes"],
                note="Bit is covered when it observed both a rise and a fall in the VCD.",
            ),
            _coverage_card(
                "functional-fl",
                "FL function coverage",
                function_cov["total"] > 0,
                "pass" if function_cov.get("meets_target") else "blocked",
                [{"label": "function bins", **_coverage_metric(function_cov["hit"], function_cov["total"], function_cov.get("target_pct"))}],
                bins=function_cov["bins"],
                missing_bins=function_cov["missing_bins"],
                note="Function-model / scenario coverage from SSOT functional bins.",
            ),
            _coverage_card(
                "functional-cl",
                "CL cycle coverage",
                cycle_cov["total"] > 0,
                "pass" if cycle_cov.get("meets_target") else "blocked",
                [{"label": "cycle bins", **_coverage_metric(cycle_cov["hit"], cycle_cov["total"], cycle_cov.get("target_pct"))}],
                bins=cycle_cov["bins"],
                missing_bins=cycle_cov["missing_bins"],
                note="Cycle-model / protocol coverage from SSOT functional bins.",
            ),
        ]

        vcd_paths = [
            p.relative_to(PROJECT_ROOT).as_posix()
            for p in sorted(list(sim_dir.glob("**/*.vcd")) + list(cov_dir.glob("**/*.vcd")))
            if p.is_file()
        ]
        artifact_paths = [
            p.relative_to(PROJECT_ROOT).as_posix()
            for p in (coverage_json_path, coverage_ssot_path, coverage_info_path, toggle_path, report_md_path)
            if p.is_file()
        ]

        return JSONResponse({
            "ip": ip,
            "resolved_ip": rel_ip,
            "top": top or ip_dir.name,
            "exists": bool(coverage_doc or lcov["available"] or toggle_report["available"] or static_report["rtl_files"]),
            "status": coverage_doc.get("status", "unknown") if coverage_doc else "unknown",
            "errors": [e for e in (coverage_error, ssot_error, toggle_error, lcov.get("error")) if e],
            "report_path": coverage_json_path.relative_to(PROJECT_ROOT).as_posix(),
            "report_exists": coverage_json_path.is_file(),
            "ssot_path": coverage_ssot_path.relative_to(PROJECT_ROOT).as_posix(),
            "ssot_exists": coverage_ssot_path.is_file(),
            "lcov_path": coverage_info_path.relative_to(PROJECT_ROOT).as_posix(),
            "lcov_exists": coverage_info_path.is_file(),
            "toggle_path": toggle_path.relative_to(PROJECT_ROOT).as_posix(),
            "toggle_exists": toggle_path.is_file(),
            "markdown_path": report_md_path.relative_to(PROJECT_ROOT).as_posix(),
            "markdown_exists": report_md_path.is_file(),
            "artifacts": artifact_paths,
            "vcd_paths": vcd_paths,
            "tools": tools,
            "coverage": coverage_doc,
            "lcov": lcov,
            "toggle": toggle_report,
            "static": static_report,
            "run": run_info,
        })

