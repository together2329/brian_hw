#!/usr/bin/env python3
"""Codex Stop hook that asks for ROCEV-shaped hardware completion wording."""

from __future__ import annotations

import json
import re
import sys
from typing import Any


LABELS = ("Requirement:", "Obligation:", "Contract:", "Evidence:", "Validation:")


def load_payload() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def needs_rocev_shape(message: str) -> bool:
    text = message.lower()
    hardware_terms = (
        "rtl",
        "tb",
        "sim",
        "lint",
        "coverage",
        "formal",
        "signoff",
        "scoreboard",
        "vcd",
        "evidence",
        "validation",
    )
    completion_terms = (
        "done",
        "passed",
        "pass",
        "closed",
        "complete",
        "tests passed",
    )
    return any(term in text for term in hardware_terms) and any(
        term in text for term in completion_terms
    )


def has_rocev_shape(message: str) -> bool:
    return all(label in message for label in LABELS)


def main() -> int:
    payload = load_payload()
    message = payload.get("last_assistant_message") or ""
    if not isinstance(message, str) or not message.strip():
        return 0

    if needs_rocev_shape(message) and not has_rocev_shape(message):
        reason = (
            "Hardware completion claims should use Requirement, Obligation, "
            "Contract, Evidence, and Validation, with concrete evidence paths."
        )
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

