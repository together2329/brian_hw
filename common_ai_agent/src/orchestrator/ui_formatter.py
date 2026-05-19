"""Render orchestrator tool calls as user-readable status lines.

The orchestrator's LLM emits structured tool calls (dispatch_workflow,
read_evidence, …). The raw JSON is unreadable to non-engineers; this module
maps each tool to a single Korean/emoji status line that surfaces in the chat
panel alongside the assistant's natural-language replies.

Separation: ``react_bridge`` persists raw text; this module renders.
"""

from __future__ import annotations

from typing import Any, Dict


def _short(value: Any, limit: int = 60) -> str:
    s = "" if value is None else str(value)
    s = s.replace("\n", " ").strip()
    if len(s) > limit:
        return s[: limit - 1] + "…"
    return s


def _short_args(args: Dict[str, Any], limit: int = 80) -> str:
    if not isinstance(args, dict) or not args:
        return ""
    parts = []
    for k, v in args.items():
        parts.append(f"{k}={_short(v, 30)}")
    joined = ", ".join(parts)
    if len(joined) > limit:
        return joined[: limit - 1] + "…"
    return joined


def _fmt_dispatch_workflow(args: Dict[str, Any]) -> str:
    workflow = _short(args.get("workflow") or args.get("name") or "?", 40)
    ip = _short(args.get("ip") or "", 40)
    model = _short(args.get("model") or "", 30)
    bits = [workflow]
    if ip:
        bits.append(ip)
    if model:
        bits.append(model)
    suffix = " / ".join(bits)
    return f"🚀 {workflow} 실행 중 ({suffix})"


def _fmt_read_evidence(args: Dict[str, Any]) -> str:
    path = (
        args.get("path")
        or args.get("artifact_path")
        or args.get("stage")
        or args.get("ip")
        or ""
    )
    return f"📂 evidence 확인 중: {_short(path, 80)}"


def _fmt_read_artifact(args: Dict[str, Any]) -> str:
    ip = _short(args.get("ip") or "", 40)
    stage = _short(args.get("stage") or "", 40)
    target = " / ".join(b for b in (ip, stage) if b) or "?"
    return f"📂 artifact 확인 중: {target}"


def _fmt_read_pipeline_state(args: Dict[str, Any]) -> str:
    ip = _short(args.get("ip") or "", 40)
    return f"🔎 파이프라인 상태 조회: {ip}" if ip else "🔎 파이프라인 상태 조회"


def _fmt_mark_downstream_stale(args: Dict[str, Any]) -> str:
    stage = _short(args.get("stage") or args.get("from_stage") or "", 40)
    ip = _short(args.get("ip") or "", 40)
    target = " / ".join(b for b in (ip, stage) if b)
    if target:
        return f"♻️ 하위 stage 다시 큐잉 ({target})"
    return "♻️ 하위 stage 다시 큐잉..."


def _fmt_ask_user(args: Dict[str, Any]) -> str:
    question = _short(args.get("question") or args.get("prompt") or "", 200)
    return f"❓ {question}" if question else "❓ 사용자에게 질문"


def _fmt_yield_run(args: Dict[str, Any]) -> str:
    reason = _short(args.get("reason") or "", 120)
    return f"⏸ 대기 중 ({reason})" if reason else "⏸ 대기 중"


def _fmt_wait_job(args: Dict[str, Any]) -> str:
    job = _short(args.get("job_id") or args.get("id") or "", 40)
    return f"⏳ 작업 대기 중: {job}" if job else "⏳ 작업 대기 중"


def _fmt_write_handoff(args: Dict[str, Any]) -> str:
    target = _short(args.get("to") or args.get("target") or "", 40)
    return f"📤 handoff 작성: {target}" if target else "📤 handoff 작성"


def _fmt_classify_failure(args: Dict[str, Any]) -> str:
    stage = _short(args.get("stage") or "", 40)
    return f"🩺 실패 분석: {stage}" if stage else "🩺 실패 분석 중"


def _fmt_import_document(args: Dict[str, Any]) -> str:
    path = _short(args.get("path") or args.get("source") or "", 80)
    return f"📥 문서 임포트: {path}" if path else "📥 문서 임포트 중"


_FORMATTERS = {
    "dispatch_workflow": _fmt_dispatch_workflow,
    "read_evidence": _fmt_read_evidence,
    "read_artifact": _fmt_read_artifact,
    "read_pipeline_state": _fmt_read_pipeline_state,
    "mark_downstream_stale": _fmt_mark_downstream_stale,
    "ask_user": _fmt_ask_user,
    "yield_run": _fmt_yield_run,
    "wait_job": _fmt_wait_job,
    "write_handoff": _fmt_write_handoff,
    "classify_failure": _fmt_classify_failure,
    "import_document": _fmt_import_document,
}


def format_tool_call(tool_name: str, args: Dict[str, Any]) -> str:
    """Render ``(tool_name, args)`` as a single user-facing status line.

    Unknown tools fall back to ``tool_name(short_args)`` so the user still
    sees progress even when a new tool ships without a mapping."""
    name = str(tool_name or "").strip()
    args = args if isinstance(args, dict) else {}
    fmt = _FORMATTERS.get(name)
    if fmt is None:
        preview = _short_args(args)
        return f"{name}({preview})" if preview else f"{name}()"
    try:
        return fmt(args)
    except Exception:
        preview = _short_args(args)
        return f"{name}({preview})" if preview else f"{name}()"
