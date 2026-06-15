#!/usr/bin/env python3
"""Platform-canonical OAG backend (L4).

The OAG engine ships with the platform (vendored at
``common_ai_agent/.codex/scripts/oag_cli.py``). This thin, stable entry point
exposes that engine as the platform's backend so a `.codex` gateway — vendored
here OR living in another project — can route to a SINGLE platform engine by
setting ``OAG_COMMON_AI_AGENT`` / ``COMMON_AI_AGENT_HOME`` to this
``common_ai_agent`` root (oag_cli.py prefers ``$OAG_COMMON_AI_AGENT/scripts/oag.py``).

Contract (the one oag_cli.py delegates with):
    python3 scripts/oag.py call --json '{"tool":"oag.inspect","arguments":{...}}'
    -> JSON oag_tool_response.v1 on stdout

It runs the engine LOCALLY and never re-delegates (it IS the backend), so there
is no delegation loop even when OAG_COMMON_AI_AGENT points back at this root.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_ENGINE_PATH = Path(__file__).resolve().parents[1] / ".codex" / "scripts" / "oag_cli.py"


def _load_engine():
    if not _ENGINE_PATH.is_file():
        raise SystemExit(f"[oag.py] OAG engine not found: {_ENGINE_PATH}")
    spec = importlib.util.spec_from_file_location("_oag_platform_engine", _ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"[oag.py] cannot load OAG engine: {_ENGINE_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # This module IS the backend — force the engine to run its local handlers and
    # never delegate again (prevents an infinite delegation loop).
    if hasattr(mod, "_delegate_to_backend"):
        mod._delegate_to_backend = lambda envelope: None  # type: ignore[assignment]
    return mod


def _envelope_from_args(args: argparse.Namespace) -> dict:
    if args.json:
        return json.loads(args.json)
    if args.file:
        return json.loads(Path(args.file).read_text(encoding="utf-8"))
    if args.tool:
        return {"tool": args.tool, "arguments": {}}
    raise SystemExit("[oag.py] call needs a tool, --json, or --file")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Platform-canonical OAG backend")
    sub = parser.add_subparsers(dest="cmd")
    call = sub.add_parser("call", help="dispatch one OAG tool call")
    call.add_argument("tool", nargs="?")
    call.add_argument("--json", default="")
    call.add_argument("--file", default="")
    args = parser.parse_args(argv)
    if args.cmd != "call":
        parser.print_help()
        return 2
    envelope = _envelope_from_args(args)
    engine = _load_engine()
    resp = engine.dispatch_call(envelope)
    print(json.dumps(resp, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
