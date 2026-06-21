#!/usr/bin/env python3
"""Probe: does the codex bridge's OAG prompt-hook fire and inject context when
pointed at an external .codex pack (e.g. ~/Desktop/Project/ip_dev/.codex)?

This exercises the SAME code path the ATLAS web UI uses per turn — the bridge's
`_oag_user_prompt_context` runs `<cwd>/.codex/hooks/codex_context_inject.py` +
`codex_draft_pressure.py` (gated by CODEX_BRIDGE_RUN_OAG_HOOKS=1) and injects
their `hookSpecificOutput.additionalContext` into turn/start. No codex/LLM call.

Usage:
    python3 scripts/verify_oag_hook.py [OAG_ROOT] [cwd] ["prompt"]
Defaults to the ip_dev pack / timer_ip IP.
"""
import asyncio
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

OAG_ROOT = sys.argv[1] if len(sys.argv) > 1 else "/Users/brian/Desktop/Project/ip_dev"
CWD = sys.argv[2] if len(sys.argv) > 2 else os.path.join(OAG_ROOT, "timer_ip")
PROMPT = sys.argv[3] if len(sys.argv) > 3 else "oag.inspect timer_ip"

os.environ["CODEX_BRIDGE_RUN_OAG_HOOKS"] = "1"
os.environ["CODEX_BRIDGE_HOME"] = os.path.join(OAG_ROOT, ".codex")
os.environ["CODEX_BRIDGE_OAG_ROOT"] = OAG_ROOT
os.environ["CODEX_BRIDGE_STAGE_DOT_CODEX"] = "1"

from core import codex_appserver_bridge as b  # noqa: E402


def main() -> int:
    print(f"OAG_ROOT  : {OAG_ROOT}")
    print(f"pack      : {b._configured_codex_pack_home()}")
    print(f"cwd       : {CWD}")
    print(f"prompt    : {PROMPT}\n")

    # In a real turn the bridge stages the pack into the thread cwd first; mirror
    # that so <cwd>/.codex/hooks/* resolve exactly as they do under the web UI.
    staged = os.path.isdir(os.path.join(CWD, ".codex", "hooks"))
    if not staged:
        b._stage_dot_codex(CWD)
        staged = os.path.isdir(os.path.join(CWD, ".codex", "hooks"))
    print(f"staged .codex/hooks at cwd: {staged}")
    print(f"  codex_context_inject.py present: "
          f"{os.path.isfile(os.path.join(CWD, '.codex', 'hooks', 'codex_context_inject.py'))}")

    ctx = asyncio.run(b._oag_user_prompt_context(CWD, PROMPT))
    print(f"\n=== OAG hook injected context: {len(ctx)} chars ===")
    print(ctx[:2500] if ctx else "(EMPTY — hook produced no additionalContext)")
    print("\n--- verdict ---")
    if ctx.strip():
        print("RESULT: PASS — OAG UserPromptSubmit hook fired and injected context.")
        return 0
    print("RESULT: FAIL — no context injected (hook missing/errored or pack not staged).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
