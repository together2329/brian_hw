#!/usr/bin/env python3
"""Live integration probe: drive the codex app-server bridge against a REAL
`codex app-server` and capture what envelope events flow — especially the new
`subagent` lane events — when codex spawns a subagent.

This validates the bridge's protocol mapping (collabAgentToolCall /
subAgentActivity / thread/started / foreign-threadId routing) against the actual
codex build, which the unit tests cannot (they use fakes).

Usage:
    CODEX_BRIDGE_MULTI_AGENT_MODE=explicitRequestOnly \
        python3 scripts/verify_codex_subagent_bridge.py ["custom prompt"]

Requires a working, authed `codex` binary (~/.codex/auth.json). Uses real model
tokens. Prints a per-event-type tally + every `subagent` payload, then a verdict.
"""
import asyncio
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force codex into explicit-request multi-agent mode so a subagent can spawn.
os.environ.setdefault("CODEX_BRIDGE_MULTI_AGENT_MODE", "explicitRequestOnly")
# Keep the OAG prompt hooks out of this probe (no sibling pack dependency).
os.environ.pop("CODEX_BRIDGE_RUN_OAG_HOOKS", None)

from core import codex_appserver_bridge as bridge  # noqa: E402

DEFAULT_PROMPT = (
    "Spawn a subagent (use your multi-agent / spawn_agent capability) named "
    "'Adder' whose only task is to compute 2+2 and return the number. Wait for "
    "it, then tell me exactly what the subagent returned."
)

tally: Counter = Counter()
subagent_events: list = []


class ProbeSession:
    session_id = "verify-subagent"

    def emit(self, msg_type: str, **payload):
        tally[msg_type] += 1
        if msg_type == "subagent":
            subagent_events.append(payload)
            line = json.dumps(payload, ensure_ascii=False)
            print(f"  >>> subagent: {line[:400]}", flush=True)
        elif msg_type in ("token", "reasoning"):
            sys.stdout.write(payload.get("text", ""))
            sys.stdout.flush()
        elif msg_type == "tool":
            print(f"\n  [tool] {str(payload.get('text',''))[:160]}", flush=True)
        elif msg_type == "error":
            print(f"\n  [error] {str(payload.get('message',''))[:300]}", flush=True)
        elif msg_type in ("agent_state", "done", "flush"):
            print(f"\n  [{msg_type}] {payload}", flush=True)


async def main() -> int:
    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    print(f"codex bin   : {bridge.CODEX_BIN}")
    print(f"app-server  : {' '.join(bridge._app_server_cmd(os.getcwd()))}")
    print(f"multi-agent : {bridge._multi_agent_enabled()} "
          f"(mode={bridge._MULTI_AGENT_MODE!r})")
    print(f"prompt      : {prompt}\n--- streaming ---", flush=True)
    try:
        await asyncio.wait_for(
            bridge.run_codex_turn(ProbeSession(), prompt, cwd=os.getcwd()),
            timeout=300,
        )
    except asyncio.TimeoutError:
        print("\n!! probe timed out after 300s", flush=True)

    print("\n\n--- verdict ---")
    print("event tally:", dict(tally))
    print(f"subagent events: {len(subagent_events)}")
    lanes = {e.get("agent_id") for e in subagent_events if e.get("agent_id")}
    kinds = Counter(e.get("kind") for e in subagent_events)
    labels = {e.get("label") for e in subagent_events if e.get("label")}
    print(f"  distinct lanes (agent_id): {len(lanes)} -> {list(lanes)[:5]}")
    print(f"  kinds: {dict(kinds)}")
    print(f"  labels seen: {list(labels)[:5]}")
    if subagent_events:
        print("RESULT: PASS — bridge surfaced subagent lane events from real codex.")
        return 0
    print("RESULT: NO-SUBAGENT — turn completed but codex emitted no subagent "
          "items (model may not have spawned one, or multi-agent unsupported).")
    return 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
