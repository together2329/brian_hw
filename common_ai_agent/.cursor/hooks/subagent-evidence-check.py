#!/usr/bin/env python3
"""Cursor `subagentStop` hook — 스테이지 오너 subagent의 증거 없는 완료 주장 차단.

계약 (Cursor hooks 스펙):
  stdin  : {"subagent_type": str, "status": "completed"|..., "summary": str,
            "task": str, "loop_count": int, ...}
  stdout : {"followup_message": "..."}  → subagent 자동 재개 (loop_limit 상한)
           {}                            → 통과

동작: 이 프로젝트에 정의된 subagent(.cursor/agents/*.md, readonly 제외)가
"완료"로 멈췄는데 summary에 검증 증거 흔적(PASS/FAIL 라인, rc/exit 코드,
N passed, gate/validator 언급, 산출물 경로)이 하나도 없으면 — 증거를 요구하는
followup 발행. silent-PASS의 subagent 판본 차단.

검증: tests/test_cursor_pack.py
"""

import json
import os
import re
import sys
from pathlib import Path

EVIDENCE_RE = re.compile(
    r"PASS|FAIL|rc=\d|exit (?:code )?\d|\d+ passed|\d+/\d+|gate|validator|"
    r"results\.xml|sim_report|scoreboard|lint|compile|pytest|check_",
    re.IGNORECASE,
)


def _enforced_agents() -> set:
    """프로젝트 정의 subagent 중 readonly 가 아닌 것들 (증거 의무 대상)."""
    root = Path(os.environ.get("CURSOR_PROJECT_DIR")
                or os.environ.get("CLAUDE_PROJECT_DIR") or ".")
    names = set()
    for p in (root / ".cursor" / "agents").glob("*.md"):
        try:
            head = p.read_text(encoding="utf-8", errors="replace")[:500]
        except OSError:
            continue
        if re.search(r"(?m)^readonly:\s*true\b", head):
            continue
        names.add(p.stem)
    return names


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    subagent = str(payload.get("subagent_type", ""))
    status = payload.get("status", "completed")
    summary = str(payload.get("summary", "") or "")

    if status != "completed" or subagent not in _enforced_agents():
        print("{}")
        return
    if EVIDENCE_RE.search(summary):
        print("{}")
        return

    print(json.dumps({
        "followup_message": (
            "완료 주장에 검증 증거가 없습니다. 멈추기 전에: 해당 스테이지의 "
            "validator/gate를 실제로 실행하고, 그 출력의 verdict 라인(PASS/FAIL, "
            "N passed, rc=0 등)과 산출물 경로를 summary에 그대로 인용하세요. "
            "증거 없이 완료로 표시하는 것은 금지입니다 (rule 80-todo-evidence)."
        )
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
