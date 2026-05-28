"""SoC dataflow API — extracted from src/atlas_ui.py.

Hosts GET /api/soc — the cluster/module/bus dataflow renderer (~2683 lines,
plus a 393-line `_build_module` helper nested inside). It was previously
the biggest route handler in atlas_ui.py's create_app() closure.

Factory pattern: register_soc_routes(app, **deps) takes the 6 closure
captures from the original nesting (SKIP_DIRS, _load_ssot_state,
_soc_build_lock, _soc_cache_get, _soc_cache_set, _valid_ip_name) as
keyword arguments whose names mirror the original locals — so the
api_soc body needs ZERO textual modification. The factory installs
api_soc on `app` via the same @app.get('/api/soc') decorator preserved
verbatim from atlas_ui.

Phase 14 of refactor/atlas-modular (backend extraction).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse

# api_soc body's `_rtl_manifest_progress` integration. Mirrors the
# atlas_ui.py:803-809 try/except chain so the body's bare-name lookup
# resolves against this module's globals. Without this the
# `_shared_rtl_manifest_progress` reference in api_soc raised NameError
# at request time — extraction debt caught by live web verification.
try:
    from .workflow_stage_engine import _rtl_manifest_progress as _shared_rtl_manifest_progress
except Exception:
    try:
        from workflow_stage_engine import _rtl_manifest_progress as _shared_rtl_manifest_progress  # type: ignore
    except Exception:
        _shared_rtl_manifest_progress = None  # type: ignore


def register_soc_routes(
    app,
    *,
    SKIP_DIRS,
    _load_ssot_state,
    _soc_build_lock,
    _soc_cache_get,
    _soc_cache_set,
    _valid_ip_name,
    PROJECT_ROOT,
    SOURCE_ROOT,
) -> None:
    """Register GET /api/soc on `app` using the supplied dep-injected helpers.

    Every kwarg is named identically to the local it replaces in the original
    create_app() closure so the inlined route body needs no textual edits.
    """
    @app.get("/api/soc")
    def api_soc(scope: str = "", ip: str = ""):
        """Build a SoC-Architect-friendly view of the project's IPs.

        Two-tier source-of-truth model:
          1. SoC-level SSOT  — `<project_root>/soc.ssot.yaml`
             Owned by the Architect supervisor. Lists clusters, IP
             instances (with overrides + addresses), connections, and
             generators. When present, drives the architect view.
          2. Per-IP leaf SSOT — `<ip>/yaml/<ip>.ssot.yaml`
             Each instance points to its leaf SSOT for parameters,
             busInterfaces, model.ports → clocks/resets, memoryMap.

        When the SoC SSOT is missing we fall back to the directory walk
        (every `*.ssot.yaml` under the project becomes a module under a
        single `ips` cluster) so existing projects keep working without
        an explicit SoC file.

        Status (ssot/rtl/sim) is derived from filesystem presence:
          ssot = ok  if yaml file parses
          rtl  = ok  if <ip>/rtl/*.sv exists, partial if dir exists empty,
                     pending otherwise
          sim  = ok  if <ip>/sim/ has any *.log or *.vcd, pending otherwise
        Used by the Atlas Architect screen to replace the mock SOC.
        """
        try:
            try: import yaml as _yaml  # type: ignore
            except Exception: _yaml = None

            def _kind_for(name: str) -> str:
                """Infer module kind from its name. Used as a fallback
                when no cluster.role is available (dir-walk mode) or
                when the cluster lists a generic role. Heuristic patterns
                broaden to catch real-world IP names: cortexa15, riscv,
                cci550, ccn508, nic400, etc."""
                n = (name or "").lower()
                if any(s in n for s in ("cpu", "core", "rv", "cortex", "riscv",
                                         "arm", "neoverse", "amba_a", "hart")): return "cpu"
                if any(s in n for s in ("mem", "ram", "ddr", "cache", "sram",
                                         "rom", "flash", "ocm")): return "mem"
                if any(s in n for s in ("noc", "bus", "axi", "apb", "ahb", "xbar",
                                         "cci", "ccn", "nic", "nip", "interconnect",
                                         "crossbar", "smmu", "iommu")): return "bus"
                if any(s in n for s in ("phy", "ana", "pll", "ldo", "vco",
                                         "adc", "dac", "afe", "rf")): return "analog"
                return "periph"

            # Cluster role string from soc.ssot.yaml → module kind. The
            # role is more authoritative than the name heuristic; we let
            # it win when present so cortexa15_0 under a CPU cluster is
            # always classified `cpu` regardless of name.
            _ROLE_TO_KIND = {
                "CPU": "cpu", "MEM": "mem", "BUS": "bus",
                "PERIPH": "periph", "ANALOG": "analog",
                "INTERCONNECT": "bus", "FABRIC": "bus", "NOC": "bus",
                "PERIPHERAL": "periph", "MISC": "periph",
            }
            def _kind_from_role(role):
                if not isinstance(role, str): return None
                return _ROLE_TO_KIND.get(role.strip().upper())

            def _soc_rel(path: Path) -> str:
                try:
                    resolved = Path(path).resolve()
                except Exception:
                    return str(path)
                for base in (PROJECT_ROOT, SOURCE_ROOT):
                    try:
                        return resolved.relative_to(base.resolve()).as_posix()
                    except Exception:
                        continue
                return resolved.as_posix()

            # YAML hex literals like `0x8000_0000` are parsed by PyYAML
            # to a Python int. Re-format as a hex string with 4-digit
            # underscore groups so the architect UI shows the canonical
            # SoC notation (`0x8000_0000`, `0x4000_2000`) instead of a
            # raw decimal (`2147483648`).
            def _hex_addr(v):
                if v is None: return ""
                if isinstance(v, int):
                    h = f"{v:x}"
                    # Zero-pad to at least 8 hex digits (32-bit address
                    # convention) so 0x0800_0000 doesn't collapse to
                    # 0x800_0000 after grouping. Larger values use the
                    # next multiple of 4.
                    target = max(8, ((len(h) - 1) // 4 + 1) * 4)
                    h = h.zfill(target)
                    if len(h) > 4:
                        rev = h[::-1]
                        groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
                        h = "_".join(groups)[::-1]
                    return f"0x{h}"
                # Already a string (might or might not be hex-prefixed).
                s = str(v).strip()
                if s.startswith("0x") or s.startswith("0X"): return s
                # Try parse as int — covers decimal-string cases.
                try:
                    return _hex_addr(int(s))
                except ValueError:
                    return s

            def _has_live_content(value: Any) -> bool:
                if value is None:
                    return False
                if isinstance(value, str):
                    text = value.strip()
                    return bool(text) and text.upper() not in {"TBD", "TODO", "NONE", "NULL"}
                if isinstance(value, (list, tuple, set)):
                    return any(_has_live_content(v) for v in value)
                if isinstance(value, dict):
                    return any(_has_live_content(v) for v in value.values())
                return True

            def _contains_tbd(value: Any) -> bool:
                if isinstance(value, str):
                    return bool(re.search(r"\b(TBD|TODO|FIXME|HACK)\b", value, re.I))
                if isinstance(value, list):
                    return any(_contains_tbd(v) for v in value)
                if isinstance(value, dict):
                    return any(_contains_tbd(v) for v in value.values())
                return False

            _SSOT_SECTIONS = [
                ("top_module", "top module"),
                ("sub_modules", "sub modules"),
                ("parameters", "parameters"),
                ("io_list", "I/O"),
                ("features", "features"),
                ("dataflow", "dataflow"),
                ("function_model", "function model"),
                ("cycle_model", "cycle model"),
                ("clock_reset_domains", "clock/reset"),
                ("cdc_requirements", "CDC"),
                ("rdc_requirements", "RDC"),
                ("registers", "registers"),
                ("memory", "memory"),
                ("interrupts", "interrupts"),
                ("fsm", "FSM"),
                ("timing", "timing"),
                ("power", "power"),
                ("security", "security"),
                ("error_handling", "errors"),
                ("debug_observability", "debug"),
                ("integration", "integration"),
                ("dft", "DFT"),
                ("synthesis", "synthesis"),
                ("coding_rules", "coding rules"),
                ("reuse_modules", "reuse modules"),
                ("custom", "custom"),
                ("dir_structure", "dir structure"),
                ("filelist", "filelist"),
                ("test_requirements", "DV plan"),
                ("quality_gates", "quality gates"),
                ("traceability", "traceability"),
                ("workflow_todos", "workflow TODOs"),
                ("generation_flow", "generation flow"),
            ]
            _SSOT_SECTION_ALIASES = {
                "clock_reset_domains": ["clock_reset_domains", "reset_behavior", "clocks", "resets"],
                "function_model": ["function_model", "functional_model", "behavior_model", "reference_model"],
                "cycle_model": ["cycle_model", "cycle_accurate_model", "timing_model", "pipeline_model"],
                "debug_observability": ["debug_observability", "debug", "observability", "trace_debug"],
                "dft": ["dft", "dfd", "testability"],
                "synthesis": ["synthesis", "implementation_constraints", "physical_constraints"],
                "coding_rules": ["coding_rules", "constraints"],
                "test_requirements": ["test_requirements", "verification"],
                "quality_gates": ["quality_gates", "acceptance_criteria", "pass_criteria", "signoff_criteria"],
                "workflow_todos": ["workflow_todos", "next_step_todos"],
            }

            def _pct(done: int, total: int) -> int:
                return int(round((100.0 * done / total))) if total else 0

            _SSOT_EMPTY_IS_DECLARED = {
                "reuse_modules",
            }

            def _is_non_empty_mapping(value: Any) -> bool:
                return isinstance(value, dict) and bool(value)

            def _is_non_empty_list(value: Any) -> bool:
                return isinstance(value, list) and bool(value)

            def _has_required_fields(value: Any, fields: list[str]) -> bool:
                if not isinstance(value, dict):
                    return False
                for field in fields:
                    item = value.get(field)
                    if item is None or item == "" or item == [] or item == {}:
                        return False
                return True

            def _scenario_complete(item: Any) -> bool:
                return _has_required_fields(item, ["id", "name", "stimulus", "expected", "checker", "coverage"])

            def _gate_complete(item: Any) -> bool:
                return _has_required_fields(item, ["pass", "evidence"])

            def _ssot_section_complete(key: str, value: Any, present: bool) -> bool:
                if not present or _contains_tbd(value):
                    return False
                if key in _SSOT_EMPTY_IS_DECLARED and isinstance(value, (list, tuple, set, dict)):
                    return True
                if key == "function_model":
                    if not isinstance(value, dict):
                        return False
                    state_variables = value.get("state_variables") if isinstance(value.get("state_variables"), list) else []
                    transactions = value.get("transactions") if isinstance(value.get("transactions"), list) else []
                    invariants = value.get("invariants") if isinstance(value.get("invariants"), list) else []
                    return (
                        _has_required_fields(value, ["state_variables", "transactions", "invariants"])
                        and _is_non_empty_list(state_variables)
                        and _is_non_empty_list(transactions)
                        and _is_non_empty_list(invariants)
                        and all(
                            _has_required_fields(tx, ["id", "name", "preconditions", "outputs"])
                            and bool(tx.get("side_effects") or tx.get("error_cases"))
                            for tx in transactions
                        )
                    )
                if key == "cycle_model":
                    return (
                        _has_required_fields(value, ["clock", "reset", "latency", "handshake_rules", "pipeline", "ordering"])
                        and _is_non_empty_list(value.get("handshake_rules"))
                        and _is_non_empty_list(value.get("pipeline"))
                        and _is_non_empty_list(value.get("ordering"))
                    )
                if key == "timing":
                    return _has_required_fields(value, ["target_clocks", "latency_budget"]) and _is_non_empty_list(value.get("target_clocks"))
                if key == "power":
                    return _has_required_fields(value, ["domains", "power_states"]) and _is_non_empty_list(value.get("domains"))
                if key == "security":
                    return (
                        _has_required_fields(value, ["classification", "assets", "threat_model"])
                        and _is_non_empty_list(value.get("assets"))
                        and _is_non_empty_list(value.get("threat_model"))
                    )
                if key == "error_handling":
                    return _has_required_fields(value, ["error_sources", "propagation", "recovery"]) and _is_non_empty_list(value.get("error_sources"))
                if key == "debug_observability":
                    return _has_required_fields(value, ["waveform_must_probe", "trace_events"]) and _is_non_empty_list(value.get("waveform_must_probe"))
                if key == "integration":
                    return _has_required_fields(value, ["bus_attachment", "dependencies"])
                if key == "dft":
                    return _has_required_fields(value, ["scan_required", "controllability", "observability"])
                if key == "synthesis":
                    return _has_required_fields(value, ["dialect", "constraints", "required_outputs"])
                if key == "test_requirements":
                    scenarios = value.get("scenarios") if isinstance(value, dict) else None
                    return (
                        _has_required_fields(value, ["scenarios", "scoreboard_checks", "coverage_goals"])
                        and _is_non_empty_list(scenarios)
                        and all(_scenario_complete(item) for item in scenarios)
                    )
                if key == "quality_gates":
                    if not _is_non_empty_mapping(value):
                        return False
                    return all(_gate_complete(value.get(gate)) for gate in ["ssot", "rtl", "dv", "coverage", "eda", "signoff"])
                if key == "traceability":
                    return _has_required_fields(value, ["yaml_to_output"]) and _is_non_empty_list(value.get("yaml_to_output"))
                return _has_live_content(value)

            def _count_list(value: Any) -> int:
                return len(value) if isinstance(value, list) else 0

            def _ssot_metrics(doc: dict) -> dict:
                io_list = doc.get("io_list") if isinstance(doc, dict) else {}
                interfaces = io_list.get("interfaces") if isinstance(io_list, dict) else []
                ports = 0
                if isinstance(interfaces, list):
                    for iface in interfaces:
                        if isinstance(iface, dict) and isinstance(iface.get("ports"), list):
                            ports += len(iface["ports"])
                registers = doc.get("registers") if isinstance(doc, dict) else {}
                register_list = registers.get("register_list") if isinstance(registers, dict) else []
                memory = doc.get("memory") if isinstance(doc, dict) else {}
                memory_instances = memory.get("instances") if isinstance(memory, dict) else []
                fsm = doc.get("fsm") if isinstance(doc, dict) else {}
                fsm_states = 0
                fsm_transitions = 0
                if isinstance(fsm, dict):
                    for item in fsm.values():
                        if isinstance(item, dict):
                            fsm_states += _count_list(item.get("states"))
                            fsm_transitions += _count_list(item.get("transitions"))
                tr = doc.get("test_requirements") if isinstance(doc, dict) else {}
                scenarios = tr.get("scenarios") if isinstance(tr, dict) else []
                coverage_goals = tr.get("coverage_goals") if isinstance(tr, dict) else {}
                function_model = doc.get("function_model") if isinstance(doc, dict) else {}
                fm_transactions = function_model.get("transactions") if isinstance(function_model, dict) else []
                fm_state = function_model.get("state_variables") if isinstance(function_model, dict) else []
                cycle_model = doc.get("cycle_model") if isinstance(doc, dict) else {}
                cm_handshakes = cycle_model.get("handshake_rules") if isinstance(cycle_model, dict) else []
                cm_pipeline = cycle_model.get("pipeline") if isinstance(cycle_model, dict) else []
                quality_gates = doc.get("quality_gates") if isinstance(doc, dict) else {}
                timing = doc.get("timing") if isinstance(doc, dict) else {}
                security = doc.get("security") if isinstance(doc, dict) else {}
                error_handling = doc.get("error_handling") if isinstance(doc, dict) else {}
                submods = doc.get("sub_modules") if isinstance(doc, dict) else []
                return {
                    "submodules": _count_list(submods),
                    "parameters": _count_list(doc.get("parameters") if isinstance(doc, dict) else []),
                    "interfaces": _count_list(interfaces),
                    "ports": ports,
                    "registers": _count_list(register_list),
                    "memories": _count_list(memory_instances),
                    "fsm_states": fsm_states,
                    "fsm_transitions": fsm_transitions,
                    "dv_scenarios": _count_list(scenarios),
                    "function_transactions": _count_list(fm_transactions),
                    "function_state_variables": _count_list(fm_state),
                    "cycle_handshake_rules": _count_list(cm_handshakes),
                    "cycle_pipeline_stages": _count_list(cm_pipeline),
                    "timing_clocks": _count_list(timing.get("target_clocks") if isinstance(timing, dict) else []),
                    "security_assets": _count_list(security.get("assets") if isinstance(security, dict) else []),
                    "error_sources": _count_list(error_handling.get("error_sources") if isinstance(error_handling, dict) else []),
                    "scoreboard_checks": tr.get("scoreboard_checks") if isinstance(tr, dict) else None,
                    "coverage_goals": len(coverage_goals) if isinstance(coverage_goals, dict) else 0,
                    "quality_gates": len(quality_gates) if isinstance(quality_gates, dict) else 0,
                }

            def _ssot_progress(doc: dict) -> dict:
                sections = []
                canonical_keys = {k for k, _ in _SSOT_SECTIONS}
                section_defs = list(_SSOT_SECTIONS)
                if isinstance(doc, dict) and doc:
                    known = set(canonical_keys)
                    known.update(a for aliases in _SSOT_SECTION_ALIASES.values() for a in aliases)
                    for key in doc.keys():
                        if key not in known:
                            section_defs.append((str(key), str(key).replace("_", " ")))
                for key, label in section_defs:
                    keys = _SSOT_SECTION_ALIASES.get(key, [key])
                    actual_key = next((k for k in keys if isinstance(doc, dict) and k in doc), key)
                    val = doc.get(actual_key) if isinstance(doc, dict) else None
                    present = actual_key in doc if isinstance(doc, dict) else False
                    complete = _ssot_section_complete(key, val, present)
                    status = "approved" if complete else ("incomplete" if present else "missing")
                    sections.append({
                        "key": key,
                        "actual_key": actual_key if present else "",
                        "label": label,
                        "status": status,
                        "canonical": key in canonical_keys,
                    })
                approved = sum(1 for s in sections if s.get("canonical") and s["status"] == "approved")
                total = sum(1 for s in sections if s.get("canonical"))
                return {
                    "approved": approved,
                    "total": total,
                    "pct": _pct(approved, total),
                    "sections": sections,
                    "metrics": _ssot_metrics(doc if isinstance(doc, dict) else {}),
                }

            def _extract_expected_rtl(doc: dict) -> list[dict[str, str]]:
                expected: list[dict[str, str]] = []
                seen: set[str] = set()
                subs = doc.get("sub_modules") if isinstance(doc, dict) else []
                if isinstance(subs, list):
                    for idx, item in enumerate(subs):
                        if not isinstance(item, dict):
                            continue
                        name = str(item.get("name") or f"module_{idx}")
                        file_name = str(item.get("file") or "").strip()
                        if file_name and file_name not in seen:
                            expected.append({"name": name, "file": file_name})
                            seen.add(file_name)
                fl = doc.get("filelist") if isinstance(doc, dict) else {}
                rtl_list = fl.get("rtl") if isinstance(fl, dict) else []
                if isinstance(rtl_list, list):
                    for raw in rtl_list:
                        file_name = str(raw or "").strip()
                        if not file_name or file_name in seen:
                            continue
                        expected.append({"name": Path(file_name).stem, "file": file_name})
                        seen.add(file_name)
                return expected

            def _resolve_ip_file(ip_dir: Path, rel: str) -> Path:
                p = Path(rel)
                if p.is_absolute():
                    return p
                cand = ip_dir / rel
                if cand.is_file():
                    return cand
                return PROJECT_ROOT / rel

            def _filelist_entries(ip_dir: Path) -> tuple[list[str], Path | None]:
                f = ip_dir / "list" / f"{ip_dir.name}.f"
                if not f.is_file():
                    return [], None
                entries: list[str] = []
                try:
                    for raw in f.read_text(encoding="utf-8", errors="replace").splitlines():
                        line = raw.split("//", 1)[0].strip()
                        if line and line.endswith((".v", ".sv", ".vh", ".svh")):
                            entries.append(line)
                except OSError:
                    pass
                return entries, f

            def _rtl_progress(ip_dir: Path, doc: dict) -> dict:
                if _shared_rtl_manifest_progress is not None:
                    try:
                        return _shared_rtl_manifest_progress(ip_dir, doc if isinstance(doc, dict) else {})
                    except Exception:
                        pass
                blocked_path = ip_dir / "rtl" / "rtl_blocked.json"
                blocked_doc: dict[str, Any] = {}
                if blocked_path.is_file():
                    try:
                        blocked_doc = json.loads(blocked_path.read_text(encoding="utf-8"))
                    except Exception:
                        blocked_doc = {
                            "status": "blocked",
                            "reason": "rtl_blocked.json is present but could not be parsed",
                        }
                entries, fpath = _filelist_entries(ip_dir)
                entry_set = set(entries)
                top_doc = doc.get("top_module") if isinstance(doc, dict) else {}
                top_name = ""
                if isinstance(top_doc, dict):
                    top_name = str(top_doc.get("name") or "").strip()
                if not top_name:
                    top_name = ip_dir.name
                listed_text = ""
                listed_sources: list[Path] = []
                for ent in entries:
                    src = _resolve_ip_file(ip_dir, ent)
                    if src.is_file():
                        listed_sources.append(src)
                        try:
                            listed_text += "\n" + src.read_text(encoding="utf-8", errors="replace")[:200000]
                        except OSError:
                            pass
                modules = []
                expected = _extract_expected_rtl(doc)
                if not expected:
                    rtl_dir = ip_dir / "rtl"
                    expected = [
                        {"name": p.stem, "file": p.relative_to(ip_dir).as_posix()}
                        for p in sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")))
                    ] if rtl_dir.is_dir() else []
                for item in expected:
                    rel = item["file"]
                    path = _resolve_ip_file(ip_dir, rel)
                    resolved_rel = rel
                    manifest_mismatch = False
                    # SSOTs often describe the integration wrapper as
                    # `<ip>_top.sv` while the real top module is `<ip>`.
                    # Verilator's DECLFILENAME rule requires the file stem
                    # to match the module name, so accept `rtl/<top>.sv`
                    # when the canonical filelist has already been repaired.
                    if (
                        not path.is_file()
                        and top_name
                        and item.get("name") in {f"{top_name}_top", "top", "wrapper"}
                    ):
                        alias_rel = f"rtl/{top_name}.sv"
                        alias_path = _resolve_ip_file(ip_dir, alias_rel)
                        if alias_rel in entry_set and alias_path.is_file():
                            path = alias_path
                            resolved_rel = alias_rel
                            manifest_mismatch = True
                    exists = path.is_file()
                    size = path.stat().st_size if exists else 0
                    text = ""
                    if exists:
                        try:
                            text = path.read_text(encoding="utf-8", errors="replace")[:200000]
                        except OSError:
                            text = ""
                    scaffold_only = bool(
                        re.search(r"Auto-generated manifest submodule", text, re.I)
                        or re.search(r"\balive_q\b", text)
                        or re.search(r"\bheartbeat_q\b", text)
                    )
                    placeholder = bool(re.search(r"\b(TBD|TODO:|FIXME|HACK)\b", text, re.I)) or scaffold_only
                    listed = rel in entry_set or resolved_rel in entry_set
                    if exists:
                        try:
                            listed = listed or _soc_rel(path) in entry_set
                        except Exception:
                            pass
                    include_header = False
                    if exists and not listed and path.suffix in {".sv", ".svh", ".vh"}:
                        include_name = path.name
                        include_header = (
                            bool(re.search(rf'`include\s+"{re.escape(include_name)}"', listed_text))
                            or path.stem.endswith("_pkg")
                            or "include header" in text[:2000].lower()
                        )
                    approved = exists and size >= 200 and (listed or include_header) and not placeholder
                    modules.append({
                        "name": item["name"],
                        "file": rel,
                        "resolved_file": resolved_rel,
                        "manifest_mismatch": manifest_mismatch or (resolved_rel != rel),
                        "status": "approved" if approved else ("partial" if exists else "missing"),
                        "exists": exists,
                        "listed": listed,
                        "include_header": include_header,
                        "bytes": size,
                        "placeholder": placeholder,
                        "scaffold_only": scaffold_only,
                    })
                approved = sum(1 for m in modules if m["status"] == "approved")
                mismatches = [m for m in modules if m.get("manifest_mismatch")]
                return {
                    "approved": approved,
                    "total": len(modules),
                    "pct": _pct(approved, len(modules)),
                    "filelist": _soc_rel(fpath) if fpath else "",
                    "manifest_mismatches": len(mismatches),
                    "manifest_mismatch_details": mismatches,
                    "blocked": bool(blocked_doc),
                    "blocker": str(blocked_doc.get("reason") or "") if blocked_doc else "",
                    "blocker_source": _soc_rel(blocked_path) if blocked_doc else "",
                    "questions": blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else [],
                    "next_action": str(blocked_doc.get("next_action") or "") if blocked_doc else "",
                    "modules": modules,
                }

            def _compile_progress(ip_dir: Path) -> dict:
                report_path = ip_dir / "rtl" / "rtl_compile.json"
                if not report_path.is_file():
                    return {
                        "status": "unknown",
                        "errors": 0,
                        "diagnostics": 0,
                        "style_violations": 0,
                        "source": "",
                        "tool": "",
                        "command": "",
                        "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json",
                    }
                try:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                except Exception:
                    return {
                        "status": "fail",
                        "errors": 1,
                        "diagnostics": 0,
                        "style_violations": 0,
                        "source": _soc_rel(report_path),
                        "tool": "",
                        "command": "",
                        "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json",
                    }
                if report.get("dut_only") is not True or str(report.get("type") or "") != "rtl_compile":
                    status = "fail"
                elif report.get("passed") is True:
                    status = "pass"
                else:
                    status = "fail"
                return {
                    "status": status,
                    "errors": int(report.get("errors") or 0),
                    "diagnostics": int(report.get("diagnostics") or report.get("warnings") or 0),
                    "style_violations": int(report.get("style_violations") or 0),
                    "style_violation_details": report.get("style_violation_details") or [],
                    "returncode": int(report.get("returncode") or 0),
                    "source": _soc_rel(report_path),
                    "tool": str(report.get("tool") or ""),
                    "command": str(report.get("command") or ""),
                    "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json; warnings, Icarus sorry diagnostics, and procedural parameterized part-selects are blockers",
                }

            def _waived_warning_kinds(waivers: list[str]) -> set[str]:
                kinds: set[str] = set()
                for raw in waivers:
                    for token in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", str(raw).upper()):
                        kinds.add(token)
                return kinds

            def _count_log_diagnostics(text: str, waivers: list[str] | None = None) -> dict:
                summary = re.search(
                    r"%Error:\s+Exiting due to\s+(\d+)\s+error\(s\),\s+(\d+)\s+warning\(s\)",
                    text,
                    re.I,
                )
                if summary:
                    return {
                        "errors": int(summary.group(1)),
                        "warnings": int(summary.group(2)),
                        "waived_warnings": 0,
                    }
                waived = _waived_warning_kinds(waivers or [])
                lines = text.splitlines()
                error_re = re.compile(r"(%ERROR\b|(^|\s)(ERROR|FATAL)(:|-)|\b\d+\s+ERROR\(S\))", re.I)
                errors = 0
                warnings = 0
                waived_warnings = 0
                for line in lines:
                    line_u = line.upper()
                    if re.search(r"%ERROR:\s+EXITING DUE TO \d+ WARNING", line_u):
                        continue
                    warning_kind = ""
                    m = re.search(r"%WARNING-([A-Z0-9_]+)", line_u)
                    if m:
                        warning_kind = m.group(1)
                    is_waived_warning = bool(warning_kind and warning_kind in waived)
                    is_warning_line = bool(
                        warning_kind
                        or re.search(r":\s*warning:", line, re.I)
                        or re.search(r"\bsorry:", line, re.I)
                    )
                    if is_warning_line and not error_re.search(line):
                        if is_waived_warning:
                            waived_warnings += 1
                        else:
                            warnings += 1
                    elif error_re.search(line):
                        errors += 1
                return {"errors": errors, "warnings": warnings, "waived_warnings": waived_warnings}

            def _lint_progress(ip_dir: Path, doc: dict) -> dict:
                lint_dir = ip_dir / "lint"
                latest: Path | None = None
                latest_mtime = -1.0
                diag = {"errors": 0, "warnings": 0, "waived_warnings": 0, "suppression_violations": 0}
                source_kind = ""
                command = ""
                tool = ""
                coding_rules = doc.get("coding_rules") if isinstance(doc, dict) else {}
                waivers = []
                if isinstance(coding_rules, dict):
                    raw_waivers = coding_rules.get("lint_waivers") or coding_rules.get("waivers") or []
                    if isinstance(raw_waivers, list):
                        waivers = [str(w) for w in raw_waivers]

                def _canonical_report_ok(report: dict) -> bool:
                    if not isinstance(report, dict):
                        return False
                    if report.get("dut_only") is not True:
                        return False
                    scope = str(report.get("scope") or report.get("type") or "").lower()
                    if scope not in {"dut", "rtl", "dut_lint", "rtl_lint"}:
                        return False
                    cmd = str(report.get("command") or "").lower()
                    if "cocotb" in cmd or "pytest" in cmd or "vvp" in cmd:
                        return False
                    return any(tok in cmd for tok in ("verilator", "pyslang", "iverilog", "slang"))

                def _reject_sim_log(text_l: str, pth: Path) -> bool:
                    parts_l = {part.lower() for part in pth.parts}
                    if {"tb", "cocotb", "sim", "sim_build"} & parts_l:
                        return True
                    sim_markers = (
                        "cocotb", "pytest", "results.xml", "module not found",
                        "vvp ", "make sim", "sim_build", "test_runner.py",
                    )
                    return any(marker in text_l for marker in sim_markers)

                report_candidates: list[Path] = []
                if lint_dir.is_dir():
                    report_candidates.extend(lint_dir.rglob("dut_lint.json"))
                    report_candidates.extend(lint_dir.rglob("rtl_lint.json"))
                    report_candidates.extend(lint_dir.rglob("*lint*.json"))
                for pth in report_candidates:
                    try:
                        report = json.loads(pth.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if not _canonical_report_ok(report):
                        continue
                    mtime = pth.stat().st_mtime
                    if mtime <= latest_mtime:
                        continue
                    latest = pth
                    latest_mtime = mtime
                    diag = {
                        "errors": int(report.get("errors") or 0),
                        "warnings": int(report.get("warnings") or 0),
                        "waived_warnings": int(report.get("waived_warnings") or 0),
                        "suppression_violations": int(report.get("suppression_violation_count") or 0),
                    }
                    command = str(report.get("command") or "")
                    tool = str(report.get("tool") or "")
                    source_kind = "canonical-dut-lint-json"

                text_candidates: list[Path] = []
                if lint_dir.is_dir():
                    for suffix in ("*.log", "*.txt", "*.out"):
                        text_candidates.extend(lint_dir.rglob(suffix))
                for pth in text_candidates:
                    name_l = pth.name.lower()
                    if name_l.startswith("sim_report") or name_l.startswith("coverage_report") or "results" in name_l:
                        continue
                    try:
                        text = pth.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    text_l = text.lower()
                    if _reject_sim_log(text_l, pth):
                        continue
                    if not any(tok in text_l for tok in ("verilator", "pyslang", "iverilog", "slang", "lint-only")):
                        continue
                    mtime = pth.stat().st_mtime
                    if mtime > latest_mtime:
                        latest = pth
                        latest_mtime = mtime
                        diag = _count_log_diagnostics(text, waivers)
                        command = ""
                        tool = ""
                        source_kind = "lint-dir-text"
                warning_budget = 0
                status = "unknown" if latest is None else (
                    "pass" if (
                        diag["errors"] == 0
                        and diag["warnings"] == 0
                        and diag.get("suppression_violations", 0) == 0
                    ) else "fail"
                )
                return {
                    "status": status,
                    "errors": diag["errors"],
                    "warnings": diag["warnings"],
                    "suppression_violations": diag.get("suppression_violations", 0),
                    "warning_budget": warning_budget,
                    "waivers": waivers,
                    "source": _soc_rel(latest) if latest else "",
                    "source_kind": source_kind,
                    "tool": tool,
                    "command": command,
                    "criteria": "DUT RTL-only lint report from <ip>/lint; sim/cocotb/root cmd_output logs are not valid lint evidence",
                }

            def _sim_progress(ip_dir: Path, doc: dict) -> dict:
                tr = doc.get("test_requirements") if isinstance(doc, dict) else {}
                scenarios = tr.get("scenarios") if isinstance(tr, dict) else []
                scenario_count = len(scenarios) if isinstance(scenarios, list) else 0
                scoreboard = tr.get("scoreboard_checks") if isinstance(tr, dict) else None
                coverage_goals = tr.get("coverage_goals") if isinstance(tr, dict) else {}
                coverage_goal_count = len(coverage_goals) if isinstance(coverage_goals, dict) else 0
                scenario_rows = []
                if isinstance(scenarios, list):
                    for sc in scenarios:
                        if isinstance(sc, dict):
                            scenario_rows.append({
                                "id": str(sc.get("id") or ""),
                                "name": str(sc.get("name") or sc.get("title") or ""),
                                "expected": str(sc.get("expected") or ""),
                                "status": "pending",
                            })
                tb_dir = ip_dir / "tb"
                tests = []
                tb_text = ""
                if tb_dir.is_dir():
                    for pth in tb_dir.rglob("test*.py"):
                        try:
                            text = pth.read_text(encoding="utf-8", errors="replace")
                        except OSError:
                            continue
                        tb_text += "\n" + text
                        tests.extend(re.findall(r"@cocotb\.test|def\s+test_", text))
                    for pth in list(tb_dir.rglob("*.sv")) + list(tb_dir.rglob("*.v")):
                        try:
                            tb_text += "\n" + pth.read_text(encoding="utf-8", errors="replace")
                        except OSError:
                            continue
                for row in scenario_rows:
                    sid = row.get("id") or ""
                    if sid and re.search(rf"\b{re.escape(sid)}\b", tb_text):
                        row["status"] = "implemented"
                def _result_xml_paths() -> list[Path]:
                    canonical = ip_dir / "sim" / "results.xml"
                    roots = [
                        ip_dir / "sim",
                        ip_dir / "tb" / "cocotb",
                        ip_dir / "tb",
                    ]
                    out: list[Path] = []
                    seen: set[Path] = set()
                    for root in roots:
                        if not root.is_dir():
                            continue
                        for pth in root.rglob("*results.xml"):
                            rp = pth.resolve()
                            if rp not in seen:
                                out.append(pth)
                                seen.add(rp)
                    if not out:
                        return [canonical] if canonical.is_file() else []
                    canonical_rp = canonical.resolve() if canonical.exists() else None
                    noncanonical = [p for p in out if canonical_rp is None or p.resolve() != canonical_rp]
                    if not noncanonical:
                        return sorted(out, key=lambda pth: pth.stat().st_mtime if pth.exists() else 0, reverse=True)[:1]
                    newest_noncanonical = max(p.stat().st_mtime for p in noncanonical if p.exists())
                    # Cocotb often writes one result XML per config/run. Keep the latest
                    # result from each run directory, and ignore stale canonical summaries.
                    latest_by_dir: dict[Path, Path] = {}
                    for pth in noncanonical:
                        parent = pth.parent
                        cur = latest_by_dir.get(parent)
                        if cur is None or pth.stat().st_mtime > cur.stat().st_mtime:
                            latest_by_dir[parent] = pth
                    selected = [
                        p for p in latest_by_dir.values()
                        if p.exists() and p.stat().st_mtime >= newest_noncanonical - 10.0
                    ]
                    if canonical.is_file() and canonical.stat().st_mtime >= newest_noncanonical - 2.0:
                        selected.append(canonical)
                    return sorted(selected, key=lambda pth: pth.stat().st_mtime if pth.exists() else 0, reverse=True)

                results = []
                result_text = ""
                has_valid_result_xml = False
                testcase_names: set[str] = set()
                failed_names: set[str] = set()
                testcase_failed: dict[str, bool] = {}
                for pth in _result_xml_paths():
                    try:
                        text = pth.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if not text.strip():
                        continue
                    result_text += "\n" + text
                    parsed_xml = False
                    try:
                        import xml.etree.ElementTree as _ET
                        root_xml = _ET.fromstring(text)
                        cases = list(root_xml.iter("testcase"))
                        if cases:
                            parsed_xml = True
                            has_valid_result_xml = True
                            source_fail = 0
                            source_err = 0
                            for tc in cases:
                                name = tc.attrib.get("name") or ""
                                if not name:
                                    continue
                                testcase_names.add(name)
                                has_failure = tc.find("failure") is not None
                                has_error = tc.find("error") is not None
                                if has_failure or has_error:
                                    failed_names.add(name)
                                if has_failure:
                                    source_fail += 1
                                if has_error:
                                    source_err += 1
                                # Result files can be mirrored under sim/ and tb/cocotb/.
                                # _result_xml_paths() returns newest first, so keep the
                                # first observation for a testcase name to avoid double
                                # counting the same run.
                                testcase_failed.setdefault(name, has_failure or has_error)
                            results.append({
                                "tests": len(cases),
                                "failures": source_fail,
                                "errors": source_err,
                                "source": _soc_rel(pth),
                            })
                    except Exception:
                        parsed_xml = False
                    if not parsed_xml:
                        names = re.findall(r'<testcase[^>]*name="([^"]+)"', text)
                        testcase_names.update(names)
                        source_failed: set[str] = set()
                        for m in re.finditer(r'<testcase[^>]*name="([^"]+)"[^>]*>(.*?)</testcase>', text, re.S):
                            if re.search(r'<(?:failure|error)\b', m.group(2)):
                                source_failed.add(m.group(1))
                        failed_names.update(source_failed)
                        for name in names:
                            testcase_failed.setdefault(name, name in source_failed)
                        tests_attr = re.search(r'tests="(\d+)"', text)
                        fail_attr = re.search(r'failures="(\d+)"', text)
                        err_attr = re.search(r'errors="(\d+)"', text)
                        if tests_attr:
                            has_valid_result_xml = True
                            results.append({
                                "tests": int(tests_attr.group(1)),
                                "failures": int(fail_attr.group(1)) if fail_attr else 0,
                                "errors": int(err_attr.group(1)) if err_attr else 0,
                                "source": _soc_rel(pth),
                            })
                        elif names:
                            has_valid_result_xml = True
                            results.append({
                                "tests": len(names),
                                "failures": len(source_failed),
                                "errors": 0,
                                "source": _soc_rel(pth),
                            })
                def _sid_matches_name(sid: str, name: str) -> bool:
                    if not sid:
                        return False
                    sid_l = sid.lower()
                    name_l = name.lower()
                    if sid_l in name_l:
                        return True
                    m = re.match(r"sc(\d+)$", sid_l)
                    return bool(m and f"sc{int(m.group(1)):02d}" in name_l)

                if has_valid_result_xml:
                    for row in scenario_rows:
                        sid = row.get("id") or ""
                        if any(_sid_matches_name(sid, name) for name in testcase_names):
                            row["status"] = "pass"
                    for row in scenario_rows:
                        sid = row.get("id") or ""
                        if any(_sid_matches_name(sid, name) for name in failed_names):
                            row["status"] = "fail"
                if testcase_failed:
                    total = len(testcase_failed)
                    fail = sum(1 for failed in testcase_failed.values() if failed)
                else:
                    total = sum(r["tests"] for r in results)
                    fail = sum(r["failures"] + r["errors"] for r in results)
                cov_pct = None
                cov_doc = {}
                cov_bins: dict[str, object] = {}
                coverage_limitations: dict[str, object] = {}
                coverage_static: dict[str, object] = {}
                check_total = None
                check_pass = None
                check_fail = None
                escalations = []
                cov_paths = sorted((ip_dir / "cov").glob("coverage*.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0)
                for cov_json in cov_paths:
                    try:
                        cov_doc = json.loads(cov_json.read_text(encoding="utf-8"))
                        functional = cov_doc.get("functional") if isinstance(cov_doc, dict) else {}
                        if isinstance(functional, dict):
                            cov_pct = functional.get("pct", cov_pct)
                        if isinstance(cov_doc, dict):
                            bins = cov_doc.get("functional_bins")
                            if isinstance(bins, dict):
                                cov_bins.update(bins)
                        if isinstance(cov_doc, dict):
                            if isinstance(cov_doc.get("total_checks"), int):
                                check_total = (check_total or 0) + cov_doc.get("total_checks")
                            if isinstance(cov_doc.get("passed"), int):
                                check_pass = (check_pass or 0) + cov_doc.get("passed")
                            if isinstance(cov_doc.get("failed"), int):
                                check_fail = (check_fail or 0) + cov_doc.get("failed")
                            static_limits = cov_doc.get("static_universe_not_instrumented")
                            if isinstance(static_limits, dict):
                                for k, v in static_limits.items():
                                    coverage_limitations[k] = v
                            explicit_limits = cov_doc.get("limitations")
                            if isinstance(explicit_limits, dict):
                                for k, v in explicit_limits.items():
                                    coverage_limitations[k] = v
                            for metric_key in ("lines", "branches", "functions", "fsm_state"):
                                metric_doc = cov_doc.get(metric_key)
                                if isinstance(metric_doc, dict):
                                    coverage_static[metric_key] = metric_doc
                            raw_escalations = cov_doc.get("escalations")
                            if isinstance(raw_escalations, list):
                                escalations.extend(e for e in raw_escalations if isinstance(e, dict))
                    except Exception:
                        pass
                if cov_bins:
                    hit = sum(1 for v in cov_bins.values() if bool(v))
                    total_bins = max(scenario_count, len(cov_bins))
                    cov_pct = _pct(hit, total_bins)
                    for row in scenario_rows:
                        sid = str(row.get("id") or "")
                        if not sid or row.get("status") == "fail":
                            continue
                        prefix = f"{sid}_".lower()
                        if any(str(k).lower().startswith(prefix) and bool(v) for k, v in cov_bins.items()):
                            row["status"] = "pass"
                escalation_by_sid: dict[str, list[dict]] = {}
                for esc in escalations:
                    sid = str(esc.get("test_id") or esc.get("scenario") or esc.get("id") or "").strip()
                    if not sid:
                        text = json.dumps(esc, ensure_ascii=False)
                        m = re.search(r"\b(SC\d+)\b", text, re.I)
                        sid = m.group(1) if m else ""
                    if sid:
                        escalation_by_sid.setdefault(sid.lower(), []).append(esc)
                for row in scenario_rows:
                    sid = str(row.get("id") or "").lower()
                    row_escalations = escalation_by_sid.get(sid, [])
                    if not row_escalations:
                        continue
                    text = json.dumps(row_escalations, ensure_ascii=False).lower()
                    row["status"] = "blocked" if (
                        "blocked" in text or "infrastructure" in text or "parameter override" in text
                    ) else "fail"
                    row["escalation"] = row_escalations[0]
                if isinstance(check_fail, int) and check_fail > fail:
                    fail = check_fail
                has_sim_evidence = total > 0
                sim_pass_evidence = has_sim_evidence and fail == 0
                passed_scenarios = sum(1 for r in scenario_rows if r["status"] == "pass")
                failed_scenarios = sum(1 for r in scenario_rows if r["status"] == "fail")
                all_scenarios_passed = scenario_count == 0 or passed_scenarios >= scenario_count
                has_coverage_numbers = cov_pct is not None or isinstance(check_total, int)
                functional_closed = cov_pct is not None and float(cov_pct) >= 100.0
                if not has_sim_evidence:
                    coverage_status = "pending"
                elif fail:
                    coverage_status = "fail"
                elif not all_scenarios_passed:
                    coverage_status = "pending"
                elif not cov_paths:
                    coverage_status = "pending"
                elif not has_coverage_numbers:
                    coverage_status = "pending"
                elif coverage_limitations:
                    coverage_status = "blocked"
                elif not functional_closed:
                    coverage_status = "fail"
                else:
                    coverage_status = "pass"
                return {
                    "dv_plan": {
                        "scenarios": scenario_count,
                        "scoreboard_checks": scoreboard,
                        "coverage_goals": coverage_goal_count,
                        "scenario_rows": scenario_rows,
                    },
                    "implemented_scenarios": sum(1 for r in scenario_rows if r["status"] in ("implemented", "pass")),
                    "passed_scenarios": passed_scenarios,
                    "failed_scenarios": failed_scenarios,
                    "implemented_tests": len(tests),
                    "results": {
                        "total": total,
                        "pass": max(total - fail, 0),
                        "fail": fail,
                        "sources": [r["source"] for r in results],
                        "check_total": check_total,
                        "check_pass": check_pass,
                        "check_fail": check_fail,
                    },
                    "coverage": {
                        "status": coverage_status,
                        "functional_pct": cov_pct,
                        "static": coverage_static,
                        "criteria": coverage_goals if isinstance(coverage_goals, dict) else {},
                        "limitations": coverage_limitations,
                    },
                    "escalations": escalations,
                }

            def _req_progress(ip_dir: Path) -> dict:
                req_dir = ip_dir / "req"
                files = []
                if req_dir.is_dir():
                    files = [
                        p for p in sorted(req_dir.rglob("*"))
                        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".yaml", ".yml", ".json"}
                    ]
                total_bytes = sum(p.stat().st_size for p in files if p.exists())
                text = ""
                for p in files[:12]:
                    try:
                        text += "\n" + p.read_text(encoding="utf-8", errors="replace")[:200000]
                    except OSError:
                        pass
                placeholder = bool(re.search(r"\b(TBD|TODO|FIXME|HACK)\b", text, re.I))
                enough = total_bytes >= 1000 and not placeholder
                return {
                    "status": "ok" if files and enough else ("partial" if files else "pending"),
                    "files": [_soc_rel(p) for p in files[:12]],
                    "bytes": total_bytes,
                    "placeholder": placeholder,
                    "criteria": "REQ capture exists under <ip>/req, has substantive content, and contains no TBD/TODO/FIXME placeholders",
                }

            def _fl_model_progress(ip_dir: Path, doc: dict | None = None) -> dict:
                model_path = ip_dir / "model" / "functional_model.py"
                check_path = ip_dir / "model" / "fl_model_check.json"
                exists = model_path.is_file()
                size = model_path.stat().st_size if exists else 0
                text = ""
                if exists:
                    try:
                        text = model_path.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        text = ""
                check = {}
                if check_path.is_file():
                    try:
                        check = json.loads(check_path.read_text(encoding="utf-8"))
                    except Exception:
                        check = {"passed": False}
                has_api = "class FunctionalModel" in text and "def apply" in text
                imports_ok = bool(check.get("passed") is True)
                fm = doc.get("function_model") if isinstance(doc, dict) and isinstance(doc.get("function_model"), dict) else {}
                txns = fm.get("transactions") if isinstance(fm.get("transactions"), list) else []
                expected_txns = [
                    str(tx.get("id") or tx.get("name") or "").strip()
                    for tx in txns
                    if isinstance(tx, dict) and (tx.get("id") or tx.get("name"))
                ]
                trace_sources = [
                    check.get("transaction_results"),
                    check.get("transaction_traceability"),
                    (check.get("self_check") or {}).get("transaction_results") if isinstance(check.get("self_check"), dict) else None,
                    (check.get("self_check") or {}).get("transaction_traceability") if isinstance(check.get("self_check"), dict) else None,
                ]
                trace_text = json.dumps(trace_sources, ensure_ascii=False).lower()
                traced_txns = [
                    txn for txn in expected_txns
                    if txn.lower() in trace_text
                ]
                trace_complete = not expected_txns or len(traced_txns) == len(expected_txns)
                status = "pass" if exists and size >= 500 and has_api and imports_ok and trace_complete else (
                    "partial" if exists else "pending"
                )
                return {
                    "status": status,
                    "source": _soc_rel(model_path) if exists else "",
                    "check_source": _soc_rel(check_path) if check_path.is_file() else "",
                    "bytes": size,
                    "has_apply": has_api,
                    "self_check": check,
                    "transactions_expected": expected_txns,
                    "transactions_traced": traced_txns,
                    "trace_complete": trace_complete,
                    "criteria": "executable Python FL model generated from SSOT with FunctionalModel.apply(txn), passing self-check, and tracing every SSOT function_model transaction",
                }

            def _fl_decomp_progress(ip_dir: Path) -> dict:
                path = ip_dir / "model" / "decomposition.json"
                doc = {}
                if path.is_file():
                    try:
                        doc = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        doc = {}
                units = doc.get("units") if isinstance(doc, dict) else []
                if not isinstance(units, list):
                    units = []
                kinds = sorted({str(u.get("kind")) for u in units if isinstance(u, dict) and u.get("kind")})
                status = "pass" if path.is_file() and isinstance(units, list) and len(units) >= 2 and doc.get("complete") is True else (
                    "partial" if path.is_file() else "pending"
                )
                return {
                    "status": status,
                    "source": _soc_rel(path) if path.is_file() else "",
                    "units": len(units) if isinstance(units, list) else 0,
                    "kinds": kinds,
                    "criteria": "FL model decomposition traces protocol/register/memory/datapath/FSM/error/security units to SSOT sections",
                }

            def _fcov_plan_progress(ip_dir: Path) -> dict:
                path = ip_dir / "cov" / "fcov_plan.json"
                doc = {}
                if path.is_file():
                    try:
                        doc = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        doc = {}
                bins = doc.get("bins") if isinstance(doc, dict) else []
                if not isinstance(bins, list):
                    bins = []
                classes = sorted({str(b.get("class")) for b in bins if isinstance(b, dict) and b.get("class")})
                status = "pass" if path.is_file() and isinstance(bins, list) and len(bins) > 0 and doc.get("planned_before_rtl") is True else (
                    "partial" if path.is_file() else "pending"
                )
                return {
                    "status": status,
                    "source": _soc_rel(path) if path.is_file() else "",
                    "bins": len(bins) if isinstance(bins, list) else 0,
                    "classes": classes,
                    "summary": doc.get("summary") if isinstance(doc, dict) else {},
                    "criteria": "functional coverage bins are planned from SSOT/FL model before RTL signoff",
                }

            def _equivalence_progress(ip_dir: Path) -> dict:
                goals_path = ip_dir / "verify" / "equivalence_goals.json"
                compare_path = ip_dir / "sim" / "fl_rtl_compare.json"
                classify_path = ip_dir / "sim" / "mismatch_classification.json"
                goals_doc: dict[str, Any] = {}
                compare_doc: dict[str, Any] = {}
                classify_doc: dict[str, Any] = {}
                if goals_path.is_file():
                    try:
                        loaded = json.loads(goals_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            goals_doc = loaded
                    except Exception:
                        goals_doc = {}
                if compare_path.is_file():
                    try:
                        loaded = json.loads(compare_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            compare_doc = loaded
                    except Exception:
                        compare_doc = {}
                if classify_path.is_file():
                    try:
                        loaded = json.loads(classify_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            classify_doc = loaded
                    except Exception:
                        classify_doc = {}

                goals = goals_doc.get("goals") if isinstance(goals_doc.get("goals"), list) else []
                goal_summary = goals_doc.get("summary") if isinstance(goals_doc.get("summary"), dict) else {}
                source_of_truth = goals_doc.get("source_of_truth") if isinstance(goals_doc.get("source_of_truth"), dict) else {}
                authority_contract = source_of_truth.get("authority_contract") if isinstance(source_of_truth.get("authority_contract"), dict) else {}
                compare_summary = compare_doc.get("summary") if isinstance(compare_doc.get("summary"), dict) else {}
                classifications = classify_doc.get("classifications") if isinstance(classify_doc.get("classifications"), list) else []
                classification_counts: dict[str, int] = {}
                owner_counts: dict[str, int] = {}
                loopable_repairs = 0
                human_gated_repairs = 0
                for item in classifications:
                    if not isinstance(item, dict):
                        continue
                    cls = str(item.get("classification") or "unknown")
                    owner = str(item.get("owner") or "unknown")
                    classification_counts[cls] = classification_counts.get(cls, 0) + 1
                    owner_counts[owner] = owner_counts.get(owner, 0) + 1
                    if item.get("llm_loop_allowed") is True:
                        loopable_repairs += 1
                    elif item.get("llm_loop_allowed") is False:
                        human_gated_repairs += 1
                total = int(goal_summary.get("total") or len(goals) or 0)
                generated = total
                checked = int(compare_summary.get("goals_checked") or 0)
                passed = int(compare_summary.get("goals_passed") or 0)
                failed = int(compare_summary.get("goals_failed") or 0)
                blocked = int(compare_summary.get("goals_blocked") or goal_summary.get("blocked") or 0)
                untested = int(compare_summary.get("goals_untested") or 0)
                compare_status = str(compare_doc.get("status") or "")
                stale_evidence = compare_summary.get("stale_evidence") if isinstance(compare_summary.get("stale_evidence"), list) else []
                if compare_status == "pass":
                    status = "pass"
                elif compare_status == "fail":
                    status = "fail"
                elif compare_status == "stale" or stale_evidence:
                    status = "stale"
                elif blocked:
                    status = "blocked"
                elif goals_path.is_file() and total:
                    status = "partial"
                else:
                    status = "pending"
                failed_ids = []
                blocked_ids = []
                untested_ids = []
                for item in compare_doc.get("goals") if isinstance(compare_doc.get("goals"), list) else []:
                    if not isinstance(item, dict):
                        continue
                    goal_id = str(item.get("goal_id") or "")
                    if item.get("status") == "fail":
                        failed_ids.append(goal_id)
                    elif item.get("status") == "blocked":
                        blocked_ids.append(goal_id)
                    elif item.get("status") == "untested":
                        untested_ids.append(goal_id)
                return {
                    "status": status,
                    "total": total,
                    "generated": generated,
                    "checked": checked,
                    "passed": passed,
                    "failed": failed,
                    "blocked": blocked,
                    "untested": untested,
                    "failed_goal_ids": [x for x in failed_ids if x][:12],
                    "blocked_goal_ids": [x for x in blocked_ids if x][:12],
                    "untested_goal_ids": [x for x in untested_ids if x][:12],
                    "classifications": len(classifications),
                    "loopable_repairs": loopable_repairs,
                    "human_gated_repairs": human_gated_repairs,
                    "classification_counts": classification_counts,
                    "owner_counts": owner_counts,
                    "module_total": int(goal_summary.get("module_total") or 0),
                    "module_required": int(goal_summary.get("module_required") or 0),
                    "module_blocked": int(goal_summary.get("module_blocked") or 0),
                    "authority_contract": authority_contract,
                    "general_evaluation_criteria": authority_contract.get("general_evaluation_criteria") if isinstance(authority_contract.get("general_evaluation_criteria"), list) else [],
                    "locked_artifacts": authority_contract.get("locked_artifacts") if isinstance(authority_contract.get("locked_artifacts"), list) else [],
                    "llm_editable_artifacts": authority_contract.get("llm_editable_artifacts") if isinstance(authority_contract.get("llm_editable_artifacts"), list) else [],
                    "loopable_evidence_points": authority_contract.get("loopable_evidence_points") if isinstance(authority_contract.get("loopable_evidence_points"), list) else [],
                    "loopable_oracles": authority_contract.get("loopable_oracles") if isinstance(authority_contract.get("loopable_oracles"), list) else [],
                    "missing_evidence": compare_summary.get("missing_evidence") if isinstance(compare_summary.get("missing_evidence"), list) else [],
                    "stale_evidence": stale_evidence,
                    "evidence": _soc_rel(goals_path) if goals_path.is_file() else "",
                    "compare_evidence": _soc_rel(compare_path) if compare_path.is_file() else "",
                    "classification_evidence": _soc_rel(classify_path) if classify_path.is_file() else "",
                    "next_action": (
                        "none; all equivalence goals passed"
                        if status == "pass" else
                        "rerun /sim <ip> and /sim-debug <ip>; existing evidence is stale"
                        if status == "stale" else
                        "answer SSOT/human gate questions from mismatch_classification.json"
                        if status == "blocked" else
                        "repair classified FL/RTL/TB/coverage owner from mismatch_classification.json"
                        if status == "fail" else
                        "run sim_debug comparator after TB emits scoreboard_events.jsonl"
                        if goals_path.is_file() else
                        "run /ssot-equiv-goals <ip>"
                    ),
                    "owner": (
                        "human gate" if status == "blocked" else
                        "LLM loop" if status in {"fail", "partial", "pending"} else
                        "LLM loop"
                    ),
                    "criteria": "SSOT-derived equivalence goals exist, TB scoreboard checks them, sim_debug compare passes every required goal, and all mismatches are classified",
                }

            def _goal_audit_progress(ip_dir: Path) -> dict:
                audit_path = ip_dir / "sim" / "fl_rtl_goal_audit.json"
                doc: dict[str, Any] = {}
                if audit_path.is_file():
                    try:
                        loaded = json.loads(audit_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            doc = loaded
                    except Exception:
                        doc = {}
                summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
                checks = doc.get("checks") if isinstance(doc.get("checks"), list) else []
                blockers = [str(x) for x in summary.get("blockers") or []] if isinstance(summary, dict) else []
                source_paths = [
                    ip_dir / "yaml" / f"{ip_dir.name}.ssot.yaml",
                    ip_dir / "model" / "functional_model.py",
                    ip_dir / "model" / "fl_model_check.json",
                    ip_dir / "model" / "decomposition.json",
                    ip_dir / "cov" / "fcov_plan.json",
                    ip_dir / "verify" / "equivalence_goals.json",
                    ip_dir / "sim" / "scoreboard_events.jsonl",
                    ip_dir / "sim" / "results.xml",
                    ip_dir / "tb" / "cocotb" / "results.xml",
                    ip_dir / "cov" / "coverage.json",
                    ip_dir / "sim" / "fl_rtl_compare.json",
                    ip_dir / "sim" / "mismatch_classification.json",
                    ip_dir / "rtl" / "rtl_compile.json",
                    ip_dir / "lint" / "dut_lint.json",
                    ip_dir / "lint" / "rtl_lint.json",
                ]
                stale_evidence: list[str] = []
                if audit_path.is_file():
                    existing_sources = [p for p in source_paths if p.is_file()]
                    if existing_sources:
                        newest = max(existing_sources, key=lambda p: p.stat().st_mtime)
                        if audit_path.stat().st_mtime + 0.5 < newest.stat().st_mtime:
                            try:
                                stale_evidence.append(
                                    f"{_soc_rel(audit_path)} older than {_soc_rel(newest)}"
                                )
                            except ValueError:
                                stale_evidence.append("goal audit artifact is older than a source artifact")
                raw_status = str(doc.get("status") or "") if doc else ""
                if stale_evidence:
                    status = "stale"
                elif raw_status == "pass":
                    status = "pass"
                elif raw_status == "fail":
                    status = "fail"
                elif audit_path.is_file():
                    status = "partial"
                else:
                    status = "pending"
                return {
                    "status": status,
                    "source": _soc_rel(audit_path) if audit_path.is_file() else "",
                    "total_checks": int(summary.get("total_checks") or 0) if isinstance(summary, dict) else 0,
                    "passed_checks": int(summary.get("passed_checks") or 0) if isinstance(summary, dict) else 0,
                    "failed_checks": int(summary.get("failed_checks") or 0) if isinstance(summary, dict) else 0,
                    "blockers": blockers,
                    "stale_evidence": stale_evidence,
                    "generated_at": doc.get("generated_at") if isinstance(doc, dict) else "",
                    "checks": [
                        {
                            "id": str(item.get("id") or ""),
                            "status": str(item.get("status") or ""),
                            "owner": str(item.get("owner") or ""),
                            "next_action": str(item.get("next_action") or ""),
                        }
                        for item in checks[:20]
                        if isinstance(item, dict)
                    ],
                    "next_action": (
                        "none; goal audit passed"
                        if status == "pass" else
                        "rerun /goal-audit <ip>; existing audit is stale"
                        if status == "stale" else
                        "inspect fl_rtl_goal_audit.json and rerun the owning ATLAS stage"
                        if status == "fail" else
                        "run /goal-audit <ip> after sim-debug and coverage evidence exist"
                    ),
                    "owner": "LLM loop",
                    "criteria": "single disk-truth audit proves REQ, SSOT, FL, cycle model, RTL DUT-only compile/lint, TB scoreboard, sim, compare, coverage, and signoff evidence",
                }

            def _strict_gate_from_progress(progress: dict) -> dict:
                ssot = progress.get("ssot") if isinstance(progress, dict) else {}
                req = progress.get("req") if isinstance(progress, dict) else {}
                fl_model = progress.get("fl_model") if isinstance(progress, dict) else {}
                fl_decomp = progress.get("fl_decomp") if isinstance(progress, dict) else {}
                fcov_plan = progress.get("fcov_plan") if isinstance(progress, dict) else {}
                equivalence = progress.get("equivalence_goals") if isinstance(progress, dict) else {}
                goal_audit = progress.get("goal_audit") if isinstance(progress, dict) else {}
                rtl = progress.get("rtl") if isinstance(progress, dict) else {}
                compile_st = progress.get("compile") if isinstance(progress, dict) else {}
                lint = progress.get("lint") if isinstance(progress, dict) else {}
                sim = progress.get("sim") if isinstance(progress, dict) else {}
                dv = sim.get("dv_plan") if isinstance(sim, dict) else {}
                results = sim.get("results") if isinstance(sim, dict) else {}
                coverage = sim.get("coverage") if isinstance(sim, dict) else {}

                ssot_total = int(ssot.get("total") or 0) if isinstance(ssot, dict) else 0
                ssot_approved = int(ssot.get("approved") or 0) if isinstance(ssot, dict) else 0
                req_status = str(req.get("status") or "pending") if isinstance(req, dict) else "pending"
                fl_model_status = str(fl_model.get("status") or "pending") if isinstance(fl_model, dict) else "pending"
                fl_decomp_status = str(fl_decomp.get("status") or "pending") if isinstance(fl_decomp, dict) else "pending"
                fcov_plan_status = str(fcov_plan.get("status") or "pending") if isinstance(fcov_plan, dict) else "pending"
                equivalence_status = str(equivalence.get("status") or "pending") if isinstance(equivalence, dict) else "pending"
                goal_audit_status = str(goal_audit.get("status") or "pending") if isinstance(goal_audit, dict) else "pending"
                rtl_total = int(rtl.get("total") or 0) if isinstance(rtl, dict) else 0
                rtl_approved = int(rtl.get("approved") or 0) if isinstance(rtl, dict) else 0
                rtl_mismatches = int(rtl.get("manifest_mismatches") or 0) if isinstance(rtl, dict) else 0
                rtl_quality = int(rtl.get("quality_issue_count") or 0) if isinstance(rtl, dict) else 0
                rtl_quality_issues = rtl.get("quality_issues") if isinstance(rtl, dict) and isinstance(rtl.get("quality_issues"), list) else []
                rtl_blocked = bool(rtl.get("blocked")) if isinstance(rtl, dict) else False
                rtl_blocker = str(rtl.get("blocker") or "") if isinstance(rtl, dict) else ""
                compile_status = str(compile_st.get("status") or "unknown") if isinstance(compile_st, dict) else "unknown"
                scenario_total = int(dv.get("scenarios") or 0) if isinstance(dv, dict) else 0
                implemented = int(sim.get("implemented_scenarios") or 0) if isinstance(sim, dict) else 0
                passed_scenarios = int(sim.get("passed_scenarios") or 0) if isinstance(sim, dict) else 0
                failed_scenarios = int(sim.get("failed_scenarios") or 0) if isinstance(sim, dict) else 0
                result_total = int(results.get("total") or 0) if isinstance(results, dict) else 0
                result_fail = int(results.get("fail") or 0) if isinstance(results, dict) else 0
                lint_status = str(lint.get("status") or "unknown") if isinstance(lint, dict) else "unknown"
                raw_cov_status = str(coverage.get("status") or "unknown") if isinstance(coverage, dict) else "unknown"
                all_scenarios_passed = scenario_total == 0 or passed_scenarios >= scenario_total
                sim_pass_evidence = result_total > 0 and result_fail == 0 and failed_scenarios == 0 and all_scenarios_passed
                if result_total <= 0:
                    cov_status = "pending"
                elif result_fail:
                    cov_status = "fail"
                elif not all_scenarios_passed:
                    cov_status = "pending"
                else:
                    cov_status = raw_cov_status

                ssot_status = "ok" if ssot_total and ssot_approved == ssot_total else (
                    "partial" if ssot_approved else "pending"
                )
                rtl_modules_status = "blocked" if rtl_blocked else ("ok" if rtl_total and rtl_approved == rtl_total else (
                    "partial" if rtl_approved else "pending"
                ))
                if rtl_blocked:
                    rtl_status = "blocked"
                elif lint_status == "fail":
                    rtl_status = "fail"
                elif compile_status == "fail":
                    rtl_status = "fail"
                elif rtl_mismatches:
                    rtl_status = "fail"
                elif rtl_modules_status == "ok" and compile_status == "pass" and lint_status == "pass":
                    rtl_status = "ok"
                elif rtl_modules_status == "pending":
                    rtl_status = "pending"
                else:
                    rtl_status = "partial"

                tb_status = "ok" if scenario_total and implemented >= scenario_total else (
                    "partial" if implemented else "pending"
                )
                if result_total <= 0:
                    sim_status = "pending"
                elif result_fail or failed_scenarios:
                    sim_status = "fail"
                elif not all_scenarios_passed:
                    sim_status = "partial"
                else:
                    sim_status = "ok"

                blockers: list[str] = []
                if ssot_status != "ok":
                    blockers.append(f"SSOT sections {ssot_approved}/{ssot_total} approved")
                if req_status != "ok":
                    blockers.append(f"REQ capture {req_status}")
                if fl_model_status != "pass":
                    blockers.append(f"FL model {fl_model_status}")
                if fl_decomp_status != "pass":
                    blockers.append(f"FL decomposition {fl_decomp_status}")
                if fcov_plan_status != "pass":
                    blockers.append(f"FCOV plan {fcov_plan_status}")
                if equivalence_status != "pass":
                    blockers.append(
                        "equivalence goals "
                        f"{equivalence_status} "
                        f"{equivalence.get('passed', 0) if isinstance(equivalence, dict) else 0}/"
                        f"{equivalence.get('total', 0) if isinstance(equivalence, dict) else 0} passed"
                    )
                if goal_audit_status != "pass":
                    audit_blockers = goal_audit.get("blockers", []) if isinstance(goal_audit, dict) else []
                    blockers.append(
                        "goal audit "
                        f"{goal_audit_status}"
                        + (f" blockers={','.join(str(x) for x in audit_blockers[:6])}" if audit_blockers else "")
                    )
                if rtl_blocked:
                    blockers.append(f"RTL blocked: {rtl_blocker or 'SSOT decision required'}")
                elif rtl_modules_status != "ok":
                    blockers.append(f"RTL modules {rtl_approved}/{rtl_total} approved")
                if rtl_mismatches:
                    blockers.append(f"SSOT/RTL manifest mismatch {rtl_mismatches}")
                if rtl_quality:
                    first_issue = ""
                    if rtl_quality_issues and isinstance(rtl_quality_issues[0], dict):
                        first_issue = str(rtl_quality_issues[0].get("issue") or "")
                    blockers.append(
                        f"RTL quality issues {rtl_quality}"
                        + (f": {first_issue}" if first_issue else "")
                    )
                if compile_status != "pass":
                    comp_err = compile_st.get("errors", 0) if isinstance(compile_st, dict) else 0
                    comp_diag = compile_st.get("diagnostics", 0) if isinstance(compile_st, dict) else 0
                    comp_style = compile_st.get("style_violations", 0) if isinstance(compile_st, dict) else 0
                    blockers.append(f"RTL compile {compile_status} E{comp_err}/D{comp_diag}/S{comp_style}")
                if lint_status != "pass":
                    err = lint.get("errors", 0) if isinstance(lint, dict) else 0
                    warn = lint.get("warnings", 0) if isinstance(lint, dict) else 0
                    suppressions = lint.get("suppression_violations", 0) if isinstance(lint, dict) else 0
                    suffix = f"/S{suppressions}" if suppressions else ""
                    blockers.append(f"lint {lint_status} E{err}/W{warn}{suffix}")
                if tb_status != "ok":
                    blockers.append(f"DV scenarios implemented {implemented}/{scenario_total}")
                if result_total <= 0:
                    blockers.append("no fresh sim result XML found")
                elif result_fail:
                    blockers.append(f"simulation failures {result_fail}/{result_total}")
                if scenario_total and passed_scenarios < scenario_total:
                    blockers.append(f"sim scenarios passed {passed_scenarios}/{scenario_total}")
                if cov_status != "pass":
                    if not sim_pass_evidence:
                        blockers.append("coverage requires fresh passing simulation result")
                    else:
                        blockers.append(f"coverage {cov_status}")

                if any(v in {"fail"} for v in (rtl_status, sim_status, lint_status, cov_status, equivalence_status, goal_audit_status)):
                    signoff = "fail"
                elif any(v in {"blocked", "stale"} for v in (rtl_status, sim_status, cov_status, equivalence_status, goal_audit_status)):
                    signoff = "blocked"
                elif not blockers:
                    signoff = "pass"
                elif ssot_approved or rtl_approved or implemented or result_total:
                    signoff = "partial"
                else:
                    signoff = "pending"

                status = {
                    "req": req_status,
                    "ssot": ssot_status,
                    "fl_model": fl_model_status,
                    "fl_decomp": fl_decomp_status,
                    "fcov_plan": fcov_plan_status,
                    "equivalence_goals": equivalence_status,
                    "goal_audit": goal_audit_status,
                    "rtl": rtl_status,
                    "lint": lint_status,
                    "tb": tb_status,
                    "sim_debug": sim_status,
                    "coverage": cov_status,
                    "signoff": signoff,
                }
                detail = {
                    "req": f"{req_status}: {len(req.get('files', [])) if isinstance(req, dict) else 0} requirement artifact(s)",
                    "ssot": f"{ssot_approved}/{ssot_total} canonical sections approved",
                    "fl_model": (
                        f"{fl_model_status}: "
                        f"{fl_model.get('source', '') if isinstance(fl_model, dict) else ''} "
                        f"self_check={bool(fl_model.get('self_check', {}).get('passed')) if isinstance(fl_model, dict) else False}"
                    ),
                    "fl_decomp": (
                        f"{fl_decomp_status}: "
                        f"{fl_decomp.get('units', 0) if isinstance(fl_decomp, dict) else 0} unit(s)"
                    ),
                    "fcov_plan": (
                        f"{fcov_plan_status}: "
                        f"{fcov_plan.get('bins', 0) if isinstance(fcov_plan, dict) else 0} bin(s)"
                    ),
                    "equivalence_goals": (
                        f"{equivalence_status}: "
                        f"{equivalence.get('passed', 0) if isinstance(equivalence, dict) else 0}/"
                        f"{equivalence.get('total', 0) if isinstance(equivalence, dict) else 0} pass; "
                        f"checked {equivalence.get('checked', 0) if isinstance(equivalence, dict) else 0}; "
                        f"failed {equivalence.get('failed', 0) if isinstance(equivalence, dict) else 0}; "
                        f"blocked {equivalence.get('blocked', 0) if isinstance(equivalence, dict) else 0}; "
                        f"untested {equivalence.get('untested', 0) if isinstance(equivalence, dict) else 0}"
                    ),
                    "goal_audit": (
                        f"{goal_audit_status}: "
                        f"{goal_audit.get('passed_checks', 0) if isinstance(goal_audit, dict) else 0}/"
                        f"{goal_audit.get('total_checks', 0) if isinstance(goal_audit, dict) else 0} checks; "
                        f"blockers {', '.join(goal_audit.get('blockers', [])[:6]) if isinstance(goal_audit.get('blockers', []), list) else ''}"
                    ),
                    "rtl": (
                        f"{rtl_approved}/{rtl_total} RTL files approved; "
                        f"blocked {rtl_blocked}; "
                        f"manifest mismatch {rtl_mismatches}; "
                        f"quality issues {rtl_quality}; "
                        f"compile {compile_status} "
                        f"E{compile_st.get('errors', 0) if isinstance(compile_st, dict) else 0}/"
                        f"D{compile_st.get('diagnostics', 0) if isinstance(compile_st, dict) else 0}/"
                        f"S{compile_st.get('style_violations', 0) if isinstance(compile_st, dict) else 0}; "
                        f"lint {lint_status} E{lint.get('errors', 0) if isinstance(lint, dict) else 0}/"
                        f"W{lint.get('warnings', 0) if isinstance(lint, dict) else 0}"
                        f"/S{lint.get('suppression_violations', 0) if isinstance(lint, dict) else 0}"
                    ),
                    "tb": f"{implemented}/{scenario_total} SSOT DV scenarios implemented",
                    "sim_debug": (
                        f"results {max(result_total - result_fail, 0)} pass / "
                        f"{result_fail} fail / {result_total} total; coverage {cov_status}"
                    ),
                    "coverage": f"coverage {cov_status}",
                    "signoff": "pass" if signoff == "pass" else "; ".join(blockers[:6]),
                }

                def _first_source(*values: Any) -> str:
                    for value in values:
                        if isinstance(value, str) and value:
                            return value
                        if isinstance(value, list) and value:
                            return str(value[0])
                    return ""

                def _owner(stage: str, stage_status: str) -> str:
                    if stage == "req" and stage_status != "ok":
                        return "human gate"
                    if stage == "rtl" and stage_status == "blocked":
                        return "human gate" if rtl_blocked else "blocked"
                    if stage == "signoff":
                        if stage_status == "pass":
                            return "human gate"
                        if req_status != "ok" or cov_status == "blocked" or equivalence_status == "blocked":
                            return "human gate"
                    if stage == "equivalence_goals" and stage_status == "blocked":
                        return "human gate"
                    if stage == "coverage" and stage_status == "blocked":
                        return "human gate"
                    if stage_status in {"blocked"}:
                        return "blocked"
                    return "LLM loop"

                def _next_action(stage: str, stage_status: str) -> str:
                    if stage_status in {"ok", "pass"}:
                        if stage == "signoff":
                            return "tool evidence passed; human final acceptance may proceed"
                        return "none; evidence accepted"
                    if stage == "req":
                        return "answer missing requirement questions or refresh req-gen ledger"
                    if stage == "ssot":
                        return "repair SSOT sections or ask human for undefined behavior"
                    if stage == "fl_model":
                        return "run fl-model-gen and repair FunctionalModel self-check"
                    if stage == "fl_decomp":
                        return "generate SSOT-traced FL decomposition units"
                    if stage == "fcov_plan":
                        return "generate planned functional coverage bins from SSOT/FL"
                    if stage == "equivalence_goals":
                        return equivalence.get("next_action", "run /ssot-equiv-goals and sim_debug compare") if isinstance(equivalence, dict) else "run /ssot-equiv-goals"
                    if stage == "goal_audit":
                        return goal_audit.get("next_action", "run /goal-audit after evidence exists") if isinstance(goal_audit, dict) else "run /goal-audit"
                    if stage == "rtl":
                        if stage_status == "blocked":
                            return "answer rtl_blocked SSOT questions, refresh SSOT/FL model, then rerun /ssot-rtl"
                        return "run rtl-gen repair from SSOT, compile, and lint evidence"
                    if stage == "lint":
                        return "repair DUT-only lint diagnostics or request explicit waiver"
                    if stage == "tb":
                        return "generate missing cocotb/pyuvm scenario checkers"
                    if stage == "sim_debug":
                        return "classify mismatch owner, then repair RTL/FL/TB or ask on SSOT ambiguity"
                    if stage == "coverage":
                        return "close missing planned bins or request explicit waiver"
                    if stage == "signoff":
                        return "resolve blockers before evidence signoff can pass"
                    return "inspect stage evidence"

                def _stage_entry(stage: str, stage_status: str, validator: str, evidence: str = "") -> dict:
                    blocker = detail.get(stage, "")
                    if stage_status in {"ok", "pass"}:
                        blocker = ""
                    elif stage == "rtl" and rtl_blocked and rtl_blocker:
                        blocker = rtl_blocker
                    return {
                        "stage": stage,
                        "status": stage_status,
                        "owner": _owner(stage, stage_status),
                        "validator": validator,
                        "evidence": evidence,
                        "blocker": blocker,
                        "next_action": _next_action(stage, stage_status),
                    }

                def _simple_summary() -> dict:
                    visible_order = [
                        "req",
                        "ssot",
                        "fl_model",
                        "fl_decomp",
                        "fcov_plan",
                        "equivalence_goals",
                        "rtl",
                        "lint",
                        "tb",
                        "sim_debug",
                        "coverage",
                        "goal_audit",
                    ]
                    passed = sum(1 for stage in visible_order if status.get(stage) in {"ok", "pass"})
                    total = len(visible_order)
                    percent = 100 if signoff == "pass" else int(round((passed / total) * 100)) if total else 0
                    audit_blockers = [
                        str(item).lower()
                        for item in (goal_audit.get("blockers", []) if isinstance(goal_audit, dict) else [])
                        if str(item)
                    ]
                    req_needed = req_status != "ok" or any(item == "req" for item in audit_blockers)
                    hard_fail = any(
                        status.get(stage) == "fail"
                        for stage in ("rtl", "lint", "sim_debug", "coverage", "equivalence_goals")
                    )
                    if signoff == "pass":
                        simple_state = "green"
                        headline = "Ready for signoff"
                        message = "All required evidence is green."
                    elif req_needed:
                        simple_state = "needs_review"
                        headline = "One user review is needed"
                        message = "Generated evidence can continue, but requirements need a real review before final green."
                    elif hard_fail:
                        simple_state = "needs_repair"
                        headline = "A generated stage needs repair"
                        message = "ATLAS should route the failed evidence to the owning workflow and rerun downstream checks."
                    elif passed:
                        simple_state = "needs_evidence"
                        headline = "Run the next evidence step"
                        message = "Some stages are complete. Continue the pipeline to collect the missing evidence."
                    else:
                        simple_state = "not_started"
                        headline = "Start the IP pipeline"
                        message = "Create or import SSOT, then run the flow toward RTL, TB, sim, coverage, and signoff."

                    stage_labels = {
                        "req": "Complete requirements review",
                        "ssot": "Complete SSOT",
                        "fl_model": "Generate FL model",
                        "fl_decomp": "Generate model decomposition",
                        "fcov_plan": "Create coverage plan",
                        "equivalence_goals": "Generate equivalence goals",
                        "rtl": "Generate or repair RTL",
                        "lint": "Run lint",
                        "tb": "Generate TB",
                        "sim_debug": "Run simulation and compare",
                        "coverage": "Close coverage evidence",
                        "goal_audit": "Run final evidence audit",
                    }
                    stage_reasons = {
                        "req": "Human-owned design intent must not be guessed.",
                        "ssot": "SSOT is the source of truth for every downstream workflow.",
                        "fl_model": "The executable functional model is the golden behavior reference.",
                        "fl_decomp": "Decomposition tells RTL/TB which design units must exist.",
                        "fcov_plan": "Coverage needs planned bins before signoff.",
                        "equivalence_goals": "Scoreboard checks need explicit FL/RTL goals.",
                        "rtl": "RTL must match SSOT and compile/lint cleanly.",
                        "lint": "DUT-only lint must be clean or explicitly waived.",
                        "tb": "Every SSOT DV scenario needs a runnable test.",
                        "sim_debug": "Simulation must produce fresh zero-fail results.",
                        "coverage": "Coverage must show required functional/cycle evidence.",
                        "goal_audit": "The final audit ties every artifact back to SSOT evidence.",
                    }
                    next_steps: list[dict[str, str]] = []
                    for stage in visible_order:
                        if stage == "req" and req_needed:
                            needs_step = True
                        else:
                            needs_step = status.get(stage) not in {"ok", "pass"}
                        if not needs_step:
                            continue
                        next_steps.append({
                            "stage": stage,
                            "label": stage_labels.get(stage, stage),
                            "owner": "user" if stage == "req" else "atlas",
                            "reason": stage_reasons.get(stage, ""),
                            "status": str(status.get(stage) or "pending"),
                        })
                        if len(next_steps) >= 3:
                            break

                    if not next_steps and signoff != "pass":
                        next_steps.append({
                            "stage": "signoff",
                            "label": "Review final signoff",
                            "owner": "user",
                            "reason": "Tool evidence is available; final acceptance is a user decision.",
                            "status": signoff,
                        })

                    next_stage = next_steps[0]["stage"] if next_steps else "signoff"
                    primary_label = "Run to Green"
                    if simple_state == "needs_review":
                        primary_label = "Open Review"
                    elif simple_state == "green":
                        primary_label = "View Evidence"

                    return {
                        "state": simple_state,
                        "headline": headline,
                        "message": message,
                        "percent": max(0, min(100, percent)),
                        "passed_checks": passed,
                        "total_checks": total,
                        "next_stage": next_stage,
                        "next_steps": next_steps,
                        "primary_action": {
                            "label": primary_label,
                            "kind": "open_stage" if simple_state in {"green", "needs_review"} else "run_pipeline",
                            "stage": next_stage,
                            "flow": "full",
                        },
                        "expert_blockers": blockers[:12],
                    }

                ownership = {
                    "req": _stage_entry("req", req_status, "REQ ledger placeholder/substance check", _first_source(req.get("files") if isinstance(req, dict) else "")),
                    "ssot": _stage_entry("ssot", ssot_status, "canonical SSOT section checker", "yaml/<ip>.ssot.yaml"),
                    "fl_model": _stage_entry("fl_model", fl_model_status, "FunctionalModel API + self-check", _first_source(fl_model.get("source", "") if isinstance(fl_model, dict) else "")),
                    "fl_decomp": _stage_entry("fl_decomp", fl_decomp_status, "decomposition completeness checker", _first_source(fl_decomp.get("source", "") if isinstance(fl_decomp, dict) else "")),
                    "fcov_plan": _stage_entry("fcov_plan", fcov_plan_status, "planned coverage-bin checker", _first_source(fcov_plan.get("source", "") if isinstance(fcov_plan, dict) else "")),
                    "equivalence_goals": _stage_entry("equivalence_goals", equivalence_status, "FL-vs-RTL equivalence goal + scoreboard comparator", _first_source(equivalence.get("compare_evidence", "") if isinstance(equivalence, dict) else "", equivalence.get("evidence", "") if isinstance(equivalence, dict) else "")),
                    "goal_audit": _stage_entry("goal_audit", goal_audit_status, "fl_rtl_goal_audit disk-truth verifier", _first_source(goal_audit.get("source", "") if isinstance(goal_audit, dict) else "")),
                    "rtl": _stage_entry("rtl", rtl_status, "SSOT filelist + DUT compile/lint", _first_source(rtl.get("blocker_source", "") if isinstance(rtl, dict) else "", rtl.get("filelist", "") if isinstance(rtl, dict) else "")),
                    "lint": _stage_entry("lint", lint_status, "DUT-only lint report", _first_source(lint.get("source", "") if isinstance(lint, dict) else "")),
                    "tb": _stage_entry("tb", tb_status, "SSOT scenario implementation checker", "tb/cocotb"),
                    "sim_debug": _stage_entry("sim_debug", sim_status, "fresh cocotb results.xml + scenario pass map", _first_source(results.get("sources", []) if isinstance(results, dict) else [])),
                    "coverage": _stage_entry("coverage", cov_status, "planned functional coverage closure", "cov/coverage.json"),
                    "signoff": _stage_entry("signoff", signoff, "strict SSOT progress gate", "ATLAS /api/progress"),
                }
                return {
                    "status": status,
                    "blockers": blockers,
                    "ownership": ownership,
                    "simple_summary": _simple_summary(),
                    "criteria": {
                        "req": "requirements captured before SSOT",
                        "ssot": "all canonical SSOT sections approved",
                        "fl_model": "executable FL model exists and self-check passes",
                        "fl_decomp": "FL model decomposition exists and drives RTL/TB planning",
                        "fcov_plan": "functional coverage plan exists before RTL signoff",
                        "equivalence_goals": "equivalence goals exist, scoreboard events cover them, and FL-vs-RTL compare passes",
                        "goal_audit": "single audit artifact proves all required REQ->SSOT->FL->RTL->TB->sim->coverage evidence",
                        "rtl": "all expected RTL files approved and compile/lint pass",
                        "tb": "all SSOT DV scenarios have implemented tests",
                        "sim_debug": "latest result XML has tests and zero failures/errors",
                        "coverage": "coverage report is pass with no limitations",
                        "signoff": "SSOT, FL/equivalence, RTL/lint, TB, sim, and coverage all pass",
                    },
                    "detail": detail,
                    "source": "strict-ssot-progress-gate",
                }

            def _build_module(leaf_ssot_path, *, deep: bool = True):
                """Read a leaf <ip>/yaml/<ip>.ssot.yaml → architect module dict."""
                p = leaf_ssot_path
                ip_dir = p.parent
                if ip_dir.name == "yaml":
                    ip_dir = ip_dir.parent
                ip_name = ip_dir.name
                top = ip_name
                params, interfaces = [], []
                clocks_n, resets_n = 0, 0
                addr = ""
                doc: dict[str, Any] = {}

                def _top_name(v):
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                    if isinstance(v, dict):
                        for key in ("name", "module", "top", "id"):
                            val = v.get(key)
                            if isinstance(val, str) and val.strip():
                                return val.strip()
                    return ip_name

                def _param_value(it):
                    for key in ("value", "default", "v"):
                        if key in it:
                            return it.get(key)
                    return ""

                def _iface_proto(it):
                    return (
                        it.get("proto") or it.get("protocol") or it.get("type")
                        or it.get("busType") or it.get("bus_type") or "AXI4"
                    )

                def _iface_side(role, idx):
                    role_s = str(role or "").lower()
                    if role_s == "master":
                        return "right"
                    if role_s == "slave":
                        return "left"
                    return ["right", "left", "top", "bottom"][idx % 4]

                if _yaml is not None and deep:
                    try:
                        loaded_doc = _yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
                        if isinstance(loaded_doc, dict):
                            doc = loaded_doc
                            top = _top_name(doc.get("top_module") or top)
                            io_list = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
                            cl = doc.get("clocks") or io_list.get("clock_domains") or []
                            rs = doc.get("resets") or io_list.get("resets") or []
                            clocks_n, resets_n = len(cl), len(rs)
                            for k in ("parameters", "params"):
                                if isinstance(doc.get(k), list):
                                    for it in doc[k][:6]:
                                        if isinstance(it, dict):
                                            nm = it.get("name") or it.get("k")
                                            vv = _param_value(it)
                                            if nm is not None:
                                                params.append({"k": str(nm), "v": str(vv)})
                            bif = (
                                doc.get("busInterfaces")
                                or doc.get("bus_interfaces")
                                or doc.get("interfaces")
                                or io_list.get("interfaces")
                                or []
                            )
                            if isinstance(bif, list):
                                for i, it in enumerate(bif[:8]):
                                    if not isinstance(it, dict): continue
                                    role = str(it.get("role") or "slave")
                                    interfaces.append({
                                        "name": str(it.get("name") or f"if{i}"),
                                        "proto": str(_iface_proto(it)),
                                        "role":  role,
                                        "side":  str(it.get("side") or _iface_side(role, i)),
                                        "width": int(it.get("width") or 0) or None,
                                    })
                            for c in cl[:2]:
                                if isinstance(c, dict):
                                    interfaces.append({"name": c.get("name") or "clk",
                                                       "proto": "CLK", "role": "slave", "side": "left"})
                            for r in rs[:2]:
                                if isinstance(r, dict):
                                    interfaces.append({"name": r.get("name") or "rst_n",
                                                       "proto": "RST", "role": "slave", "side": "left"})
                            mm = doc.get("memoryMap") or []
                            if isinstance(mm, list) and mm and isinstance(mm[0], dict):
                                base = mm[0].get("base")
                                if base is not None: addr = _hex_addr(base)
                    except Exception:
                        pass
                rtl_dir = ip_dir / "rtl"
                rtl_files = list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")) if rtl_dir.is_dir() else []
                list_path = ip_dir / "list" / f"{ip_dir.name}.f"
                rtl_detail = ""
                if not rtl_files:
                    rtl_st = "partial" if rtl_dir.is_dir() else "pending"
                    rtl_detail = "rtl directory exists but no RTL files" if rtl_dir.is_dir() else "no rtl directory"
                elif not list_path.is_file():
                    rtl_st = "partial"
                    rtl_detail = f"RTL files exist but filelist missing: {_soc_rel(list_path)}"
                else:
                    missing = []
                    try:
                        for raw in list_path.read_text(encoding="utf-8", errors="replace").splitlines():
                            line = raw.split("//", 1)[0].strip()
                            if not line or not line.endswith((".v", ".sv", ".vh", ".svh")):
                                continue
                            candidate = ip_dir / line
                            if not candidate.is_file():
                                candidate = PROJECT_ROOT / line
                            if not candidate.is_file():
                                missing.append(line)
                    except OSError as e:
                        missing.append(f"{list_path}: {e}")
                    if missing:
                        rtl_st = "partial"
                        rtl_detail = "filelist has missing entries: " + ", ".join(missing[:3])
                    else:
                        rtl_st = "ok"
                        rtl_detail = f"filelist OK: {_soc_rel(list_path)}"
                sim_dir = ip_dir / "sim"
                sim_files = []
                if sim_dir.is_dir():
                    sim_files = _collect_matches(sim_dir, ["*.log", "*.vcd"], recursive=True, limit=32)
                sim_history = []
                hist = sim_dir / "history.json"
                if hist.is_file():
                    try:
                        h = json.loads(hist.read_text(encoding="utf-8"))
                        if isinstance(h, dict) and isinstance(h.get("runs"), list):
                            sim_history = h["runs"][-12:]
                    except Exception:
                        pass
                tb_dir = ip_dir / "tb"
                cocotb_dir = tb_dir / "cocotb"
                tb_files = []
                if tb_dir.is_dir():
                    tb_files = _collect_matches(tb_dir, ["*.py", "*.sv", "*.v"], recursive=True, limit=64)
                cov_json = ip_dir / "cov" / "coverage.json"
                cov_detail = ""
                sim_debug_st = "pending"
                sim_debug_detail = "no VCD or coverage artifacts"
                if cov_json.is_file():
                    try:
                        cov_doc = json.loads(cov_json.read_text(encoding="utf-8"))
                        functional = cov_doc.get("functional") if isinstance(cov_doc, dict) else {}
                        lines = cov_doc.get("lines") if isinstance(cov_doc, dict) else {}
                        branches = cov_doc.get("branches") if isinstance(cov_doc, dict) else {}
                        fsm = cov_doc.get("fsm") if isinstance(cov_doc, dict) else {}
                        if isinstance(functional, dict) and functional.get("pct") is not None:
                            cov_detail = f", functional coverage {functional.get('pct')}%"
                        static_bits = []
                        for name, item in (("line", lines), ("branch", branches), ("fsm", fsm)):
                            if isinstance(item, dict):
                                source = item.get("source") or "unknown"
                                total = item.get("total")
                                pct = item.get("pct")
                                if str(source).startswith("static"):
                                    static_bits.append(f"{name} static {total}")
                                elif pct is not None:
                                    static_bits.append(f"{name} {pct}%")
                        if static_bits:
                            cov_detail += "; " + ", ".join(static_bits)
                    except Exception:
                        pass
                ssot_state = _load_ssot_state(ip_name)
                ssot_st = "ok"
                if ssot_state.get("approved") and not p.is_file():
                    ssot_st = "approved"
                elif ssot_state.get("status") == "planned" and not p.is_file():
                    ssot_st = "planned"
                tb_st = "ok" if tb_files else ("partial" if tb_dir.is_dir() else "pending")
                sim_debug_artifacts = []
                sim_wave_artifacts = []
                sim_result_artifacts = []
                sim_coverage_artifacts = []
                if sim_dir.is_dir():
                    sim_wave_artifacts.extend(_collect_matches(sim_dir, ["*.vcd", "*.fst"], recursive=True, limit=32))
                    sim_coverage_artifacts.extend(_collect_matches(sim_dir, ["coverage_report.*"], recursive=True, limit=16))
                    sim_result_artifacts.extend(_collect_matches(sim_dir, ["*results.xml"], recursive=True, limit=16))
                cocotb_build = ip_dir / "tb" / "cocotb"
                if cocotb_build.is_dir():
                    sim_wave_artifacts.extend(_collect_matches(cocotb_build, ["*.vcd", "*.fst"], recursive=True, limit=32))
                    sim_result_artifacts.extend(_collect_matches(cocotb_build, ["*results.xml"], recursive=True, limit=16))
                cov_dir = ip_dir / "cov"
                if cov_dir.is_dir():
                    sim_coverage_artifacts.extend(_collect_matches(cov_dir, ["coverage.json", "toggle.json"], recursive=True, limit=16))
                sim_debug_artifacts = sim_wave_artifacts + sim_result_artifacts + sim_coverage_artifacts
                if sim_result_artifacts and (sim_wave_artifacts or sim_coverage_artifacts):
                    sim_debug_st = "ok"
                    sim_debug_detail = f"{len(sim_debug_artifacts)} debug artifact(s)"
                    if cov_detail:
                        sim_debug_detail += cov_detail
                elif sim_debug_artifacts:
                    sim_debug_st = "partial"
                    sim_debug_detail = (
                        f"{len(sim_debug_artifacts)} debug artifact(s); "
                        "needs result XML plus waveform or coverage artifact"
                    )
                if not deep:
                    fast_status = {
                        "req": "unknown",
                        "ssot": ssot_st,
                        "fl_model": "unknown",
                        "fl_decomp": "unknown",
                        "fcov_plan": "unknown",
                        "equivalence_goals": "unknown",
                        "goal_audit": "unknown",
                        "rtl": rtl_st,
                        "compile": "unknown",
                        "lint": "unknown",
                        "tb": tb_st,
                        "sim_debug": sim_debug_st,
                        "coverage": "unknown",
                        "signoff": "pending",
                    }
                    fast_detail = {
                        "req": "not scanned in project overview",
                        "ssot": f"parsed {_soc_rel(p)}",
                        "fl_model": "not scanned in project overview",
                        "fl_decomp": "not scanned in project overview",
                        "fcov_plan": "not scanned in project overview",
                        "equivalence_goals": "not scanned in project overview",
                        "goal_audit": "not scanned in project overview",
                        "rtl": rtl_detail,
                        "compile": "not scanned in project overview",
                        "lint": "not scanned in project overview",
                        "tb": (
                            f"{len(tb_files)} TB artifact(s)"
                            + (" under tb/cocotb" if cocotb_dir.is_dir() else "")
                            + cov_detail
                            if tb_files else "no tb artifacts"
                        ),
                        "sim_debug": sim_debug_detail,
                        "coverage": "not scanned in project overview",
                        "signoff": "open IP scope for strict gate",
                    }
                    fast_source = {key: "fast-filesystem-scan" for key in fast_status}
                    top_meta = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
                    ssot_kind = str(top_meta.get("type") or "").strip()
                    fast_gate = {
                        "status": fast_status,
                        "detail": fast_detail,
                        "source": "fast-filesystem-scan",
                        "simple_summary": {},
                    }
                    return {
                        "id": ip_name,
                        "name": top,
                        "label": top,
                        "kind": _kind_for(ssot_kind or ip_name),
                        "params": params,
                        "status": fast_status,
                        "status_detail": fast_detail,
                        "status_source": fast_source,
                        "artifact_status": fast_status,
                        "artifact_detail": fast_detail,
                        "artifact_source": fast_source,
                        "interfaces": interfaces,
                        "addr": addr,
                        "rtl_files": [_soc_rel(f) for f in rtl_files],
                        "ssot_path": _soc_rel(p),
                        "ip_dir": _soc_rel(ip_dir),
                        "clocks": clocks_n,
                        "resets": resets_n,
                        "sim_history": sim_history,
                        "ssot_mtime": p.stat().st_mtime,
                        "progress": {},
                        "signoff": fast_gate,
                        "simple_summary": {},
                    }
                req_prog = _req_progress(ip_dir)
                fl_model_prog = _fl_model_progress(ip_dir, doc)
                fl_decomp_prog = _fl_decomp_progress(ip_dir)
                fcov_plan_prog = _fcov_plan_progress(ip_dir)
                equivalence_prog = _equivalence_progress(ip_dir)
                goal_audit_prog = _goal_audit_progress(ip_dir)
                artifact_status = {
                    "req": req_prog["status"],
                    "ssot": ssot_st,
                    "fl_model": fl_model_prog["status"],
                    "fl_decomp": fl_decomp_prog["status"],
                    "fcov_plan": fcov_plan_prog["status"],
                    "equivalence_goals": equivalence_prog["status"],
                    "goal_audit": goal_audit_prog["status"],
                    "rtl": rtl_st,
                    "tb": tb_st,
                    "sim_debug": sim_debug_st,
                }
                artifact_detail = {
                    "req": f"{len(req_prog.get('files', []))} requirement artifact(s), {req_prog.get('bytes', 0)}B",
                    "ssot": (
                        f"parsed {_soc_rel(p)}"
                        + ("; approved via .session state" if ssot_state.get("approved") else "")
                    ),
                    "fl_model": fl_model_prog.get("source") or "no executable FL model",
                    "fl_decomp": (
                        f"{fl_decomp_prog.get('units', 0)} unit(s): "
                        + ", ".join(fl_decomp_prog.get("kinds") or [])
                    ),
                    "fcov_plan": f"{fcov_plan_prog.get('bins', 0)} bin(s)",
                    "equivalence_goals": (
                        f"{equivalence_prog.get('passed', 0)}/"
                        f"{equivalence_prog.get('total', 0)} pass, "
                        f"{equivalence_prog.get('blocked', 0)} blocked, "
                        f"{equivalence_prog.get('untested', 0)} untested"
                    ),
                    "goal_audit": (
                        f"{goal_audit_prog.get('passed_checks', 0)}/"
                        f"{goal_audit_prog.get('total_checks', 0)} checks, "
                        f"{goal_audit_prog.get('failed_checks', 0)} failed"
                    ),
                    "rtl": rtl_detail,
                    "tb": (
                        f"{len(tb_files)} TB artifact(s)"
                        + (" under tb/cocotb" if cocotb_dir.is_dir() else "")
                        + cov_detail
                        if tb_files else "no tb artifacts"
                    ),
                    "sim_debug": sim_debug_detail,
                }
                progress = {
                    "req": req_prog,
                    "ssot": _ssot_progress(doc),
                    "fl_model": fl_model_prog,
                    "fl_decomp": fl_decomp_prog,
                    "fcov_plan": fcov_plan_prog,
                    "equivalence_goals": equivalence_prog,
                    "goal_audit": goal_audit_prog,
                    "rtl": _rtl_progress(ip_dir, doc),
                    "compile": _compile_progress(ip_dir),
                    "lint": _lint_progress(ip_dir, doc),
                    "sim": _sim_progress(ip_dir, doc),
                }
                gate = _strict_gate_from_progress(progress)
                artifact_status["rtl"] = gate["status"].get("rtl", rtl_st)
                artifact_detail["rtl"] = gate["detail"].get("rtl", rtl_detail)
                top_meta = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
                ssot_kind = str(top_meta.get("type") or "").strip()
                return {
                    "id": ip_name,
                    "name": top,
                    "label": top,
                    "kind": _kind_for(ssot_kind or ip_name),
                    "params": params,
                    "status": gate["status"],
                    "status_detail": gate["detail"],
                    "status_source": {
                        "req": gate["source"],
                        "ssot": gate["source"],
                        "fl_model": gate["source"],
                        "fl_decomp": gate["source"],
                        "fcov_plan": gate["source"],
                        "equivalence_goals": gate["source"],
                        "goal_audit": gate["source"],
                        "rtl": gate["source"],
                        "compile": gate["source"],
                        "lint": gate["source"],
                        "tb": gate["source"],
                        "sim_debug": gate["source"],
                        "coverage": gate["source"],
                        "signoff": gate["source"],
                    },
                    "artifact_status": artifact_status,
                    "artifact_detail": artifact_detail,
                    "artifact_source": {
                        "req": "filesystem-artifact",
                        "ssot": "yaml-parse",
                        "fl_model": "model/fl_model_check.json",
                        "fl_decomp": "model/decomposition.json",
                        "fcov_plan": "cov/fcov_plan.json",
                        "equivalence_goals": "verify/equivalence_goals.json",
                        "goal_audit": "sim/fl_rtl_goal_audit.json",
                        "rtl": "rtl-filelist",
                        "tb": "filesystem-artifact",
                        "sim_debug": "filesystem-artifact",
                    },
                    "interfaces": interfaces,
                    "addr": addr,
                    "rtl_files": [_soc_rel(f) for f in rtl_files],
                    "ssot_path": _soc_rel(p),
                    "ip_dir": _soc_rel(ip_dir),
                    "clocks": clocks_n,
                    "resets": resets_n,
                    "sim_history": sim_history,
                    "ssot_mtime": p.stat().st_mtime,
                    "progress": progress,
                    "signoff": gate,
                    "simple_summary": gate.get("simple_summary", {}),
                }

            def _aggregate_status(modules):
                if not modules:
                    return {
                        "req": "pending", "ssot": "pending", "fl_model": "pending",
                        "fl_decomp": "pending", "fcov_plan": "pending",
                        "equivalence_goals": "pending", "goal_audit": "pending",
                        "rtl": "pending", "lint": "unknown",
                        "tb": "pending", "sim_debug": "pending", "coverage": "unknown",
                        "signoff": "pending",
                    }
                def _all(stage: str, value: str) -> bool:
                    return all(m.get("status", {}).get(stage) == value for m in modules)
                def _any(stage: str, *values: str) -> bool:
                    return any(m.get("status", {}).get(stage) in values for m in modules)
                return {
                    "req": "ok" if _all("req", "ok") else (
                        "partial" if _any("req", "ok", "partial") else "pending"
                    ),
                    "ssot": "ok" if _all("ssot", "ok") else (
                        "partial" if _any("ssot", "ok", "partial") else "pending"
                    ),
                    "fl_model": "pass" if _all("fl_model", "pass") else (
                        "partial" if _any("fl_model", "pass", "partial") else "pending"
                    ),
                    "fl_decomp": "pass" if _all("fl_decomp", "pass") else (
                        "partial" if _any("fl_decomp", "pass", "partial") else "pending"
                    ),
                    "fcov_plan": "pass" if _all("fcov_plan", "pass") else (
                        "partial" if _any("fcov_plan", "pass", "partial") else "pending"
                    ),
                    "equivalence_goals": "fail" if _any("equivalence_goals", "fail") else (
                        "blocked" if _any("equivalence_goals", "blocked") else (
                            "pass" if _all("equivalence_goals", "pass") else (
                                "partial" if _any("equivalence_goals", "pass", "partial") else "pending"
                            )
                        )
                    ),
                    "goal_audit": "fail" if _any("goal_audit", "fail") else (
                        "blocked" if _any("goal_audit", "blocked", "stale") else (
                            "pass" if _all("goal_audit", "pass") else (
                                "partial" if _any("goal_audit", "pass", "partial") else "pending"
                            )
                        )
                    ),
                    "rtl": "fail" if _any("rtl", "fail") else (
                        "ok" if _all("rtl", "ok") else ("partial" if _any("rtl", "ok", "partial") else "pending")
                    ),
                    "lint": "fail" if _any("lint", "fail") else (
                        "pass" if _all("lint", "pass") else "unknown"
                    ),
                    "tb": "ok" if _all("tb", "ok") else (
                        "partial" if _any("tb", "ok", "partial") else "pending"
                    ),
                    "sim_debug": "fail" if _any("sim_debug", "fail") else (
                        "blocked" if _any("sim_debug", "blocked") else (
                            "ok" if _all("sim_debug", "ok") else (
                                "partial" if _any("sim_debug", "ok", "partial") else "pending"
                            )
                        )
                    ),
                    "coverage": "fail" if _any("coverage", "fail") else (
                        "blocked" if _any("coverage", "blocked") else (
                            "pass" if _all("coverage", "pass") else "unknown"
                        )
                    ),
                    "signoff": "fail" if _any("signoff", "fail") else (
                        "blocked" if _any("signoff", "blocked") else (
                            "pass" if _all("signoff", "pass") else (
                                "partial" if _any("signoff", "partial") else "pending"
                            )
                        )
                    ),
                }

            project_name = PROJECT_ROOT.name or "project"
            soc_path = PROJECT_ROOT / "soc.ssot.yaml"
            want_raw = str(ip or scope or "").strip().strip("/")
            want_parts = [part for part in want_raw.split("/") if part]
            want_ip = (
                want_parts[-2]
                if len(want_parts) >= 3
                else want_parts[0]
                if want_parts
                else ""
            )

            def _accept_leaf_path(candidate: Path, seen: set[Path]) -> Path | None:
                try:
                    resolved = candidate.resolve()
                    resolved.relative_to(PROJECT_ROOT)
                except Exception:
                    try:
                        resolved.relative_to(SOURCE_ROOT)
                    except Exception:
                        return None
                if resolved in seen or not resolved.is_file():
                    return None
                if resolved.name == "soc.ssot.yaml":
                    return None
                if any(part in SKIP_DIRS or part.startswith(".") for part in resolved.parts):
                    return None
                seen.add(resolved)
                return resolved

            def _scoped_leaf_paths(ip_name: str) -> list[Path]:
                if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip_name or ""):
                    return []
                seen: set[Path] = set()
                out: list[Path] = []
                bases = [PROJECT_ROOT, SOURCE_ROOT, PROJECT_ROOT / "common_ai_agent"]
                for base in bases:
                    if not base.is_dir():
                        continue
                    candidates = [
                        base / ip_name / "yaml" / f"{ip_name}.ssot.yaml",
                        *base.glob(f"*/{ip_name}/yaml/{ip_name}.ssot.yaml"),
                    ]
                    for candidate in candidates:
                        accepted = _accept_leaf_path(candidate, seen)
                        if accepted is not None:
                            out.append(accepted)
                return out

            def _project_leaf_paths() -> list[Path]:
                seen: set[Path] = set()
                out: list[Path] = []
                bases = [PROJECT_ROOT, SOURCE_ROOT, PROJECT_ROOT / "common_ai_agent"]
                for base in bases:
                    if not base.is_dir():
                        continue
                    for pattern in ("*/yaml/*.ssot.yaml", "*/*/yaml/*.ssot.yaml"):
                        for candidate in base.glob(pattern):
                            accepted = _accept_leaf_path(candidate, seen)
                            if accepted is not None:
                                out.append(accepted)
                return out

            def _collect_matches(root: Path, patterns: list[str], *, recursive: bool = False, limit: int = 64) -> list[Path]:
                if not root.is_dir() or limit <= 0:
                    return []
                out: list[Path] = []
                for pattern in patterns:
                    try:
                        iterator = root.rglob(pattern) if recursive else root.glob(pattern)
                        for item in iterator:
                            out.append(item)
                            if len(out) >= limit:
                                return out
                    except OSError:
                        continue
                return out

            if want_ip:
                cache_key = ("scoped", str(PROJECT_ROOT), want_ip)
                cached = _soc_cache_get(cache_key)
                if cached is not None:
                    return JSONResponse(cached)
                with _soc_build_lock:
                    cached = _soc_cache_get(cache_key)
                    if cached is not None:
                        return JSONResponse(cached)
                    modules = [_build_module(p) for p in _scoped_leaf_paths(want_ip)]
                    modules.sort(key=lambda m: m["id"])
                    cluster = {
                        "id": "ips", "name": "ips", "label": "Project IPs",
                        "x": 60, "y": 80, "w": 1200, "h": 600,
                        "status": _aggregate_status(modules),
                        "modules": modules,
                    }
                    payload = {
                        "name": project_name,
                        "version": "live",
                        "clusters": [cluster] if modules else [],
                        "busses": [],
                        "addrMap": [],
                        "module_count": len(modules),
                        "source": "scoped-dir-walk",
                        "scope": want_ip,
                    }
                    _soc_cache_set(cache_key, payload)
                    return JSONResponse(payload)

            # ── Tier 1: SoC-level SSOT exists → use it as the spine ──
            if _yaml is not None and soc_path.is_file():
                try:
                    soc_doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8", errors="replace")) or {}
                except Exception as e:
                    return JSONResponse({"error": f"soc.ssot.yaml parse: {e}", "clusters": []},
                                        status_code=500)
                if not isinstance(soc_doc, dict): soc_doc = {}

                instances = soc_doc.get("instances") or []
                clusters_def = soc_doc.get("clusters") or []
                connections = soc_doc.get("connections") or []
                addr_map = soc_doc.get("addrMap") or []

                # Build module dict per instance, looking up its leaf SSOT.
                inst_to_mod = {}
                for inst in instances:
                    if not isinstance(inst, dict): continue
                    iid = inst.get("id")
                    if not iid: continue
                    leaf = inst.get("ssot")
                    leaf_path = (PROJECT_ROOT / leaf) if leaf else None
                    if leaf_path and leaf_path.is_file():
                        m = _build_module(leaf_path, deep=False)
                    else:
                        # No leaf SSOT yet — minimal stub.
                        m = {
                            "id": iid, "name": iid, "label": iid,
                            "kind": _kind_for(inst.get("kind") or iid),
                            "params": [], "interfaces": [],
                            "status": {"ssot": "pending", "rtl": "pending", "sim": "pending"},
                            "rtl_files": [], "ssot_path": leaf or "",
                            "ip_dir": "", "addr": "",
                            "clocks": 0, "resets": 0, "sim_history": [], "ssot_mtime": 0,
                        }
                    # Apply instance-level overrides.
                    m["id"] = iid
                    if inst.get("name"):  m["name"] = inst["name"]; m["label"] = inst["name"]
                    if inst.get("addr") is not None: m["addr"] = _hex_addr(inst["addr"])
                    if inst.get("kind"):  m["kind"] = inst["kind"]
                    # Saved layout: `instances[].x/y` from soc.ssot.yaml
                    # (set by /api/soc/layout). Surfaces as module.savedX/Y
                    # so the frontend can use it as the default block
                    # position when localStorage doesn't override.
                    if isinstance(inst.get("x"), (int, float)): m["savedX"] = float(inst["x"])
                    if isinstance(inst.get("y"), (int, float)): m["savedY"] = float(inst["y"])
                    # Separate full-SoC canvas placement. Cluster/module
                    # views use x/y in a different coordinate system.
                    if isinstance(inst.get("top_x"), (int, float)): m["savedTopX"] = float(inst["top_x"])
                    if isinstance(inst.get("top_y"), (int, float)): m["savedTopY"] = float(inst["top_y"])
                    if isinstance(inst.get("overrides"), dict):
                        # Surface overrides as extra params.
                        for k, v in inst["overrides"].items():
                            m["params"].append({"k": str(k), "v": str(v)})
                    inst_to_mod[iid] = m

                # Group modules by cluster membership. Anything not in a
                # cluster falls into a synthetic "uncategorized" cluster.
                # While we're walking, propagate `cluster.role` → each
                # member's `kind` (CPU/BUS/MEM/PERIPH/ANALOG). The role
                # is the architect's explicit declaration and beats the
                # name heuristic (e.g. cortexa15_0 has no "cpu" in its
                # name; without role propagation it would fall through
                # to "periph").
                claimed = set()
                clusters_out = []
                for c in clusters_def:
                    if not isinstance(c, dict): continue
                    cid = c.get("id") or c.get("name")
                    if not cid: continue
                    members = c.get("members") or []
                    role_kind = _kind_from_role(c.get("role"))
                    cmods = []
                    for mid in members:
                        if mid not in inst_to_mod: continue
                        mod = inst_to_mod[mid]
                        # Role-from-cluster wins UNLESS the instance had
                        # an explicit `kind:` override in soc.ssot.yaml
                        # (set above when applying instance overrides).
                        # We detect "explicit override" by checking the
                        # raw instance dict, not the heuristic-derived
                        # value already in mod.
                        inst_def = next((i for i in instances
                                         if isinstance(i, dict) and i.get("id") == mid), {})
                        if not inst_def.get("kind") and role_kind:
                            mod["kind"] = role_kind
                        cmods.append(mod)
                    for m in members: claimed.add(m)
                    clusters_out.append({
                        "id": cid,
                        "name": cid,
                        "label": c.get("label") or cid,
                        "x": c.get("x", 60), "y": c.get("y", 80),
                        "w": c.get("w", 1200), "h": c.get("h", 600),
                        "role": c.get("role"),
                        "status": _aggregate_status(cmods),
                        "modules": cmods,
                    })
                stray = [m for iid, m in inst_to_mod.items() if iid not in claimed]
                if stray:
                    clusters_out.append({
                        "id": "uncategorized", "name": "uncategorized",
                        "label": "Uncategorized",
                        "x": 60, "y": 80, "w": 1200, "h": 600,
                        "status": _aggregate_status(stray),
                        "modules": stray,
                    })

                # Normalize connections — frontend renderer expects
                # {from: 'inst/iface', to: 'inst/iface', proto: 'AXI4'}.
                norm_conns = []
                for cn in connections:
                    if not isinstance(cn, dict): continue
                    if cn.get("from") and cn.get("to"):
                        norm_conns.append({
                            "from": str(cn["from"]),
                            "to":   str(cn["to"]),
                            "proto": str(cn.get("proto") or "AXI4"),
                        })

                return JSONResponse({
                    "name": soc_doc.get("name") or project_name,
                    "version": str(soc_doc.get("version") or "live"),
                    "clusters": clusters_out,
                    "busses": norm_conns,
                    "connections": norm_conns,        # alias for clarity
                    "addrMap": [
                        {**e, "base": _hex_addr(e.get("base")), "range": _hex_addr(e.get("range"))}
                        for e in (addr_map if isinstance(addr_map, list) else [])
                        if isinstance(e, dict)
                    ],
                    "module_count": len(inst_to_mod),
                    "source": "soc.ssot.yaml",
                    "soc_ssot_path": soc_path.relative_to(PROJECT_ROOT).as_posix(),
                    "soc_ssot_mtime": soc_path.stat().st_mtime,
                })

            # ── Tier 2: no soc.ssot.yaml → fall back to dir-walk ──
            cache_key = ("fallback", str(PROJECT_ROOT), str(SOURCE_ROOT))
            cached = _soc_cache_get(cache_key)
            if cached is not None:
                return JSONResponse(cached)
            with _soc_build_lock:
                cached = _soc_cache_get(cache_key)
                if cached is not None:
                    return JSONResponse(cached)
                modules = []
                for p in _project_leaf_paths():
                    modules.append(_build_module(p, deep=False))
                seen_ids = {m.get("id") for m in modules}
                session_root = PROJECT_ROOT / ".session"
                if session_root.is_dir():
                    for state_path in session_root.glob("*/*/ssot-gen/state.json"):
                        # Only accept owner-scoped trees:
                        #     .session/<owner>/<ip>/ssot-gen/state.json   (4 parts)
                        # Legacy bare-IP layouts written by pre-owner
                        # backends:
                        #     .session/<ip>/ssot-gen/state.json           (3 parts)
                        # used to leak ip_name = '<ip>' into the SoC view
                        # forever, even after the user wiped that owner
                        # from disk. Skip anything shorter than 4 segments.
                        try:
                            rel_parts = state_path.relative_to(session_root).parts
                        except Exception:
                            continue
                        if len(rel_parts) != 4 or rel_parts[2] != "ssot-gen":
                            continue
                        ip_name = rel_parts[1]
                        if ip_name in seen_ids or not _valid_ip_name(ip_name):
                            continue
                        try:
                            state = json.loads(state_path.read_text(encoding="utf-8"))
                            if not isinstance(state, dict):
                                state = {}
                        except Exception:
                            state = {}
                        status = (
                            "approved" if state.get("approved")
                            else "answered" if str(state.get("status") or "").lower() == "answered"
                            else "planned"
                        )
                        raw_kind = str(state.get("kind") or ip_name)
                        low_kind = raw_kind.lower()
                        if any(s in low_kind for s in (
                            "i2c", "uart", "spi", "gpio", "timer", "pwm",
                            "peripheral", "controller",
                        )):
                            module_kind = "periph"
                        else:
                            module_kind = _kind_for(raw_kind)
                        modules.append({
                            "id": ip_name,
                            "name": ip_name,
                            "label": ip_name,
                            "kind": module_kind,
                            "params": [],
                            "status": {
                                "ssot": status,
                                "rtl": "pending",
                                "tb": "pending",
                                "sim": "pending",
                            },
                            "status_detail": {
                                "ssot": (
                                    f"{status}; waiting for /to-ssot {ip_name}"
                                    if status == "approved"
                                    else f"answered; press /to-ssot {ip_name} to generate"
                                    if status == "answered"
                                    else f"planned; answer Web Q&A, then press /to-ssot {ip_name}"
                                ),
                                "rtl": "blocked until SSOT ok",
                                "tb": "blocked until RTL/TB generation",
                                "sim": "blocked until TB/SIM generation",
                            },
                            "status_source": {
                                "ssot": ".session-state",
                                "rtl": "filesystem-artifact",
                                "tb": "filesystem-artifact",
                                "sim": "filesystem-artifact",
                            },
                            "interfaces": [],
                            "addr": "",
                            "rtl_files": [],
                            "ssot_path": f"{ip_name}/yaml/{ip_name}.ssot.yaml",
                            "ip_dir": ip_name,
                            "clocks": 0,
                            "resets": 0,
                            "sim_history": [],
                            "ssot_mtime": state_path.stat().st_mtime,
                        })
                modules.sort(key=lambda m: m["id"])
                cluster = {
                    "id": "ips", "name": "ips", "label": "Project IPs",
                    "x": 60, "y": 80, "w": 1200, "h": 600,
                    "status": _aggregate_status(modules),
                    "modules": modules,
                }
                payload = {
                    "name": project_name,
                    "version": "live",
                    "clusters": [cluster] if modules else [],
                    "busses": [],
                    "addrMap": [],
                    "module_count": len(modules),
                    "source": "dir-walk",
                }
                _soc_cache_set(cache_key, payload)
                return JSONResponse(payload)
        except Exception as e:
            return JSONResponse({"error": str(e), "clusters": []}, status_code=500)

    # Return api_soc so the caller can rebind it as a local for any
    # cross-route Python-level callers (e.g. api_progress in atlas_ui.py).
    return api_soc
