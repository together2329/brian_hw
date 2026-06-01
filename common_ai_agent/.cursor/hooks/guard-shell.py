#!/usr/bin/env python3
"""Guard risky shell commands for Cursor hooks."""

import json
import re
import sys


def emit(permission, user_message="", agent_message=""):
    payload = {"permission": permission}
    if user_message:
        payload["user_message"] = user_message
    if agent_message:
        payload["agent_message"] = agent_message
    print(json.dumps(payload))


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        emit("allow")
        return

    command = (
        data.get("command")
        or data.get("cmd")
        or data.get("input", {}).get("command")
        or data.get("tool_input", {}).get("command")
        or ""
    )

    if not isinstance(command, str) or not command.strip():
        emit("allow")
        return

    unsafe_hdl_pipe = re.search(
        r"(?:\bvvp\b|cocotb|run_sim\.py|/sim\.sh|run_sim\.sh).*\|.*\b(?:head|tail|grep)\b",
        command,
        re.IGNORECASE,
    )
    if unsafe_hdl_pipe:
        emit(
            "deny",
            "HDL simulation output is being piped through head/tail/grep. Use the project sim script and inspect full logs instead.",
            "Use workflow sim scripts or the demo run_sim.sh without output-truncating pipes.",
        )
        return

    live_test = re.search(r"scripts/run_tests\.sh\s+live\b", command)
    if live_test and "--yes" not in command and "ATLAS_ALLOW_LIVE_TESTS=1" not in command:
        emit(
            "ask",
            "This appears to run live LLM tests. Confirm API cost and credentials before continuing.",
            "Live tests require explicit cost approval; add --yes only after the user agrees.",
        )
        return

    destructive_git = re.search(r"\bgit\s+(reset\s+--hard|clean\s+-[^\n]*f|checkout\s+--)\b", command)
    if destructive_git:
        emit(
            "ask",
            "This git command can discard work. Confirm before running it.",
            "Destructive git operations need explicit user approval.",
        )
        return

    emit("allow")


if __name__ == "__main__":
    main()
