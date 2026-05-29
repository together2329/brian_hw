"""Regression guard for atlas_slash_handlers.py emit/name scope.

The 14 slash handlers were extracted from the ws_agent closure into the
`make_slash_handlers` factory (Phase 12a). The factory takes NO `bridge`
kwarg, so a `bridge.emit(...)` / `bridge.request_stop()` in any handler body
is a dangling free name → LOAD_GLOBAL bridge → NameError the moment that
handler runs (e.g. `/ssot-rtl` → `_run_stage_command`). The per-call
`client_session` param is the session emitter (it has `.emit` and
`.request_stop`), exactly as `_handle_bang_shell_command` already uses.

This bug shipped twice (bridge.emit, then a wrong fix to a bare emit()), so it
gets a permanent test. Both checks are cheap + need no live server:
  1. bytecode: no nested function in make_slash_handlers references the global
     name 'bridge' (would be a guaranteed NameError).
  2. source: no bare `emit(` free call (must be `client_session.emit(`).
"""
import re
import types
from pathlib import Path

import importlib

SRC = Path(__file__).resolve().parents[1] / "src" / "atlas_slash_handlers.py"


def _walk_code(code):
    yield code
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            yield from _walk_code(const)


def test_no_handler_references_undefined_bridge():
    mod = importlib.import_module("src.atlas_slash_handlers")
    factory = mod.make_slash_handlers
    offenders = [
        c.co_name
        for c in _walk_code(factory.__code__)
        if "bridge" in c.co_names
    ]
    assert not offenders, (
        "make_slash_handlers has no 'bridge' in scope; these nested functions "
        f"reference an undefined global 'bridge' (use client_session.*): {offenders}"
    )


def test_no_bare_emit_call_in_source():
    src = SRC.read_text(encoding="utf-8")
    # bare emit( NOT preceded by a word char or dot (i.e. not client_session.emit / X_emit)
    bare = re.findall(r"(?<![\w.])emit\(", src)
    assert not bare, (
        f"{len(bare)} bare emit() call(s) found; the session emitter is "
        "client_session.emit(...)"
    )


def test_no_dangling_bridge_in_code_lines():
    """Readable backstop: no 'bridge.' attribute access in non-comment code."""
    code = "\n".join(
        ln for ln in SRC.read_text(encoding="utf-8").splitlines()
        if not ln.lstrip().startswith("#")
    )
    assert "bridge." not in code, "use client_session.* (no 'bridge' kwarg in this module)"
