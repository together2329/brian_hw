#!/usr/bin/env python3
"""Codex Stop hook: re-inject the next OAG action while an active run is incomplete.

Output contract (Codex Stop hook):
  - print {"decision": "block", "reason": "<next-action prompt>"} on stdout to block the stop
  - exit 0 ALWAYS (a hook must never break the turn)

Target resolution order:
  1. hook stdin payload: {"ip_dir": "...", "run_id": "..."}
  2. environment: OAG_IP_DIR / OAG_RUN_ID
  3. fallback scan: <project>/*/ontology/runs/active_run.json

For each target it calls oag.stop_check. If any run wants to continue or needs a
human decision, it blocks the stop with that run's prompt block. When no active
run wants to continue, it stays silent so normal stops pass.

This is the Codex-hook-shaped sibling of scripts-driven oag.stop_check; the older
hooks/oag_stop_check.py stays as a manual/example runner.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # .codex/
PROJECT = ROOT.parent  # project root that holds the IP folders
sys.path.insert(0, str(ROOT / "scripts"))

import oag_cli  # noqa: E402


def _read_payload() -> dict:
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _project_path(value: str) -> str:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = PROJECT / path
    return str(path.resolve())


def _target_runs(payload: dict) -> list[dict[str, str]]:
    payload_ip = str(payload.get("ip_dir") or "").strip()
    env_ip = os.environ.get("OAG_IP_DIR", "").strip()
    payload_run = str(payload.get("run_id") or "").strip()
    env_run = os.environ.get("OAG_RUN_ID", "").strip()
    run_id = payload_run or env_run

    explicit_ip = payload_ip or env_ip
    if explicit_ip:
        return [{"ip_dir": _project_path(explicit_ip), "run_id": run_id}]

    found: list[dict[str, str]] = []
    for active in PROJECT.glob("*/ontology/runs/active_run.json"):
        try:
            data = json.loads(active.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        active_run = str(data.get("run_id") or "") if isinstance(data, dict) else ""
        if run_id and active_run != run_id:
            continue
        # <ip>/ontology/runs/active_run.json -> <ip>
        found.append({"ip_dir": str(active.parents[2]), "run_id": active_run})
    return found


def _dedupe_targets(targets: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for target in targets:
        key = (target.get("ip_dir", ""), target.get("run_id", ""))
        if not key[0] or key in seen:
            continue
        seen.add(key)
        unique.append(target)
    return unique


def _stop_check(target: dict[str, str]) -> dict:
    args = {"ip_dir": target["ip_dir"]}
    if target.get("run_id"):
        args["run_id"] = target["run_id"]
    response = oag_cli.dispatch_call({"tool": "oag.stop_check", "arguments": args})
    if not isinstance(response, dict) or not response.get("ok"):
        return {}
    result = response.get("result")
    return result if isinstance(result, dict) else {}


def main() -> int:
    payload = _read_payload()
    blocks: list[str] = []
    for target in _dedupe_targets(_target_runs(payload)):
        try:
            result = _stop_check(target)
        except Exception:
            continue  # fail open: a hook must never break the turn
        should_continue = result.get("should_continue") is True or result.get("reason") == "needs_human_decision"
        if not should_continue:
            continue
        reason_code = str(result.get("reason") or "")
        name = result.get("ip") or Path(target["ip_dir"]).name
        prompt = str(result.get("prompt_block") or "").strip()
        if reason_code == "needs_human_decision":
            header = f"[OAG:{name}] run needs human decision before continuing."
        else:
            header = f"[OAG:{name}] run incomplete ({reason_code})."
        blocks.append(f"{header}\n{prompt}".strip())

    if blocks:
        reason = (
            "Active OAG run(s) still require closure or a human decision. "
            "Do not stop until the prompt below is handled:\n\n" + "\n\n".join(blocks)
        )
        print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
