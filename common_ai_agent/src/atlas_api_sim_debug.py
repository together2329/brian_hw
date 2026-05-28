"""sim_debug API routes — extracted from src/atlas_ui.py.

Phase 11 PoC of refactor/atlas-modular: start the sim_debug API cluster
extraction (/api/source, /api/elab/*, /api/hierarchy, /api/trace,
/api/cocotb, /api/debug/scenarios). PoC moves the simplest endpoint
(/api/source); subsequent phases extend the factory with the rest.

Same factory pattern Phase 8/9 used for /api/file*: closure captures
become explicit kwargs on register_source_routes(app, **deps).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, FrozenSet, Optional, Set

from fastapi.responses import JSONResponse


# Whitelist of source-file extensions /api/source accepts.
_SOURCE_EXTS: FrozenSet[str] = frozenset({
    ".sv", ".v", ".svh", ".vh",            # systemverilog / verilog
    ".py",                                  # python (cocotb)
    ".sdc", ".tcl",                         # constraints / scripts
    ".f",                                   # filelist
    ".yaml", ".yml", ".json",               # config / metadata
    ".md", ".txt", ".log", ".rpt",          # docs / reports
    ".sh", ".bash",                         # scripts
    ".c", ".h", ".cpp", ".hpp",             # firmware
    ".xml",                                 # results.xml
})

# Files without extensions whose name alone qualifies them as source.
_SOURCE_NO_EXT_NAMES: FrozenSet[str] = frozenset({"Makefile", "makefile", "Dockerfile"})


def register_source_route(
    app: Any,
    *,
    safe_path_fn: Callable[[str], Optional[Path]],
) -> None:
    """Wire /api/source onto `app`.

    safe_path_fn(path) returns a Path inside PROJECT_ROOT or None if the
    path escapes / is rejected.
    """

    @app.get("/api/source")
    async def api_source(path: str):
        """Read a source file. Accepts SV / V / Python / Make /
        constraints / YAML / JSON / Markdown / shell / firmware /
        results.xml. Returns split-by-line array for the SourceViewer
        component."""
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
            "path": path,
            "size": len(content),
            "content": content,
            "lines": content.split("\n"),
        })
