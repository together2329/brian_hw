"""SSOT gates API — extracted from src/atlas_ui.py.

Hosts GET /api/ssot-gates/{ip} — collects every workflow-stage gate
status for a single IP from disk evidence (ssot/rtl/sim/lint/coverage/
syn/sta/pnr/sta-post stages + dependency map + overall summary). Was a
497-line nested route inside create_app() before Phase 15.

Factory pattern: register_ssot_gates_routes(app, **deps) takes the 2
real closure captures from the original nesting (PROJECT_ROOT, _safe)
as keyword arguments whose names mirror the original locals — so the
route body needs ZERO textual modification.

Phase 15 of refactor/atlas-modular (backend extraction).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse


def register_ssot_gates_routes(
    app,
    *,
    PROJECT_ROOT,
    _safe,
) -> None:
    """Register GET /api/ssot-gates/{ip} on `app` via dep-injected helpers.

    The 2 kwarg names mirror the locals the original body referenced inside
    create_app(), so no edits to the route body are required.
    """
    @app.get("/api/ssot-gates/{ip}")
    async def api_ssot_gates(ip: str):
        """Aggregate SSOT-quality + per-stage checker results for one IP.

        Drives the SSOT Design Preview "Gates" tab. Reads existing
        artifacts produced by repair_ssot_schema, check_ssot_disk,
        emit_fl_model, emit_equivalence_goals, ssot_to_rtl, rtl_compile,
        dut_lint, fl_rtl_compare, fl_rtl_goal_audit, etc. Does NOT
        re-run any LLM-bearing stage; only inspects evidence on disk.
        """
        import yaml as _yaml
        ip_dir = _safe(ip)
        if ip_dir is None or not ip_dir.is_dir():
            return JSONResponse({"error": "ip not found", "ip": ip}, status_code=404)

        def _read_json(path: Path) -> Any:
            if not path.is_file():
                return None
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None

        def _stat_iso(path: Path) -> str:
            if not path.exists():
                return ""
            try:
                ts = path.stat().st_mtime
                return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
            except Exception:
                return ""

        def _rel(path: Path) -> str:
            try:
                return str(path.relative_to(PROJECT_ROOT))
            except Exception:
                return str(path)

        ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
        ssot_doc: dict[str, Any] = {}
        ssot_parses = False
        if ssot_path.is_file():
            try:
                ssot_doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
                ssot_parses = isinstance(ssot_doc, dict)
            except Exception:
                ssot_parses = False

        REQUIRED_SECTIONS = [
            "top_module", "sub_modules", "decomposition", "parameters", "io_list",
            "features", "dataflow", "function_model", "cycle_model", "rtl_contract",
            "clock_reset_domains", "cdc_requirements", "rdc_requirements",
            "registers", "memory", "interrupts", "fsm",
            "timing", "power", "security", "error_handling", "debug_observability",
            "integration", "dft", "synthesis", "pnr", "test_requirements",
            "quality_gates", "traceability", "workflow_todos", "filelist",
            "coding_rules", "reuse_modules", "custom", "dir_structure",
            "generation_flow",
        ]

        present_sections = sum(1 for k in REQUIRED_SECTIONS if k in ssot_doc)
        legacy_keys = [
            k for k in ("interface", "bus_interface", "apb_behavior", "clock_reset",
                        "interrupt", "interrupt_behavior", "register_map",
                        "submodule_structure", "counter_behavior", "reset_behavior")
            if k in ssot_doc
        ]
        ssot_text = ""
        try:
            ssot_text = ssot_path.read_text(encoding="utf-8") if ssot_path.is_file() else ""
        except Exception:
            pass
        tbd_count = ssot_text.count("TBD") + ssot_text.count("?TBD")

        downstream_doc = _read_json(ip_dir / "req" / "ssot_downstream_blockers.json")
        downstream_blockers = []
        if isinstance(downstream_doc, dict):
            downstream_blockers = downstream_doc.get("issues") or downstream_doc.get("blockers") or []

        fm = ssot_doc.get("function_model") if isinstance(ssot_doc.get("function_model"), dict) else {}
        txs = [t for t in (fm.get("transactions") or []) if isinstance(t, dict)]
        rtl_contract = ssot_doc.get("rtl_contract") if isinstance(ssot_doc.get("rtl_contract"), dict) else {}
        input_map = rtl_contract.get("input_map") if isinstance(rtl_contract.get("input_map"), dict) else {}
        output_map = rtl_contract.get("output_map") if isinstance(rtl_contract.get("output_map"), dict) else {}
        sample_condition = str(rtl_contract.get("sample_condition") or "")

        sub_modules = ssot_doc.get("sub_modules") if isinstance(ssot_doc.get("sub_modules"), list) else []
        owned = sum(1 for m in sub_modules if isinstance(m, dict) and (m.get("owner") or m.get("ownership")))
        with_fm_refs = sum(1 for m in sub_modules if isinstance(m, dict) and m.get("function_model_refs"))

        quality: list[dict[str, Any]] = []

        def _add_q(id_: str, label: str, status: str, summary: str, evidence: list[str] = None,
                   helper: str = ""):
            quality.append({
                "id": id_,
                "label": label,
                "status": status,
                "summary": summary,
                "evidence": evidence or [],
                "helper": helper,
            })

        _add_q(
            "structure",
            "Structure (REQUIRED_ORDER)",
            "pass" if present_sections >= len(REQUIRED_SECTIONS) else (
                "fail" if not ssot_parses else "unverified"
            ),
            f"{present_sections}/{len(REQUIRED_SECTIONS)} canonical sections present",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py (REQUIRED_ORDER)",
        )
        _add_q(
            "disk_validator",
            "Disk validator (size + parse)",
            "pass" if ssot_parses and ssot_path.is_file() and ssot_path.stat().st_size >= 4000 else "fail",
            (
                f"{ssot_path.stat().st_size}B parses={ssot_parses}"
                if ssot_path.is_file() else "ssot file not found"
            ),
            [_rel(ssot_path)] if ssot_path.is_file() else [],
            "workflow/ssot-gen/scripts/check_ssot_disk.sh",
        )
        _add_q(
            "downstream_readiness",
            "Downstream readiness (--strict-downstream)",
            "pass" if not downstream_blockers else "fail",
            f"{len(downstream_blockers)} blocker(s)" if downstream_blockers else "clean",
            [_rel(ip_dir / "req" / "ssot_downstream_blockers.json")] if downstream_doc else [],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py --strict-downstream",
        )
        _add_q(
            "legacy_detection",
            "Legacy top-level keys",
            "pass" if not legacy_keys else "unverified",
            "no legacy keys" if not legacy_keys else f"{len(legacy_keys)} found: " + ", ".join(legacy_keys[:5]),
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_legacy_interface_to_io_list",
        )
        _add_q(
            "tbd_count",
            "TBD / placeholder count",
            "pass" if tbd_count == 0 else "unverified",
            f"{tbd_count} TBD occurrences" if tbd_count else "0 TBD",
            [_rel(ssot_path)] if ssot_path.is_file() else [],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_has_tbd",
        )
        _add_q(
            "submodule_ownership",
            "Submodule ownership",
            "pass" if sub_modules and owned == len(sub_modules) else (
                "skip" if not sub_modules else "fail"
            ),
            f"{owned}/{len(sub_modules)} owned" if sub_modules else "no sub_modules",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_validate_submodule_ownership",
        )
        _add_q(
            "fm_refs_completeness",
            "Function-model refs on sub_modules",
            "pass" if sub_modules and with_fm_refs == len(sub_modules) else (
                "skip" if not sub_modules else "unverified"
            ),
            f"{with_fm_refs}/{len(sub_modules)} have function_model_refs" if sub_modules else "no sub_modules",
            [_rel(ssot_path)],
            "workflow/fl-model-gen/scripts/emit_equivalence_goals.py (B-2 advisory)",
        )

        # IO completeness — referenced names in expressions vs declared ports + input_map
        try:
            import ast as _ast
            referenced: set[str] = set()
            for tx in txs:
                for r in (tx.get("output_rules") or []):
                    if isinstance(r, dict):
                        for k in ("expr", "expression", "value"):
                            if k in r:
                                py = str(r.get(k) or "").replace("&&", " and ").replace("||", " or ")
                                try:
                                    for n in _ast.walk(_ast.parse(py, mode="eval")):
                                        if isinstance(n, _ast.Name): referenced.add(n.id)
                                except Exception: pass
            io = ssot_doc.get("io_list") if isinstance(ssot_doc.get("io_list"), dict) else {}
            declared_ports: set[str] = set()
            for grp in (io.get("interfaces") or []) + (io.get("clock_domains") or []) + (io.get("resets") or []):
                if isinstance(grp, dict):
                    for p in (grp.get("ports") or []):
                        if isinstance(p, dict):
                            n = str(p.get("name") or "").strip()
                            if n: declared_ports.add(n)
            helpers = {"and","or","not","True","False","None","gray_to_bin","bin_to_gray","popcount","parity","clog2","min","max","abs"}
            missing_io = sorted(n for n in referenced if n and n not in declared_ports and n not in input_map and n not in output_map and n not in helpers and not n.isdigit())
        except Exception:
            missing_io = []

        _add_q(
            "io_completeness",
            "IO completeness (rule names → input_map/ports)",
            "pass" if not missing_io else "fail",
            f"{len(missing_io)} unmapped names: {', '.join(missing_io[:5])}" if missing_io else f"{len(input_map)} mapped, 0 missing",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_ensure_rule_expr_input_map_completeness (C-1)",
        )

        # Sample condition DSL parseable
        try:
            sc_py = sample_condition.replace("&&", " and ").replace("||", " or ")
            sc_ok = bool(sample_condition.strip())
            if sc_ok:
                try:
                    import ast as _ast2
                    _ast2.parse(sc_py, mode="eval")
                except Exception:
                    sc_ok = False
        except Exception:
            sc_ok = False
        _add_q(
            "sample_condition",
            "rtl_contract.sample_condition DSL",
            "pass" if sc_ok else "fail",
            f"sample_condition={sample_condition!r}" if sample_condition else "empty",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_validate_sample_conditions (C-2)",
        )

        state_vars = (fm.get("state_variables") or []) if isinstance(fm.get("state_variables"), list) else []
        observable_state_count = 0
        observable_with_rule = 0
        for s in state_vars:
            if not isinstance(s, dict): continue
            name = str(s.get("name") or "").strip()
            if not name: continue
            for grp in (ssot_doc.get("io_list") or {}).get("interfaces") or []:
                ports = (grp.get("ports") or []) if isinstance(grp, dict) else []
                if any(isinstance(p, dict) and str(p.get("name") or "") == name and str(p.get("direction") or "") == "output" for p in ports):
                    observable_state_count += 1
                    has_rule = False
                    for tx in txs:
                        for r in (tx.get("output_rules") or []) + (tx.get("state_updates") or []):
                            if isinstance(r, dict) and (str(r.get("name") or "") == name or str(r.get("port") or "") == name):
                                has_rule = True; break
                        if has_rule: break
                    if has_rule:
                        observable_with_rule += 1
                    break
        _add_q(
            "state_observability",
            "Observable state variables have rules",
            "pass" if observable_state_count == 0 or observable_with_rule == observable_state_count else "unverified",
            f"{observable_with_rule}/{observable_state_count} observable state vars have rules" if observable_state_count else "no observable state vars",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_ensure_rule_expr_input_map_completeness (C-3)",
        )

        # Equivalence goals
        eg = _read_json(ip_dir / "verify" / "equivalence_goals.json")
        eg_total = eg_blocked = eg_unverified = None
        if isinstance(eg, dict):
            s = eg.get("summary") or {}
            eg_total = int(s.get("total", 0))
            eg_blocked = int(s.get("blocked", 0))
            eg_unverified = int(s.get("unverified", 0))
        _add_q(
            "equiv_goals",
            "Equivalence goals (FL↔RTL)",
            "skip" if eg is None else (
                "fail" if (eg_blocked or 0) > 0 else (
                    "unverified" if (eg_unverified or 0) > 0 else "pass"
                )
            ),
            f"total={eg_total} blocked={eg_blocked} unverified={eg_unverified}" if eg else "not yet generated",
            [_rel(ip_dir / "verify" / "equivalence_goals.json")] if eg else [],
            "workflow/fl-model-gen/scripts/emit_equivalence_goals.py",
        )

        # Connection contracts (production manifest)
        connection_issues = 0
        prov = _read_json(ip_dir / "rtl" / "rtl_authoring_provenance.json")
        if isinstance(prov, dict):
            connection_issues = int(prov.get("quality_issues", 0)) + int(prov.get("hierarchy_issues", 0))
        _add_q(
            "connection_contracts",
            "RTL manifest connection contracts",
            "skip" if not prov else ("pass" if connection_issues == 0 else "fail"),
            f"{connection_issues} hierarchy/quality issues" if prov else "not yet generated",
            [_rel(ip_dir / "rtl" / "rtl_authoring_provenance.json")] if prov else [],
            "workflow/rtl-gen/scripts/derive_rtl_todos.py",
        )

        # Coverage refs
        fcov = _read_json(ip_dir / "cov" / "fcov_plan.json")
        bins = (fcov.get("bins") or fcov.get("plan") or []) if isinstance(fcov, dict) else []
        _add_q(
            "coverage_refs",
            "Functional coverage plan exists",
            "skip" if not fcov else ("pass" if bins else "unverified"),
            f"{len(bins)} bins/plan entries" if fcov else "not yet generated",
            [_rel(ip_dir / "cov" / "fcov_plan.json")] if fcov else [],
            "workflow/fl-model-gen/scripts/emit_fl_model.py",
        )

        # Per-stage results
        stages: list[dict[str, Any]] = []

        def _add_s(stage: str, status: str, summary: str, evidence: list[str] = None,
                   scripts: list[str] = None):
            stages.append({
                "stage": stage,
                "status": status,
                "summary": summary,
                "evidence": evidence or [],
                "scripts": scripts or [],
                "last_modified": max((_stat_iso(PROJECT_ROOT / e) for e in (evidence or [])), default=""),
            })

        # ssot-gen
        ssot_gen_status = "pass" if ssot_parses and present_sections >= 30 and not downstream_blockers else (
            "skip" if not ssot_parses else "fail"
        )
        _add_s(
            "ssot-gen",
            ssot_gen_status,
            f"sections={present_sections}/{len(REQUIRED_SECTIONS)} downstream_blockers={len(downstream_blockers)}",
            [_rel(ssot_path)],
            ["workflow/ssot-gen/scripts/repair_ssot_schema.py", "workflow/ssot-gen/scripts/check_ssot_disk.sh"],
        )

        # fl-model-gen
        fl_check = _read_json(ip_dir / "model" / "fl_model_check.json")
        fl_passed = isinstance(fl_check, dict) and fl_check.get("passed")
        _add_s(
            "fl-model-gen",
            "skip" if not fl_check else ("pass" if fl_passed else "fail"),
            (f"checks={(fl_check.get('self_check') or {}).get('checks',0)} passed={fl_passed}" if fl_check else "not yet run"),
            [_rel(ip_dir / "model" / "fl_model_check.json"), _rel(ip_dir / "model" / "functional_model.py")] if fl_check else [],
            ["workflow/fl-model-gen/scripts/emit_fl_model.py"],
        )

        # cl-model-gen
        cl_check = _read_json(ip_dir / "model" / "cl_model_check.json")
        cl_passed = isinstance(cl_check, dict) and cl_check.get("passed")
        _add_s(
            "cl-model-gen",
            "skip" if not cl_check else ("pass" if cl_passed else "fail"),
            (f"passed={cl_passed}" if cl_check else "not yet run"),
            [_rel(ip_dir / "model" / "cl_model_check.json")] if cl_check else [],
            ["workflow/cl-model-gen/scripts/emit_cl_model.py"],
        )

        # equiv-goals
        _add_s(
            "equiv-goals",
            "skip" if eg is None else (
                "fail" if (eg_blocked or 0) > 0 else (
                    "unverified" if (eg_unverified or 0) > 0 else "pass"
                )
            ),
            f"total={eg_total} blocked={eg_blocked} unverified={eg_unverified}" if eg else "not yet run",
            [_rel(ip_dir / "verify" / "equivalence_goals.json")] if eg else [],
            ["workflow/fl-model-gen/scripts/emit_equivalence_goals.py"],
        )

        # rtl-gen
        rtl_blocked_doc = _read_json(ip_dir / "rtl" / "rtl_blocked.json")
        rtl_compile = _read_json(ip_dir / "rtl" / "rtl_compile.json")
        dut_lint = _read_json(ip_dir / "lint" / "dut_lint.json")
        compile_errors = int((rtl_compile or {}).get("errors", 0))
        lint_errors = int((dut_lint or {}).get("errors", 0))
        lint_warnings = int((dut_lint or {}).get("warnings", 0))
        if rtl_blocked_doc:
            rtl_status = "blocked"
            rtl_summary = f"preflight blocked: {len((rtl_blocked_doc or {}).get('questions') or [])} questions"
        elif rtl_compile is None:
            rtl_status = "skip"
            rtl_summary = "not yet run"
        elif compile_errors == 0 and lint_errors == 0:
            rtl_status = "pass"
            rtl_summary = f"compile_errors=0 lint_errors=0 warnings={lint_warnings}"
        else:
            rtl_status = "fail"
            rtl_summary = f"compile_errors={compile_errors} lint_errors={lint_errors} warnings={lint_warnings}"
        _add_s(
            "rtl-gen",
            rtl_status,
            rtl_summary,
            [p for p in [
                _rel(ip_dir / "rtl" / "rtl_compile.json") if rtl_compile else "",
                _rel(ip_dir / "lint" / "dut_lint.json") if dut_lint else "",
                _rel(ip_dir / "rtl" / "rtl_blocked.json") if rtl_blocked_doc else "",
                _rel(ip_dir / "rtl" / "rtl_authoring_provenance.json") if prov else "",
            ] if p],
            [
                "workflow/rtl-gen/scripts/ssot_to_rtl.py",
                "workflow/rtl-gen/scripts/derive_rtl_todos.py",
                "workflow/rtl-gen/scripts/rtl_compile_report.py",
                "workflow/lint/scripts/dut_lint_report.py",
            ],
        )

        # tb-gen
        tb_dir = ip_dir / "tb"
        tb_artifacts = sorted(p.name for p in tb_dir.glob("**/*.py")) if tb_dir.is_dir() else []
        _add_s(
            "tb-gen",
            "skip" if not tb_artifacts else "pass",
            f"{len(tb_artifacts)} TB python files" if tb_artifacts else "not yet run",
            [_rel(tb_dir)] if tb_artifacts else [],
            ["workflow/tb-gen/scripts/emit_tb.py", "workflow/tb-gen/runtime/equivalence_scoreboard.py"],
        )

        # sim
        sim_compare = _read_json(ip_dir / "sim" / "fl_rtl_compare.json")
        sim_status = "skip"
        sim_summary = "not yet run"
        if sim_compare:
            mm = int(sim_compare.get("mismatch_count", sim_compare.get("mismatches", 0)))
            tot = int(sim_compare.get("total_rows", sim_compare.get("total", 0)))
            sim_status = "pass" if mm == 0 else "fail"
            sim_summary = f"total={tot} mismatch={mm}"
        _add_s(
            "sim", sim_status, sim_summary,
            [_rel(ip_dir / "sim" / "fl_rtl_compare.json")] if sim_compare else [],
            ["workflow/sim_debug/scripts/compare_fl_rtl_results.py"],
        )

        # sim-debug
        mc = _read_json(ip_dir / "sim" / "mismatch_classification.json")
        if mc:
            items = mc.get("classifications") or []
            owners: dict[str, int] = {}
            for it in items:
                if isinstance(it, dict):
                    o = str(it.get("owner", "?"))
                    owners[o] = owners.get(o, 0) + 1
            sd_summary = " ".join(f"{k}:{v}" for k, v in sorted(owners.items())) if owners else "no mismatches"
            _add_s("sim-debug", "pass" if items else "skip", sd_summary,
                   [_rel(ip_dir / "sim" / "mismatch_classification.json")],
                   ["workflow/sim_debug/scripts/compare_fl_rtl_results.py"])
        else:
            _add_s("sim-debug", "skip", "not yet run", [], [])

        # lint
        if dut_lint:
            _add_s("lint", "pass" if lint_errors == 0 else "fail",
                   f"errors={lint_errors} warnings={lint_warnings}",
                   [_rel(ip_dir / "lint" / "dut_lint.json")],
                   ["workflow/lint/scripts/dut_lint_report.py"])
        else:
            _add_s("lint", "skip", "not yet run", [], [])

        # coverage
        cov = _read_json(ip_dir / "cov" / "coverage.json")
        ga = _read_json(ip_dir / "sim" / "fl_rtl_goal_audit.json")
        cov_summary = "not yet run"
        cov_status = "skip"
        if ga:
            bins_doc = ga.get("bins") if isinstance(ga.get("bins"), dict) else {}
            hit = int(bins_doc.get("hit", bins_doc.get("hit_count", 0)) or 0)
            tot = int(bins_doc.get("total", 0) or 0)
            cov_status = "pass" if (tot > 0 and hit == tot) else ("fail" if tot else "skip")
            cov_summary = f"bins_hit={hit}/{tot}"
        _add_s("coverage", cov_status, cov_summary,
               [_rel(ip_dir / "sim" / "fl_rtl_goal_audit.json")] if ga else [],
               ["workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py"])

        # goal-audit
        ga_audit = _read_json(ip_dir / "verify" / "equivalence_goals_audit.json")
        ga_summary = "not yet run"
        ga_status = "skip"
        if ga_audit:
            ga_status = str(ga_audit.get("status", "unknown"))
            if ga_status not in ("pass", "fail", "blocked"): ga_status = "unverified"
            s = ga_audit.get("summary") or {}
            ga_summary = ", ".join(f"{k}={v}" for k, v in list(s.items())[:6]) if s else "audit produced"
        _add_s("goal-audit", ga_status, ga_summary,
               [_rel(ip_dir / "verify" / "equivalence_goals_audit.json")] if ga_audit else [],
               ["workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py"])

        passed_q = sum(1 for q in quality if q["status"] == "pass")
        passed_s = sum(1 for s in stages if s["status"] == "pass")
        return JSONResponse({
            "ip": ip,
            "ssot_path": _rel(ssot_path),
            "ssot_exists": ssot_path.is_file(),
            "ssot_parses": ssot_parses,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ssot_quality": {
                "items": quality,
                "passed": passed_q,
                "total": len(quality),
            },
            "stages": {
                "items": stages,
                "passed": passed_s,
                "total": len(stages),
            },
        })

