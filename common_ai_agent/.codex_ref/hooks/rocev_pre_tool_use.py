#!/usr/bin/env python3
"""Codex PreToolUse hook for shallow hardware evidence commands."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


def load_payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def command_from(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value
    for key in ("command", "cmd"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))


def main() -> int:
    payload = load_payload()
    command = command_from(payload)
    if not command:
        return 0

    truncates_evidence = re.search(
        r"(results\.xml|scoreboard_events\.jsonl|coverage\.json|\.vcd|\.fst|sim_report|formal_status).*"
        r"\|.*\b(head|tail)\b",
        command,
        re.IGNORECASE,
    )
    if truncates_evidence:
        block(
            "ROCEV evidence should not be sampled with head/tail. Inspect the full relevant artifact or run the audit script."
        )
        return 0

    shallow_pass_grep = re.search(
        r"\bgrep\b.*\b(PASS|passed|0 failures|success)\b.*"
        r"(results\.xml|sim_report|scoreboard|coverage)",
        command,
        re.IGNORECASE,
    )
    if shallow_pass_grep:
        block(
            "A PASS string is not enough. Map it to Requirement, Obligation, Contract, Evidence, and Validation."
        )
        return 0

    destructive_ip_memory = re.search(
        r"(\bgit\b.*\breset\b.*(?:^|\s)--hard(?:\s|$)|"
        r"\brm\b\s+-rf\b.*(/|\\)(\.git|wiki)\b)",
        command,
        re.IGNORECASE,
    )
    if destructive_ip_memory:
        block(
            "This can erase IP-local git/wiki memory. Snapshot or inspect the IP memory before running it."
        )
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
