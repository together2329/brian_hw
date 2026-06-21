#!/usr/bin/env python3
"""End-to-end probe: run ONE real codex app-server turn through the ATLAS bridge
configured against an external .codex OAG pack (ip_dev), and confirm the model
actually FOLLOWS the injected OAG context + can drive the oag tool — i.e. what the
ATLAS web UI does per turn when CODEX_BRIDGE_HOME points at ip_dev/.codex.

Auth stays on ~/.codex; only the OAG pack is staged into the thread cwd.
Uses real model tokens. Stages <cwd>/.codex (cleaned up by the caller).
"""
import asyncio
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

OAG_ROOT = "/Users/brian/Desktop/Project/ip_dev"
CWD = os.path.join(OAG_ROOT, "timer_ip")
PROMPT = ("In ONE short line, state timer_ip's current OAG closure status, "
          "scope_lock state, and whether implementation is allowed — read it "
          "from the injected IP knowledge ledger, do not guess.")

os.environ["CODEX_BRIDGE_HOME"] = os.path.join(OAG_ROOT, ".codex")
os.environ["CODEX_BRIDGE_OAG_ROOT"] = OAG_ROOT
os.environ["CODEX_BRIDGE_RUN_OAG_HOOKS"] = "1"
os.environ["CODEX_BRIDGE_STAGE_DOT_CODEX"] = "1"
os.environ["CODEX_BRIDGE_ENABLE_HOOKS"] = "1"
os.environ["CODEX_BRIDGE_BYPASS_HOOK_TRUST"] = "1"
os.environ["CODEX_BRIDGE_TRUST_THREAD_CWD"] = "1"

from core import codex_appserver_bridge as b  # noqa: E402

events = []
agent = []


class Sess:
    session_id = "verify-oag"

    def emit(self, t, **p):
        events.append((t, p))
        if t == "token":
            agent.append(p.get("text", ""))
            sys.stdout.write(p.get("text", "")); sys.stdout.flush()
        elif t == "tool":
            print(f"\n  [tool] {str(p.get('text',''))[:140]}", flush=True)
        elif t == "error":
            print(f"\n  [error] {str(p.get('message',''))[:300]}", flush=True)


async def main() -> int:
    print(f"pack staged from : {b._configured_codex_pack_home()}")
    print(f"cwd (IP)         : {CWD}")
    print(f"app-server cmd   : {' '.join(b._app_server_cmd(CWD))}")
    print(f"prompt           : {PROMPT}\n--- turn ---", flush=True)
    try:
        await asyncio.wait_for(b.run_codex_turn(Sess(), PROMPT, cwd=CWD), timeout=240)
    except asyncio.TimeoutError:
        print("\n!! turn timed out", flush=True)

    reply = "".join(agent).lower()
    print("\n\n--- verdict ---")
    tools = [p.get("text", "") for t, p in events if t == "tool"]
    print(f"tool calls: {tools[:6]}")
    hits = [k for k in ("draft", "10/10", "100", "scope_lock", "lock", "not allowed",
                        "cannot", "can_implement", "false", "interview") if k in reply]
    print(f"OAG-state terms echoed in reply: {hits}")
    used_oag = any("oag" in str(t).lower() for t in tools)
    grounded = len(hits) >= 2
    if grounded or used_oag:
        print("RESULT: PASS — model followed the injected OAG context"
              + (" and/or used the oag tool." if used_oag else "."))
        return 0
    print("RESULT: WEAK — turn ran but reply did not clearly reflect OAG state.")
    return 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
