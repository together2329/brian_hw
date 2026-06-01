#!/usr/bin/env python3
"""Ask before editing generated evidence or local runtime artifacts."""

import json
import re
import sys


GENERATED_PATTERNS = [
    r"(^|/)\.session/",
    r"(^|/)cmd_output_[^/]*\.txt$",
    r"(^|/)current_todos\.json$",
    r"(^|/)ip_examples/",
    r"(^|/)sim/.*\.(vvp|vcd|log|json|csv|xml)$",
    r"(^|/)sim/(random|waves)/",
    r"(^|/)verify/",
    r"(^|/)cov/",
    r"(^|/)lint/.*\.(log|json)$",
    r"(^|/)(syn|sta|pnr|dft)/out/",
]


def emit(permission, user_message="", agent_message=""):
    payload = {"permission": permission}
    if user_message:
        payload["user_message"] = user_message
    if agent_message:
        payload["agent_message"] = agent_message
    print(json.dumps(payload))


def collect_paths(obj):
    paths = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in {"path", "file_path", "target_file", "target_path", "filename"} and isinstance(value, str):
                paths.append(value)
            else:
                paths.extend(collect_paths(value))
    elif isinstance(obj, list):
        for value in obj:
            paths.extend(collect_paths(value))
    return paths


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        emit("allow")
        return

    tool_name = (
        data.get("tool")
        or data.get("tool_name")
        or data.get("name")
        or data.get("input", {}).get("tool")
        or data.get("input", {}).get("tool_name")
        or ""
    )
    tool_name = str(tool_name).lower()
    if tool_name and not any(token in tool_name for token in ("write", "edit", "patch", "delete", "notebook")):
        emit("allow")
        return

    paths = collect_paths(data)
    risky = []
    for path in paths:
        normalized = path.replace("\\", "/")
        if any(re.search(pattern, normalized) for pattern in GENERATED_PATTERNS):
            risky.append(path)

    if risky:
        emit(
            "ask",
            "This edit targets generated evidence or runtime state. Regenerate through the owning workflow unless the user explicitly asked to edit it.",
            "Generated artifact edit guard matched: " + ", ".join(risky[:5]),
        )
        return

    emit("allow")


if __name__ == "__main__":
    main()
