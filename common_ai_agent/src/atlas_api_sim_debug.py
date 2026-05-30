"""sim_debug API routes — extracted from src/atlas_ui.py.

Phases 11a + 11b of refactor/atlas-modular: full sim_debug API cluster.
PoC (Phase 11a) moved /api/source via register_source_route. Phase 11b
batches the elab/hierarchy/trace/cocotb/debug_scenarios endpoints + their
shared helpers (_load_sim_debug_elab, _elab_resolve_sources) into a
single factory that takes all closure captures as kwargs.

Factory kwarg names mirror the original closure names (e.g. `_safe`,
`PROJECT_ROOT`, `_read_filelist`) so the moved function bodies need no
modification — they reference the kwargs as if they were the original
closure bindings.
"""
from __future__ import annotations

import asyncio
import os
import shlex
from pathlib import Path
from typing import Any, Callable, FrozenSet, Optional

from fastapi.responses import JSONResponse


# Whitelist of source-file extensions /api/source accepts.
_SOURCE_EXTS: FrozenSet[str] = frozenset({
    ".sv", ".v", ".svh", ".vh",
    ".py",
    ".sdc", ".tcl",
    ".f",
    ".yaml", ".yml", ".json",
    ".md", ".txt", ".log", ".rpt",
    ".sh", ".bash",
    ".c", ".h", ".cpp", ".hpp",
    ".xml",
})
_SOURCE_NO_EXT_NAMES: FrozenSet[str] = frozenset({"Makefile", "makefile", "Dockerfile"})


def register_source_route(
    app: Any,
    *,
    safe_path_fn: Callable[[str], Optional[Path]],
) -> None:
    """Wire /api/source onto `app` (Phase 11a PoC, kept verbatim)."""

    @app.get("/api/source")
    async def api_source(path: str):
        target = safe_path_fn(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        suffix = target.suffix.lower()
        if suffix not in _SOURCE_EXTS and target.name not in _SOURCE_NO_EXT_NAMES:
            return JSONResponse({
                "error": f"unsupported extension '{suffix or target.name}'",
                "allowed": sorted(_SOURCE_EXTS) + sorted(_SOURCE_NO_EXT_NAMES),
            }, status_code=400)
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({
            "path": path, "size": len(content), "content": content,
            "lines": content.split("\n"),
        })


def register_sim_debug_routes(
    app: Any,
    *,
    # Closure captures — kwarg names match original names so the function
    # bodies below need zero textual edits to call them. The other `_xxx`
    # references in the bodies (e.g. _parse_py, _add_default_filelists,
    # _read_scoreboard_rows) are all defined LOCALLY inside their parent
    # functions, not captured from create_app(), so they don't need kwargs.
    _safe,
    PROJECT_ROOT,
    WORKFLOW_ROOT,
):
    """Wire /api/debug/scenarios, /api/elab/status, /api/hierarchy,
    /api/trace, /api/cocotb. Bodies are the verbatim originals from
    create_app(); deps come in as explicit kwargs (lambdas in atlas_ui).
    """

    @app.get("/api/debug/scenarios")
    async def api_debug_scenarios(ip: str):
        """Resolve `<ip>/yaml/<ip>.ssot.yaml` test_requirements.scenarios
        and roll up pass/fail per scenario from
        `<ip>/sim/scoreboard_events.jsonl`.

        Drives the Debug tab's Tests panel: scenarios are the source of
        truth (SSOT), status comes from the latest sim run. No cross-IP
        leakage — only the requested IP's directory is read.
        """
        ip_dir = _safe(ip)
        if ip_dir is None or not ip_dir.is_dir():
            return JSONResponse({"error": "ip not found", "tests": []}, status_code=404)
        ssot_path = ip_dir / "yaml" / f"{ip_dir.name}.ssot.yaml"
        sb_path   = ip_dir / "sim"  / "scoreboard_events.jsonl"

        # Disk reads moved off the event loop. Reading SSOT YAML +
        # scoreboard JSONL synchronously inside the coroutine pinned
        # every other request behind it for hundreds of milliseconds
        # whenever the user opened the Debug tab.
        def _read_ssot_scenarios() -> list:
            if not ssot_path.is_file():
                return []
            try:
                import yaml as _yaml  # type: ignore
                doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8", errors="replace"))
                tr = (doc or {}).get("test_requirements") or {}
                return list(tr.get("scenarios") or [])
            except Exception:
                return []

        def _read_scoreboard_rows() -> list:
            if not sb_path.is_file():
                return []
            import json as _json
            out = []
            for line in sb_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(_json.loads(line))
                except Exception:
                    continue
            return out

        scenarios = await asyncio.to_thread(_read_ssot_scenarios)
        rows = await asyncio.to_thread(_read_scoreboard_rows)

        by_sid: dict[str, dict] = {}
        for r in rows:
            sid = r.get("scenario_id")
            if not sid:
                continue
            bucket = by_sid.setdefault(sid, {"pass": 0, "fail": 0, "rows": []})
            bucket["rows"].append(r)
            if r.get("passed"):
                bucket["pass"] += 1
            else:
                bucket["fail"] += 1

        tests = []
        seen_sids: set[str] = set()
        for sc in scenarios:
            sid = sc.get("id")
            if sid:
                seen_sids.add(str(sid))
            b = by_sid.get(sid, {"pass": 0, "fail": 0, "rows": []})
            if b["fail"] > 0:
                status = "fail"
            elif b["pass"] > 0:
                status = "pass"
            else:
                status = "pending"
            tests.append({
                "scenario_id": sid,
                "name": sc.get("name", sid or ""),
                "status": status,
                "stimulus": sc.get("stimulus", ""),
                "expected": sc.get("expected", ""),
                "checker":  sc.get("checker", ""),
                "coverage": sc.get("coverage", []),
                "pass_rows": b["pass"],
                "fail_rows": b["fail"],
                "source": "ssot",
            })
        for sid in sorted(k for k in by_sid.keys() if str(k) not in seen_sids):
            b = by_sid.get(sid, {"pass": 0, "fail": 0, "rows": []})
            if b["fail"] > 0:
                status = "fail"
            elif b["pass"] > 0:
                status = "pass"
            else:
                status = "pending"
            tests.append({
                "scenario_id": sid,
                "name": sid,
                "status": status,
                "stimulus": "",
                "expected": "",
                "checker": "",
                "coverage": [],
                "pass_rows": b["pass"],
                "fail_rows": b["fail"],
                "source": "scoreboard",
            })
        summary = {
            "pass":    sum(1 for t in tests if t["status"] == "pass"),
            "fail":    sum(1 for t in tests if t["status"] == "fail"),
            "pending": sum(1 for t in tests if t["status"] == "pending"),
            "total":   len(tests),
        }
        return JSONResponse({
            "ip": ip,
            "ssot_path": str(ssot_path.relative_to(PROJECT_ROOT)) if ssot_path.is_file() else "",
            "sb_path":   str(sb_path.relative_to(PROJECT_ROOT))   if sb_path.is_file()   else "",
            "tests":   tests,
            "summary": summary,
        })


    _ELAB_CACHE = {}


    def _load_sim_debug_elab():
        import importlib.util as _ilu
        elab_path = WORKFLOW_ROOT / "sim_debug" / "elab.py"
        if not elab_path.is_file():
            raise FileNotFoundError(f"sim_debug elab module not found at {elab_path}")
        try:
            mtime_ns = elab_path.stat().st_mtime_ns
        except OSError:
            mtime_ns = 0
        if _ELAB_CACHE.get("path") == str(elab_path) and _ELAB_CACHE.get("mtime_ns") == mtime_ns:
            return _ELAB_CACHE["mod"]
        spec = _ilu.spec_from_file_location("sim_debug_elab", str(elab_path))
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ELAB_CACHE.update({"mod": mod, "path": str(elab_path), "mtime_ns": mtime_ns})
        return mod


    @app.get("/api/elab/status")
    async def api_elab_status():
        try:
            mod = _load_sim_debug_elab()
            return JSONResponse(mod.status())
        except Exception as e:
            return JSONResponse({"error": str(e), "pyslang": False, "verilator": False, "slang": False}, status_code=500)


    def _elab_resolve_sources(sources_glob: str, ip: str = "") -> list:
        """Resolve a comma-separated glob list (or a single ip-tree default).
        Each pattern is interpreted relative to PROJECT_ROOT and clipped to
        files that pass _safe(). Default source discovery prefers the IP
        filelist (`<ip>/list/*.f` or nested `*/<ip>/list/*.f`) before
        falling back to RTL directory scans.
        """
        skip_parts = {
            ".git", ".session", "__pycache__", "node_modules", "vendor",
            ".venv", "venv", "dist", "build",
        }
        rtl_suffixes = (".sv", ".v", ".svh", ".vh")
        filelist_suffixes = (".f", ".vf", ".flist", ".list")
        out: list = []
        seen: set[str] = set()
        seen_filelists: set[str] = set()

        def _add(f):
            try:
                resolved = f.resolve()
                rel = resolved.relative_to(PROJECT_ROOT)
            except (OSError, ValueError):
                return
            if any(part in skip_parts for part in rel.parts):
                return
            if not f.is_file() or f.suffix.lower() not in rtl_suffixes:
                return
            key = rel.as_posix()
            if key in seen:
                return
            seen.add(key)
            out.append(resolved)

        def _project_relative_file(p: Path, suffixes: tuple[str, ...]) -> Optional[Path]:
            try:
                resolved = p.resolve()
                rel = resolved.relative_to(PROJECT_ROOT)
            except (OSError, ValueError):
                return None
            if any(part in skip_parts for part in rel.parts):
                return None
            if not resolved.is_file() or resolved.suffix.lower() not in suffixes:
                return None
            return resolved

        def _resolve_filelist_token(token: str, bases: list[Path]) -> list[Path]:
            raw = os.path.expanduser(os.path.expandvars(str(token or "").strip()))
            if not raw:
                return []
            p = Path(raw)
            if p.is_absolute():
                return [p]
            candidates: list[Path] = []
            for base in bases:
                candidates.append(base / p)
            candidates.append(PROJECT_ROOT / p)
            return candidates

        def _read_filelist(filelist: Path) -> None:
            resolved = _project_relative_file(filelist, filelist_suffixes)
            if resolved is None:
                return
            key = resolved.relative_to(PROJECT_ROOT).as_posix()
            if key in seen_filelists:
                return
            seen_filelists.add(key)
            bases = [resolved.parent, resolved.parent.parent, PROJECT_ROOT]
            try:
                lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                return
            for raw in lines:
                line = raw.split("//", 1)[0].split("#", 1)[0].strip()
                if not line:
                    continue
                try:
                    tokens = shlex.split(line, comments=False, posix=True)
                except ValueError:
                    tokens = line.split()
                i = 0
                while i < len(tokens):
                    token = tokens[i].strip()
                    if token in ("-f", "-F") and i + 1 < len(tokens):
                        for candidate in _resolve_filelist_token(tokens[i + 1], bases):
                            _read_filelist(candidate)
                        i += 2
                        continue
                    if (token.startswith("-f") or token.startswith("-F")) and len(token) > 2:
                        for candidate in _resolve_filelist_token(token[2:], bases):
                            _read_filelist(candidate)
                        i += 1
                        continue
                    if token.startswith("+incdir+") or token.startswith("+define+") or token.startswith("-I"):
                        i += 1
                        continue
                    if token.startswith("-") or token.startswith("+"):
                        i += 1
                        continue
                    if Path(token).suffix.lower() in rtl_suffixes:
                        for candidate in _resolve_filelist_token(token, bases):
                            _add(candidate)
                    i += 1

        def _add_default_filelists(clean_ip: str) -> None:
            ip_leaf = Path(clean_ip).name
            patterns = [
                f"{clean_ip}/list/{ip_leaf}.f",
                f"{clean_ip}/list/*.f",
                f"common_ai_agent/{clean_ip}/list/{ip_leaf}.f",
                f"common_ai_agent/{clean_ip}/list/*.f",
                f"common_ai_agent/*/{clean_ip}/list/{ip_leaf}.f",
                f"common_ai_agent/*/{clean_ip}/list/*.f",
                f"*/{clean_ip}/list/{ip_leaf}.f",
                f"*/{clean_ip}/list/*.f",
                f"*/*/{clean_ip}/list/{ip_leaf}.f",
                f"*/*/{clean_ip}/list/*.f",
            ]
            for pat in patterns:
                for f in PROJECT_ROOT.glob(pat):
                    _read_filelist(f)

        if not sources_glob and ip:
            clean_ip = str(ip).strip().strip("/")
            _add_default_filelists(clean_ip)
            if out:
                return out
            default_patterns = [
                f"{clean_ip}/rtl/*",
                f"common_ai_agent/{clean_ip}/rtl/*",
                f"common_ai_agent/*/{clean_ip}/rtl/*",
                f"*/{clean_ip}/rtl/*",
                f"*/*/{clean_ip}/rtl/*",
            ]
            for pat in default_patterns:
                for f in PROJECT_ROOT.glob(pat):
                    _add(f)
            if not out:
                for rtl_dir in PROJECT_ROOT.rglob("rtl"):
                    try:
                        rel = rtl_dir.resolve().relative_to(PROJECT_ROOT)
                    except (OSError, ValueError):
                        continue
                    if any(part in skip_parts for part in rel.parts):
                        continue
                    parent = rtl_dir.parent.name
                    if parent == clean_ip or clean_ip in rel.parts:
                        for f in rtl_dir.glob("*"):
                            _add(f)
            return out
        for pat in (sources_glob or "").split(","):
            pat = pat.strip().lstrip("/")
            if not pat:
                continue
            for f in PROJECT_ROOT.glob(pat):
                _add(f)
        return out


    @app.get("/api/hierarchy")
    async def api_hierarchy(top: str, sources: str = "", ip: str = "",
                            backend: str = ""):
        """Return the elaborated instance tree.

        Query params:
          - top      : top module name (required)
          - sources  : comma-separated globs of SV/V files (relative to PROJECT_ROOT)
          - ip       : shorthand — prefers `<ip>/list/*.f`, then `<ip>/rtl/*.sv`
          - backend  : 'dual' (default), 'pyslang', 'verilator', or 'slang'
        """
        try:
            mod = _load_sim_debug_elab()
            build_hierarchy_cached = mod.build_hierarchy_cached
            from atlas_sim_debug_top import resolve_sim_debug_top
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}"}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched", "sources_tried": sources or ip}, status_code=400)
        try:
            top_info = resolve_sim_debug_top(PROJECT_ROOT, ip=ip, requested_top=top)
            resolved_top = top_info.get("top") or top
            res = build_hierarchy_cached(backend, resolved_top, srcs)
            res = dict(res)
            res["requested_top"] = top
            res["resolved_top"] = resolved_top
            res["top_resolution"] = top_info
            res["sources"] = [p.relative_to(PROJECT_ROOT).as_posix() for p in srcs]
            return JSONResponse(res)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=503)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)


    @app.get("/api/trace")
    async def api_trace(signal: str, top: str = "", scope: str = "",
                        sources: str = "", ip: str = "",
                        backend: str = ""):
        """Trace driver/sinks for a signal. Top module resolution priority:
        explicit `top` > scope[0] > `ip` > signal[0]. Same source resolution
        as /api/hierarchy."""
        try:
            mod = _load_sim_debug_elab()
            trace_driver_cached = mod.trace_driver_cached
            from atlas_sim_debug_top import resolve_sim_debug_top
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}"}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched"}, status_code=400)
        top_info = resolve_sim_debug_top(
            PROJECT_ROOT,
            ip=ip,
            requested_top=top,
            vcd_scope=scope,
        )
        resolved_top = top_info.get("top") or signal.split(".", 1)[0]
        try:
            res = trace_driver_cached(backend, resolved_top, signal, srcs)
            res = dict(res)
            res["requested_top"] = top
            res["resolved_top"] = resolved_top
            res["top_resolution"] = top_info
            res["sources"] = [p.relative_to(PROJECT_ROOT).as_posix() for p in srcs]
            return JSONResponse(res)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=503)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)


    @app.get("/api/module/signals")
    async def api_module_signals(module: str, top: str = "", sources: str = "",
                                 ip: str = "", backend: str = ""):
        """List every declared signal of one RTL module: ports (with
        in/out/inout direction) plus internal nets/variables, each with
        type, bit width, and file:line. Drives the Debug left-panel signal
        list when the user clicks a module in the hierarchy tree.

        Always elaborated via pyslang (the only backend exposing port
        directions). Same source resolution as /api/hierarchy."""
        if not module:
            return JSONResponse({"error": "module parameter required", "signals": []}, status_code=400)
        try:
            mod = _load_sim_debug_elab()
            module_signals_cached = mod.module_signals_cached
            from atlas_sim_debug_top import resolve_sim_debug_top
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}", "signals": []}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched", "signals": []}, status_code=400)
        top_info = resolve_sim_debug_top(PROJECT_ROOT, ip=ip, requested_top=top)
        resolved_top = top_info.get("top") or top or module
        try:
            res = await asyncio.to_thread(
                module_signals_cached, backend, resolved_top, module, srcs)
            res = dict(res)
            res["requested_top"] = top
            res["resolved_top"] = resolved_top
            res["sources"] = [p.relative_to(PROJECT_ROOT).as_posix() for p in srcs]
            status_code = 200 if res.get("signals") else (200 if not res.get("error") else 404)
            return JSONResponse(res, status_code=status_code)
        except ValueError as e:
            return JSONResponse({"error": str(e), "signals": []}, status_code=503)
        except Exception as e:
            return JSONResponse({"error": str(e), "signals": []}, status_code=500)


    @app.get("/api/cocotb")
    async def api_cocotb(ip: str = ""):
        """Inspect a cocotb testbench environment under <ip>/cocotb/ or <ip>/tb/cocotb/.
        Returns a categorised file tree + parsed results.xml summary
        so the sim_debug UI can show 'TB' alongside the RTL hierarchy.
        """
        if not ip:
            return JSONResponse({"error": "ip parameter required"}, status_code=400)
        base = _safe(ip + "/cocotb")
        if base is None or not base.is_dir():
            base = _safe(ip + "/tb/cocotb")
        if base is None or not base.is_dir():
            return JSONResponse({"error": f"no cocotb dir under {ip}/ or {ip}/tb/", "exists": False})
        out = {
            "exists": True,
            "ip": ip,
            "tests":     [],   # tests/*.py
            "sequences": [],
            "env":       [],
            "agent":     [],
            "other":     [],   # Makefile, __init__.py, sim_dump.v, etc.
            "build":     [],   # sim_build/*
            "results":   None, # parsed results.xml
        }
        bucket_dirs = {
            "tests": "tests", "sequences": "sequences",
            "env": "env", "agent": "agent",
        }

        def _parse_py(p):
            """Static-analyse a cocotb Python file via the `ast` module.
            Returns { classes, tests, functions } with file:line locs.
            Same idea as pyslang for SV — no execution, fast, accurate."""
            import ast as _ast
            try:
                src = p.read_text(encoding="utf-8", errors="replace")
                tree = _ast.parse(src, filename=str(p))
            except Exception as e:
                return {"error": str(e)}
            classes, tests, funcs = [], [], []
            for node in tree.body:
                if isinstance(node, _ast.ClassDef):
                    bases = [_ast.unparse(b) if hasattr(_ast, "unparse") else "" for b in node.bases]
                    methods = []
                    for sub in node.body:
                        if isinstance(sub, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                            methods.append({"name": sub.name, "line": sub.lineno, "is_async": isinstance(sub, _ast.AsyncFunctionDef)})
                    classes.append({"name": node.name, "line": node.lineno, "bases": bases, "methods": methods})
                elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    decorators = []
                    is_test = False
                    for d in node.decorator_list:
                        try:
                            ds = _ast.unparse(d) if hasattr(_ast, "unparse") else ""
                        except Exception:
                            ds = ""
                        decorators.append(ds)
                        if "cocotb.test" in ds:
                            is_test = True
                    entry = {
                        "name": node.name, "line": node.lineno,
                        "is_async": isinstance(node, _ast.AsyncFunctionDef),
                        "decorators": decorators,
                    }
                    (tests if is_test else funcs).append(entry)
            return {"classes": classes, "tests": tests, "functions": funcs}

        try:
            for sub in sorted(base.iterdir()):
                if sub.is_file():
                    rel = sub.relative_to(PROJECT_ROOT).as_posix()
                    entry = {"path": rel, "name": sub.name, "size": sub.stat().st_size}
                    if sub.suffix == ".py" and sub.name.startswith("test_"):
                        entry["parsed"] = _parse_py(sub)
                        out["tests"].append(entry)
                    else:
                        out["other"].append(entry)
                    continue
                if sub.is_dir():
                    bucket = next((k for k, v in bucket_dirs.items() if v == sub.name), None)
                    if bucket:
                        for f in sorted(sub.rglob("*.py")):
                            if "__pycache__" in f.parts or f.name == "__init__.py":
                                rel = f.relative_to(PROJECT_ROOT).as_posix()
                                if f.name == "__init__.py":
                                    out[bucket].append({"path": rel, "name": f.name, "size": f.stat().st_size, "parsed": None})
                                continue
                            rel = f.relative_to(PROJECT_ROOT).as_posix()
                            out[bucket].append({
                                "path": rel, "name": f.name,
                                "size": f.stat().st_size,
                                "parsed": _parse_py(f),
                            })
                    elif sub.name == "sim_build":
                        for f in sorted(sub.iterdir()):
                            if not f.is_file(): continue
                            rel = f.relative_to(PROJECT_ROOT).as_posix()
                            out["build"].append({"path": rel, "name": f.name, "size": f.stat().st_size})
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)

        # Build TB hierarchy: aggregate class definitions across files.
        tb_hier = {"agents": [], "envs": [], "scoreboards": [], "sequences": [], "tests": []}
        for bucket in ("agent", "env", "sequences", "tests"):
            for f in out.get(bucket, []):
                p = f.get("parsed") or {}
                for c in p.get("classes", []):
                    info = {"name": c["name"], "line": c["line"], "file": f["path"], "bases": c["bases"], "methods": [m["name"] for m in c["methods"]]}
                    bases_blob = " ".join(c["bases"]).lower()
                    if "scoreboard" in c["name"].lower() or "scoreboard" in bases_blob:
                        tb_hier["scoreboards"].append(info)
                    elif bucket == "agent" or "agent" in c["name"].lower() or "driver" in c["name"].lower() or "monitor" in c["name"].lower():
                        tb_hier["agents"].append(info)
                    elif bucket == "env" or "env" in c["name"].lower() or "tb" in c["name"].lower():
                        tb_hier["envs"].append(info)
                    elif bucket == "sequences" or "sequence" in c["name"].lower() or "seq" in c["name"].lower():
                        tb_hier["sequences"].append(info)
                for t in p.get("tests", []):
                    tb_hier["tests"].append({"name": t["name"], "line": t["line"], "file": f["path"], "decorators": t["decorators"]})
        out["tb_hierarchy"] = tb_hier

        # Parse results.xml (cocotb format) for test pass/fail summary.
        rx = base / "results.xml"
        if rx.is_file():
            try:
                import xml.etree.ElementTree as _ET
                root_xml = _ET.parse(str(rx)).getroot()
                cases = []
                pass_n = 0; fail_n = 0; skip_n = 0
                for tc in root_xml.iter("testcase"):
                    name = tc.attrib.get("name", "")
                    classname = tc.attrib.get("classname", "")
                    time_s = tc.attrib.get("time", "0")
                    sim_t  = tc.attrib.get("sim_time_ns", "")
                    file_attr = tc.attrib.get("file", "")
                    line_attr = tc.attrib.get("lineno", "0")
                    failure = tc.find("failure") is not None or tc.find("error") is not None
                    skipped = tc.find("skipped") is not None
                    if failure: fail_n += 1
                    elif skipped: skip_n += 1
                    else: pass_n += 1
                    rel_file = ""
                    if file_attr:
                        try:
                            fp = Path(file_attr)
                            if fp.is_absolute():
                                rel_file = str(fp.resolve().relative_to(PROJECT_ROOT))
                            else:
                                safe_fp = _safe(file_attr)
                                rel_file = safe_fp.relative_to(PROJECT_ROOT).as_posix() if safe_fp else file_attr
                        except Exception:
                            try:
                                rel_file = str(Path(file_attr).resolve().relative_to(PROJECT_ROOT))
                            except Exception:
                                rel_file = file_attr
                    cases.append({
                        "name": name, "classname": classname,
                        "time_s": float(time_s) if time_s else 0,
                        "sim_time_ns": sim_t,
                        "file": rel_file, "line": int(line_attr) if line_attr.isdigit() else 0,
                        "status": "fail" if failure else ("skip" if skipped else "pass"),
                    })
                out["results"] = {
                    "total": pass_n + fail_n + skip_n,
                    "pass": pass_n, "fail": fail_n, "skip": skip_n,
                    "cases": cases,
                    "mtime": rx.stat().st_mtime,
                }
            except Exception as e:
                out["results"] = {"error": f"parse failed: {e}"}
        return JSONResponse(out)
