#!/usr/bin/env python3
"""Shared helpers for OAG Codex hook adapters."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]  # .codex/
PROJECT = ROOT.parent

STAGE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "req": ("req", "requirement", "requirements", "interview", "locked truth"),
    "rtl": ("rtl", "verilog", "systemverilog", "module", "implementation"),
    "tb": ("tb", "testbench", "scoreboard", "stimulus"),
    "sim": ("sim", "simulation", "verilator", "cocotb"),
    "lint": ("lint",),
    "formal": ("formal", "assertion", "sva"),
    "coverage": ("coverage", "coverpoint", "cov"),
    "signoff": ("signoff", "closure", "complete", "claim_complete"),
}


def read_payload() -> dict[str, Any]:
    try:
        raw = os.read(0, 1_000_000).decode("utf-8")
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def first_text(payload: Any, keys: tuple[str, ...]) -> str:
    if isinstance(payload, dict):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        for value in payload.values():
            found = first_text(value, keys)
            if found:
                return found
    elif isinstance(payload, list):
        for value in payload:
            found = first_text(value, keys)
            if found:
                return found
    return ""


def prompt_text(payload: dict[str, Any]) -> str:
    return first_text(payload, ("prompt", "user_prompt", "userPrompt", "message", "content", "input"))


def project_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT / path
    return path.resolve()


def is_ip_dir(path: Path) -> bool:
    return (path / "ontology").is_dir() and (
        (path / "ontology" / "requirements.yaml").is_file()
        or (path / "ontology" / "ip.yaml").is_file()
        or (path / "req" / "locked_truth.md").is_file()
    )


def scan_ip_dirs() -> list[Path]:
    ips: list[Path] = []
    for child in sorted(PROJECT.iterdir()):
        if child.is_dir() and is_ip_dir(child):
            ips.append(child.resolve())
    return ips


def active_run_ips() -> list[Path]:
    ips: list[Path] = []
    for active in PROJECT.glob("*/ontology/runs/active_run.json"):
        try:
            data = json.loads(active.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        if isinstance(data, dict) and str(data.get("status") or "") == "complete":
            continue
        ips.append(active.parents[2].resolve())
    return ips


def infer_stage(text: str, fallback: str = "") -> str:
    lower = text.lower()
    for stage, words in STAGE_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(word)}\b", lower) for word in words):
            return stage
    return fallback


def has_oag_work_signal(text: str) -> bool:
    lower = text.lower()
    needles = {
        "oag",
        "ontology",
        "ip",
        "requirement",
        "obligation",
        "contract",
        "evidence",
        "validation",
        "rtl",
        "tb",
        "sim",
        "signoff",
        "coverage",
        "interview",
    }
    return any(needle in lower for needle in needles)


def target_ip_dirs(payload: dict[str, Any], *, require_signal: bool = True) -> list[Path]:
    prompt = prompt_text(payload)
    explicit = str(payload.get("ip_dir") or os.environ.get("OAG_IP_DIR") or "").strip()
    if explicit:
        path = project_path(explicit)
        return [path] if path.exists() else []

    lower_prompt = prompt.lower()
    matches = [ip for ip in scan_ip_dirs() if ip.name.lower() in lower_prompt]
    if matches:
        return matches[:3]

    active = active_run_ips()
    if active and (not require_signal or has_oag_work_signal(prompt)):
        return active[:3]
    return []


def hook_additional_context(text: str, hook_event: str = "UserPromptSubmit") -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": hook_event,
            "additionalContext": text,
        }
    }
