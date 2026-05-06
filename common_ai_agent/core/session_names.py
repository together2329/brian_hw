"""Session namespace normalization helpers.

The server stores run state under ``.session/<namespace>/``. UI clients may
send either that namespace (``ip/rtl-gen``) or a platform path copied from a
session artifact. Never use a client path directly; extract the namespace and
then resolve it under the local project ``.session`` root.
"""

from __future__ import annotations

import re

_SESSION_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_KNOWN_SESSION_FILES = {
    "conversation.json",
    "todo.json",
    "todo_error.json",
    "cost.json",
    "state.json",
}
_KNOWN_WORKFLOWS = {
    "architect",
    "coverage",
    "fl-model-gen",
    "goal-audit",
    "lint",
    "mas-gen",
    "rtl-gen",
    "signoff",
    "sim",
    "sim_debug",
    "ssot-gen",
    "tb-gen",
}


def normalize_session_name(value: str) -> str:
    """Return a safe ``.session`` namespace, or ``""`` when invalid.

    Accepted inputs:
    - ``dma330/rtl-gen``
    - ``u-mabc123/dma330/rtl-gen``
    - ``.session/dma330/rtl-gen``
    - ``C:\\repo\\common_ai_agent\\.session\\dma330\\rtl-gen``
    - ``C:\\repo\\common_ai_agent\\.session\\dma330\\rtl-gen\\conversation.json``

    The returned value is always slash-separated and relative to ``.session``.
    """

    raw = str(value or "").strip().strip("\"'")
    if not raw:
        return ""

    pathish = "\\" in raw or ":" in raw or raw.startswith(("/", "~"))
    normalized = raw.replace("\\", "/").strip("/")
    parts = [part for part in normalized.split("/") if part and part != "."]
    if not parts:
        return ""

    lowered = [part.lower() for part in parts]
    had_session_marker = ".session" in lowered
    if ".session" in lowered:
        index = len(lowered) - 1 - lowered[::-1].index(".session")
        parts = parts[index + 1:]
    elif re.match(r"^[A-Za-z]:$", parts[0]):
        # A UI scope can accidentally arrive as a Windows filesystem path plus
        # workflow, e.g. C:\Users\me\Desktop\SQA\ssot-gen. A session is a
        # namespace, not a host path; keep only the final scope/workflow pair.
        parts = parts[1:]
        if len(parts) > 2:
            parts = parts[-2:]

    if parts and parts[-1].lower() in _KNOWN_SESSION_FILES:
        parts = parts[:-1]

    if not parts:
        return ""

    # Windows UI paths sometimes arrive without an explicit ".session"
    # marker, for example "\Users\me\Desktop\SQA\ssot-gen" or
    # "C:\Users\me\Desktop\SQA\ssot-gen". Treat those as path-ish and
    # keep the namespace-looking tail instead of accepting the entire host
    # filesystem path as a deeply nested session name.
    if (
        len(parts) > 2
        and parts[-1].lower() in _KNOWN_WORKFLOWS
        and ((pathish and not had_session_marker) or len(parts) > 3)
    ):
        parts = parts[-2:]

    safe_parts: list[str] = []
    for part in parts:
        if part == ".." or ":" in part or not _SESSION_SEGMENT_RE.match(part):
            return ""
        safe_parts.append(part)

    return "/".join(safe_parts)
