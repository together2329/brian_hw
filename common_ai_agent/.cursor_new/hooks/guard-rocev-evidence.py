#!/usr/bin/env python3
"""Small Cursor hook: warn about shallow evidence commands.

This hook is intentionally simple for seminar use. It does not try to prove the
workflow. It catches common shortcuts that often lead to weak PASS claims.
"""

import json
import re
import sys


def emit(permission: str, user_message: str = "", agent_message: str = "") -> None:
    payload = {"permission": permission}
    if user_message:
        payload["user_message"] = user_message
    if agent_message:
        payload["agent_message"] = agent_message
    print(json.dumps(payload, ensure_ascii=False))


def get_command(data: dict) -> str:
    candidates = [
        data.get("command"),
        data.get("cmd"),
        (data.get("input") or {}).get("command"),
        (data.get("tool_input") or {}).get("command"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        emit("allow")
        return

    command = get_command(data)
    if not command:
        emit("allow")
        return

    truncates_sim = re.search(
        r"(results\.xml|scoreboard_events\.jsonl|\.vcd|sim_report|cocotb|vvp).*\|.*\b(head|tail)\b",
        command,
        re.IGNORECASE,
    )
    if truncates_sim:
        emit(
            "ask",
            "This samples evidence with head/tail. For ROCEV, inspect the full relevant artifact or use a validator.",
            "Evidence should be tied to Requirement -> Obligation -> Contract -> Evidence -> Validation.",
        )
        return

    shallow_pass_grep = re.search(
        r"\bgrep\b.*\b(PASS|passed|0 failures|success)\b.*(results\.xml|sim_report|scoreboard)",
        command,
        re.IGNORECASE,
    )
    if shallow_pass_grep:
        emit(
            "ask",
            "This checks only a PASS string. Add the contract/evidence context: scoreboard, coverage, and the exact obligation.",
            "A PASS string is evidence only after it is mapped to the obligation and validation question.",
        )
        return

    destructive_ip_memory = re.search(
        r"(\bgit\b.*\breset\b.*(?:^|\s)--hard(?:\s|$)|"
        r"\brm\b\s+-rf\b.*(/|\\)(\.git|wiki)\b)",
        command,
        re.IGNORECASE,
    )
    if destructive_ip_memory:
        emit(
            "ask",
            "This can erase IP-local git/wiki memory. Snapshot or inspect the IP memory before running it.",
            "Use scripts/ip_dev_memory.py check <ip> --require-git before destructive cleanup.",
        )
        return

    emit("allow")


if __name__ == "__main__":
    main()
