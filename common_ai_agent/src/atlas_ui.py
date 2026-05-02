"""
src/atlas_ui.py — Atlas frontend server for common_ai_agent

Serves the static frontend bundle at common_ai_agent/frontend/atlas/ and
bridges it to the existing main.py agent loop via:

  • GET  /                       → frontend/atlas/index.html
  • GET  /<asset>                → frontend/atlas/<asset>     (jsx, css, js)
  • WS   /ws/agent               → bidirectional event stream

Activation:
    UI_MODE=atlas  python3 src/textual_main.py        (preferred)
    or directly:   python3 -m src.atlas_ui --port 8765

This mirrors web_ui.py (SSE) but uses WebSockets so the frontend can both
push prompts AND receive token / stage / tool / cost / todo events.

Author: Atlas frontend
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import queue
import re
import sys
import threading
import time
from pathlib import Path

# `from __future__ import annotations` turns every type annotation into
# a string. FastAPI's `get_type_hints()` then needs to resolve those
# strings in the *module globals*. The inner endpoint functions live
# inside create_app() (they import fastapi locally), so without a
# module-level alias of `Request`, the annotation `request: Request`
# becomes an unresolvable ForwardRef and pydantic v2 falls back to
# treating `request` as a query parameter (→ 422 on every POST).
# This conditional import keeps the script usable even when fastapi is
# missing — `Request` just becomes None and the endpoint won't be
# registered (the local import inside create_app sys.exits first).
try:
    from fastapi import Request  # noqa: F401  (used as a forward-ref target)
except ImportError:
    Request = None  # type: ignore

# ── Paths ──────────────────────────────────────────────────────────
HERE         = Path(__file__).resolve().parent
SOURCE_ROOT  = HERE.parent                            # common_ai_agent/ (source)
FRONTEND     = SOURCE_ROOT / "frontend" / "atlas"
# PROJECT_ROOT is the user's cwd at launch, NOT the source repo. This
# lets the user run `python ../path/to/textual_main.py` from any
# project directory and have the file API + scope operate on THAT dir.
PROJECT_ROOT = Path(os.getcwd()).resolve()
# Backwards compat alias — older code references ROOT.
ROOT         = SOURCE_ROOT


# ── ask_user answer formatter ──────────────────────────────────────
def _format_answer(ans: dict, options: list) -> str:
    """Render a UI answer payload back into a tool observation string."""
    selected_ids = ans.get("selected") or []
    custom = (ans.get("custom") or "").strip()
    label_by_id = {o.get("id"): o.get("label", o.get("id")) for o in options or []}
    selected_labels = [label_by_id.get(sid, sid) for sid in selected_ids]
    parts = []
    if selected_labels:
        parts.append("selected: " + ", ".join(selected_labels))
    if custom:
        parts.append("note: " + custom)
    if not parts:
        return "(user submitted with no selection)"
    return " · ".join(parts)


# ── Bridge between agent thread and async WS handlers ──────────────
class _AtlasBridge:
    """Queues prompts from the WS into the sync agent loop and pushes
    agent events back out to all connected WS clients.
    """

    def __init__(self) -> None:
        self._inbox: queue.Queue[str] = queue.Queue()
        self._interrupts: queue.Queue[str] = queue.Queue()
        self._outbox: queue.Queue[dict] = queue.Queue()
        self._answer_qs: dict = {}            # flow_id → queue.Queue
        self._answer_lock = threading.Lock()
        self.agent_running: bool = False
        # Esc-style abort flag — checked once per poll by react_loop.
        # Set when the UI sends {type:'stop'}; cleared by check_stop().
        self._stop_flag: bool = False

    # — agent-side (sync) —
    def get_input(self, prompt: str = "") -> str:
        return self._inbox.get()

    def poll_interrupt(self):
        try:
            return self._interrupts.get_nowait()
        except queue.Empty:
            return None

    def emit(self, msg_type: str, **payload) -> None:
        self._outbox.put_nowait({"type": msg_type, **payload})

    # ask_user lifecycle (agent-side, sync) —
    def open_question(self, flow_id: str) -> "queue.Queue":
        q: queue.Queue = queue.Queue()
        with self._answer_lock:
            self._answer_qs[flow_id] = q
        return q

    def close_question(self, flow_id: str) -> None:
        with self._answer_lock:
            self._answer_qs.pop(flow_id, None)

    def wait_answer(self, flow_id: str, timeout=None):
        with self._answer_lock:
            q = self._answer_qs.get(flow_id)
        if q is None:
            return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None

    # — ws-side (async) —
    def submit_prompt(self, text: str) -> None:
        if self.agent_running:
            self._interrupts.put(text)
        else:
            self._inbox.put(text)

    def submit_answer(self, flow_id: str, payload: dict) -> bool:
        with self._answer_lock:
            q = self._answer_qs.get(flow_id)
        if q is None:
            return False
        q.put(payload)
        return True

    # Esc / abort handling
    def request_stop(self) -> None:
        """Mark a stop request — react_loop will see it on its next poll."""
        self._stop_flag = True

    def check_stop(self) -> bool:
        """Read-and-clear the stop flag (drop-in for esc_check_fn)."""
        if self._stop_flag:
            self._stop_flag = False
            return True
        return False

    async def next_event(self) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._outbox.get)


# ── App factory ────────────────────────────────────────────────────
def create_app():
    try:
        from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
        from fastapi.responses import FileResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
        from starlette.routing import WebSocketRoute
    except ImportError:
        print("ERROR: fastapi not installed. Run: pip install fastapi uvicorn websockets")
        sys.exit(1)

    if not FRONTEND.exists():
        print(f"ERROR: frontend bundle not found at {FRONTEND}")
        sys.exit(1)

    app = FastAPI(title="ATLAS · common_ai_agent")
    bridge = _AtlasBridge()
    clients: set = set()

    @app.get("/")
    async def index():
        return FileResponse(FRONTEND / "index.html")

    @app.get("/api/version")
    async def api_version():
        """Returns the latest mtime across the frontend bundle. The
        browser polls this every few seconds — if it bumps, the page
        reloads. Cheap server-side hot-reload without watchdog or
        websocket file-watcher complexity.
        """
        latest = 0.0
        try:
            for f in FRONTEND.iterdir():
                if f.is_file():
                    latest = max(latest, f.stat().st_mtime)
        except OSError:
            pass
        return JSONResponse({"mtime": latest})

    @app.get("/healthz")
    async def healthz():
        info = {
            "ok": True,
            "frontend": str(FRONTEND),
            "source_root":  str(SOURCE_ROOT),     # where atlas_ui.py lives
            "project_root": str(PROJECT_ROOT),    # = user's cwd at launch
            "cwd": os.getcwd(),
        }
        # Expose the real model + context window so the sidebar doesn't
        # have to invent values. Pull from src.config (the per-process
        # frozen settings); if config isn't importable yet, fall through
        # to env vars.
        try:
            import src.config as _cfg  # noqa: WPS433
        except Exception:
            try: import config as _cfg  # noqa: WPS433
            except Exception: _cfg = None
        # Pick up any .env edits made while the server has been running so
        # the sidebar (and dispatch on the next call) reflect the latest
        # active model / profile without a restart. mtime-cached → cheap.
        if _cfg is not None:
            try:
                _cfg.reload_env()
            except Exception:
                pass
        if _cfg is not None:
            model = ""
            try:
                from src.llm_client import get_active_model
                model = get_active_model() or ""
            except Exception:
                pass
            if not model:
                model = (
                    getattr(_cfg, "MODEL_NAME", None)
                    or getattr(_cfg, "PRIMARY_MODEL", None)
                    or getattr(_cfg, "LLM_MODEL_NAME", "")
                )
            info["model"] = model
            info["base_model"] = (
                getattr(_cfg, "PRIMARY_MODEL", "")
                or getattr(_cfg, "MODEL_NAME", "")
            )
            info["base_url"] = getattr(_cfg, "BASE_URL", "")
            info["provider"] = getattr(_cfg, "LLM_PROVIDER", "")
            info["max_context"] = getattr(_cfg, "MAX_CONTEXT_TOKENS", 0)
            info["max_iterations"] = getattr(_cfg, "MAX_ITERATIONS", 0)
            # Resolve the "active session" the user is looking at. When
            # the agent boots WITHOUT -w, ACTIVE_WORKSPACE is unset but
            # the session still maps to .session/default/. Prefer the
            # explicit workspace; fall back to the actual project the
            # session loader is using (config.ACTIVE_PROJECT) so the
            # UI can show "default" instead of an ambiguous "—".
            info["workspace"] = (os.environ.get("ACTIVE_WORKSPACE")
                                  or os.environ.get("WORKSPACE")
                                  or getattr(_cfg, "ACTIVE_PROJECT", "")
                                  or "default")
            # Per-model pricing (USD / 1M tokens) — input / cache / output.
            # get_active_pricing honors LLM_BASE_MODEL env first, falling
            # back to LLM_MODEL_NAME / config.MODEL_NAME, so the rate shown
            # in the sidebar always matches the model actually in use.
            info["pricing"] = None
            try:
                from lib.model_pricing import get_active_pricing
                p = get_active_pricing()
                if p is not None:
                    info["pricing"] = {
                        "input": p.input, "cache": p.cache, "output": p.output,
                    }
            except Exception:
                pass
            # Live cumulative token + cost totals (from session cost.json)
            try:
                import json as _json
                from pathlib import Path as _P
                _sess = os.environ.get("ATLAS_PROJECT_ROOT") or os.getcwd()
                _candidates = [
                    _P(_sess) / ".session" / (info["workspace"] or "default") / "cost.json",
                    _P(_sess) / ".session" / "default" / "cost.json",
                ]
                for c in _candidates:
                    if c.exists():
                        d = _json.loads(c.read_text())
                        # cost.json schema (written by lib/textual_ui.py):
                        # {in_tok, cache_tok, out_tok, sum_tok}. The
                        # previous code read input/cached/output, which
                        # always missed and reported 0 — that wiped the
                        # live-accumulated tokens on every flush via the
                        # /healthz refresh path.
                        info["tokens_in"]    = d.get("in_tok",    d.get("input",  0))
                        info["tokens_cache"] = d.get("cache_tok", d.get("cached", 0))
                        info["tokens_out"]   = d.get("out_tok",   d.get("output", 0))
                        # Cost in USD
                        if info["pricing"]:
                            ti = info["tokens_in"]    or 0
                            tc = info["tokens_cache"] or 0
                            to = info["tokens_out"]   or 0
                            info["cost_usd"] = (
                                ti * info["pricing"]["input"]  / 1_000_000
                                + tc * info["pricing"]["cache"]  / 1_000_000
                                + to * info["pricing"]["output"] / 1_000_000
                            )
                        break
            except Exception:
                pass
        else:
            import os as _os
            info["model"] = _os.environ.get("LLM_MODEL_NAME", "") or _os.environ.get("MODEL_NAME", "")
            info["max_context"] = int(_os.environ.get("MAX_CONTEXT_TOKENS", "0") or "0")
            info["max_iterations"] = int(_os.environ.get("MAX_ITERATIONS", "0") or "0")
            info["workspace"] = _os.environ.get("ACTIVE_WORKSPACE", "") or _os.environ.get("WORKSPACE", "")
        return JSONResponse(info)

    @app.get("/api/workspaces")
    async def api_workspaces():
        """List every workspace under workflow/ with a workspace.json.

        Reads from the SOURCE repo (not the user's cwd) since workspace
        definitions ship with common_ai_agent itself.
        """
        workflow_dir = SOURCE_ROOT / "workflow"
        items = []
        if workflow_dir.is_dir():
            for d in sorted(workflow_dir.iterdir()):
                if not d.is_dir():
                    continue
                ws_json = d / "workspace.json"
                if not ws_json.exists():
                    continue
                try:
                    spec = json.loads(ws_json.read_text())
                except Exception:
                    spec = {}
                items.append({
                    "id": d.name,
                    "name": d.name,
                    "label": spec.get("name", d.name),
                    "description": spec.get("description", ""),
                })
        # Same fallback as /healthz — show the actual session name even
        # when ACTIVE_WORKSPACE is unset (boot without -w). Frontend
        # uses this to render the workflow strip's active highlight.
        active = (os.environ.get("ACTIVE_WORKSPACE")
                  or os.environ.get("ACTIVE_PROJECT")
                  or "default")
        return JSONResponse({"active": active, "items": items})

    # ── REAL project data API ────────────────────────────────────
    # File-system backed endpoints. All paths are confined to the user's
    # PROJECT_ROOT (= cwd at launch, computed at module import) and
    # rejected if they try to escape via .. or absolute paths. This is
    # NOT the source repo — when the user runs:
    #   cd Custom_IP && python ../brian_hw/common_ai_agent/src/textual_main.py
    # the file API operates on Custom_IP, not on common_ai_agent/.
    # We intentionally re-bind here as a local var so the module-level
    # PROJECT_ROOT survives even if the import gets reloaded weirdly.
    import sys as _sys_local
    _PROJECT_ROOT = globals().get("PROJECT_ROOT") or Path(os.getcwd()).resolve()
    PROJECT_ROOT = _PROJECT_ROOT
    MAX_READ_BYTES = 256 * 1024
    SKIP_DIRS = {".git", "__pycache__", "node_modules", ".session",
                 "ATLAS", "vendor", ".venv", ".pytest_cache"}

    def _safe(rel_path):
        rel = (rel_path or "").lstrip("/")
        candidate = (PROJECT_ROOT / rel).resolve()
        try:
            candidate.relative_to(PROJECT_ROOT)
        except ValueError:
            return None
        return candidate

    @app.get("/api/files")
    async def api_files(path: str = "", recursive: int = 0, max_depth: int = 4,
                          max_entries: int = 800):
        target = _safe(path)
        if target is None:
            return JSONResponse({"error": "path outside project root"},
                                status_code=400)
        if not target.exists():
            return JSONResponse({"error": "not found"}, status_code=404)
        rel = "" if target == PROJECT_ROOT else str(
            target.relative_to(PROJECT_ROOT))
        if target.is_file():
            stat = target.stat()
            return JSONResponse({
                "type": "file", "path": rel,
                "size": stat.st_size, "mtime": stat.st_mtime,
            })

        entries: list = []

        def _list_one(d, depth):
            try:
                children = sorted(d.iterdir(),
                                   key=lambda p: (p.is_file(), p.name.lower()))
            except PermissionError:
                return
            for child in children:
                if len(entries) >= max_entries:
                    return
                if child.name in SKIP_DIRS or child.name.startswith("."):
                    continue
                try:
                    stat = child.stat()
                except OSError:
                    continue
                entries.append({
                    "name":  child.name if not recursive else str(child.relative_to(target)),
                    "type":  "dir" if child.is_dir() else "file",
                    "size":  stat.st_size if child.is_file() else None,
                    "mtime": stat.st_mtime,
                    "depth": depth,
                })
                if recursive and child.is_dir() and depth < max_depth:
                    _list_one(child, depth + 1)

        _list_one(target, 0)
        return JSONResponse({"type": "dir", "path": rel,
                              "entries": entries,
                              "truncated": len(entries) >= max_entries})

    @app.get("/api/file")
    async def api_file(path: str):
        target = _safe(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        stat = target.stat()
        truncated = stat.st_size > MAX_READ_BYTES
        try:
            data = target.read_bytes()[:MAX_READ_BYTES]
            content = data.decode("utf-8", errors="replace")
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({
            "path": path, "size": stat.st_size, "mtime": stat.st_mtime,
            "truncated": truncated, "content": content,
        })

    # ── VCD (waveform) endpoints — sim_debug workspace ────────────
    # VCD files can be MB+ so we bypass MAX_READ_BYTES with a separate
    # ceiling. Path resolution still goes through _safe() so the user
    # can't escape PROJECT_ROOT.
    MAX_VCD_BYTES = 32 * 1024 * 1024  # 32 MB

    @app.get("/api/vcd/list")
    async def api_vcd_list(ip: str = "", scope: str = ""):
        """Discover VCD files under PROJECT_ROOT.

        - `ip`    — restrict to `<ip>/sim/*.vcd` (matches the IP-tree convention).
        - `scope` — arbitrary sub-directory under PROJECT_ROOT to search.
        - neither — recursive scan up to depth 4 (cheap on typical projects).
        Returns: `{files: [{path, size, mtime}]}` sorted by mtime desc.
        """
        if ip:
            base = _safe(ip + "/sim")
        elif scope:
            base = _safe(scope)
        else:
            base = PROJECT_ROOT
        if base is None or not base.is_dir():
            return JSONResponse({"files": [], "error": "scope not found"}, status_code=404)

        results = []
        try:
            if ip or scope:
                # Direct *.vcd in chosen dir.
                for f in base.glob("*.vcd"):
                    if f.is_file():
                        st = f.stat()
                        rel = str(f.relative_to(PROJECT_ROOT))
                        results.append({"path": rel, "size": st.st_size, "mtime": st.st_mtime})
            else:
                # Recursive scan (capped depth).
                for f in base.rglob("*.vcd"):
                    try:
                        rel = f.relative_to(PROJECT_ROOT)
                    except ValueError:
                        continue
                    if any(p in SKIP_DIRS for p in rel.parts):
                        continue
                    if len(rel.parts) > 5:
                        continue
                    st = f.stat()
                    results.append({"path": str(rel), "size": st.st_size, "mtime": st.st_mtime})
        except OSError as e:
            return JSONResponse({"error": str(e), "files": []}, status_code=500)
        results.sort(key=lambda x: x["mtime"], reverse=True)
        return JSONResponse({"files": results, "project_root": str(PROJECT_ROOT)})

    @app.get("/api/vcd/raw")
    async def api_vcd_raw(path: str):
        """Return raw VCD content (UTF-8, replace errors). Capped at 32 MB."""
        target = _safe(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        if target.suffix.lower() != ".vcd":
            return JSONResponse({"error": "not a .vcd file"}, status_code=400)
        st = target.stat()
        truncated = st.st_size > MAX_VCD_BYTES
        try:
            data = target.read_bytes()[:MAX_VCD_BYTES]
            content = data.decode("utf-8", errors="replace")
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({
            "path": path,
            "size": st.st_size,
            "mtime": st.st_mtime,
            "truncated": truncated,
            "content": content,
        })

    # ── Source endpoint — sim_debug signal→driver + cocotb test view ─
    # Accepts SV/V plus the text extensions that show up in the
    # cocotb tab (Python tests, sequences, agents, env, Makefile,
    # YAML/JSON, etc.). Rejects binaries to avoid shipping .vvp / .out
    # contents over WS.
    _SOURCE_EXTS = {
        ".sv", ".v", ".svh", ".vh",          # SystemVerilog
        ".py",                                # cocotb / Python testbench
        ".sdc", ".tcl", ".f",                 # constraints / filelists
        ".yaml", ".yml", ".json", ".md",      # config / docs
        ".txt", ".log", ".rpt",               # reports
        ".sh", ".bash",                       # scripts
        ".c", ".h", ".cpp", ".hpp",           # firmware
        ".xml",                               # results.xml
    }
    _SOURCE_NO_EXT_NAMES = {"Makefile", "makefile", "Dockerfile"}

    @app.get("/api/source")
    async def api_source(path: str):
        """Read a source file. Accepts SV / V / Python / Make /
        constraints / YAML / JSON / Markdown / shell / firmware /
        results.xml. Returns split-by-line array for the SourceViewer
        component."""
        target = _safe(path)
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
            "path": path,
            "size": len(content),
            "content": content,
            "lines": content.split("\n"),
        })

    # ── sim_debug elab module loader ─────────────────────────────
    # Lives at workflow/sim_debug/elab.py — co-located with the rest
    # of the sim_debug workspace (system_prompt.md, commands/, rules/,
    # scripts/). Loaded via importlib so we don't have to add
    # workflow/sim_debug/ to sys.path globally.
    _ELAB_CACHE = {}
    def _load_sim_debug_elab():
        if "mod" in _ELAB_CACHE:
            return _ELAB_CACHE["mod"]
        import importlib.util as _ilu
        elab_path = SOURCE_ROOT / "workflow" / "sim_debug" / "elab.py"
        if not elab_path.is_file():
            raise FileNotFoundError(f"sim_debug elab module not found at {elab_path}")
        spec = _ilu.spec_from_file_location("sim_debug_elab", str(elab_path))
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ELAB_CACHE["mod"] = mod
        return mod

    # ── Elab endpoints (pyslang / Verilator / slang) — sim_debug hierarchy + trace ─
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
        files that pass _safe(). Default: `<ip>/rtl/*.sv`.
        """
        from pathlib import Path as _P
        out: list = []
        if not sources_glob and ip:
            sources_glob = f"{ip}/rtl/*.sv"
        for pat in (sources_glob or "").split(","):
            pat = pat.strip().lstrip("/")
            if not pat:
                continue
            for f in PROJECT_ROOT.glob(pat):
                try:
                    f.resolve().relative_to(PROJECT_ROOT)
                except ValueError:
                    continue
                if f.is_file() and f.suffix.lower() in (".sv", ".v", ".svh", ".vh"):
                    out.append(f)
        return out

    @app.get("/api/hierarchy")
    async def api_hierarchy(top: str, sources: str = "", ip: str = "",
                            backend: str = ""):
        """Return the elaborated instance tree.

        Query params:
          - top      : top module name (required)
          - sources  : comma-separated globs of SV/V files (relative to PROJECT_ROOT)
          - ip       : shorthand — equivalent to sources=`<ip>/rtl/*.sv`
          - backend  : 'verilator' (default) or 'slang'; falls back if unavailable
        """
        try:
            mod = _load_sim_debug_elab()
            build_hierarchy_cached = mod.build_hierarchy_cached
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}"}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched", "sources_tried": sources or ip}, status_code=400)
        try:
            return JSONResponse(build_hierarchy_cached(backend, top, srcs))
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
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}"}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched"}, status_code=400)
        # Prefer explicit top > scope's first segment > ip > signal's first segment.
        resolved_top = (
            top
            or (scope.split(".", 1)[0] if scope else "")
            or ip
            or signal.split(".", 1)[0]
        )
        try:
            return JSONResponse(trace_driver_cached(backend, resolved_top, signal, srcs))
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=503)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    # ── cocotb / TB env browsing — sim_debug "TB" tab ─────────────
    @app.get("/api/cocotb")
    async def api_cocotb(ip: str = ""):
        """Inspect a cocotb testbench environment under <ip>/cocotb/.
        Returns a categorised file tree + parsed results.xml summary
        so the sim_debug UI can show 'TB' alongside the RTL hierarchy.
        """
        if not ip:
            return JSONResponse({"error": "ip parameter required"}, status_code=400)
        base = _safe(ip + "/cocotb")
        if base is None or not base.is_dir():
            return JSONResponse({"error": f"no cocotb dir under {ip}/", "exists": False})
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
                    rel = str(sub.relative_to(PROJECT_ROOT))
                    out["other"].append({"path": rel, "name": sub.name, "size": sub.stat().st_size})
                    continue
                if sub.is_dir():
                    bucket = next((k for k, v in bucket_dirs.items() if v == sub.name), None)
                    if bucket:
                        for f in sorted(sub.rglob("*.py")):
                            if "__pycache__" in f.parts or f.name == "__init__.py":
                                rel = str(f.relative_to(PROJECT_ROOT))
                                if f.name == "__init__.py":
                                    out[bucket].append({"path": rel, "name": f.name, "size": f.stat().st_size, "parsed": None})
                                continue
                            rel = str(f.relative_to(PROJECT_ROOT))
                            out[bucket].append({
                                "path": rel, "name": f.name,
                                "size": f.stat().st_size,
                                "parsed": _parse_py(f),
                            })
                    elif sub.name == "sim_build":
                        for f in sorted(sub.iterdir()):
                            if not f.is_file(): continue
                            rel = str(f.relative_to(PROJECT_ROOT))
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
                            rel_file = str(_safe(str(_safe(file_attr) or file_attr)).relative_to(PROJECT_ROOT)) if _safe(file_attr) else ""
                        except Exception:
                            # Strip PROJECT_ROOT prefix manually.
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

    @app.post("/api/todos/clear")
    async def api_todos_clear():
        """Wipe both the in-memory tracker and the on-disk file."""
        try:
            import main as _main  # noqa: WPS433
            tt = getattr(_main, "todo_tracker", None)
            if tt is not None and hasattr(tt, "todos"):
                tt.todos = []
                if hasattr(tt, "current_index"):
                    tt.current_index = -1
                if hasattr(tt, "save"):
                    try: tt.save()
                    except Exception: pass
        except Exception:
            pass
        # Remove the on-disk file too so the legacy fallback can't
        # re-surface old todos.
        try:
            from pathlib import Path as _P
            for cand in ("current_todos.json",
                         str(_P.home() / ".common_ai_agent" / "current_todos.json")):
                p = _P(cand)
                if p.exists():
                    try: p.unlink()
                    except Exception: pass
        except Exception:
            pass
        return JSONResponse({"ok": True})

    @app.get("/api/todos")
    async def api_todos():
        # Prefer the live tracker the agent is mutating in main.py — that's
        # the only way to see in-progress changes before they hit disk. Fall
        # back to TodoTracker.load() if main hasn't initialized one yet.
        try:
            import main as _main  # noqa: WPS433
            live = getattr(_main, "todo_tracker", None)
            if live is not None and getattr(live, "todos", None):
                return JSONResponse(live.to_dict())
        except Exception:
            pass
        try:
            from lib.todo_tracker import TodoTracker
            tt = TodoTracker.load()
            # If the on-disk file is in the legacy array shape (`[{...}]`),
            # to_dict() returns {todos: []}; try parsing the array directly.
            d = tt.to_dict()
            if not d.get("todos"):
                import json as _json
                p = Path("current_todos.json")
                if p.exists():
                    try:
                        raw = _json.loads(p.read_text())
                        if isinstance(raw, list):
                            d = {"todos": [
                                {"content": t.get("content", ""),
                                 "status": t.get("status", "pending"),
                                 "priority": t.get("priority", ""),
                                 "detail": t.get("detail", "")}
                                for t in raw if isinstance(t, dict)
                            ]}
                    except Exception:
                        pass
            return JSONResponse(d)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/commands")
    async def api_commands():
        """List every slash command currently registered, including the
        workspace-specific ones (e.g. /grill-me, /to-ssot for ssot-gen).
        """
        try:
            from core.slash_commands import get_registry as _gr
            reg = _gr()
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        # The registry stores commands in an internal dict; read it
        # defensively through whatever public surface is available.
        cmds = []
        seen = set()
        for attr in ("commands", "_commands"):
            entries = getattr(reg, attr, None)
            if isinstance(entries, dict):
                for name, spec in entries.items():
                    canonical = spec.get("name", name) if isinstance(spec, dict) else name
                    if canonical in seen:
                        continue
                    seen.add(canonical)
                    if isinstance(spec, dict):
                        cmds.append({
                            "cmd":     "/" + canonical,
                            "name":    canonical,
                            "aliases": spec.get("aliases", []) or [],
                            "hint":    spec.get("description", "") or "",
                            "usage":   spec.get("usage", f"/{canonical}"),
                        })
                break
        cmds.sort(key=lambda c: c["name"])
        return JSONResponse({"commands": cmds})

    @app.get("/api/ssot")
    async def api_ssot(file: str = ""):
        if file:
            target = _safe(file)
            if target is None or not target.is_file():
                return JSONResponse({"error": "not found"}, status_code=404)
            try:
                content = target.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                return JSONResponse({"error": str(e)}, status_code=500)
            return JSONResponse({"path": file, "content": content})
        # No specific file → list every *.ssot.yaml in the project
        results = []
        for p in PROJECT_ROOT.rglob("*.ssot.yaml"):
            if any(part in SKIP_DIRS or part.startswith(".")
                   for part in p.parts):
                continue
            try:
                rel = str(p.relative_to(PROJECT_ROOT))
                stat = p.stat()
                results.append({"path": rel, "size": stat.st_size,
                                 "mtime": stat.st_mtime})
            except OSError:
                continue
        return JSONResponse({"files": results})

    @app.get("/api/soc")
    async def api_soc():
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

            def _build_module(leaf_ssot_path):
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
                if _yaml is not None:
                    try:
                        doc = _yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
                        if isinstance(doc, dict):
                            top = doc.get("top_module") or top
                            cl = doc.get("clocks") or []
                            rs = doc.get("resets") or []
                            clocks_n, resets_n = len(cl), len(rs)
                            for k in ("parameters", "params"):
                                if isinstance(doc.get(k), list):
                                    for it in doc[k][:6]:
                                        if isinstance(it, dict):
                                            nm = it.get("name") or it.get("k")
                                            vv = it.get("value") if "value" in it else it.get("v")
                                            if nm is not None:
                                                params.append({"k": str(nm), "v": str(vv)})
                            bif = doc.get("busInterfaces") or doc.get("interfaces") or []
                            if isinstance(bif, list):
                                _sides = ["right", "left", "top", "bottom"]
                                for i, it in enumerate(bif[:8]):
                                    if not isinstance(it, dict): continue
                                    interfaces.append({
                                        "name": str(it.get("name") or f"if{i}"),
                                        "proto": str(it.get("proto") or it.get("protocol") or "AXI4"),
                                        "role":  str(it.get("role") or "slave"),
                                        "side":  str(it.get("side") or _sides[i % 4]),
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
                sim_dir = ip_dir / "sim"
                sim_files = []
                if sim_dir.is_dir():
                    sim_files = list(sim_dir.rglob("*.log")) + list(sim_dir.rglob("*.vcd"))
                sim_history = []
                hist = sim_dir / "history.json"
                if hist.is_file():
                    try:
                        h = json.loads(hist.read_text(encoding="utf-8"))
                        if isinstance(h, dict) and isinstance(h.get("runs"), list):
                            sim_history = h["runs"][-12:]
                    except Exception:
                        pass
                ssot_st = "ok"
                rtl_st  = "ok" if rtl_files else ("partial" if rtl_dir.is_dir() else "pending")
                sim_st  = "ok" if sim_files else "pending"
                return {
                    "id": ip_name,
                    "name": top,
                    "label": top,
                    "kind": _kind_for(ip_name),
                    "params": params,
                    "status": {"ssot": ssot_st, "rtl": rtl_st, "sim": sim_st},
                    "interfaces": interfaces,
                    "addr": addr,
                    "rtl_files": [str(f.relative_to(PROJECT_ROOT)) for f in rtl_files],
                    "ssot_path": str(p.relative_to(PROJECT_ROOT)),
                    "ip_dir": str(ip_dir.relative_to(PROJECT_ROOT)),
                    "clocks": clocks_n,
                    "resets": resets_n,
                    "sim_history": sim_history,
                    "ssot_mtime": p.stat().st_mtime,
                }

            def _aggregate_status(modules):
                if not modules:
                    return {"ssot": "pending", "rtl": "pending", "sim": "pending"}
                return {
                    "ssot": "ok",
                    "rtl":  "ok" if all(m["status"]["rtl"] == "ok" for m in modules)
                          else ("partial" if any(m["status"]["rtl"] == "ok" for m in modules) else "pending"),
                    "sim":  "ok" if all(m["status"]["sim"] == "ok" for m in modules)
                          else ("partial" if any(m["status"]["sim"] == "ok" for m in modules) else "pending"),
                }

            project_name = PROJECT_ROOT.name or "project"
            soc_path = PROJECT_ROOT / "soc.ssot.yaml"

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
                        m = _build_module(leaf_path)
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
                    "soc_ssot_path": str(soc_path.relative_to(PROJECT_ROOT)),
                    "soc_ssot_mtime": soc_path.stat().st_mtime,
                })

            # ── Tier 2: no soc.ssot.yaml → fall back to dir-walk ──
            modules = []
            for p in PROJECT_ROOT.rglob("*.ssot.yaml"):
                if any(part in SKIP_DIRS or part.startswith(".")
                       for part in p.parts):
                    continue
                if p.name == "soc.ssot.yaml": continue  # handled above
                modules.append(_build_module(p))
            modules.sort(key=lambda m: m["id"])
            cluster = {
                "id": "ips", "name": "ips", "label": "Project IPs",
                "x": 60, "y": 80, "w": 1200, "h": 600,
                "status": _aggregate_status(modules),
                "modules": modules,
            }
            return JSONResponse({
                "name": project_name,
                "version": "live",
                "clusters": [cluster] if modules else [],
                "busses": [],
                "addrMap": [],
                "module_count": len(modules),
                "source": "dir-walk",
            })
        except Exception as e:
            return JSONResponse({"error": str(e), "clusters": []}, status_code=500)

    # ── Jobs (HTTP-worker dispatch tracker) ────────────────────────
    # Atlas UI tracks jobs the user dispatched from the Architect screen
    # via the block ⚡ button. We fire-and-forget POST /run (sync=False)
    # to the matching worker, store the run_id locally, and the
    # frontend's JobTracker polls /api/jobs which in turn polls each
    # worker's /status/{run_id}. The atlas_ui process never blocks on
    # a worker; the worker carries the full main-loop ReAct work.
    _jobs_lock = threading.Lock()
    _jobs: dict = {}     # job_id (uuid) → {workflow, ip, run_id, worker, started_at, status, …}

    def _resolve_worker_url(workflow: str) -> str:
        """Same precedence as core.delegate_runner.HTTPWorkerDelegate."""
        if workflow:
            key = "WORKER_URL_" + workflow.upper().replace("-", "_")
            url = os.environ.get(key)
            if url:
                return url
        return os.environ.get("WORKER_URL_DEFAULT", "http://localhost:8001")

    @app.post("/api/job/dispatch")
    async def api_job_dispatch(request: Request):
        """Dispatch a workflow onto an IP via an HTTP worker.

        Body: `{workflow: 'rtl-gen', ip: 'counter', prompt?: '...'}`

        Defaults the prompt to a workflow-specific template so the user
        can just click the block menu without typing. Returns
        `{job_id, run_id, worker, status: 'queued'}` immediately; the
        frontend polls /api/jobs to track progress.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        workflow = (body.get("workflow") or "").strip()
        ip       = (body.get("ip") or "").strip()
        prompt   = (body.get("prompt") or "").strip()
        if not workflow:
            return JSONResponse({"error": "missing 'workflow'"}, status_code=400)
        if not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", workflow):
            return JSONResponse({"error": f"invalid workflow {workflow!r}"}, status_code=400)
        if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)

        # Default prompt per workflow — short and explicit so the worker
        # has a clear task even when the user just clicks the menu.
        if not prompt:
            prompt_for = {
                "rtl-gen":  f"regenerate RTL for {ip} from {ip}/yaml/{ip}.ssot.yaml",
                "tb-gen":   f"generate testbench for {ip}",
                "sim":      f"run simulation for {ip}",
                "lint":     f"lint {ip}/rtl/*.sv",
                "syn":      f"synthesise {ip}",
                "sta":      f"run STA for {ip}",
                "ssot-gen": f"refresh SSOT for {ip}",
            }
            prompt = prompt_for.get(workflow,
                f"run {workflow}" + (f" on {ip}" if ip else ""))

        worker_url = _resolve_worker_url(workflow)
        # Fire-and-forget POST /run with sync=False.
        try:
            import urllib.request as _u
            payload = json.dumps({
                "task": prompt,
                "workflow": workflow,
                "sync": False,
            }).encode("utf-8")
            req = _u.Request(
                f"{worker_url.rstrip('/')}/run",
                data=payload, method="POST",
                headers={"Content-Type": "application/json"},
            )
            with _u.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return JSONResponse({
                "error": f"worker dispatch failed at {worker_url}: {e}",
                "worker": worker_url,
            }, status_code=502)

        run_id = resp_data.get("run_id", "")
        if not run_id:
            return JSONResponse({
                "error": "worker did not return run_id",
                "worker": worker_url,
                "raw": resp_data,
            }, status_code=502)

        import uuid
        job_id = uuid.uuid4().hex[:12]
        now = time.time()
        with _jobs_lock:
            _jobs[job_id] = {
                "job_id": job_id,
                "run_id": run_id,
                "worker": worker_url,
                "workflow": workflow,
                "ip": ip,
                "prompt": prompt,
                "started_at": now,
                "status": "running",
                "iterations": 0,
                "files_modified": [],
                "result_summary": "",
                "error": "",
                "_last_polled": 0.0,
            }
        return JSONResponse({
            "ok": True,
            "job_id": job_id,
            "run_id": run_id,
            "worker": worker_url,
            "status": "running",
        })

    @app.get("/api/jobs")
    async def api_jobs():
        """Aggregate job status across all dispatched workers.

        For each tracked job, poll the worker's /status/{run_id} (with a
        small 1.5s per-job cache to avoid hammering during a 2-second
        frontend poll cycle) and return the merged list. Sorted by
        started_at descending so the most-recent job is first.
        """
        out = []
        now = time.time()
        with _jobs_lock:
            snapshot = list(_jobs.values())
        for job in snapshot:
            if job["status"] in ("running",) and (now - job.get("_last_polled", 0)) > 1.5:
                # Poll worker for fresh state.
                try:
                    import urllib.request as _u
                    req = _u.Request(
                        f"{job['worker'].rstrip('/')}/status/{job['run_id']}",
                        method="GET",
                    )
                    with _u.urlopen(req, timeout=5) as resp:
                        s = json.loads(resp.read().decode("utf-8"))
                    job["_last_polled"] = now
                    job["status"] = s.get("status", job["status"])
                    if isinstance(s.get("iterations"), int):
                        job["iterations"] = s["iterations"]
                    if s.get("status") in ("completed", "error", "cancelled"):
                        # Fetch full result body once on completion.
                        try:
                            req2 = _u.Request(
                                f"{job['worker'].rstrip('/')}/result/{job['run_id']}",
                                method="GET",
                            )
                            with _u.urlopen(req2, timeout=5) as r2:
                                rr = json.loads(r2.read().decode("utf-8"))
                            job["files_modified"] = rr.get("files_modified") or []
                            job["result_summary"] = (rr.get("result") or "")[:600]
                            job["error"] = rr.get("error") or ""
                            job["finished_at"] = now
                            if rr.get("execution_time_ms"):
                                job["duration_ms"] = rr["execution_time_ms"]
                        except Exception:
                            pass
                except Exception as e:
                    job["error"] = f"poll failed: {e}"
            out.append({k: v for k, v in job.items() if not k.startswith("_")})
        out.sort(key=lambda j: j.get("started_at", 0), reverse=True)
        return JSONResponse({"jobs": out, "count": len(out)})

    @app.post("/api/job/{job_id}/cancel")
    async def api_job_cancel(job_id: str):
        with _jobs_lock:
            job = _jobs.get(job_id)
        if not job:
            return JSONResponse({"error": "job not found"}, status_code=404)
        if job["status"] != "running":
            return JSONResponse({"error": f"job already {job['status']}"}, status_code=400)
        try:
            import urllib.request as _u
            req = _u.Request(
                f"{job['worker'].rstrip('/')}/cancel/{job['run_id']}",
                method="POST",
            )
            with _u.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception as e:
            return JSONResponse({"error": f"cancel failed: {e}"}, status_code=502)
        with _jobs_lock:
            job["status"] = "cancelled"
        return JSONResponse({"ok": True})

    @app.post("/api/jobs/clear")
    async def api_jobs_clear():
        """Drop completed/cancelled/failed jobs from the tracker."""
        with _jobs_lock:
            for jid in list(_jobs.keys()):
                if _jobs[jid]["status"] != "running":
                    _jobs.pop(jid, None)
        return JSONResponse({"ok": True})

    @app.post("/api/soc/layout")
    async def api_soc_layout(request: Request):
        """Persist user-dragged block positions back into soc.ssot.yaml.

        Body (JSON): `{"layout": {"<cluster>/<inst>": {"x": <num>, "y": <num>}, …}}`

        For each entry, find the matching `instances[].id` (`<cluster>/<inst>`
        is split on `/`; we use just the inst id since SoC SSOT instance
        ids are unique) and set its `x:` / `y:` keys. Other fields are
        left untouched. The file is rewritten in-place with
        `yaml.safe_dump`. Empty layout `{}` clears all x/y from every
        instance (paired with the frontend's [reset] button).

        Architect screen reads these on the next /api/soc fetch and
        uses them as the default block position (overriding the
        auto-grid). LocalStorage layout still wins as the most-local
        cache, so a user can preview drag-arounds before committing.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        layout = body.get("layout") if isinstance(body, dict) else None
        if not isinstance(layout, dict):
            return JSONResponse({"error": "missing 'layout' object"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)

        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                 status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"parse: {e}"}, status_code=500)
        if not isinstance(doc, dict): doc = {}
        instances = doc.get("instances")
        if not isinstance(instances, list):
            return JSONResponse({"error": "soc.ssot.yaml has no instances[]"},
                                 status_code=400)

        # Build lookup `inst_id → ref` from layout keys.
        ref_for_inst = {}
        for ref in layout.keys():
            if not isinstance(ref, str) or "/" not in ref: continue
            inst_id = ref.split("/", 1)[1]
            ref_for_inst[inst_id] = ref

        touched = 0
        cleared = 0
        for inst in instances:
            if not isinstance(inst, dict): continue
            iid = inst.get("id")
            if not iid: continue
            ref = ref_for_inst.get(iid)
            if ref is None:
                # Instance not in incoming layout: if it has stale x/y
                # AND the incoming layout was empty `{}`, clear them.
                if not layout:
                    if "x" in inst: inst.pop("x"); cleared += 1
                    if "y" in inst: inst.pop("y"); cleared += 1
                continue
            pos = layout.get(ref)
            if isinstance(pos, dict) and isinstance(pos.get("x"), (int, float)) \
               and isinstance(pos.get("y"), (int, float)):
                inst["x"] = round(float(pos["x"]), 1)
                inst["y"] = round(float(pos["y"]), 1)
                touched += 1

        # Preserve hex formatting on address fields. PyYAML parses
        # `0x4000_2000` to int 1073750016 on load; safe_dump would write
        # it back as decimal. Walk the doc and stringify any int in
        # known address slots so the rewritten file keeps the canonical
        # `0x4000_2000` notation the user wrote.
        def _hex8(n):
            h = f"{n:x}"
            target = max(8, ((len(h) - 1) // 4 + 1) * 4)
            h = h.zfill(target)
            if len(h) > 4:
                rev = h[::-1]
                groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
                h = "_".join(groups)[::-1]
            return f"0x{h}"
        for inst in (doc.get("instances") or []):
            if isinstance(inst, dict) and isinstance(inst.get("addr"), int):
                inst["addr"] = _hex8(inst["addr"])
        for e in (doc.get("addrMap") or []):
            if isinstance(e, dict):
                if isinstance(e.get("base"), int):  e["base"]  = _hex8(e["base"])
                if isinstance(e.get("range"), int): e["range"] = _hex8(e["range"])

        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "touched": touched, "cleared": cleared,
                              "path": str(soc_path.relative_to(PROJECT_ROOT))})

    @app.post("/api/ipxact/import")
    async def api_ipxact_import(request: Request):
        """Import an IP-XACT XML payload into the project as a new IP.

        Accepts either:
          • multipart/form-data with a `xml` file part + optional `name`
          • application/json: {"xml": "<XML…>", "name": "spi_master"}
          • application/xml or text/xml body + ?name=<ip_name> query

        Writes <project_root>/<name>/yaml/<name>.ssot.yaml and scaffolds
        the surrounding IP layout. Returns the parsed SSOT + path.
        """
        try:
            ct = (request.headers.get("content-type") or "").lower()
            xml_text: str = ""
            ip_name: str = ""
            if ct.startswith("multipart/form-data"):
                form = await request.form()
                up = form.get("xml")
                if up is None:
                    return JSONResponse({"error": "missing 'xml' file part"}, status_code=400)
                if hasattr(up, "read"):
                    raw = await up.read()
                    xml_text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
                else:
                    xml_text = str(up)
                ip_name = (form.get("name") or "").strip()
            elif "json" in ct:
                body = await request.json()
                xml_text = body.get("xml", "") or ""
                ip_name = (body.get("name") or "").strip()
            else:
                raw = await request.body()
                xml_text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
                ip_name = (request.query_params.get("name") or "").strip()
            if not xml_text.strip():
                return JSONResponse({"error": "empty XML payload"}, status_code=400)

            try:
                from core.ipxact_import import import_ipxact as _conv
            except Exception:
                try: from ipxact_import import import_ipxact as _conv  # type: ignore
                except Exception as e:
                    return JSONResponse({"error": f"importer unavailable: {e}"}, status_code=500)
            try:
                ssot = _conv(xml_text, ip_name=ip_name or None)
            except Exception as e:
                return JSONResponse({"error": f"parse error: {e}"}, status_code=400)
            name = (ip_name or ssot.get("top_module") or "").strip()
            if not name or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
                return JSONResponse({"error": f"invalid ip name {name!r}"}, status_code=400)

            # Write into <project_root>/<name>/yaml/<name>.ssot.yaml.
            ip_dir = PROJECT_ROOT / name
            (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
            for sub in ("rtl", "sim", "tb", "list", "lint", "doc"):
                (ip_dir / sub).mkdir(parents=True, exist_ok=True)
            yaml_path = ip_dir / "yaml" / f"{name}.ssot.yaml"
            try:
                import yaml as _yaml
                with open(yaml_path, "w", encoding="utf-8") as f:
                    f.write("# Auto-imported from IP-XACT — review and edit as needed.\n")
                    _yaml.safe_dump(ssot, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
            except ImportError:
                # No PyYAML → write a JSON sidecar so the import still
                # produces something usable.
                with open(yaml_path.with_suffix(".json"), "w", encoding="utf-8") as f:
                    json.dump(ssot, f, indent=2)
                yaml_path = yaml_path.with_suffix(".json")
            except OSError as e:
                return JSONResponse({"error": f"write error: {e}"}, status_code=500)

            # Auto-register into soc.ssot.yaml when Tier-1 is active so
            # the new IP appears in the architect tree on the next
            # /api/soc fetch (was P1 bug — yaml on disk but tree empty).
            registered = False
            try:
                soc_path = PROJECT_ROOT / "soc.ssot.yaml"
                if soc_path.is_file():
                    import yaml as _y
                    sd = _y.safe_load(soc_path.read_text(encoding="utf-8")) or {}
                    if isinstance(sd, dict):
                        instances = sd.setdefault("instances", [])
                        # Skip if an instance with this id already exists.
                        existing = next((i for i in instances
                                          if isinstance(i, dict) and i.get("id") == name), None)
                        if existing is None:
                            new_inst = {
                                "id": name,
                                "ssot": str(yaml_path.relative_to(PROJECT_ROOT)),
                            }
                            # Pull addr from the imported IP's memoryMap
                            # so addrmap_check can validate it.
                            mm = (ssot or {}).get("memoryMap") or []
                            if isinstance(mm, list) and mm and isinstance(mm[0], dict):
                                base = mm[0].get("base")
                                if base: new_inst["addr"] = base
                            instances.append(new_inst)
                            # Drop into a synthetic "uncategorized" cluster
                            # if nothing else claims it (clusters[].members
                            # is the source of truth — auto-add a stub).
                            clusters = sd.setdefault("clusters", [])
                            uncat = next((c for c in clusters
                                          if isinstance(c, dict) and c.get("id") == "uncategorized"),
                                          None)
                            if uncat is None:
                                clusters.append({
                                    "id": "uncategorized",
                                    "role": "PERIPH",
                                    "label": "Uncategorized (auto-imported)",
                                    "members": [name],
                                })
                            else:
                                members = uncat.setdefault("members", [])
                                if name not in members: members.append(name)
                            with open(soc_path, "w", encoding="utf-8") as f:
                                _y.safe_dump(sd, f, sort_keys=False,
                                             default_flow_style=False, allow_unicode=True)
                            registered = True
            except Exception as e:
                # Non-fatal — IP file is on disk, just couldn't auto-register.
                # Frontend will still see it via Tier-2 fallback.
                pass

            return JSONResponse({
                "ok": True,
                "name": name,
                "path": str(yaml_path.relative_to(PROJECT_ROOT)),
                "registered_in_soc": registered,
                "ssot": ssot,
            })
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/conversation")
    async def api_conversation(limit: int = 200):
        """Return the last N messages from the active workspace's
        conversation.json. Used by the Atlas frontend to hydrate the
        chat feed when the user switches workflow (/wf <name>) — without
        this the Atlas chat is browser-session-only and prior context
        from the workflow is invisible.

        config.HISTORY_FILE is already redirected per workspace by
        session_setup.setup_session, so we just read whichever file
        the live session points at right now.
        """
        try:
            try: import src.config as _cfg  # type: ignore
            except Exception:
                try: import config as _cfg  # type: ignore
                except Exception: _cfg = None
            if _cfg is None:
                return JSONResponse({"messages": [], "error": "config unavailable"})
            hpath = Path(getattr(_cfg, "HISTORY_FILE", "") or "")
            if not hpath.is_file():
                return JSONResponse({"messages": [], "path": str(hpath)})
            try:
                msgs = json.loads(hpath.read_text(encoding="utf-8"))
                if not isinstance(msgs, list):
                    msgs = []
            except Exception as e:
                return JSONResponse({"messages": [], "path": str(hpath),
                                       "error": f"parse: {e}"})
            # Drop system prompts (huge, useless in chat replay) and
            # keep only the last `limit` items.
            msgs = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system"]
            if len(msgs) > limit:
                msgs = msgs[-limit:]
            return JSONResponse({"messages": msgs, "path": str(hpath),
                                  "truncated_to": limit})
        except Exception as e:
            return JSONResponse({"messages": [], "error": str(e)},
                                 status_code=500)

    # ── Git API — status / diff / commit / push ─────────────────
    # All git commands run inside PROJECT_ROOT (the user's cwd at
    # launch). Read-only ops stream back; commit + push run sync
    # and return their stdout/stderr. Push includes an explicit
    # confirm flag because it's destructive (remote-visible).
    import subprocess as _sp_git
    def _git(*args, check_root: bool = True):
        try:
            r = _sp_git.run(
                ["git", *args], cwd=str(PROJECT_ROOT),
                capture_output=True, text=True, timeout=30,
            )
            return r.returncode, r.stdout, r.stderr
        except _sp_git.TimeoutExpired:
            return 124, "", "git command timed out"
        except FileNotFoundError:
            return 127, "", "git executable not found"

    @app.get("/api/git/status")
    async def api_git_status():
        # Branch
        rc, branch, _ = _git("rev-parse", "--abbrev-ref", "HEAD")
        branch = branch.strip() if rc == 0 else ""
        # Porcelain status with numstat-ish summary
        rc, out, err = _git("status", "--porcelain=v1", "--branch")
        if rc != 0:
            return JSONResponse({"error": err.strip() or "git status failed",
                                 "branch": branch, "files": []}, status_code=200)
        files = []
        ahead = behind = 0
        for line in out.splitlines():
            if not line: continue
            if line.startswith("##"):
                # ## main...origin/main [ahead 1, behind 2]
                m = re.search(r"ahead (\d+)", line)
                if m: ahead = int(m.group(1))
                m = re.search(r"behind (\d+)", line)
                if m: behind = int(m.group(1))
                continue
            # XY <path>  (X=staged, Y=unstaged)
            xy = line[:2]; path = line[3:]
            # Renames: "old -> new"
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            files.append({
                "path": path,
                "status": xy,
                "staged":   xy[0] not in (" ", "?"),
                "unstaged": xy[1] != " ",
            })
        # Per-file numstat (added/removed lines) — best-effort
        rc, ns_out, _ = _git("diff", "--numstat", "HEAD")
        numstat = {}
        if rc == 0:
            for line in ns_out.splitlines():
                parts = line.split("\t")
                if len(parts) >= 3:
                    a, d, p = parts[0], parts[1], parts[2]
                    try:
                        numstat[p] = {"added": int(a) if a != "-" else 0,
                                       "removed": int(d) if d != "-" else 0}
                    except ValueError:
                        pass
        for f in files:
            ns = numstat.get(f["path"])
            if ns: f.update(ns)
        return JSONResponse({"branch": branch, "ahead": ahead,
                              "behind": behind, "files": files})

    @app.get("/api/git/diff")
    async def api_git_diff(path: str = "", staged: int = 0):
        if not path:
            rc, out, err = _git("diff" if not staged else "diff", "--cached" if staged else "HEAD")
        else:
            args = ["diff"]
            if staged: args.append("--cached")
            args.append("--")
            args.append(path)
            rc, out, err = _git(*args)
        if rc != 0 and not out:
            return JSONResponse({"error": err.strip() or "diff failed",
                                  "diff": ""}, status_code=200)
        return JSONResponse({"diff": out, "path": path})

    @app.post("/api/git/commit")
    async def api_git_commit(payload: dict):
        message = (payload or {}).get("message", "").strip()
        add_all = bool((payload or {}).get("add_all", True))
        if not message:
            return JSONResponse({"error": "commit message required"},
                                 status_code=400)
        if add_all:
            rc, _, err = _git("add", "-A")
            if rc != 0:
                return JSONResponse({"error": "git add -A failed: " + err.strip()},
                                     status_code=200)
        rc, out, err = _git("commit", "-m", message)
        return JSONResponse({"ok": rc == 0, "stdout": out, "stderr": err,
                              "returncode": rc})

    @app.post("/api/git/push")
    async def api_git_push(payload: dict = None):
        # Push current branch to origin. User must explicitly confirm
        # in the UI before this fires.
        rc, branch, _ = _git("rev-parse", "--abbrev-ref", "HEAD")
        branch = branch.strip()
        if not branch or branch == "HEAD":
            return JSONResponse({"error": "no current branch (detached HEAD?)"},
                                 status_code=400)
        rc, out, err = _git("push", "origin", branch)
        return JSONResponse({"ok": rc == 0, "stdout": out, "stderr": err,
                              "branch": branch, "returncode": rc})

    # NOTE: WebSocket endpoint is registered via Starlette's WebSocketRoute
    # (added to app.router.routes below) instead of the @app.websocket
    # decorator. The decorator routes through FastAPI's dependency-injection
    # layer, which can't resolve the `websocket: WebSocket` annotation when
    # `from __future__ import annotations` is active (PEP 563 turns all
    # annotations into strings) and rejects the handshake with HTTP 403.
    # Starlette's WebSocketRoute talks to the function directly and ignores
    # parameter annotations entirely.
    async def ws_agent(websocket: WebSocket):
        await websocket.accept()
        clients.add(websocket)
        # Greeting — surface user-tunable layout settings so the frontend
        # can pick its center-column shape (classic vs tabbed Chat/Preview/Q&A).
        try:
            import src.config as _cfg_hello
            _center_layout = getattr(_cfg_hello, "ATLAS_CENTER_LAYOUT", "classic")
        except Exception:
            _center_layout = "classic"
        await websocket.send_json({"type": "hello", "frontend": "atlas",
                                    "running": bridge.agent_running,
                                    "center_layout": _center_layout})

        # Pump outbox → all sockets. Broadcast in parallel with a per-client
        # timeout so a single half-dead WS (browser tab closed but TCP FIN
        # not yet processed by uvicorn — send_json blocks instead of
        # raising) doesn't strand the message for the rest of the live
        # clients. The previous sequential loop made every emit hostage to
        # the slowest peer, which on browser-reload races caused token
        # frames to silently disappear while later events (agent_state,
        # done) still landed via a different pump_out task.
        async def _send_one(client, msg):
            # Scale the per-client send timeout with the message size so
            # large payloads (e.g. /context with a 50 kB full system prompt
            # + conversation dump) don't get killed mid-flight and strand
            # subsequent events (flush, slash_output, agent_state). Floor
            # at 4 s so tiny control frames still get a reasonable window.
            try:
                import json
                raw = json.dumps(msg, ensure_ascii=False)
                size_kb = max(len(raw.encode("utf-8", errors="replace")) / 1024, 1)
                timeout = max(4.0, size_kb * 0.25)  # 0.25 s per kB → 50 kB ≈ 12.5 s
                await asyncio.wait_for(client.send_json(msg), timeout=timeout)
                return None
            except Exception:
                return client

        async def pump_out():
            while True:
                msg = await bridge.next_event()
                snapshot = list(clients)
                if not snapshot:
                    continue
                results = await asyncio.gather(
                    *(_send_one(c, msg) for c in snapshot),
                    return_exceptions=False,
                )
                for stale_client in results:
                    if stale_client is not None:
                        clients.discard(stale_client)

        pump_task = asyncio.create_task(pump_out())
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                except Exception:
                    continue
                t = msg.get("type")
                if t in ("prompt", "send") and msg.get("text"):
                    _txt = msg["text"].strip()
                    # ── Mode-flip slashes need to apply mid-loop ──
                    # `/mode normal` and `/plan` typed while the agent is
                    # running normally land in the _interrupts queue,
                    # which feeds the agent as conversational text — the
                    # slash dispatcher only runs against _inbox between
                    # turns. So agent_mode never actually flips and the
                    # agent stays trapped in plan_q forever, hitting
                    # `[Plan Mode] blocked` on every write_file. We
                    # intercept those four canonical forms here and set
                    # AGENT_MODE_OVERRIDE in the environment; react_loop
                    # reads it at the top of each iteration.
                    import os as _os
                    _low = _txt.lower()
                    if _low in ("/plan", "/mode plan", "/mode normal", "/normal"):
                        if _low in ("/plan", "/mode plan"):
                            _os.environ["AGENT_MODE_OVERRIDE"] = "plan_q"
                            _os.environ["PLAN_MODE"] = "true"
                        else:
                            _os.environ["AGENT_MODE_OVERRIDE"] = "normal"
                            _os.environ["PLAN_MODE"] = "false"
                            _os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
                        # Two-pronged dispatch:
                        # (1) AGENT_MODE_OVERRIDE handles the MID-LOOP case
                        #     (agent currently iterating; react_loop top
                        #     pops it on the next pass and flips local
                        #     agent_mode for parallel_executor).
                        # (2) submit_prompt forwards the slash so main.py's
                        #     dispatcher can fire AGENT_MODE:normal/plan
                        #     when the loop is IDLE — that path is what
                        #     keeps main.py's local agent_mode + the
                        #     system prompt in messages[0] consistent
                        #     across turns. Without this submit, the
                        #     UI's "● NORMAL" pill could click without
                        #     ever telling main.py to flip — desync.
                        # The slash dispatcher in main.py emits its own
                        # "✅ <Mode> mode — tools enabled." banner, so we
                        # don't need to emit one here too (was creating
                        # duplicate confirmations on the idle path).
                        bridge.submit_prompt(_txt)
                        continue

                    # `y` / `yc` / `yes` / `confirm` mid-loop while agent
                    # is in plan mode → treat as plan confirmation. Without
                    # this, the input lands in the _interrupts queue and
                    # gets fed to the LLM as conversational text — the
                    # plan-confirmation handler in chat_loop only runs
                    # against _inbox between turns. So `y` after the
                    # agent shows the [Plan Mode] Plan ready prompt does
                    # nothing if the agent is still mid-iteration.
                    if (_os.environ.get("PLAN_MODE") == "true"
                            and bridge.agent_running
                            and _low in ("y", "yes", "yc", "confirm", "ok",
                                         "proceed", "ㅇㅇ", "확인", "진행")):
                        _os.environ["AGENT_MODE_OVERRIDE"] = "normal"
                        _os.environ["PLAN_MODE"] = "false"
                        _os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
                        bridge.emit("token", text="\n✅ Plan confirmed (mid-loop): tools enabled. Executing.\n")
                        bridge.emit("flush")
                        # Inject an instruction so the agent knows to start
                        # executing the agreed-upon plan. This goes to
                        # _interrupts (since agent is running), fed mid-loop.
                        bridge.submit_prompt(
                            "Confirmed. Execute all tasks in order. "
                            "For EACH task: todo_update(in_progress) → do work "
                            "→ todo_update(completed) → verify → todo_update(approved)."
                        )
                        continue
                    bridge.submit_prompt(_txt)
                elif t == "interrupt":
                    bridge.submit_prompt(msg.get("text", ""))
                elif t == "answer" and msg.get("flow_id"):
                    bridge.submit_answer(msg["flow_id"], msg)
                elif t == "stop":
                    # Esc from the UI — abort the current iteration.
                    bridge.request_stop()
                    bridge.emit("agent_state", running=False)
                elif t == "shutdown":
                    # Exit button — kill the whole Python process so the
                    # user's terminal returns to a normal prompt.
                    bridge.emit("error", message="server is shutting down")
                    bridge.emit("done")
                    import os as _os, threading as _t
                    _t.Timer(0.4, lambda: _os._exit(0)).start()
                # Other types (e.g. run_stage, tool_call) can be wired later
        except WebSocketDisconnect:
            pass
        finally:
            clients.discard(websocket)
            pump_task.cancel()

    # Register the WebSocket endpoint via Starlette so we don't go through
    # FastAPI's DI layer (see the long comment above the ws_agent definition).
    app.router.routes.append(WebSocketRoute("/ws/agent", ws_agent))

    # Static assets — jsx, css, js, fonts (registered LAST so it doesn't
    # shadow the explicit routes above). Disable client-side caching so
    # a normal page refresh always picks up new JSX/CSS.
    class _NoCacheStatic(StaticFiles):
        async def get_response(self, path, scope):
            resp = await super().get_response(path, scope)
            resp.headers["Cache-Control"] = "no-store, max-age=0"
            return resp

    app.mount("/", _NoCacheStatic(directory=str(FRONTEND), html=False),
              name="atlas-static")

    app.state.bridge = bridge
    return app


# ── Entry point ────────────────────────────────────────────────────
def run_atlas_ui(port: int = 8765, host: str = "127.0.0.1") -> None:
    """Start the Atlas web UI server and run the agent in a worker thread.

    Wires brian_hw/common_ai_agent/src/main.py's _textual_* callbacks so the
    existing ReAct loop streams to all connected WS clients.
    """
    import uvicorn
    import main as _main  # noqa: WPS433  (intentional runtime import)

    app = create_app()
    bridge: _AtlasBridge = app.state.bridge

    # ── Wire main.py callbacks → bridge.emit ───────────────────────
    _main._textual_input_fn = bridge.get_input
    # Esc from the UI sets bridge._stop_flag; react_loop polls this
    # via esc_check_fn and aborts the current iteration cleanly.
    _main._textual_esc_check_fn = bridge.check_stop
    _main._textual_poll_human_input_fn = bridge.poll_interrupt

    # Strip ANSI escape sequences from ANY text destined for the browser.
    # The terminal-targeting Color class wraps lines in \x1b[2m … \x1b[0m;
    # the browser renders the ESC byte invisibly but happily prints the
    # leftover "[2m" / "[0m" markers, which leaked into the chat as visible
    # garbage. Doing the strip once here covers every emit path.
    import re as _re_ansi
    _ANSI_RE = _re_ansi.compile(
        r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
    )
    def _clean(s):
        return _ANSI_RE.sub("", s) if isinstance(s, str) else s

    _main._textual_emit_content_fn   = lambda text, cls="": bridge.emit("token",     text=_clean(text), cls=cls)
    _main._textual_emit_reasoning_fn = lambda text, blank=False: bridge.emit("reasoning", text=_clean(text))
    _main._textual_emit_todo_fn      = lambda text: bridge.emit("todo_line", text=_clean(text))
    _main._textual_emit_flush_fn     = lambda: (
        bridge.emit("flush"),
        # Workspace switches happen behind a slash command and re-register
        # the slash registry. Nudge the UI to re-fetch /api/commands so the
        # autocomplete dropdown picks up new workspace commands.
        bridge.emit("commands_changed"),
    )
    _main._textual_emit_tool_fn      = lambda text: bridge.emit("tool", text=_clean(text))
    # Browser-side tool_result cap. Display-only — LLM still gets the
    # full obs upstream; this just trims what we ship over the WS so a
    # 200KB grep doesn't drown the chat. Configurable in .config via
    # WS_TOOL_RESULT_MAX_CHARS (default 8000).
    _ws_tool_max = 8000
    try:
        try: import src.config as _cfg2  # type: ignore  # noqa: WPS433
        except Exception:
            try: import config as _cfg2  # type: ignore  # noqa: WPS433
            except Exception: _cfg2 = None
        if _cfg2 is not None:
            _ws_tool_max = int(getattr(_cfg2, "WS_TOOL_RESULT_MAX_CHARS", 8000))
    except Exception:
        _ws_tool_max = 8000
    def _emit_tool_result(obs, tool=""):
        cleaned = _clean(obs)
        bridge.emit(
            "tool_result",
            text=cleaned[:_ws_tool_max],
            tool=tool,
            truncated=len(cleaned) > _ws_tool_max,
        )
    _main._textual_emit_tool_result_fn = _emit_tool_result

    def _ctx_update(tokens, max_tok):
        bridge.emit("context", used=tokens, max=max_tok)
    _main._textual_emit_context_fn = _ctx_update
    def _emit_token(in_tok, cache_tok, out_tok):
        # Resolve pricing at LLM-call time so the rate matches the model
        # actually used for THIS call (LLM_BASE_MODEL env can pin the base
        # model; otherwise fall back to MODEL_NAME / LLM_MODEL_NAME).
        # Computing the USD delta on the backend keeps frontend math simple
        # and avoids drift between page-load /healthz pricing and the
        # current call's model.
        try:
            from lib.model_pricing import get_active_pricing
            p = get_active_pricing()
        except Exception:
            p = None
        cost_delta = 0.0
        if p is not None:
            cost_delta = (
                (in_tok or 0)    * p.input  +
                (cache_tok or 0) * p.cache  +
                (out_tok or 0)   * p.output
            ) / 1_000_000.0
        # Resolve display model name for the frontend cost panel.
        try:
            import os as _os_cost
            _model_now = (
                _os_cost.getenv("LLM_BASE_MODEL", "").strip()
                or _os_cost.getenv("LLM_MODEL_NAME", "").strip()
            )
            if not _model_now:
                try:
                    from src.llm_client import get_active_model as _gam
                    _model_now = _gam() or ""
                except Exception:
                    _model_now = ""
        except Exception:
            _model_now = ""
        bridge.emit(
            "cost",
            input=in_tok, cached=cache_tok, output=out_tok,
            cost_usd_delta=cost_delta,
            pricing={"input": p.input, "cache": p.cache, "output": p.output} if p else None,
            model=_model_now,
        )
    _main._textual_emit_token_fn = _emit_token

    def _set_running(val: bool):
        bridge.agent_running = val
        bridge.emit("agent_state", running=val)
    _main._textual_set_agent_running_fn = _set_running

    # Safety-net emit for slash command output. The token+flush pipeline has
    # shown intermittent delivery for slash payloads (frontend gets the
    # subsequent agent_state but no token frame), leaving the user with a
    # missing /context / /help / /skills response. This event lands the
    # payload directly in the feed via workspace.jsx's slash_output handler.
    _main._textual_emit_slash_output_fn = lambda text: bridge.emit(
        "slash_output", text=_clean(text)
    )

    # Mode-change notification — chat_loop auto-promotes plan_q→normal when
    # the user types "y" to confirm. Without this signal the React mode pill
    # stays on PLAN even though the agent is now executing.
    _main._textual_emit_mode_fn = lambda mode: bridge.emit("mode_change", mode=mode)

    # ── ask_user → emit qcard event, block on answer queue ────────
    import uuid
    try:
        from core import tools as _tools
    except ImportError:
        _tools = None

    def _ask_user_cb(question, options, kind, subtitle, questions=None):
        """ask_user UI bridge.

        Single-question mode: pass `question/options/kind/subtitle`.
        Batched mode (mirrors textual UI): pass `questions=[{...}, ...]`
        and the frontend renders a tab strip — one breadcrumb per
        question, ☐/☒ answered marker, plus a final 'Submit' tab — so
        the user fills N answers in one round-trip.
        """
        flow_id = "qa_" + uuid.uuid4().hex[:10]
        bridge.open_question(flow_id)
        if questions:
            # Batched payload — frontend (workspace.jsx) detects the
            # `questions` array and switches to tabbed render.
            bridge.emit(
                "ask_user",
                flow_id=flow_id,
                questions=questions,
            )
        else:
            bridge.emit(
                "ask_user",
                flow_id=flow_id,
                question=question,
                kind=kind,
                subtitle=subtitle or "",
                options=options or [],
            )
        try:
            ans = bridge.wait_answer(flow_id, timeout=900)  # 15 min ceiling
        finally:
            bridge.close_question(flow_id)
        if ans is None:
            return "[ask_user: no answer received within 15 min]"
        # Cancel-all from the user — match textual UI wording.
        if isinstance(ans, dict) and ans.get("type") == "cancel":
            return "User declined to answer questions"
        # Batched answer format: {"answers": [{...}, ...]} aligned with questions.
        if questions and isinstance(ans, dict) and "answers" in ans:
            blocks = []
            for q, qa in zip(questions, ans.get("answers") or []):
                label = (q.get("subtitle") or q.get("question", ""))[:40]
                blocks.append(
                    f"  • {label}\n    {_format_answer(qa, q.get('options'))}"
                )
            return "Batched answers:\n" + "\n".join(blocks) if blocks else "(no answers)"
        return _format_answer(ans, options or [])

    if _tools and hasattr(_tools, "set_ask_user_callback"):
        _tools.set_ask_user_callback(_ask_user_cb)

    def _run_agent():
        try:
            _main.chat_loop()
        except Exception as e:
            bridge.emit("error", message=str(e))
        finally:
            bridge.agent_running = False
            bridge.emit("agent_state", running=False)
            bridge.emit("done")

    threading.Thread(target=_run_agent, daemon=True).start()

    # Surface the source-repo path to the agent so it can locate
    # workflow/, rules/, templates/, etc. when running from a non-source
    # cwd (e.g. user runs `cd Custom_IP && python ../…/textual_main.py`).
    os.environ["ATLAS_SOURCE_ROOT"] = str(SOURCE_ROOT)
    os.environ["ATLAS_PROJECT_ROOT"] = str(PROJECT_ROOT)
    # Inject a system-prompt note so the LLM knows about both roots.
    _root_note = (
        f"\n\n[Atlas Runtime] You are running with cwd = {PROJECT_ROOT}. "
        f"All file reads/writes default to here. The source repo "
        f"(workflow templates, ssot-template.yaml, skills) lives at "
        f"{SOURCE_ROOT} — reference those by absolute path, not by "
        f"relative path from cwd."
    )
    try:
        # Append to whatever the existing system prompt builder produces
        # so the hint is part of every system-prompt rebuild (workspace
        # switches included).
        _orig_builder = getattr(_main, "_build_system_prompt_str", None)
        if callable(_orig_builder):
            def _patched_builder(*a, _orig=_orig_builder, _note=_root_note, **kw):
                return _orig(*a, **kw) + _note
            _main._build_system_prompt_str = _patched_builder
    except Exception:
        pass

    print(f"\n  ATLAS UI → http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main() -> None:
    ap = argparse.ArgumentParser(prog="atlas_ui",
                                  description="Atlas frontend for common_ai_agent")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    run_atlas_ui(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
